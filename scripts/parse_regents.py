#!/usr/bin/env python3
"""Parse NY Regents Algebra I / Geometry / Algebra II Part I MC. Do not invent items."""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ingest_lib import RAW, ROOT, base_item, clean_ws, dump_jsonl, extract_pdf_text
from parse_helpers import extract_paren_choices, looks_like_figure

LICENSE = (
    "NYSED Regents Examination released exam and scoring key. Public. "
    "Part I multiple-choice only. Reuse terms follow NYSED."
)
NUM_TO_LETTER = {"1": "A", "2": "B", "3": "C", "4": "D"}
QSTART = re.compile(r"^\s*(\d{1,2})\s+(\S.*)$")


def course_from_path(path: Path) -> str:
    blob = str(path).lower()
    name = path.name.lower()
    if "alg2" in blob or "algebra-ii" in blob or "algebratwo" in blob or "algtwo" in name:
        return "algebra-ii"
    if "geo" in blob or "geometry" in blob or name.startswith("geom"):
        return "geometry"
    return "algebra-i"


def exam_stem(name: str) -> str:
    low = name.lower()
    low = re.sub(r"[-_]?lt\b", "", low)
    low = re.sub(r"\.(pdf|xlsx|xls)$", "", low)
    low = re.sub(r"-(exam|sk|rg|cc|mrsw|scoring|key).*$", "", low)
    low = re.sub(r"(exam|sk|rg)$", "", low)
    return low.strip("-_")


def year_from_name(name: str) -> str:
    m = re.search(r"(20[1-2][0-9])", name)
    if m:
        return m.group(1)
    return "unknown"


def session_from_name(name: str) -> str:
    low = name.lower()
    if "aug" in low or "august" in low:
        return "aug"
    if "june" in low or "jun" in low:
        return "jun"
    if "jan" in low or "january" in low:
        return "jan"
    m = re.search(r"(?:^|[-_])(0?1|0?6|0?8)[-_]?(20[1-2]\d|\d{2})", low)
    if m:
        month = m.group(1).zfill(2)[-2:] if len(m.group(1)) >= 2 else m.group(1)
        return {"1": "jan", "01": "jan", "6": "jun", "06": "jun", "8": "aug", "08": "aug"}.get(
            m.group(1).lstrip("0") or m.group(1), "unk"
        )
    m = re.search(r"(algone|algtwo|geom|geometry)[-]?([168])20", low)
    if m:
        return {"1": "jan", "6": "jun", "8": "aug"}[m.group(2)]
    return "unk"


def is_exam(name: str) -> bool:
    low = name.lower()
    if "lt" in low and "examlt" in low:
        return False
    if any(x in low for x in ("key", "rating", "conversion", "model", "chart", "notice", "-rg", "-cc", "mrsw", "-sk")):
        return False
    return low.endswith(".pdf") and "exam" in low


def is_key_file(name: str) -> bool:
    low = name.lower()
    return ("-sk." in low or low.endswith("sk.xlsx") or low.endswith("sk.xls") or "scoring-key" in low) and not any(
        x in low for x in ("conversion", "chart", "rating-guide", "model")
    )


def parse_key_xlsx(path: Path) -> dict[int, str]:
    import pandas as pd

    keys: dict[int, str] = {}
    try:
        frames = pd.read_excel(path, sheet_name=None, header=None, dtype=str)
    except Exception:
        return keys
    for df in frames.values():
        header_idx = None
        q_col = None
        k_col = None
        t_col = None
        for i, row in df.iterrows():
            cells = [str(c).strip() for c in row.tolist()]
            joined = " ".join(cells).lower()
            if "question number" in joined and "scoring key" in joined:
                header_idx = i
                for j, c in enumerate(cells):
                    cl = c.lower()
                    if "question number" in cl:
                        q_col = j
                    elif "scoring key" in cl:
                        k_col = j
                    elif "question type" in cl:
                        t_col = j
                break
        if header_idx is None or q_col is None or k_col is None:
            continue
        for _, row in df.iloc[header_idx + 1 :].iterrows():
            cells = [str(c).strip() for c in row.tolist()]
            if q_col >= len(cells) or k_col >= len(cells):
                continue
            q_s = cells[q_col]
            k_s = cells[k_col]
            t_s = cells[t_col] if t_col is not None and t_col < len(cells) else "MC"
            if not re.fullmatch(r"\d{1,2}", q_s):
                continue
            q = int(q_s)
            if q > 24:
                continue
            if t_s.upper() not in {"MC", "NAN", ""}:
                if t_s.upper() not in {"MC"}:
                    continue
            if k_s in NUM_TO_LETTER:
                keys[q] = NUM_TO_LETTER[k_s]
    return keys


def parse_key_pdf(path: Path) -> dict[int, str]:
    text = extract_pdf_text(path)
    keys: dict[int, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        m = re.match(r"^(\d{1,2})\s+(?:MC|Multiple Choice)?\s*([1-4])\b", line, re.I)
        if m and int(m.group(1)) <= 24:
            keys[int(m.group(1))] = NUM_TO_LETTER[m.group(2)]
    return keys


def parse_exam(text: str, keys: dict[int, str], meta: dict[str, str]) -> list[dict]:
    cut = re.search(r"Part\s+II", text, re.I)
    body = text[: cut.start()] if cut else text
    lines = [ln.rstrip() for ln in body.splitlines()]
    blocks: dict[int, list[str]] = {}
    current: int | None = None
    for ln in lines:
        s = ln.strip()
        if not s:
            continue
        if s.startswith("Page ") or "Reference Sheet" in s or "Use this space" in s:
            continue
        if re.fullmatch(r"\[\d+\]", s):
            continue
        qm = QSTART.match(s)
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
        if q > 24:
            continue
        stem_parts, choices = extract_paren_choices(blocks.get(q, []))
        stem = clean_ws(" ".join(stem_parts))
        if looks_like_figure(stem):
            continue
        if len(choices) != 4 or not all(1 <= len(v) <= 400 for v in choices.values()):
            continue
        if key not in choices:
            continue
        if len(stem) < 12:
            continue
        rec = base_item(
            item_id=f"nyregents-{meta['course']}-{meta['year']}-{meta['session']}-q{q}",
            corpus="nyregents",
            authority="nyregents",
            claim=meta["course"],
            stem=stem,
            key=key,
            response_type="selected",
            source_url=meta["source"],
            license_note=LICENSE,
            year=meta["year"],
            grade="hs",
            choices=choices,
            official_tag=meta["course"],
            transcription_method="text-layer",
        )
        rows.append(rec)
    return rows


def collect_files() -> list[Path]:
    out: list[Path] = []
    for sub in ("regents-alg1", "regents-geo", "regents-alg2"):
        d = RAW / sub
        if d.exists():
            out.extend(p for p in d.iterdir() if p.is_file())
    return out


def main() -> None:
    files = collect_files()
    exams = [p for p in files if is_exam(p.name)]
    key_files = [p for p in files if is_key_file(p.name)]
    keys_by_stem: dict[str, dict[int, str]] = {}
    for kf in key_files:
        stem = exam_stem(kf.name)
        parsed = parse_key_xlsx(kf) if kf.suffix.lower() in {".xlsx", ".xls"} else parse_key_pdf(kf)
        if len(parsed) >= 10:
            keys_by_stem[stem] = parsed
            print("key", kf.name, len(parsed))
    rows: list[dict] = []
    seen: set[str] = set()
    for exam in exams:
        course = course_from_path(exam)
        year = year_from_name(exam.name)
        session = session_from_name(exam.name)
        stem = exam_stem(exam.name)
        keys = keys_by_stem.get(stem, {})
        if len(keys) < 10:
            print("few keys", exam.name, stem, len(keys))
            continue
        try:
            text = extract_pdf_text(exam)
        except Exception as exc:  # noqa: BLE001
            print("exam fail", exam, exc)
            continue
        meta = {
            "course": course,
            "year": year,
            "session": session,
            "source": f"https://www.nysedregents.org/{exam.name}",
        }
        got = parse_exam(text, keys, meta)
        print(f"{exam.name}: {len(got)} / {len(keys)} keys")
        for rec in got:
            if rec["id"] in seen:
                continue
            seen.add(rec["id"])
            rows.append(rec)
    out = ROOT / "data" / "nyregents.jsonl"
    dump_jsonl(out, rows)
    print(f"wrote {len(rows)} -> {out}")


if __name__ == "__main__":
    main()
