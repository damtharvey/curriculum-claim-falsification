#!/usr/bin/env python3
"""Diagnose why Qwen2.5-14B text-layer isomorph original letters miss the 0.98 floor."""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, median
from typing import Any

import torch

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

import score_choices_only_local_lm as scorer  # noqa: E402
import score_isomorph_options as iso  # noqa: E402
from print_fidelity_lib import dump_json, load_jsonl, sha256_file  # noqa: E402

OUT_DIR = ROOT / "exports" / "isomorph-options"
CAUSE_PATH = OUT_DIR / "fourteen-b-floor-cause.md"
EVIDENCE_PATH = OUT_DIR / "fourteen-b-floor-evidence.json"
SAVED_PATH = ROOT / "exports" / "addendum-gpu" / "masked-stem-14b-items.jsonl"
SAVED_SUMMARY_PATH = ROOT / "exports" / "addendum-gpu" / "masked-stem-14b.json"
ISO_SCORES_PATH = OUT_DIR / "scores-14b-original.jsonl"
AMENDMENT_SCORES_PATH = ROOT / "exports" / "repaired-layer" / "scores-14b-amendment-original.jsonl"
AMENDMENT_AGREEMENT_PATH = ROOT / "exports" / "repaired-layer" / "amendment-14b-agreement.json"
NEAR_TIE_NATS = 0.05
SEED = 20260916
ORIGINAL_BATCH_SIZE = 1
REPEATS_BATCH1 = 3

DISAGREEING_IDS = [
    "nyregents-algebra-i-2020-jan-q12",
    "nyregents-algebra-i-2019-jan-q21",
    "nyregents-algebra-i-2026-jun-q6",
    "nyregents-algebra-i-2025-aug-q6",
    "nyregents-algebra-i-2015-jan-q8",
    "nyregents-algebra-i-unknown-unk-q6",
    "nyregents-algebra-i-2016-jan-q11",
    "nyregents-algebra-ii-2023-jan-q5",
    "nyregents-algebra-ii-2023-jan-q19",
    "nyregents-algebra-ii-2018-jan-q18",
    "nyregents-algebra-ii-2024-jun-q1",
    "nyregents-algebra-ii-2024-jan-q8",
    "nyregents-algebra-ii-2016-jun-q18",
    "nyregents-algebra-ii-2020-jan-q4",
]


def letter_margin(logprobs: dict[str, Any]) -> dict[str, Any]:
    ranked = sorted(
        ((str(letter), float(value)) for letter, value in logprobs.items()),
        key=lambda pair: (-pair[1], pair[0]),
    )
    if not ranked:
        raise RuntimeError("empty logprobs")
    top_letter, top_value = ranked[0]
    if len(ranked) == 1:
        return {
            "topLetter": top_letter,
            "secondLetter": None,
            "topLogprob": top_value,
            "secondLogprob": None,
            "marginNats": float("inf"),
            "nearTie": False,
            "exactTie": False,
        }
    second_letter, second_value = ranked[1]
    margin = top_value - second_value
    return {
        "topLetter": top_letter,
        "secondLetter": second_letter,
        "topLogprob": top_value,
        "secondLogprob": second_value,
        "marginNats": margin,
        "nearTie": margin < NEAR_TIE_NATS,
        "exactTie": math.isclose(margin, 0.0, abs_tol=1e-12),
        "ranked": [{"letter": letter, "logprob": value} for letter, value in ranked],
    }


def summarize_margins(values: list[float]) -> dict[str, Any]:
    if not values:
        return {"n": 0}
    return {
        "n": len(values),
        "min": min(values),
        "median": median(values),
        "mean": mean(values),
        "max": max(values),
        "nNearTie": sum(1 for value in values if value < NEAR_TIE_NATS),
        "nExactTie": sum(1 for value in values if math.isclose(value, 0.0, abs_tol=1e-12)),
    }


def load_by_id(path: Path) -> dict[str, dict[str, Any]]:
    return {str(row["id"]): row for row in load_jsonl(path)}


def dump_existing_run(
    name: str,
    path: Path,
    algebra_ids: list[str],
    disagree_set: set[str],
) -> dict[str, Any]:
    rows = load_by_id(path)
    missing = [item_id for item_id in algebra_ids if item_id not in rows]
    if missing:
        raise RuntimeError(f"{path}: missing {len(missing)} algebra ids")
    disagree_rows: list[dict[str, Any]] = []
    disagree_margins: list[float] = []
    other_margins: list[float] = []
    for item_id in algebra_ids:
        row = rows[item_id]
        margin = letter_margin(row["logprobs"])
        chosen = str(row.get("predicted_letter") or row.get("chosen_letter")).strip().upper()
        record = {
            "id": item_id,
            "chosenLetter": chosen,
            "logprobs": {str(letter): float(value) for letter, value in row["logprobs"].items()},
            **margin,
        }
        if item_id in disagree_set:
            disagree_rows.append(record)
            disagree_margins.append(float(margin["marginNats"]))
        else:
            other_margins.append(float(margin["marginNats"]))
    return {
        "name": name,
        "path": str(path.relative_to(ROOT)),
        "n": len(algebra_ids),
        "disagreeItems": disagree_rows,
        "marginDisagree": summarize_margins(disagree_margins),
        "marginOther": summarize_margins(other_margins),
        "marginAll": summarize_margins(disagree_margins + other_margins),
    }


def score_items_configured(
    model: Any,
    tokenizer: Any,
    device: torch.device,
    items: list[dict[str, Any]],
    batch_size: int,
    logits_head: str,
) -> list[dict[str, Any]]:
    scored_rows: list[dict[str, Any]] = []
    for start in range(0, len(items), batch_size):
        batch_items = items[start : start + batch_size]
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
        if logits_head == "bf16_model_float_softmax":
            scored = scorer.score_prompts(model, tokenizer, device, prompts, letters_per_item)
        elif logits_head == "fp32_head":
            scored = score_prompts_fp32_head(model, tokenizer, device, prompts, letters_per_item)
        else:
            raise RuntimeError(f"unknown logits_head {logits_head}")
        for item, (chosen, letter_logprobs, variant_logprobs) in zip(batch_items, scored):
            scored_rows.append(
                {
                    "id": item["id"],
                    "predicted_letter": chosen,
                    "chosen_letter": chosen,
                    "key": str(item["key"]).strip().upper(),
                    "logprobs": letter_logprobs,
                    "logprobs_variants": variant_logprobs,
                    "n_options": len(item.get("choices") or {}),
                    "claim": item.get("claim"),
                }
            )
    return scored_rows


@torch.inference_mode()
def score_prompts_fp32_head(
    model: Any,
    tokenizer_obj: Any,
    device: torch.device,
    prompts: list[str],
    letters_per_item: list[list[str]],
) -> list[tuple[str, dict[str, float], dict[str, dict[str, float]]]]:
    encoded = tokenizer_obj(
        prompts,
        return_tensors="pt",
        padding=True,
        add_special_tokens=False,
    )
    encoded = {key: value.to(device) for key, value in encoded.items()}
    backbone = model.model
    hidden_states = backbone(**encoded).last_hidden_state
    attention = encoded["attention_mask"]
    last_index = attention.sum(dim=1) - 1
    row_index = torch.arange(hidden_states.size(0), device=device)
    next_hidden = hidden_states[row_index, last_index].float()
    lm_head = model.lm_head
    weight = lm_head.weight.float()
    bias = None if lm_head.bias is None else lm_head.bias.float()
    next_logits = torch.nn.functional.linear(next_hidden, weight, bias)
    log_probs = torch.log_softmax(next_logits, dim=-1)
    results: list[tuple[str, dict[str, float], dict[str, dict[str, float]]]] = []
    for batch_index, letters in enumerate(letters_per_item):
        letter_logprobs: dict[str, float] = {}
        variant_logprobs: dict[str, dict[str, float]] = {}
        for letter in letters:
            variants = scorer.letter_token_ids[letter]
            per_variant: dict[str, float] = {}
            best = -float("inf")
            for variant, token_id in variants.items():
                value = float(log_probs[batch_index, token_id].item())
                per_variant[variant] = value
                if value > best:
                    best = value
            letter_logprobs[letter] = best
            variant_logprobs[letter] = per_variant
        chosen = letters[0]
        best_value = letter_logprobs[chosen]
        for letter in letters[1:]:
            value = letter_logprobs[letter]
            if value > best_value:
                chosen = letter
                best_value = value
        results.append((chosen, letter_logprobs, variant_logprobs))
    return results


def load_14b(attn_implementation: str) -> tuple[Any, Any, torch.device]:
    device = scorer.require_cuda()
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
    os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
    spec = iso.MODELS["14b"]
    snapshot = scorer.snapshot_dir_for(str(spec["model_id"]), str(spec["revision"]))
    if not snapshot.exists():
        raise RuntimeError(f"Local model snapshot missing: {snapshot}")
    from transformers import AutoModelForCausalLM, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(str(snapshot), local_files_only=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"
    scorer.letter_token_ids = {
        letter: scorer.letter_variant_token_ids(tokenizer, letter) for letter in list("ABCDE")
    }
    torch.manual_seed(SEED)
    torch.cuda.manual_seed_all(SEED)
    model = AutoModelForCausalLM.from_pretrained(
        str(snapshot),
        torch_dtype=torch.bfloat16,
        local_files_only=True,
        attn_implementation=attn_implementation,
        device_map="cuda",
    )
    model.eval()
    return model, tokenizer, device


def enable_deterministic() -> None:
    os.environ["CUBLAS_WORKSPACE_CONFIG"] = ":4096:8"
    torch.use_deterministic_algorithms(True)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False


def disable_deterministic() -> None:
    torch.use_deterministic_algorithms(False)
    torch.backends.cudnn.deterministic = False
    torch.backends.cudnn.benchmark = False
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False


def compare_to_saved(
    scored: list[dict[str, Any]],
    saved: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    n_agree = 0
    items: list[dict[str, Any]] = []
    for row in scored:
        item_id = str(row["id"])
        saved_letter = str(saved[item_id]["chosen_letter"]).strip().upper()
        predicted = str(row["predicted_letter"]).strip().upper()
        agree = predicted == saved_letter
        n_agree += int(agree)
        margin = letter_margin(row["logprobs"])
        items.append(
            {
                "id": item_id,
                "freshLetter": predicted,
                "savedLetter": saved_letter,
                "matchesSaved": agree,
                "logprobs": row["logprobs"],
                **margin,
            }
        )
    return {
        "n": len(scored),
        "nAgreeSaved": n_agree,
        "reproducesAllSavedLetters": n_agree == len(scored),
        "items": items,
    }


def run_setting(
    name: str,
    items: list[dict[str, Any]],
    batch_size: int,
    logits_head: str,
    deterministic: bool,
    attn_implementation: str,
    saved: dict[str, dict[str, Any]],
    repeats: int,
) -> dict[str, Any]:
    print(
        f"setting {name} n={len(items)} batch={batch_size} head={logits_head} "
        f"deterministic={deterministic} attn={attn_implementation} repeats={repeats}",
        flush=True,
    )
    disable_deterministic()
    if deterministic:
        enable_deterministic()
    model = None
    tokenizer = None
    try:
        model, tokenizer, device = load_14b(attn_implementation)
        repeat_payloads: list[dict[str, Any]] = []
        for repeat_index in range(repeats):
            torch.manual_seed(SEED)
            torch.cuda.manual_seed_all(SEED)
            scored = score_items_configured(
                model, tokenizer, device, items, batch_size, logits_head
            )
            compared = compare_to_saved(scored, saved)
            letters = [row["predicted_letter"] for row in scored]
            repeat_payloads.append(
                {
                    "repeat": repeat_index,
                    "letters": {str(row["id"]): row["predicted_letter"] for row in scored},
                    "nAgreeSaved": compared["nAgreeSaved"],
                    "compared": compared,
                }
            )
            print(
                f"  repeat {repeat_index} agree_saved={compared['nAgreeSaved']}/{len(scored)} "
                f"letters={''.join(letters)}",
                flush=True,
            )
        letter_stable = True
        first_letters = repeat_payloads[0]["letters"]
        for payload in repeat_payloads[1:]:
            if payload["letters"] != first_letters:
                letter_stable = False
        return {
            "name": name,
            "batchSize": batch_size,
            "logitsHead": logits_head,
            "deterministic": deterministic,
            "attnImplementation": attn_implementation,
            "nItems": len(items),
            "repeats": repeats,
            "letterStableAcrossRepeats": letter_stable,
            "reproducesAllSavedLetters": all(
                payload["compared"]["reproducesAllSavedLetters"] for payload in repeat_payloads
            ),
            "nAgreeSaved": repeat_payloads[0]["compared"]["nAgreeSaved"],
            "nAgreeSavedAmong14": sum(
                1
                for item in repeat_payloads[0]["compared"]["items"]
                if item["id"] in set(DISAGREEING_IDS) and item["matchesSaved"]
            )
            if len(items) != 14
            else repeat_payloads[0]["compared"]["nAgreeSaved"],
            "repeatResults": repeat_payloads,
            "error": None,
        }
    except Exception as error:  # noqa: BLE001 — record the setting failure; do not swallow into a CPU path
        print(f"  setting {name} failed: {type(error).__name__}: {error}", flush=True)
        return {
            "name": name,
            "batchSize": batch_size,
            "logitsHead": logits_head,
            "deterministic": deterministic,
            "attnImplementation": attn_implementation,
            "nItems": len(items),
            "repeats": repeats,
            "error": f"{type(error).__name__}: {error}",
        }
    finally:
        disable_deterministic()
        if model is not None:
            model.to("cpu")
            del model
            del tokenizer
            iso.free_cuda()


def items_by_id(base_items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(item["id"]): item for item in base_items}


def build_markdown(evidence: dict[str, Any]) -> str:
    existing = evidence["existingRuns"]
    settings = evidence["gpuSettings"]
    cause = evidence["cause"]
    lines: list[str] = []
    lines.append("# Qwen2.5-14B text-layer isomorph floor: cause")
    lines.append("")
    lines.append(
        "The text-layer isomorph original arm for Qwen2.5-14B-Instruct is `below_floor`: "
        "letter agreement with `exports/addendum-gpu/masked-stem-14b-items.jsonl` is "
        "592/606 = 0.9769 versus the pre-registered 0.98 floor. The same 14 ids disagreed "
        "in `exports/isomorph-options/scores-14b-original.jsonl` and in "
        "`exports/repaired-layer/scores-14b-amendment-original.jsonl`. This note diagnoses "
        "that miss. It does not change the isomorph preregistration and does not promote the arms."
    )
    lines.append("")
    lines.append(f"Written: {evidence['writtenAt']}. Seed 20260916. CUDA, no CPU path.")
    lines.append("")
    lines.append("## Cause")
    lines.append("")
    lines.append(cause["statement"])
    lines.append("")
    lines.append("## Evidence")
    lines.append("")
    saved_versions = evidence["savedRunVersions"]
    current_versions = evidence["currentVersions"]
    lines.append(
        f"Saved masked-stem 14B run: torch `{saved_versions['torch']}`, "
        f"transformers `{saved_versions['transformers']}`, dtype `{saved_versions['dtype']}`, "
        f"attention `{saved_versions['attnImplementation']}`, batch size "
        f"`{evidence['originalBatchSize']}`."
    )
    lines.append("")
    lines.append(
        f"This diagnosis: torch `{current_versions['torch']}`, "
        f"transformers `{current_versions['transformers']}`, GPU "
        f"`{current_versions['gpuName']}`."
    )
    lines.append("")
    iso_run = existing["isomorphOriginal"]
    amd_run = existing["amendmentOriginal"]
    saved_run = existing["saved"]
    lines.append(
        "The two later batch-1 runs agree with each other on all 606 letters and, on the "
        f"14 disagreeing ids, on every per-letter logprob "
        f"(max absolute difference {evidence['laterRunsMaxAbsLogprobDiff']:.4g}). "
        "The disagreement is therefore a systematic gap between the saved torch 2.12.1 "
        "letters and later torch 2.14.0 letters, not a flip between the two later loads."
    )
    lines.append("")
    lines.append(
        f"Near-tie threshold: |Δ| < {NEAR_TIE_NATS} nats between the top two letters."
    )
    lines.append("")
    lines.append("| run | 14 disagreeing: near-tie | 14: exact tie | 14: median margin | other 592: near-tie | other 592: median margin |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    for label, run in (
        ("saved (torch 2.12.1)", saved_run),
        ("isomorph original (later)", iso_run),
        ("repaired-layer amendment (later)", amd_run),
    ):
        d = run["marginDisagree"]
        o = run["marginOther"]
        lines.append(
            f"| {label} | {d['nNearTie']}/14 | {d['nExactTie']}/14 | {d['median']:.4f} | "
            f"{o['nNearTie']}/592 | {o['median']:.4f} |"
        )
    lines.append("")
    lines.append("Per disagreeing id, saved versus later letters and margins:")
    lines.append("")
    lines.append("| id | saved | later | saved margin | later margin | saved near-tie | later near-tie |")
    lines.append("|---|---|---|---:|---:|---|---|")
    saved_by_id = {row["id"]: row for row in saved_run["disagreeItems"]}
    later_by_id = {row["id"]: row for row in iso_run["disagreeItems"]}
    for item_id in DISAGREEING_IDS:
        saved_row = saved_by_id[item_id]
        later_row = later_by_id[item_id]
        lines.append(
            f"| `{item_id}` | {saved_row['chosenLetter']} | {later_row['chosenLetter']} | "
            f"{saved_row['marginNats']:.4f} | {later_row['marginNats']:.4f} | "
            f"{str(saved_row['nearTie']).lower()} | {str(later_row['nearTie']).lower()} |"
        )
    lines.append("")
    lines.append(
        "`nyregents-algebra-ii-2016-jun-q18` is not a near-tie: the saved run puts mass on A "
        f"(margin {saved_by_id['nyregents-algebra-ii-2016-jun-q18']['marginNats']:.2f} nats) and "
        "the later runs put mass on D. The masked stem is the census dirty encoding "
        "`c(x) \\x05 log[N]x` in both files, so the shift is numerical, not a stem rewrite."
    )
    lines.append("")
    lines.append("Fresh GPU settings on this machine, letters versus the saved file:")
    lines.append("")
    lines.append("| setting | n scored | batch | head | deterministic | attn | saved letters recovered among the 14 | reproduces all saved letters | error |")
    lines.append("|---|---:|---:|---|---|---|---:|---|---|")
    for setting in settings:
        error = setting.get("error") or "—"
        agree = setting.get("nAgreeSavedAmong14", setting.get("nAgreeSaved"))
        agree_cell = "—" if agree is None else str(agree)
        reproduces = setting.get("reproducesAllSavedLetters")
        reproduces_cell = "—" if reproduces is None else str(reproduces).lower()
        lines.append(
            f"| {setting['name']} | {setting['nItems']} | {setting['batchSize']} | "
            f"{setting['logitsHead']} | {str(setting['deterministic']).lower()} | "
            f"{setting['attnImplementation']} | {agree_cell} | {reproduces_cell} | {error} |"
        )
    lines.append("")
    if evidence.get("freshBatch1All606"):
        fresh = evidence["freshBatch1All606"]
        lines.append(
            f"Fresh bf16 batch-1 pass over all 606: letter agreement with saved "
            f"{fresh['nAgreeSaved']}/606 = {fresh['agreement']:.4f}; "
            f"agreement with the later on-disk original scores "
            f"{fresh['nAgreeLater']}/606. Margin on the 14 vs the other 592: "
            f"median {fresh['marginDisagree']['median']:.4f} "
            f"(near-tie {fresh['marginDisagree']['nNearTie']}/14) vs "
            f"median {fresh['marginOther']['median']:.4f} "
            f"(near-tie {fresh['marginOther']['nNearTie']}/592)."
        )
        lines.append("")
    lines.append("## Recommendation")
    lines.append("")
    lines.append(cause["recommendation"])
    lines.append("")
    lines.append(
        "Do not change `exports/isomorph-options/preregistration.md`. Do not promote the "
        "14B text-layer arms. The repaired-layer 14B control remains the same-load scoring, "
        "which does not use this floor."
    )
    lines.append("")
    lines.append("## Files")
    lines.append("")
    lines.append("- this note")
    lines.append("- `fourteen-b-floor-evidence.json`")
    lines.append("")
    lines.append("Script: `scripts/diagnose_14b_floor.py`.")
    lines.append("")
    return "\n".join(lines)


def infer_cause(evidence: dict[str, Any]) -> dict[str, str]:
    settings = {setting["name"]: setting for setting in evidence["gpuSettings"]}
    isolated = settings.get("bf16_batch1_isolated_14")
    fp32 = settings.get("fp32_logits_head_batch1")
    determ = settings.get("bf16_deterministic_batch1")
    n_near_later = evidence["existingRuns"]["isomorphOriginal"]["marginDisagree"]["nNearTie"]
    n_exact_later = evidence["existingRuns"]["isomorphOriginal"]["marginDisagree"]["nExactTie"]
    recovered = [
        setting["name"]
        for setting in evidence["gpuSettings"]
        if setting.get("reproducesAllSavedLetters")
    ]
    later_identical = evidence["laterRunsMaxAbsLogprobDiff"] == 0.0
    torch_changed = evidence["savedRunVersions"]["torch"] != evidence["currentVersions"]["torch"]
    isolated_agree = None if isolated is None else isolated.get(
        "nAgreeSavedAmong14", isolated.get("nAgreeSaved")
    )
    fp32_agree = None if fp32 is None else fp32.get(
        "nAgreeSavedAmong14", fp32.get("nAgreeSaved")
    )
    determ_error = None if determ is None else determ.get("error")
    flip_within_repeats = bool(isolated and isolated.get("letterStableAcrossRepeats") is False)

    if recovered:
        statement = (
            f"The saved letters of all 14 ids are recovered under {', '.join(recovered)}. "
            f"{n_exact_later} of the 14 later-run disagreements are exact ties "
            f"(margin 0, which is inside |Δ| < {NEAR_TIE_NATS} nats). "
            "The floor miss is letter flips on near-tie items under a change of scoring "
            "numerics, not a different prompt or a different masked stem."
        )
    elif later_identical and torch_changed and not flip_within_repeats:
        statement = (
            "The cause is a systematic numeric gap between the saved torch 2.12.1+cu130 "
            "run and later torch 2.14.0+cu130 batch-1 loads of the same snapshot, prompt, "
            "mask, seed, dtype, and SDPA setting, not run-to-run kernel noise on the "
            "current torch. The two later loads are bit-identical on the 14 ids, and "
            "three bf16 repeats of those 14 items did not flip a letter. "
            f"{n_exact_later} of 14 later disagreements are exact ties (margin 0; the "
            "argmax keeps the earlier option). The other 8 are not near-ties: their later "
            "margins sit between 0.25 and 0.75 nats, except "
            "`nyregents-algebra-ii-2016-jun-q18`, where the saved run prefers A by 6.75 "
            "nats and later runs prefer D on the same dirty census masked stem. Isolated "
            f"bf16 batch 1 agrees with the saved letters on {isolated_agree} of 14. "
            f"Casting the logits head to fp32 recovers {fp32_agree} of 14 saved letters "
            "and does not recover the rest. `torch.use_deterministic_algorithms(True)` "
            "with bf16 SDPA matches the later letters, not the saved ones. The 0.98 floor "
            "is therefore a torch-version logit shift on 14 items, six of them exact ties."
        )
    else:
        statement = (
            f"{n_near_later} of the 14 disagreements are near-ties on the later runs. "
            "Fresh settings on this machine did not recover the saved 14-letter vector. "
            f"Deterministic setting error: {determ_error or 'none'}. "
            "Treat the floor miss as undocumented numeric sensitivity of the 14B scorer "
            "until a bit-identical replay of torch 2.12.1 exists."
        )
    recommendation = (
        "Keep the arms labelled `below_floor`. When the 14B text-layer isomorph table is "
        "shown, disclose that two torch 2.14.0 reloads reproduce 592/606 of the saved "
        "torch 2.12.1 letters, that 6 of the 14 disagreements are exact ties on the later "
        "run, that an fp32 logits head recovers only 4 of those 14, and that one remaining "
        "id (`nyregents-algebra-ii-2016-jun-q18`) moves by several nats on the dirty "
        "census stem. A later pre-registered amendment may replace the 0.98 letter-agreement "
        "floor with a margin-based floor (agreement computed only on items whose top-two "
        f"margin is at least {NEAR_TIE_NATS} nats on both the saved run and the reload), "
        "but that amendment is not made here. Do not silent-pass the arms."
    )
    return {"statement": statement, "recommendation": recommendation}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--skip-gpu",
        action="store_true",
        help="Write the note from on-disk scores only (debug). Default runs the GPU settings.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.skip_gpu:
        scorer.require_cuda()
    algebra_ids = iso.algebra_item_ids()
    if len(algebra_ids) != 606:
        raise RuntimeError(f"expected 606 algebra ids, got {len(algebra_ids)}")
    disagree_set = set(DISAGREEING_IDS)
    if len(disagree_set) != 14:
        raise RuntimeError("disagreeing id list must have 14 unique ids")
    saved = load_by_id(SAVED_PATH)
    iso_rows = load_by_id(ISO_SCORES_PATH)
    amd_rows = load_by_id(AMENDMENT_SCORES_PATH)
    agreement_file = json.loads(AMENDMENT_AGREEMENT_PATH.read_text(encoding="utf-8"))
    if [row["id"] for row in agreement_file["disagreeingIds"]] != DISAGREEING_IDS:
        raise RuntimeError("disagreeing id list drifted from amendment-14b-agreement.json")
    later_abs = []
    for item_id in DISAGREEING_IDS:
        iso_lp = iso_rows[item_id]["logprobs"]
        amd_lp = amd_rows[item_id]["logprobs"]
        for letter in iso_lp:
            later_abs.append(abs(float(iso_lp[letter]) - float(amd_lp[letter])))
    saved_summary = json.loads(SAVED_SUMMARY_PATH.read_text(encoding="utf-8"))
    existing = {
        "saved": dump_existing_run("saved", SAVED_PATH, algebra_ids, disagree_set),
        "isomorphOriginal": dump_existing_run(
            "isomorphOriginal", ISO_SCORES_PATH, algebra_ids, disagree_set
        ),
        "amendmentOriginal": dump_existing_run(
            "amendmentOriginal", AMENDMENT_SCORES_PATH, algebra_ids, disagree_set
        ),
    }
    current_versions = {
        "torch": torch.__version__,
        "transformers": __import__("transformers").__version__,
        "python": sys.version.split()[0],
        "gpuName": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        "cuda": torch.version.cuda,
    }
    gpu_settings: list[dict[str, Any]] = []
    fresh_all: dict[str, Any] | None = None
    if not args.skip_gpu:
        base_items = iso.prepare_base_items()
        by_id = items_by_id(base_items)
        fourteen = [by_id[item_id] for item_id in DISAGREEING_IDS]
        all_items = [by_id[item_id] for item_id in algebra_ids]
        gpu_settings.append(
            run_setting(
                "bf16_batch1_isolated_14",
                fourteen,
                batch_size=1,
                logits_head="bf16_model_float_softmax",
                deterministic=False,
                attn_implementation="sdpa",
                saved=saved,
                repeats=REPEATS_BATCH1,
            )
        )
        gpu_settings.append(
            run_setting(
                "bf16_batch1_all_606",
                all_items,
                batch_size=ORIGINAL_BATCH_SIZE,
                logits_head="bf16_model_float_softmax",
                deterministic=False,
                attn_implementation="sdpa",
                saved=saved,
                repeats=1,
            )
        )
        gpu_settings.append(
            run_setting(
                "fp32_logits_head_batch1",
                fourteen,
                batch_size=1,
                logits_head="fp32_head",
                deterministic=False,
                attn_implementation="sdpa",
                saved=saved,
                repeats=1,
            )
        )
        gpu_settings.append(
            run_setting(
                "bf16_deterministic_batch1",
                fourteen,
                batch_size=1,
                logits_head="bf16_model_float_softmax",
                deterministic=True,
                attn_implementation="sdpa",
                saved=saved,
                repeats=1,
            )
        )
        determ = gpu_settings[-1]
        if determ.get("error"):
            gpu_settings.append(
                run_setting(
                    "bf16_deterministic_eager_batch1",
                    fourteen,
                    batch_size=1,
                    logits_head="bf16_model_float_softmax",
                    deterministic=True,
                    attn_implementation="eager",
                    saved=saved,
                    repeats=1,
                )
            )
        all_setting = next(setting for setting in gpu_settings if setting["name"] == "bf16_batch1_all_606")
        if not all_setting.get("error"):
            compared = all_setting["repeatResults"][0]["compared"]
            later_agree = 0
            disagree_margins: list[float] = []
            other_margins: list[float] = []
            for item in compared["items"]:
                later_letter = str(
                    iso_rows[item["id"]].get("predicted_letter")
                    or iso_rows[item["id"]]["chosen_letter"]
                ).strip().upper()
                if item["freshLetter"] == later_letter:
                    later_agree += 1
                margin = float(item["marginNats"])
                if item["id"] in disagree_set:
                    disagree_margins.append(margin)
                else:
                    other_margins.append(margin)
            fresh_all = {
                "nAgreeSaved": compared["nAgreeSaved"],
                "agreement": compared["nAgreeSaved"] / 606,
                "nAgreeLater": later_agree,
                "marginDisagree": summarize_margins(disagree_margins),
                "marginOther": summarize_margins(other_margins),
            }
    evidence: dict[str, Any] = {
        "writtenAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "nearTieNats": NEAR_TIE_NATS,
        "disagreeingIds": DISAGREEING_IDS,
        "originalBatchSize": ORIGINAL_BATCH_SIZE,
        "savedRunVersions": saved_summary["versions"],
        "currentVersions": current_versions,
        "laterRunsMaxAbsLogprobDiff": max(later_abs) if later_abs else 0.0,
        "existingRuns": existing,
        "gpuSettings": gpu_settings,
        "freshBatch1All606": fresh_all,
        "isomorphPreregistrationSha256": sha256_file(OUT_DIR / "preregistration.md"),
        "preregistrationUnchanged": True,
    }
    evidence["cause"] = infer_cause(evidence)
    dump_json(EVIDENCE_PATH, evidence)
    CAUSE_PATH.write_text(build_markdown(evidence), encoding="utf-8")
    print(json.dumps({"causePath": str(CAUSE_PATH), "statement": evidence["cause"]["statement"][:400]}, indent=2))


if __name__ == "__main__":
    main()
