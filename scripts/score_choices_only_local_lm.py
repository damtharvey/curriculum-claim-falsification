#!/usr/bin/env python3
"""Choices-only next-token scoring with a local instruction-tuned LM on GPU."""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

ROOT = Path(__file__).resolve().parents[1]
ITEMS_PATH = ROOT / "data" / "items.jsonl"
SIBLING_FILTER_PATH = ROOT / "exports" / "addendum" / "choices-only-clean-filter.json"
SIBLING_KEEP_IDS_PATH = ROOT / "exports" / "addendum" / "choices-only-clean-item-ids.json"
SCORED_SUBAGENT_PATH = ROOT / "exports" / "choices-only" / "scored.jsonl"
BATCH_MAP_DIR = ROOT / "exports" / "choices-only" / "batches"
OUT_DIR = ROOT / "exports" / "addendum-gpu"
SUMMARY_PATH = OUT_DIR / "choices-only-local-lm.json"
ITEMS_OUT_PATH = OUT_DIR / "choices-only-local-lm-items.jsonl"
STEM_ITEMS_OUT_PATH = OUT_DIR / "with-stem-local-lm-items.jsonl"
FILTER_COPY_PATH = OUT_DIR / "clean-filter.json"
README_PATH = OUT_DIR / "README.md"

MODEL_ID = "Qwen/Qwen2.5-7B-Instruct"
MODEL_REVISION = "a09a35458c702b33eeacc393d103063234e8bc28"
SNAPSHOT_PATH = (
    Path.home()
    / ".cache"
    / "huggingface"
    / "hub"
    / "models--Qwen--Qwen2.5-7B-Instruct"
    / "snapshots"
    / MODEL_REVISION
)
EXPERIMENT_SEED = 20260916
WITH_STEM_N = 200
BATCH_SIZE = 8

SYSTEM_PROMPT = (
    "You answer multiple-choice questions. Reply with only the letter of the correct option."
)
CHOICES_ONLY_USER_TEMPLATE = """Pick the letter of the correct answer. You see only the answer options. There is no question stem and no source or exam name.

{options_block}"""
WITH_STEM_USER_TEMPLATE = """Pick the letter of the correct answer.

Question:
{stem}

Options:
{options_block}"""
MASKED_STEM_USER_TEMPLATE = """Pick the letter of the correct answer. Numeric quantities in the question have been replaced by [N].

Question:
{stem}

Options:
{options_block}"""
MASKED_STEM_V2_USER_TEMPLATE = """Pick the letter of the correct answer. Given quantities, named figure types, and variable bindings in the question have been replaced by [N].

Question:
{stem}

Options:
{options_block}"""
PREREG_V2_PATH = OUT_DIR / "masked-stem-v2-preregistration.md"

SINGLE_LETTER_RE = re.compile(r"^[A-E]$")
PLACEHOLDER = "[N]"
ALWAYS_B_BASELINE = 0.275
AUDIT_N = 40
POSITION_JSON_PATH = OUT_DIR / "position-and-memorization.json"
OPTIONS_ONLY_7B_ITEMS = OUT_DIR / "choices-only-local-lm-items.jsonl"
OPTIONS_ONLY_14B_ITEMS = OUT_DIR / "choices-only-local-lm-14b-items.jsonl"
PREREG_PATH = OUT_DIR / "masked-stem-preregistration.md"
WITNESS_CELLS = ("nyregents::geometry", "eqao::g6")
NAMED_CELLS = (
    "nyregents::algebra-i",
    "nyregents::geometry",
    "eqao::g6",
    "timss::knowing",
    "timss::applying",
    "timss::reasoning",
)
CARDINAL_WORDS = (
    "zero",
    "one",
    "two",
    "three",
    "four",
    "five",
    "six",
    "seven",
    "eight",
    "nine",
    "ten",
    "eleven",
    "twelve",
    "thirteen",
    "fourteen",
    "fifteen",
    "sixteen",
    "seventeen",
    "eighteen",
    "nineteen",
    "twenty",
    "thirty",
    "forty",
    "fifty",
    "sixty",
    "seventy",
    "eighty",
    "ninety",
    "hundred",
    "thousand",
    "million",
    "billion",
)
FRACTION_TAILS = (
    "half",
    "halves",
    "third",
    "thirds",
    "fourth",
    "fourths",
    "fifth",
    "fifths",
    "sixth",
    "sixths",
    "seventh",
    "sevenths",
    "eighth",
    "eighths",
    "ninth",
    "ninths",
    "tenth",
    "tenths",
    "eleventh",
    "elevenths",
    "twelfth",
    "twelfths",
    "hundredth",
    "hundredths",
    "thousandth",
    "thousandths",
    "quarter",
    "quarters",
)
VULGAR_FRACTION_RE = re.compile(r"[½⅓⅔¼¾⅕⅖⅗⅘⅙⅚⅐⅛⅜⅝⅞⅑⅒]")
SUPER_SUB_DIGIT_RE = re.compile(r"[⁰¹²³⁴⁵⁶⁷⁸⁹₀₁₂₃₄₅₆₇₈₉]")
CARDINAL_RE = re.compile(
    r"\b(?:" + "|".join(sorted(CARDINAL_WORDS, key=len, reverse=True)) + r")\b",
    re.IGNORECASE,
)
HYPHEN_FRACTION_RE = re.compile(
    r"\b(?:"
    + "|".join(sorted(CARDINAL_WORDS, key=len, reverse=True))
    + r")\s*-\s*(?:"
    + "|".join(FRACTION_TAILS)
    + r")\b",
    re.IGNORECASE,
)
SCALE_WORD_RE = re.compile(r"\b(?:twice|thrice)\b", re.IGNORECASE)
STANDALONE_FRACTION_WORD_RE = re.compile(
    r"\b(?:half|halves|quarter|quarters)\b",
    re.IGNORECASE,
)
CURRENCY_AMOUNT_RE = re.compile(
    r"\$\s*[-−]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?"
)
PERCENT_NUM_RE = re.compile(
    r"[-−]?(?:\d{1,3}(?:,\d{3})*|\d+)(?:\.\d+)?(?=\s*%|\s*percent\b)",
    re.IGNORECASE,
)
DECIMAL_RE = re.compile(r"(?<![\d.])[-−]?(?:\d{1,3}(?:,\d{3})*|\d+)?\.\d+")
COMMA_INT_RE = re.compile(r"(?<![\d.])[-−]?\d{1,3}(?:,\d{3})+\b")
INTEGER_RE = re.compile(r"(?<![\d.])[-−]?\d+(?!\.\d)")
SPACED_FRACTION_RE = re.compile(
    r"\b(?:"
    + "|".join(sorted(CARDINAL_WORDS, key=len, reverse=True))
    + r")\s+(?:"
    + "|".join(FRACTION_TAILS)
    + r")\b",
    re.IGNORECASE,
)
OCR_SPLIT_FRACTION_RE = re.compile(
    r"\bt\s+hirds?\b|\bf\s+ourths?\b|\bf\s+ifths?\b|\bt\s+enths?\b",
    re.IGNORECASE,
)
PLACEHOLDER_FRACTION_RE = re.compile(
    re.escape(PLACEHOLDER) + r"\s+(?:" + "|".join(FRACTION_TAILS) + r")\b",
    re.IGNORECASE,
)
ALGEBRA_LEAK_RE = re.compile(
    r"\b\d+\s*[a-zA-Z]\b|\b\d+\s*[+\-−]\s*\d+\s*[a-zA-Z]|\(\s*[-−]?\d+(?:\.\d+)?\s*,\s*[-−]?\d+"
)
NAMED_FIGURE_RE = re.compile(
    r"\b(?:isosceles|equilateral|scalene)\b"
    r"|\bregular\s+(?:right\s+)?"
    r"(?:triangle|quadrilateral|polygon|pentagon|hexagon|heptagon|octagon|"
    r"nonagon|decagon|n-gon)s?\b"
    r"|\bright\s+triangles?\b"
    r"|\b(?:triangle|parallelogram|rhombus|rhombi|rectangle|square|trapezoid|"
    r"trapezium|kite|pentagon|hexagon|heptagon|octagon|decagon|quadrilateral|"
    r"cube|cuboid|prism|pyramid|cylinder|cone|sphere|hemisphere|circle)s?\b",
    re.I,
)
FUNC_ASSIGN_RE = re.compile(
    r"(?P<left>\b(?:let|given(?:\s+that)?)\s+[a-zA-Z]\s*\(\s*[a-zA-Z]\s*\)\s*"
    r"(?:=|equals|equal to|5)\s*)(?P<rhs>[^.?!,;]+)",
    re.I,
)
FUNC_ASSIGN_PLACEHOLDER_RE = re.compile(
    r"(?P<left>\b(?:let|given(?:\s+that)?)\s+[a-zA-Z]\s*\(\s*[a-zA-Z]\s*\)\s*\[N\]\s*)"
    r"(?P<rhs>[^.?!,;]+)",
    re.I,
)
LET_ASSIGN_RE = re.compile(
    r"(?P<left>\blet\s+[a-zA-Z](?:\s*\(\s*[a-zA-Z]\s*\))?\s*"
    r"(?:=|equals|equal to|be)\s*)(?P<rhs>[^.?!,;]+)",
    re.I,
)
LETTER_EQ_EXPR_RE = re.compile(
    r"(?P<left>\b[a-zA-Z]\s*=\s*)(?P<rhs>[-−\[].{0,80}?)(?=(?:,|;|\.|\?|which\b|what\b|$))",
    re.I,
)
LEFTOVER_COEFFICIENT_RE = re.compile(
    r"(?<!\[N\])(?<!\d)(?P<coef>\d+(?:\.\d+)?)(?=[a-zA-Z(])"
)


def bootstrap_ci(flags: list[int], n_boot: int = 1000, seed: int = 11) -> tuple[float, float]:
    """Percentile bootstrap matching scripts/score_choices_only.py (Random.randrange)."""
    if not flags:
        return (0.0, 0.0)
    rng = random.Random(seed)
    n = len(flags)
    samples: list[float] = []
    for _ in range(n_boot):
        tot = 0
        for _i in range(n):
            tot += flags[rng.randrange(n)]
        samples.append(tot / n)
    samples.sort()
    lo = samples[int(0.025 * (n_boot - 1))]
    hi = samples[int(0.975 * (n_boot - 1))]
    return (lo, hi)


def _replace_currency(match: re.Match[str]) -> str:
    return "$" + PLACEHOLDER


def leak_flags(masked: str) -> list[str]:
    flags: list[str] = []
    if re.search(r"\d", masked) or SUPER_SUB_DIGIT_RE.search(masked):
        flags.append("remaining_digit")
    if VULGAR_FRACTION_RE.search(masked):
        flags.append("remaining_vulgar_fraction")
    if CARDINAL_RE.search(masked):
        flags.append("remaining_cardinal")
    if HYPHEN_FRACTION_RE.search(masked):
        flags.append("remaining_hyphen_fraction")
    if SCALE_WORD_RE.search(masked):
        flags.append("remaining_scale_word")
    if STANDALONE_FRACTION_WORD_RE.search(masked):
        flags.append("remaining_fraction_word")
    if ALGEBRA_LEAK_RE.search(masked):
        flags.append("remaining_algebra_or_coordinate")
    return flags


def _mask_pass(text: str) -> str:
    masked = VULGAR_FRACTION_RE.sub(PLACEHOLDER, text)
    masked = SUPER_SUB_DIGIT_RE.sub(PLACEHOLDER, masked)
    masked = HYPHEN_FRACTION_RE.sub(PLACEHOLDER, masked)
    masked = SPACED_FRACTION_RE.sub(PLACEHOLDER, masked)
    masked = OCR_SPLIT_FRACTION_RE.sub(PLACEHOLDER, masked)
    masked = CURRENCY_AMOUNT_RE.sub(_replace_currency, masked)
    masked = PERCENT_NUM_RE.sub(PLACEHOLDER, masked)
    masked = DECIMAL_RE.sub(PLACEHOLDER, masked)
    masked = COMMA_INT_RE.sub(PLACEHOLDER, masked)
    masked = INTEGER_RE.sub(PLACEHOLDER, masked)
    masked = SCALE_WORD_RE.sub(PLACEHOLDER, masked)
    masked = STANDALONE_FRACTION_WORD_RE.sub(PLACEHOLDER, masked)
    masked = CARDINAL_RE.sub(PLACEHOLDER, masked)
    masked = PLACEHOLDER_FRACTION_RE.sub(PLACEHOLDER, masked)
    masked = re.sub(r"[ \t]{2,}", " ", masked)
    return masked


def _mask_assignments(text: str) -> str:
    masked = FUNC_ASSIGN_RE.sub(lambda match: match.group("left") + PLACEHOLDER, text)
    masked = FUNC_ASSIGN_PLACEHOLDER_RE.sub(
        lambda match: match.group("left") + PLACEHOLDER, masked
    )
    masked = LET_ASSIGN_RE.sub(lambda match: match.group("left") + PLACEHOLDER, masked)
    masked = LETTER_EQ_EXPR_RE.sub(lambda match: match.group("left") + PLACEHOLDER, masked)
    return masked


def _mask_version2_extras(text: str) -> str:
    masked = NAMED_FIGURE_RE.sub(PLACEHOLDER, text)
    masked = _mask_assignments(masked)
    masked = LEFTOVER_COEFFICIENT_RE.sub(PLACEHOLDER, masked)
    masked = re.sub(r"[ \t]{2,}", " ", masked)
    return masked


def mask_stem(stem: str, version: int = 1) -> dict[str, Any]:
    """Hide given quantities in a stem. Options are not passed through here."""
    if version not in (1, 2):
        raise RuntimeError(f"unsupported mask version: {version}")
    original = stem
    masked = _mask_pass(original)
    flags = leak_flags(masked)
    second_sweep = False
    if flags:
        second_sweep = True
        masked = _mask_pass(masked)
        masked = re.sub(r"\d", PLACEHOLDER, masked)
        masked = VULGAR_FRACTION_RE.sub(PLACEHOLDER, masked)
        masked = SUPER_SUB_DIGIT_RE.sub(PLACEHOLDER, masked)
        masked = CARDINAL_RE.sub(PLACEHOLDER, masked)
        masked = SCALE_WORD_RE.sub(PLACEHOLDER, masked)
        masked = STANDALONE_FRACTION_WORD_RE.sub(PLACEHOLDER, masked)
        flags = leak_flags(masked)
    version2_applied = False
    if version == 2:
        version2_applied = True
        masked = _mask_version2_extras(masked)
        masked = _mask_pass(masked)
        flags = leak_flags(masked)
    dropped = bool(flags)
    return {
        "original": original,
        "masked": masked,
        "nPlaceholders": masked.count(PLACEHOLDER),
        "maskedTokenCount": masked.count(PLACEHOLDER),
        "leakFlags": flags,
        "secondSweep": second_sweep,
        "version2Applied": version2_applied,
        "maskVersion": version,
        "dropped": dropped,
        "dropReason": ",".join(flags) if dropped else None,
    }


def apply_option_permutation(
    items: list[dict[str, Any]],
    seed: int,
) -> list[dict[str, Any]]:
    """Shuffle option contents across the original letters. Resume-safe per item id."""
    import hashlib

    out: list[dict[str, Any]] = []
    for item in items:
        item = dict(item)
        choices = dict(item.get("choices") or {})
        letters = option_letters(choices)
        letter_to_text: dict[str, str] = {}
        for raw_key, text in choices.items():
            letter = str(raw_key).strip().upper()[:1]
            letter_to_text[letter] = str(text)
        texts = [letter_to_text[letter] for letter in letters]
        digest = hashlib.sha256(f"{seed}:{item['id']}".encode("utf-8")).hexdigest()
        rng = random.Random(int(digest[:16], 16))
        order = list(range(len(letters)))
        rng.shuffle(order)
        new_choices: dict[str, str] = {}
        old_to_new: dict[str, str] = {}
        for new_index, old_index in enumerate(order):
            new_letter = letters[new_index]
            old_letter = letters[old_index]
            new_choices[new_letter] = texts[old_index]
            old_to_new[old_letter] = new_letter
        original_key = str(item.get("key", "")).strip().upper()
        if original_key not in old_to_new:
            raise RuntimeError(f"permutation missing original key {original_key} for {item['id']}")
        item["choices"] = new_choices
        item["_original_key"] = original_key
        item["key"] = old_to_new[original_key]
        item["_option_permutation"] = {
            "seed": seed,
            "oldToNew": old_to_new,
            "originalKey": original_key,
            "scoredKey": item["key"],
            "order": order,
        }
        out.append(item)
    return out


def apply_masking(
    items: list[dict[str, Any]],
    version: int = 1,
    min_masked_token_count: int = 0,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    kept: list[dict[str, Any]] = []
    dropped: list[dict[str, Any]] = []
    below_min: list[dict[str, Any]] = []
    reports: list[dict[str, Any]] = []
    for item in items:
        report = mask_stem(str(item.get("stem") or ""), version=version)
        report["id"] = item["id"]
        report["cell"] = f"{item.get('authority')}::{item.get('claim')}"
        reports.append(report)
        if report["dropped"]:
            dropped.append(item)
            continue
        if int(report["nPlaceholders"]) < min_masked_token_count:
            below_min.append(item)
            continue
        item = dict(item)
        item["_masked_stem"] = report["masked"]
        item["_mask_report"] = report
        item["_mask_version"] = version
        kept.append(item)
    return kept, dropped, below_min, reports


def write_mask_audit(
    reports: list[dict[str, Any]],
    dropped: list[dict[str, Any]],
    path: Path,
    seed: int = EXPERIMENT_SEED,
    n_sample: int = AUDIT_N,
) -> dict[str, Any]:
    rng = random.Random(seed)
    pool = list(reports)
    sample = rng.sample(pool, min(n_sample, len(pool))) if pool else []
    payload = {
        "seed": seed,
        "nSampleRequested": n_sample,
        "nReports": len(reports),
        "nDropped": len(dropped),
        "droppedIds": [str(item["id"]) for item in dropped],
        "dropReasons": [
            {
                "id": rec["id"],
                "cell": rec.get("cell"),
                "dropReason": rec.get("dropReason"),
                "leakFlags": rec.get("leakFlags"),
            }
            for rec in reports
            if rec.get("dropped")
        ],
        "nSecondSweep": sum(1 for rec in reports if rec.get("secondSweep")),
        "sampleLeakCount": sum(1 for rec in sample if rec.get("leakFlags")),
        "items": [
            {
                "id": rec["id"],
                "cell": rec.get("cell"),
                "originalStem": rec.get("original"),
                "maskedStem": rec.get("masked"),
                "nPlaceholders": rec.get("nPlaceholders"),
                "secondSweep": rec.get("secondSweep"),
                "leakFlags": rec.get("leakFlags") or [],
                "dropped": rec.get("dropped"),
                "verdict": "leak" if rec.get("leakFlags") else "ok",
            }
            for rec in sample
        ],
    }
    dump_json(path, payload)
    return payload


def load_modal_by_cell(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        raise RuntimeError(f"position control file missing: {path}")
    blob = json.loads(path.read_text(encoding="utf-8"))
    cells = ((blob.get("perCellPositionBaseline") or {}).get("cells")) or []
    return {str(row["cell"]): row for row in cells}


def load_rows_by_id(path: Path) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    if not path.exists():
        return rows
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            rec = json.loads(line)
            rows[str(rec["id"])] = rec
    return rows


def paired_increment(
    masked_rows: list[dict[str, Any]],
    options_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    both_correct = 0
    both_wrong = 0
    masked_only = 0
    options_only = 0
    overlap = 0
    missing = 0
    for row in masked_rows:
        other = options_by_id.get(str(row["id"]))
        if other is None:
            missing += 1
            continue
        overlap += 1
        masked_ok = bool(row["correct"])
        options_ok = bool(other.get("correct"))
        if masked_ok and options_ok:
            both_correct += 1
        elif (not masked_ok) and (not options_ok):
            both_wrong += 1
        elif masked_ok and (not options_ok):
            masked_only += 1
        else:
            options_only += 1
    n01 = masked_only
    n10 = options_only
    mcnemar_stat = None
    if (n01 + n10) > 0:
        mcnemar_stat = ((n01 - n10) ** 2) / (n01 + n10)
    return {
        "nOverlap": overlap,
        "nMissingFromOptionsOnly": missing,
        "maskedCorrectOptionsWrong": n01,
        "optionsCorrectMaskedWrong": n10,
        "bothCorrect": both_correct,
        "bothWrong": both_wrong,
        "shareMaskedOnly": (n01 / overlap) if overlap else None,
        "shareOptionsOnly": (n10 / overlap) if overlap else None,
        "mcnemarN01": n01,
        "mcnemarN10": n10,
        "mcnemarChiSquareNoContinuity": mcnemar_stat,
        "note": (
            "n01 = masked-stem correct and options-only incorrect; "
            "n10 = options-only correct and masked-stem incorrect."
        ),
    }


def enrich_cells_with_modal(
    rows: list[dict[str, Any]],
    modal_by_cell: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("cell") or "unknown")].append(row)
    per_cell: dict[str, dict[str, Any]] = {}
    clears_both: list[dict[str, Any]] = []
    named: dict[str, dict[str, Any]] = {}
    for name, group in sorted(grouped.items()):
        stats = summarize_rows(group)
        modal = modal_by_cell.get(name) or {}
        modal_letter = modal.get("modalLetter")
        modal_frequency = modal.get("modalFrequency")
        lower = stats["ci95"][0]
        n = stats["n"]
        stats["modalLetter"] = modal_letter
        stats["modalFrequency"] = modal_frequency
        stats["modalCount"] = modal.get("modalCount")
        stats["lowerCiAboveChance"] = n >= 10 and lower > stats["chance"]
        stats["lowerCiAboveModalFrequency"] = (
            n >= 10 and modal_frequency is not None and lower > float(modal_frequency)
        )
        stats["clearsWitnessBarThisChannel"] = bool(
            stats["lowerCiAboveChance"] and stats["lowerCiAboveModalFrequency"]
        )
        non_modal = [
            row
            for row in group
            if modal_letter and str(row["key"]) != str(modal_letter)
        ]
        if non_modal:
            stats["nonModalKey"] = summarize_rows(non_modal)
        else:
            stats["nonModalKey"] = {"n": 0, "passRate": None, "ci95": None}
        if n >= 10:
            per_cell[name] = stats
            if stats["clearsWitnessBarThisChannel"]:
                clears_both.append({"cell": name, **stats})
        if name in NAMED_CELLS:
            named[name] = stats
    non_modal_all = []
    for row in rows:
        modal = modal_by_cell.get(str(row.get("cell") or ""))
        if modal and str(row["key"]) != str(modal.get("modalLetter")):
            non_modal_all.append(row)
    return {
        "perCell": per_cell,
        "cellsClearingChanceAndModal": clears_both,
        "namedCells": named,
        "nonModalKeyOverall": summarize_rows(non_modal_all) if non_modal_all else {"n": 0},
    }


def sha256_file(path: Path) -> str:
    import hashlib

    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return digest


def require_cuda() -> torch.device:
    if not torch.cuda.is_available():
        raise RuntimeError(
            "CUDA GPU is required for this experiment; torch cannot see a GPU."
        )
    if torch.cuda.device_count() < 1:
        raise RuntimeError("CUDA GPU is required; torch.cuda.device_count() is 0.")
    return torch.device("cuda")


def load_items() -> dict[str, dict[str, Any]]:
    by_id: dict[str, dict[str, Any]] = {}
    with ITEMS_PATH.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            item = json.loads(line)
            by_id[str(item["id"])] = item
    return by_id


def option_letters(choices: dict[str, Any]) -> list[str]:
    letters: list[str] = []
    for raw_key in choices.keys():
        letter = str(raw_key).strip().upper()[:1]
        if letter:
            letters.append(letter)
    return letters


def format_options_block(choices: dict[str, Any]) -> str:
    lines: list[str] = []
    for raw_key, text in choices.items():
        letter = str(raw_key).strip().upper()[:1]
        lines.append(f"{letter}) {text}")
    return "\n".join(lines)


def scorable_item(item: dict[str, Any]) -> bool:
    choices = item.get("choices") or {}
    if not choices:
        return False
    key = str(item.get("key", "")).strip().upper()
    letters = set(option_letters(choices))
    return bool(SINGLE_LETTER_RE.fullmatch(key) and key in letters)


def resolve_prompt_mode(with_stem: bool, prompt_mode: str | None) -> str:
    if prompt_mode:
        return prompt_mode
    return "with-stem" if with_stem else "choices-only"


def build_prompt(
    item: dict[str, Any],
    with_stem: bool,
    tokenizer_obj: Any,
    prompt_mode: str | None = None,
) -> str:
    options_block = format_options_block(item.get("choices") or {})
    mode = resolve_prompt_mode(with_stem, prompt_mode)
    if mode == "masked-stem":
        mask_version = int(item.get("_mask_version") or 1)
        stem = str(
            item.get("_masked_stem")
            or mask_stem(str(item.get("stem") or ""), version=mask_version)["masked"]
        )
        template = (
            MASKED_STEM_V2_USER_TEMPLATE if mask_version == 2 else MASKED_STEM_USER_TEMPLATE
        )
        user = template.format(stem=stem, options_block=options_block)
    elif mode == "with-stem":
        user = WITH_STEM_USER_TEMPLATE.format(
            stem=str(item.get("stem", "")),
            options_block=options_block,
        )
    else:
        user = CHOICES_ONLY_USER_TEMPLATE.format(options_block=options_block)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user},
    ]
    return tokenizer_obj.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
    )


def letter_variant_token_ids(tokenizer_obj: Any, letter: str) -> dict[str, int]:
    variants: dict[str, int] = {}
    for variant in (letter, f" {letter}"):
        token_ids = tokenizer_obj.encode(variant, add_special_tokens=False)
        if len(token_ids) == 1:
            variants[variant] = int(token_ids[0])
    if not variants:
        token_ids = tokenizer_obj.encode(letter, add_special_tokens=False)
        variants[letter] = int(token_ids[0])
    return variants


def summarize_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    n = len(rows)
    flags = [int(row["correct"]) for row in rows]
    rate = sum(flags) / n if n else 0.0
    chance = sum(1.0 / int(row["n_options"]) for row in rows) / n if n else 0.0
    ci = bootstrap_ci(flags, 1000, 21 + n) if n else (0.0, 0.0)
    return {
        "n": n,
        "passRate": rate,
        "ci95": [ci[0], ci[1]],
        "chance": chance,
        "meanOneOverK": chance,
        "ciExcludesChance": n >= 10 and ci[0] > chance,
        "witnessBarEligible": n >= 10 and ci[0] > chance,
    }


def group_rows(rows: list[dict[str, Any]], key_name: str) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get(key_name) or "unknown")].append(row)
    out: dict[str, dict[str, Any]] = {}
    for name, group in sorted(grouped.items()):
        if len(group) < 10:
            continue
        out[name] = summarize_rows(group)
    return out


def position_baseline(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {"letter": None, "rate": 0.0, "n": 0, "counts": {}}
    counts = Counter(str(row["key"]) for row in rows)
    letter, _count = counts.most_common(1)[0]
    flags = [int(str(row["key"]) == letter) for row in rows]
    rate = sum(flags) / len(flags)
    return {
        "letter": letter,
        "rate": rate,
        "n": len(rows),
        "counts": dict(counts),
        "note": "Always pick the most common key letter among scored items.",
    }


def dump_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


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


def load_existing_rows(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


@torch.inference_mode()
def score_prompts(
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
    logits = model(**encoded).logits
    attention = encoded["attention_mask"]
    last_index = attention.sum(dim=1) - 1
    row_index = torch.arange(logits.size(0), device=device)
    next_logits = logits[row_index, last_index]
    log_probs = torch.log_softmax(next_logits.float(), dim=-1)
    results: list[tuple[str, dict[str, float], dict[str, dict[str, float]]]] = []
    for batch_index, letters in enumerate(letters_per_item):
        letter_logprobs: dict[str, float] = {}
        variant_logprobs: dict[str, dict[str, float]] = {}
        for letter in letters:
            variants = letter_token_ids[letter]
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


def score_items(
    model: Any,
    tokenizer_obj: Any,
    device: torch.device,
    items: list[dict[str, Any]],
    with_stem: bool,
    out_path: Path,
    summary_hook: Any,
    batch_size: int = BATCH_SIZE,
    prompt_mode: str | None = None,
) -> list[dict[str, Any]]:
    mode = resolve_prompt_mode(with_stem, prompt_mode)
    done_ids = already_scored_ids(out_path)
    scored_rows = load_existing_rows(out_path)
    pending = [item for item in items if str(item["id"]) not in done_ids]
    print(
        f"scoring prompt_mode={mode} pending={len(pending)} already={len(done_ids)}",
        flush=True,
    )
    for start in range(0, len(pending), batch_size):
        batch_items = pending[start : start + batch_size]
        prompts = [
            build_prompt(
                item,
                with_stem=with_stem,
                tokenizer_obj=tokenizer_obj,
                prompt_mode=mode,
            )
            for item in batch_items
        ]
        letters_per_item = [option_letters(item.get("choices") or {}) for item in batch_items]
        scored = score_prompts(model, tokenizer_obj, device, prompts, letters_per_item)
        new_rows: list[dict[str, Any]] = []
        for item, (chosen, letter_logprobs, variant_logprobs) in zip(batch_items, scored):
            key = str(item["key"]).strip().upper()
            choices = item.get("choices") or {}
            n_options = len(choices)
            correct = chosen == key
            row = {
                "id": item["id"],
                "n_options": n_options,
                "chosen_letter": chosen,
                "key": key,
                "correct": bool(correct),
                "logprobs": letter_logprobs,
                "logprobs_variants": variant_logprobs,
                "corpus": item.get("corpus"),
                "authority": item.get("authority"),
                "claim": item.get("claim"),
                "cell": f"{item.get('authority')}::{item.get('claim')}",
                "with_stem": with_stem or mode == "masked-stem",
                "prompt_mode": mode,
            }
            if mode == "masked-stem":
                report = item.get("_mask_report") or {}
                row["masked_stem"] = item.get("_masked_stem") or report.get("masked")
                row["n_placeholders"] = report.get("nPlaceholders")
                row["masked_token_count"] = report.get(
                    "maskedTokenCount", report.get("nPlaceholders")
                )
                row["mask_version"] = int(item.get("_mask_version") or 1)
                permutation = item.get("_option_permutation")
                if permutation:
                    row["option_permutation"] = permutation
                    row["original_key"] = item.get("_original_key")
            new_rows.append(row)
            scored_rows.append(row)
        append_jsonl(out_path, new_rows)
        summary_hook(scored_rows, with_stem=with_stem)
        done = len(scored_rows)
        rate = sum(int(row["correct"]) for row in scored_rows) / done if done else 0.0
        print(
            f"  prompt_mode={mode} {done}/{len(items)} rate={rate:.4f}",
            flush=True,
        )
    return scored_rows


def load_subagent_agreement(scored_rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not SCORED_SUBAGENT_PATH.exists():
        return {"available": False, "reason": "exports/choices-only/scored.jsonl missing"}
    sub_by_id: dict[str, dict[str, Any]] = {}
    with SCORED_SUBAGENT_PATH.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            rec = json.loads(line)
            sub_by_id[str(rec["itemId"])] = rec
    maps_by_id: dict[str, dict[str, Any]] = {}
    if BATCH_MAP_DIR.exists():
        for map_file in sorted(BATCH_MAP_DIR.glob("batch-*.map.json")):
            blob = json.loads(map_file.read_text(encoding="utf-8"))
            for rec in blob:
                maps_by_id[str(rec["itemId"])] = rec
    overlap_rows: list[dict[str, Any]] = []
    letter_agree = 0
    letter_compared = 0
    correctness_agree = 0
    both_correct = 0
    for row in scored_rows:
        sub = sub_by_id.get(str(row["id"]))
        if sub is None:
            continue
        local_correct = bool(row["correct"])
        sub_correct = bool(sub.get("correct"))
        correctness_agree += int(local_correct == sub_correct)
        both_correct += int(local_correct and sub_correct)
        original_letter = None
        rec_map = maps_by_id.get(str(row["id"]))
        if rec_map is not None:
            old_to_new = rec_map.get("letterMapOldToNew") or {}
            predicted_shuffled = str(sub.get("predicted", "")).strip().upper()[:1]
            for original, shuffled in old_to_new.items():
                if str(shuffled).strip().upper()[:1] == predicted_shuffled:
                    original_letter = str(original).strip().upper()[:1]
                    break
            if original_letter is not None:
                letter_compared += 1
                letter_agree += int(original_letter == str(row["chosen_letter"]))
        overlap_rows.append(
            {
                "id": row["id"],
                "local_correct": local_correct,
                "subagent_correct": sub_correct,
                "local_letter": row["chosen_letter"],
                "subagent_original_letter": original_letter,
            }
        )
    n = len(overlap_rows)
    return {
        "available": True,
        "nSubagentScoredOnDisk": len(sub_by_id),
        "nOverlap": n,
        "note": (
            "User brief mentioned 488 previously scored items; disk now has "
            f"{len(sub_by_id)} per-item subagent rows in scored.jsonl. "
            "Agreement uses that full on-disk set. Subagent letters were shuffled; "
            "letter agreement maps them back to original option letters."
        ),
        "agreementOnCorrectness": (correctness_agree / n) if n else None,
        "agreementOnOriginalLetter": (letter_agree / letter_compared) if letter_compared else None,
        "nLetterCompared": letter_compared,
        "bothCorrectRate": (both_correct / n) if n else None,
        "localRateOnOverlap": (sum(int(r["local_correct"]) for r in overlap_rows) / n) if n else None,
        "subagentRateOnOverlap": (
            sum(int(r["subagent_correct"]) for r in overlap_rows) / n if n else None
        ),
    }


def write_readme(payload: dict[str, Any]) -> None:
    overall = payload.get("overall") or {}
    sanity = payload.get("withStemSanity") or {}
    cells = payload.get("cellsLowerCiAboveChance") or []
    cell_lines = (
        "\n".join(
            f"- `{row['cell']}` n={row['n']} rate={row['passRate']:.3f} "
            f"CI [{row['ci95'][0]:.3f}, {row['ci95'][1]:.3f}] chance={row['chance']:.3f}"
            for row in cells
        )
        or "- none"
    )
    agreement = payload.get("subagentAgreement") or {}
    status = payload.get("status", "unknown")
    text = f"""# Choices-only local LM (exploratory)

## Question

On selected-response items whose option strings pass the sibling mechanical clean-option filter, does a local instruction-tuned language model beat chance (mean of 1/k) from the option list alone, with the stem withheld?

## Method

- Model: `{payload.get('modelId')}` revision `{payload.get('modelRevision')}`.
- Filter: sibling `exports/addendum/choices-only-clean-filter.json` used verbatim (`used_verbatim: true`).
- Prompt: options only, original order with letters, no stem, no source or exam name. Exact templates are in `choices-only-local-lm.json` under `promptTemplate`.
- Score: next-token log-probabilities over option letters after the chat template; greedy argmax over those letters (max of the bare letter token and the space-prefixed letter token).
- Chance: mean of 1/k per item. Bootstrap: `random.Random.randrange`, 1000 replicates, 95% percentile CI, seed `21 + n`, matching `scripts/score_choices_only.py`.
- Position control: always pick the most common key letter among scored items.
- With-stem sanity: same model, 200 clean items, stem included.
- Label: exploratory. The paper's witness bar applies per cell: n >= 10 and lower CI above chance. This run does not change the frozen paper.

Status: **{status}**.

## Numbers

- Clean keep-list size: {payload.get('nCleanKeepList')}
- n scored (choices-only): {overall.get('n')}
- overall rate: {overall.get('passRate')}
- chance (mean 1/k): {overall.get('chance')}
- 95% CI: {overall.get('ci95')}
- lower CI above chance: {overall.get('ciExcludesChance')}
- position baseline: letter {payload.get('positionBaseline', {}).get('letter')} rate {payload.get('positionBaseline', {}).get('rate')}
- with-stem sanity n={sanity.get('n')} rate={sanity.get('passRate')} CI {sanity.get('ci95')}
- subagent overlap n={agreement.get('nOverlap')} correctness agreement={agreement.get('agreementOnCorrectness')} original-letter agreement={agreement.get('agreementOnOriginalLetter')}

### Cells with lower CI above chance

{cell_lines}

## What a writer should cite

From `exports/addendum-gpu/choices-only-local-lm.json`:

- `modelId`, `modelRevision`
- `filter.used_verbatim`, `filter.filter_source`
- `overall.n`, `overall.passRate`, `overall.chance`, `overall.ci95`, `overall.witnessBarEligible`
- `positionBaseline.letter`, `positionBaseline.rate`
- `perSource`, `perCell` (only n >= 10)
- `cellsLowerCiAboveChance`
- `withStemSanity.passRate`
- `subagentAgreement`
- `promptTemplate`
- `versions`, `wallTimeSeconds`

Per-item rows: `exports/addendum-gpu/choices-only-local-lm-items.jsonl` fields `id`, `n_options`, `chosen_letter`, `key`, `correct`, `logprobs`.

This is exploratory. Dirty option strings were the reason the subagent choices-only channel was not claimed; this run uses the sibling clean filter and a local LM. It still does not authorize a paper claim unless a cell clears the witness bar and the authors decide to add it after the freeze.
"""
    follow_up_marker = "## Position baseline and memorization"
    existing = README_PATH.read_text(encoding="utf-8") if README_PATH.exists() else ""
    follow_up = ""
    if follow_up_marker in existing:
        follow_up = existing[existing.index(follow_up_marker) :].rstrip() + "\n"
    README_PATH.write_text(
        (text.rstrip() + "\n\n" + follow_up) if follow_up else text,
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Choices-only next-token scoring on GPU.")
    parser.add_argument("--model-id", default=MODEL_ID)
    parser.add_argument("--model-revision", default=None)
    parser.add_argument(
        "--summary-path",
        default=str(SUMMARY_PATH),
        help="JSON summary output path relative to the experiment root or absolute.",
    )
    parser.add_argument(
        "--items-out",
        default=str(ITEMS_OUT_PATH),
        help="Per-item JSONL output path.",
    )
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE)
    parser.add_argument(
        "--device-map",
        default="to",
        choices=["to", "cuda"],
        help='Use transformers device_map="cuda" or model.to(cuda).',
    )
    parser.add_argument("--skip-with-stem", action="store_true")
    parser.add_argument("--no-readme", action="store_true")
    parser.add_argument(
        "--prompt-mode",
        default="choices-only",
        choices=["choices-only", "masked-stem", "with-stem"],
        help="Prompt channel. masked-stem hides quantities in the stem and keeps options.",
    )
    parser.add_argument(
        "--mask-version",
        type=int,
        default=1,
        choices=[1, 2],
        help="Stem masking version. 2 adds named figures, bindings, leftover coefficients.",
    )
    parser.add_argument(
        "--min-masked-token-count",
        type=int,
        default=0,
        help="Keep items with at least this many [N] placeholders after masking.",
    )
    parser.add_argument(
        "--permute-options-seed",
        type=int,
        default=None,
        help="If set, randomly permute option contents across letters with this seed.",
    )
    parser.add_argument(
        "--preregistration",
        default=None,
        help="Preregistration markdown path. Defaults to the version-1 or version-2 file.",
    )
    parser.add_argument(
        "--options-only-items",
        default=None,
        help="Existing options-only item JSONL for paired increment (masked-stem mode).",
    )
    parser.add_argument(
        "--position-json",
        default=str(POSITION_JSON_PATH),
        help="Per-cell modal-letter frequencies from the position-and-memorization run.",
    )
    parser.add_argument(
        "--audit-out",
        default=str(OUT_DIR / "masked-stem-audit-sample.json"),
        help="40-item masking audit JSON (written before scoring in masked-stem mode).",
    )
    parser.add_argument(
        "--allow-download",
        action="store_true",
        help="Do not force HF offline; download weights if the snapshot is missing.",
    )
    parser.add_argument(
        "--item-ids-file",
        default=None,
        help="JSON list of item ids to score (after the clean keep list and scorable-key filter).",
    )
    parser.add_argument(
        "--restrict-cells",
        default=None,
        help="Comma-separated authority::claim cells to keep (applied after --item-ids-file).",
    )
    return parser.parse_args()


def resolve_path(raw: str) -> Path:
    path = Path(raw)
    if path.is_absolute():
        return path
    return ROOT / path


def snapshot_dir_for(model_id: str, revision: str | None) -> Path:
    cache_name = "models--" + model_id.replace("/", "--")
    snapshots = Path.home() / ".cache" / "huggingface" / "hub" / cache_name / "snapshots"
    if revision:
        return snapshots / revision
    if not snapshots.exists():
        return snapshots / "missing"
    children = [path for path in snapshots.iterdir() if path.is_dir()]
    if not children:
        return snapshots / "missing"
    children.sort(key=lambda path: path.stat().st_mtime, reverse=True)
    return children[0]


def main() -> None:
    args = parse_args()
    os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
    if not args.allow_download:
        os.environ.setdefault("HF_HUB_OFFLINE", "1")
        os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
    started = time.time()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    summary_path = resolve_path(args.summary_path)
    items_out_path = resolve_path(args.items_out)
    batch_size = int(args.batch_size)
    if batch_size < 1:
        raise RuntimeError(f"batch size must be >= 1, got {batch_size}")

    device = require_cuda()
    gpu_name = torch.cuda.get_device_name(0)
    print(f"GPU {gpu_name} device={device}", flush=True)

    if not SIBLING_FILTER_PATH.exists() or not SIBLING_KEEP_IDS_PATH.exists():
        raise RuntimeError(
            "Sibling clean filter was expected at "
            f"{SIBLING_FILTER_PATH} and {SIBLING_KEEP_IDS_PATH}"
        )
    sibling_filter = json.loads(SIBLING_FILTER_PATH.read_text(encoding="utf-8"))
    keep_ids = [
        str(item_id)
        for item_id in json.loads(SIBLING_KEEP_IDS_PATH.read_text(encoding="utf-8"))
    ]
    prompt_mode = str(args.prompt_mode)
    if prompt_mode != "masked-stem" and not FILTER_COPY_PATH.exists():
        dump_json(
            FILTER_COPY_PATH,
            {
                "filter_source": "exports/addendum/choices-only-clean-filter.json",
                "used_verbatim": True,
                "kept_ids_source": "exports/addendum/choices-only-clean-item-ids.json",
                "rules": sibling_filter.get("rules"),
                "nSelected": sibling_filter.get("nSelected"),
                "nKeptBySiblingFilter": sibling_filter.get("nKept"),
                "nDroppedBySiblingFilter": sibling_filter.get("nDropped"),
                "reasonCounts": sibling_filter.get("reasonCounts"),
                "byCorpus": sibling_filter.get("byCorpus"),
                "note": (
                    "Sibling E3 mechanical filter existed on disk. Rules and keep list "
                    "used verbatim. Items that cannot be scored as a single letter "
                    "versus key are skipped at score time, not by changing the filter."
                ),
            },
        )

    items_by_id = load_items()
    clean_items = [items_by_id[item_id] for item_id in keep_ids if item_id in items_by_id]
    skipped = [item for item in clean_items if not scorable_item(item)]
    to_score = [item for item in clean_items if scorable_item(item)]
    print(
        f"keep={len(keep_ids)} found={len(clean_items)} scorable={len(to_score)} skipped={len(skipped)}",
        flush=True,
    )
    item_ids_file = str(args.item_ids_file) if args.item_ids_file else None
    restrict_cells_arg = str(args.restrict_cells) if args.restrict_cells else None
    if item_ids_file:
        id_path = resolve_path(item_ids_file)
        requested_ids = [str(item_id) for item_id in json.loads(id_path.read_text(encoding="utf-8"))]
        allowed_ids = set(requested_ids)
        to_score = [item for item in to_score if str(item["id"]) in allowed_ids]
        print(
            f"item-ids-file={id_path} requested={len(requested_ids)} kept={len(to_score)}",
            flush=True,
        )
    if restrict_cells_arg:
        restrict_cells = {
            part.strip() for part in restrict_cells_arg.split(",") if part.strip()
        }
        to_score = [
            item
            for item in to_score
            if f"{item.get('authority')}::{item.get('claim')}" in restrict_cells
        ]
        print(
            f"restrict-cells={sorted(restrict_cells)} kept={len(to_score)}",
            flush=True,
        )
    if not to_score:
        raise RuntimeError("no items left to score after keep-list, id, and cell filters")
    dropped_mask: list[dict[str, Any]] = []
    below_min_mask: list[dict[str, Any]] = []
    mask_reports: list[dict[str, Any]] = []
    audit_payload: dict[str, Any] | None = None
    mask_version = int(args.mask_version)
    min_masked_token_count = int(args.min_masked_token_count)
    permute_seed = args.permute_options_seed
    if args.preregistration:
        prereg_path = resolve_path(str(args.preregistration))
    elif mask_version == 2:
        prereg_path = PREREG_V2_PATH
    else:
        prereg_path = PREREG_PATH
    if prompt_mode == "masked-stem":
        if not prereg_path.exists():
            raise RuntimeError(f"Preregistration must exist before scoring: {prereg_path}")
        to_score, dropped_mask, below_min_mask, mask_reports = apply_masking(
            to_score,
            version=mask_version,
            min_masked_token_count=min_masked_token_count,
        )
        if permute_seed is not None:
            to_score = apply_option_permutation(to_score, int(permute_seed))
        audit_path = resolve_path(str(args.audit_out))
        audit_payload = write_mask_audit(mask_reports, dropped_mask, audit_path)
        print(
            f"masked-stem version={mask_version} kept={len(to_score)} "
            f"dropped={len(dropped_mask)} below_min={len(below_min_mask)} "
            f"permute={permute_seed} audit={audit_path} "
            f"sample_leaks={audit_payload.get('sampleLeakCount')}",
            flush=True,
        )
        dump_json(
            summary_path,
            {
                "status": "masking_complete",
                "label": "exploratory",
                "promptMode": prompt_mode,
                "maskVersion": mask_version,
                "minMaskedTokenCount": min_masked_token_count,
                "permuteOptionsSeed": permute_seed,
                "preregistration": str(prereg_path.relative_to(ROOT))
                if prereg_path.is_relative_to(ROOT)
                else str(prereg_path),
                "preregistrationSha256": sha256_file(prereg_path),
                "nCleanKeepList": len(keep_ids),
                "nScorableBeforeMask": len(to_score) + len(dropped_mask) + len(below_min_mask),
                "nDroppedUnmaskable": len(dropped_mask),
                "nBelowMinMaskedTokenCount": len(below_min_mask),
                "droppedUnmaskableIds": [item["id"] for item in dropped_mask],
                "belowMinMaskedTokenCountIds": [item["id"] for item in below_min_mask],
                "auditPath": str(audit_path.relative_to(ROOT))
                if audit_path.is_relative_to(ROOT)
                else str(audit_path),
                "masking": {
                    "nReports": len(mask_reports),
                    "nSecondSweep": audit_payload.get("nSecondSweep"),
                    "nDropped": len(dropped_mask),
                    "nBelowMin": len(below_min_mask),
                    "placeholder": PLACEHOLDER,
                    "maskVersion": mask_version,
                },
            },
        )

    model_id = str(args.model_id)
    model_revision = args.model_revision
    local_files_only = not args.allow_download
    if model_id == MODEL_ID and model_revision is None:
        model_revision = MODEL_REVISION
        load_source: str | Path = SNAPSHOT_PATH
        if not SNAPSHOT_PATH.exists():
            raise RuntimeError(f"Local model snapshot missing: {SNAPSHOT_PATH}")
    elif local_files_only:
        snapshot_path = snapshot_dir_for(model_id, model_revision)
        if not snapshot_path.exists():
            raise RuntimeError(f"Local model snapshot missing: {snapshot_path}")
        load_source = snapshot_path
        model_revision = snapshot_path.name
    else:
        load_source = model_id

    global tokenizer, letter_token_ids, model
    tokenizer = AutoTokenizer.from_pretrained(
        str(load_source),
        local_files_only=local_files_only,
        revision=model_revision if isinstance(load_source, str) else None,
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"
    letter_token_ids = {
        letter: letter_variant_token_ids(tokenizer, letter) for letter in list("ABCDE")
    }

    torch.manual_seed(EXPERIMENT_SEED)
    torch.cuda.manual_seed_all(EXPERIMENT_SEED)
    load_started = time.time()
    pretrained_kwargs: dict[str, Any] = {
        "torch_dtype": torch.bfloat16,
        "local_files_only": local_files_only,
        "attn_implementation": "sdpa",
    }
    if isinstance(load_source, str) and model_revision:
        pretrained_kwargs["revision"] = model_revision
    if args.device_map == "cuda":
        pretrained_kwargs["device_map"] = "cuda"
        model = AutoModelForCausalLM.from_pretrained(str(load_source), **pretrained_kwargs)
    else:
        model = AutoModelForCausalLM.from_pretrained(str(load_source), **pretrained_kwargs)
        model.to(device)
    model.eval()
    load_seconds = time.time() - load_started
    resolved_snapshot = snapshot_dir_for(
        model_id,
        model_revision or getattr(model, "name_or_path", None),
    )
    if model_revision is None:
        model_revision = resolved_snapshot.name if resolved_snapshot.exists() else None
        if model_revision is None:
            commit_hash = getattr(getattr(model, "config", None), "_commit_hash", None)
            model_revision = str(commit_hash) if commit_hash else None
    print(
        f"model loaded in {load_seconds:.1f}s on {gpu_name} "
        f"id={model_id} rev={model_revision} device_map={args.device_map}",
        flush=True,
    )

    payload: dict[str, Any] = {
        "status": "in_progress",
        "label": "exploratory",
        "modelId": model_id,
        "modelRevision": model_revision,
        "snapshotPath": str(resolved_snapshot if resolved_snapshot.exists() else load_source),
        "promptTemplate": {
            "system": SYSTEM_PROMPT,
            "choicesOnlyUser": CHOICES_ONLY_USER_TEMPLATE,
            "withStemUser": WITH_STEM_USER_TEMPLATE,
            "maskedStemUser": MASKED_STEM_USER_TEMPLATE,
            "maskedStemUserV2": MASKED_STEM_V2_USER_TEMPLATE,
            "scoring": (
                "Apply the chat template with add_generation_prompt=True. "
                "Take next-token log-softmax. For each option letter, take the max "
                "log-probability of the bare letter token and the leading-space letter "
                "token. Greedy argmax over those letters. Ties keep the earlier option."
            ),
        },
        "promptMode": prompt_mode,
        "maskVersion": mask_version,
        "minMaskedTokenCount": min_masked_token_count,
        "permuteOptionsSeed": permute_seed,
        "filter": json.loads(FILTER_COPY_PATH.read_text(encoding="utf-8")),
        "nCleanKeepList": len(keep_ids),
        "nScorable": len(to_score),
        "nSkippedUnscorableKey": len(skipped),
        "skippedUnscorableIds": [item["id"] for item in skipped],
        "nDroppedUnmaskable": len(dropped_mask),
        "droppedUnmaskableIds": [item["id"] for item in dropped_mask],
        "nBelowMinMaskedTokenCount": len(below_min_mask),
        "belowMinMaskedTokenCountIds": [item["id"] for item in below_min_mask],
        "itemIdsFile": item_ids_file,
        "restrictCells": restrict_cells_arg,
        "seed": EXPERIMENT_SEED,
        "batchSize": batch_size,
        "deviceMap": args.device_map,
        "versions": {
            "torch": torch.__version__,
            "transformers": __import__("transformers").__version__,
            "python": sys.version.split()[0],
            "gpuName": gpu_name,
            "cuda": torch.version.cuda,
            "dtype": "bfloat16",
            "attnImplementation": "sdpa",
            "env": "repository .venv",
        },
        "modelLoadSeconds": load_seconds,
        "preregistration": (
            str(prereg_path.relative_to(ROOT))
            if prereg_path.is_relative_to(ROOT)
            else str(prereg_path)
        )
        if prereg_path.exists()
        else None,
        "preregistrationSha256": sha256_file(prereg_path) if prereg_path.exists() else None,
    }
    if audit_payload is not None:
        payload["masking"] = {
            "nReports": len(mask_reports),
            "nSecondSweep": audit_payload.get("nSecondSweep"),
            "nDropped": len(dropped_mask),
            "nBelowMin": len(below_min_mask),
            "placeholder": PLACEHOLDER,
            "maskVersion": mask_version,
            "auditPath": str(resolve_path(str(args.audit_out)).relative_to(ROOT)),
            "auditSampleLeakCount": audit_payload.get("sampleLeakCount"),
        }
    dump_json(summary_path, payload)

    def maybe_readme(current: dict[str, Any]) -> None:
        if not args.no_readme:
            write_readme(current)

    def summary_hook(rows: list[dict[str, Any]], with_stem: bool) -> None:
        if with_stem:
            payload["withStemSanityPartial"] = summarize_rows(rows)
        else:
            payload["status"] = "in_progress"
            payload["overall"] = summarize_rows(rows)
            payload["perSource"] = group_rows(rows, "corpus")
            payload["perCell"] = group_rows(rows, "cell")
            payload["positionBaseline"] = position_baseline(rows)
            payload["nScoredSoFar"] = len(rows)
            payload["wallTimeSecondsSoFar"] = time.time() - started
            cells_clear = []
            for cell_name, stats in payload["perCell"].items():
                if stats.get("witnessBarEligible"):
                    cells_clear.append({"cell": cell_name, **stats})
            payload["cellsLowerCiAboveChance"] = cells_clear
        dump_json(summary_path, payload)
        maybe_readme(payload)

    choices_rows = score_items(
        model,
        tokenizer,
        device,
        to_score,
        with_stem=(prompt_mode == "with-stem"),
        out_path=items_out_path,
        summary_hook=summary_hook,
        batch_size=batch_size,
        prompt_mode=prompt_mode,
    )

    skip_with_stem = bool(args.skip_with_stem or prompt_mode != "choices-only")
    if skip_with_stem:
        if prompt_mode == "masked-stem":
            skip_reason = "masked-stem protocol; with-stem sanity not requested"
        elif prompt_mode == "with-stem":
            skip_reason = "with-stem is the scored channel; no separate 200-item sanity sample"
        else:
            skip_reason = "options-only protocol rerun; with-stem sanity not requested"
        payload["withStemSanity"] = {
            "skipped": True,
            "reason": skip_reason,
        }
    else:
        rng = random.Random(EXPERIMENT_SEED)
        with_stem_pool = [item for item in to_score if str(item.get("stem", "")).strip()]
        if len(with_stem_pool) < WITH_STEM_N:
            with_stem_sample = list(with_stem_pool)
        else:
            with_stem_sample = rng.sample(with_stem_pool, WITH_STEM_N)
        payload["withStemSampleIds"] = [item["id"] for item in with_stem_sample]
        dump_json(summary_path, payload)
        stem_rows = score_items(
            model,
            tokenizer,
            device,
            with_stem_sample,
            with_stem=True,
            out_path=STEM_ITEMS_OUT_PATH,
            summary_hook=summary_hook,
            batch_size=batch_size,
        )
        payload["withStemSanity"] = summarize_rows(stem_rows)
        payload["withStemSanity"]["nRequested"] = WITH_STEM_N
        payload["withStemSanity"]["sampleSeed"] = EXPERIMENT_SEED

    payload["status"] = "complete"
    payload["overall"] = summarize_rows(choices_rows)
    payload["perSource"] = group_rows(choices_rows, "corpus")
    payload["perCell"] = group_rows(choices_rows, "cell")
    payload["positionBaseline"] = position_baseline(choices_rows)
    cells_clear = []
    for cell_name, stats in payload["perCell"].items():
        if stats.get("witnessBarEligible"):
            cells_clear.append({"cell": cell_name, **stats})
    payload["cellsLowerCiAboveChance"] = cells_clear
    if prompt_mode == "masked-stem":
        position_path = resolve_path(str(args.position_json))
        modal_by_cell = load_modal_by_cell(position_path)
        enriched = enrich_cells_with_modal(choices_rows, modal_by_cell)
        payload["perCell"] = enriched["perCell"]
        payload["namedCells"] = enriched["namedCells"]
        payload["cellsClearingChanceAndModal"] = enriched["cellsClearingChanceAndModal"]
        payload["nonModalKeyOverall"] = enriched["nonModalKeyOverall"]
        payload["witnessCells"] = {
            name: enriched["namedCells"].get(name) or {"n": 0, "missing": True}
            for name in WITNESS_CELLS
        }
        payload["timssCells"] = {
            name: enriched["namedCells"].get(name) or {"n": 0, "missing": True}
            for name in ("timss::knowing", "timss::applying", "timss::reasoning")
        }
        if args.options_only_items:
            options_path = resolve_path(str(args.options_only_items))
        elif "14B" in model_id:
            options_path = OPTIONS_ONLY_14B_ITEMS
        else:
            options_path = OPTIONS_ONLY_7B_ITEMS
        payload["optionsOnlyItems"] = str(options_path.relative_to(ROOT)) if options_path.is_relative_to(ROOT) else str(options_path)
        payload["vsOptionsOnly"] = paired_increment(
            choices_rows,
            load_rows_by_id(options_path),
        )
        overall = payload["overall"]
        always_b = position_baseline(choices_rows)
        payload["vsAlwaysB"] = {
            "statedBaseline": ALWAYS_B_BASELINE,
            "passRate": overall.get("passRate"),
            "ci95": overall.get("ci95"),
            "lowerCiAboveAlwaysB": (
                int(overall.get("n") or 0) >= 10
                and float(overall["ci95"][0]) > ALWAYS_B_BASELINE
            ),
            "recomputedAlwaysB": always_b,
        }
        payload["vsChance"] = {
            "chance": overall.get("chance"),
            "lowerCiAboveChance": overall.get("ciExcludesChance"),
        }
        payload["positionJson"] = str(position_path.relative_to(ROOT))
    else:
        payload["subagentAgreement"] = load_subagent_agreement(choices_rows)
    payload["chosenLetterCounts"] = dict(
        Counter(str(row["chosen_letter"]) for row in choices_rows)
    )
    payload["keyLetterCounts"] = dict(Counter(str(row["key"]) for row in choices_rows))
    payload["wallTimeSeconds"] = time.time() - started
    payload["scoringSeconds"] = payload["wallTimeSeconds"] - load_seconds
    dump_json(summary_path, payload)
    maybe_readme(payload)
    print(json.dumps(
        {
            "status": payload["status"],
            "overall": payload["overall"],
            "positionBaseline": payload["positionBaseline"],
            "withStemSanity": payload["withStemSanity"],
            "nCellsClearingBar": len(cells_clear),
            "wallTimeSeconds": payload["wallTimeSeconds"],
            "modelId": model_id,
            "modelRevision": model_revision,
        },
        indent=2,
    ))


tokenizer: Any
letter_token_ids: dict[str, dict[str, int]]
model: Any


if __name__ == "__main__":
    main()
