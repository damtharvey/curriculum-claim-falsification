#!/usr/bin/env python3
"""Position baseline and recency/memorization analysis for the choices-only local LM."""

from __future__ import annotations

import json
import random
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ITEMS_PATH = ROOT / "data" / "items.jsonl"
KEEP_IDS_PATH = ROOT / "exports" / "addendum" / "choices-only-clean-item-ids.json"
FILTER_PATH = ROOT / "exports" / "addendum" / "choices-only-clean-filter.json"
LOCAL_SUMMARY_PATH = ROOT / "exports" / "addendum-gpu" / "choices-only-local-lm.json"
LOCAL_ITEMS_PATH = ROOT / "exports" / "addendum-gpu" / "choices-only-local-lm-items.jsonl"
COMPOSER_ITEMS_PATH = ROOT / "exports" / "choices-only" / "scored.jsonl"
OUT_PATH = ROOT / "exports" / "addendum-gpu" / "position-and-memorization.json"

YEAR_IN_TEXT_RE = re.compile(r"(?:^|[-_])((?:19|20)\d{2})(?:[-_]|$)")
YEAR_IN_CORPUS_RE = re.compile(r"((?:19|20)\d{2})")
HIGHLIGHTED_CELLS = ("nyregents::algebra-i", "teks::g3", "teks::g7")
BUCKET_ORDER = ("before_2015", "2015_to_2019", "2020_and_later")


def bootstrap_ci(flags: list[int], n_boot: int = 1000, seed: int = 11) -> tuple[float, float]:
    """Percentile bootstrap matching scripts/score_choices_only.py (Random.randrange)."""
    if not flags:
        return (0.0, 0.0)
    rng = random.Random(seed)
    n = len(flags)
    samples: list[float] = []
    for _ in range(n_boot):
        tot = 0
        for _i in range(n):
            tot += flags[rng.randrange(n)]
        samples.append(tot / n)
    samples.sort()
    lo = samples[int(0.025 * (n_boot - 1))]
    hi = samples[int(0.975 * (n_boot - 1))]
    return (lo, hi)


def summarize_flags(flags: list[int], chances: list[float] | None = None) -> dict[str, Any]:
    n = len(flags)
    rate = sum(flags) / n if n else 0.0
    chance = (sum(chances) / n) if chances and n else None
    ci = bootstrap_ci(flags, 1000, 21 + n) if n else (0.0, 0.0)
    out: dict[str, Any] = {
        "n": n,
        "passRate": rate,
        "ci95": [ci[0], ci[1]],
    }
    if chance is not None:
        out["chance"] = chance
        out["ciExcludesChance"] = n >= 10 and ci[0] > chance
    return out


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def load_items() -> dict[str, dict[str, Any]]:
    by_id: dict[str, dict[str, Any]] = {}
    with ITEMS_PATH.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            item = json.loads(line)
            by_id[str(item["id"])] = item
    return by_id


def parse_year(item: dict[str, Any]) -> int | None:
    raw = item.get("year")
    if raw is not None:
        text = str(raw).strip()
        if re.fullmatch(r"(19|20)\d{2}", text):
            return int(text)
    item_id = str(item.get("id") or "")
    match = YEAR_IN_TEXT_RE.search(item_id)
    if match:
        return int(match.group(1))
    corpus = str(item.get("corpus") or "")
    match = YEAR_IN_CORPUS_RE.search(corpus)
    if match:
        return int(match.group(1))
    match = YEAR_IN_CORPUS_RE.search(item_id)
    if match:
        return int(match.group(0))
    return None


def year_bucket(year: int | None) -> str:
    if year is None:
        return "unparsed"
    if year < 2015:
        return "before_2015"
    if year <= 2019:
        return "2015_to_2019"
    return "2020_and_later"


def modal_letter(keys: list[str]) -> tuple[str, int, float]:
    counts = Counter(keys)
    if not counts:
        return ("", 0, 0.0)
    max_count = max(counts.values())
    letter = min(letter for letter, count in counts.items() if count == max_count)
    return (letter, max_count, max_count / len(keys))


def rates_fall_with_recency(bucket_stats: dict[str, dict[str, Any]]) -> dict[str, Any]:
    present = [name for name in BUCKET_ORDER if name in bucket_stats and bucket_stats[name]["n"] > 0]
    rates = [bucket_stats[name]["passRate"] for name in present]
    strictly_falling = len(rates) >= 2 and all(rates[i] > rates[i + 1] for i in range(len(rates) - 1))
    weakly_falling = len(rates) >= 2 and all(rates[i] >= rates[i + 1] for i in range(len(rates) - 1))
    newest = bucket_stats.get("2020_and_later", {}).get("passRate")
    oldest = bucket_stats.get("before_2015", {}).get("passRate")
    newest_minus_oldest = None
    if newest is not None and oldest is not None:
        newest_minus_oldest = newest - oldest
    return {
        "bucketOrder": list(present),
        "ratesInOrder": rates,
        "strictlyFalling": strictly_falling,
        "weaklyMonotoneNonincreasing": weakly_falling,
        "newestMinusOldest": newest_minus_oldest,
        "newestBelowOldest": bool(
            newest_minus_oldest is not None and newest_minus_oldest < 0
        ),
        "fallsWithRecency": strictly_falling,
    }


def attach_year(row: dict[str, Any], item: dict[str, Any] | None) -> dict[str, Any]:
    year = parse_year(item) if item is not None else None
    return {
        "year": year,
        "yearBucket": year_bucket(year),
        "yearSource": (
            "field"
            if item is not None and item.get("year") is not None and parse_year({"year": item.get("year")}) == year
            else "id_or_corpus"
            if year is not None
            else None
        ),
    }


def group_rate(
    rows: list[dict[str, Any]],
    key_name: str,
    correct_field: str,
    chance_from: str | None = None,
) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get(key_name) or "unknown")].append(row)
    out: dict[str, dict[str, Any]] = {}
    for name, group in sorted(grouped.items()):
        flags = [int(row[correct_field]) for row in group]
        chances = None
        if chance_from:
            chances = [1.0 / int(row[chance_from]) for row in group]
        out[name] = summarize_flags(flags, chances)
    return out


def decomposition(
    rows: list[dict[str, Any]],
    modal_by_cell: dict[str, str],
    correct_field: str,
) -> dict[str, Any]:
    n = len(rows)
    correct_rows = [row for row in rows if row[correct_field]]
    n_correct = len(correct_rows)
    n_correct_modal = sum(
        int(str(row["key"]) == modal_by_cell.get(str(row["cell"]))) for row in correct_rows
    )
    non_modal = [row for row in rows if str(row["key"]) != modal_by_cell.get(str(row["cell"]))]
    non_modal_flags = [int(row[correct_field]) for row in non_modal]
    non_modal_chances = [1.0 / int(row["n_options"]) for row in non_modal]
    non_modal_summary = summarize_flags(non_modal_flags, non_modal_chances)
    return {
        "nItems": n,
        "nCorrect": n_correct,
        "nCorrectOnModalKey": n_correct_modal,
        "shareOfCorrectOnModalKey": (n_correct_modal / n_correct) if n_correct else None,
        "nNonModalKey": len(non_modal),
        "nonModalKey": non_modal_summary,
        "nonModalRateVsChance": {
            "passRate": non_modal_summary["passRate"],
            "chance": non_modal_summary.get("chance"),
            "aboveChance": (
                non_modal_summary["passRate"] > non_modal_summary["chance"]
                if non_modal_summary.get("chance") is not None
                else None
            ),
            "lowerCiAboveChance": bool(non_modal_summary.get("ciExcludesChance")),
        },
    }


def main() -> None:
    local_summary = json.loads(LOCAL_SUMMARY_PATH.read_text(encoding="utf-8"))
    keep_ids = [str(item_id) for item_id in json.loads(KEEP_IDS_PATH.read_text(encoding="utf-8"))]
    sibling_filter = json.loads(FILTER_PATH.read_text(encoding="utf-8"))
    items_by_id = load_items()
    local_rows = load_jsonl(LOCAL_ITEMS_PATH)
    composer_rows_raw = load_jsonl(COMPOSER_ITEMS_PATH)

    for row in local_rows:
        item = items_by_id[str(row["id"])]
        row["source"] = str(item.get("corpus") or row.get("corpus") or "unknown")
        if "cell" not in row:
            row["cell"] = f"{item.get('authority')}::{item.get('claim')}"
        year_info = attach_year(row, item)
        row.update(year_info)
        row["n_options"] = int(row["n_options"])
        row["correct"] = bool(row["correct"])
        row["key"] = str(row["key"]).strip().upper()

    keys_by_cell: dict[str, list[str]] = defaultdict(list)
    for row in local_rows:
        keys_by_cell[str(row["cell"])].append(row["key"])

    cell_modals: dict[str, dict[str, Any]] = {}
    modal_letter_by_cell: dict[str, str] = {}
    for cell_name, keys in keys_by_cell.items():
        letter, count, frequency = modal_letter(keys)
        modal_letter_by_cell[cell_name] = letter
        cell_modals[cell_name] = {
            "letter": letter,
            "count": count,
            "frequency": frequency,
            "n": len(keys),
            "keyCounts": dict(Counter(keys)),
        }

    per_cell_position: list[dict[str, Any]] = []
    flagged: list[dict[str, Any]] = []
    highlighted: dict[str, Any] = {}
    stored_cells = local_summary.get("perCell") or {}
    for cell_name, modal in sorted(cell_modals.items()):
        cell_rows = [row for row in local_rows if str(row["cell"]) == cell_name]
        if len(cell_rows) < 10:
            continue
        flags = [int(row["correct"]) for row in cell_rows]
        chances = [1.0 / int(row["n_options"]) for row in cell_rows]
        model_stats = summarize_flags(flags, chances)
        stored = stored_cells.get(cell_name)
        if stored is not None:
            if stored["n"] != model_stats["n"] or stored["passRate"] != model_stats["passRate"]:
                raise RuntimeError(f"Recomputed cell stats mismatch for {cell_name}")
        lower_ci = model_stats["ci95"][0]
        chance = model_stats["chance"]
        modal_frequency = modal["frequency"]
        lower_ci_above_chance = lower_ci > chance
        lower_ci_above_modal = lower_ci > modal_frequency
        rate_above_modal = model_stats["passRate"] > modal_frequency
        record = {
            "cell": cell_name,
            "n": modal["n"],
            "modalLetter": modal["letter"],
            "modalCount": modal["count"],
            "modalFrequency": modal_frequency,
            "keyCounts": modal["keyCounts"],
            "modelPassRate": model_stats["passRate"],
            "modelCi95": model_stats["ci95"],
            "chance": chance,
            "lowerCiAboveChance": lower_ci_above_chance,
            "lowerCiAboveModalFrequency": lower_ci_above_modal,
            "rateAboveModalFrequency": rate_above_modal,
            "beatsPosition": lower_ci_above_modal,
            "flagLowerCiAboveChanceNotModal": lower_ci_above_chance and not lower_ci_above_modal,
        }
        per_cell_position.append(record)
        if record["flagLowerCiAboveChanceNotModal"]:
            flagged.append(record)
        if cell_name in HIGHLIGHTED_CELLS:
            highlighted[cell_name] = {
                **record,
                "verdict": (
                    "beats_position"
                    if lower_ci_above_modal
                    else "does_not_beat_position"
                ),
            }

    pooled_decomp = decomposition(local_rows, modal_letter_by_cell, "correct")
    large_cell_rows = [row for row in local_rows if cell_modals[str(row["cell"])]["n"] >= 10]
    large_cell_decomp = decomposition(large_cell_rows, modal_letter_by_cell, "correct")
    per_source_decomp: dict[str, Any] = {}
    by_source_rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in local_rows:
        by_source_rows[str(row["source"])].append(row)
    for source_name, source_rows in sorted(by_source_rows.items()):
        per_source_decomp[source_name] = decomposition(
            source_rows, modal_letter_by_cell, "correct"
        )

    local_by_source = group_rate(local_rows, "source", "correct", "n_options")
    local_by_bucket = group_rate(local_rows, "yearBucket", "correct", "n_options")
    local_source_bucket: dict[str, dict[str, Any]] = {}
    for source_name, source_rows in sorted(by_source_rows.items()):
        local_source_bucket[source_name] = group_rate(
            source_rows, "yearBucket", "correct", "n_options"
        )

    composer_rows: list[dict[str, Any]] = []
    for raw in composer_rows_raw:
        item_id = str(raw.get("itemId") or raw.get("id"))
        item = items_by_id.get(item_id)
        n_options = int(raw.get("nOptions") or raw.get("n_options") or 4)
        if item is not None and item.get("choices"):
            n_options = len(item["choices"])
        key = str(item.get("key") if item is not None else raw.get("key") or "").strip().upper()
        cell = (
            f"{item.get('authority')}::{item.get('claim')}"
            if item is not None
            else f"unknown::{raw.get('claim')}"
        )
        year_info = attach_year({"id": item_id}, item)
        composer_rows.append(
            {
                "id": item_id,
                "source": str((item or {}).get("corpus") or raw.get("corpus") or "unknown"),
                "cell": cell,
                "key": key,
                "n_options": n_options,
                "correct": bool(raw.get("correct")),
                **year_info,
            }
        )

    composer_by_source = group_rate(composer_rows, "source", "correct", "n_options")
    composer_by_bucket = group_rate(composer_rows, "yearBucket", "correct", "n_options")

    local_by_id = {str(row["id"]): row for row in local_rows}
    overlap_rows: list[dict[str, Any]] = []
    for composer_row in composer_rows:
        local_row = local_by_id.get(composer_row["id"])
        if local_row is None:
            continue
        overlap_rows.append(
            {
                "id": composer_row["id"],
                "source": local_row["source"],
                "yearBucket": local_row["yearBucket"],
                "year": local_row["year"],
                "n_options": local_row["n_options"],
                "local_correct": int(local_row["correct"]),
                "composer_correct": int(composer_row["correct"]),
            }
        )

    overlap_local_by_bucket: dict[str, dict[str, Any]] = {}
    overlap_composer_by_bucket: dict[str, dict[str, Any]] = {}
    gap_by_bucket: dict[str, Any] = {}
    overlap_grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in overlap_rows:
        overlap_grouped[str(row["yearBucket"])].append(row)
    for bucket_name in list(BUCKET_ORDER) + ["unparsed"]:
        group = overlap_grouped.get(bucket_name, [])
        if not group and bucket_name == "unparsed":
            continue
        local_flags = [int(row["local_correct"]) for row in group]
        composer_flags = [int(row["composer_correct"]) for row in group]
        chances = [1.0 / int(row["n_options"]) for row in group]
        local_summary_bucket = summarize_flags(local_flags, chances)
        composer_summary_bucket = summarize_flags(composer_flags, chances)
        overlap_local_by_bucket[bucket_name] = local_summary_bucket
        overlap_composer_by_bucket[bucket_name] = composer_summary_bucket
        gap_by_bucket[bucket_name] = {
            "n": len(group),
            "composerMinusLocal": composer_summary_bucket["passRate"] - local_summary_bucket["passRate"],
            "composerPassRate": composer_summary_bucket["passRate"],
            "localPassRate": local_summary_bucket["passRate"],
            "chance": local_summary_bucket.get("chance"),
        }

    overlap_local_all = summarize_flags(
        [int(row["local_correct"]) for row in overlap_rows],
        [1.0 / int(row["n_options"]) for row in overlap_rows],
    )
    overlap_composer_all = summarize_flags(
        [int(row["composer_correct"]) for row in overlap_rows],
        [1.0 / int(row["n_options"]) for row in overlap_rows],
    )

    overall_flags = [int(row["correct"]) for row in local_rows]
    overall_chances = [1.0 / int(row["n_options"]) for row in local_rows]
    recomputed_overall = summarize_flags(overall_flags, overall_chances)
    stored_overall = local_summary["overall"]
    keep_list_n = len(keep_ids)
    sanity = {
        "cleanKeepListN": keep_list_n,
        "siblingFilterNKept": sibling_filter.get("nKept"),
        "summaryNCleanKeepList": local_summary.get("nCleanKeepList"),
        "nScored": len(local_rows),
        "summaryNScored": stored_overall.get("n"),
        "recomputedPassRate": recomputed_overall["passRate"],
        "summaryPassRate": stored_overall.get("passRate"),
        "recomputedChance": recomputed_overall["chance"],
        "summaryChance": stored_overall.get("chance"),
        "recomputedCi95": recomputed_overall["ci95"],
        "summaryCi95": stored_overall.get("ci95"),
        "keepListMatchesSummary": keep_list_n == local_summary.get("nCleanKeepList")
        and keep_list_n == sibling_filter.get("nKept"),
        "nScoredMatchesSummary": len(local_rows) == stored_overall.get("n")
        and len(local_rows) == local_summary.get("nScorable"),
        "passRateMatchesExactly": recomputed_overall["passRate"] == stored_overall.get("passRate"),
        "chanceMatchesExactly": recomputed_overall["chance"] == stored_overall.get("chance"),
        "ciMatchesExactly": recomputed_overall["ci95"] == stored_overall.get("ci95"),
    }
    sanity["allExact"] = (
        sanity["keepListMatchesSummary"]
        and sanity["nScoredMatchesSummary"]
        and sanity["passRateMatchesExactly"]
        and sanity["chanceMatchesExactly"]
        and sanity["ciMatchesExactly"]
    )
    if not sanity["allExact"]:
        raise RuntimeError(f"Sanity mismatch against on-disk 7B JSON: {json.dumps(sanity, indent=2)}")

    local_recency = rates_fall_with_recency(local_by_bucket)
    composer_recency = rates_fall_with_recency(composer_by_bucket)
    overlap_local_recency = rates_fall_with_recency(overlap_local_by_bucket)
    overlap_composer_recency = rates_fall_with_recency(overlap_composer_by_bucket)

    payload: dict[str, Any] = {
        "label": "exploratory",
        "question": (
            "On the clean choices-only 7B run, do cells that beat chance also beat the "
            "per-cell modal-letter baseline, and does accuracy fall on more recent exams?"
        ),
        "inputs": {
            "localSummary": str(LOCAL_SUMMARY_PATH.relative_to(ROOT)),
            "localItems": str(LOCAL_ITEMS_PATH.relative_to(ROOT)),
            "cleanKeepList": str(KEEP_IDS_PATH.relative_to(ROOT)),
            "cleanFilter": str(FILTER_PATH.relative_to(ROOT)),
            "composerItems": str(COMPOSER_ITEMS_PATH.relative_to(ROOT)),
            "items": str(ITEMS_PATH.relative_to(ROOT)),
            "modelId": local_summary.get("modelId"),
            "modelRevision": local_summary.get("modelRevision"),
        },
        "sanity": sanity,
        "yearParse": {
            "rule": (
                "Prefer item.year when it is a 19xx/20xx string. Else take a year "
                "bounded by start/hyphen/underscore in the id. Else a 19xx/20xx in corpus "
                "or a leftover 19xx/20xx in the id. nyregents ...-unknown-unk-... ids are unparsed."
            ),
            "nLocalScored": len(local_rows),
            "nLocalParseable": sum(int(row["yearBucket"] != "unparsed") for row in local_rows),
            "nLocalUnparsed": sum(int(row["yearBucket"] == "unparsed") for row in local_rows),
            "unparsedIds": [row["id"] for row in local_rows if row["yearBucket"] == "unparsed"],
            "buckets": BUCKET_ORDER,
            "note": (
                "Regents exams before 2015 are widely posted. EQAO 2023 is in 2020_and_later. "
                "Unparsed rows are excluded from recency-rate comparisons but counted separately."
            ),
        },
        "perCellPositionBaseline": {
            "nCellsNge10": len(per_cell_position),
            "tieBreak": "Among letters tied for the highest key count, take the earliest letter in A-E order.",
            "cells": per_cell_position,
            "flaggedLowerCiAboveChanceNotModal": [
                {
                    "cell": row["cell"],
                    "n": row["n"],
                    "modelPassRate": row["modelPassRate"],
                    "modelCi95": row["modelCi95"],
                    "chance": row["chance"],
                    "modalLetter": row["modalLetter"],
                    "modalFrequency": row["modalFrequency"],
                }
                for row in flagged
            ],
            "highlightedCells": highlighted,
        },
        "decomposition": {
            "modalDefinedOn": "cell (scored clean set; all cell sizes, including n < 10)",
            "pooled": pooled_decomp,
            "pooledCellsNge10": large_cell_decomp,
            "perSource": per_source_decomp,
            "note": (
                "shareOfCorrectOnModalKey is among items the model got right. "
                "nonModalKey.passRate is accuracy on items whose key is not that cell's modal letter, "
                "the options-content signal net of always guessing the cell's most common key."
            ),
        },
        "memorization": {
            "local": {
                "bySource": local_by_source,
                "byYearBucket": local_by_bucket,
                "bySourceThenYearBucket": local_source_bucket,
                "fallsWithRecency": local_recency,
            },
            "composer": {
                "model": "composer-2.5-fast",
                "nRowsOnDisk": len(composer_rows),
                "bySource": composer_by_source,
                "byYearBucket": composer_by_bucket,
                "fallsWithRecency": composer_recency,
            },
            "overlapSameItems": {
                "nOverlap": len(overlap_rows),
                "local": overlap_local_all,
                "composer": overlap_composer_all,
                "composerMinusLocal": overlap_composer_all["passRate"] - overlap_local_all["passRate"],
                "byYearBucketLocal": overlap_local_by_bucket,
                "byYearBucketComposer": overlap_composer_by_bucket,
                "gapComposerMinusLocal": gap_by_bucket,
                "localFallsWithRecency": overlap_local_recency,
                "composerFallsWithRecency": overlap_composer_recency,
            },
        },
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(
        {
            "out": str(OUT_PATH),
            "sanityAllExact": sanity["allExact"],
            "highlighted": {
                name: {
                    "rate": row["modelPassRate"],
                    "modalFrequency": row["modalFrequency"],
                    "verdict": row["verdict"],
                    "ci": row["modelCi95"],
                }
                for name, row in highlighted.items()
            },
            "flagged": [row["cell"] for row in flagged],
            "nonModal": pooled_decomp["nonModalKey"],
            "localBuckets": {k: local_by_bucket[k]["passRate"] for k in local_by_bucket},
            "overlapGaps": {k: v["composerMinusLocal"] for k, v in gap_by_bucket.items()},
        },
        indent=2,
    ))


if __name__ == "__main__":
    main()
