#!/usr/bin/env python3
"""Cue attribution and talk examples for 14B masked-stem on Algebra I primary items."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = Path(__file__).resolve().parent
import sys

sys.path.insert(0, str(SCRIPTS))

from masked_stem_followup_lib import (  # noqa: E402
    dump_json,
    load_jsonl,
    modal_letter,
    summarize_rows,
)
from score_choices_only_local_lm import load_items, mask_stem  # noqa: E402
from strategy_channels import apply_s1, lower_central_key, parse_option_number  # noqa: E402

OUT_DIR = ROOT / "exports" / "addendum-gpu"
ITEMS_14B = OUT_DIR / "masked-stem-14b-items.jsonl"
STATS_PATH = OUT_DIR / "masked-stem-item-mask-stats.jsonl"
CUE_PATH = OUT_DIR / "masked-stem-cue-attribution.json"
EXAMPLES_PATH = OUT_DIR / "masked-stem-examples.json"
ALGEBRA_I_CELL = "nyregents::algebra-i"
ORDERED_PAIR_RE = re.compile(
    r"^\s*\(\s*[-−]?(?:[A-Za-z]|\$?\d+(?:\.\d+)?|\d+\s*/\s*\d+)"
    r"(?:\s*,\s*[-−]?(?:[A-Za-z]|\$?\d+(?:\.\d+)?|\d+\s*/\s*\d+))+\s*\)\s*$"
)
PURE_NUMERIC_RE = re.compile(
    r"^\s*[-−]?(?:\$\s*)?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?"
    r"(?:\s*/\s*[-−]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?)?"
    r"(?:\s*%)?\s*(?:cm|mm|m|km|in|ft|yd|kg|g|mg|ml|l|lb|"
    r"hours?|minutes?|seconds?|degrees?|units?|students?|people)?"
    r"\s*$",
    re.I,
)
PURE_FRACTION_RE = re.compile(r"^\s*[-−]?\d+\s*/\s*[-−]?\d+\s*$")
ALGEBRA_EQ_RE = re.compile(r"[A-Za-z]\s*=")
ALGEBRA_TERM_RE = re.compile(
    r"(?:\d\s*[A-Za-z]\b)|(?:\b[A-Za-z]\s*[+\-−*/^])|(?:[+\-−*/^]\s*[A-Za-z]\b)"
)


def load_primary_ids() -> set[str]:
    ids: set[str] = set()
    with STATS_PATH.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if int(row["masked_token_count"]) >= 1:
                ids.add(str(row["id"]))
    return ids


def unique_longest_letter(choices: dict[str, Any]) -> str | None:
    lengths: list[tuple[str, int]] = []
    for raw_key, text in choices.items():
        letter = str(raw_key).strip().upper()[:1]
        lengths.append((letter, len(str(text))))
    if not lengths:
        return None
    max_length = max(length for _letter, length in lengths)
    winners = [letter for letter, length in lengths if length == max_length]
    if len(winners) != 1:
        return None
    return winners[0]


def numeric_pairs(item: dict[str, Any]) -> list[tuple[str, float]]:
    pairs: list[tuple[str, float]] = []
    for raw_key, text in (item.get("choices") or {}).items():
        letter = str(raw_key).strip().upper()[:1]
        value = parse_option_number(str(text))
        if value is not None:
            pairs.append((letter, value))
    return pairs


def classify_option_text(text: str) -> str:
    cleaned = str(text).strip().replace("\u2212", "-")
    if ORDERED_PAIR_RE.match(cleaned):
        return "ordered_pair"
    if PURE_FRACTION_RE.match(cleaned) or PURE_NUMERIC_RE.match(cleaned):
        return "numeric"
    if ALGEBRA_EQ_RE.search(cleaned) or ALGEBRA_TERM_RE.search(cleaned):
        return "algebraic_expression"
    if parse_option_number(cleaned) is not None and not re.search(r"[A-Za-z]", cleaned):
        return "numeric"
    return "text"


def classify_item_option_type(item: dict[str, Any]) -> str:
    types = [classify_option_text(str(text)) for text in (item.get("choices") or {}).values()]
    if not types:
        return "text"
    unique = set(types)
    if len(unique) == 1:
        return types[0]
    counts: dict[str, int] = {}
    for option_type in types:
        counts[option_type] = counts.get(option_type, 0) + 1
    top = max(counts.values())
    leaders = [name for name, count in counts.items() if count == top]
    if len(leaders) == 1 and top >= (len(types) / 2.0):
        return leaders[0]
    return "mixed"


def logprob_margin(row: dict[str, Any]) -> float:
    logprobs = row.get("logprobs") or {}
    if not logprobs:
        return float("-inf")
    values = sorted((float(value) for value in logprobs.values()), reverse=True)
    if len(values) < 2:
        return values[0] if values else float("-inf")
    return values[0] - values[1]


def split_rate(
    rows: list[dict[str, Any]],
    predicate,
) -> dict[str, Any]:
    yes = [row for row in rows if predicate(row)]
    no = [row for row in rows if not predicate(row)]
    return {
        "whenTrue": summarize_rows(yes) if yes else {"n": 0, "passRate": None, "ci95": None, "chance": None},
        "whenFalse": summarize_rows(no) if no else {"n": 0, "passRate": None, "ci95": None, "chance": None},
        "nTrue": len(yes),
        "nFalse": len(no),
    }


def main() -> None:
    items_by_id = load_items()
    primary_ids = load_primary_ids()
    scored = load_jsonl(ITEMS_14B)
    algebra_rows: list[dict[str, Any]] = []
    for row in scored:
        if str(row.get("cell")) != ALGEBRA_I_CELL:
            continue
        if str(row["id"]) not in primary_ids:
            continue
        item = items_by_id[str(row["id"])]
        choices = item.get("choices") or {}
        key = str(row["key"]).strip().upper()
        chosen = str(row["chosen_letter"]).strip().upper()
        pairs = numeric_pairs(item)
        lower_central = lower_central_key(pairs) if pairs else None
        hub = apply_s1(item)
        hub_letter = str(hub.answer).strip().upper() if hub.fired and hub.answer else None
        longest = unique_longest_letter(choices)
        option_type = classify_item_option_type(item)
        mask_report = mask_stem(str(item.get("stem") or ""))
        enriched = dict(row)
        enriched["item"] = item
        enriched["lower_central"] = lower_central
        enriched["key_is_lower_central"] = bool(lower_central and key == lower_central)
        enriched["hub_fired"] = bool(hub.fired)
        enriched["hub_letter"] = hub_letter
        enriched["key_is_hub"] = bool(hub_letter and key == hub_letter)
        enriched["longest_letter"] = longest
        enriched["key_is_longest"] = bool(longest and key == longest)
        enriched["option_type"] = option_type
        enriched["masked_stem"] = mask_report["masked"]
        enriched["original_stem"] = str(item.get("stem") or "")
        enriched["margin"] = logprob_margin(row)
        enriched["model_picked_hub"] = bool(hub_letter and chosen == hub_letter)
        enriched["model_picked_longest"] = bool(longest and chosen == longest)
        algebra_rows.append(enriched)

    if len(algebra_rows) != 358:
        raise RuntimeError(f"expected 358 Algebra I primary items, got {len(algebra_rows)}")

    keys = [str(row["key"]) for row in algebra_rows]
    modal, modal_count, modal_frequency = modal_letter(keys)
    for row in algebra_rows:
        row["modal_letter"] = modal
        row["key_is_modal_letter"] = str(row["key"]) == modal

    residual = [
        row
        for row in algebra_rows
        if not row["key_is_lower_central"]
        and not row["key_is_modal_letter"]
        and not row["key_is_hub"]
        and not row["key_is_longest"]
    ]
    residual_stats = summarize_rows(residual)
    chance = residual_stats["chance"] if residual else 0.25
    residual_clears_chance = bool(
        residual and residual_stats["n"] >= 10 and residual_stats["ci95"][0] > chance
    )

    type_groups: dict[str, list[dict[str, Any]]] = {}
    for row in algebra_rows:
        type_groups.setdefault(str(row["option_type"]), []).append(row)
    per_type = {
        name: summarize_rows(group)
        for name, group in sorted(type_groups.items())
    }

    cue_payload = {
        "status": "complete",
        "label": "exploratory",
        "writtenAt": datetime.now(timezone.utc).isoformat(),
        "modelId": "Qwen/Qwen2.5-14B-Instruct",
        "cell": ALGEBRA_I_CELL,
        "population": "masked_token_count_ge_1",
        "n": len(algebra_rows),
        "overall": summarize_rows(algebra_rows),
        "modalLetterOnPopulation": {
            "letter": modal,
            "count": modal_count,
            "frequency": modal_frequency,
        },
        "hubRule": (
            "scripts/strategy_channels.py apply_s1 / hub_from_edges: numeric options "
            "with at least 3 parsed values; hub is max out-degree under TRANSFORM_NAMES; "
            "ties broken by lower_central_key."
        ),
        "longestRule": "Unique maximum character length among option strings; ties count as no unique longest.",
        "lowerCentralRule": (
            "lower_central_key on parse_option_number pairs; undefined when no option parses as numeric."
        ),
        "splits": {
            "keyIsLowerCentralNumeric": split_rate(
                algebra_rows, lambda row: bool(row["key_is_lower_central"])
            ),
            "keyIsModalLetter": split_rate(
                algebra_rows, lambda row: bool(row["key_is_modal_letter"])
            ),
            "keyIsS1Hub": split_rate(
                algebra_rows, lambda row: bool(row["key_is_hub"])
            ),
            "keyIsUniqueLongest": split_rate(
                algebra_rows, lambda row: bool(row["key_is_longest"])
            ),
        },
        "cueDefinedCounts": {
            "lowerCentralDefined": sum(1 for row in algebra_rows if row["lower_central"]),
            "s1HubFired": sum(1 for row in algebra_rows if row["hub_fired"]),
            "uniqueLongestDefined": sum(1 for row in algebra_rows if row["longest_letter"]),
        },
        "residual": {
            "definition": (
                "Items where none of lower-central numeric, population modal letter, "
                "S1 hub, or unique-longest option points at the key."
            ),
            "n": len(residual),
            "stats": residual_stats,
            "clearsChance": residual_clears_chance,
            "verdict": (
                "flexible reader uses cues outside the catalog"
                if residual_clears_chance
                else "residual does not clear chance"
            ),
        },
        "perOptionType": per_type,
        "optionTypeRule": (
            "Item-level: all options share a type, else majority if it is at least half, else mixed. "
            "Types: numeric, algebraic_expression, ordered_pair, text."
        ),
    }
    dump_json(CUE_PATH, cue_payload)

    by_id = {str(row["id"]): row for row in algebra_rows}
    correct_pool = [
        row
        for row in algebra_rows
        if bool(row["correct"])
        and not row["key_is_modal_letter"]
        and not row["key_is_lower_central"]
    ]
    wrong_pool = [row for row in algebra_rows if not bool(row["correct"])]

    def example_record(row: dict[str, Any], cue: str) -> dict[str, Any]:
        item = row["item"]
        return {
            "id": row["id"],
            "originalStem": row["original_stem"],
            "maskedStem": row["masked_stem"],
            "options": item.get("choices"),
            "key": row["key"],
            "chosenLetter": row["chosen_letter"],
            "correct": bool(row["correct"]),
            "logprobs": row.get("logprobs"),
            "margin": row["margin"],
            "optionType": row["option_type"],
            "keyIsModalLetter": row["key_is_modal_letter"],
            "keyIsLowerCentral": row["key_is_lower_central"],
            "keyIsHub": row["key_is_hub"],
            "keyIsLongest": row["key_is_longest"],
            "hubLetter": row["hub_letter"],
            "longestLetter": row["longest_letter"],
            "visibleCue": cue,
        }

    talk_correct = [
        (
            "nyregents-algebra-i-2015-jun-q1",
            "Numbers 110 and 900 remain in the options; the leftover C(n)=[N]n+[N] story maps the larger dollar amount to production and the smaller to per airing.",
        ),
        (
            "nyregents-algebra-i-2023-jun-q8",
            "Growth model b=[N]([N])^x is still named; among verbal roles, the exponent is the number of time periods.",
        ),
        (
            "nyregents-algebra-i-2017-aug-q17",
            "Highest grade with a constant deduction each late day is still a linear story after the 100 and 10 are hidden.",
        ),
        (
            "nyregents-algebra-i-2017-aug-q22",
            "The sign on r is still visible as a minus; the leftover asks for the relationship, so strong negative rather than positive or weak.",
        ),
        (
            "nyregents-algebra-i-2023-jan-q22",
            "The zero set is listed as three placeholders, so the matching polynomial is the three-factor option that includes an x.",
        ),
        (
            "nyregents-algebra-i-2014-jun-q22",
            "60 and 0.05 are repeated in the option formulas; the leftover base-plus-per-megabyte story selects c=60+0.05d, not 60d.",
        ),
    ]
    talk_wrong = [
        (
            "nyregents-algebra-i-2026-jun-q17",
            "Completing the square by adding 16 to both sides; the model assigned probability 1 to distributive property instead of addition property of equality.",
        ),
        (
            "nyregents-algebra-i-2023-jan-q11",
            "Depreciation of [N]% per year; the model took (1+.20)^t (growth) over (1-.20)^t (decay) at margin 24.3.",
        ),
        (
            "nyregents-algebra-i-2024-aug-q6",
            "Moving a term by adding to both sides; again assigned probability 1 to distributive property instead of addition property of equality.",
        ),
    ]
    selected_correct: list[dict[str, Any]] = []
    for item_id, cue in talk_correct:
        row = by_id.get(item_id)
        if row is None:
            raise RuntimeError(f"talk example missing from Algebra I primary: {item_id}")
        if not bool(row["correct"]):
            raise RuntimeError(f"talk example is not a 14B masked-stem hit: {item_id}")
        if row["key_is_modal_letter"] or row["key_is_lower_central"]:
            raise RuntimeError(f"talk example fails non-modal non-lower-central filter: {item_id}")
        selected_correct.append(example_record(row, cue))
    selected_wrong: list[dict[str, Any]] = []
    for item_id, cue in talk_wrong:
        row = by_id.get(item_id)
        if row is None or bool(row["correct"]):
            raise RuntimeError(f"talk miss missing or not a miss: {item_id}")
        selected_wrong.append(example_record(row, cue))

    examples_payload = {
        "status": "complete",
        "label": "exploratory",
        "writtenAt": datetime.now(timezone.utc).isoformat(),
        "modelId": "Qwen/Qwen2.5-14B-Instruct",
        "cell": ALGEBRA_I_CELL,
        "population": "masked_token_count_ge_1",
        "selection": {
            "correct": (
                "14B masked-stem correct; key is not the Algebra I primary modal letter "
                "and is not the lower-central numeric option."
            ),
            "wrong": "14B masked-stem incorrect; highest letter-logprob margin.",
        },
        "nCorrectPool": len(correct_pool),
        "nWrongPool": len(wrong_pool),
        "correctExamples": selected_correct[:6],
        "wrongHighConfidenceExamples": selected_wrong[:3],
    }
    dump_json(EXAMPLES_PATH, examples_payload)
    print(
        json.dumps(
            {
                "n": len(algebra_rows),
                "modal": modal,
                "modalFrequency": modal_frequency,
                "residualN": len(residual),
                "residualRate": residual_stats.get("passRate"),
                "residualCi": residual_stats.get("ci95"),
                "residualClearsChance": residual_clears_chance,
                "perTypeN": {name: stats["n"] for name, stats in per_type.items()},
                "nCorrectExamples": len(selected_correct[:6]),
                "nWrongExamples": len(selected_wrong[:3]),
                "correctIds": [row["id"] for row in selected_correct[:6]],
                "wrongIds": [row["id"] for row in selected_wrong[:3]],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
