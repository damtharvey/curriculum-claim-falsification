#!/usr/bin/env python3
"""Shared helpers for the masked-stem construct and contamination follow-up."""

from __future__ import annotations

import math
import random
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

PLACEHOLDER = "[N]"
ALWAYS_B_BASELINE = 0.275
EXPERIMENT_SEED = 20260916
NAMED_REPORT_CELLS = (
    "nyregents::algebra-i",
    "nyregents::algebra-ii",
    "nyregents::geometry",
    "eqao::g6",
    "timss::knowing",
    "timss::applying",
    "timss::reasoning",
)
FIRST_RUN_CLEAR_7B = (
    "nyregents::algebra-i",
    "nyregents::algebra-ii",
    "nyregents::geometry",
    "teks::g5",
    "teks::g8",
    "timss::knowing",
)
FIRST_RUN_CLEAR_14B = (
    "nyregents::algebra-i",
    "nyregents::algebra-ii",
    "nyregents::geometry",
    "eqao::g9",
    "teks::g8",
    "timss::knowing",
)
YEAR_BUCKET_ORDER = (
    "before_2015",
    "2015_to_2019",
    "2020_to_2023",
    "2024_and_later",
)
YEAR_IN_TEXT_RE = re.compile(r"(?:^|[-_])((?:19|20)\d{2})(?:[-_]|$)")
YEAR_IN_CORPUS_RE = re.compile(r"((?:19|20)\d{2})")
REGENTS_SESSION_RE = re.compile(
    r"nyregents-[a-z0-9-]+-((?:19|20)\d{2})-(jan|jun|aug|unk)-",
    re.I,
)

# One-line construct judgments for TIMSS knowing. cue = option/type heuristic
# after masking; knowledge = tagged fact or operation still usable; unclear otherwise.
TIMSS_KNOWING_JUDGMENTS: dict[str, dict[str, str]] = {
    "timss2011-8-M032094": {
        "verdict": "cue",
        "reason": "Addends hidden; leftover is a four-decimal option list for a blank sum.",
    },
    "timss2011-8-M032166": {
        "verdict": "cue",
        "reason": "Factors hidden; options are a scale-of-ten estimate ladder.",
    },
    "timss2011-8-M052216": {
        "verdict": "cue",
        "reason": "3/5 hidden; leftover is which decimal matches an unknown fraction.",
    },
    "timss2011-8-M032295": {
        "verdict": "knowledge",
        "reason": "Story still maps to a multiple of (m+n); the 2 also remains in the options.",
    },
    "timss2011-8-M032419": {
        "verdict": "cue",
        "reason": "Coefficients of 2x+3x hidden, so the 5x reading cannot be recovered.",
    },
    "timss2011-4-M041010": {
        "verdict": "unclear",
        "reason": "Place-value digits hidden; a hit can be option scanning or item recall.",
    },
    "timss2011-4-M041011": {
        "verdict": "cue",
        "reason": "Both 100 and 5,432 hidden; leftover is a +100 near-miss option set.",
    },
    "timss1999-8-B10": {
        "verdict": "knowledge",
        "reason": "Stem withholds nothing; the tagged task is comparing the option decimals.",
    },
    "timss1999-8-L10": {
        "verdict": "cue",
        "reason": "Number words hidden; 206.9 is the conventional written form in the list.",
    },
    "timss1999-8-N14": {
        "verdict": "knowledge",
        "reason": "Stem withholds nothing; equivalent-fraction checking is on the option lists.",
    },
    "timss1999-8-B12": {
        "verdict": "cue",
        "reason": "7, 6, and 41 hidden in the stem but printed in the option equations.",
    },
    "timss1999-8-D10": {
        "verdict": "cue",
        "reason": "Fixed 100 and 6 hidden in the stem but printed in C=(100+6n).",
    },
    "timss1999-8-P09": {
        "verdict": "knowledge",
        "reason": "n x n x n is fully visible; that is the tagged identity (OCR n3 vs n^3).",
    },
    "timss1999-8-P11": {
        "verdict": "knowledge",
        "reason": "Five k addends are visible, so 5k is the tagged rewrite.",
    },
    "timss1999-8-R10": {
        "verdict": "knowledge",
        "reason": "Commutativity of real multiplication; no quantity is withheld.",
    },
    "timss1999-8-R12": {
        "verdict": "knowledge",
        "reason": "Sign of powers of a negative k; the named sign is unmasked.",
    },
    "timss1999-8-D11": {
        "verdict": "knowledge",
        "reason": "Units for the mass of an egg; the named object is unmasked.",
    },
    "timss1999-8-J11": {
        "verdict": "knowledge",
        "reason": "Rectangle properties; the named shape is unmasked.",
    },
    "timss1999-8-F08": {
        "verdict": "knowledge",
        "reason": "Independence of a fair coin; 1/2 and four tosses are not required.",
    },
    "timss1995-8-J15": {
        "verdict": "unclear",
        "reason": "two is masked; similar-triangle choice still needs the figure.",
    },
    "timss1995-8-L9": {
        "verdict": "cue",
        "reason": "Number words hidden; leftover is which decimal matches a spoken form.",
    },
    "timss1995-8-M1": {
        "verdict": "unclear",
        "reason": "Scale reading; the figure and tick numbers sit in the option footer.",
    },
    "timss1995-8-O3": {
        "verdict": "knowledge",
        "reason": "Parallel lines give supplementary pairs; 180 and two are not required.",
    },
    "timss1995-8-P10": {
        "verdict": "knowledge",
        "reason": "Four m addends are visible, so 4m is the tagged rewrite.",
    },
    "timss2003-4-M031338": {
        "verdict": "knowledge",
        "reason": "Milliliters as liquid volume; 150 is hidden, the unit remains.",
    },
    "timss1995-4-I2": {
        "verdict": "cue",
        "reason": "0.4 hidden; leftover is tenths vs hundredths option wording.",
    },
    "timss1995-4-J1": {
        "verdict": "knowledge",
        "reason": "A hexagon splits into triangles; hexagon is unmasked, six is [N].",
    },
    "timss1995-4-J8": {
        "verdict": "cue",
        "reason": "Hours hidden; options are round-number estimate triples.",
    },
    "timss1995-4-K3": {
        "verdict": "cue",
        "reason": "Multiply-by-5 hidden in the stem; 3 to 15 remains in the options.",
    },
    "timss1995-4-L3": {
        "verdict": "unclear",
        "reason": "Coordinate 2 is masked; the game board is not in the stem.",
    },
    "timss1995-4-L5": {
        "verdict": "knowledge",
        "reason": "A cube has 12 edges; cube is unmasked, one is [N].",
    },
    "timss1995-4-L9": {
        "verdict": "knowledge",
        "reason": "Transitivity of older-than; no quantity is withheld.",
    },
    "timss1995-4-M3": {
        "verdict": "knowledge",
        "reason": "Commutativity of multiplication; 7 is hidden, the times sign remains.",
    },
    "timss1995-4-M5": {
        "verdict": "unclear",
        "reason": "Shaded-part reading; the figure is not in the stem.",
    },
    "timss1995-4-M7": {
        "verdict": "knowledge",
        "reason": "Milliliters for a teaspoon of liquid; named objects are unmasked.",
    },
}


def stem_chars_masked_share(original: str, masked: str, placeholder: str = PLACEHOLDER) -> float:
    """Share of original stem characters that are absent from the non-placeholder residue."""
    if not original:
        return 0.0
    remaining = masked.replace(placeholder, "")
    removed = len(original) - len(remaining)
    return min(1.0, max(0.0, removed / len(original)))


def parse_year(item: dict[str, Any]) -> int | None:
    raw = item.get("year")
    if raw is not None:
        text = str(raw).strip()
        if re.fullmatch(r"(19|20)\d{2}", text):
            return int(text)
    item_id = str(item.get("id") or "")
    match = YEAR_IN_TEXT_RE.search(item_id)
    if match:
        return int(match.group(1))
    corpus = str(item.get("corpus") or "")
    match = YEAR_IN_CORPUS_RE.search(corpus)
    if match:
        return int(match.group(1))
    match = YEAR_IN_CORPUS_RE.search(item_id)
    if match:
        return int(match.group(0))
    return None


def year_bucket(year: int | None) -> str:
    if year is None:
        return "unparsed"
    if year < 2015:
        return "before_2015"
    if year <= 2019:
        return "2015_to_2019"
    if year <= 2023:
        return "2020_to_2023"
    return "2024_and_later"


def parse_regents_session(item_id: str) -> dict[str, Any] | None:
    match = REGENTS_SESSION_RE.search(str(item_id))
    if not match:
        return None
    return {"year": int(match.group(1)), "session": match.group(2).lower()}


def bootstrap_ci(flags: list[int], n_boot: int = 1000, seed: int = 11) -> tuple[float, float]:
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
        "lowerCiAboveChance": n >= 10 and ci[0] > chance,
    }


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
        "note": "Always pick the most common key letter among items in this population.",
    }


def modal_letter(keys: list[str]) -> tuple[str, int, float]:
    counts = Counter(keys)
    if not counts:
        return ("", 0, 0.0)
    max_count = max(counts.values())
    letter = min(letter for letter, count in counts.items() if count == max_count)
    return (letter, max_count, max_count / len(keys))


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


def enrich_cells(
    rows: list[dict[str, Any]],
    modal_by_cell_full: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("cell") or "unknown")].append(row)
    per_cell: dict[str, dict[str, Any]] = {}
    named: dict[str, dict[str, Any]] = {}
    clears_population_modal: list[dict[str, Any]] = []
    n_by_cell: dict[str, int] = {}
    for name, group in sorted(grouped.items()):
        n_by_cell[name] = len(group)
        stats = summarize_rows(group)
        keys = [str(row["key"]) for row in group]
        pop_letter, pop_count, pop_frequency = modal_letter(keys)
        full = modal_by_cell_full.get(name) or {}
        full_letter = full.get("modalLetter")
        full_frequency = full.get("modalFrequency")
        lower = stats["ci95"][0]
        n = stats["n"]
        stats["modalLetterOnPopulation"] = pop_letter
        stats["modalCountOnPopulation"] = pop_count
        stats["modalFrequencyOnPopulation"] = pop_frequency
        stats["modalLetterFull1487"] = full_letter
        stats["modalFrequencyFull1487"] = full_frequency
        stats["lowerCiAboveModalOnPopulation"] = n >= 10 and lower > pop_frequency
        stats["lowerCiAboveModalFull1487"] = (
            n >= 10 and full_frequency is not None and lower > float(full_frequency)
        )
        stats["clearsWitnessBarOnPopulation"] = bool(
            stats["lowerCiAboveChance"] and stats["lowerCiAboveModalOnPopulation"]
        )
        stats["clearsWitnessBarVsFull1487Modal"] = bool(
            stats["lowerCiAboveChance"] and stats["lowerCiAboveModalFull1487"]
        )
        non_modal = [row for row in group if str(row["key"]) != pop_letter]
        stats["nonModalKey"] = summarize_rows(non_modal) if non_modal else {"n": 0}
        if n >= 10:
            per_cell[name] = stats
            if stats["clearsWitnessBarOnPopulation"]:
                clears_population_modal.append({"cell": name, **stats})
        if name in NAMED_REPORT_CELLS:
            named[name] = stats
    return {
        "nByCell": n_by_cell,
        "perCell": per_cell,
        "namedCells": named,
        "cellsClearingChanceAndModalOnPopulation": clears_population_modal,
    }


def vs_always_b(rows: list[dict[str, Any]]) -> dict[str, Any]:
    overall = summarize_rows(rows)
    recomputed = position_baseline(rows)
    lower = overall["ci95"][0] if rows else 0.0
    return {
        "statedBaseline": ALWAYS_B_BASELINE,
        "passRate": overall.get("passRate"),
        "ci95": overall.get("ci95"),
        "lowerCiAboveStatedAlwaysB": (
            int(overall.get("n") or 0) >= 10 and lower > ALWAYS_B_BASELINE
        ),
        "recomputedAlwaysB": recomputed,
        "lowerCiAboveRecomputedAlwaysB": (
            int(overall.get("n") or 0) >= 10 and lower > float(recomputed["rate"])
        ),
    }


def rank_average(values: list[float]) -> list[float]:
    n = len(values)
    order = sorted(range(n), key=lambda index: values[index])
    ranks = [0.0] * n
    index = 0
    while index < n:
        end = index
        while end + 1 < n and values[order[end + 1]] == values[order[index]]:
            end += 1
        average = (index + end + 2) / 2.0
        for pos in range(index, end + 1):
            ranks[order[pos]] = average
        index = end + 1
    return ranks


def pearson(xs: list[float], ys: list[float]) -> float | None:
    n = len(xs)
    if n != len(ys) or n < 3:
        return None
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    num = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    den_x = math.sqrt(sum((x - mean_x) ** 2 for x in xs))
    den_y = math.sqrt(sum((y - mean_y) ** 2 for y in ys))
    if den_x == 0.0 or den_y == 0.0:
        return None
    return num / (den_x * den_y)


def spearman(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) != len(ys) or len(xs) < 3:
        return None
    return pearson(rank_average(xs), rank_average(ys))


def quartile_by_rank(values: list[float]) -> list[int]:
    """Assign 1 (lowest) through 4 (highest) by rank; ties keep adjacent ranks."""
    n = len(values)
    if n == 0:
        return []
    order = sorted(range(n), key=lambda index: values[index])
    labels = [0] * n
    for rank, index in enumerate(order):
        labels[index] = min(4, (rank * 4) // n + 1)
    return labels


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(__import__("json").loads(line))
    return rows


def dump_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        __import__("json").dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )
