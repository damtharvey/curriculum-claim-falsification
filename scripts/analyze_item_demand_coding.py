#!/usr/bin/env python3
"""Agreement between the two item-level demand coders and the cluster split, and masked-stem rows on the coder subsets. No GPU.

Inputs are the two blind codings of the 358 Algebra I masked-stem primary items
(``exports/item-demand-coding/coder-glm/codes.jsonl`` and ``coder-kimi/codes.jsonl``), the
pre-registered cluster verb class of each item (``exports/standards-split``), and the saved
per-item language-model predictions on the repaired layer (``exports/repaired-layer``) and on
the census text layer (``exports/addendum-gpu``). Nothing is rescored; rows are recomputed
from saved flags with the addendum's bootstrap (``random.Random.randrange``, 1000 replicates,
seed ``21 + n``). The bar is the channel bar: n >= 10, lower 95% CI strictly above chance 0.25
and strictly above the subset's modal key-letter frequency.

Writes ``exports/item-demand-coding/agreement.json`` and ``exports/item-demand-coding/README.md``.
"""

from __future__ import annotations

import json
import random
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from split_masked_stem_by_standard import (  # noqa: E402
    CLUSTER_CLASS,
    EXECUTION,
    ITEM_STANDARDS_PATH,
    MIXED,
    RECOGNITION,
)

ROOT = Path(__file__).resolve().parent.parent
CODING_DIR = ROOT / "exports" / "item-demand-coding"
CODER_PATHS = {
    "glm": CODING_DIR / "coder-glm" / "codes.jsonl",
    "kimi": CODING_DIR / "coder-kimi" / "codes.jsonl",
}
REPAIRED_DIR = ROOT / "exports" / "repaired-layer"
REPAIRED_MASKED_PATH = REPAIRED_DIR / "repaired-masked-items.jsonl"
PRIMARY_IDS_PATH = ROOT / "exports" / "addendum-gpu" / "masked-stem-algebra-primary-item-ids.json"
FIDELITY_ITEMS_PATH = ROOT / "exports" / "print-faithful" / "fidelity-items.jsonl"
MODEL_KEYS = ("7b", "14b", "phi4")
MODEL_LABELS = {"7b": "Qwen2.5-7B-Instruct", "14b": "Qwen2.5-14B-Instruct", "phi4": "Phi-4"}
SCORE_PATHS = {
    "repaired": {key: REPAIRED_DIR / f"scores-{key}-repaired.jsonl" for key in MODEL_KEYS},
    "isomorph": {key: REPAIRED_DIR / f"scores-{key}-repaired-isomorph_rank_preserving.jsonl" for key in MODEL_KEYS},
    "text": {key: ROOT / "exports" / "addendum-gpu" / f"masked-stem-{key}-items.jsonl" for key in MODEL_KEYS},
}
UNREADABLE = "unreadable"
CLASSES = (EXECUTION, RECOGNITION, MIXED)
CHANCE = 0.25
MIN_N = 10
LETTER_ORDER = ("A", "B", "C", "D", "E")
OUTPUT_JSON = CODING_DIR / "agreement.json"
OUTPUT_README = CODING_DIR / "README.md"


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def bootstrap_ci(flags: list[int], n_boot: int = 1000, seed: int = 11) -> tuple[float, float]:
    """Percentile bootstrap identical to scripts/score_choices_only_local_lm.py."""
    if not flags:
        return (0.0, 0.0)
    rng = random.Random(seed)
    n = len(flags)
    samples: list[float] = []
    for _ in range(n_boot):
        total = 0
        for _inner in range(n):
            total += flags[rng.randrange(n)]
        samples.append(total / n)
    samples.sort()
    return (samples[int(0.025 * (n_boot - 1))], samples[int(0.975 * (n_boot - 1))])


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


def rate_stats(rows: list[dict[str, Any]]) -> dict[str, Any]:
    n = len(rows)
    flags = [int(bool(row["correct"])) for row in rows]
    rate = sum(flags) / n if n else 0.0
    chance = sum(1.0 / int(row["n_options"]) for row in rows) / n if n else 0.0
    ci = bootstrap_ci(flags, 1000, 21 + n) if n else (0.0, 0.0)
    letter, modal_frequency = modal_letter([str(row["key"]) for row in rows])
    lower = ci[0]
    return {
        "n": n,
        "passes": sum(flags),
        "passRate": rate,
        "chance": chance,
        "ci95": [ci[0], ci[1]],
        "modalLetter": letter,
        "modalFrequency": modal_frequency,
        "lowerCiAboveChance": n >= MIN_N and lower > CHANCE,
        "lowerCiAboveModal": n >= MIN_N and lower > modal_frequency,
        "clearsBar": n >= MIN_N and lower > CHANCE and lower > modal_frequency,
    }


def cohen_kappa(pairs: list[tuple[str, str]], labels: tuple[str, ...]) -> dict[str, Any]:
    n = len(pairs)
    if n == 0:
        raise RuntimeError("kappa on zero pairs")
    agree = sum(1 for a, b in pairs if a == b)
    observed = agree / n
    first = Counter(a for a, _ in pairs)
    second = Counter(b for _, b in pairs)
    expected = sum(first[label] * second[label] for label in labels) / (n * n)
    kappa = (observed - expected) / (1.0 - expected) if expected < 1.0 else 1.0
    return {"n": n, "agree": agree, "observed": observed, "expected": expected, "kappa": kappa}


def confusion(pairs: list[tuple[str, str]], labels: tuple[str, ...]) -> dict[str, dict[str, int]]:
    matrix = {row: {col: 0 for col in labels} for row in labels}
    for a, b in pairs:
        matrix[a][b] += 1
    return matrix


def load_codes(path: Path, universe: list[str]) -> dict[str, dict[str, Any]]:
    rows = load_jsonl(path)
    by_id = {str(row["id"]): row for row in rows}
    if len(by_id) != len(rows):
        raise RuntimeError(f"{path}: duplicate ids")
    if set(by_id) != set(universe):
        raise RuntimeError(f"{path}: coded ids differ from the 358-item universe")
    allowed = set(CLASSES) | {UNREADABLE}
    for row in rows:
        if row["code"] not in allowed:
            raise RuntimeError(f"{path}: unknown code {row['code']!r} on {row['id']}")
    return by_id


def cluster_classes(universe: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for row in load_jsonl(ITEM_STANDARDS_PATH):
        item_id = str(row["id"])
        if item_id in universe:
            out[item_id] = CLUSTER_CLASS[str(row["standard"])][0]
    missing = [item_id for item_id in universe if item_id not in out]
    if missing:
        raise RuntimeError(f"{len(missing)} universe items have no cluster class")
    return out


def fmt_ci(ci: list[float]) -> str:
    return f"[{ci[0]:.3f}, {ci[1]:.3f}]"


def yes_no(flag: bool) -> str:
    return "yes" if flag else "no"


def main() -> None:
    universe = [
        item_id
        for item_id in json.loads(PRIMARY_IDS_PATH.read_text(encoding="utf-8"))
        if str(item_id).startswith("nyregents-algebra-i-")
    ]
    if len(universe) != 358:
        raise RuntimeError(f"expected 358 Algebra I primary ids, found {len(universe)}")
    codes = {name: load_codes(path, universe) for name, path in CODER_PATHS.items()}
    cluster = cluster_classes(universe)

    code_counts = {
        name: dict(Counter(str(rows[item_id]["code"]) for item_id in universe)) for name, rows in codes.items()
    }
    confidence_counts = {
        name: dict(Counter(str(rows[item_id].get("confidence")) for item_id in universe))
        for name, rows in codes.items()
    }

    def readable(name: str, item_id: str) -> bool:
        return codes[name][item_id]["code"] != UNREADABLE

    coder_pairs = [
        (codes["glm"][item_id]["code"], codes["kimi"][item_id]["code"])
        for item_id in universe
        if readable("glm", item_id) and readable("kimi", item_id)
    ]
    agreement: dict[str, Any] = {
        "glm_vs_kimi": {
            **cohen_kappa(coder_pairs, CLASSES),
            "confusion_rows_glm_cols_kimi": confusion(coder_pairs, CLASSES),
            "dropped_unreadable": len(universe) - len(coder_pairs),
        }
    }
    for name in CODER_PATHS:
        pairs = [
            (codes[name][item_id]["code"], cluster[item_id]) for item_id in universe if readable(name, item_id)
        ]
        agreement[f"{name}_vs_cluster"] = {
            **cohen_kappa(pairs, CLASSES),
            f"confusion_rows_{name}_cols_cluster": confusion(pairs, CLASSES),
            "dropped_unreadable": len(universe) - len(pairs),
        }
    binary_pairs = [
        (
            "execution" if codes["glm"][item_id]["code"] == EXECUTION else "other",
            "execution" if codes["kimi"][item_id]["code"] == EXECUTION else "other",
        )
        for item_id in universe
        if readable("glm", item_id) and readable("kimi", item_id)
    ]
    agreement["glm_vs_kimi_execution_binary"] = cohen_kappa(binary_pairs, ("execution", "other"))

    def both(code: str) -> list[str]:
        return [
            item_id
            for item_id in universe
            if codes["glm"][item_id]["code"] == code and codes["kimi"][item_id]["code"] == code
        ]

    subsets: dict[str, list[str]] = {
        "execution_either": [
            item_id
            for item_id in universe
            if codes["glm"][item_id]["code"] == EXECUTION or codes["kimi"][item_id]["code"] == EXECUTION
        ],
        "execution_both": both(EXECUTION),
        "recognition_both": both(RECOGNITION),
        "execution_both_and_cluster": [item_id for item_id in both(EXECUTION) if cluster[item_id] == EXECUTION],
        "recognition_both_and_cluster": [
            item_id for item_id in both(RECOGNITION) if cluster[item_id] == RECOGNITION
        ],
        "cluster_execution": [item_id for item_id in universe if cluster[item_id] == EXECUTION],
        "cluster_recognition": [item_id for item_id in universe if cluster[item_id] == RECOGNITION],
    }
    subset_cluster_mix = {
        name: dict(Counter(cluster[item_id] for item_id in ids)) for name, ids in subsets.items()
    }

    masked = {str(row["id"]): row for row in load_jsonl(REPAIRED_MASKED_PATH)}
    repaired_all = {item_id for item_id in universe if masked[item_id].get("withheld_quantity")}
    repaired_verified = {
        item_id for item_id in repaired_all if masked[item_id].get("repair_verdict") == "repaired_verified"
    }
    faithful = {
        str(row["id"])
        for row in load_jsonl(FIDELITY_ITEMS_PATH)
        if row.get("stage") in ("calibration", "census") and row.get("verdict") == "faithful"
    }
    populations: dict[str, set[str]] = {
        "repaired_verified": repaired_verified,
        "repaired_all": repaired_all,
        "text_layer": set(universe),
        "text_layer_faithful": set(universe) & faithful,
    }
    layer_for_population = {
        "repaired_verified": "repaired",
        "repaired_all": "repaired",
        "text_layer": "text",
        "text_layer_faithful": "text",
    }

    predictions: dict[str, dict[str, dict[str, dict[str, Any]]]] = {}
    for layer, paths in SCORE_PATHS.items():
        predictions[layer] = {}
        for model_key, path in paths.items():
            predictions[layer][model_key] = {str(row["id"]): row for row in load_jsonl(path)}

    rows: dict[str, Any] = {}
    for population_name, population_ids in populations.items():
        layer = layer_for_population[population_name]
        rows[population_name] = {}
        for subset_name, subset_ids in subsets.items():
            ids = [item_id for item_id in subset_ids if item_id in population_ids]
            entry: dict[str, Any] = {"n_subset_in_population": len(ids), "models": {}}
            for model_key in MODEL_KEYS:
                preds = predictions[layer][model_key]
                present = [item_id for item_id in ids if item_id in preds]
                stats = rate_stats([preds[item_id] for item_id in present])
                stats["nMissingScores"] = len(ids) - len(present)
                model_entry: dict[str, Any] = {"masked_stem": stats}
                if layer == "repaired":
                    iso_preds = predictions["isomorph"][model_key]
                    iso_present = [item_id for item_id in ids if item_id in iso_preds]
                    iso_stats = rate_stats([iso_preds[item_id] for item_id in iso_present])
                    iso_stats["nExcludedPerturbFailed"] = len(ids) - len(iso_present)
                    model_entry["isomorph_rank_preserving"] = iso_stats
                entry["models"][model_key] = model_entry
            rows[population_name][subset_name] = entry

    payload = {
        "universe": {"cell": "nyregents::algebra-i", "n": len(universe), "source": str(PRIMARY_IDS_PATH.relative_to(ROOT))},
        "coders": {
            name: {"path": str(path.relative_to(ROOT)), "code_counts": code_counts[name], "confidence_counts": confidence_counts[name]}
            for name, path in CODER_PATHS.items()
        },
        "cluster_class_counts": dict(Counter(cluster[item_id] for item_id in universe)),
        "agreement": agreement,
        "subsets": {name: {"n": len(ids), "cluster_mix": subset_cluster_mix[name], "ids": ids} for name, ids in subsets.items()},
        "populations": {name: len(ids) for name, ids in populations.items()},
        "bar": "n >= 10, lower 95% bootstrap CI strictly above chance 0.25 and strictly above the subset modal key-letter frequency",
        "bootstrap": "random.Random.randrange, 1000 replicates, seed 21 + n, rows in primary-id order",
        "rows": rows,
        "writtenAt": datetime.now(timezone.utc).isoformat(),
    }
    OUTPUT_JSON.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    OUTPUT_README.write_text(render_readme(payload), encoding="utf-8")
    print(f"wrote {OUTPUT_JSON} and {OUTPUT_README}")
    for key in ("glm_vs_kimi", "glm_vs_cluster", "kimi_vs_cluster", "glm_vs_kimi_execution_binary"):
        print(f"{key}: kappa {agreement[key]['kappa']:.3f} n {agreement[key]['n']}")


def render_readme(payload: dict[str, Any]) -> str:
    agreement = payload["agreement"]
    lines: list[str] = [
        "# Item-level demand coding of the Algebra I masked-stem items",
        "",
        "Two language-model coders (GLM 5.2 in `coder-glm/`, Kimi K3 in `coder-kimi/`) each coded the 358 New York Regents "
        "Algebra I masked-stem primary items for what answering the item requires, under one fixed rubric (recorded with its "
        "sha256 in each coder's README), blind to the key, to every model prediction, and to the pre-registered cluster split. "
        "Codes: `execution` (the key requires operating on the specific given quantities), `recognition_or_interpretation` "
        "(the key can be picked from the form, meaning, or property named in the wording), `mixed`, `unreadable`.",
        "",
        "This file is written by `scripts/analyze_item_demand_coding.py` from `codes.jsonl`, the cluster classes in "
        "`exports/standards-split/`, and the saved per-item predictions in `exports/repaired-layer/` and `exports/addendum-gpu/`. "
        "Nothing is rescored. A pass does not require the tagged operation. Nothing here says students did not learn.",
        "",
        "## Code counts",
        "",
        "| code | GLM 5.2 | Kimi K3 | cluster split |",
        "|---|---:|---:|---:|",
    ]
    cluster_counts = payload["cluster_class_counts"]
    for code in (EXECUTION, RECOGNITION, MIXED, UNREADABLE):
        lines.append(
            f"| {code} | {payload['coders']['glm']['code_counts'].get(code, 0)} | "
            f"{payload['coders']['kimi']['code_counts'].get(code, 0)} | {cluster_counts.get(code, 0)} |"
        )
    lines += [
        "",
        "## Agreement (Cohen's kappa, unweighted)",
        "",
        "Three classes (execution, recognition or interpretation, mixed); items either coder marked unreadable are dropped from that pair.",
        "",
        "| pair | n | observed agreement | kappa |",
        "|---|---:|---:|---:|",
    ]
    for key, label in (
        ("glm_vs_kimi", "GLM vs Kimi"),
        ("glm_vs_cluster", "GLM vs cluster split"),
        ("kimi_vs_cluster", "Kimi vs cluster split"),
        ("glm_vs_kimi_execution_binary", "GLM vs Kimi, execution vs other"),
    ):
        block = agreement[key]
        lines.append(f"| {label} | {block['n']} | {block['observed']:.3f} | {block['kappa']:.3f} |")
    lines += ["", "### Confusion matrices", ""]
    for key, row_label, col_label, matrix_key in (
        ("glm_vs_kimi", "GLM", "Kimi", "confusion_rows_glm_cols_kimi"),
        ("glm_vs_cluster", "GLM", "cluster", "confusion_rows_glm_cols_cluster"),
        ("kimi_vs_cluster", "Kimi", "cluster", "confusion_rows_kimi_cols_cluster"),
    ):
        matrix = agreement[key][matrix_key]
        lines.append(f"Rows {row_label}, columns {col_label}.")
        lines.append("")
        lines.append("| | " + " | ".join(CLASSES) + " |")
        lines.append("|---|" + "---:|" * len(CLASSES))
        for row in CLASSES:
            lines.append(f"| {row} | " + " | ".join(str(matrix[row][col]) for col in CLASSES) + " |")
        lines.append("")
    lines += [
        "## Subsets",
        "",
        "| subset | definition | n of 358 | cluster mix |",
        "|---|---|---:|---|",
    ]
    definitions = {
        "execution_either": "at least one coder codes execution",
        "execution_both": "both coders code execution",
        "recognition_both": "both coders code recognition or interpretation",
        "execution_both_and_cluster": "both coders and the cluster tag say execution",
        "recognition_both_and_cluster": "both coders and the cluster tag say recognition or interpretation",
        "cluster_execution": "cluster tag execution (pre-registered split)",
        "cluster_recognition": "cluster tag recognition or interpretation (pre-registered split)",
    }
    for name, block in payload["subsets"].items():
        mix = ", ".join(f"{k} {v}" for k, v in sorted(block["cluster_mix"].items()))
        lines.append(f"| `{name}` | {definitions[name]} | {block['n']} | {mix} |")
    lines += [
        "",
        "## Masked-stem rows on the coder subsets",
        "",
        f"Bar: {payload['bar']}. Bootstrap: {payload['bootstrap']}. Populations: repaired-verified "
        f"(n={payload['populations']['repaired_verified']} of the Algebra I withheld-quantity repaired items), repaired-all "
        f"(n={payload['populations']['repaired_all']}), text layer (n={payload['populations']['text_layer']}), and text layer "
        f"print-faithful (n={payload['populations']['text_layer_faithful']}). Repaired rows use `exports/repaired-layer/scores-*-repaired.jsonl`; "
        "the isomorph column is the rank-preserving option-numeral arm on the repaired options "
        "(`scores-*-repaired-isomorph_rank_preserving.jsonl`; items whose perturbation failed are excluded and counted). "
        "Text-layer rows use the saved census predictions and have no isomorph column.",
        "",
    ]
    for population_name, population_label in (
        ("repaired_verified", "Repaired, verified"),
        ("repaired_all", "Repaired, all"),
        ("text_layer", "Text layer, all"),
        ("text_layer_faithful", "Text layer, print-faithful"),
    ):
        lines.append(f"### {population_label}")
        lines.append("")
        has_iso = population_name.startswith("repaired")
        header = "| subset | model | n | pass | rate | 95% CI | modal (freq) | bar |"
        if has_iso:
            header += " isomorph n | isomorph rate | isomorph 95% CI | isomorph bar |"
        lines.append(header)
        lines.append("|---|---|---:|---:|---:|---|---|---|" + ("---:|---:|---|---|" if has_iso else ""))
        for subset_name, entry in payload["rows"][population_name].items():
            for model_key in MODEL_KEYS:
                stats = entry["models"][model_key]["masked_stem"]
                line = (
                    f"| `{subset_name}` | {MODEL_LABELS[model_key]} | {stats['n']} | {stats['passes']} | {stats['passRate']:.3f} | "
                    f"{fmt_ci(stats['ci95'])} | {stats['modalLetter']} ({stats['modalFrequency']:.3f}) | {yes_no(stats['clearsBar'])} |"
                )
                if has_iso:
                    iso = entry["models"][model_key]["isomorph_rank_preserving"]
                    line += (
                        f" {iso['n']} | {iso['passRate']:.3f} | {fmt_ci(iso['ci95'])} | {yes_no(iso['clearsBar'])} |"
                    )
                lines.append(line)
        lines.append("")
    lines += [
        "## Files",
        "",
        "- `coder-glm/`, `coder-kimi/`: the two blind codings (`codes.jsonl`, `items-to-code.jsonl`, rubric, README).",
        "- `agreement.json`: everything above with subset id lists.",
        "- Script: `scripts/analyze_item_demand_coding.py`.",
        "",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    main()
