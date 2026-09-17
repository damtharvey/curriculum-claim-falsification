#!/usr/bin/env python3
"""Parse NAPLAN numeracy papers + answer keys via pdfplumber tables. Skip figure-only items."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ingest_lib import RAW, ROOT, base_item, choice_ok, clean_ws, dump_jsonl, extract_pdf_text
from parse_helpers import extract_lettered_choices, looks_like_figure

LICENSE = (
    "ACARA NAPLAN public paper tests. "
    "© Australian Curriculum, Assessment and Reporting Authority."
)


def year_from_name(name: str) -> str:
    m = re.search(r"(20[0-2][0-9])", name)
    return m.group(1) if m else "unknown"


def grade_from_name(name: str) -> str:
    m = re.search(r"year[\s_-]*([3579])", name.lower())
    if m:
        return m.group(1)
    m = re.search(r"yr[\s_-]*([3579])", name.lower())
    if m:
        return m.group(1)
    m = re.search(r"y(\d)", name.lower())
    return m.group(1) if m else "unknown"


def paper_kind(name: str) -> str:
    low = name.lower()
    if "non" in low or "no-calculator" in low or "nocalc" in low:
        return "noncalc"
    if "calc" in low:
        return "calc"
    return "num"


def is_answers(name: str) -> bool:
    return "answer" in name.lower() or name.lower().endswith("-key.pdf")


def parse_answers_tables(path: Path, grade: str) -> dict[int, str]:
    import pdfplumber

    keys: dict[int, str] = {}
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables() or []
            for table in tables:
                if not table:
                    continue
                header = [clean_ws(c or "") for c in table[0]]
                num_col = None
                for i, h in enumerate(header):
                    if re.search(r"numeracy", h, re.I):
                        num_col = i
                if num_col is None:
                    # year-level booklet with a Numeracy column somewhere
                    continue
                for row in table[1:]:
                    if not row or not row[0]:
                        continue
                    q_s = clean_ws(str(row[0]))
                    if not re.fullmatch(r"\d{1,2}", q_s):
                        continue
                    if num_col >= len(row) or row[num_col] is None:
                        continue
                    val = clean_ws(str(row[num_col])).lower()
                    if re.fullmatch(r"[a-d]", val):
                        keys[int(q_s)] = val.upper()
    return keys


def parse_paper(text: str, keys: dict[int, str], meta: dict[str, str]) -> list[dict]:
    lines = [ln.rstrip() for ln in text.splitlines()]
    blocks: dict[int, list[str]] = {}
    current: int | None = None
    qstart = re.compile(r"^(\d{1,2})\s+(\S.*)$")
    for ln in lines:
        s = ln.strip()
        if not s or s.startswith("©") or s.lower().startswith("page "):
            continue
        qm = qstart.match(s)
        if qm and int(qm.group(1)) in keys:
            current = int(qm.group(1))
            blocks.setdefault(current, [])
            rest = qm.group(2).strip()
            if rest:
                blocks[current].append(rest)
            continue
        if current is not None:
            blocks[current].append(s)

    rows: list[dict] = []
    for q, key in sorted(keys.items()):
        if not re.fullmatch(r"[A-D]", key):
            continue
        block = blocks.get(q, [])
        stem_parts, choices = extract_lettered_choices(block, "ABCD")
        stem = clean_ws(" ".join(stem_parts))
        if looks_like_figure(stem):
            continue
        if len(choices) != 4 or key not in choices:
            continue
        if len(stem) < 12:
            continue
        if not all(choice_ok(v) and len(v) <= 200 for v in choices.values()):
            continue
        year = meta["year"]
        grade = meta["grade"]
        kind = meta["kind"]
        rec = base_item(
            item_id=f"naplan-{year}-y{grade}-{kind}-q{q}",
            corpus="naplan",
            authority="acara",
            claim=f"y{grade}-numeracy",
            stem=stem,
            key=key,
            response_type="selected",
            source_url=meta["source"],
            license_note=LICENSE,
            year=year,
            grade=grade,
            choices=choices,
            official_tag=f"y{grade}-numeracy",
            transcription_method="text-layer",
        )
        rows.append(rec)
    return rows


def main() -> None:
    files = list((RAW / "naplan").glob("*")) + list(RAW.glob("naplan-*.pdf"))
    papers = [p for p in files if p.suffix.lower() == ".pdf" and not is_answers(p.name)]
    answers = [p for p in files if p.suffix.lower() == ".pdf" and is_answers(p.name)]
    answer_text: dict[tuple[str, str], dict[int, str]] = {}
    for ap in answers:
        y = year_from_name(ap.name)
        g = grade_from_name(ap.name)
        try:
            keys = parse_answers_tables(ap, g)
        except Exception as exc:  # noqa: BLE001
            print("answer fail", ap.name, exc)
            continue
        if len(keys) >= 8:
            answer_text[(y, g)] = keys
            print("answers", ap.name, "y", g, len(keys))

    rows: list[dict] = []
    seen: set[str] = set()
    for paper in papers:
        y = year_from_name(paper.name)
        g = grade_from_name(paper.name)
        keys = answer_text.get((y, g), {})
        if len(keys) < 8:
            print("no keys", paper.name, y, g)
            continue
        try:
            text = extract_pdf_text(paper)
        except Exception as exc:  # noqa: BLE001
            print("fail", paper, exc)
            continue
        meta = {
            "year": y,
            "grade": g,
            "kind": paper_kind(paper.name),
            "source": f"https://www.acara.edu.au/assessment/naplan/naplan-2012-2016-test-papers#{paper.name}",
        }
        got = parse_paper(text, keys, meta)
        print(paper.name, len(got))
        for rec in got:
            if rec["id"] not in seen:
                seen.add(rec["id"])
                rows.append(rec)
    old = ROOT / "data" / "naplan.jsonl"
    if old.exists():
        for line in old.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            if rec["id"] not in seen:
                seen.add(rec["id"])
                rows.append(rec)
    dump_jsonl(ROOT / "data" / "naplan.jsonl", rows)
    print("wrote", len(rows))


if __name__ == "__main__":
    main()
