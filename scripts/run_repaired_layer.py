#!/usr/bin/env python3
"""Repair Algebra I/II stems from page transcriptions, verify, rescore, and run the 14B isomorph amendment."""

from __future__ import annotations

import argparse
import json
import os
import signal
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import fitz

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

import score_choices_only_local_lm as scorer  # noqa: E402
import score_isomorph_options as iso  # noqa: E402
from addendum_lib import (  # noqa: E402
    load_items as load_item_list,
    middle_value_option,
    score_program,
    summarize_scored,
)
from perturb_option_numerals import (  # noqa: E402
    ARM_PRESERVING,
    ARM_SCRAMBLED,
    ARMS,
    perturb_choices,
    rng_for,
)
from print_fidelity_lib import (  # noqa: E402
    CELL_EQAO_G6_LC,
    CELL_GEOMETRY_LC,
    DPI,
    FIDELITY_ITEMS_PATH,
    STEM_F1_THRESHOLD,
    VERDICT_FAITHFUL,
    VERDICT_NOT_FAITHFUL,
    VERDICT_UNVERIFIED,
    append_jsonl,
    clean_vlm_stem,
    continuation_clip,
    dump_json,
    generate_transcription,
    load_jsonl,
    load_vlm,
    parse_json_object,
    require_cuda,
    score_fidelity,
    sha256_file,
    transcribed_options,
)
from rescore_print_faithful_rows import lm_row  # noqa: E402
from split_masked_stem_by_standard import (  # noqa: E402
    CLUSTER_CLASS,
    EXECUTION,
    MIXED,
    RECOGNITION,
)
from vlm_backsolve_lib import index_pdfs, question_number, resolve_pdf  # noqa: E402

OUT_DIR = ROOT / "exports" / "repaired-layer"
PREREG_PATH = OUT_DIR / "preregistration.md"
PREREG_SHA_PATH = OUT_DIR / "preregistration.sha256"
VERIFY_PAGES_DIR = OUT_DIR / "pages-verify"
VERIFY_ITEMS_PATH = OUT_DIR / "verification-items.jsonl"
REPAIRED_ITEMS_PATH = OUT_DIR / "repaired-items.jsonl"
REPAIRED_MASKED_PATH = OUT_DIR / "repaired-masked-items.jsonl"
PERTURBED_PATH = OUT_DIR / f"perturbed-items-{ARM_PRESERVING}.jsonl"
RESULTS_PATH = OUT_DIR / "results.json"
README_PATH = OUT_DIR / "README.md"
ALGEBRA_IDS_PATH = ROOT / "exports" / "addendum-gpu" / "masked-stem-algebra-primary-item-ids.json"
ITEM_STANDARDS_PATH = ROOT / "exports" / "standards-split" / "item-standards.jsonl"
SAVED_PREDICTIONS = iso.SAVED_PREDICTIONS
ISOMORPH_PERTURBED_DIR = iso.OUT_DIR
SEED = 20260916
VERIFY_CROP_EXTRA_PT = 6.0
CHANCE = 0.25
LETTER_ORDER = ("A", "B", "C", "D", "E")
REPAIRED_VERIFIED = "repaired_verified"
REPAIRED_UNVERIFIED = "repaired_unverified"
MODEL_KEYS = ("7b", "14b", "phi4")

VERIFY_PROMPT_TEMPLATE = """Copy the printed multiple-choice question numbered {qnum} from this exam-page image. Do not solve it and do not name the correct choice.

Skip headers, footers, other questions, and the computations box labeled "Use this space for computations".

Output:
1. "stem": the wording of question {qnum} starting after the printed item number and stopping before the first answer choice. Keep any sentence that continues after a table or figure. If a table is printed, copy its cells row by row into the stem. Do not describe diagrams, graphs, or pictures. Do not copy labels that appear only inside a diagram. Do not put answer choices in the stem.
2. "options": every printed answer choice of question {qnum}, keyed by the printed marker exactly as printed ("1", "2", "3", "4" or "A", "B", "C", "D", "E"). Each value is one JSON string; if a choice wraps across lines, join those lines with "; ". Include every printed choice and no unprinted choice.

Write mathematics in plain text: exponents as x^2, fractions as 5/3, mixed numbers as 2 1/3, roots as sqrt(10), coordinates as (-1, -3), subscripts as a_n. Keep degrees, pi, <=, >=, and the minus sign.

Return a JSON object and nothing else:
{{"stem": "...", "options": {{"1": "...", "2": "...", "3": "...", "4": "..."}}}}
"""


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
    prompt_head = VERIFY_PROMPT_TEMPLATE.split("{qnum}")[0]
    if prompt_head not in prereg_text:
        raise RuntimeError("verification prompt drifted from preregistration")
    if "expanded by 6 pt" not in prereg_text:
        raise RuntimeError("verification crop margin drifted from preregistration")
    return current


def algebra_primary_ids() -> list[str]:
    return [str(item_id) for item_id in json.loads(ALGEBRA_IDS_PATH.read_text(encoding="utf-8"))]


def census_fidelity_by_id() -> dict[str, dict[str, Any]]:
    rows = [
        row
        for row in load_jsonl(FIDELITY_ITEMS_PATH)
        if row.get("stage") in ("calibration", "census")
    ]
    return {str(row["id"]): row for row in rows}


def item_verb_class() -> dict[str, str]:
    out: dict[str, str] = {}
    for row in load_jsonl(ITEM_STANDARDS_PATH):
        code = str(row["standard"])
        if code not in CLUSTER_CLASS:
            raise KeyError(f"{row['id']}: cluster {code} has no class")
        out[str(row["id"])] = CLUSTER_CLASS[code][0]
    return out


def transcription_one(row: dict[str, Any]) -> tuple[str | None, dict[str, str]]:
    stem = str(row.get("vlmStem") or "").strip()
    options = {str(letter): str(text) for letter, text in dict(row.get("vlmOptions") or {}).items() if str(text).strip()}
    if stem and len(options) >= 2:
        return stem, options
    payload = parse_json_object(str(row.get("rawVlm") or ""))
    if payload is None:
        return None, {}
    qnum = row.get("qnum")
    cleaned = clean_vlm_stem(payload, int(qnum) if qnum is not None else None)
    mapped = transcribed_options(payload)
    if cleaned.strip() and len(mapped) >= 2:
        return cleaned.strip(), mapped
    return None, {}


def usable_transcription(stem: str | None, options: dict[str, str]) -> bool:
    return bool(stem and stem.strip() and len(options) >= 2)


def expand_clip(page_rect: fitz.Rect, clip: tuple[float, float, float, float], extra_pt: float) -> fitz.Rect:
    _x0, y0, _x1, y1 = clip
    return fitz.Rect(
        page_rect.x0,
        max(page_rect.y0, y0 - extra_pt),
        page_rect.x1,
        min(page_rect.y1, y1 + extra_pt),
    )


def clip_tuple(raw: Any) -> tuple[float, float, float, float] | None:
    if not raw or len(raw) != 4:
        return None
    return (float(raw[0]), float(raw[1]), float(raw[2]), float(raw[3]))


def render_verify_pages(
    row: dict[str, Any],
    item: dict[str, Any],
    pdf_index: dict[str, Path],
    document_cache: dict[Path, fitz.Document],
) -> list[Path]:
    item_id = str(row["id"])
    clip = clip_tuple(row.get("clip"))
    page_index = row.get("pageIndex")
    if clip is None or page_index is None:
        return []
    pdf = resolve_pdf(item, pdf_index)
    if pdf is None:
        stored = row.get("pdf")
        pdf = ROOT / str(stored) if stored else None
    if pdf is None or not pdf.exists():
        return []
    if pdf not in document_cache:
        document_cache[pdf] = fitz.open(pdf)
    document = document_cache[pdf]
    page = document[int(page_index)]
    matrix = fitz.Matrix(DPI / 72.0, DPI / 72.0)
    VERIFY_PAGES_DIR.mkdir(parents=True, exist_ok=True)
    main_png = VERIFY_PAGES_DIR / f"{item_id}.png"
    if not main_png.exists() or main_png.stat().st_size < 100:
        rect = expand_clip(page.rect, clip, VERIFY_CROP_EXTRA_PT)
        pix = page.get_pixmap(matrix=matrix, clip=rect)
        pix.save(str(main_png))
    paths = [main_png]
    qnum = question_number(item)
    original_rect = fitz.Rect(*clip)
    continuation = continuation_clip(document, int(page_index), original_rect, qnum)
    if continuation is not None:
        continuation_index, continuation_rect = continuation
        cont_png = VERIFY_PAGES_DIR / f"{item_id}-continuation.png"
        if not cont_png.exists() or cont_png.stat().st_size < 100:
            cont_page = document[continuation_index]
            expanded = expand_clip(
                cont_page.rect,
                (
                    continuation_rect.x0,
                    continuation_rect.y0,
                    continuation_rect.x1,
                    continuation_rect.y1,
                ),
                VERIFY_CROP_EXTRA_PT,
            )
            pix = cont_page.get_pixmap(matrix=matrix, clip=expanded)
            pix.save(str(cont_png))
        paths.append(cont_png)
    return paths


def verify_prompt(qnum: int) -> str:
    return VERIFY_PROMPT_TEMPLATE.format(qnum=qnum).rstrip() + "\n"


def run_verify(limit: int) -> list[dict[str, Any]]:
    require_cuda()
    prereg_sha = check_preregistration()
    item_ids = algebra_primary_ids()
    if limit > 0:
        item_ids = item_ids[:limit]
    items_by_id = scorer.load_items()
    fidelity = census_fidelity_by_id()
    missing = [item_id for item_id in item_ids if item_id not in fidelity]
    if missing:
        raise RuntimeError(f"print-faithful transcription missing for {len(missing)} ids, e.g. {missing[:5]}")
    existing = {str(row["id"]): row for row in load_jsonl(VERIFY_ITEMS_PATH)}
    pending = [item_id for item_id in item_ids if item_id not in existing]
    print(
        f"verify requested={len(item_ids)} already={len(item_ids) - len(pending)} pending={len(pending)} "
        f"prereg={prereg_sha[:12]}",
        flush=True,
    )
    pdf_index = index_pdfs()
    document_cache: dict[Path, fitz.Document] = {}
    processor = None
    model = None
    if pending:
        print("loading Qwen2-VL-7B-Instruct for verification transcription", flush=True)
        processor, model = load_vlm()
        print("verification model loaded", flush=True)
    started = time.time()
    for index, item_id in enumerate(pending, start=1):
        item = items_by_id[item_id]
        source = fidelity[item_id]
        stem_one, options_one = transcription_one(source)
        qnum = question_number(item)
        if qnum is None:
            raise RuntimeError(f"no question number for {item_id}")
        png_paths = render_verify_pages(source, item, pdf_index, document_cache)
        if not png_paths:
            raw = ""
            payload = None
        else:
            raw = generate_transcription(processor, model, png_paths, verify_prompt(qnum))
            payload = parse_json_object(raw)
        if not usable_transcription(stem_one, options_one) or payload is None:
            repair_verdict = REPAIRED_UNVERIFIED
            score_dict: dict[str, Any] = {
                "stem_f1": 0.0,
                "stem_precision": 0.0,
                "stem_recall": 0.0,
                "option_match": {},
                "option_count_equal": False,
                "verdict": VERDICT_UNVERIFIED,
                "flags": ["missing_transcription"],
            }
        else:
            compare_item = dict(item)
            compare_item["stem"] = stem_one
            compare_item["choices"] = options_one
            score = score_fidelity(
                compare_item,
                payload,
                stem_threshold=STEM_F1_THRESHOLD,
                option_threshold=0.9,
            )
            repair_verdict = REPAIRED_VERIFIED if score.verdict == VERDICT_FAITHFUL else REPAIRED_UNVERIFIED
            score_dict = {
                "stem_f1": score.stem_f1,
                "stem_precision": score.stem_precision,
                "stem_recall": score.stem_recall,
                "option_match": score.option_scores,
                "option_count_equal": score.option_count_equal,
                "verdict": score.verdict,
                "flags": score.flags,
            }
        row = {
            "id": item_id,
            "claim": item.get("claim"),
            "authority": item.get("authority"),
            "qnum": qnum,
            "old_verdict": source.get("verdict"),
            "old_category": source.get("category"),
            "repair_verdict": repair_verdict,
            "transcription1_stem": stem_one,
            "transcription1_options": options_one,
            "transcription1_usable": usable_transcription(stem_one, options_one),
            "rawVlm2": raw,
            "transcription2_stem": None if payload is None else clean_vlm_stem(payload, qnum),
            "transcription2_options": {} if payload is None else transcribed_options(payload),
            "pngs": [str(path.relative_to(ROOT)) for path in png_paths],
            "cropExtraPt": VERIFY_CROP_EXTRA_PT,
            "preregistrationSha256": prereg_sha,
            "scoredAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            **score_dict,
        }
        append_jsonl(VERIFY_ITEMS_PATH, row)
        existing[item_id] = row
        elapsed = time.time() - started
        print(
            f"[{index}/{len(pending)}] {item_id} {repair_verdict} "
            f"old={source.get('verdict')} stem_f1={score_dict['stem_f1']:.2f} "
            f"{elapsed:.0f}s ({elapsed / index:.1f}s/item)",
            flush=True,
        )
    for document in document_cache.values():
        document.close()
    if model is not None:
        model.to("cpu")
        del model
        del processor
        iso.free_cuda()
    return [existing[item_id] for item_id in item_ids if item_id in existing]


def overlap_counts(rows: list[dict[str, Any]]) -> dict[str, Any]:
    old_labels = (VERDICT_FAITHFUL, VERDICT_NOT_FAITHFUL, VERDICT_UNVERIFIED)
    new_labels = (REPAIRED_VERIFIED, REPAIRED_UNVERIFIED)
    matrix = {old: {new: 0 for new in new_labels} for old in old_labels}
    for row in rows:
        old = str(row.get("old_verdict") or VERDICT_UNVERIFIED)
        new = str(row.get("repair_verdict") or REPAIRED_UNVERIFIED)
        if old not in matrix:
            old = VERDICT_UNVERIFIED
        matrix[old][new] += 1
    return {
        "n": len(rows),
        "repaired_verified": sum(1 for row in rows if row.get("repair_verdict") == REPAIRED_VERIFIED),
        "repaired_unverified": sum(1 for row in rows if row.get("repair_verdict") == REPAIRED_UNVERIFIED),
        "transcription1_usable": sum(1 for row in rows if row.get("transcription1_usable")),
        "overlap": matrix,
    }


def build_repaired_and_masked() -> dict[str, Any]:
    check_preregistration()
    verify_rows = {str(row["id"]): row for row in load_jsonl(VERIFY_ITEMS_PATH)}
    item_ids = algebra_primary_ids()
    missing_verify = [item_id for item_id in item_ids if item_id not in verify_rows]
    if missing_verify:
        raise RuntimeError(f"verification incomplete, missing {len(missing_verify)}")
    items_by_id = scorer.load_items()
    repaired_rows: list[dict[str, Any]] = []
    masked_rows: list[dict[str, Any]] = []
    n_key_missing = 0
    n_below_min = 0
    n_unusable = 0
    withheld_ids: list[str] = []
    for item_id in item_ids:
        original = items_by_id[item_id]
        verify = verify_rows[item_id]
        stem = verify.get("transcription1_stem")
        options = dict(verify.get("transcription1_options") or {})
        key = str(original.get("key") or "").strip().upper()
        usable = bool(verify.get("transcription1_usable")) and usable_transcription(stem, options)
        if not usable:
            n_unusable += 1
        key_present = bool(usable and key in options)
        if usable and not key_present:
            n_key_missing += 1
        report = scorer.mask_stem(str(stem or ""), version=1) if usable else None
        masked_count = int(report["maskedTokenCount"]) if report is not None else 0
        withheld = bool(usable and key_present and masked_count >= 1)
        if usable and key_present and masked_count < 1:
            n_below_min += 1
        if withheld:
            withheld_ids.append(item_id)
        repaired_rows.append(
            {
                "id": item_id,
                "stem": stem,
                "options": options,
                "key": key,
                "claim": original.get("claim"),
                "authority": original.get("authority"),
                "old_verdict": verify.get("old_verdict"),
                "repair_verdict": verify.get("repair_verdict"),
                "transcription1_usable": usable,
                "key_present": key_present,
            }
        )
        masked_rows.append(
            {
                "id": item_id,
                "stem": stem,
                "options": options,
                "key": key,
                "claim": original.get("claim"),
                "authority": original.get("authority"),
                "old_verdict": verify.get("old_verdict"),
                "repair_verdict": verify.get("repair_verdict"),
                "masked_stem": None if report is None else report["masked"],
                "masked_token_count": masked_count,
                "nPlaceholders": None if report is None else report["nPlaceholders"],
                "leakFlags": None if report is None else report["leakFlags"],
                "maskVersion": 1,
                "withheld_quantity": withheld,
            }
        )
    write_jsonl(REPAIRED_ITEMS_PATH, repaired_rows)
    write_jsonl(REPAIRED_MASKED_PATH, masked_rows)
    perturb_repaired_options(masked_rows, withheld_ids)
    summary = {
        "nPrimary": len(item_ids),
        "nUnusableTranscription1": n_unusable,
        "nKeyMissing": n_key_missing,
        "nBelowMinMaskedTokenCount": n_below_min,
        "nWithheldQuantity": len(withheld_ids),
        "nPerturbFailed": sum(
            1 for row in load_jsonl(PERTURBED_PATH) if row.get("perturbFailed")
        ),
        "verification": {
            "all": overlap_counts([verify_rows[item_id] for item_id in item_ids]),
            "algebra-i": overlap_counts(
                [verify_rows[item_id] for item_id in item_ids if items_by_id[item_id]["claim"] == "algebra-i"]
            ),
            "algebra-ii": overlap_counts(
                [verify_rows[item_id] for item_id in item_ids if items_by_id[item_id]["claim"] == "algebra-ii"]
            ),
        },
    }
    print(json.dumps(summary["verification"], indent=2), flush=True)
    dump_json(OUT_DIR / "build-summary.json", summary)
    print(
        f"withheld_quantity={summary['nWithheldQuantity']} unusable_t1={n_unusable} "
        f"key_missing={n_key_missing} below_min={n_below_min}",
        flush=True,
    )
    return summary


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


class PerturbTimeout(BaseException):
    """Must not subclass RuntimeError: perturb_choices swallows RuntimeError."""

    pass


def _perturb_alarm(_signum: int, _frame: Any) -> None:
    raise PerturbTimeout("rank-preserving perturb exceeded 20 seconds")


def perturb_repaired_options(masked_rows: list[dict[str, Any]], withheld_ids: list[str]) -> None:
    by_id = {str(row["id"]): row for row in masked_rows}
    existing = {str(row["id"]): row for row in load_jsonl(PERTURBED_PATH)}
    n_failed = sum(1 for row in existing.values() if row.get("perturbFailed"))
    n_no_numeral = sum(1 for row in existing.values() if row.get("noNumeral"))
    pending = [item_id for item_id in withheld_ids if item_id not in existing]
    print(
        f"perturb rank-preserving requested={len(withheld_ids)} already={len(existing)} pending={len(pending)}",
        flush=True,
    )
    signal.signal(signal.SIGALRM, _perturb_alarm)
    started = time.time()
    for index, item_id in enumerate(pending, start=1):
        row = by_id[item_id]
        choices = dict(row["options"])
        rng = rng_for(item_id, ARM_PRESERVING)
        try:
            signal.alarm(20)
            perturbed, substitution_map, no_numeral = perturb_choices(choices, ARM_PRESERVING, rng)
            signal.alarm(0)
            failed = False
            error = None
        except PerturbTimeout as exc:
            signal.alarm(0)
            perturbed = dict(choices)
            substitution_map = {}
            no_numeral = False
            failed = True
            error = str(exc)
            n_failed += 1
        except RuntimeError as exc:
            signal.alarm(0)
            perturbed = dict(choices)
            substitution_map = {}
            no_numeral = False
            failed = True
            error = str(exc)
            n_failed += 1
        if no_numeral:
            n_no_numeral += 1
        out_row = {
            "id": item_id,
            "arm": ARM_PRESERVING,
            "claim": row.get("claim"),
            "authority": row.get("authority"),
            "key": row.get("key"),
            "choices": perturbed,
            "originalChoices": choices,
            "substitutionMap": substitution_map,
            "noNumeral": no_numeral,
            "perturbFailed": failed,
            "perturbError": error,
            "repair_verdict": row.get("repair_verdict"),
            "seed": SEED,
        }
        scorer.append_jsonl(PERTURBED_PATH, [out_row])
        existing[item_id] = out_row
        if index % 25 == 0 or failed:
            elapsed = time.time() - started
            print(
                f"  perturb {index}/{len(pending)} {item_id} failed={failed} {elapsed:.0f}s",
                flush=True,
            )
    ordered = [existing[item_id] for item_id in withheld_ids if item_id in existing]
    write_jsonl(PERTURBED_PATH, ordered)
    print(
        f"wrote {PERTURBED_PATH.relative_to(ROOT)} n={len(ordered)} "
        f"no_numeral={n_no_numeral} perturb_failed={n_failed}",
        flush=True,
    )


def repaired_scoring_items() -> list[dict[str, Any]]:
    items_by_id = scorer.load_items()
    out: list[dict[str, Any]] = []
    for row in load_jsonl(REPAIRED_MASKED_PATH):
        if not row.get("withheld_quantity"):
            continue
        original = items_by_id[str(row["id"])]
        item = dict(original)
        item["stem"] = row["stem"]
        item["choices"] = dict(row["options"])
        item["key"] = row["key"]
        item["_masked_stem"] = row["masked_stem"]
        item["_mask_version"] = 1
        item["_mask_report"] = {
            "masked": row["masked_stem"],
            "nPlaceholders": row["nPlaceholders"],
            "maskedTokenCount": row["masked_token_count"],
        }
        item["_repair_verdict"] = row["repair_verdict"]
        out.append(item)
    return out


def attach_perturbed(base_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    perturbed = {
        str(row["id"]): row
        for row in load_jsonl(PERTURBED_PATH)
        if not row.get("perturbFailed")
    }
    out: list[dict[str, Any]] = []
    for item in base_items:
        row = perturbed.get(str(item["id"]))
        if row is None:
            continue
        copy = dict(item)
        copy["choices"] = dict(row["choices"])
        copy["_no_numeral"] = bool(row.get("noNumeral"))
        out.append(copy)
    return out


def scores_path(name: str) -> Path:
    return OUT_DIR / f"scores-{name}.jsonl"


def score_item_list(
    model: Any,
    tokenizer: Any,
    device: Any,
    items: list[dict[str, Any]],
    out_path: Path,
    batch_size: int,
    arm: str,
) -> list[dict[str, Any]]:
    done_ids = scorer.already_scored_ids(out_path)
    scored_rows = scorer.load_existing_rows(out_path)
    pending = [item for item in items if str(item["id"]) not in done_ids]
    print(
        f"scoring {out_path.name} pending={len(pending)} already={len(done_ids)} arm={arm}",
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
                "repair_verdict": item.get("_repair_verdict"),
                "masked_stem": item.get("_masked_stem"),
                "masked_token_count": (item.get("_mask_report") or {}).get("maskedTokenCount"),
            }
            new_rows.append(row)
            scored_rows.append(row)
        scorer.append_jsonl(out_path, new_rows)
        done = len(scored_rows)
        rate = sum(int(row["correct"]) for row in scored_rows) / done if done else 0.0
        print(f"  {out_path.name} {done}/{len(items)} rate={rate:.4f}", flush=True)
    by_id = {str(row["id"]): row for row in scored_rows}
    ordered = [by_id[str(item["id"])] for item in items if str(item["id"]) in by_id]
    return ordered


def letter_agreement(scored: list[dict[str, Any]], saved_path: Path) -> dict[str, Any]:
    saved = {str(row["id"]): row for row in load_jsonl(saved_path)}
    agree = 0
    compared = 0
    mismatches: list[dict[str, str]] = []
    for row in scored:
        item_id = str(row["id"])
        if item_id not in saved:
            raise RuntimeError(f"saved prediction missing {item_id} in {saved_path}")
        compared += 1
        saved_letter = str(saved[item_id]["chosen_letter"]).strip().upper()
        predicted = str(row.get("predicted_letter") or row.get("chosen_letter")).strip().upper()
        if predicted == saved_letter:
            agree += 1
        else:
            mismatches.append({"id": item_id, "rerun": predicted, "saved": saved_letter})
    rate = agree / compared if compared else 0.0
    return {
        "n": compared,
        "nAgree": agree,
        "agreement": rate,
        "clearsFloor": rate >= iso.MIN_REPRODUCTION,
        "label": "clears_floor" if rate >= iso.MIN_REPRODUCTION else "below_floor",
        "disagreeingIds": mismatches,
        "savedPath": str(saved_path.relative_to(ROOT)),
    }


def run_catalog() -> dict[str, Any]:
    check_preregistration()
    fidelity = census_fidelity_by_id()
    items_by_id = {str(item["id"]): item for item in load_item_list()}
    out: dict[str, Any] = {}
    for cell, name in (
        (CELL_GEOMETRY_LC, "geometry_lower_central"),
        (CELL_EQAO_G6_LC, "eqao_g6_lower_central"),
    ):
        cell_rows = [row for row in fidelity.values() if cell in (row.get("cells") or [])]
        if not cell_rows:
            out[name] = {
                "skipped": True,
                "reason": f"no print-faithful transcriptions for {cell}",
            }
            print(f"catalog skip {name}: no transcriptions", flush=True)
            continue
        usable_items: list[dict[str, Any]] = []
        n_missing = 0
        for row in cell_rows:
            stem, options = transcription_one(row)
            if not usable_transcription(stem, options):
                n_missing += 1
                continue
            item = dict(items_by_id[str(row["id"])])
            item["choices"] = options
            usable_items.append(item)
        scored = score_program(usable_items, middle_value_option)
        stats = summarize_scored(scored)
        out[name] = {
            "skipped": False,
            "cell": cell,
            "nOriginalFired": len(cell_rows),
            "nMissingTranscription1": n_missing,
            "nWithRepairedOptions": len(usable_items),
            "nRuleFires": stats["n"],
            "passes": stats["nCorrect"],
            "passRate": stats["passRate"],
            "chance": stats["chanceRate"],
            "itemCi95": stats["itemBootstrapCi95"],
            "clusterCi95": stats["clusterBootstrapCi95"],
            "clearsItemBar": bool(stats["clearsItemBar"]),
            "nAdministrations": stats["nAdministrations"],
        }
        print(
            f"catalog {name} original_fired={len(cell_rows)} missing_t1={n_missing} "
            f"rule_fires={stats['n']} rate={stats['passRate']:.3f} "
            f"item_ci={stats['itemBootstrapCi95']} bar={stats['clearsItemBar']}",
            flush=True,
        )
    return out


def run_model_gpu(model_key: str, repaired_items: list[dict[str, Any]], do_amendment: bool) -> None:
    require_cuda()
    check_preregistration()
    import torch

    device = scorer.require_cuda()
    spec = iso.MODELS[model_key]
    batch_size = int(spec["batch_size"])
    print(f"loading {spec['model_id']} {spec['revision']}", flush=True)
    model, tokenizer = iso.load_causal_lm(model_key, device)
    score_item_list(
        model,
        tokenizer,
        device,
        repaired_items,
        scores_path(f"{model_key}-repaired"),
        batch_size,
        "repaired",
    )
    isomorph_items = attach_perturbed(repaired_items)
    score_item_list(
        model,
        tokenizer,
        device,
        isomorph_items,
        scores_path(f"{model_key}-repaired-{ARM_PRESERVING}"),
        batch_size,
        ARM_PRESERVING,
    )
    if do_amendment:
        run_14b_amendment_with_model(model, tokenizer, device)
    model.to("cpu")
    del model
    del tokenizer
    iso.free_cuda()
    print(f"unloaded {model_key}", flush=True)


def census_algebra_items() -> list[dict[str, Any]]:
    return iso.prepare_base_items()


def run_14b_amendment_with_model(model: Any, tokenizer: Any, device: Any) -> dict[str, Any]:
    base_items = census_algebra_items()
    original_choices = {str(item["id"]): dict(item["choices"]) for item in base_items}
    original_items = iso.attach_choices(base_items, original_choices)
    original_rows = score_item_list(
        model,
        tokenizer,
        device,
        original_items,
        scores_path("14b-amendment-original"),
        1,
        "original",
    )
    agreement = letter_agreement(original_rows, SAVED_PREDICTIONS["14b"])
    print(
        f"14B amendment agreement {agreement['nAgree']}/{agreement['n']} = "
        f"{agreement['agreement']:.4f} label={agreement['label']}",
        flush=True,
    )
    for arm in ARMS:
        path = ISOMORPH_PERTURBED_DIR / f"perturbed-items-{arm}.jsonl"
        if not path.exists():
            raise RuntimeError(f"original-layer perturbed items missing: {path}")
        choices = {str(row["id"]): dict(row["choices"]) for row in load_jsonl(path)}
        arm_items = iso.attach_choices(base_items, choices)
        score_item_list(
            model,
            tokenizer,
            device,
            arm_items,
            scores_path(f"14b-amendment-{arm}"),
            1,
            arm,
        )
        print(f"14B amendment scored {arm} label={agreement['label']}", flush=True)
    dump_json(
        OUT_DIR / "amendment-14b-agreement.json",
        agreement,
    )
    return agreement


def subset_stats(
    predictions: dict[str, dict[str, Any]],
    ids: list[str],
) -> dict[str, Any]:
    present = [item_id for item_id in ids if item_id in predictions]
    stats = iso.rate_stats([predictions[item_id] for item_id in present])
    stats["nRequested"] = len(ids)
    stats["nMissingScores"] = len(ids) - len(present)
    return stats


def original_text_layer_stats(model_key: str, ids: list[str]) -> dict[str, Any]:
    predictions = {str(row["id"]): row for row in load_jsonl(SAVED_PREDICTIONS[model_key])}
    return lm_row(predictions, ids)


def id_lists() -> dict[str, list[str]]:
    masked = {str(row["id"]): row for row in load_jsonl(REPAIRED_MASKED_PATH)}
    items_by_id = scorer.load_items()
    primary = algebra_primary_ids()
    algebra_i = [item_id for item_id in primary if items_by_id[item_id]["claim"] == "algebra-i"]
    algebra_ii = [item_id for item_id in primary if items_by_id[item_id]["claim"] == "algebra-ii"]
    withheld = [item_id for item_id in primary if masked[item_id].get("withheld_quantity")]
    verified = [
        item_id
        for item_id in withheld
        if masked[item_id].get("repair_verdict") == REPAIRED_VERIFIED
    ]
    verb = item_verb_class()
    perturb_ok = {
        str(row["id"])
        for row in load_jsonl(PERTURBED_PATH)
        if not row.get("perturbFailed")
    }

    def verb_ids(pool: list[str], verb_class: str) -> list[str]:
        return [item_id for item_id in pool if verb.get(item_id) == verb_class]

    return {
        "algebra_i_original": algebra_i,
        "algebra_ii_original": algebra_ii,
        "algebra_i_repaired_all": [item_id for item_id in withheld if item_id in algebra_i],
        "algebra_ii_repaired_all": [item_id for item_id in withheld if item_id in algebra_ii],
        "algebra_i_repaired_verified": [item_id for item_id in verified if item_id in algebra_i],
        "algebra_ii_repaired_verified": [item_id for item_id in verified if item_id in algebra_ii],
        "algebra_i_execution_all": verb_ids([item_id for item_id in withheld if item_id in algebra_i], EXECUTION),
        "algebra_i_recognition_all": verb_ids(
            [item_id for item_id in withheld if item_id in algebra_i], RECOGNITION
        ),
        "algebra_i_mixed_all": verb_ids([item_id for item_id in withheld if item_id in algebra_i], MIXED),
        "algebra_i_execution_verified": verb_ids(
            [item_id for item_id in verified if item_id in algebra_i], EXECUTION
        ),
        "algebra_i_recognition_verified": verb_ids(
            [item_id for item_id in verified if item_id in algebra_i], RECOGNITION
        ),
        "algebra_ii_execution_all": verb_ids(
            [item_id for item_id in withheld if item_id in algebra_ii], EXECUTION
        ),
        "algebra_ii_recognition_all": verb_ids(
            [item_id for item_id in withheld if item_id in algebra_ii], RECOGNITION
        ),
        "algebra_ii_execution_verified": verb_ids(
            [item_id for item_id in verified if item_id in algebra_ii], EXECUTION
        ),
        "algebra_ii_recognition_verified": verb_ids(
            [item_id for item_id in verified if item_id in algebra_ii], RECOGNITION
        ),
        "algebra_i_isomorph_all": [
            item_id for item_id in withheld if item_id in algebra_i and item_id in perturb_ok
        ],
        "algebra_ii_isomorph_all": [
            item_id for item_id in withheld if item_id in algebra_ii and item_id in perturb_ok
        ],
        "algebra_i_isomorph_verified": [
            item_id for item_id in verified if item_id in algebra_i and item_id in perturb_ok
        ],
        "algebra_ii_isomorph_verified": [
            item_id for item_id in verified if item_id in algebra_ii and item_id in perturb_ok
        ],
    }


def summarize_amendment() -> dict[str, Any]:
    original_path = scores_path("14b-amendment-original")
    if not original_path.exists():
        return {"status": "not_scored"}
    original_rows = load_jsonl(original_path)
    agreement = letter_agreement(original_rows, SAVED_PREDICTIONS["14b"])
    if not scores_path(f"14b-amendment-{ARM_PRESERVING}").exists():
        return {"status": "original_only", "agreement": agreement, "label": agreement["label"]}
    base_items = census_algebra_items()
    subsets = iso.build_subsets(base_items)
    scores = {
        "original": {str(row["id"]): row for row in original_rows},
        ARM_PRESERVING: {str(row["id"]): row for row in load_jsonl(scores_path(f"14b-amendment-{ARM_PRESERVING}"))},
        ARM_SCRAMBLED: {str(row["id"]): row for row in load_jsonl(scores_path(f"14b-amendment-{ARM_SCRAMBLED}"))},
    }
    excluded = iso.no_numeral_ids()
    subset_rows: dict[str, Any] = {}
    for subset_key, _label in iso.SUBSET_SPECS:
        ids = subsets[subset_key]
        paired_ids = [item_id for item_id in ids if item_id not in excluded]
        original_paired = [int(bool(scores["original"][item_id]["correct"])) for item_id in paired_ids]
        preserving_paired = [
            int(bool(scores[ARM_PRESERVING][item_id]["correct"])) for item_id in paired_ids
        ]
        scrambled_paired = [
            int(bool(scores[ARM_SCRAMBLED][item_id]["correct"])) for item_id in paired_ids
        ]
        n_paired = len(paired_ids)
        preserving_diff = iso.paired_difference_ci(original_paired, preserving_paired, seed=31 + n_paired)
        scrambled_diff = iso.paired_difference_ci(original_paired, scrambled_paired, seed=31 + n_paired)
        subset_rows[subset_key] = {
            "n": len(ids),
            "nPaired": n_paired,
            "original": iso.rate_stats([scores["original"][item_id] for item_id in ids]),
            "rankPreserving": iso.rate_stats([scores[ARM_PRESERVING][item_id] for item_id in ids]),
            "scrambled": iso.rate_stats([scores[ARM_SCRAMBLED][item_id] for item_id in ids]),
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
    return {
        "status": "scored",
        "label": agreement["label"],
        "agreement": agreement,
        "note": (
            "clears_floor means letter agreement >= 0.98. below_floor arms are reported "
            "so a reader can see them; they are not a pass of the isomorph control."
            if agreement["label"] == "below_floor"
            else "letter agreement cleared 0.98; arms are a claimed-style isomorph report."
        ),
        "subsets": subset_rows,
    }


def fmt_ci(ci: list[float]) -> str:
    return f"[{ci[0]:.3f}, {ci[1]:.3f}]"


def yes_no(flag: bool) -> str:
    return "yes" if flag else "no"


def rate_line(stats: dict[str, Any]) -> str:
    return (
        f"n={stats['n']} {stats['passRate']:.3f} {fmt_ci(stats['ci95'])} "
        f"modal {stats.get('modalLetter')} ({stats.get('modalFrequency', 0.0):.3f}) "
        f"bar={yes_no(bool(stats.get('clearsBar')))}"
    )


def write_readme(payload: dict[str, Any]) -> None:
    verification = payload["verification"]
    catalog = payload["catalog"]
    amendment = payload["amendment_14b"]
    models = payload["models"]

    def overlap_table(block: dict[str, Any]) -> str:
        matrix = block["overlap"]
        lines = [
            "| old verdict | repaired_verified | repaired_unverified |",
            "|---|---:|---:|",
        ]
        for old in (VERDICT_FAITHFUL, VERDICT_NOT_FAITHFUL, VERDICT_UNVERIFIED):
            lines.append(
                f"| {old} | {matrix[old][REPAIRED_VERIFIED]} | {matrix[old][REPAIRED_UNVERIFIED]} |"
            )
        return "\n".join(lines)

    lm_lines = [
        "| model | cell | subset | n | pass | rate | chance | 95% CI | modal (freq) | bar |",
        "|---|---|---|---:|---:|---:|---:|---|---|---|",
    ]
    for model_key in MODEL_KEYS:
        model = models[model_key]
        label = model["label"]
        for cell_key, cell_label in (("algebra-i", "Algebra I"), ("algebra-ii", "Algebra II")):
            cell = model["cells"][cell_key]
            for subset_key, subset_label in (
                ("original", "original text-layer"),
                ("repaired_all", "repaired all"),
                ("repaired_verified", "repaired verified"),
            ):
                row = cell[subset_key]
                lm_lines.append(
                    f"| {label} | {cell_label} | {subset_label} | {row['n']} | {row.get('passes', '')} | "
                    f"{row['passRate']:.3f} | {row.get('chance', CHANCE):.3f} | {fmt_ci(row['ci95'])} | "
                    f"{row.get('modalLetter')} ({row.get('modalFrequency', 0):.3f}) | "
                    f"{yes_no(bool(row.get('clearsBar')))} |"
                )

    verb_lines = [
        "| model | cell | class | n | rate | 95% CI | modal (freq) | bar |",
        "|---|---|---|---:|---:|---|---|---|",
    ]
    for model_key in MODEL_KEYS:
        model = models[model_key]
        label = model["label"]
        for cell_key, cell_label in (("algebra-i", "Algebra I"), ("algebra-ii", "Algebra II")):
            cell = model["cells"][cell_key]
            for class_key, class_label in (
                ("execution_all", "execution / repaired all"),
                ("recognition_all", "recognition / repaired all"),
                ("execution_verified", "execution / verified"),
                ("recognition_verified", "recognition / verified"),
            ):
                row = cell[class_key]
                verb_lines.append(
                    f"| {label} | {cell_label} | {class_label} | {row['n']} | "
                    f"{row['passRate']:.3f} | {fmt_ci(row['ci95'])} | "
                    f"{row.get('modalLetter')} ({row.get('modalFrequency', 0):.3f}) | "
                    f"{yes_no(bool(row.get('clearsBar')))} |"
                )

    iso_lines = [
        "| model | cell | subset | n | rate | 95% CI | modal (freq) | bar |",
        "|---|---|---|---:|---:|---|---|---|",
    ]
    for model_key in MODEL_KEYS:
        model = models[model_key]
        label = model["label"]
        for cell_key, cell_label in (("algebra-i", "Algebra I"), ("algebra-ii", "Algebra II")):
            cell = model["cells"][cell_key]
            for subset_key, subset_label in (
                ("isomorph_all", "rank-preserving / repaired all"),
                ("isomorph_verified", "rank-preserving / verified"),
            ):
                row = cell[subset_key]
                iso_lines.append(
                    f"| {label} | {cell_label} | {subset_label} | {row['n']} | "
                    f"{row['passRate']:.3f} | {fmt_ci(row['ci95'])} | "
                    f"{row.get('modalLetter')} ({row.get('modalFrequency', 0):.3f}) | "
                    f"{yes_no(bool(row.get('clearsBar')))} |"
                )

    catalog_lines = []
    for name, title in (
        ("geometry_lower_central", "NY Regents geometry lower-central"),
        ("eqao_g6_lower_central", "EQAO grade 6 lower-central"),
    ):
        row = catalog[name]
        if row.get("skipped"):
            catalog_lines.append(f"- **{title}**: skipped. {row.get('reason')}")
        else:
            catalog_lines.append(
                f"- **{title}**: original fired n={row['nOriginalFired']}, "
                f"missing transcription 1 n={row['nMissingTranscription1']}, "
                f"rule still fires n={row['nRuleFires']}, "
                f"pass {row['passes']}/{row['nRuleFires']} = {row['passRate']:.3f}, "
                f"item CI {fmt_ci(row['itemCi95'])}, chance {row['chance']:.3f}, "
                f"item bar {yes_no(row['clearsItemBar'])}."
            )

    amendment_lines = []
    if amendment.get("status") == "not_scored":
        amendment_lines.append("14B amendment was not scored.")
    else:
        agr = amendment["agreement"]
        amendment_lines.append(
            f"Label: **{amendment['label']}**. Letter agreement with "
            f"`exports/addendum-gpu/masked-stem-14b-items.jsonl`: "
            f"{agr['nAgree']}/{agr['n']} = {agr['agreement']:.4f} "
            f"(floor 0.98)."
        )
        mismatches = agr.get("disagreeingIds") or []
        amendment_lines.append(f"Disagreeing ids ({len(mismatches)}):")
        for mismatch in mismatches:
            amendment_lines.append(
                f"- `{mismatch['id']}`: rerun {mismatch['rerun']} vs saved {mismatch['saved']}"
            )
        if amendment["label"] == "below_floor":
            amendment_lines.append(
                "This is not a pass of the isomorph control. Rank-preserving and scrambled "
                "arms are reported below so a reader can see them."
            )
        if amendment.get("subsets"):
            amendment_lines.append("")
            amendment_lines.append(
                "| subset | n | original | rank-preserving | scrambled | paired Δ preserving | preserving bar |"
            )
            amendment_lines.append("|---|---:|---|---|---|---|---|")
            labels = dict(iso.SUBSET_SPECS)
            for subset_key, subset_label in iso.SUBSET_SPECS:
                row = amendment["subsets"][subset_key]
                amendment_lines.append(
                    f"| {subset_label} | {row['n']} | "
                    f"{row['original']['passRate']:.3f} {fmt_ci(row['original']['ci95'])} | "
                    f"{row['rankPreserving']['passRate']:.3f} {fmt_ci(row['rankPreserving']['ci95'])} | "
                    f"{row['scrambled']['passRate']:.3f} {fmt_ci(row['scrambled']['ci95'])} | "
                    f"{row['pairedRankPreserving']['mean']:+.3f} {fmt_ci(row['pairedRankPreserving']['ci95'])} | "
                    f"{yes_no(row['rankPreserving']['clearsBar'])} |"
                )

    text = f"""# Repaired text layer for Algebra I and Algebra II masked-stem items

Review-2 post-rebuttal W2 / N1: the print-faithful subset is selected (pre-2023 forms, word options over-represented). This addendum repairs the text layer from the page image for every Algebra I (358) and Algebra II (248) masked-stem primary item, then rescores the withheld-quantity population. W8 / N4: Qwen2.5-14B isomorph letters are re-run at batch size 1 and reported with a floor label.

Preregistration: `preregistration.md`, sha256 `{payload['preregistrationSha256']}`, frozen before verification transcription and before language-model scoring. Seed 20260916. Masking hash v1. CUDA letter-logprob argmax reused from `scripts/score_choices_only_local_lm.py`. Does not edit `paper/`.

A pass does not require the tagged operation. Nothing here says students did not learn.

## Verification counts

Transcription 1 is the stored print-fidelity VLM output (Qwen2-VL-7B-Instruct `eed13092…`). Transcription 2 is a second pass with different prompt wording and a 6 pt extra crop margin, same model. `repaired_verified` means the two transcriptions agree under the print-fidelity thresholds (stem F1 >= 0.8 with precision and recall >= 0.8, each option >= 0.9, option counts equal).

Overall: verified {verification['all']['repaired_verified']} / unverified {verification['all']['repaired_unverified']} of {verification['all']['n']}. Transcription 1 usable {verification['all']['transcription1_usable']}.

{overlap_table(verification['all'])}

Algebra I: verified {verification['algebra-i']['repaired_verified']} / unverified {verification['algebra-i']['repaired_unverified']} of 358.

{overlap_table(verification['algebra-i'])}

Algebra II: verified {verification['algebra-ii']['repaired_verified']} / unverified {verification['algebra-ii']['repaired_unverified']} of 248.

{overlap_table(verification['algebra-ii'])}

Withheld-quantity scoring population (usable transcription 1, key present, masked_token_count >= 1): {payload['masking']['nWithheldQuantity']}. Unusable transcription 1: {payload['masking']['nUnusableTranscription1']}. Key missing from repaired options: {payload['masking']['nKeyMissing']}. Below one mask: {payload['masking']['nBelowMinMaskedTokenCount']}.

## Per model: original text-layer vs repaired-all vs repaired-verified

Bar: n >= 10, lower bootstrap 95% CI strictly above chance 0.25 and strictly above the subset modal-letter frequency. Bootstrap: `random.Random.randrange`, 1000 replicates, seed `21 + n`. Original rates are the saved masked-stem predictions on the census text layer, not rerun.

{chr(10).join(lm_lines)}

## Verb-class on the repaired layer

Join `exports/standards-split/item-standards.jsonl` with the locked cluster table. Execution versus recognition-or-interpretation. Mixed-class items are not a claimed row.

{chr(10).join(verb_lines)}

## Rank-preserving isomorph on repaired options

Same numeral substitution as `scripts/perturb_option_numerals.py`, applied to transcription-1 options. Rank-preserving arm only. Items whose perturbation raised or timed out (`perturbFailed`, n={payload.get('perturbFailed', 0)}) are excluded from this table; items with no numeral stay in.

{chr(10).join(iso_lines)}

## Catalog lower-central on repaired options

No new transcription. Geometry and EQAO grade 6 fired sets use stored print-fidelity transcription 1 when it exists.

{chr(10).join(catalog_lines)}

## 14B isomorph amendment

Rerun of Qwen2.5-14B original masked-stem letters on the census text layer, batch size 1, seed 20260916, then both option-numeral arms. Floor remains 0.98.

{chr(10).join(amendment_lines)}

## Files

- `preregistration.md`, `preregistration.sha256`
- `verification-items.jsonl`, `repaired-items.jsonl`, `repaired-masked-items.jsonl`
- `perturbed-items-isomorph_rank_preserving.jsonl`
- `scores-{{7b,14b,phi4}}-repaired.jsonl`, `scores-{{7b,14b,phi4}}-repaired-isomorph_rank_preserving.jsonl`
- `scores-14b-amendment-{{original,isomorph_rank_preserving,isomorph_rank_scrambled}}.jsonl`
- `results.json`

Script: `scripts/run_repaired_layer.py`.
"""
    README_PATH.write_text(text, encoding="utf-8")


def summarize() -> dict[str, Any]:
    prereg_sha = check_preregistration()
    ids = id_lists()
    verify_rows = load_jsonl(VERIFY_ITEMS_PATH)
    items_by_id = scorer.load_items()
    verification = {
        "all": overlap_counts(verify_rows),
        "algebra-i": overlap_counts(
            [row for row in verify_rows if items_by_id[str(row["id"])]["claim"] == "algebra-i"]
        ),
        "algebra-ii": overlap_counts(
            [row for row in verify_rows if items_by_id[str(row["id"])]["claim"] == "algebra-ii"]
        ),
    }
    catalog_path = OUT_DIR / "catalog-lower-central.json"
    if catalog_path.exists():
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    else:
        catalog = run_catalog()
        dump_json(catalog_path, catalog)
    models_out: dict[str, Any] = {}
    for model_key in MODEL_KEYS:
        repaired = {str(row["id"]): row for row in load_jsonl(scores_path(f"{model_key}-repaired"))}
        isomorph = {
            str(row["id"]): row
            for row in load_jsonl(scores_path(f"{model_key}-repaired-{ARM_PRESERVING}"))
        }
        spec = iso.MODELS[model_key]
        cells: dict[str, Any] = {}
        for cell_key, original_key, all_key, verified_key, iso_all_key, iso_ver_key in (
            (
                "algebra-i",
                "algebra_i_original",
                "algebra_i_repaired_all",
                "algebra_i_repaired_verified",
                "algebra_i_isomorph_all",
                "algebra_i_isomorph_verified",
            ),
            (
                "algebra-ii",
                "algebra_ii_original",
                "algebra_ii_repaired_all",
                "algebra_ii_repaired_verified",
                "algebra_ii_isomorph_all",
                "algebra_ii_isomorph_verified",
            ),
        ):
            prefix = "algebra_i" if cell_key == "algebra-i" else "algebra_ii"
            cells[cell_key] = {
                "original": original_text_layer_stats(model_key, ids[original_key]),
                "repaired_all": subset_stats(repaired, ids[all_key]),
                "repaired_verified": subset_stats(repaired, ids[verified_key]),
                "execution_all": subset_stats(repaired, ids[f"{prefix}_execution_all"]),
                "recognition_all": subset_stats(repaired, ids[f"{prefix}_recognition_all"]),
                "execution_verified": subset_stats(repaired, ids[f"{prefix}_execution_verified"]),
                "recognition_verified": subset_stats(repaired, ids[f"{prefix}_recognition_verified"]),
                "isomorph_all": subset_stats(isomorph, ids[iso_all_key]),
                "isomorph_verified": subset_stats(isomorph, ids[iso_ver_key]),
            }
            if cell_key == "algebra-i":
                cells[cell_key]["mixed_all"] = subset_stats(repaired, ids["algebra_i_mixed_all"])
        models_out[model_key] = {
            "label": spec["label"],
            "modelId": spec["model_id"],
            "modelRevision": spec["revision"],
            "cells": cells,
        }
    build_summary_path = OUT_DIR / "build-summary.json"
    if build_summary_path.exists():
        masking = {
            key: json.loads(build_summary_path.read_text(encoding="utf-8"))[key]
            for key in (
                "nPrimary",
                "nUnusableTranscription1",
                "nKeyMissing",
                "nBelowMinMaskedTokenCount",
                "nWithheldQuantity",
            )
        }
    else:
        masking = {
            "nPrimary": 606,
            "nUnusableTranscription1": verification["all"]["n"]
            - verification["all"]["transcription1_usable"],
            "nKeyMissing": sum(
                1
                for row in load_jsonl(REPAIRED_ITEMS_PATH)
                if row.get("transcription1_usable") and not row.get("key_present")
            ),
            "nBelowMinMaskedTokenCount": sum(
                1
                for row in load_jsonl(REPAIRED_MASKED_PATH)
                if row.get("stem")
                and (row.get("masked_token_count") or 0) < 1
                and str(row.get("id"))
                in {str(item["id"]) for item in load_jsonl(REPAIRED_ITEMS_PATH) if item.get("key_present")}
            ),
            "nWithheldQuantity": sum(
                1 for row in load_jsonl(REPAIRED_MASKED_PATH) if row.get("withheld_quantity")
            ),
        }
    payload = {
        "status": "complete",
        "preregistration": str(PREREG_PATH.relative_to(ROOT)),
        "preregistrationSha256": prereg_sha,
        "seed": SEED,
        "chance": CHANCE,
        "maskingHash": "v1",
        "verification": verification,
        "masking": masking,
        "idLists": {key: len(value) for key, value in ids.items()},
        "catalog": catalog,
        "models": models_out,
        "amendment_14b": summarize_amendment(),
        "perturbFailed": sum(
            1 for row in load_jsonl(PERTURBED_PATH) if row.get("perturbFailed")
        ),
        "writtenAt": datetime.now(timezone.utc).isoformat(),
    }
    dump_json(RESULTS_PATH, payload)
    write_readme(payload)
    print(f"wrote {RESULTS_PATH}", flush=True)
    print(f"wrote {README_PATH}", flush=True)
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--stage",
        choices=["verify", "build", "catalog", "score", "summarize", "all"],
        default="all",
    )
    parser.add_argument("--model", choices=["7b", "14b", "phi4", "all"], default="all")
    parser.add_argument("--limit", type=int, default=0)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    prereg_sha = check_preregistration()
    print(f"preregistration sha256 {prereg_sha}", flush=True)
    if args.stage in ("verify", "all"):
        run_verify(args.limit)
    if args.stage in ("build", "all"):
        build_repaired_and_masked()
    if args.stage in ("catalog", "all"):
        dump_json(OUT_DIR / "catalog-lower-central.json", run_catalog())
    if args.stage in ("score", "all"):
        if args.limit > 0:
            raise RuntimeError("refusing to GPU-score a --limit subset; finish verify/build without scoring")
        repaired_items = repaired_scoring_items()
        model_keys = list(MODEL_KEYS) if args.model == "all" else [args.model]
        for model_key in model_keys:
            run_model_gpu(model_key, repaired_items, do_amendment=(model_key == "14b"))
    if args.stage in ("summarize", "all"):
        summarize()


if __name__ == "__main__":
    main()
