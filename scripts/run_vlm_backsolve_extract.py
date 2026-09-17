#!/usr/bin/env python3
"""Extract equations from page images with a cached VLM; substitute options in sympy."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from addendum_lib import ITEMS_PATH, load_items
from vlm_backsolve_lib import (
    EXTRACT_PROMPT_TEMPLATE,
    PAGES_DIR,
    PREREG_PATH,
    ROOT,
    VERIFY_PROMPT_TEMPLATE,
    build_page_target,
    chance_k,
    extraction_prompt,
    extract_equations_from_payload,
    index_pdfs,
    is_solving_item,
    is_teks_solve_se,
    is_timss_algebra,
    option_map_from_payload,
    parse_json_object,
    stem_prefix,
    summarize_cell,
    unique_satisfier,
    verify_prompt,
)

OUT_DIR = ROOT / "exports" / "addendum-vlm"
ITEMS_OUT = OUT_DIR / "backsolve-extract-items.jsonl"
SUMMARY_OUT = OUT_DIR / "backsolve-extract.json"
VERIFY_ITEMS_OUT = OUT_DIR / "backsolve-vlm-verify-items.jsonl"
VERIFY_SUMMARY_OUT = OUT_DIR / "backsolve-vlm-verify.json"
SHA_PATH = OUT_DIR / "preregistration.sha256"
HAND_CHECK_PATH = OUT_DIR / "hand-check.json"
README_PATH = OUT_DIR / "README.md"

MODEL_ID = "Qwen/Qwen2-VL-7B-Instruct"
MODEL_REVISION = "eed13092ef92e448dd6875b2a00151bd3f7db0ac"
SNAPSHOT_PATH = (
    Path.home()
    / ".cache"
    / "huggingface"
    / "hub"
    / "models--Qwen--Qwen2-VL-7B-Instruct"
    / "snapshots"
    / MODEL_REVISION
)
SEED = 20260917
MAX_NEW_TOKENS = 400


def require_cuda() -> None:
    import torch

    if not torch.cuda.is_available():
        raise RuntimeError("CUDA GPU is required; torch.cuda.is_available() is False.")
    if torch.cuda.device_count() < 1:
        raise RuntimeError("CUDA GPU is required; torch.cuda.device_count() is 0.")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def freeze_preregistration() -> str:
    if not PREREG_PATH.exists():
        raise RuntimeError(f"missing {PREREG_PATH}")
    digest = sha256_file(PREREG_PATH)
    SHA_PATH.write_text(digest + "\n", encoding="utf-8")
    return digest


def selected_solving(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = [
        item
        for item in items
        if item.get("responseType") == "selected"
        and is_solving_item(item)
        and (item.get("choices") or {})
    ]
    rows.sort(key=lambda row: str(row["id"]))
    return rows


def load_existing(path: Path) -> dict[str, dict[str, Any]]:
    existing: dict[str, dict[str, Any]] = {}
    if not path.exists():
        return existing
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            existing[str(row["id"])] = row
    return existing


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def rewrite_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def load_vlm():
    import torch
    from transformers import AutoProcessor, Qwen2VLForConditionalGeneration

    require_cuda()
    if not SNAPSHOT_PATH.exists():
        raise RuntimeError(f"cached snapshot missing: {SNAPSHOT_PATH}")
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
    torch.manual_seed(SEED)
    torch.cuda.manual_seed_all(SEED)
    processor = AutoProcessor.from_pretrained(
        str(SNAPSHOT_PATH),
        local_files_only=True,
    )
    model = Qwen2VLForConditionalGeneration.from_pretrained(
        str(SNAPSHOT_PATH),
        torch_dtype=torch.bfloat16,
        device_map="cuda",
        local_files_only=True,
        attn_implementation="sdpa",
    )
    model.eval()
    return processor, model


def generate_json(processor: Any, model: Any, image_path: Path, prompt: str) -> str:
    from qwen_vl_utils import process_vision_info

    messages = [
        {
            "role": "user",
            "content": [
                {"type": "image", "image": str(image_path)},
                {"type": "text", "text": prompt},
            ],
        }
    ]
    text = processor.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )
    image_inputs, video_inputs = process_vision_info(messages)
    processor_kwargs: dict[str, Any] = {
        "text": [text],
        "images": image_inputs,
        "padding": True,
        "return_tensors": "pt",
    }
    if video_inputs:
        processor_kwargs["videos"] = video_inputs
    inputs = processor(**processor_kwargs)
    inputs = inputs.to(model.device)
    output_ids = model.generate(
        **inputs,
        max_new_tokens=MAX_NEW_TOKENS,
        do_sample=False,
    )
    generated = output_ids[0, inputs["input_ids"].shape[1] :]
    return processor.batch_decode([generated], skip_special_tokens=True)[0].strip()


def score_extraction(
    item: dict[str, Any],
    raw_text: str,
    png_rel: str | None,
    locate_reason: str,
) -> dict[str, Any]:
    prefix = stem_prefix(str(item.get("stem") or ""))
    chance = chance_k(item)
    key = str(item.get("key") or "").strip().upper()[:1]
    base = {
        "id": item["id"],
        "authority": item.get("authority"),
        "claim": item.get("claim"),
        "officialTag": item.get("officialTag"),
        "contentDomain": item.get("contentDomain"),
        "key": key,
        "chance": chance,
        "stemPrefix": prefix,
        "png": png_rel,
        "locateReason": locate_reason,
        "hasImage": png_rel is not None,
        "rawVlm": raw_text,
        "extractedLatex": None,
        "extractedAscii": None,
        "satisfierLetter": None,
        "correct": False,
        "fired": False,
        "abstainReason": None,
        "substitution": {},
    }
    payload = parse_json_object(raw_text)
    if payload is None:
        base["abstainReason"] = "extract_unparseable"
        return base
    equations = extract_equations_from_payload(payload)
    option_texts = option_map_from_payload(payload)
    latex_bits: list[str] = []
    ascii_bits: list[str] = []
    for entry in payload.get("equations") or []:
        if isinstance(entry, dict):
            if entry.get("latex"):
                latex_bits.append(str(entry["latex"]))
            if entry.get("ascii"):
                ascii_bits.append(str(entry["ascii"]))
        elif isinstance(entry, str):
            ascii_bits.append(entry)
    base["extractedLatex"] = " ; ".join(latex_bits) if latex_bits else None
    base["extractedAscii"] = " ; ".join(ascii_bits) if ascii_bits else None
    base["transcribedOptions"] = option_texts
    if payload.get("has_equation") is False and not equations:
        base["abstainReason"] = "no_equation"
        return base
    pick, reason, extra = unique_satisfier(equations, option_texts)
    base["substitution"] = extra
    if reason != "unique" or pick is None:
        base["abstainReason"] = reason
        return base
    base["fired"] = True
    base["satisfierLetter"] = pick
    base["correct"] = pick == key
    base["abstainReason"] = None
    return base


def score_verify(item: dict[str, Any], raw_text: str, png_rel: str | None) -> dict[str, Any]:
    chance = chance_k(item)
    key = str(item.get("key") or "").strip().upper()[:1]
    row = {
        "id": item["id"],
        "authority": item.get("authority"),
        "claim": item.get("claim"),
        "key": key,
        "chance": chance,
        "png": png_rel,
        "rawVlm": raw_text,
        "verdicts": {},
        "satisfierLetter": None,
        "correct": False,
        "fired": False,
        "abstainReason": None,
        "arm": "exploratory-vlm-verify",
    }
    payload = parse_json_object(raw_text)
    if payload is None:
        row["abstainReason"] = "extract_unparseable"
        return row
    from vlm_backsolve_lib import map_option_letter

    yes_letters: list[str] = []
    verdicts: dict[str, str] = {}
    for raw_key, raw_value in payload.items():
        letter = map_option_letter(str(raw_key))
        if letter is None:
            continue
        token = str(raw_value).strip().lower()
        verdicts[letter] = token
        if token == "yes":
            yes_letters.append(letter)
    row["verdicts"] = verdicts
    if len(yes_letters) == 1:
        row["fired"] = True
        row["satisfierLetter"] = yes_letters[0]
        row["correct"] = yes_letters[0] == key
    elif len(yes_letters) == 0:
        row["abstainReason"] = "zero_hits"
    else:
        row["abstainReason"] = "multiple_hits"
    return row


def cell_groups(rows: list[dict[str, Any]], items_by_id: dict[str, dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        item = items_by_id[row["id"]]
        label = f"{item['authority']}/{item['claim']}"
        groups[label].append(row)
        if is_teks_solve_se(item):
            groups["teks/solve-se"].append(row)
        if is_timss_algebra(item):
            groups["timss/algebra"].append(row)
    return groups


def build_summary(
    rows: list[dict[str, Any]],
    items_by_id: dict[str, dict[str, Any]],
    *,
    channel: str,
    prereg_sha: str,
    model_id: str,
    model_revision: str,
    extra: dict[str, Any],
) -> dict[str, Any]:
    groups = cell_groups(rows, items_by_id)
    cells: dict[str, Any] = {}
    for label in sorted(groups):
        cells[label] = summarize_cell(groups[label])
    algebra = cells.get("nyregents/algebra-i", summarize_cell([]))
    named_clears = [
        label
        for label, stats in cells.items()
        if stats["nFiredUnique"] >= 10 and stats["clearsBar"]
    ]
    named_measured = [
        label for label, stats in cells.items() if stats["nFiredUnique"] >= 10
    ]
    return {
        "channel": channel,
        "question": "Does substituting VLM-transcribed options into a VLM-extracted page equation uniquely recover the key?",
        "citation": "Millman, Bishop, and Ebel 1965 substitution; verify-versus-solve.",
        "preregistration": "exports/addendum-vlm/preregistration.md",
        "preregistrationSha256": prereg_sha,
        "modelId": model_id,
        "modelRevision": model_revision,
        "snapshotPath": str(SNAPSHOT_PATH),
        "scoredAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "nSolvingTaggedSelected": len(rows),
        "nFiredUnique": sum(1 for row in rows if row.get("fired")),
        "unblocksBacksolvingUnmeasured": algebra["nFiredUnique"] >= 10
        or any(
            label.startswith("nyregents/algebra-i") and stats["nFiredUnique"] >= 10
            for label, stats in cells.items()
        )
        or any(stats["nFiredUnique"] >= 10 for stats in cells.values()),
        "namedCellsWithNFiredAtLeast10": named_measured,
        "namedCellsClearingBar": named_clears,
        "cells": cells,
        **extra,
    }


def write_hand_check_template(fired: list[dict[str, Any]]) -> None:
    sample = sorted(fired, key=lambda row: str(row["id"]))[:30]
    payload = {
        "rule": "Fired extract+sympy items sorted by id, first 30. Compare extracted equation to the PNG.",
        "nFiredAvailable": len(fired),
        "nSample": len(sample),
        "parseCorrect": 0,
        "parseWrong": 0,
        "parseAmbiguous": 0,
        "keyDoesNotSatisfy": 0,
        "items": [
            {
                "id": row["id"],
                "png": row.get("png"),
                "extractedLatex": row.get("extractedLatex"),
                "extractedAscii": row.get("extractedAscii"),
                "satisfierLetter": row.get("satisfierLetter"),
                "key": row.get("key"),
                "correct": row.get("correct"),
                "transcribedOptions": row.get("transcribedOptions"),
                "substitution": row.get("substitution"),
                "judgment": "pending",
                "keyDoesNotSatisfy": (not row.get("correct")),
                "notes": "",
            }
            for row in sample
        ],
    }
    HAND_CHECK_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_readme(summary: dict[str, Any], verify: dict[str, Any] | None) -> None:
    algebra = summary["cells"].get("nyregents/algebra-i", {})
    lines = [
        "# VLM image backsolving",
        "",
        "Extract the displayed equation from a page PNG with a cached instruct VLM, then substitute each transcribed option in sympy. The model is not asked to solve.",
        "",
        f"- Model: `{summary['modelId']}` revision `{summary['modelRevision']}`",
        f"- Preregistration: `exports/addendum-vlm/preregistration.md` sha256 `{summary['preregistrationSha256']}`",
        f"- Solving-tagged selected-response scored: {summary['nSolvingTaggedSelected']}",
        f"- Fired unique overall: {summary['nFiredUnique']}",
        f"- Unblocks paper sentence (n fired >= 10 in a named cell): {summary['unblocksBacksolvingUnmeasured']}",
        "",
        "## Algebra I",
        "",
        f"- n eligible: {algebra.get('nEligible')}",
        f"- n with image: {algebra.get('nWithImage')}",
        f"- n fired unique: {algebra.get('nFiredUnique')}",
        f"- hits: {algebra.get('hits')}",
        f"- rate among fired: {algebra.get('rate')}",
        f"- chance (mean 1/k): {algebra.get('chance')}",
        f"- CI95: {algebra.get('ci95')}",
        f"- coverage (fired / eligible): {algebra.get('coverage')}",
        f"- rate with abstention as chance: {algebra.get('rateWithAbstentionAsChance')}",
        f"- clears bar: {algebra.get('clearsBar')}",
        "",
        "## Cells with n fired >= 10",
        "",
    ]
    measured = summary.get("namedCellsWithNFiredAtLeast10") or []
    if not measured:
        lines.append("None.")
    else:
        for label in measured:
            stats = summary["cells"][label]
            lines.append(
                f"- `{label}` n={stats['nFiredUnique']} rate={stats['rate']:.3f} "
                f"CI={stats['ci95']} chance={stats['chance']:.3f} "
                f"coverage={stats['coverage']:.3f} clears={stats['clearsBar']}"
            )
    lines.extend(["", "## All solving-tagged cells", ""])
    for label, stats in summary["cells"].items():
        lines.append(
            f"- `{label}` eligible={stats['nEligible']} image={stats['nWithImage']} "
            f"fired={stats['nFiredUnique']} hits={stats['hits']} "
            f"rate={stats['rate']} coverage={stats['coverage']}"
        )
    if verify is not None:
        v_alg = verify["cells"].get("nyregents/algebra-i", {})
        lines.extend(
            [
                "",
                "## Exploratory VLM yes/no arm (not the witness)",
                "",
                f"- Algebra I fired={v_alg.get('nFiredUnique')} rate={v_alg.get('rate')} CI={v_alg.get('ci95')}",
            ]
        )
    lines.append("")
    README_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--items", type=Path, default=ITEMS_PATH)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--authority", default="")
    parser.add_argument("--claim", default="")
    parser.add_argument("--skip-existing", action="store_true", default=True)
    parser.add_argument("--rerun", action="store_true")
    parser.add_argument("--force-verify", action="store_true")
    args = parser.parse_args()
    require_cuda()
    prereg_text = PREREG_PATH.read_text(encoding="utf-8")
    if "You are a transcription tool, not a tutor." not in prereg_text:
        raise RuntimeError("extraction prompt missing from preregistration")
    if "You are checking substitution, not solving by algebra." not in prereg_text:
        raise RuntimeError("verify prompt missing from preregistration")
    if EXTRACT_PROMPT_TEMPLATE.format(stem_prefix="{stem_prefix}").split("{stem_prefix}")[
        0
    ] not in prereg_text:
        raise RuntimeError("extraction prompt drifted from preregistration")
    if VERIFY_PROMPT_TEMPLATE.format(stem_prefix="{stem_prefix}").split("{stem_prefix}")[
        0
    ] not in prereg_text:
        raise RuntimeError("verify prompt drifted from preregistration")
    prereg_sha = freeze_preregistration()
    print(f"preregistration sha256 {prereg_sha}", flush=True)
    items = selected_solving(load_items(args.items))
    if args.authority:
        items = [item for item in items if item.get("authority") == args.authority]
    if args.claim:
        items = [item for item in items if item.get("claim") == args.claim]
    if args.limit > 0:
        items = items[: args.limit]
    items_by_id = {str(item["id"]): item for item in items}
    existing = {} if args.rerun else load_existing(ITEMS_OUT)
    pdf_index = index_pdfs()
    document_cache: dict[Path, Any] = {}
    need_vlm = [
        item
        for item in items
        if args.rerun or str(item["id"]) not in existing
    ]
    processor = None
    model = None
    if need_vlm:
        print(f"loading {MODEL_ID} {MODEL_REVISION} for {len(need_vlm)} items", flush=True)
        processor, model = load_vlm()
        print("model loaded", flush=True)
    scored: list[dict[str, Any]] = []
    if not args.rerun and ITEMS_OUT.exists() and need_vlm:
        # Keep completed rows; append new ones.
        scored.extend(existing[i] for i in existing if i in items_by_id)
    started = time.time()
    for index, item in enumerate(items, start=1):
        item_id = str(item["id"])
        if not args.rerun and item_id in existing:
            continue
        target = build_page_target(item, pdf_index, document_cache)
        png_rel = None
        raw_text = ""
        if target.png_path.exists() and target.png_path.stat().st_size > 100:
            png_rel = str(target.png_path.relative_to(ROOT))
            prompt = extraction_prompt(stem_prefix(str(item.get("stem") or "")))
            if processor is None or model is None:
                raise RuntimeError("VLM required but not loaded")
            raw_text = generate_json(processor, model, target.png_path, prompt)
            row = score_extraction(item, raw_text, png_rel, target.locate_reason)
        else:
            row = score_extraction(item, "", None, target.locate_reason)
            row["abstainReason"] = "no_image"
        if args.rerun:
            scored.append(row)
        else:
            append_jsonl(ITEMS_OUT, row)
            scored.append(row)
        if index % 10 == 0 or row.get("fired"):
            elapsed = time.time() - started
            print(
                f"[{index}/{len(items)}] {item_id} fired={row.get('fired')} "
                f"reason={row.get('abstainReason')} pick={row.get('satisfierLetter')} "
                f"{elapsed:.0f}s",
                flush=True,
            )
    for document in document_cache.values():
        document.close()
    if args.rerun:
        rewrite_jsonl(ITEMS_OUT, scored)
    else:
        # Reload full file so skipped existing rows are included.
        scored = list(load_existing(ITEMS_OUT).values())
        scored.sort(key=lambda row: str(row["id"]))
    extra = {
        "promptTemplate": EXTRACT_PROMPT_TEMPLATE,
        "substitution": "vlm_backsolve_lib.unique_satisfier",
        "imageDpi": 150,
        "maxNewTokens": MAX_NEW_TOKENS,
        "seed": SEED,
        "dtype": "bfloat16",
        "device": "cuda",
    }
    summary = build_summary(
        scored,
        {str(item["id"]): item for item in selected_solving(load_items(args.items))},
        channel="backsolve-extract",
        prereg_sha=prereg_sha,
        model_id=MODEL_ID,
        model_revision=MODEL_REVISION,
        extra=extra,
    )
    SUMMARY_OUT.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    fired = [row for row in scored if row.get("fired")]
    write_hand_check_template(fired)
    algebra_fired = summary["cells"].get("nyregents/algebra-i", {}).get("nFiredUnique", 0)
    verify_summary = None
    if args.force_verify or algebra_fired < 10:
        print(
            f"running exploratory verify arm (algebra_i fired={algebra_fired})",
            flush=True,
        )
        if processor is None or model is None:
            processor, model = load_vlm()
        verify_existing = {} if args.rerun else load_existing(VERIFY_ITEMS_OUT)
        verify_rows: list[dict[str, Any]] = []
        algebra_items = [
            item
            for item in selected_solving(load_items(args.items))
            if item.get("authority") == "nyregents" and item.get("claim") == "algebra-i"
        ]
        if args.limit > 0:
            algebra_items = algebra_items[: args.limit]
        for item in algebra_items:
            item_id = str(item["id"])
            if item_id in verify_existing:
                verify_rows.append(verify_existing[item_id])
                continue
            png_path = PAGES_DIR / f"{item_id}.png"
            if not png_path.exists():
                row = score_verify(item, "", None)
                row["abstainReason"] = "no_image"
            else:
                prompt = verify_prompt(stem_prefix(str(item.get("stem") or "")))
                raw_text = generate_json(processor, model, png_path, prompt)
                row = score_verify(item, raw_text, str(png_path.relative_to(ROOT)))
            append_jsonl(VERIFY_ITEMS_OUT, row)
            verify_rows.append(row)
        verify_summary = build_summary(
            verify_rows,
            {str(item["id"]): item for item in algebra_items},
            channel="backsolve-vlm-verify",
            prereg_sha=prereg_sha,
            model_id=MODEL_ID,
            model_revision=MODEL_REVISION,
            extra={"label": "exploratory", "notWitness": True},
        )
        VERIFY_SUMMARY_OUT.write_text(
            json.dumps(verify_summary, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    write_readme(summary, verify_summary)
    print(json.dumps({"wrote": str(SUMMARY_OUT), "algebraI": summary["cells"].get("nyregents/algebra-i")}, indent=2))


if __name__ == "__main__":
    main()
