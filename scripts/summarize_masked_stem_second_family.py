#!/usr/bin/env python3
"""Primary-population summary for the second-family masked-stem run."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

from masked_stem_followup_lib import (  # noqa: E402
    NAMED_REPORT_CELLS,
    dump_json,
    enrich_cells,
    load_jsonl,
    paired_increment,
    summarize_rows,
    vs_always_b,
)
from score_choices_only_local_lm import load_modal_by_cell  # noqa: E402

OUT_DIR = ROOT / "exports" / "addendum-gpu"
POSITION_PATH = OUT_DIR / "position-and-memorization.json"
REPORT_CELLS = (
    "nyregents::algebra-i",
    "nyregents::algebra-ii",
    "nyregents::geometry",
    "eqao::g6",
    "timss::knowing",
)


def cell_verdict(stats: dict[str, Any] | None) -> dict[str, Any]:
    if not stats:
        return {"n": 0, "clearsBoth": False, "reason": "missing"}
    lower = stats["ci95"][0]
    return {
        "n": stats["n"],
        "passRate": stats["passRate"],
        "ci95": stats["ci95"],
        "chance": stats["chance"],
        "modalLetterOnPopulation": stats.get("modalLetterOnPopulation"),
        "modalFrequencyOnPopulation": stats.get("modalFrequencyOnPopulation"),
        "lowerCiAboveChance": stats.get("lowerCiAboveChance"),
        "lowerCiAboveModalOnPopulation": stats.get("lowerCiAboveModalOnPopulation"),
        "clearsBoth": bool(stats.get("clearsWitnessBarOnPopulation")),
        "lowerCi": lower,
    }


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--masked-summary", required=True)
    parser.add_argument("--masked-items", required=True)
    parser.add_argument("--options-items", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    summary_path = Path(args.masked_summary)
    items_path = Path(args.masked_items)
    options_path = Path(args.options_items)
    out_path = Path(args.out)
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    masked_rows = load_jsonl(items_path)
    options_by_id = {str(row["id"]): row for row in load_jsonl(options_path)}
    modal_by_cell = load_modal_by_cell(POSITION_PATH)
    overall = summarize_rows(masked_rows)
    enriched = enrich_cells(masked_rows, modal_by_cell)
    increment = paired_increment(masked_rows, options_by_id)
    named = {cell: cell_verdict(enriched["namedCells"].get(cell)) for cell in REPORT_CELLS}
    by_cell_rows: dict[str, list[dict[str, Any]]] = {}
    for row in masked_rows:
        by_cell_rows.setdefault(str(row.get("cell") or "unknown"), []).append(row)
    for cell_name, stats in named.items():
        stats["vsOptionsOnly"] = paired_increment(
            by_cell_rows.get(cell_name, []),
            options_by_id,
        )
    algebra_i = named["nyregents::algebra-i"]
    algebra_ii = named["nyregents::algebra-ii"]
    payload = {
        "status": "complete" if summary.get("status") == "complete" else "partial",
        "label": "exploratory",
        "writtenAt": datetime.now(timezone.utc).isoformat(),
        "population": "masked_token_count_ge_1",
        "modelId": summary.get("modelId"),
        "modelRevision": summary.get("modelRevision"),
        "snapshotPath": summary.get("snapshotPath"),
        "sourceSummary": str(summary_path.relative_to(ROOT))
        if summary_path.is_relative_to(ROOT)
        else str(summary_path),
        "sourceItems": str(items_path.relative_to(ROOT))
        if items_path.is_relative_to(ROOT)
        else str(items_path),
        "optionsOnlyItems": str(options_path.relative_to(ROOT))
        if options_path.is_relative_to(ROOT)
        else str(options_path),
        "n": overall["n"],
        "overall": overall,
        "vsChance": {
            "chance": overall["chance"],
            "lowerCiAboveChance": overall.get("lowerCiAboveChance"),
        },
        "vsAlwaysB": vs_always_b(masked_rows),
        "vsOptionsOnly": increment,
        "namedCells": named,
        "perCell": enriched["perCell"],
        "algebraIClearsBothOnNonQwen": bool(algebra_i.get("clearsBoth")),
        "algebraIIClearsBothOnNonQwen": bool(algebra_ii.get("clearsBoth")),
        "pooledIncrement": {
            "mcnemarN01": increment.get("mcnemarN01"),
            "mcnemarN10": increment.get("mcnemarN10"),
            "maskedMinusOptionsShare": increment.get("shareMaskedOnly"),
            "bothCorrect": increment.get("bothCorrect"),
            "bothWrong": increment.get("bothWrong"),
        },
        "namedReportCells": list(NAMED_REPORT_CELLS),
        "wallTimeSecondsFromScorer": summary.get("wallTimeSeconds"),
    }
    dump_json(out_path, payload)
    print(
        json.dumps(
            {
                "out": str(out_path),
                "n": overall["n"],
                "modelId": payload["modelId"],
                "modelRevision": payload["modelRevision"],
                "algebraI": algebra_i,
                "algebraII": algebra_ii,
                "pooled": overall,
                "increment": increment,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
