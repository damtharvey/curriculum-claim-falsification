#!/usr/bin/env python3
"""Parse NYSED grades 3-8 released-item PDFs using the existing key-map parser."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ingest_lib import RAW, ROOT, dump_jsonl
from ingest_public_corpora import parse_nysed


def year_grade_from_name(name: str) -> tuple[str, str] | None:
    import re

    m = re.search(r"(20[1-2][0-9]).*g(?:rade)?[\s_-]*([3-8])", name.lower())
    if m:
        return m.group(1), m.group(2)
    m = re.search(r"math-g([3-8]).*(20[1-2][0-9])", name.lower())
    if m:
        return m.group(2), m.group(1)
    m = re.search(r"(20[1-2][0-9])-released-items-math-g([3-8])", name.lower())
    if m:
        return m.group(1), m.group(2)
    return None


def main() -> None:
    files = list((RAW / "nysed").glob("*.pdf")) + list(RAW.glob("nysed-*.pdf"))
    rows: list[dict] = []
    seen: set[str] = set()
    txt_dir = RAW / "nysed_txt"
    txt_dir.mkdir(parents=True, exist_ok=True)
    from ingest_lib import extract_pdf_text

    for pdf in files:
        yg = year_grade_from_name(pdf.name)
        if not yg:
            print("skip name", pdf.name)
            continue
        year, grade = yg
        txt = txt_dir / f"{pdf.stem}.txt"
        if not txt.exists():
            try:
                txt.write_text(extract_pdf_text(pdf), encoding="utf-8")
            except Exception as exc:  # noqa: BLE001
                print("fail", pdf, exc)
                continue
        url = f"https://www.nysedregents.org/ei/math/{year}/english/{year}-released-items-math-g{grade}.pdf"
        got = parse_nysed(grade, txt, url, year)
        print(pdf.name, len(got))
        for rec in got:
            rec.setdefault("year", year)
            rec.setdefault("transcriptionMethod", "text-layer")
            rec.setdefault("figureDependent", False)
            if rec["id"] in seen:
                continue
            seen.add(rec["id"])
            rows.append(rec)
    old = ROOT / "data" / "nysed.jsonl"
    if old.exists():
        import json

        for line in old.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            if rec["id"] not in seen:
                seen.add(rec["id"])
                rows.append(rec)
    dump_jsonl(ROOT / "data" / "nysed.jsonl", rows)
    print("wrote", len(rows))


if __name__ == "__main__":
    main()
