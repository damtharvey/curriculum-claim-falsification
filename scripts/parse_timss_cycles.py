#!/usr/bin/env python3
"""Parse TIMSS 1995-2007 NCES/IEA public-release mathematics PDFs into Contract A items."""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ingest_lib import RAW, ROOT, base_item, choice_ok, clean_ws, dump_jsonl, extract_pdf_text
from parse_helpers import COUNTRY_START, flatten

LICENSE = (
    "SOURCE: TIMSS public-release mathematics items. Copyright IEA. "
    "Released items are for non-commercial, educational, and research purposes only. "
    "Not TIMSS 2015+ restricted-use."
)

ITEM_ID_RE = re.compile(r"Item Number:\s*([A-Z]?\d{1,7}[A-Z]?)", re.I)
BMITEM_START = re.compile(r"^([A-Z]\d+)\.\s+(.*)$")
CORRECT_LETTER = re.compile(r"Correct Response:\s*([A-E])\b", re.I)
COG_MAP = {
    "knowing": "knowing",
    "knowing facts and procedures": "knowing",
    "performing routine procedures": "applying",
    "using routine procedures": "applying",
    "using concepts": "applying",
    "solving routine problems": "applying",
    "applying": "applying",
    "using complex procedures": "reasoning",
    "solving problems": "reasoning",
    "investigating and solving problems": "reasoning",
    "reasoning": "reasoning",
}
COG_RE = re.compile(
    r"(knowing facts and procedures|performing routine procedures|using routine procedures|"
    r"using concepts|solving routine problems|using complex procedures|"
    r"investigating and solving problems|solving problems|"
    r"knowing|applying|reasoning)",
    re.I,
)
CHOICE_LINE = re.compile(r"^\s*([a-eA-E])(?:[\.\)])?\s*(.*)$")


def corpus_grade_year(name: str) -> tuple[str, str, str]:
    low = name.lower()
    year = "unknown"
    m = re.search(r"(1995|1999|2003|2007|2011)", low)
    if m:
        year = m.group(1)
    if "bmitems" in low:
        year = "1995"
    if "amitems" in low:
        year = "1995"
    grade = "8"
    if "g4" in low or "grade 4" in low or "grade4" in low or "amitems" in low or "pop1" in low:
        grade = "4"
    if "g8" in low or "grade 8" in low or "bmitems" in low or "pop2" in low:
        grade = "8"
    corpus = f"timss{year}" if year != "unknown" else "timss"
    return corpus, grade, year


def extract_choices(block: str) -> dict[str, str]:
    choices: dict[str, str] = {}
    current: str | None = None
    skipped_lead = False
    for raw in block.splitlines():
        s = raw.strip()
        if not s:
            continue
        if COUNTRY_START.match(s):
            break
        if not skipped_lead and re.fullmatch(r"[EMC]|CR", s):
            skipped_lead = True
            continue
        skipped_lead = True
        cm = CHOICE_LINE.match(s)
        if cm:
            letter = cm.group(1).upper()
            rest = cm.group(2).strip()
            if letter in choices and current != letter:
                break
            choices[letter] = rest
            current = letter
            continue
        if current is not None:
            if re.match(r"^(Item Number|Correct Response|Cognitive|Content Domain|Main Topic)", s, re.I):
                break
            if COUNTRY_START.match(s):
                break
            choices[current] = (choices[current] + " " + s).strip()
    out = {}
    for k, v in choices.items():
        v = clean_ws(v)
        if choice_ok(v) and len(v) < 220:
            out[k] = v
    return out


def parse_bmitems(text: str, source_url: str) -> list[dict]:
    """1995 Population 2 released booklet: I1. stem / A.-D. / key letter after Mathematics."""
    rows: list[dict] = []
    chunks = re.split(r"(?m)^(?=[A-Z]\d+\.\s)", text)
    for chunk in chunks:
        hm = re.match(r"^([A-Z]\d+)\.\s+(.*)$", chunk, re.S)
        if not hm:
            continue
        item_id = hm.group(1)
        body = chunk
        key_m = re.search(r"Mathematics\s+([A-D])\s+", body)
        if not key_m:
            continue
        key = key_m.group(1)
        cog_hits = COG_RE.findall(flatten(body))
        claim = ""
        for h in cog_hits:
            claim = COG_MAP.get(h.lower(), "")
            if claim:
                break
        if claim not in {"knowing", "applying", "reasoning"}:
            continue
        choices: dict[str, str] = {}
        current: str | None = None
        stem_parts: list[str] = []
        started = False
        for raw in body.splitlines()[1:]:
            s = raw.strip()
            if not s:
                continue
            if s.startswith("I-") or s.startswith("J-") or s.startswith("K-") or s == "Mathematics":
                break
            cm = re.match(r"^([A-D])\.\s*(.*)$", s)
            if cm:
                choices[cm.group(1)] = cm.group(2).strip()
                current = cm.group(1)
                started = True
                continue
            if started and current:
                choices[current] = (choices[current] + " " + s).strip()
                continue
            stem_parts.append(s)
        stem = clean_ws(" ".join(stem_parts))
        cleaned = {k: clean_ws(v) for k, v in choices.items() if choice_ok(v)}
        if len(cleaned) < 4 or key not in cleaned or len(stem) < 12:
            continue
        rec = base_item(
            item_id=f"timss1995-8-{item_id}",
            corpus="timss1995",
            authority="timss",
            claim=claim,
            stem=stem,
            key=key,
            response_type="selected",
            source_url=source_url,
            license_note=LICENSE,
            year="1995",
            grade="8",
            choices=cleaned,
            official_tag=claim,
            transcription_method="text-layer",
        )
        rows.append(rec)
    return rows


def parse_text(text: str, source_url: str, corpus: str, grade: str, year: str) -> list[dict]:
    rows: list[dict] = []
    for m in ITEM_ID_RE.finditer(text):
        item_id = m.group(1).upper()
        part = text[max(0, m.start() - 900) : min(len(text), m.end() + 2800)]
        letter_m = CORRECT_LETTER.search(part) or re.search(
            r"(?:Correct answer|Answer):\s*([A-E])\b", part, re.I
        )
        if not letter_m:
            continue
        key = letter_m.group(1).upper()
        flat = flatten(part[:1800]).lower()
        claim = ""
        cog_hits = COG_RE.findall(flat)
        for h in cog_hits:
            claim = COG_MAP.get(h.lower(), "")
            if claim:
                break
        if claim not in {"knowing", "applying", "reasoning"}:
            continue
        after = text[m.end() : min(len(text), m.end() + 2500)]
        after_lines = [ln for ln in after.splitlines()]
        if after_lines and re.fullmatch(r"\s*[EMC]\s*", after_lines[0] or ""):
            after_lines = after_lines[1:]
        after_body = "\n".join(after_lines)
        choices = extract_choices(after_body)
        if len(choices) < 4 or key not in choices:
            continue
        stem_lines: list[str] = []
        for raw in after_lines:
            if CHOICE_LINE.match(raw.strip()) and raw.strip()[:1].lower() in "abcde":
                break
            if re.search(r"Item Number|Cognitive Domain|Content Domain|Correct Response|Answer:", raw, re.I):
                continue
            if COUNTRY_START.match(raw.strip()):
                continue
            if re.fullmatch(r"[EMC]|CR", raw.strip()):
                continue
            s = raw.strip()
            if s:
                stem_lines.append(s)
        stem = clean_ws(" ".join(stem_lines[:10]))
        if len(stem) < 12:
            continue
        rec = base_item(
            item_id=f"{corpus}-{grade}-{item_id}",
            corpus=corpus,
            authority="timss",
            claim=claim,
            stem=stem,
            key=key,
            response_type="selected",
            source_url=source_url,
            license_note=LICENSE,
            year=year,
            grade=grade,
            choices=choices,
            official_tag=claim,
            transcription_method="text-layer",
        )
        rows.append(rec)
    return rows


def main() -> None:
    files = list((RAW / "timss").glob("*.pdf")) + [
        RAW / "TIMSS2011_G4_Math.pdf",
        RAW / "TIMSS2011_G8_Math.pdf",
    ]
    rows: list[dict] = []
    seen: set[str] = set()
    for path in files:
        if not path.exists() or path.suffix.lower() != ".pdf":
            continue
        if "2011" in path.name:
            continue
        try:
            text = extract_pdf_text(path)
        except Exception as exc:  # noqa: BLE001
            print("fail", path, exc)
            continue
        url = f"https://nces.ed.gov/timss/pdf/{path.name}"
        if path.name.lower() in {"bmitems.pdf", "amitems.pdf"}:
            grade = "8" if "bm" in path.name.lower() else "4"
            got = parse_bmitems(text, url)
            if grade == "4":
                for rec in got:
                    rec["id"] = rec["id"].replace("timss1995-8-", "timss1995-4-")
                    rec["grade"] = "4"
                    rec["corpus"] = "timss1995"
        else:
            corpus, grade, year = corpus_grade_year(path.name)
            got = parse_text(text, url, corpus, grade, year)
        print(path.name, len(got))
        for rec in got:
            if rec["id"] in seen:
                continue
            seen.add(rec["id"])
            rows.append(rec)
    out = ROOT / "data" / "timss_historical.jsonl"
    dump_jsonl(out, rows)
    print("wrote", len(rows), "->", out)


if __name__ == "__main__":
    main()
