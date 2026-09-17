#!/usr/bin/env python3
"""Parse TIMSS 2011 NCES public-release PDFs (layout text) into Contract A items."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "items.jsonl"
OVERLAY = ROOT / "data" / "timss_overlay.json"

G8_PDF = "https://nces.ed.gov/timss/pdf/TIMSS2011_G8_Math.pdf"
G4_PDF = "https://nces.ed.gov/timss/pdf/TIMSS2011_G4_Math.pdf"
LICENSE = (
    "SOURCE: TIMSS 2011 Assessment. Copyright © 2013 International Association "
    "for the Evaluation of Educational Achievement (IEA). Released items are for "
    "non-commercial, educational, and research purposes only. Public-release cycle; "
    "not TIMSS 2015+ restricted-use."
)

ITEM_ID_RE = re.compile(r"Item Number:\s*(M\d{6}[A-Z]?)", re.I)
INTL_AVG_RE = re.compile(r"International average\s+(\d+)")
CORRECT_LETTER_RE = re.compile(r"Correct Response:\s*([A-D])(?![A-Za-z])")
CORRECT_BULLET_RE = re.compile(
    r"Correct Response(?![^\n]{0,40}:\s*[A-D])[\s\S]{0,240}?•\s*([0-9][0-9.,/]*)",
    re.I,
)
COG_RE = re.compile(r"\b(Knowing|Applying|Reasoning)\b")
CONTENT_RE = re.compile(r"\b(NUMBER|ALGEBRA|GEOMETRY|DATA AND CHANCE|DATA DISPLAY)\b")
COUNTRY_LINE = re.compile(
    r"^(Singapore|Korea|Hong Kong|Chinese Taipei|Finland|Russian Federation|"
    r"Japan|Israel|Hungary|Sweden|England|Australia|Italy|Lithuania|Malaysia|"
    r"Norway|Kazakhstan|Turkey|New Zealand|United States|Slovenia|Ukraine|"
    r"Armenia|Georgia|Tunisia|Romania|United Arab Emirates|Iran|Macedonia|"
    r"Qatar|Chile|Thailand|Palestinian|Lebanon|Bahrain|Indonesia|Saudi Arabia|"
    r"Oman|Jordan|Morocco|Syrian|Ghana|North Carolina|Massachusetts|Minnesota|"
    r"Connecticut|Indiana|Florida|Colorado|California|Alabama|Quebec|Ontario|"
    r"Alberta|Dubai|Abu Dhabi|Benchmarking|Education system|Percent correct|"
    r"Overall Percent|International average|Copyright|Percent higher|Percent lower|"
    r"SCORING|Incorrect Response|Correct Response|Item Number)",
    re.I,
)

# Verified restorations: scoring-guide arithmetic or pie-chart transcription.
RESTORATIONS: dict[str, dict] = {
    "M032064": {
        "stem": (
            "Ann and Jenny divide 560 zeds between them. If Jenny gets 3/8 of the "
            "money, how many zeds will Ann get?"
        ),
        "key": "350",
        "responseType": "numeric",
        "restorationNote": (
            "Fraction 3/8 restored from the scoring guide: correct 350, listed "
            "incorrect 210 (Jenny's share) and 5/8 (Ann's fraction of 560)."
        ),
    },
    "M032166": {
        "stem": "Which of these is the BEST estimate of (7.21 × 3.86) / 10.09?",
        "choices": {"A": "28", "B": "2.8", "C": "0.28", "D": "0.028"},
        "key": "B",
        "responseType": "selected",
        "restorationNote": (
            "Choice numerals were graphics; filled as successive powers of ten "
            "around 7.2×3.9/10 ≈ 2.8, matching published key B."
        ),
    },
    "M032595": {
        "stem": (
            "The pie chart shows the percentage of caps for sale at a sporting goods "
            "store. White 30%, Green 25%, Red 20%, Black 15%, Blue 10%. If there are "
            "200 caps, what is the total number of caps that are either white or green?"
        ),
        "choices": {"A": "55", "B": "100", "C": "110", "D": "145"},
        "key": "C",
        "responseType": "selected",
        "figure": {
            "kind": "table",
            "transcription": "White 30%; Green 25%; Red 20%; Black 15%; Blue 10%; n=200",
        },
        "restorationNote": "Pie-chart percentages transcribed from the PDF layout.",
    },
    "M032094": {
        "stem": "4/100 + 3/1000 =",
        "choices": {"A": "0.043", "B": "0.1043", "C": "0.403", "D": "0.43"},
        "key": "A",
        "responseType": "selected",
        "restorationNote": "Stem and choices transcribed from the PDF layout.",
    },
}


def left_text(line: str) -> str:
    if len(line) > 105:
        line = line[:105]
    return line.rstrip()


def extract_choices(block: str) -> dict[str, str]:
    choices: dict[str, str] = {}
    for letter in "ABCD":
        matches = list(re.finditer(rf"(?m)^\s*{letter}\.\s+(\S.*)$", block))
        if not matches:
            continue
        val = left_text(matches[-1].group(1)).strip()
        val = re.sub(r"\s{2,}", " ", val)
        if COUNTRY_LINE.match(val):
            continue
        # drop trailing country fragments
        val = re.split(
            r"\s+\b(Singapore|Korea|Japan|United S|Hungar|Italy|Australi|Lebanon|Finland|Israel)\w*",
            val,
        )[0].strip()
        if val:
            choices[letter] = val
    return choices


def stem_from_header(block: str) -> str:
    lines: list[str] = []
    after_cog = False
    for raw in block.splitlines():
        if "Cognitive Domain" in raw:
            after_cog = True
            continue
        if not after_cog:
            continue
        if re.match(r"^\s*Item Number:", raw):
            break
        line = left_text(raw).strip()
        if not line or COUNTRY_LINE.match(line):
            continue
        if COG_RE.fullmatch(line) or CONTENT_RE.search(line):
            continue
        if re.match(r"^\s*[A-D]\.\s+", line):
            break
        if re.match(r"^\s*Answer:", line):
            continue
        lines.append(line)
    text = " ".join(lines)
    text = re.sub(r"\s{2,}", " ", text).strip()
    return text


def parse_file(text: str, *, corpus: str, source_url: str, grade: str) -> list[dict]:
    parts = re.split(r"(?=Item Number:\s*M\d{6})", text)
    items: list[dict] = []
    preamble = parts[0]
    for i, part in enumerate(parts[1:], start=1):
        mid = ITEM_ID_RE.search(part)
        if not mid:
            continue
        item_id = mid.group(1).upper()
        lookback = preamble if i == 1 else parts[i - 1]
        header_idx = lookback.rfind("Cognitive Domain")
        header = lookback[header_idx:] if header_idx >= 0 else lookback[-4000:]
        cog_hits = COG_RE.findall(header)
        claim = cog_hits[0].lower() if cog_hits else ""
        content_hits = CONTENT_RE.findall(header)
        content = content_hits[0].title() if content_hits else ""
        if claim not in {"knowing", "applying", "reasoning"}:
            continue

        head = part[:2200]
        letter = CORRECT_LETTER_RE.search(head)
        bullet = CORRECT_BULLET_RE.search(head)
        key = ""
        response_type = "constructed"
        choices = extract_choices(header)
        # Scoring-guide bullets are this item's numeric key. A later
        # "Correct Response: A" belongs to the next selected item.
        if "SCORING" in head and bullet:
            key = bullet.group(1).replace(" ", "").replace(",", "").rstrip(".")
            response_type = "numeric"
            choices = {}
        elif letter:
            key = letter.group(1).upper()
            response_type = "selected"
        elif bullet:
            key = bullet.group(1).replace(" ", "").replace(",", "").rstrip(".")
            response_type = "numeric"
            choices = {}

        intl_hits = INTL_AVG_RE.findall(header)
        if not intl_hits:
            intl_hits = INTL_AVG_RE.findall(lookback[-3500:])
        percent = float(intl_hits[-1]) if intl_hits else None

        stem = stem_from_header(header)
        figure = None
        stem_restored = False
        restoration_note = None
        rest = RESTORATIONS.get(item_id)
        if rest:
            stem = rest["stem"]
            if "choices" in rest:
                choices = dict(rest["choices"])
            if "key" in rest:
                key = rest["key"]
            if "responseType" in rest:
                response_type = rest["responseType"]
            if "figure" in rest:
                figure = rest["figure"]
            stem_restored = True
            restoration_note = rest["restorationNote"]

        if not stem or len(stem) < 12 or COUNTRY_LINE.match(stem):
            stem = f"TIMSS 2011 item {item_id} (stem graphics not recovered from PDF text layer)."
            figure = figure or {"kind": "diagram", "transcription": "graphics-only stem in source PDF"}

        choices = {k: v for k, v in choices.items() if v and len(v) < 80}
        if not key:
            continue

        rec: dict = {
            "id": f"timss2011-{grade}-{item_id}",
            "corpus": corpus,
            "authority": "timss",
            "claim": claim,
            "stem": stem,
            "key": key,
            "responseType": response_type,
            "sourceUrl": source_url,
            "licenseNote": LICENSE,
            "grade": grade,
            "contentDomain": content,
            "role": "target",
        }
        if response_type == "selected" and len(choices) < 2:
            rec["_incomplete"] = "selected-without-choices"
            figure = figure or {
                "kind": "diagram",
                "transcription": "choice graphics missing from PDF text layer",
            }
        if choices and response_type == "selected":
            rec["choices"] = choices
        if percent is not None:
            rec["percentCorrect"] = percent
        if figure:
            rec["figure"] = figure
        if stem_restored:
            rec["stemRestored"] = True
            rec["restorationNote"] = restoration_note
        base = re.sub(r"[A-Z]$", "", item_id)
        if base != item_id:
            rec["clusterId"] = f"timss2011-{grade}-{base}"
        items.append(rec)
    return items


def load_overlay() -> list[dict]:
    if not OVERLAY.exists():
        return []
    data = json.loads(OVERLAY.read_text(encoding="utf-8"))
    return list(data) if isinstance(data, list) else list(data.get("items", []))


def merge_non_timss(existing_path: Path) -> list[dict]:
    if not existing_path.exists():
        return []
    kept: list[dict] = []
    for line in existing_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        if not str(rec.get("id", "")).startswith("timss2011-"):
            kept.append(rec)
    return kept


def main() -> None:
    all_items: list[dict] = []
    g8 = RAW / "TIMSS2011_G8_Math.txt"
    g4 = RAW / "TIMSS2011_G4_Math.txt"
    if g8.exists():
        all_items.extend(
            parse_file(g8.read_text(encoding="utf-8", errors="replace"), corpus="timss2011", source_url=G8_PDF, grade="8")
        )
    if g4.exists():
        all_items.extend(
            parse_file(g4.read_text(encoding="utf-8", errors="replace"), corpus="timss2011", source_url=G4_PDF, grade="4")
        )
    overlay = load_overlay()
    by_id = {it["id"]: it for it in all_items}
    for rec in overlay:
        rec.pop("_incomplete", None)
        by_id[rec["id"]] = rec
    complete: list[dict] = []
    incomplete: list[dict] = []
    for rec in by_id.values():
        if rec.get("_incomplete") or (
            rec.get("responseType") == "selected" and len(rec.get("choices") or {}) < 2
        ):
            incomplete.append(rec)
        else:
            rec.pop("_incomplete", None)
            complete.append(rec)
    others = merge_non_timss(OUT)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    complete_path = ROOT / "data" / "timss_complete.jsonl"
    with complete_path.open("w", encoding="utf-8") as fh:
        for rec in complete:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    with OUT.open("w", encoding="utf-8") as fh:
        for rec in others + complete:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    inc_path = ROOT / "data" / "timss_incomplete.jsonl"
    with inc_path.open("w", encoding="utf-8") as fh:
        for rec in incomplete:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    from collections import Counter

    print(f"wrote {len(complete)} TIMSS items -> {OUT}")
    print(f"incomplete (figures/choices missing) {len(incomplete)} -> {inc_path}")
    print("by claim:", dict(Counter(r["claim"] for r in complete)))
    print("by type:", dict(Counter(r["responseType"] for r in complete)))
    print(
        "selected with 2+ choices:",
        sum(1 for r in complete if r["responseType"] == "selected" and len(r.get("choices") or {}) >= 2),
    )


if __name__ == "__main__":
    main()
