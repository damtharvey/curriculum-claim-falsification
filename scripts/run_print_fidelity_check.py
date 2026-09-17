#!/usr/bin/env python3
"""Transcribe claimed-cell items from page images with the cached VLM and score text-layer fidelity."""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from addendum_lib import load_items
from print_fidelity_lib import (
    AUDIT_PATH,
    CALIBRATION_GRID_OPTION,
    CALIBRATION_GRID_STEM,
    CALIBRATION_MIN_AGREEMENT,
    CALIBRATION_PATH,
    DEV_ITEMS_PATH,
    FIDELITY_ITEMS_PATH,
    MODEL_ID,
    MODEL_REVISION,
    OPTION_MATCH_THRESHOLD,
    OUT_DIR,
    PAGES_DIR,
    POPULATION_PATH,
    PREREG_PATH,
    PREREG_SHA_PATH,
    ROOT,
    SEED,
    SNAPSHOT_PATH,
    STEM_F1_THRESHOLD,
    TRANSCRIPTION_PROMPT_TEMPLATE,
    append_jsonl,
    audited_ids,
    build_population,
    confusion_matrix,
    development_ids,
    dump_json,
    fidelity_row,
    generate_transcription,
    load_jsonl,
    load_vlm,
    parse_json_object,
    population_counts,
    render_item_pages,
    require_cuda,
    rescore_row,
    score_fidelity,
    sha256_file,
    transcription_prompt,
)
from vlm_backsolve_lib import index_pdfs, question_number

DEV_PER_CELL = 10
DEV_SEED = 20260916


def frozen_preregistration_sha() -> str:
    if not PREREG_PATH.exists():
        raise RuntimeError(f"preregistration missing: {PREREG_PATH}")
    if not PREREG_SHA_PATH.exists():
        raise RuntimeError(f"preregistration sha missing: {PREREG_SHA_PATH}; freeze before scoring")
    recorded = PREREG_SHA_PATH.read_text(encoding="utf-8").split()[0]
    current = sha256_file(PREREG_PATH)
    if recorded != current:
        raise RuntimeError(f"preregistration changed after freeze: recorded {recorded} current {current}")
    prereg_text = PREREG_PATH.read_text(encoding="utf-8")
    prompt_head = TRANSCRIPTION_PROMPT_TEMPLATE.split("{qnum}")[0]
    if prompt_head not in prereg_text:
        raise RuntimeError("transcription prompt drifted from preregistration")
    return current


def transcribe_items(
    item_ids: list[str],
    items_by_id: dict[str, dict[str, Any]],
    membership: dict[str, list[str]],
    out_path: Path,
    stage: str,
    *,
    stem_threshold: float,
    option_threshold: float,
    force_render: bool,
) -> list[dict[str, Any]]:
    existing = {str(row["id"]): row for row in load_jsonl(out_path)}
    pending = [item_id for item_id in item_ids if item_id not in existing]
    print(f"stage={stage} requested={len(item_ids)} already={len(item_ids) - len(pending)} pending={len(pending)}", flush=True)
    pdf_index = index_pdfs()
    document_cache: dict[Path, Any] = {}
    processor = None
    model = None
    if pending:
        print(f"loading {MODEL_ID} {MODEL_REVISION}", flush=True)
        processor, model = load_vlm()
        print("model loaded", flush=True)
    started = time.time()
    for index, item_id in enumerate(pending, start=1):
        item = items_by_id[item_id]
        pages = render_item_pages(item, pdf_index, document_cache, PAGES_DIR, force=force_render)
        qnum = question_number(item)
        if qnum is None:
            raise RuntimeError(f"no question number for {item_id}")
        if not pages.png_paths:
            raw = ""
            payload = None
        else:
            prompt = transcription_prompt(qnum)
            raw = generate_transcription(processor, model, [ROOT / png for png in pages.png_paths], prompt)
            payload = parse_json_object(raw)
        score = score_fidelity(item, payload, stem_threshold=stem_threshold, option_threshold=option_threshold)
        row = fidelity_row(item, membership.get(item_id, []), pages, raw, payload, score, stage)
        row["scoredAt"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        append_jsonl(out_path, row)
        existing[item_id] = row
        elapsed = time.time() - started
        print(
            f"[{index}/{len(pending)}] {item_id} verdict={score.verdict} cat={score.category} "
            f"stem_f1={score.stem_f1:.2f} opts={score.n_options_transcribed}/{score.n_options_text_layer} "
            f"flags={','.join(score.flags) or '-'} {elapsed:.0f}s ({elapsed / index:.1f}s/item)",
            flush=True,
        )
    for document in document_cache.values():
        document.close()
    return [existing[item_id] for item_id in item_ids if item_id in existing]


def run_dev(args: argparse.Namespace, items: list[dict[str, Any]], membership: dict[str, list[str]]) -> None:
    items_by_id = {str(item["id"]): item for item in items}
    ids = development_ids(items, membership, DEV_PER_CELL, DEV_SEED)
    if args.limit > 0:
        ids = ids[: args.limit]
    rows = transcribe_items(
        ids,
        items_by_id,
        membership,
        DEV_ITEMS_PATH,
        "dev",
        stem_threshold=STEM_F1_THRESHOLD,
        option_threshold=OPTION_MATCH_THRESHOLD,
        force_render=args.force_render,
    )
    counts = Counter(str(row["category"]) for row in rows)
    print(json.dumps({"stage": "dev", "n": len(rows), "categories": dict(counts)}, indent=2))


def choose_thresholds(rows: list[dict[str, Any]], items_by_id: dict[str, dict[str, Any]], audit: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Pre-registered calibration step: adjust only when default agreement is below the floor, over the declared grid."""
    default = confusion_matrix(rows, audit)
    result: dict[str, Any] = {
        "defaultThresholds": {"stem": STEM_F1_THRESHOLD, "option": OPTION_MATCH_THRESHOLD},
        "defaultBinaryAgreement": default["binaryAgreement"],
        "minAgreementToKeepDefault": CALIBRATION_MIN_AGREEMENT,
        "adjusted": False,
        "grid": [],
        "chosenThresholds": {"stem": STEM_F1_THRESHOLD, "option": OPTION_MATCH_THRESHOLD},
    }
    grid: list[dict[str, Any]] = []
    for stem_threshold in CALIBRATION_GRID_STEM:
        for option_threshold in CALIBRATION_GRID_OPTION:
            rescored = [rescore_row(row, items_by_id[str(row["id"])], stem_threshold, option_threshold) for row in rows]
            matrix = confusion_matrix(rescored, audit)
            grid.append(
                {
                    "stem": stem_threshold,
                    "option": option_threshold,
                    "binaryAgreement": matrix["binaryAgreement"],
                    "categoryAgreement": matrix["categoryAgreement"],
                }
            )
    result["grid"] = grid
    if default["binaryAgreement"] >= CALIBRATION_MIN_AGREEMENT:
        return result
    best = max(grid, key=lambda entry: (entry["binaryAgreement"], entry["stem"], entry["option"]))
    result["adjusted"] = True
    result["chosenThresholds"] = {"stem": best["stem"], "option": best["option"]}
    result["chosenBinaryAgreement"] = best["binaryAgreement"]
    return result


def run_calibration(args: argparse.Namespace, items: list[dict[str, Any]], membership: dict[str, list[str]]) -> None:
    prereg_sha = frozen_preregistration_sha()
    items_by_id = {str(item["id"]): item for item in items}
    audit = audited_ids()
    ids = sorted(audit)
    missing = [item_id for item_id in ids if item_id not in membership]
    if missing:
        raise RuntimeError(f"audited items outside the population: {missing}")
    rows = transcribe_items(
        ids,
        items_by_id,
        membership,
        FIDELITY_ITEMS_PATH,
        "calibration",
        stem_threshold=STEM_F1_THRESHOLD,
        option_threshold=OPTION_MATCH_THRESHOLD,
        force_render=args.force_render,
    )
    thresholds = choose_thresholds(rows, items_by_id, audit)
    chosen_stem = float(thresholds["chosenThresholds"]["stem"])
    chosen_option = float(thresholds["chosenThresholds"]["option"])
    final_rows = [rescore_row(row, items_by_id[str(row["id"])], chosen_stem, chosen_option) for row in rows]
    matrix_default = confusion_matrix(rows, audit)
    matrix_final = confusion_matrix(final_rows, audit)
    payload = {
        "preregistrationSha256": prereg_sha,
        "audit": str(AUDIT_PATH.relative_to(ROOT)),
        "nAudited": len(ids),
        "modelId": MODEL_ID,
        "modelRevision": MODEL_REVISION,
        "thresholds": thresholds,
        "confusionDefault": matrix_default,
        "confusionChosen": matrix_final,
        "calibratedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    dump_json(CALIBRATION_PATH, payload)
    if thresholds["adjusted"]:
        rewrite_calibration_rows(final_rows)
    print(json.dumps({k: v for k, v in payload.items() if k not in ("confusionDefault", "confusionChosen")}, indent=2))
    print("default matrix", json.dumps(matrix_default["matrix"], indent=1))
    print("binary", json.dumps(matrix_default["binary"]))
    print("binary agreement", matrix_default["binaryAgreement"], "/", len(ids))
    if thresholds["adjusted"]:
        print("chosen matrix", json.dumps(matrix_final["matrix"], indent=1))
        print("chosen binary agreement", matrix_final["binaryAgreement"], "/", len(ids))


def rewrite_calibration_rows(final_rows: list[dict[str, Any]]) -> None:
    by_id = {str(row["id"]): row for row in final_rows}
    rows = load_jsonl(FIDELITY_ITEMS_PATH)
    rewritten = [by_id.get(str(row["id"]), row) for row in rows]
    FIDELITY_ITEMS_PATH.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rewritten),
        encoding="utf-8",
    )


def run_census(args: argparse.Namespace, items: list[dict[str, Any]], membership: dict[str, list[str]]) -> None:
    prereg_sha = frozen_preregistration_sha()
    if not CALIBRATION_PATH.exists():
        raise RuntimeError("run --stage calibration before the census")
    calibration = json.loads(CALIBRATION_PATH.read_text(encoding="utf-8"))
    if calibration["preregistrationSha256"] != prereg_sha:
        raise RuntimeError("calibration was recorded under a different preregistration sha")
    stem_threshold = float(calibration["thresholds"]["chosenThresholds"]["stem"])
    option_threshold = float(calibration["thresholds"]["chosenThresholds"]["option"])
    items_by_id = {str(item["id"]): item for item in items}
    ids = sorted(membership)
    if args.limit > 0:
        ids = ids[: args.limit]
    rows = transcribe_items(
        ids,
        items_by_id,
        membership,
        FIDELITY_ITEMS_PATH,
        "census",
        stem_threshold=stem_threshold,
        option_threshold=option_threshold,
        force_render=args.force_render,
    )
    counts = Counter(str(row["verdict"]) for row in rows)
    per_cell: dict[str, Counter[str]] = {}
    for row in rows:
        for cell in row["cells"]:
            per_cell.setdefault(cell, Counter())[str(row["verdict"])] += 1
    summary = {
        "preregistrationSha256": prereg_sha,
        "modelId": MODEL_ID,
        "modelRevision": MODEL_REVISION,
        "snapshotPath": str(SNAPSHOT_PATH),
        "seed": SEED,
        "thresholds": {"stem": stem_threshold, "option": option_threshold},
        "nPopulation": len(membership),
        "nScored": len(rows),
        "verdicts": dict(counts),
        "perCell": {cell: dict(counter) for cell, counter in sorted(per_cell.items())},
        "completedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    dump_json(OUT_DIR / "census-summary.json", summary)
    print(json.dumps(summary, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=["dev", "calibration", "census"], required=True)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--force-render", action="store_true")
    args = parser.parse_args()
    require_cuda()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    items = load_items()
    membership = build_population(items)
    dump_json(
        POPULATION_PATH,
        {
            "counts": population_counts(membership),
            "sources": {
                "algebraPrimary": "exports/addendum-gpu/masked-stem-algebra-primary-item-ids.json",
                "geometryPhi4Primary": "exports/addendum-gpu/masked-stem-primary-item-ids.json (nyregents::geometry)",
                "lowerCentralFired": "scripts/addendum_lib.py middle_value_option over nyregents geometry and eqao g6 selected-response items",
            },
            "items": {item_id: cells for item_id, cells in sorted(membership.items())},
        },
    )
    if args.stage == "dev":
        run_dev(args, items, membership)
    elif args.stage == "calibration":
        run_calibration(args, items, membership)
    else:
        run_census(args, items, membership)


if __name__ == "__main__":
    main()
