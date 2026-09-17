#!/usr/bin/env python3
"""Parse and score STAAR grade-5 extension forms. Does not overwrite version-1 files.

Parse first, hash preregistration-extended.sha256, then score.
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from addendum_lib import dump_json  # noqa: E402
from ingest_lib import ROOT, dump_jsonl, extract_pdf_text  # noqa: E402
from parse_staar_bulk import parse_items, parse_keys_from_pdf  # noqa: E402
from repair_staar_options import repair_items  # noqa: E402
from run_staar_replication import (  # noqa: E402
    BOOT_SEED,
    N_BOOT,
    POWER_MIN_N,
    n_parseable_numeric_options,
    score_s3_cell,
)
from run_staar_replication_v2 import load_jsonl, prediction_met, source_path  # noqa: E402

OUT_DIR = ROOT / "exports" / "replication-staar"
EXTENDED_ITEMS = OUT_DIR / "items-extended.jsonl"
SHA_PATH = OUT_DIR / "preregistration-extended.sha256"
PREREG_PATH = OUT_DIR / "preregistration.md"

EXTENSION_FORMS: list[dict[str, str]] = [
    {
        "formId": "staar-2017-5-english",
        "year": "2017",
        "grade": "5",
        "testPdf": "data/raw/staar/STAAR_G5-2017-Test-Math-f.pdf",
        "keyPdf": "data/raw/staar/2017_STAAR_Gr5Math_Key_Paper_tagged.pdf",
    },
    {
        "formId": "staar-2018-5-english",
        "year": "2018",
        "grade": "5",
        "testPdf": "data/raw/staar/2018_STAAR_Gr5_Math_Test.PDF",
        "keyPdf": "data/raw/staar/2018_STAAR_Gr5_Math_Key_Paper_tagged.pdf",
    },
]


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_extension_forms() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    items: list[dict[str, Any]] = []
    reports: list[dict[str, Any]] = []
    for form in EXTENSION_FORMS:
        test_path = ROOT / form["testPdf"]
        key_path = ROOT / form["keyPdf"]
        keys = parse_keys_from_pdf(key_path)
        test_text = extract_pdf_text(test_path)
        meta = {
            "grade": "5",
            "year": form["year"],
            "source": f"file:{form['testPdf']}",
        }
        parsed = parse_items(test_text, keys, meta)
        selected = [row for row in parsed if row.get("responseType") == "selected"]
        key_in_choices = [
            row
            for row in selected
            if str(row.get("key")) in (row.get("choices") or {})
        ]
        four_numeric = [row for row in selected if n_parseable_numeric_options(row) == 4]
        stopped = False
        stop_reason = None
        if not keys:
            stopped = True
            stop_reason = "zero_keys_recovered"
        elif keys and not key_in_choices:
            stopped = True
            stop_reason = "keys_not_in_parsed_choices"
        reports.append(
            {
                "formId": form["formId"],
                "year": form["year"],
                "grade": "5",
                "testPdf": form["testPdf"],
                "keyPdf": form["keyPdf"],
                "nKeysRecovered": len(keys),
                "nItemsParsed": len(parsed),
                "nSelected": len(selected),
                "nSelectedKeyInChoices": len(key_in_choices),
                "nFourParseableNumericOptions": len(four_numeric),
                "nParseFailures": len(keys) - len(parsed),
                "stopped": stopped,
                "stopReason": stop_reason,
                "parser": "parse_keys_from_pdf y-gap 4, same as version 1",
            }
        )
        if stopped:
            continue
        repaired = repair_items(parsed, {form["testPdf"]: test_text})
        for row in repaired:
            row["replicationFormId"] = form["formId"]
            row["extensionForm"] = True
        items.extend(repaired)
    return items, reports


def write_extended_items() -> dict[str, Any]:
    repaired_v1 = load_jsonl(OUT_DIR / "items-repaired.jsonl")
    for item in repaired_v1:
        item["extensionForm"] = False
    new_items, reports = parse_extension_forms()
    combined = repaired_v1 + new_items
    dump_jsonl(EXTENDED_ITEMS, combined)
    payload = {
        "writtenAt": utc_now(),
        "nVersion1Repaired": len(repaired_v1),
        "nNewItems": len(new_items),
        "nCombined": len(combined),
        "formReports": reports,
        "newItemIds": [item["id"] for item in new_items],
    }
    dump_json(OUT_DIR / "parse-extended.json", payload)
    return payload


def strip_items(summary: dict[str, Any]) -> dict[str, Any]:
    out = {key: value for key, value in summary.items() if key != "items"}
    out["predictionMetLowerCiAbove025"] = prediction_met(summary)
    out["powerFloorReached"] = int(summary["nFired"]) >= POWER_MIN_N
    out["powerMinimumN"] = POWER_MIN_N
    return out


def score_extended() -> None:
    sha_text = SHA_PATH.read_text(encoding="utf-8")
    sha_fields: dict[str, str] = {}
    for line in sha_text.splitlines():
        if ": " in line:
            key, value = line.split(": ", 1)
            sha_fields[key] = value
    live_sha = sha256_file(PREREG_PATH)
    if sha_fields.get("sha256") != live_sha:
        raise SystemExit(
            f"preregistration.md sha256 {live_sha} does not match {SHA_PATH}"
        )
    items = load_jsonl(EXTENDED_ITEMS)
    version1 = [item for item in items if not item.get("extensionForm")]
    new_items = [item for item in items if item.get("extensionForm")]
    grade5_v1 = [
        item
        for item in version1
        if item.get("claim") == "g5" and item.get("responseType") == "selected"
    ]
    grade5_new = [
        item
        for item in new_items
        if item.get("claim") == "g5" and item.get("responseType") == "selected"
    ]
    grade5_combined = grade5_v1 + grade5_new
    v1_filtered = score_s3_cell(grade5_v1, filtered=True, cell="teks/g5")
    new_filtered = score_s3_cell(grade5_new, filtered=True, cell="teks/g5")
    combined_filtered = score_s3_cell(grade5_combined, filtered=True, cell="teks/g5")
    v1_unfiltered = score_s3_cell(grade5_v1, filtered=False, cell="teks/g5")
    new_unfiltered = score_s3_cell(grade5_new, filtered=False, cell="teks/g5")
    combined_unfiltered = score_s3_cell(grade5_combined, filtered=False, cell="teks/g5")
    parse_meta = json.loads((OUT_DIR / "parse-extended.json").read_text(encoding="utf-8"))
    payload = {
        "writtenAt": utc_now(),
        "version": "extended",
        "preregistration": {
            "path": "exports/replication-staar/preregistration.md",
            "sha256File": "exports/replication-staar/preregistration-extended.sha256",
            "sha256": sha_fields.get("sha256"),
            "utc": sha_fields.get("utc"),
            "powerMinimumN": POWER_MIN_N,
            "bootstrap": {
                "method": "random.Random.randrange",
                "nBoot": N_BOOT,
                "seed": BOOT_SEED,
            },
        },
        "formsParsed": parse_meta["formReports"],
        "nVersion1RepairedItems": len(version1),
        "nNewItems": len(new_items),
        "nGrade5SelectedVersion1": len(grade5_v1),
        "nGrade5SelectedNew": len(grade5_new),
        "nGrade5SelectedCombined": len(grade5_combined),
        "version1RepairedFiltered": strip_items(v1_filtered),
        "newFormsAloneFiltered": strip_items(new_filtered),
        "combinedFiltered": strip_items(combined_filtered),
        "version1RepairedUnfiltered": strip_items(v1_unfiltered),
        "newFormsAloneUnfiltered": strip_items(new_unfiltered),
        "combinedUnfiltered": strip_items(combined_unfiltered),
        "combinedNReaches46": combined_filtered["nFired"] >= POWER_MIN_N,
        "primaryItemIdsCombined": [row["id"] for row in combined_filtered["items"]],
        "primaryItemIdsNew": [row["id"] for row in new_filtered["items"]],
        "notFound": [
            "2015 English g5 math key (test PDF on disk; TEA 2020-12-30 table has no 2015 math form)",
            "2020 English g5 math test and key (not on TEA released-test table; COVID year)",
            "2023 English g5 operational test PDF (key on disk; TEA no longer releases the paper test form)",
        ],
        "cut": [
            "Census English 2019/2021/2022",
            "Spanish, samplers, practice, redesign, rationales, online keys",
            "Scanned PDFs (no OCR)",
        ],
    }
    dump_json(OUT_DIR / "results-extended.json", payload)


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] not in {"parse", "score"}:
        raise SystemExit("usage: run_staar_replication_extended.py parse|score")
    if sys.argv[1] == "parse":
        payload = write_extended_items()
        print(json.dumps({k: payload[k] for k in payload if k != "newItemIds"}, indent=2))
        return
    score_extended()
    print("wrote results-extended.json")


if __name__ == "__main__":
    main()
