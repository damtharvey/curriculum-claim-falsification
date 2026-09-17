#!/usr/bin/env python3
"""Score original and isomorph option arms on the masked-stem algebra population."""

from __future__ import annotations

import argparse
import gc
import json
import os
import random
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

import score_choices_only_local_lm as scorer  # noqa: E402
from perturb_option_numerals import (  # noqa: E402
    ARM_PRESERVING,
    ARM_SCRAMBLED,
    ARMS,
    OUT_DIR,
    PREREG_PATH,
    PREREG_SHA_PATH,
    SEED,
    check_preregistration,
)
from print_fidelity_lib import FIDELITY_ITEMS_PATH, VERDICT_FAITHFUL, load_jsonl  # noqa: E402
from split_masked_stem_by_standard import CLUSTER_CLASS, EXECUTION, RECOGNITION  # noqa: E402

ALGEBRA_IDS_PATH = ROOT / "exports" / "addendum-gpu" / "masked-stem-algebra-primary-item-ids.json"
ITEM_STANDARDS_PATH = ROOT / "exports" / "standards-split" / "item-standards.jsonl"
SAVED_PREDICTIONS = {
    "7b": ROOT / "exports" / "addendum-gpu" / "masked-stem-7b-items.jsonl",
    "14b": ROOT / "exports" / "addendum-gpu" / "masked-stem-14b-items.jsonl",
    "phi4": ROOT / "exports" / "addendum-gpu" / "masked-stem-phi4-items.jsonl",
}
MODELS: dict[str, dict[str, Any]] = {
    "7b": {
        "model_id": "Qwen/Qwen2.5-7B-Instruct",
        "revision": "a09a35458c702b33eeacc393d103063234e8bc28",
        "batch_size": 4,
        "device_map": "to",
        "label": "Qwen2.5-7B-Instruct",
    },
    "14b": {
        "model_id": "Qwen/Qwen2.5-14B-Instruct",
        "revision": "cf98f3b3bbb457ad9e2bb7baf9a0125b6b88caa8",
        "batch_size": 1,
        "device_map": "cuda",
        "label": "Qwen2.5-14B-Instruct",
    },
    "phi4": {
        "model_id": "microsoft/phi-4",
        "revision": "2db69c1c3e91a05d2c64a3185acfbaf36f744e25",
        "batch_size": 1,
        "device_map": "cuda",
        "label": "Phi-4",
    },
}
ARM_ORIGINAL = "original"
MIN_REPRODUCTION = 0.98
CHANCE = 0.25
LETTER_ORDER = ("A", "B", "C", "D", "E")
SUBSET_SPECS = (
    ("algebra_i_all", "Algebra I all"),
    ("algebra_i_faithful", "Algebra I faithful"),
    ("algebra_i_faithful_recognition", "Algebra I faithful and recognition"),
    ("algebra_i_faithful_execution", "Algebra I faithful and execution"),
    ("algebra_ii_all", "Algebra II all"),
    ("algebra_ii_faithful", "Algebra II faithful"),
)


def load_jsonl_by_id(path: Path) -> dict[str, dict[str, Any]]:
    return {str(row["id"]): row for row in load_jsonl(path)}


def algebra_item_ids() -> list[str]:
    return [str(item_id) for item_id in json.loads(ALGEBRA_IDS_PATH.read_text(encoding="utf-8"))]


def faithful_ids() -> set[str]:
    return {
        str(row["id"])
        for row in load_jsonl(FIDELITY_ITEMS_PATH)
        if row.get("stage") in ("calibration", "census") and row["verdict"] == VERDICT_FAITHFUL
    }


def item_verb_class() -> dict[str, str]:
    out: dict[str, str] = {}
    for row in load_jsonl(ITEM_STANDARDS_PATH):
        code = str(row["standard"])
        if code not in CLUSTER_CLASS:
            raise KeyError(f"{row['id']}: cluster {code} has no class")
        out[str(row["id"])] = CLUSTER_CLASS[code][0]
    return out


def build_subsets(items: list[dict[str, Any]]) -> dict[str, list[str]]:
    faithful = faithful_ids()
    verb = item_verb_class()
    algebra_i = [str(item["id"]) for item in items if item["claim"] == "algebra-i"]
    algebra_ii = [str(item["id"]) for item in items if item["claim"] == "algebra-ii"]
    subsets = {
        "algebra_i_all": algebra_i,
        "algebra_i_faithful": [item_id for item_id in algebra_i if item_id in faithful],
        "algebra_i_faithful_recognition": [
            item_id
            for item_id in algebra_i
            if item_id in faithful and verb.get(item_id) == RECOGNITION
        ],
        "algebra_i_faithful_execution": [
            item_id
            for item_id in algebra_i
            if item_id in faithful and verb.get(item_id) == EXECUTION
        ],
        "algebra_ii_all": algebra_ii,
        "algebra_ii_faithful": [item_id for item_id in algebra_ii if item_id in faithful],
    }
    expected = {
        "algebra_i_all": 358,
        "algebra_i_faithful": 184,
        "algebra_i_faithful_recognition": 83,
        "algebra_i_faithful_execution": 75,
        "algebra_ii_all": 248,
        "algebra_ii_faithful": 115,
    }
    for name, count in expected.items():
        if len(subsets[name]) != count:
            raise RuntimeError(f"{name} has {len(subsets[name])}, expected {count}")
    return subsets


def prepare_base_items() -> list[dict[str, Any]]:
    item_ids = algebra_item_ids()
    items_by_id = scorer.load_items()
    raw = [items_by_id[item_id] for item_id in item_ids]
    kept, dropped, below_min, _reports = scorer.apply_masking(
        raw, version=1, min_masked_token_count=1
    )
    if dropped or below_min:
        raise RuntimeError(
            f"masking dropped {len(dropped)} or below-min {len(below_min)} algebra items"
        )
    if len(kept) != 606:
        raise RuntimeError(f"expected 606 masked algebra items, got {len(kept)}")
    saved = load_jsonl_by_id(SAVED_PREDICTIONS["7b"])
    for item in kept:
        item_id = str(item["id"])
        if item["_masked_stem"] != saved[item_id]["masked_stem"]:
            raise RuntimeError(f"masked stem mismatch for {item_id}")
    return kept


def attach_choices(base_items: list[dict[str, Any]], choices_by_id: dict[str, dict[str, str]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for item in base_items:
        copy = dict(item)
        copy["choices"] = dict(choices_by_id[str(item["id"])])
        out.append(copy)
    return out


def load_perturbed_choices(arm: str) -> dict[str, dict[str, str]]:
    path = OUT_DIR / f"perturbed-items-{arm}.jsonl"
    if not path.exists():
        raise RuntimeError(f"perturbed items missing: {path}")
    return {str(row["id"]): dict(row["choices"]) for row in load_jsonl(path)}


def no_numeral_ids() -> set[str]:
    path = OUT_DIR / f"perturbed-items-{ARM_PRESERVING}.jsonl"
    return {str(row["id"]) for row in load_jsonl(path) if row.get("noNumeral")}


def scores_path(model_key: str, arm: str) -> Path:
    return OUT_DIR / f"scores-{model_key}-{arm}.jsonl"


def already_scored_ids(path: Path) -> set[str]:
    return scorer.already_scored_ids(path)


def load_causal_lm(
    model_key: str,
    device: torch.device,
) -> tuple[Any, Any]:
    spec = MODELS[model_key]
    snapshot = scorer.snapshot_dir_for(str(spec["model_id"]), str(spec["revision"]))
    if not snapshot.exists():
        raise RuntimeError(f"Local model snapshot missing: {snapshot}")
    tokenizer = AutoTokenizer.from_pretrained(str(snapshot), local_files_only=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"
    scorer.letter_token_ids = {
        letter: scorer.letter_variant_token_ids(tokenizer, letter) for letter in list("ABCDE")
    }
    torch.manual_seed(scorer.EXPERIMENT_SEED)
    torch.cuda.manual_seed_all(scorer.EXPERIMENT_SEED)
    pretrained_kwargs: dict[str, Any] = {
        "torch_dtype": torch.bfloat16,
        "local_files_only": True,
        "attn_implementation": "sdpa",
    }
    if spec["device_map"] == "cuda":
        pretrained_kwargs["device_map"] = "cuda"
        model = AutoModelForCausalLM.from_pretrained(str(snapshot), **pretrained_kwargs)
    else:
        model = AutoModelForCausalLM.from_pretrained(str(snapshot), **pretrained_kwargs)
        model.to(device)
    model.eval()
    return model, tokenizer


def free_cuda() -> None:
    gc.collect()
    torch.cuda.empty_cache()
    torch.cuda.synchronize()


def arm_complete(model_key: str, arm: str, n_items: int) -> bool:
    path = scores_path(model_key, arm)
    return path.exists() and len(already_scored_ids(path)) >= n_items


def model_complete(model_key: str, n_items: int) -> bool:
    return all(arm_complete(model_key, arm, n_items) for arm in (ARM_ORIGINAL, *ARMS))


def score_arm(
    model: Any,
    tokenizer: Any,
    device: torch.device,
    items: list[dict[str, Any]],
    model_key: str,
    arm: str,
    batch_size: int,
) -> list[dict[str, Any]]:
    out_path = scores_path(model_key, arm)
    done_ids = already_scored_ids(out_path)
    scored_rows = scorer.load_existing_rows(out_path)
    pending = [item for item in items if str(item["id"]) not in done_ids]
    print(
        f"scoring model={model_key} arm={arm} pending={len(pending)} already={len(done_ids)}",
        flush=True,
    )
    for start in range(0, len(pending), batch_size):
        batch_items = pending[start : start + batch_size]
        prompts = [
            scorer.build_prompt(
                item,
                with_stem=True,
                tokenizer_obj=tokenizer,
                prompt_mode="masked-stem",
            )
            for item in batch_items
        ]
        letters_per_item = [scorer.option_letters(item.get("choices") or {}) for item in batch_items]
        scored = scorer.score_prompts(model, tokenizer, device, prompts, letters_per_item)
        new_rows: list[dict[str, Any]] = []
        for item, (chosen, letter_logprobs, _variants) in zip(batch_items, scored):
            key = str(item["key"]).strip().upper()
            row = {
                "id": item["id"],
                "predicted_letter": chosen,
                "chosen_letter": chosen,
                "key": key,
                "correct": bool(chosen == key),
                "logprobs": letter_logprobs,
                "n_options": len(item.get("choices") or {}),
                "claim": item.get("claim"),
                "arm": arm,
            }
            new_rows.append(row)
            scored_rows.append(row)
        scorer.append_jsonl(out_path, new_rows)
        done = len(scored_rows)
        rate = sum(int(row["correct"]) for row in scored_rows) / done if done else 0.0
        print(f"  {model_key} {arm} {done}/{len(items)} rate={rate:.4f}", flush=True)
    by_id = {str(row["id"]): row for row in scored_rows}
    ordered = [by_id[str(item["id"])] for item in items]
    if len(ordered) != len(items):
        raise RuntimeError(f"missing scores for {model_key} {arm}")
    return ordered


def reproduction_agreement(
    scored: list[dict[str, Any]],
    saved_path: Path,
) -> dict[str, Any]:
    saved = load_jsonl_by_id(saved_path)
    agree = 0
    compared = 0
    mismatches: list[dict[str, str]] = []
    for row in scored:
        item_id = str(row["id"])
        if item_id not in saved:
            raise RuntimeError(f"saved prediction missing {item_id} in {saved_path}")
        compared += 1
        saved_letter = str(saved[item_id]["chosen_letter"]).strip().upper()
        predicted = str(row["predicted_letter"]).strip().upper()
        if predicted == saved_letter:
            agree += 1
        elif len(mismatches) < 12:
            mismatches.append(
                {
                    "id": item_id,
                    "rerun": predicted,
                    "saved": saved_letter,
                }
            )
    rate = agree / compared if compared else 0.0
    return {
        "n": compared,
        "nAgree": agree,
        "agreement": rate,
        "clearsFloor": rate >= MIN_REPRODUCTION,
        "mismatches": mismatches,
        "savedPath": str(saved_path.relative_to(ROOT)),
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


def paired_difference_ci(
    original_flags: list[int],
    perturbed_flags: list[int],
    seed: int,
    n_boot: int = 1000,
) -> tuple[float, float, float]:
    if len(original_flags) != len(perturbed_flags):
        raise RuntimeError("paired flags length mismatch")
    n = len(original_flags)
    if n == 0:
        return (0.0, 0.0, 0.0)
    diffs = [int(perturbed_flags[index]) - int(original_flags[index]) for index in range(n)]
    point = sum(diffs) / n
    rng = random.Random(seed)
    samples: list[float] = []
    for _ in range(n_boot):
        total = 0
        for _inner in range(n):
            total += diffs[rng.randrange(n)]
        samples.append(total / n)
    samples.sort()
    lo = samples[int(0.025 * (n_boot - 1))]
    hi = samples[int(0.975 * (n_boot - 1))]
    return (point, lo, hi)


def rate_stats(rows: list[dict[str, Any]]) -> dict[str, Any]:
    n = len(rows)
    flags = [int(bool(row["correct"])) for row in rows]
    rate = sum(flags) / n if n else 0.0
    chance = sum(1.0 / int(row["n_options"]) for row in rows) / n if n else 0.0
    ci = scorer.bootstrap_ci(flags, 1000, 21 + n) if n else (0.0, 0.0)
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
        "lowerCiAboveChance": n >= 10 and lower > CHANCE,
        "lowerCiAboveModal": n >= 10 and lower > modal_frequency,
        "clearsBar": n >= 10 and lower > CHANCE and lower > modal_frequency,
    }


def apply_reading(faithful_row: dict[str, Any]) -> str:
    preserving = faithful_row["rankPreserving"]
    paired = faithful_row["pairedRankPreserving"]
    if preserving["clearsBar"] and paired["ci95"][0] <= 0.0 <= paired["ci95"][1]:
        return (
            "form-based: the rank-preserving faithful rate clears the channel bar "
            "and the paired difference CI includes 0; the contamination concern is not supported"
        )
    if not preserving["lowerCiAboveChance"]:
        return (
            "not a form effect: the rank-preserving faithful lower CI is not strictly "
            "above chance 0.25"
        )
    return (
        "mixed: neither polar reading; the rank-preserving faithful rate did not both "
        "clear the bar and have a paired difference CI that includes 0, and it did not "
        "fall to chance"
    )


def record_reproduction_stop(model_key: str, reproduction: dict[str, Any], prereg_sha: str) -> None:
    report = {
        "status": "stopped_reproduction_failed",
        "model": model_key,
        "reproduction": reproduction,
        "preregistrationSha256": prereg_sha,
    }
    (OUT_DIR / "reproduction-report.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(
        f"stopped {model_key} perturbed arms; "
        f"reproduction {reproduction['agreement']:.4f} below {MIN_REPRODUCTION}",
        flush=True,
    )


def summarize(base_items: list[dict[str, Any]], reproductions: dict[str, dict[str, Any]]) -> dict[str, Any]:
    subsets = build_subsets(base_items)
    excluded = no_numeral_ids()
    sanity = json.loads((OUT_DIR / "sanity-examples.json").read_text(encoding="utf-8"))
    models_out: dict[str, Any] = {}
    stopped: list[str] = []
    for model_key, spec in MODELS.items():
        if not model_complete(model_key, len(base_items)):
            original_path = scores_path(model_key, ARM_ORIGINAL)
            if original_path.exists() and model_key in reproductions:
                models_out[model_key] = {
                    "label": spec["label"],
                    "modelId": spec["model_id"],
                    "modelRevision": spec["revision"],
                    "reproduction": reproductions[model_key],
                    "reading": "not scored: original letter agreement was below 0.98",
                    "subsets": None,
                    "status": "stopped_reproduction_failed",
                }
                stopped.append(model_key)
            continue
        scores = {
            ARM_ORIGINAL: load_jsonl_by_id(scores_path(model_key, ARM_ORIGINAL)),
            ARM_PRESERVING: load_jsonl_by_id(scores_path(model_key, ARM_PRESERVING)),
            ARM_SCRAMBLED: load_jsonl_by_id(scores_path(model_key, ARM_SCRAMBLED)),
        }
        subset_rows: dict[str, Any] = {}
        for subset_key, _label in SUBSET_SPECS:
            ids = subsets[subset_key]
            original_rows = [scores[ARM_ORIGINAL][item_id] for item_id in ids]
            preserving_rows = [scores[ARM_PRESERVING][item_id] for item_id in ids]
            scrambled_rows = [scores[ARM_SCRAMBLED][item_id] for item_id in ids]
            paired_ids = [item_id for item_id in ids if item_id not in excluded]
            original_paired = [int(bool(scores[ARM_ORIGINAL][item_id]["correct"])) for item_id in paired_ids]
            preserving_paired = [
                int(bool(scores[ARM_PRESERVING][item_id]["correct"])) for item_id in paired_ids
            ]
            scrambled_paired = [
                int(bool(scores[ARM_SCRAMBLED][item_id]["correct"])) for item_id in paired_ids
            ]
            n_paired = len(paired_ids)
            preserving_diff = paired_difference_ci(
                original_paired, preserving_paired, seed=31 + n_paired
            )
            scrambled_diff = paired_difference_ci(
                original_paired, scrambled_paired, seed=31 + n_paired
            )
            subset_rows[subset_key] = {
                "n": len(ids),
                "nPaired": n_paired,
                "nNoNumeral": len(ids) - n_paired,
                "original": rate_stats(original_rows),
                "rankPreserving": rate_stats(preserving_rows),
                "scrambled": rate_stats(scrambled_rows),
                "pairedRankPreserving": {
                    "n": n_paired,
                    "mean": preserving_diff[0],
                    "ci95": [preserving_diff[1], preserving_diff[2]],
                    "includesZero": preserving_diff[1] <= 0.0 <= preserving_diff[2],
                },
                "pairedScrambled": {
                    "n": n_paired,
                    "mean": scrambled_diff[0],
                    "ci95": [scrambled_diff[1], scrambled_diff[2]],
                    "includesZero": scrambled_diff[1] <= 0.0 <= scrambled_diff[2],
                },
            }
        faithful = subset_rows["algebra_i_faithful"]
        models_out[model_key] = {
            "label": spec["label"],
            "modelId": spec["model_id"],
            "modelRevision": spec["revision"],
            "reproduction": reproductions[model_key],
            "reading": apply_reading(faithful),
            "subsets": subset_rows,
        }
    payload = {
        "status": "complete" if not stopped else "stopped_reproduction_failed",
        "stoppedModels": stopped,
        "preregistration": "exports/isomorph-options/preregistration.md",
        "preregistrationSha256": check_preregistration(),
        "seed": SEED,
        "maskingHash": "v1",
        "maskingPreregistrationSha256": "af473bb6cd9d46dc74e034f4460d56a808273fe83ffaf457cd7d122c40ae80e8",
        "chance": CHANCE,
        "noNumeral": {
            "algebra-i": sanity["noNumeral"]["algebra-i"]["n"],
            "algebra-ii": sanity["noNumeral"]["algebra-ii"]["n"],
            "total": sanity["noNumeral"]["algebra-i"]["n"] + sanity["noNumeral"]["algebra-ii"]["n"],
        },
        "models": models_out,
        "writtenAt": datetime.now(timezone.utc).isoformat(),
    }
    return payload


def fmt_ci(ci: list[float]) -> str:
    return f"[{ci[0]:.3f}, {ci[1]:.3f}]"


def yes_no(flag: bool) -> str:
    return "yes" if flag else "no"


def write_readme(payload: dict[str, Any]) -> None:
    sanity = json.loads((OUT_DIR / "sanity-examples.json").read_text(encoding="utf-8"))
    example_lines: list[str] = []
    for example in sanity["examples"]:
        example_lines.append(f"### `{example['id']}`")
        example_lines.append("")
        example_lines.append(f"- original: `{json.dumps(example['original'], ensure_ascii=False)}`")
        example_lines.append(
            f"- rank-preserving: `{json.dumps(example['rankPreserving'], ensure_ascii=False)}`"
        )
        example_lines.append(
            f"- scrambled: `{json.dumps(example['rankScrambled'], ensure_ascii=False)}`"
        )
        example_lines.append("")
    table_lines = [
        "| model | subset | n | original | rank-preserving | scrambled | paired Δ preserving 95% CI | preserving bar | scrambled bar |",
        "|---|---|---:|---|---|---|---|---|---|",
    ]
    for model_key, _spec in MODELS.items():
        model = payload["models"].get(model_key)
        if model is None or model.get("subsets") is None:
            continue
        for subset_key, label in SUBSET_SPECS:
            row = model["subsets"][subset_key]
            table_lines.append(
                f"| {model['label']} | {label} | {row['n']} | "
                f"{row['original']['passRate']:.3f} {fmt_ci(row['original']['ci95'])} | "
                f"{row['rankPreserving']['passRate']:.3f} {fmt_ci(row['rankPreserving']['ci95'])} | "
                f"{row['scrambled']['passRate']:.3f} {fmt_ci(row['scrambled']['ci95'])} | "
                f"{row['pairedRankPreserving']['mean']:+.3f} {fmt_ci(row['pairedRankPreserving']['ci95'])} | "
                f"{yes_no(row['rankPreserving']['clearsBar'])} | "
                f"{yes_no(row['scrambled']['clearsBar'])} |"
            )
    repro_lines = []
    reading_lines = []
    for model_key, _spec in MODELS.items():
        model = payload["models"].get(model_key)
        if model is None:
            continue
        repro = model["reproduction"]
        repro_lines.append(
            f"- {model['label']}: {repro['nAgree']}/{repro['n']} = {repro['agreement']:.4f} "
            f"vs saved `{repro['savedPath']}`"
        )
        reading_lines.append(f"- {model['label']}: {model['reading']}")
    text = f"""# Option-numeral isomorphs (masked-stem contamination control)

Review-2 W4 Q4 and W8. The reader sees the same masked stem and the same key letter. Numerals in the option strings are replaced by value-changing, form-preserving isomorphs. If the rate holds, the reader is using form. If it collapses toward chance, the original rate is not a form effect.

Preregistration: `preregistration.md`, sha256 `{payload['preregistrationSha256']}`, written before scoring. Seed 20260916. Masking hash v1. CUDA letter-logprob argmax reused from `scripts/score_choices_only_local_lm.py`. Does not edit `paper/`.

## Reproduction of saved original letters

{chr(10).join(repro_lines)}

Floor was 0.98. Perturbed arms were scored only for models that cleared it. Models below the floor are listed in `results.json` `stoppedModels` and their perturbed arms were not scored.

## Pre-registered reading (Algebra I print-faithful, rank-preserving)

{chr(10).join(reading_lines)}

## no_numeral

Items with no numeral in any option are unchanged and are excluded from the paired difference.

- Algebra I: {payload['noNumeral']['algebra-i']}
- Algebra II: {payload['noNumeral']['algebra-ii']}
- Total: {payload['noNumeral']['total']}

## Rates

Bar: n >= 10 and lower bootstrap 95% CI strictly above chance 0.25 and above the subset modal-letter frequency. Paired Δ is perturbed minus original on items that are not `no_numeral`. Chance is 0.25 (mean 1/k on these 4-option items). Bootstrap: `random.Random.randrange`, 1000 replicates, rate seed `21 + n`, paired seed `31 + n`.

{chr(10).join(table_lines)}

## Sanity examples (before / after)

Digit counts, signs, decimal places, nonzero denominators, consistent substitution, and rank order on the rank-preserving arm were asserted in `scripts/perturb_option_numerals.py` before GPU scoring.

{chr(10).join(example_lines).rstrip()}

## Files

- `preregistration.md`, `preregistration.sha256`
- `perturbed-items-isomorph_rank_preserving.jsonl`, `perturbed-items-isomorph_rank_scrambled.jsonl`
- `scores-{{7b,14b,phi4}}-{{original,isomorph_rank_preserving,isomorph_rank_scrambled}}.jsonl`
- `results.json`, `sanity-examples.json`

Scripts: `scripts/perturb_option_numerals.py`, `scripts/score_isomorph_options.py`.
"""
    (OUT_DIR / "README.md").write_text(text, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--model",
        choices=["7b", "14b", "phi4", "all"],
        default="all",
    )
    parser.add_argument(
        "--summarize-only",
        action="store_true",
        help="Write results.json and README.md from existing score files.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
    prereg_sha = check_preregistration()
    print(f"preregistration sha256 {prereg_sha}", flush=True)
    base_items = prepare_base_items()
    original_choices = {str(item["id"]): dict(item["choices"]) for item in base_items}
    perturbed_choices = {arm: load_perturbed_choices(arm) for arm in ARMS}
    model_keys = list(MODELS) if args.model == "all" else [args.model]
    reproductions: dict[str, dict[str, Any]] = {}
    if not args.summarize_only:
        device = scorer.require_cuda()
        gpu_name = torch.cuda.get_device_name(0)
        print(f"GPU {gpu_name} device={device}", flush=True)
        for model_key in model_keys:
            n_items = len(base_items)
            if arm_complete(model_key, ARM_ORIGINAL, n_items):
                original_rows = load_jsonl(scores_path(model_key, ARM_ORIGINAL))
                reproduction = reproduction_agreement(
                    original_rows, SAVED_PREDICTIONS[model_key]
                )
                reproductions[model_key] = reproduction
                print(
                    f"original {model_key} already scored; "
                    f"reproduction {reproduction['agreement']:.4f} "
                    f"{reproduction['nAgree']}/{reproduction['n']}",
                    flush=True,
                )
                if not reproduction["clearsFloor"]:
                    record_reproduction_stop(model_key, reproduction, prereg_sha)
                    continue
                if model_complete(model_key, n_items):
                    print(f"skip {model_key} already scored", flush=True)
                    continue
            spec = MODELS[model_key]
            print(f"loading {spec['model_id']} {spec['revision']}", flush=True)
            model, tokenizer = load_causal_lm(model_key, device)
            original_items = attach_choices(base_items, original_choices)
            original_rows = score_arm(
                model,
                tokenizer,
                device,
                original_items,
                model_key,
                ARM_ORIGINAL,
                int(spec["batch_size"]),
            )
            reproduction = reproduction_agreement(original_rows, SAVED_PREDICTIONS[model_key])
            reproductions[model_key] = reproduction
            print(
                f"reproduction {model_key} {reproduction['agreement']:.4f} "
                f"{reproduction['nAgree']}/{reproduction['n']}",
                flush=True,
            )
            if not reproduction["clearsFloor"]:
                record_reproduction_stop(model_key, reproduction, prereg_sha)
                model.to("cpu")
                del model
                del tokenizer
                free_cuda()
                continue
            for arm in ARMS:
                arm_items = attach_choices(base_items, perturbed_choices[arm])
                score_arm(
                    model,
                    tokenizer,
                    device,
                    arm_items,
                    model_key,
                    arm,
                    int(spec["batch_size"]),
                )
            model.to("cpu")
            del model
            del tokenizer
            free_cuda()
    if args.summarize_only or args.model == "all":
        if args.summarize_only:
            for model_key in MODELS:
                original_path = scores_path(model_key, ARM_ORIGINAL)
                if not original_path.exists():
                    continue
                original_rows = load_jsonl(original_path)
                reproductions[model_key] = reproduction_agreement(
                    original_rows, SAVED_PREDICTIONS[model_key]
                )
        elif args.model != "all":
            return
        for model_key in MODELS:
            original_path = scores_path(model_key, ARM_ORIGINAL)
            if original_path.exists() and model_key not in reproductions:
                reproductions[model_key] = reproduction_agreement(
                    load_jsonl(original_path), SAVED_PREDICTIONS[model_key]
                )
        payload = summarize(base_items, reproductions)
        (OUT_DIR / "results.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        write_readme(payload)
        print(f"wrote {OUT_DIR / 'results.json'}", flush=True)
        print(f"wrote {OUT_DIR / 'README.md'}", flush=True)


if __name__ == "__main__":
    main()
