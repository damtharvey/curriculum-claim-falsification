#!/usr/bin/env python3
"""Inventory STAAR PDFs for a held-out replication set. Does not parse items."""

from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ingest_lib import RAW, ROOT  # noqa: E402
from parse_staar_bulk import grade_from_name, is_key_name, year_from_name  # noqa: E402

OUT_DIR = ROOT / "exports" / "replication-staar"
ITEMS_PATH = ROOT / "data" / "items.jsonl"
MIN_ALNUM_EXTRACTABLE = 200
CENSUS_YEARS = {"2019", "2021", "2022"}
PRIORITY_GRADES = ["5", "3", "4", "6", "7", "8", "alg1"]
EXCLUDED_NAME_PARTS = (
    "rationale",
    "itemanalysis",
    "item-analysis",
    "sampler",
    "practice",
    "redesign",
    "exptested",
    "expectation",
)


def load_census_forms() -> dict[str, Any]:
    forms: dict[tuple[str, str], int] = defaultdict(int)
    n_staar = 0
    with ITEMS_PATH.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            item = json.loads(line)
            if item.get("corpus") != "staar":
                continue
            n_staar += 1
            year = str(item.get("year") or "unknown")
            grade_raw = str(item.get("grade") or "")
            claim = str(item.get("claim") or "")
            if claim == "alg1" or grade_raw == "hs":
                grade = "alg1"
            else:
                grade = grade_raw
            forms[(year, grade)] += 1
    return {
        "nStaarItems": n_staar,
        "forms": {f"{year}|{grade}": count for (year, grade), count in sorted(forms.items())},
        "formTuples": [(year, grade) for year, grade in forms],
    }


def classify_role(name: str) -> str:
    low = name.lower()
    if any(part in low for part in EXCLUDED_NAME_PARTS):
        return "excluded"
    if is_key_name(name):
        return "key"
    if "test" in low or "releasedtest" in low:
        return "test"
    return "other"


def language_from_name(name: str) -> str:
    return "spanish" if "spanish" in name.lower() else "english"


def inspect_pdf(path: Path) -> dict[str, Any]:
    header = path.read_bytes()[:8]
    starts_pdf = header.startswith(b"%PDF")
    size = path.stat().st_size
    record: dict[str, Any] = {
        "path": str(path.relative_to(ROOT)),
        "name": path.name,
        "bytes": size,
        "startsWithPdfHeader": starts_pdf,
        "likelyTruncated": size == 1_048_576,
        "pageCount": None,
        "alnumChars": 0,
        "digitChars": 0,
        "textExtractable": False,
        "openError": None,
    }
    if not starts_pdf:
        record["openError"] = "not-a-pdf-header"
        return record
    try:
        import fitz
    except ImportError as exc:
        record["openError"] = f"pymupdf-missing:{exc}"
        return record
    try:
        document = fitz.open(path)
    except Exception as exc:  # noqa: BLE001
        record["openError"] = str(exc)[:240]
        return record
    try:
        record["pageCount"] = int(document.page_count)
        chunks: list[str] = []
        for page in document:
            chunks.append(page.get_text("text") or "")
        text = "".join(chunks)
        alnum = sum(1 for char in text if char.isalnum())
        digits = sum(1 for char in text if char.isdigit())
        record["alnumChars"] = alnum
        record["digitChars"] = digits
        record["textExtractable"] = alnum >= MIN_ALNUM_EXTRACTABLE
    finally:
        document.close()
    return record


def form_id(year: str, grade: str, language: str) -> str:
    return f"staar-{year}-{grade}-{language}"


def pick_best(paths: list[Path], inspections: dict[str, dict[str, Any]]) -> Path | None:
    if not paths:
        return None

    def rank(path: Path) -> tuple[int, int, int]:
        info = inspections[path.name]
        extractable = 1 if info["textExtractable"] else 0
        pages = int(info["pageCount"] or 0)
        size = int(info["bytes"] or 0)
        return (extractable, pages, size)

    return max(paths, key=rank)


def main() -> None:
    census = load_census_forms()
    census_set = {(year, grade) for year, grade in census["formTuples"]}
    staar_dir = RAW / "staar"
    pdfs = sorted(p for p in staar_dir.iterdir() if p.is_file() and p.suffix.lower() == ".pdf")
    inspections: dict[str, dict[str, Any]] = {}
    pdf_rows: list[dict[str, Any]] = []
    for path in pdfs:
        info = inspect_pdf(path)
        grade = grade_from_name(path.name)
        year = year_from_name(path.name)
        role = classify_role(path.name)
        language = language_from_name(path.name)
        in_census = (year, grade) in census_set
        row = {
            **info,
            "grade": grade,
            "year": year,
            "role": role,
            "language": language,
            "formId": form_id(year, grade, language),
            "censusFormPresent": in_census,
            "censusMembership": (
                "census_form"
                if in_census and language == "english"
                else "census_year_spanish"
                if in_census and language == "spanish"
                else "absent_from_census"
            ),
        }
        inspections[path.name] = row
        pdf_rows.append(row)

    grouped: dict[tuple[str, str, str], dict[str, list[Path]]] = defaultdict(
        lambda: {"test": [], "key": [], "excluded": [], "other": []}
    )
    for row in pdf_rows:
        path = ROOT / row["path"]
        grouped[(row["year"], row["grade"], row["language"])][row["role"]].append(path)

    candidates: list[dict[str, Any]] = []
    paired_forms: list[dict[str, Any]] = []
    for (year, grade, language), buckets in sorted(grouped.items()):
        test_path = pick_best(buckets["test"], inspections)
        key_path = pick_best(buckets["key"], inspections)
        test_info = inspections[test_path.name] if test_path else None
        key_info = inspections[key_path.name] if key_path else None
        in_census = (year, grade) in census_set
        extractable_pair = bool(
            test_info
            and key_info
            and test_info["textExtractable"]
            and key_info["textExtractable"]
        )
        status = "not_a_pair"
        if extractable_pair and language == "english" and not in_census:
            status = "replication_candidate"
        elif extractable_pair and language == "english" and in_census:
            status = "census_form"
        elif extractable_pair and language == "spanish" and in_census:
            status = "census_year_spanish"
        elif extractable_pair and language == "spanish" and not in_census:
            status = "spanish_absent_from_census"
        elif test_path and key_path:
            status = "pair_not_extractable"
        form_row = {
            "formId": form_id(year, grade, language),
            "year": year,
            "grade": grade,
            "language": language,
            "testPdf": None if test_path is None else str(test_path.relative_to(ROOT)),
            "keyPdf": None if key_path is None else str(key_path.relative_to(ROOT)),
            "testExtractable": bool(test_info and test_info["textExtractable"]),
            "keyExtractable": bool(key_info and key_info["textExtractable"]),
            "testPageCount": None if test_info is None else test_info["pageCount"],
            "keyPageCount": None if key_info is None else key_info["pageCount"],
            "testAlnumChars": None if test_info is None else test_info["alnumChars"],
            "keyAlnumChars": None if key_info is None else key_info["alnumChars"],
            "censusFormPresent": in_census,
            "status": status,
            "nExcludedPdfs": len(buckets["excluded"]),
            "nOtherPdfs": len(buckets["other"]),
        }
        paired_forms.append(form_row)
        if status == "replication_candidate":
            candidates.append(form_row)

    def priority_index(grade: str) -> int:
        return PRIORITY_GRADES.index(grade) if grade in PRIORITY_GRADES else 99

    candidates.sort(key=lambda row: (priority_index(row["grade"]), row["year"], row["formId"]))

    n_scanned = sum(
        1
        for row in pdf_rows
        if row["role"] in {"test", "key"}
        and row["startsWithPdfHeader"]
        and not row["textExtractable"]
        and row["openError"] is None
    )
    n_unreadable = sum(1 for row in pdf_rows if row["openError"])
    by_grade_candidates = Counter(row["grade"] for row in candidates)
    payload = {
        "writtenAt": None,
        "source": {
            "staarPdfDir": str((RAW / "staar").relative_to(ROOT)),
            "censusItems": str(ITEMS_PATH.relative_to(ROOT)),
            "nPdfOnDisk": len(pdfs),
            "minAlnumExtractable": MIN_ALNUM_EXTRACTABLE,
            "parser": "scripts/parse_staar_bulk.py grade_from_name/year_from_name/is_key_name; pymupdf text layer only",
        },
        "census": {
            "nStaarItems": census["nStaarItems"],
            "forms": census["forms"],
            "years": sorted({year for year, _grade in census_set}),
            "grades": sorted({grade for _year, grade in census_set}),
            "note": "Census form is year+grade from item ids staar-{year}-{grade}-qN (alg1 uses grade alg1). English 2019/2021/2022 only.",
        },
        "pdfs": pdf_rows,
        "forms": paired_forms,
        "replicationCandidates": candidates,
        "counts": {
            "nPdfs": len(pdfs),
            "nPdfsByRole": dict(Counter(row["role"] for row in pdf_rows)),
            "nTextExtractable": sum(1 for row in pdf_rows if row["textExtractable"]),
            "nScannedOrImageOnly": n_scanned,
            "nUnreadable": n_unreadable,
            "nLikelyTruncated": sum(1 for row in pdf_rows if row["likelyTruncated"]),
            "nCandidateForms": len(candidates),
            "nCandidateFormsByGrade": {grade: by_grade_candidates[grade] for grade in PRIORITY_GRADES},
            "nCandidateGrade5": by_grade_candidates["5"],
        },
        "cut": {
            "spanishCensusYear": "same administration as census, other language; not independent replication",
            "spanishAbsent": "held out of the registered English replication set",
            "samplersPracticeRedesignRationales": "not operational administrations",
            "scanned": "no neural OCR before 16:30 MDT; no CPU OCR",
        },
    }
    from datetime import datetime, timezone

    payload["writtenAt"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / "inventory.json"
    out_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out_path}")
    print("candidates by grade", dict(payload["counts"]["nCandidateFormsByGrade"]))
    print("n scanned/image-only", n_scanned, "truncated", payload["counts"]["nLikelyTruncated"])
    for row in candidates:
        print(
            f"  {row['formId']} test={row['testExtractable']} "
            f"key={row['keyExtractable']} pages={row['testPageCount']}"
        )


if __name__ == "__main__":
    main()
