#!/usr/bin/env python3
"""Recompute masked-stem metrics on all / >=1 / >=2 withheld-quantity populations."""

from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

from masked_stem_followup_lib import (  # noqa: E402
    FIRST_RUN_CLEAR_14B,
    FIRST_RUN_CLEAR_7B,
    NAMED_REPORT_CELLS,
    PLACEHOLDER,
    TIMSS_KNOWING_JUDGMENTS,
    dump_json,
    enrich_cells,
    group_rows,
    load_jsonl,
    paired_increment,
    parse_year,
    stem_chars_masked_share,
    summarize_rows,
    vs_always_b,
    year_bucket,
)
from score_choices_only_local_lm import load_items, load_modal_by_cell, mask_stem  # noqa: E402

OUT_DIR = ROOT / "exports" / "addendum-gpu"
POP_PATH = OUT_DIR / "masked-stem-populations.json"
STATS_PATH = OUT_DIR / "masked-stem-item-mask-stats.jsonl"
TIMSS_EQAO_PATH = OUT_DIR / "masked-stem-timss-eqao-items.json"
POSITION_PATH = OUT_DIR / "position-and-memorization.json"
ITEMS_7B = OUT_DIR / "masked-stem-7b-items.jsonl"
ITEMS_14B = OUT_DIR / "masked-stem-14b-items.jsonl"
OPTIONS_7B = OUT_DIR / "choices-only-local-lm-items.jsonl"
OPTIONS_14B = OUT_DIR / "choices-only-local-lm-14b-items.jsonl"
SUMMARY_7B = OUT_DIR / "masked-stem-7b.json"
SUMMARY_14B = OUT_DIR / "masked-stem-14b.json"
POPULATION_SPECS = (
    ("all", 0),
    ("masked_token_count_ge_1", 1),
    ("masked_token_count_ge_2", 2),
)
LIST_CELLS = (
    "timss::knowing",
    "timss::applying",
    "timss::reasoning",
    "eqao::g6",
)


def attach_mask_stats(
    scored_rows: list[dict[str, Any]],
    items_by_id: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    attached: list[dict[str, Any]] = []
    stats_rows: list[dict[str, Any]] = []
    for row in scored_rows:
        item = items_by_id[str(row["id"])]
        original = str(item.get("stem") or "")
        report = mask_stem(original)
        masked = str(report["masked"])
        token_count = int(report["nPlaceholders"])
        share = stem_chars_masked_share(original, masked)
        stored = row.get("n_placeholders")
        if stored is not None and int(stored) != token_count:
            raise RuntimeError(
                f"placeholder mismatch for {row['id']}: stored={stored} recomputed={token_count}"
            )
        enriched = dict(row)
        enriched["masked_token_count"] = token_count
        enriched["stem_chars_masked_share"] = share
        enriched["masked_stem"] = masked
        attached.append(enriched)
        stats_rows.append(
            {
                "id": row["id"],
                "cell": row.get("cell"),
                "corpus": row.get("corpus"),
                "original_stem_chars": len(original),
                "masked_token_count": token_count,
                "stem_chars_masked_share": share,
                "n_placeholders": token_count,
                "placeholder": PLACEHOLDER,
                "year": parse_year(item),
                "year_bucket": year_bucket(parse_year(item)),
            }
        )
    return attached, stats_rows


def model_metrics(
    rows: list[dict[str, Any]],
    options_by_id: dict[str, dict[str, Any]],
    modal_by_cell: dict[str, dict[str, Any]],
    first_run_clear: tuple[str, ...],
    first_run_summary: dict[str, Any],
) -> dict[str, Any]:
    overall = summarize_rows(rows)
    always_b = vs_always_b(rows)
    enriched = enrich_cells(rows, modal_by_cell)
    per_source = group_rows(rows, "corpus")
    still: dict[str, Any] = {}
    for cell_name in first_run_clear:
        stats = enriched["namedCells"].get(cell_name) or enriched["perCell"].get(cell_name)
        if stats is None:
            n = int(enriched["nByCell"].get(cell_name) or 0)
            still[cell_name] = {
                "n": n,
                "stillClearsOnPopulationModal": False,
                "stillClearsVsFull1487Modal": False,
                "reason": "cell missing or n < 10 on this population",
            }
            continue
        still[cell_name] = {
            "n": stats["n"],
            "passRate": stats["passRate"],
            "ci95": stats["ci95"],
            "chance": stats["chance"],
            "modalFrequencyOnPopulation": stats["modalFrequencyOnPopulation"],
            "modalFrequencyFull1487": stats["modalFrequencyFull1487"],
            "lowerCiAboveChance": stats["lowerCiAboveChance"],
            "clearsWitnessBarOnPopulation": stats["clearsWitnessBarOnPopulation"],
            "clearsWitnessBarVsFull1487Modal": stats["clearsWitnessBarVsFull1487Modal"],
        }
    first_run_overall = (first_run_summary.get("overall") or {}) if first_run_summary else {}
    return {
        "n": overall["n"],
        "overall": overall,
        "vsChance": {
            "chance": overall["chance"],
            "lowerCiAboveChance": overall["lowerCiAboveChance"],
        },
        "vsAlwaysB": always_b,
        "vsOptionsOnly": paired_increment(rows, options_by_id),
        "perSource": per_source,
        "perCell": enriched["perCell"],
        "namedCells": enriched["namedCells"],
        "nByCell": enriched["nByCell"],
        "cellsClearingChanceAndModalOnPopulation": [
            {"cell": row["cell"], "n": row["n"], "passRate": row["passRate"], "ci95": row["ci95"]}
            for row in enriched["cellsClearingChanceAndModalOnPopulation"]
        ],
        "firstRunClearCellsOnThisPopulation": still,
        "firstRunPooledReference": {
            "n": first_run_overall.get("n"),
            "passRate": first_run_overall.get("passRate"),
            "ci95": first_run_overall.get("ci95"),
            "note": "First-run pooled numbers on all 1487; not recomputed here.",
        },
        "chosenLetterCounts": dict(Counter(str(row["chosen_letter"]) for row in rows)),
        "keyLetterCounts": dict(Counter(str(row["key"]) for row in rows)),
    }


def population_block(
    attached_7b: list[dict[str, Any]],
    attached_14b: list[dict[str, Any]],
    min_tokens: int,
    options_7b: dict[str, dict[str, Any]],
    options_14b: dict[str, dict[str, Any]],
    modal_by_cell: dict[str, dict[str, Any]],
    summary_7b: dict[str, Any],
    summary_14b: dict[str, Any],
) -> dict[str, Any]:
    rows_7b = [row for row in attached_7b if int(row["masked_token_count"]) >= min_tokens]
    ids = {str(row["id"]) for row in rows_7b}
    rows_14b = [row for row in attached_14b if str(row["id"]) in ids]
    if len(rows_14b) != len(rows_7b):
        raise RuntimeError(
            f"7B/14B population mismatch at min_tokens={min_tokens}: "
            f"{len(rows_7b)} vs {len(rows_14b)}"
        )
    n_by_cell: dict[str, int] = {}
    for row in rows_7b:
        cell = str(row.get("cell") or "unknown")
        n_by_cell[cell] = n_by_cell.get(cell, 0) + 1
    named_n = {cell: n_by_cell.get(cell, 0) for cell in NAMED_REPORT_CELLS}
    histogram = dict(Counter(int(row["masked_token_count"]) for row in attached_7b))
    return {
        "minMaskedTokenCount": min_tokens,
        "n": len(rows_7b),
        "nByNamedCell": named_n,
        "nByCell": n_by_cell,
        "shareOfAll1487": (len(rows_7b) / len(attached_7b)) if attached_7b else None,
        "meanStemCharsMaskedShare": (
            sum(float(row["stem_chars_masked_share"]) for row in rows_7b) / len(rows_7b)
            if rows_7b
            else 0.0
        ),
        "models": {
            "qwen2.5-7b-instruct": model_metrics(
                rows_7b, options_7b, modal_by_cell, FIRST_RUN_CLEAR_7B, summary_7b
            ),
            "qwen2.5-14b-instruct": model_metrics(
                rows_14b, options_14b, modal_by_cell, FIRST_RUN_CLEAR_14B, summary_14b
            ),
        },
        "maskedTokenCountHistogramOnAll": histogram if min_tokens == 0 else None,
    }


def list_cell_items(
    cell_name: str,
    attached_7b: list[dict[str, Any]],
    rows_14b_by_id: dict[str, dict[str, Any]],
    items_by_id: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    listed: list[dict[str, Any]] = []
    for row in attached_7b:
        if str(row.get("cell")) != cell_name:
            continue
        item = items_by_id[str(row["id"])]
        row_14 = rows_14b_by_id[str(row["id"])]
        record: dict[str, Any] = {
            "id": row["id"],
            "cell": cell_name,
            "masked_token_count": row["masked_token_count"],
            "stem_chars_masked_share": row["stem_chars_masked_share"],
            "original_stem": str(item.get("stem") or ""),
            "masked_stem": row["masked_stem"],
            "options": item.get("choices"),
            "key": row["key"],
            "pick_7b": row["chosen_letter"],
            "correct_7b": bool(row["correct"]),
            "pick_14b": row_14["chosen_letter"],
            "correct_14b": bool(row_14["correct"]),
        }
        if cell_name == "timss::knowing":
            judgment = TIMSS_KNOWING_JUDGMENTS.get(str(row["id"]))
            if judgment is None:
                raise RuntimeError(f"missing TIMSS knowing judgment for {row['id']}")
            record["judgment"] = judgment["verdict"]
            record["judgment_reason"] = judgment["reason"]
        listed.append(record)
    return listed


def main() -> None:
    items_by_id = load_items()
    modal_by_cell = load_modal_by_cell(POSITION_PATH)
    summary_7b = json.loads(SUMMARY_7B.read_text(encoding="utf-8"))
    summary_14b = json.loads(SUMMARY_14B.read_text(encoding="utf-8"))
    raw_7b = load_jsonl(ITEMS_7B)
    raw_14b = load_jsonl(ITEMS_14B)
    if len(raw_7b) != 1487 or len(raw_14b) != 1487:
        raise RuntimeError(f"expected 1487 scored items, got 7B={len(raw_7b)} 14B={len(raw_14b)}")
    attached_7b, stats_rows = attach_mask_stats(raw_7b, items_by_id)
    attached_14b, _stats_14 = attach_mask_stats(raw_14b, items_by_id)
    options_7b = {str(row["id"]): row for row in load_jsonl(OPTIONS_7B)}
    options_14b = {str(row["id"]): row for row in load_jsonl(OPTIONS_14B)}
    rows_14_by_id = {str(row["id"]): row for row in attached_14b}

    STATS_PATH.write_text(
        "".join(json.dumps(row) + "\n" for row in stats_rows),
        encoding="utf-8",
    )

    populations: dict[str, Any] = {}
    for name, min_tokens in POPULATION_SPECS:
        populations[name] = population_block(
            attached_7b,
            attached_14b,
            min_tokens,
            options_7b,
            options_14b,
            modal_by_cell,
            summary_7b,
            summary_14b,
        )

    zero_n = sum(1 for row in attached_7b if int(row["masked_token_count"]) == 0)
    listed_cells: dict[str, Any] = {}
    for cell_name in LIST_CELLS:
        items = list_cell_items(cell_name, attached_7b, rows_14_by_id, items_by_id)
        listed_cells[cell_name] = {
            "n": len(items),
            "nMaskedTokenCountGe1": sum(1 for rec in items if rec["masked_token_count"] >= 1),
            "nMaskedTokenCountGe2": sum(1 for rec in items if rec["masked_token_count"] >= 2),
            "nMaskedTokenCount0": sum(1 for rec in items if rec["masked_token_count"] == 0),
            "items": items,
        }
    knowing = listed_cells["timss::knowing"]["items"]
    judgment_counts = dict(Counter(str(rec["judgment"]) for rec in knowing))
    judgment_counts_ge1 = dict(
        Counter(str(rec["judgment"]) for rec in knowing if rec["masked_token_count"] >= 1)
    )
    listed_cells["timss::knowing"]["judgmentCountsAll35"] = judgment_counts
    listed_cells["timss::knowing"]["judgmentCountsMaskedTokenCountGe1"] = judgment_counts_ge1
    listed_cells["timss::knowing"]["judgmentRule"] = (
        "cue: after v1 masking a human can still pick from option form or leaked numbers "
        "in the choices. knowledge: the tagged fact or operation remains usable from the "
        "unmasked residue (including n=0 stems that never withheld a quantity). "
        "unclear: figure-dependent or a hit that could be recall."
    )

    dump_json(
        TIMSS_EQAO_PATH,
        {
            "label": "exploratory",
            "maskVersion": 1,
            "question": (
                "On TIMSS knowing/applying/reasoning and EQAO grade 6, after v1 quantity "
                "masking, are surviving items cue-readable or knowledge-answerable?"
            ),
            "cells": listed_cells,
            "timssKnowingJudgmentCounts": {
                "all35": judgment_counts,
                "masked_token_count_ge_1": judgment_counts_ge1,
            },
        },
    )

    payload = {
        "status": "partial_populations_from_first_run",
        "label": "exploratory",
        "writtenAt": datetime.now(timezone.utc).isoformat(),
        "primaryPopulation": "masked_token_count_ge_1",
        "robustnessPopulation": "masked_token_count_ge_2",
        "maskVersion": 1,
        "placeholder": PLACEHOLDER,
        "nFirstRun": 1487,
        "nMaskedTokenCount0": zero_n,
        "nMaskedTokenCountGe1": populations["masked_token_count_ge_1"]["n"],
        "nMaskedTokenCountGe2": populations["masked_token_count_ge_2"]["n"],
        "constructNote": (
            "On an item whose stem contained no quantity, nothing was withheld and the "
            "model may be performing the tagged operation. Primary report is items with "
            "masked_token_count >= 1. >= 2 is robustness. First-run pooled 7B 0.405 / "
            "14B 0.425 on all 1487 is the reference, not the primary."
        ),
        "itemMaskStatsPath": str(STATS_PATH.relative_to(ROOT)),
        "timssEqaoItemsPath": str(TIMSS_EQAO_PATH.relative_to(ROOT)),
        "inputs": {
            "items7b": str(ITEMS_7B.relative_to(ROOT)),
            "items14b": str(ITEMS_14B.relative_to(ROOT)),
            "options7b": str(OPTIONS_7B.relative_to(ROOT)),
            "options14b": str(OPTIONS_14B.relative_to(ROOT)),
            "position": str(POSITION_PATH.relative_to(ROOT)),
        },
        "populations": populations,
        "gpuFollowupsPending": [
            "masked-stem-v2-7b",
            "masked-stem-permuted-7b",
            "masked-stem-contamination membership signal",
        ],
    }
    dump_json(POP_PATH, payload)
    ge1 = populations["masked_token_count_ge_1"]
    print(
        json.dumps(
            {
                "out": str(POP_PATH),
                "n0": zero_n,
                "nGe1": populations["masked_token_count_ge_1"]["n"],
                "nGe2": populations["masked_token_count_ge_2"]["n"],
                "namedN": populations["masked_token_count_ge_1"]["nByNamedCell"],
                "7bGe1": ge1["models"]["qwen2.5-7b-instruct"]["overall"],
                "14bGe1": ge1["models"]["qwen2.5-14b-instruct"]["overall"],
                "knowingJudgments": judgment_counts,
                "knowingJudgmentsGe1": judgment_counts_ge1,
                "stillClears7bGe1": ge1["models"]["qwen2.5-7b-instruct"][
                    "firstRunClearCellsOnThisPopulation"
                ],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
