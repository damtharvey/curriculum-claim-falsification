#!/usr/bin/env python3
"""Recompute the claimed catalog and LM masked-stem rows on the print-faithful subset and its complement. No GPU."""

from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from addendum_lib import ROOT, load_items, middle_value_option, score_program, summarize_scored
from print_fidelity_lib import (
    CALIBRATION_PATH,
    CELL_ALGEBRA_I,
    CELL_ALGEBRA_II,
    CELL_EQAO_G6_LC,
    CELL_GEOMETRY_LC,
    CELL_GEOMETRY_PHI4,
    FIDELITY_ITEMS_PATH,
    OUT_DIR,
    PREREG_SHA_PATH,
    VERDICT_FAITHFUL,
    VERDICT_NOT_FAITHFUL,
    VERDICT_UNVERIFIED,
    dump_json,
    load_jsonl,
    tokens,
)
from score_choices_only_local_lm import bootstrap_ci

RESCORED_PATH = OUT_DIR / "rescored-rows.json"
RELOCATED_PATH = OUT_DIR / "relocated-items.jsonl"
TABLES_PATH = OUT_DIR / "rescored-tables.md"
GPU_DIR = ROOT / "exports" / "addendum-gpu"
LM_MODELS: dict[str, dict[str, str]] = {
    "qwen2.5-7b-instruct": {
        "items": "masked-stem-7b-items.jsonl",
        "summary": "masked-stem-7b.json",
        "label": "Qwen2.5-7B-Instruct",
    },
    "qwen2.5-14b-instruct": {
        "items": "masked-stem-14b-items.jsonl",
        "summary": "masked-stem-14b.json",
        "label": "Qwen2.5-14B-Instruct",
    },
    "phi-4": {
        "items": "masked-stem-phi4-items.jsonl",
        "summary": "masked-stem-phi4.json",
        "label": "Phi-4",
    },
}
LM_CELLS: dict[str, tuple[str, str, bool]] = {
    CELL_ALGEBRA_I: ("nyregents::algebra-i", "Algebra I", True),
    CELL_ALGEBRA_II: ("nyregents::algebra-ii", "Algebra II", True),
    CELL_GEOMETRY_PHI4: ("nyregents::geometry", "geometry", False),
}
CATALOG_CELLS: dict[str, tuple[str, str]] = {
    CELL_GEOMETRY_LC: ("nyregents::geometry", "NY Regents geometry"),
    CELL_EQAO_G6_LC: ("eqao::g6", "EQAO grade 6"),
}
LETTER_ORDER = ("A", "B", "C", "D", "E")
MIN_N = 10


def spurious_digit_tokens(text_layer: str, transcription: str) -> list[str]:
    """Digit tokens the text layer carries that the transcription does not (operator-as-digit encoding, lost minus signs, glued page numbers)."""
    left = tokens(text_layer)
    counts = Counter(tokens(transcription))
    extras: list[str] = []
    for tok in left:
        if counts.get(tok, 0) > 0:
            counts[tok] -= 1
        elif tok.isdigit():
            extras.append(tok)
    return extras


def strict_faithful(row: dict[str, Any]) -> bool:
    """Post-hoc tightening (not pre-registered): faithful and no spurious digit token in the stem or any option."""
    if row["verdict"] != VERDICT_FAITHFUL:
        return False
    if spurious_digit_tokens(str(row.get("textLayerStem") or ""), str(row.get("vlmStem") or "")):
        return False
    vlm_options = row.get("vlmOptions") or {}
    for letter, text in (row.get("textLayerOptions") or {}).items():
        if spurious_digit_tokens(str(text), str(vlm_options.get(letter, ""))):
            return False
    return True


def relocated_verdicts() -> dict[str, str]:
    """Verdicts from the post-hoc locator repair (relocate_print_fidelity_items.py) for items whose crop changed."""
    return {str(row["id"]): str(row["verdict"]) for row in load_jsonl(RELOCATED_PATH)}


def subset_ids(rows: list[dict[str, Any]], cell: str) -> dict[str, list[str]]:
    in_cell = [row for row in rows if cell in row["cells"]]
    relocated = relocated_verdicts()
    return {
        "original": [str(row["id"]) for row in in_cell],
        "faithful": [str(row["id"]) for row in in_cell if row["verdict"] == VERDICT_FAITHFUL],
        "faithful_after_relocation": [
            str(row["id"]) for row in in_cell if relocated.get(str(row["id"]), row["verdict"]) == VERDICT_FAITHFUL
        ],
        "faithful_strict": [str(row["id"]) for row in in_cell if strict_faithful(row)],
        "faithful_digit_suspect": [str(row["id"]) for row in in_cell if row["verdict"] == VERDICT_FAITHFUL and not strict_faithful(row)],
        "not_faithful": [str(row["id"]) for row in in_cell if row["verdict"] == VERDICT_NOT_FAITHFUL],
        "unverified": [str(row["id"]) for row in in_cell if row["verdict"] == VERDICT_UNVERIFIED],
        "numeric_faithful": [str(row["id"]) for row in in_cell if row.get("numeric_faithful") is True],
        "numeric_not_faithful": [str(row["id"]) for row in in_cell if row.get("numeric_faithful") is False],
        "trailing_junk_only": [str(row["id"]) for row in in_cell if row.get("trailing_junk_only")],
    }


def category_counts(rows: list[dict[str, Any]], cell: str) -> dict[str, int]:
    counts = Counter(str(row["category"]) for row in rows if cell in row["cells"])
    return dict(sorted(counts.items()))


def catalog_row(items_by_id: dict[str, dict[str, Any]], ids: list[str]) -> dict[str, Any]:
    items = [items_by_id[item_id] for item_id in ids]
    scored = score_program(items, middle_value_option)
    if len(scored) != len(items):
        raise RuntimeError("lower-central did not fire on every population item; population is the fired set by construction")
    stats = summarize_scored(scored)
    return {
        "n": stats["n"],
        "passes": stats["nCorrect"],
        "passRate": stats["passRate"],
        "chance": stats["chanceRate"],
        "itemCi95": stats["itemBootstrapCi95"],
        "clusterCi95": stats["clusterBootstrapCi95"],
        "nAdministrations": stats["nAdministrations"],
        "clearsItemBar": bool(stats["clearsItemBar"]),
        "clearsClusterBar": bool(stats["clearsClusterBar"]),
    }


def modal_letter(keys: list[str]) -> tuple[str | None, float]:
    if not keys:
        return None, 0.0
    counts = Counter(keys)
    best_letter = None
    best_count = -1
    for letter in LETTER_ORDER:
        if counts.get(letter, 0) > best_count:
            best_count = counts[letter]
            best_letter = letter
    return best_letter, best_count / len(keys)


def lm_row(predictions: dict[str, dict[str, Any]], ids: list[str]) -> dict[str, Any]:
    """Rows are taken in the per-item file order (the order the addendum bootstraps used), restricted to ids."""
    wanted = set(ids)
    rows = [row for item_id, row in predictions.items() if item_id in wanted]
    missing = [item_id for item_id in ids if item_id not in predictions]
    n = len(rows)
    flags = [int(bool(row["correct"])) for row in rows]
    passes = sum(flags)
    rate = passes / n if n else 0.0
    chance = sum(1.0 / int(row["n_options"]) for row in rows) / n if n else 0.0
    ci = bootstrap_ci(flags, 1000, 21 + n) if n else (0.0, 0.0)
    letter, modal_frequency = modal_letter([str(row["key"]) for row in rows])
    chosen = Counter(str(row["chosen_letter"]) for row in rows)
    lower = ci[0]
    return {
        "n": n,
        "nMissingPredictions": len(missing),
        "passes": passes,
        "passRate": rate,
        "chance": chance,
        "ci95": [ci[0], ci[1]],
        "modalLetter": letter,
        "modalFrequency": modal_frequency,
        "chosenLetterCounts": dict(sorted(chosen.items())),
        "lowerCiAboveChance": n >= MIN_N and lower > chance,
        "lowerCiAboveModal": n >= MIN_N and lower > modal_frequency,
        "clearsBar": n >= MIN_N and lower > chance and lower > modal_frequency,
    }


def load_predictions(path: Path) -> dict[str, dict[str, Any]]:
    return {str(row["id"]): row for row in load_jsonl(path)}


def fmt_ci(ci: list[float]) -> str:
    return f"[{ci[0]:.3f}, {ci[1]:.3f}]"


def yes_no(flag: bool) -> str:
    return "yes" if flag else "no"


def build_tables(payload: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("### Faithful fraction per cell")
    lines.append("")
    lines.append("| cell | n | faithful (pre-registered) | faithful, strict (post hoc) | not faithful | unverified | faithful fraction | categories (not faithful and unverified) |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---|")
    for cell, entry in payload["cells"].items():
        cats = ", ".join(f"{k} {v}" for k, v in entry["categories"].items() if k != "match")
        lines.append(
            f"| `{cell}` | {entry['n']} | {entry['faithful']} | {entry['faithfulStrict']} | {entry['notFaithful']} | {entry['unverified']} | "
            f"{entry['faithfulFraction']:.3f} | {cats} |"
        )
    lines.append("")
    lines.append("### Catalog rows (lower-central, `middle_value_option`)")
    lines.append("")
    lines.append("| cell | subset | n | pass | rate | chance | item 95% CI | cluster 95% CI | item bar (n >= 10, lower CI > chance) |")
    lines.append("|---|---|---:|---:|---:|---:|---|---|---|")
    for cell, entry in payload["catalog"].items():
        for subset in ("original", "faithful", "faithful_after_relocation", "faithful_strict", "faithful_digit_suspect", "not_faithful", "numeric_faithful", "numeric_not_faithful", "unverified"):
            stats = entry["subsets"].get(subset)
            if stats is None or stats["n"] == 0:
                continue
            if subset == "faithful_after_relocation" and stats["n"] == entry["subsets"]["faithful"]["n"]:
                continue
            lines.append(
                f"| {entry['label']} | {subset} | {stats['n']} | {stats['passes']} | {stats['passRate']:.3f} | {stats['chance']:.3f} | "
                f"{fmt_ci(stats['itemCi95'])} | {fmt_ci(stats['clusterCi95'])} | {yes_no(stats['clearsItemBar'])} |"
            )
    lines.append("")
    lines.append("### LM masked-stem rows (saved per-item predictions, seed 20260916)")
    lines.append("")
    lines.append("| model | cell | subset | n | pass | rate | chance | 95% CI | modal letter (freq, this subset) | lower CI > chance | lower CI > modal | bar cleared |")
    lines.append("|---|---|---|---:|---:|---:|---:|---|---|---|---|---|")
    for model_key, model_entry in payload["lm"].items():
        for cell, cell_entry in model_entry["cells"].items():
            for subset in ("original", "faithful", "faithful_after_relocation", "faithful_strict", "faithful_digit_suspect", "not_faithful", "trailing_junk_only", "unverified"):
                stats = cell_entry["subsets"].get(subset)
                if stats is None or stats["n"] == 0:
                    continue
                if subset == "faithful_after_relocation" and stats["n"] == cell_entry["subsets"]["faithful"]["n"]:
                    continue
                claimed = "" if cell_entry["claimed"] else " (unclaimed)"
                lines.append(
                    f"| {model_entry['label']} | {cell_entry['label']}{claimed} | {subset} | {stats['n']} | {stats['passes']} | {stats['passRate']:.3f} | "
                    f"{stats['chance']:.3f} | {fmt_ci(stats['ci95'])} | {stats['modalLetter']} ({stats['modalFrequency']:.3f}) | "
                    f"{yes_no(stats['lowerCiAboveChance'])} | {yes_no(stats['lowerCiAboveModal'])} | {yes_no(stats['clearsBar'])} |"
                )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    if not FIDELITY_ITEMS_PATH.exists():
        raise RuntimeError(f"missing {FIDELITY_ITEMS_PATH}")
    prereg_sha = PREREG_SHA_PATH.read_text(encoding="utf-8").split()[0]
    calibration = json.loads(CALIBRATION_PATH.read_text(encoding="utf-8"))
    rows = [row for row in load_jsonl(FIDELITY_ITEMS_PATH) if row.get("stage") in ("calibration", "census")]
    seen: set[str] = set()
    unique_rows: list[dict[str, Any]] = []
    for row in rows:
        if str(row["id"]) in seen:
            raise RuntimeError(f"duplicate fidelity row {row['id']}")
        seen.add(str(row["id"]))
        unique_rows.append(row)
    rows = unique_rows
    items_by_id = {str(item["id"]): item for item in load_items()}
    all_cells = [CELL_ALGEBRA_I, CELL_ALGEBRA_II, CELL_GEOMETRY_LC, CELL_EQAO_G6_LC, CELL_GEOMETRY_PHI4]
    cells_payload: dict[str, Any] = {}
    for cell in all_cells:
        ids = subset_ids(rows, cell)
        denominator = len(ids["faithful"]) + len(ids["not_faithful"])
        cells_payload[cell] = {
            "n": len(ids["original"]),
            "faithful": len(ids["faithful"]),
            "faithfulStrict": len(ids["faithful_strict"]),
            "notFaithful": len(ids["not_faithful"]),
            "unverified": len(ids["unverified"]),
            "faithfulFraction": (len(ids["faithful"]) / denominator) if denominator else 0.0,
            "numericFaithful": len(ids["numeric_faithful"]),
            "trailingJunkOnly": len(ids["trailing_junk_only"]),
            "categories": category_counts(rows, cell),
        }
    catalog_payload: dict[str, Any] = {}
    for cell, (paper_cell, label) in CATALOG_CELLS.items():
        ids = subset_ids(rows, cell)
        subsets = {name: catalog_row(items_by_id, ids[name]) for name in ids if ids[name]}
        catalog_payload[cell] = {
            "paperCell": paper_cell,
            "label": label,
            "programId": "middle-value-option (lower-central)",
            "subsets": subsets,
            "faithfulClearsItemBar": subsets.get("faithful", {}).get("clearsItemBar", False),
            "faithfulClearsClusterBar": subsets.get("faithful", {}).get("clearsClusterBar", False),
            "faithfulStrictClearsItemBar": subsets.get("faithful_strict", {}).get("clearsItemBar", False),
        }
    lm_payload: dict[str, Any] = {}
    for model_key, spec in LM_MODELS.items():
        predictions = load_predictions(GPU_DIR / spec["items"])
        summary = json.loads((GPU_DIR / spec["summary"]).read_text(encoding="utf-8"))
        cells_entry: dict[str, Any] = {}
        for cell, (paper_cell, label, claimed) in LM_CELLS.items():
            if cell == CELL_GEOMETRY_PHI4 and model_key != "phi-4":
                continue
            ids = subset_ids(rows, cell)
            subsets = {name: lm_row(predictions, ids[name]) for name in ids if ids[name]}
            cells_entry[cell] = {
                "paperCell": paper_cell,
                "label": label,
                "claimed": claimed,
                "subsets": subsets,
                "faithfulClearsBar": subsets.get("faithful", {}).get("clearsBar", False),
                "faithfulStrictClearsBar": subsets.get("faithful_strict", {}).get("clearsBar", False),
            }
        lm_payload[model_key] = {
            "label": spec["label"],
            "modelId": summary.get("modelId"),
            "modelRevision": summary.get("modelRevision"),
            "itemsFile": f"exports/addendum-gpu/{spec['items']}",
            "cells": cells_entry,
        }
    failures: list[str] = []
    for cell, entry in catalog_payload.items():
        if not entry["faithfulClearsItemBar"]:
            failures.append(f"catalog {entry['label']} lower-central: faithful subset does not clear the item bar")
        if not entry["faithfulStrictClearsItemBar"]:
            failures.append(f"catalog {entry['label']} lower-central: strict faithful subset (post hoc) does not clear the item bar")
    for model_key, model_entry in lm_payload.items():
        for cell, cell_entry in model_entry["cells"].items():
            if cell_entry["claimed"] and not cell_entry["faithfulClearsBar"]:
                failures.append(f"LM {model_entry['label']} {cell_entry['label']}: faithful subset does not clear chance and modal")
            if cell_entry["claimed"] and not cell_entry["faithfulStrictClearsBar"]:
                failures.append(f"LM {model_entry['label']} {cell_entry['label']}: strict faithful subset (post hoc) does not clear chance and modal")
    payload = {
        "preregistrationSha256": prereg_sha,
        "calibration": {
            "binaryAgreement": calibration["confusionChosen"]["binaryAgreement"],
            "n": calibration["nAudited"],
            "thresholds": calibration["thresholds"]["chosenThresholds"],
            "adjusted": calibration["thresholds"]["adjusted"],
        },
        "nFidelityRows": len(rows),
        "verdicts": dict(Counter(str(row["verdict"]) for row in rows)),
        "cells": cells_payload,
        "catalog": catalog_payload,
        "lm": lm_payload,
        "claimedRowsFailingOnFaithfulSubset": failures,
        "relocation": {
            "nRelocated": len(load_jsonl(RELOCATED_PATH)),
            "nVerdictChanged": sum(1 for row in load_jsonl(RELOCATED_PATH) if row["verdict"] != row.get("preregisteredVerdict")),
            "changed": [
                {"id": row["id"], "preregistered": row.get("preregisteredVerdict"), "relocated": row["verdict"]}
                for row in load_jsonl(RELOCATED_PATH)
                if row["verdict"] != row.get("preregisteredVerdict")
            ],
            "note": "Post-hoc locator repair; see relocate_print_fidelity_items.py. faithful_after_relocation applies these verdicts.",
        },
        "strictFaithfulNote": (
            "faithful_strict is a post-hoc tightening, not in the preregistration: a faithful item is dropped if its text-layer stem "
            "or any option carries a digit token absent from the transcription (the recent Regents encoding of =, +, - as 5, 1, 2; "
            "lost minus signs; glued page numbers). Motivation: the pre-registered option score accepts max(token F1, character ratio) "
            ">= 0.9, and the character ratio admits a one-character digit substitution inside a long option string."
        ),
        "bootstrap": {
            "catalogItem": "addendum_lib.bootstrap_ci_mulberry, mulberry32 seed 11, 1000 replicates",
            "catalogCluster": "addendum_lib.cluster_bootstrap_ci by administration, seed 20260916, 2000 replicates",
            "lm": "score_choices_only_local_lm.bootstrap_ci, random.Random(21 + n), 1000 replicates",
        },
        "generatedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    dump_json(RESCORED_PATH, payload)
    TABLES_PATH.write_text(build_tables(payload), encoding="utf-8")
    print(json.dumps({"cells": cells_payload, "failures": failures}, indent=2))
    print(build_tables(payload))


if __name__ == "__main__":
    main()
