#!/usr/bin/env python3
"""Paired original-minus-isomorph differences on the repaired layer. No GPU, no rescoring.

For each model, cell (Algebra I, Algebra II), and population (repaired all, repaired verified),
pairs the saved repaired masked-stem letter with the saved rank-preserving isomorph letter on
items that carry at least one option numeral and whose perturbation succeeded, and reports the
mean difference (perturbed minus original) with the percentile bootstrap of the option-numeral
control (``random.Random.randrange``, 1000 replicates, seed ``31 + n``). Also counts how many
items are unchanged under the arm (no numeral) and how many perturbations failed.

Writes ``exports/repaired-layer/isomorph-paired.json``.
"""

from __future__ import annotations

import json
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
REPAIRED_DIR = ROOT / "exports" / "repaired-layer"
PERTURBED_PATH = REPAIRED_DIR / "perturbed-items-isomorph_rank_preserving.jsonl"
MASKED_PATH = REPAIRED_DIR / "repaired-masked-items.jsonl"
RESULTS_PATH = REPAIRED_DIR / "results.json"
PRIMARY_IDS_PATH = ROOT / "exports" / "addendum-gpu" / "masked-stem-algebra-primary-item-ids.json"
OUTPUT_PATH = REPAIRED_DIR / "isomorph-paired.json"
MODEL_KEYS = ("7b", "14b", "phi4")
MODEL_LABELS = {"7b": "Qwen2.5-7B-Instruct", "14b": "Qwen2.5-14B-Instruct", "phi4": "Phi-4"}
CELLS = {"algebra-i": "algebra_i", "algebra-ii": "algebra_ii"}


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def paired_difference_ci(original: list[int], perturbed: list[int], seed: int, n_boot: int = 1000) -> dict[str, Any]:
    n = len(original)
    diffs = [perturbed[index] - original[index] for index in range(n)]
    point = sum(diffs) / n if n else 0.0
    rng = random.Random(seed)
    samples: list[float] = []
    for _ in range(n_boot):
        total = 0
        for _inner in range(n):
            total += diffs[rng.randrange(n)]
        samples.append(total / n)
    samples.sort()
    low = samples[int(0.025 * (n_boot - 1))]
    high = samples[int(0.975 * (n_boot - 1))]
    return {"n": n, "mean": point, "ci95": [low, high], "includesZero": low <= 0.0 <= high}


def main() -> None:
    results = json.loads(RESULTS_PATH.read_text(encoding="utf-8"))
    perturbed = {str(row["id"]): row for row in load_jsonl(PERTURBED_PATH)}
    masked = {str(row["id"]): row for row in load_jsonl(MASKED_PATH)}
    primary = [str(item_id) for item_id in json.loads(PRIMARY_IDS_PATH.read_text(encoding="utf-8"))]
    id_lists: dict[str, list[str]] = {}
    for cell_key, list_prefix in CELLS.items():
        withheld = [
            item_id for item_id in primary if masked[item_id]["claim"] == cell_key and masked[item_id].get("withheld_quantity")
        ]
        id_lists[f"{list_prefix}_repaired_all"] = withheld
        id_lists[f"{list_prefix}_repaired_verified"] = [
            item_id for item_id in withheld if masked[item_id].get("repair_verdict") == "repaired_verified"
        ]
        for population in ("all", "verified"):
            key = f"{list_prefix}_repaired_{population}"
            if len(id_lists[key]) != results["idLists"][key]:
                raise RuntimeError(f"{key}: rebuilt {len(id_lists[key])} ids, results.json says {results['idLists'][key]}")
    out: dict[str, Any] = {
        "seedRule": "31 + n, 1000 replicates, random.Random.randrange",
        "pairedOn": "items with at least one option numeral whose rank-preserving perturbation succeeded",
        "models": {},
        "writtenAt": datetime.now(timezone.utc).isoformat(),
    }
    for model_key in MODEL_KEYS:
        original = {str(row["id"]): row for row in load_jsonl(REPAIRED_DIR / f"scores-{model_key}-repaired.jsonl")}
        isomorph = {
            str(row["id"]): row
            for row in load_jsonl(REPAIRED_DIR / f"scores-{model_key}-repaired-isomorph_rank_preserving.jsonl")
        }
        model_out: dict[str, Any] = {"label": MODEL_LABELS[model_key], "cells": {}}
        for cell_key, list_prefix in CELLS.items():
            cell_out: dict[str, Any] = {}
            for population in ("all", "verified"):
                ids = id_lists[f"{list_prefix}_repaired_{population}"]
                no_numeral = [item_id for item_id in ids if perturbed[item_id].get("noNumeral")]
                failed = [item_id for item_id in ids if perturbed[item_id].get("perturbFailed")]
                pair_ids = [
                    item_id
                    for item_id in ids
                    if not perturbed[item_id].get("noNumeral")
                    and not perturbed[item_id].get("perturbFailed")
                    and item_id in original
                    and item_id in isomorph
                ]
                original_flags = [int(bool(original[item_id]["correct"])) for item_id in pair_ids]
                perturbed_flags = [int(bool(isomorph[item_id]["correct"])) for item_id in pair_ids]
                paired = paired_difference_ci(original_flags, perturbed_flags, 31 + len(pair_ids))
                paired["nNoNumeral"] = len(no_numeral)
                paired["nPerturbFailed"] = len(failed)
                paired["originalRateOnPaired"] = sum(original_flags) / len(pair_ids) if pair_ids else 0.0
                paired["perturbedRateOnPaired"] = sum(perturbed_flags) / len(pair_ids) if pair_ids else 0.0
                paired["repairVerdicts"] = {
                    verdict: sum(1 for item_id in pair_ids if masked[item_id].get("repair_verdict") == verdict)
                    for verdict in ("repaired_verified", "repaired_unverified")
                }
                cell_out[population] = paired
            model_out["cells"][cell_key] = cell_out
        out["models"][model_key] = model_out
    OUTPUT_PATH.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    for model_key in MODEL_KEYS:
        for cell_key in CELLS:
            for population in ("all", "verified"):
                block = out["models"][model_key]["cells"][cell_key][population]
                print(
                    f"{model_key} {cell_key} {population}: paired n={block['n']} mean={block['mean']:+.3f} "
                    f"ci=[{block['ci95'][0]:+.3f}, {block['ci95'][1]:+.3f}] noNumeral={block['nNoNumeral']} "
                    f"failed={block['nPerturbFailed']}"
                )


if __name__ == "__main__":
    main()
