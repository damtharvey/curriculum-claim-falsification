#!/usr/bin/env python3
"""Min-K% and mean token log-prob of the original stem plus options (7B, GPU)."""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
from pathlib import Path
from typing import Any

import torch

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

from score_choices_only_local_lm import (  # noqa: E402
    EXPERIMENT_SEED,
    MODEL_ID,
    MODEL_REVISION,
    SNAPSHOT_PATH,
    format_options_block,
    load_items,
    require_cuda,
    scorable_item,
    snapshot_dir_for,
)

KEEP_IDS_PATH = ROOT / "exports" / "addendum" / "choices-only-clean-item-ids.json"
OUT_DIR = ROOT / "exports" / "addendum-gpu"
ITEMS_OUT = OUT_DIR / "masked-stem-membership-7b-items.jsonl"
SUMMARY_OUT = OUT_DIR / "masked-stem-membership-7b.json"
SCORED_7B = OUT_DIR / "masked-stem-7b-items.jsonl"


def online_exam_text(item: dict[str, Any]) -> str:
    stem = str(item.get("stem") or "").strip()
    options_block = format_options_block(item.get("choices") or {})
    return f"{stem}\n\n{options_block}"


def min_k_percent_mean(token_logprobs: list[float], k_percent: float = 20.0) -> float:
    if not token_logprobs:
        raise RuntimeError("empty token log-probability list")
    n_keep = max(1, int(math.ceil(len(token_logprobs) * k_percent / 100.0)))
    lowest = sorted(token_logprobs)[:n_keep]
    return sum(lowest) / len(lowest)


def already_scored_ids(path: Path) -> set[str]:
    done: set[str] = set()
    if not path.exists():
        return done
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            rec = json.loads(line)
            done.add(str(rec["id"]))
    return done


def append_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


@torch.inference_mode()
def token_logprobs_for_text(
    model: Any,
    tokenizer_obj: Any,
    device: torch.device,
    text: str,
) -> tuple[list[float], int]:
    encoded = tokenizer_obj(
        text,
        return_tensors="pt",
        add_special_tokens=True,
    )
    input_ids = encoded["input_ids"].to(device)
    n_tokens = int(input_ids.size(1))
    if n_tokens < 2:
        raise RuntimeError(f"sequence too short to score: {text[:120]!r}")
    logits = model(input_ids=input_ids).logits
    log_probs = torch.log_softmax(logits[0, :-1].float(), dim=-1)
    targets = input_ids[0, 1:]
    gathered = log_probs[torch.arange(targets.size(0), device=device), targets]
    return [float(value) for value in gathered.tolist()], n_tokens


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Mean and Min-20% token log-prob of original stem plus options."
    )
    parser.add_argument("--items-out", default=str(ITEMS_OUT))
    parser.add_argument("--summary-path", default=str(SUMMARY_OUT))
    parser.add_argument("--k-percent", type=float, default=20.0)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
    started = time.time()
    device = require_cuda()
    gpu_name = torch.cuda.get_device_name(0)
    if not SNAPSHOT_PATH.exists():
        raise RuntimeError(f"Local model snapshot missing: {SNAPSHOT_PATH}")
    from transformers import AutoModelForCausalLM, AutoTokenizer

    keep_ids = [str(item_id) for item_id in json.loads(KEEP_IDS_PATH.read_text(encoding="utf-8"))]
    items_by_id = load_items()
    scored_ids = [
        str(row["id"])
        for row in (
            json.loads(line)
            for line in SCORED_7B.read_text(encoding="utf-8").splitlines()
            if line.strip()
        )
    ]
    to_score = []
    for item_id in scored_ids:
        item = items_by_id[item_id]
        if not scorable_item(item):
            raise RuntimeError(f"scored id is not scorable: {item_id}")
        to_score.append(item)
    if len(to_score) != 1487:
        raise RuntimeError(f"expected 1487 scored ids, got {len(to_score)}")

    items_out = Path(args.items_out)
    summary_path = Path(args.summary_path)
    done_ids = already_scored_ids(items_out)
    pending = [item for item in to_score if str(item["id"]) not in done_ids]
    print(
        f"GPU {gpu_name} membership pending={len(pending)} already={len(done_ids)}",
        flush=True,
    )

    tokenizer = AutoTokenizer.from_pretrained(str(SNAPSHOT_PATH), local_files_only=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    load_started = time.time()
    model = AutoModelForCausalLM.from_pretrained(
        str(SNAPSHOT_PATH),
        torch_dtype=torch.bfloat16,
        local_files_only=True,
        attn_implementation="sdpa",
    )
    model.to(device)
    model.eval()
    load_seconds = time.time() - load_started
    print(f"model loaded in {load_seconds:.1f}s", flush=True)

    torch.manual_seed(EXPERIMENT_SEED)
    torch.cuda.manual_seed_all(EXPERIMENT_SEED)
    k_percent = float(args.k_percent)
    scored_count = len(done_ids)
    for item in pending:
        text = online_exam_text(item)
        token_lp, n_tokens = token_logprobs_for_text(model, tokenizer, device, text)
        mean_lp = sum(token_lp) / len(token_lp)
        min20 = min_k_percent_mean(token_lp, k_percent)
        row = {
            "id": item["id"],
            "cell": f"{item.get('authority')}::{item.get('claim')}",
            "corpus": item.get("corpus"),
            "n_tokens": n_tokens,
            "n_scored_tokens": len(token_lp),
            "mean_token_logprob": mean_lp,
            "min20_token_logprob": min20,
            "k_percent": k_percent,
            "text_chars": len(text),
            "modelId": MODEL_ID,
            "modelRevision": MODEL_REVISION,
        }
        append_jsonl(items_out, [row])
        scored_count += 1
        if scored_count % 50 == 0 or scored_count == len(to_score):
            print(
                f"  membership {scored_count}/{len(to_score)} "
                f"last_mean={mean_lp:.4f} last_min20={min20:.4f}",
                flush=True,
            )
            summary_path.write_text(
                json.dumps(
                    {
                        "status": "in_progress",
                        "nScored": scored_count,
                        "nTarget": len(to_score),
                        "modelId": MODEL_ID,
                        "modelRevision": MODEL_REVISION,
                        "gpuName": gpu_name,
                        "wallTimeSecondsSoFar": time.time() - started,
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

    payload = {
        "status": "complete",
        "label": "exploratory",
        "question": (
            "Mean token log-probability and Min-20% token log-probability of the original "
            "unmasked stem plus options, scored with Qwen2.5-7B-Instruct on GPU."
        ),
        "modelId": MODEL_ID,
        "modelRevision": MODEL_REVISION,
        "snapshotPath": str(SNAPSHOT_PATH),
        "n": len(to_score),
        "kPercent": k_percent,
        "text": (
            "Original stem, blank line, then lettered options in original order. "
            "No chat template and no masking instruction. This is the text as it would "
            "appear in a released exam PDF."
        ),
        "scoring": (
            "Causal next-token log-softmax over the tokenized online text. Mean is the "
            "average log-probability of tokens 1..n-1. Min-20% is the mean of the lowest "
            "ceil(0.20 * n) token log-probabilities."
        ),
        "itemsOut": str(items_out.relative_to(ROOT)) if items_out.is_relative_to(ROOT) else str(items_out),
        "seed": EXPERIMENT_SEED,
        "versions": {
            "torch": torch.__version__,
            "gpuName": gpu_name,
            "cuda": torch.version.cuda,
            "dtype": "bfloat16",
        },
        "modelLoadSeconds": load_seconds,
        "wallTimeSeconds": time.time() - started,
        "snapshotResolved": str(snapshot_dir_for(MODEL_ID, MODEL_REVISION)),
    }
    summary_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "complete", "n": len(to_score), "out": str(items_out)}, indent=2))


if __name__ == "__main__":
    main()
