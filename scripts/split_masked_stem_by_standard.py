#!/usr/bin/env python3
"""Split the claimed masked-stem Algebra I and Algebra II rows by the verb class of the publisher's tag. No GPU.

The verb class of every CCSS cluster is the pre-registered table in
``exports/standards-split/preregistration.md`` (copied here as data). The script refuses to
run if that file no longer matches ``preregistration.sha256``. Rows are recomputed from the
saved per-item predictions with the addendum's bootstrap; the ``all`` and ``faithful``
subsets must reproduce the addendum and the print-faithful rows exactly.
"""

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from print_fidelity_lib import (
    CELL_ALGEBRA_I,
    CELL_ALGEBRA_II,
    FIDELITY_ITEMS_PATH,
    VERDICT_FAITHFUL,
    dump_json,
    load_jsonl,
)
from rescore_print_faithful_rows import GPU_DIR, LM_MODELS, MIN_N, RESCORED_PATH, lm_row, load_predictions

ROOT = Path(__file__).resolve().parent.parent
SPLIT_DIR = ROOT / "exports" / "standards-split"
PREREG_PATH = SPLIT_DIR / "preregistration.md"
PREREG_SHA_PATH = SPLIT_DIR / "preregistration.sha256"
ITEM_STANDARDS_PATH = SPLIT_DIR / "item-standards.jsonl"
STANDARDS_TEXT_PATH = SPLIT_DIR / "standards-text.json"
COVERAGE_PATH = SPLIT_DIR / "coverage.json"
OUTPUT_PATH = SPLIT_DIR / "execution-subset.json"
TABLES_PATH = SPLIT_DIR / "execution-subset-tables.md"

EXECUTION = "execution"
RECOGNITION = "recognition_or_interpretation"
MIXED = "mixed"

# Pre-registered classification (preregistration.md, section "Classification of every cluster in use").
CLUSTER_CLASS: dict[str, tuple[str, bool]] = {
    "A-APR.A": (EXECUTION, True),
    "A-APR.B": (RECOGNITION, False),
    "A-APR.C": (EXECUTION, False),
    "A-APR.D": (EXECUTION, True),
    "A-CED.A": (EXECUTION, True),
    "A-REI.A": (RECOGNITION, False),
    "A-REI.B": (EXECUTION, True),
    "A-REI.C": (EXECUTION, False),
    "A-REI.D": (EXECUTION, False),
    "A-SSE.A": (RECOGNITION, False),
    "A-SSE.B": (EXECUTION, True),
    "F-BF.A": (EXECUTION, True),
    "F-BF.B": (EXECUTION, True),
    "F-IF.A": (RECOGNITION, False),
    "F-IF.B": (RECOGNITION, False),
    "F-IF.C": (RECOGNITION, False),
    "F-LE.A": (MIXED, False),
    "F-LE.B": (RECOGNITION, False),
    "F-TF.A": (RECOGNITION, False),
    "F-TF.C": (MIXED, False),
    "G-GPE.A": (EXECUTION, True),
    "N-CN.A": (EXECUTION, False),
    "N-CN.C": (EXECUTION, True),
    "N-Q.A": (MIXED, False),
    "N-RN.A": (MIXED, False),
    "N-RN.B": (RECOGNITION, False),
    "S-CP.A": (RECOGNITION, False),
    "S-CP.B": (EXECUTION, True),
    "S-IC.A": (RECOGNITION, False),
    "S-IC.B": (RECOGNITION, False),
    "S-ID.A": (MIXED, False),
    "S-ID.B": (MIXED, False),
    "S-ID.C": (RECOGNITION, False),
}

CELLS: dict[str, tuple[str, str]] = {
    CELL_ALGEBRA_I: ("nyregents::algebra-i", "Algebra I"),
    CELL_ALGEBRA_II: ("nyregents::algebra-ii", "Algebra II"),
}
SUBSET_ORDER = (
    "all",
    "faithful",
    EXECUTION,
    f"{EXECUTION}_and_faithful",
    "execution_strict",
    "execution_strict_and_faithful",
    RECOGNITION,
    f"{RECOGNITION}_and_faithful",
    MIXED,
    f"{MIXED}_and_faithful",
)


def check_preregistration() -> str:
    recorded = PREREG_SHA_PATH.read_text(encoding="utf-8").split()[0]
    actual = hashlib.sha256(PREREG_PATH.read_bytes()).hexdigest()
    if recorded != actual:
        raise RuntimeError(f"preregistration.md sha256 {actual} does not match recorded {recorded}")
    return recorded


def load_item_classes() -> dict[str, dict[str, Any]]:
    standards_text = json.loads(STANDARDS_TEXT_PATH.read_text(encoding="utf-8"))
    codes_in_text = set(standards_text["clusters"])
    if set(CLUSTER_CLASS) != codes_in_text:
        raise RuntimeError(f"classified codes {sorted(set(CLUSTER_CLASS) ^ codes_in_text)} differ from standards-text.json")
    rows = load_jsonl(ITEM_STANDARDS_PATH)
    by_id: dict[str, dict[str, Any]] = {}
    for row in rows:
        code = str(row["standard"])
        if code not in CLUSTER_CLASS:
            raise KeyError(f"{row['id']}: cluster {code} has no pre-registered class")
        verb_class, strict = CLUSTER_CLASS[code]
        by_id[str(row["id"])] = {"cell": str(row["cell"]), "standard": code, "class": verb_class, "strict": strict}
    return by_id


def faithful_ids() -> set[str]:
    rows = load_jsonl(FIDELITY_ITEMS_PATH)
    return {str(row["id"]) for row in rows if row.get("stage") in ("calibration", "census") and row["verdict"] == VERDICT_FAITHFUL}


def cell_subsets(item_classes: dict[str, dict[str, Any]], paper_cell: str, faithful: set[str]) -> dict[str, list[str]]:
    ids = sorted(item_id for item_id, entry in item_classes.items() if entry["cell"] == paper_cell)
    subsets: dict[str, list[str]] = {"all": ids, "faithful": [i for i in ids if i in faithful]}
    for verb_class in (EXECUTION, RECOGNITION, MIXED):
        members = [i for i in ids if item_classes[i]["class"] == verb_class]
        subsets[verb_class] = members
        subsets[f"{verb_class}_and_faithful"] = [i for i in members if i in faithful]
    strict = [i for i in ids if item_classes[i]["strict"]]
    subsets["execution_strict"] = strict
    subsets["execution_strict_and_faithful"] = [i for i in strict if i in faithful]
    return subsets


def per_cluster(predictions: dict[str, dict[str, Any]], item_classes: dict[str, dict[str, Any]], ids: list[str], faithful: set[str]) -> dict[str, Any]:
    out: dict[str, dict[str, int]] = defaultdict(lambda: {"n": 0, "passes": 0, "nFaithful": 0, "passesFaithful": 0})
    for item_id in ids:
        code = item_classes[item_id]["standard"]
        correct = int(bool(predictions[item_id]["correct"]))
        out[code]["n"] += 1
        out[code]["passes"] += correct
        if item_id in faithful:
            out[code]["nFaithful"] += 1
            out[code]["passesFaithful"] += correct
    return {code: {**stats, "class": CLUSTER_CLASS[code][0], "strict": CLUSTER_CLASS[code][1]} for code, stats in sorted(out.items())}


def fmt_ci(ci: list[float]) -> str:
    return f"[{ci[0]:.3f}, {ci[1]:.3f}]"


def yes_no(flag: bool) -> str:
    return "yes" if flag else "no"


def build_tables(payload: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("### Verb-class counts per cell (items; pre-registered classes)")
    lines.append("")
    lines.append("| cell | all | faithful | execution | execution and faithful | execution_strict | execution_strict and faithful | recognition_or_interpretation | recognition and faithful | mixed | mixed and faithful |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for cell, entry in payload["counts"].items():
        c = entry
        lines.append(
            f"| {payload['cellLabels'][cell]} | {c['all']} | {c['faithful']} | {c[EXECUTION]} | {c[EXECUTION + '_and_faithful']} | {c['execution_strict']} | "
            f"{c['execution_strict_and_faithful']} | {c[RECOGNITION]} | {c[RECOGNITION + '_and_faithful']} | {c[MIXED]} | {c[MIXED + '_and_faithful']} |"
        )
    lines.append("")
    lines.append("### Masked-stem rows by verb class (saved per-item predictions, seed 20260916)")
    lines.append("")
    lines.append("Bar: n >= 10, lower 95% CI above chance (mean 1/k) and above the modal key-letter frequency of that subset.")
    lines.append("")
    lines.append("| model | cell | subset | n | pass | rate | chance | 95% CI | modal letter (freq, this subset) | lower CI > chance | lower CI > modal | bar cleared |")
    lines.append("|---|---|---|---:|---:|---:|---:|---|---|---|---|---|")
    for model_key, model_entry in payload["lm"].items():
        for cell, cell_entry in model_entry["cells"].items():
            for subset in SUBSET_ORDER:
                stats = cell_entry["subsets"].get(subset)
                if stats is None or stats["n"] == 0:
                    continue
                lines.append(
                    f"| {model_entry['label']} | {cell_entry['label']} | {subset} | {stats['n']} | {stats['passes']} | {stats['passRate']:.3f} | "
                    f"{stats['chance']:.3f} | {fmt_ci(stats['ci95'])} | {stats['modalLetter']} ({stats['modalFrequency']:.3f}) | "
                    f"{yes_no(stats['lowerCiAboveChance'])} | {yes_no(stats['lowerCiAboveModal'])} | {yes_no(stats['clearsBar'])} |"
                )
    lines.append("")
    lines.append("### Per-cluster pass counts (descriptive; no per-cluster row is a claim)")
    lines.append("")
    for model_key, model_entry in payload["lm"].items():
        for cell, cell_entry in model_entry["cells"].items():
            lines.append(f"#### {model_entry['label']}, {cell_entry['label']}")
            lines.append("")
            lines.append("| cluster | class | strict | n | pass | n faithful | pass faithful |")
            lines.append("|---|---|---|---:|---:|---:|---:|")
            for code, stats in cell_entry["perCluster"].items():
                lines.append(f"| {code} | {stats['class']} | {yes_no(stats['strict'])} | {stats['n']} | {stats['passes']} | {stats['nFaithful']} | {stats['passesFaithful']} |")
            lines.append("")
    return "\n".join(lines)


def main() -> None:
    prereg_sha = check_preregistration()
    item_classes = load_item_classes()
    faithful = faithful_ids()
    coverage = json.loads(COVERAGE_PATH.read_text(encoding="utf-8"))
    rescored = json.loads(RESCORED_PATH.read_text(encoding="utf-8"))

    counts: dict[str, dict[str, int]] = {}
    subsets_by_cell: dict[str, dict[str, list[str]]] = {}
    for cell, (paper_cell, _label) in CELLS.items():
        subsets = cell_subsets(item_classes, paper_cell, faithful)
        if len(subsets["all"]) != coverage["cells"][paper_cell]["population"]:
            raise RuntimeError(f"{paper_cell}: {len(subsets['all'])} classified items, population {coverage['cells'][paper_cell]['population']}")
        subsets_by_cell[cell] = subsets
        counts[cell] = {name: len(ids) for name, ids in subsets.items()}

    lm_payload: dict[str, Any] = {}
    mismatches: list[str] = []
    for model_key, spec in LM_MODELS.items():
        predictions = load_predictions(GPU_DIR / spec["items"])
        cells_entry: dict[str, Any] = {}
        for cell, (paper_cell, label) in CELLS.items():
            subsets = subsets_by_cell[cell]
            rows = {name: lm_row(predictions, ids) for name, ids in subsets.items() if ids}
            for name in rows:
                if rows[name]["nMissingPredictions"]:
                    raise RuntimeError(f"{model_key} {label} {name}: {rows[name]['nMissingPredictions']} items without predictions")
            reference = rescored["lm"][model_key]["cells"][cell]["subsets"]
            for name, reference_name in (("all", "original"), ("faithful", "faithful")):
                for field in ("n", "passes", "passRate", "ci95", "modalLetter", "modalFrequency", "clearsBar"):
                    if rows[name][field] != reference[reference_name][field]:
                        mismatches.append(f"{model_key} {label} {name}.{field}: {rows[name][field]} vs print-faithful {reference[reference_name][field]}")
            cells_entry[cell] = {
                "paperCell": paper_cell,
                "label": label,
                "subsets": rows,
                "perCluster": per_cluster(predictions, item_classes, subsets["all"], faithful),
                "executionAndFaithfulClearsBar": rows.get(f"{EXECUTION}_and_faithful", {}).get("clearsBar", False),
                "executionStrictAndFaithfulClearsBar": rows.get("execution_strict_and_faithful", {}).get("clearsBar", False),
            }
        lm_payload[model_key] = {"label": spec["label"], "itemsFile": f"exports/addendum-gpu/{spec['items']}", "cells": cells_entry}
    if mismatches:
        raise RuntimeError("all/faithful rows do not reproduce the addendum and print-faithful rows:\n" + "\n".join(mismatches))

    payload = {
        "preregistrationSha256": prereg_sha,
        "printFaithfulPreregistrationSha256": rescored["preregistrationSha256"],
        "standardLevel": "ccss_cluster",
        "clusterClasses": {code: {"class": c, "executionStrict": s} for code, (c, s) in sorted(CLUSTER_CLASS.items())},
        "cellLabels": {cell: label for cell, (_p, label) in CELLS.items()},
        "counts": counts,
        "lm": lm_payload,
        "bar": f"n >= {MIN_N}, lower 95% CI above chance and above the subset modal-letter frequency",
        "bootstrap": "score_choices_only_local_lm.bootstrap_ci, random.Random(21 + n), 1000 replicates, rows in per-item file order",
        "reproduction": "all == addendum original rows; faithful == print-faithful faithful rows (checked field by field)",
        "generatedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    dump_json(OUTPUT_PATH, payload)
    tables = build_tables(payload)
    TABLES_PATH.write_text(tables + "\n", encoding="utf-8")
    print(json.dumps(counts, indent=1))
    print(tables)


if __name__ == "__main__":
    main()
