#!/usr/bin/env python3
"""Transcribe Algebra I/II crops with LLaVA and verify against Qwen transcription 1."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

import score_choices_only_local_lm as scorer  # noqa: E402
import score_isomorph_options as iso  # noqa: E402
from print_fidelity_lib import (  # noqa: E402
    DPI,
    FIDELITY_ITEMS_PATH,
    OPTION_MATCH_THRESHOLD,
    STEM_F1_THRESHOLD,
    TRANSCRIPTION_PROMPT_TEMPLATE,
    VERDICT_FAITHFUL,
    append_jsonl,
    clean_vlm_stem,
    dump_json,
    load_jsonl,
    parse_json_object,
    require_cuda,
    score_fidelity,
    sha256_file,
    transcribed_options,
    transcription_prompt,
)
from split_masked_stem_by_standard import (  # noqa: E402
    CLUSTER_CLASS,
    EXECUTION,
    MIXED,
    RECOGNITION,
)
from vlm_backsolve_lib import question_number  # noqa: E402

OUT_DIR = ROOT / "exports" / "repaired-layer-second-family"
PREREG_PATH = OUT_DIR / "preregistration.md"
PREREG_SHA_PATH = OUT_DIR / "preregistration.sha256"
TRANSCRIPTIONS_PATH = OUT_DIR / "transcriptions-llava.jsonl"
VERDICTS_PATH = OUT_DIR / "verdicts.jsonl"
RESULTS_PATH = OUT_DIR / "results.json"
README_PATH = OUT_DIR / "README.md"
REPAIRED_ITEMS_PATH = ROOT / "exports" / "repaired-layer" / "repaired-items.jsonl"
REPAIRED_MASKED_PATH = ROOT / "exports" / "repaired-layer" / "repaired-masked-items.jsonl"
REPAIRED_SCORES_DIR = ROOT / "exports" / "repaired-layer"
PERTURBED_PATH = ROOT / "exports" / "repaired-layer" / "perturbed-items-isomorph_rank_preserving.jsonl"
ITEM_STANDARDS_PATH = ROOT / "exports" / "standards-split" / "item-standards.jsonl"
ALGEBRA_IDS_PATH = ROOT / "exports" / "addendum-gpu" / "masked-stem-algebra-primary-item-ids.json"

MODEL_ID = "llava-hf/llava-v1.6-vicuna-13b-hf"
MODEL_REVISION = "745cfbdb14dfeff9bcc6eb731937102e88ea3024"
SNAPSHOT_PATH = (
    Path.home()
    / ".cache"
    / "huggingface"
    / "hub"
    / "models--llava-hf--llava-v1.6-vicuna-13b-hf"
    / "snapshots"
    / MODEL_REVISION
)
MODEL_MAX_INPUT_TOKENS = 4096
SEED = 20260916
MAX_NEW_TOKENS = 640
VERIFIED_CROSS_FAMILY = "verified_cross_family"
NOT_VERIFIED_CROSS_FAMILY = "not_verified_cross_family"
REPAIRED_VERIFIED = "repaired_verified"
MODEL_KEYS = ("7b", "14b", "phi4")
MODEL_LABELS = {
    "7b": "Qwen2.5-7B-Instruct",
    "14b": "Qwen2.5-14B-Instruct",
    "phi4": "Phi-4",
}
CHANCE = 0.25


def check_preregistration() -> str:
    if not PREREG_PATH.exists():
        raise RuntimeError(f"preregistration missing: {PREREG_PATH}")
    if not PREREG_SHA_PATH.exists():
        raise RuntimeError(f"preregistration sha256 missing: {PREREG_SHA_PATH}; freeze before scoring")
    recorded = PREREG_SHA_PATH.read_text(encoding="utf-8").split()[0]
    current = sha256_file(PREREG_PATH)
    if recorded != current:
        raise RuntimeError(f"preregistration changed after freeze: recorded {recorded} current {current}")
    prereg_text = PREREG_PATH.read_text(encoding="utf-8")
    prompt_head = TRANSCRIPTION_PROMPT_TEMPLATE.split("{qnum}")[0]
    if prompt_head not in prereg_text:
        raise RuntimeError("transcription prompt drifted from preregistration")
    if MODEL_ID not in prereg_text or MODEL_REVISION not in prereg_text:
        raise RuntimeError("model id or revision drifted from preregistration")
    return current


def algebra_primary_ids() -> list[str]:
    return [str(item_id) for item_id in json.loads(ALGEBRA_IDS_PATH.read_text(encoding="utf-8"))]


def snapshot_complete() -> None:
    if not SNAPSHOT_PATH.exists():
        raise RuntimeError(f"cached snapshot missing: {SNAPSHOT_PATH}")
    weight_index = SNAPSHOT_PATH / "model.safetensors.index.json"
    if not weight_index.exists():
        raise RuntimeError(f"weight index missing: {weight_index}")
    payload = json.loads(weight_index.read_text(encoding="utf-8"))
    shards = sorted(set(payload["weight_map"].values()))
    missing = [name for name in shards if not (SNAPSHOT_PATH / name).exists()]
    if missing:
        raise RuntimeError(f"cached shards missing under {SNAPSHOT_PATH}: {missing}")


def load_llava() -> tuple[Any, Any]:
    import torch
    from transformers import AutoProcessor, LlavaNextForConditionalGeneration

    require_cuda()
    snapshot_complete()
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
    os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
    torch.manual_seed(SEED)
    torch.cuda.manual_seed_all(SEED)
    processor = AutoProcessor.from_pretrained(
        str(SNAPSHOT_PATH),
        local_files_only=True,
        use_fast=False,
    )
    model = LlavaNextForConditionalGeneration.from_pretrained(
        str(SNAPSHOT_PATH),
        torch_dtype=torch.bfloat16,
        device_map="cuda",
        local_files_only=True,
        attn_implementation="sdpa",
    )
    model.eval()
    pad_token_id = processor.tokenizer.pad_token_id
    if pad_token_id is None:
        raise RuntimeError("LLaVA tokenizer has no pad_token_id")
    model.generation_config.pad_token_id = pad_token_id
    return processor, model


class ContextOverflowError(RuntimeError):
    def __init__(self, n_tokens: int):
        super().__init__(
            f"LLaVA input length {n_tokens} exceeds model max {MODEL_MAX_INPUT_TOKENS}"
        )
        self.n_tokens = n_tokens


def model_device(model: Any) -> Any:
    return next(model.parameters()).device


def generate_llava(processor: Any, model: Any, image_paths: list[Path], prompt: str) -> str:
    import torch
    from PIL import Image

    if not image_paths:
        raise RuntimeError("generate_llava requires at least one image")
    images = [Image.open(path).convert("RGB") for path in image_paths]
    content: list[dict[str, str]] = [{"type": "image"} for _ in images]
    content.append({"type": "text", "text": prompt})
    messages = [{"role": "user", "content": content}]
    text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    image_argument: Any = images[0] if len(images) == 1 else images
    inputs = processor(images=image_argument, text=text, return_tensors="pt")
    device = model_device(model)
    moved: dict[str, Any] = {}
    for key, value in inputs.items():
        if hasattr(value, "to"):
            tensor = value.to(device)
            if key == "pixel_values":
                tensor = tensor.to(dtype=torch.bfloat16)
            moved[key] = tensor
        else:
            moved[key] = value
    with torch.inference_mode():
        n_tokens = int(moved["input_ids"].shape[1])
        if n_tokens > MODEL_MAX_INPUT_TOKENS:
            raise ContextOverflowError(n_tokens)
        output_ids = model.generate(**moved, max_new_tokens=MAX_NEW_TOKENS, do_sample=False)
    generated = output_ids[0, n_tokens:]
    return processor.batch_decode([generated], skip_special_tokens=True)[0].strip()


def census_fidelity_by_id() -> dict[str, dict[str, Any]]:
    rows = [
        row
        for row in load_jsonl(FIDELITY_ITEMS_PATH)
        if row.get("stage") in ("calibration", "census")
    ]
    return {str(row["id"]): row for row in rows}


def repaired_items_by_id() -> dict[str, dict[str, Any]]:
    return {str(row["id"]): row for row in load_jsonl(REPAIRED_ITEMS_PATH)}


def page_image_paths(fidelity_row: dict[str, Any]) -> list[Path]:
    listed = [ROOT / str(relative) for relative in (fidelity_row.get("pngs") or [])]
    missing = [path for path in listed if not path.exists() or path.stat().st_size < 100]
    if listed and not missing:
        return listed
    if missing:
        raise RuntimeError(
            f"{fidelity_row['id']}: stored page render missing: "
            + ", ".join(str(path) for path in missing)
        )
    raise RuntimeError(f"{fidelity_row['id']}: no stored pngs on the print-faithful row")


def item_verb_class() -> dict[str, str]:
    out: dict[str, str] = {}
    for row in load_jsonl(ITEM_STANDARDS_PATH):
        code = str(row["standard"])
        if code not in CLUSTER_CLASS:
            raise KeyError(f"{row['id']}: cluster {code} has no class")
        out[str(row["id"])] = CLUSTER_CLASS[code][0]
    return out


def transcribe(limit: int) -> list[dict[str, Any]]:
    require_cuda()
    prereg_sha = check_preregistration()
    item_ids = algebra_primary_ids()
    if limit > 0:
        item_ids = item_ids[:limit]
    items_by_id = scorer.load_items()
    fidelity = census_fidelity_by_id()
    existing = {str(row["id"]): row for row in load_jsonl(TRANSCRIPTIONS_PATH)}
    pending = [item_id for item_id in item_ids if item_id not in existing]
    print(
        f"llava requested={len(item_ids)} already={len(item_ids) - len(pending)} "
        f"pending={len(pending)} prereg={prereg_sha[:12]}",
        flush=True,
    )
    processor = None
    model = None
    if pending:
        print(f"loading {MODEL_ID} {MODEL_REVISION}", flush=True)
        processor, model = load_llava()
        print("model loaded", flush=True)
    started = time.time()
    import torch

    for index, item_id in enumerate(pending, start=1):
        if item_id not in fidelity:
            raise RuntimeError(f"print-faithful row missing for {item_id}")
        item = items_by_id[item_id]
        qnum = question_number(item)
        if qnum is None:
            raise RuntimeError(f"no question number for {item_id}")
        png_paths = page_image_paths(fidelity[item_id])
        overflow_tokens: int | None = None
        try:
            raw = generate_llava(processor, model, png_paths, transcription_prompt(qnum))
            payload = parse_json_object(raw)
        except ContextOverflowError as error:
            raw = ""
            payload = None
            overflow_tokens = error.n_tokens
        row = {
            "id": item_id,
            "claim": item.get("claim"),
            "authority": item.get("authority"),
            "qnum": qnum,
            "pngs": [str(path.relative_to(ROOT)) for path in png_paths],
            "rawVlm": raw,
            "llavaStem": None if payload is None else clean_vlm_stem(payload, qnum),
            "llavaOptions": {} if payload is None else transcribed_options(payload),
            "parseable": payload is not None,
            "contextOverflowTokens": overflow_tokens,
            "modelId": MODEL_ID,
            "modelRevision": MODEL_REVISION,
            "dpi": DPI,
            "preregistrationSha256": prereg_sha,
            "scoredAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        append_jsonl(TRANSCRIPTIONS_PATH, row)
        existing[item_id] = row
        elapsed = time.time() - started
        overflow_note = "" if overflow_tokens is None else f" overflow={overflow_tokens}"
        print(
            f"[{index}/{len(pending)}] {item_id} parseable={row['parseable']} "
            f"opts={len(row['llavaOptions'])}{overflow_note} {elapsed:.0f}s ({elapsed / index:.1f}s/item)",
            flush=True,
        )
        torch.cuda.empty_cache()
    if model is not None:
        model.to("cpu")
        del model
        del processor
        iso.free_cuda()
    return [existing[item_id] for item_id in item_ids if item_id in existing]


def usable_transcription_one(repaired: dict[str, Any] | None) -> bool:
    if repaired is None:
        return False
    stem = str(repaired.get("stem") or "").strip()
    options = {str(letter): str(text) for letter, text in dict(repaired.get("options") or {}).items() if str(text).strip()}
    return bool(stem and len(options) >= 2)


def build_verdicts(item_ids: list[str]) -> list[dict[str, Any]]:
    check_preregistration()
    transcriptions = {str(row["id"]): row for row in load_jsonl(TRANSCRIPTIONS_PATH)}
    repaired = repaired_items_by_id()
    items_by_id = scorer.load_items()
    missing = [item_id for item_id in item_ids if item_id not in transcriptions]
    if missing:
        raise RuntimeError(f"transcriptions incomplete, missing {len(missing)} e.g. {missing[:5]}")
    rows: list[dict[str, Any]] = []
    if VERDICTS_PATH.exists():
        VERDICTS_PATH.unlink()
    for item_id in item_ids:
        item = items_by_id[item_id]
        llava = transcriptions[item_id]
        target = repaired.get(item_id)
        payload = parse_json_object(str(llava.get("rawVlm") or ""))
        if not usable_transcription_one(target) or payload is None:
            score_dict: dict[str, Any] = {
                "stem_f1": 0.0,
                "stem_precision": 0.0,
                "stem_recall": 0.0,
                "option_match": {},
                "option_count_equal": False,
                "fidelity_verdict": "unverified",
                "flags": ["missing_transcription"],
            }
            cross_verdict = NOT_VERIFIED_CROSS_FAMILY
        else:
            compare_item = dict(item)
            compare_item["stem"] = str(target["stem"])
            compare_item["choices"] = dict(target["options"])
            score = score_fidelity(
                compare_item,
                payload,
                stem_threshold=STEM_F1_THRESHOLD,
                option_threshold=OPTION_MATCH_THRESHOLD,
            )
            score_dict = {
                "stem_f1": score.stem_f1,
                "stem_precision": score.stem_precision,
                "stem_recall": score.stem_recall,
                "option_match": score.option_scores,
                "option_count_equal": score.option_count_equal,
                "fidelity_verdict": score.verdict,
                "flags": score.flags,
            }
            cross_verdict = (
                VERIFIED_CROSS_FAMILY if score.verdict == VERDICT_FAITHFUL else NOT_VERIFIED_CROSS_FAMILY
            )
        row = {
            "id": item_id,
            "claim": item.get("claim"),
            "authority": item.get("authority"),
            "qwen_repair_verdict": None if target is None else target.get("repair_verdict"),
            "transcription1_usable": usable_transcription_one(target),
            "verdict": cross_verdict,
            "llavaStem": llava.get("llavaStem"),
            "llavaOptions": llava.get("llavaOptions") or {},
            "transcription1_stem": None if target is None else target.get("stem"),
            "transcription1_options": None if target is None else target.get("options"),
            **score_dict,
        }
        append_jsonl(VERDICTS_PATH, row)
        rows.append(row)
    return rows


def load_predictions(path: Path) -> dict[str, dict[str, Any]]:
    return {str(row["id"]): row for row in load_jsonl(path)}


def subset_stats(predictions: dict[str, dict[str, Any]], ids: list[str]) -> dict[str, Any]:
    present = [item_id for item_id in ids if item_id in predictions]
    stats = iso.rate_stats([predictions[item_id] for item_id in present])
    stats["nRequested"] = len(ids)
    stats["nMissingScores"] = len(ids) - len(present)
    return stats


def fmt_ci(ci: list[float]) -> str:
    return f"[{ci[0]:.3f}, {ci[1]:.3f}]"


def yes_no(flag: bool) -> str:
    return "yes" if flag else "no"


def overlap_matrix(verdicts: list[dict[str, Any]]) -> dict[str, Any]:
    qwen_labels = (REPAIRED_VERIFIED, "repaired_unverified")
    llava_labels = (VERIFIED_CROSS_FAMILY, NOT_VERIFIED_CROSS_FAMILY)
    matrix = {qwen: {llava: 0 for llava in llava_labels} for qwen in qwen_labels}
    for row in verdicts:
        qwen = str(row.get("qwen_repair_verdict") or "repaired_unverified")
        if qwen not in matrix:
            qwen = "repaired_unverified"
        llava = str(row["verdict"])
        matrix[qwen][llava] += 1
    both = [
        str(row["id"])
        for row in verdicts
        if row.get("qwen_repair_verdict") == REPAIRED_VERIFIED
        and row["verdict"] == VERIFIED_CROSS_FAMILY
    ]
    return {
        "n": len(verdicts),
        "verified_cross_family": sum(1 for row in verdicts if row["verdict"] == VERIFIED_CROSS_FAMILY),
        "not_verified_cross_family": sum(
            1 for row in verdicts if row["verdict"] == NOT_VERIFIED_CROSS_FAMILY
        ),
        "qwen_repaired_verified": sum(
            1 for row in verdicts if row.get("qwen_repair_verdict") == REPAIRED_VERIFIED
        ),
        "both_checks": len(both),
        "bothCheckIds": both,
        "overlap": matrix,
    }


def id_lists(verdicts: list[dict[str, Any]]) -> dict[str, list[str]]:
    masked = {str(row["id"]): row for row in load_jsonl(REPAIRED_MASKED_PATH)}
    verb = item_verb_class()
    perturb_ok = {
        str(row["id"])
        for row in load_jsonl(PERTURBED_PATH)
        if not row.get("perturbFailed")
    }
    withheld = {
        item_id
        for item_id, row in masked.items()
        if row.get("withheld_quantity")
    }
    algebra_i = [str(row["id"]) for row in verdicts if row.get("claim") == "algebra-i"]
    algebra_ii = [str(row["id"]) for row in verdicts if row.get("claim") == "algebra-ii"]
    cross = {str(row["id"]) for row in verdicts if row["verdict"] == VERIFIED_CROSS_FAMILY}
    both = {
        str(row["id"])
        for row in verdicts
        if row["verdict"] == VERIFIED_CROSS_FAMILY and row.get("qwen_repair_verdict") == REPAIRED_VERIFIED
    }

    def scored_pool(pool: list[str], extra: set[str]) -> list[str]:
        return [item_id for item_id in pool if item_id in extra and item_id in withheld]

    def verb_ids(pool: list[str], verb_class: str) -> list[str]:
        return [item_id for item_id in pool if verb.get(item_id) == verb_class]

    return {
        "algebra_i_cross": scored_pool(algebra_i, cross),
        "algebra_ii_cross": scored_pool(algebra_ii, cross),
        "algebra_i_both": scored_pool(algebra_i, both),
        "algebra_ii_both": scored_pool(algebra_ii, both),
        "algebra_i_execution_cross": verb_ids(scored_pool(algebra_i, cross), EXECUTION),
        "algebra_i_recognition_cross": verb_ids(scored_pool(algebra_i, cross), RECOGNITION),
        "algebra_i_mixed_cross": verb_ids(scored_pool(algebra_i, cross), MIXED),
        "algebra_ii_execution_cross": verb_ids(scored_pool(algebra_ii, cross), EXECUTION),
        "algebra_ii_recognition_cross": verb_ids(scored_pool(algebra_ii, cross), RECOGNITION),
        "algebra_ii_mixed_cross": verb_ids(scored_pool(algebra_ii, cross), MIXED),
        "algebra_i_isomorph_cross": [
            item_id for item_id in scored_pool(algebra_i, cross) if item_id in perturb_ok
        ],
        "algebra_ii_isomorph_cross": [
            item_id for item_id in scored_pool(algebra_ii, cross) if item_id in perturb_ok
        ],
    }


def load_repaired_scores() -> dict[str, dict[str, dict[str, Any]]]:
    out: dict[str, dict[str, dict[str, Any]]] = {}
    for model_key in MODEL_KEYS:
        out[model_key] = {
            "repaired": load_predictions(REPAIRED_SCORES_DIR / f"scores-{model_key}-repaired.jsonl"),
            "isomorph": load_predictions(
                REPAIRED_SCORES_DIR / f"scores-{model_key}-repaired-isomorph_rank_preserving.jsonl"
            ),
        }
    return out


def summarize(verdicts: list[dict[str, Any]]) -> dict[str, Any]:
    check_preregistration()
    ids = id_lists(verdicts)
    scores = load_repaired_scores()
    overlap = overlap_matrix(verdicts)
    by_claim = {
        "algebra-i": [row for row in verdicts if row.get("claim") == "algebra-i"],
        "algebra-ii": [row for row in verdicts if row.get("claim") == "algebra-ii"],
    }
    verification = {
        "all": overlap,
        "algebra-i": overlap_matrix(by_claim["algebra-i"]),
        "algebra-ii": overlap_matrix(by_claim["algebra-ii"]),
    }
    masked_stem: dict[str, Any] = {}
    verb_class: dict[str, Any] = {}
    isomorph: dict[str, Any] = {}
    for model_key in MODEL_KEYS:
        repaired = scores[model_key]["repaired"]
        iso_scores = scores[model_key]["isomorph"]
        masked_stem[model_key] = {
            "label": MODEL_LABELS[model_key],
            "algebra_i_cross": subset_stats(repaired, ids["algebra_i_cross"]),
            "algebra_ii_cross": subset_stats(repaired, ids["algebra_ii_cross"]),
            "algebra_i_both": subset_stats(repaired, ids["algebra_i_both"]),
            "algebra_ii_both": subset_stats(repaired, ids["algebra_ii_both"]),
        }
        verb_class[model_key] = {
            "label": MODEL_LABELS[model_key],
            "algebra_i_execution_cross": subset_stats(repaired, ids["algebra_i_execution_cross"]),
            "algebra_i_recognition_cross": subset_stats(repaired, ids["algebra_i_recognition_cross"]),
            "algebra_ii_execution_cross": subset_stats(repaired, ids["algebra_ii_execution_cross"]),
            "algebra_ii_recognition_cross": subset_stats(repaired, ids["algebra_ii_recognition_cross"]),
        }
        isomorph[model_key] = {
            "label": MODEL_LABELS[model_key],
            "algebra_i_isomorph_cross": subset_stats(iso_scores, ids["algebra_i_isomorph_cross"]),
            "algebra_ii_isomorph_cross": subset_stats(iso_scores, ids["algebra_ii_isomorph_cross"]),
        }
    payload = {
        "status": "complete",
        "writtenAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "preregistrationSha256": check_preregistration(),
        "modelId": MODEL_ID,
        "modelRevision": MODEL_REVISION,
        "seed": SEED,
        "thresholds": {
            "stemF1": STEM_F1_THRESHOLD,
            "stemPrecision": STEM_F1_THRESHOLD,
            "stemRecall": STEM_F1_THRESHOLD,
            "optionMatch": OPTION_MATCH_THRESHOLD,
        },
        "nItems": len(verdicts),
        "nContextOverflow": sum(
            1
            for row in load_jsonl(TRANSCRIPTIONS_PATH)
            if row.get("contextOverflowTokens")
        ),
        "verification": verification,
        "idLists": {key: value for key, value in ids.items()},
        "maskedStem": masked_stem,
        "verbClass": verb_class,
        "isomorph": isomorph,
        "chance": CHANCE,
    }
    dump_json(RESULTS_PATH, payload)
    README_PATH.write_text(build_readme(payload), encoding="utf-8")
    return payload


def rate_line(stats: dict[str, Any]) -> str:
    return (
        f"{stats['n']} | {stats['passes']} | {stats['passRate']:.3f} | {stats['chance']:.3f} | "
        f"{fmt_ci(stats['ci95'])} | {stats['modalLetter']} ({stats['modalFrequency']:.3f}) | "
        f"{yes_no(stats['clearsBar'])}"
    )


def build_readme(payload: dict[str, Any]) -> str:
    verification = payload["verification"]
    lines: list[str] = []
    lines.append("# Second VLM family for the verification transcription")
    lines.append("")
    lines.append(
        "Review weakness 2: the repaired-layer verified set used two readings of one family "
        "(Qwen2-VL-7B-Instruct). This addendum transcribes the same 606 Algebra I and Algebra II "
        "crops with LLaVA-NeXT Vicuna 13B and marks an item `verified_cross_family` when that "
        "transcription agrees with Qwen transcription 1 under the print-fidelity thresholds."
    )
    lines.append("")
    lines.append(
        f"Preregistration: `preregistration.md`, sha256 `{payload['preregistrationSha256']}`, "
        "frozen before LLaVA scoring. Seed 20260916. No language-model re-scoring; rates join "
        "`exports/repaired-layer/scores-*.jsonl`. Does not edit `paper/`."
    )
    lines.append("")
    lines.append("A pass does not require the tagged operation. Nothing here says students did not learn.")
    lines.append("")
    missed: list[str] = []
    for model_key, cell, subset_key in (
        ("7b", "Algebra I", "algebra_i_cross"),
        ("7b", "Algebra II", "algebra_ii_cross"),
        ("14b", "Algebra I", "algebra_i_cross"),
        ("14b", "Algebra II", "algebra_ii_cross"),
        ("phi4", "Algebra I", "algebra_i_cross"),
        ("phi4", "Algebra II", "algebra_ii_cross"),
    ):
        stats = payload["maskedStem"][model_key][subset_key]
        if stats["n"] >= 10 and not stats["clearsBar"]:
            missed.append(
                f"{MODEL_LABELS[model_key]} {cell} cross-family verified "
                f"{stats['passRate']:.3f} n={stats['n']} bar no"
            )
    lines.append("## Honesty")
    lines.append("")
    if missed:
        lines.append("Rates that do not clear the channel bar on the cross-family verified set:")
        lines.append("")
        for item in missed:
            lines.append(f"- {item}")
    else:
        lines.append(
            "Every Algebra I and Algebra II masked-stem row on the cross-family verified set "
            "clears the channel bar (n >= 10, lower CI above 0.25 and above the subset modal letter)."
        )
    lines.append("")
    lines.append("## Verification counts")
    lines.append("")
    lines.append(
        "LLaVA-NeXT Vicuna 13B (`745cfbdb…`) versus Qwen2-VL transcription 1. "
        "`verified_cross_family` means the print-fidelity thresholds hold "
        "(stem F1 >= 0.8 with precision and recall >= 0.8, each option >= 0.9, option counts equal)."
    )
    lines.append("")
    all_v = verification["all"]
    overflow = int(payload.get("nContextOverflow") or 0)
    overflow_note = (
        f" {overflow} items exceeded LLaVA's 4096-token context (two-page crops under anyres) "
        "and are `not_verified_cross_family`."
        if overflow
        else ""
    )
    lines.append(
        f"Overall: cross-family verified {all_v['verified_cross_family']} / not "
        f"{all_v['not_verified_cross_family']} of {all_v['n']}. "
        f"Qwen–Qwen repaired_verified {all_v['qwen_repaired_verified']}. "
        f"Both checks {all_v['both_checks']}.{overflow_note}"
    )
    lines.append("")
    lines.append("| Qwen–Qwen | verified_cross_family | not_verified_cross_family |")
    lines.append("|---|---:|---:|")
    overlap = all_v["overlap"]
    lines.append(
        f"| repaired_verified | {overlap['repaired_verified']['verified_cross_family']} | "
        f"{overlap['repaired_verified']['not_verified_cross_family']} |"
    )
    lines.append(
        f"| repaired_unverified | {overlap['repaired_unverified']['verified_cross_family']} | "
        f"{overlap['repaired_unverified']['not_verified_cross_family']} |"
    )
    lines.append("")
    for claim, label, expected_n in (("algebra-i", "Algebra I", 358), ("algebra-ii", "Algebra II", 248)):
        cell = verification[claim]
        lines.append(
            f"{label}: cross-family verified {cell['verified_cross_family']} / not "
            f"{cell['not_verified_cross_family']} of {expected_n}. Both checks {cell['both_checks']}."
        )
        lines.append("")
        lines.append("| Qwen–Qwen | verified_cross_family | not_verified_cross_family |")
        lines.append("|---|---:|---:|")
        cell_overlap = cell["overlap"]
        lines.append(
            f"| repaired_verified | {cell_overlap['repaired_verified']['verified_cross_family']} | "
            f"{cell_overlap['repaired_verified']['not_verified_cross_family']} |"
        )
        lines.append(
            f"| repaired_unverified | {cell_overlap['repaired_unverified']['verified_cross_family']} | "
            f"{cell_overlap['repaired_unverified']['not_verified_cross_family']} |"
        )
        lines.append("")
    lines.append("## Per model: cross-family verified and both checks")
    lines.append("")
    lines.append(
        "Bar: n >= 10, lower bootstrap 95% CI strictly above chance 0.25 and strictly above "
        "the subset modal-letter frequency. Bootstrap: `random.Random.randrange`, 1000 replicates, "
        "seed `21 + n`. Predictions are the repaired-layer scores on transcription 1."
    )
    lines.append("")
    lines.append("| model | cell | subset | n | pass | rate | chance | 95% CI | modal (freq) | bar |")
    lines.append("|---|---|---|---:|---:|---:|---:|---|---|---|")
    for model_key in MODEL_KEYS:
        label = MODEL_LABELS[model_key]
        block = payload["maskedStem"][model_key]
        for cell, key in (
            ("Algebra I", "algebra_i_cross"),
            ("Algebra I", "algebra_i_both"),
            ("Algebra II", "algebra_ii_cross"),
            ("Algebra II", "algebra_ii_both"),
        ):
            subset = "cross-family verified" if key.endswith("_cross") else "both checks"
            stats = block[key]
            lines.append(f"| {label} | {cell} | {subset} | {rate_line(stats)} |")
    lines.append("")
    lines.append("## Verb-class on the cross-family verified set")
    lines.append("")
    lines.append("Join `exports/standards-split/item-standards.jsonl` with the locked cluster table.")
    lines.append("")
    lines.append("| model | cell | class | n | pass | rate | chance | 95% CI | modal (freq) | bar |")
    lines.append("|---|---|---|---:|---:|---:|---:|---|---|---|")
    for model_key in MODEL_KEYS:
        label = MODEL_LABELS[model_key]
        block = payload["verbClass"][model_key]
        for cell, key, class_label in (
            ("Algebra I", "algebra_i_execution_cross", "execution"),
            ("Algebra I", "algebra_i_recognition_cross", "recognition"),
            ("Algebra II", "algebra_ii_execution_cross", "execution"),
            ("Algebra II", "algebra_ii_recognition_cross", "recognition"),
        ):
            stats = block[key]
            lines.append(f"| {label} | {cell} | {class_label} | {rate_line(stats)} |")
    lines.append("")
    lines.append("## Rank-preserving isomorph on the cross-family verified set")
    lines.append("")
    lines.append(
        "Join repaired-layer rank-preserving scores. Items whose perturbation failed are excluded."
    )
    lines.append("")
    lines.append("| model | cell | n | pass | rate | chance | 95% CI | modal (freq) | bar |")
    lines.append("|---|---|---:|---:|---:|---:|---|---|---|")
    for model_key in MODEL_KEYS:
        label = MODEL_LABELS[model_key]
        block = payload["isomorph"][model_key]
        for cell, key in (
            ("Algebra I", "algebra_i_isomorph_cross"),
            ("Algebra II", "algebra_ii_isomorph_cross"),
        ):
            stats = block[key]
            lines.append(f"| {label} | {cell} | {rate_line(stats)} |")
    lines.append("")
    lines.append("## Files")
    lines.append("")
    lines.append("- `preregistration.md`, `preregistration.sha256`")
    lines.append("- `transcriptions-llava.jsonl`, `verdicts.jsonl`")
    lines.append("- `results.json`")
    lines.append("")
    lines.append("Script: `scripts/run_second_family_transcription.py`.")
    lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=("transcribe", "summarize", "all"), default="all")
    parser.add_argument("--limit", type=int, default=0, help="Transcribe only the first N ids.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    item_ids = algebra_primary_ids()
    if args.limit > 0:
        item_ids = item_ids[: args.limit]
    if args.stage in ("transcribe", "all"):
        transcribe(args.limit)
    if args.stage == "summarize" and args.limit > 0:
        raise RuntimeError("summarize requires the full 606-item transcription; omit --limit")
    if args.stage == "all" and args.limit > 0:
        print("skipping summarize because --limit is set", flush=True)
    elif args.stage in ("summarize", "all"):
        verdicts = build_verdicts(algebra_primary_ids())
        payload = summarize(verdicts)
        print(
            json.dumps(
                {
                    "verified_cross_family": payload["verification"]["all"]["verified_cross_family"],
                    "both_checks": payload["verification"]["all"]["both_checks"],
                    "algebra_i": payload["verification"]["algebra-i"]["verified_cross_family"],
                    "algebra_ii": payload["verification"]["algebra-ii"]["verified_cross_family"],
                },
                indent=2,
            )
        )


if __name__ == "__main__":
    main()
