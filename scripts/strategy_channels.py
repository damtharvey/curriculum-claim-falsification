#!/usr/bin/env python3
"""Adaptive test-taker strategy channels S1–S5. Matches addendum-strategies preregistration v1."""

from __future__ import annotations

import itertools
import math
import re
import tokenize
from dataclasses import dataclass, field
from typing import Any, Callable

import sympy
from sympy.core.sympify import SympifyError
from sympy.parsing.sympy_parser import (
    convert_xor,
    implicit_multiplication_application,
    parse_expr,
    standard_transformations,
)

LEADING_NUMBER_RE = re.compile(r"^[^\d-]*(-?\d+(?:\.\d+)?)")
FRACTION_RE = re.compile(r"^(-?\d+)\s*/\s*(-?\d+)$")
STEM_NUMBER_RE = re.compile(r"-?\d+(?:\.\d+)?")
STEM_FRACTION_RE = re.compile(r"(-?\d+)\s*/\s*(-?\d+)")
EQUATION_RE = re.compile(
    r"(?P<left>[0-9A-Za-z.\s+\-*/×·÷^()√π]+)"
    r"\s*(?P<rel>==|≠|!=|≤|≥|<=|>=|=|<|>)\s*"
    r"(?P<right>[0-9A-Za-z.\s+\-*/×·÷^()√π]+)"
)
RELATION_TOKEN_RE = re.compile(r"==|≠|!=|≤|≥|<=|>=|=|<|>")
OPTION_EQ_RE = re.compile(r"^([A-Za-z])\s*=\s*(.+)$")
PI_RE = re.compile(r"\bpi\b|π", re.I)
UNIT_WORD_RE = re.compile(
    r"\b(cm|mm|km|kg|mg|ms|ml|lb|ft|in|yd|mph|hours?|minutes?|"
    r"seconds?|degrees?|percent|metres?|meters?)\b",
    re.I,
)
GEOMETRY_RE = re.compile(
    r"\b(triangle|circle|radius|diameter|circumference|rectangle|square|"
    r"trapezoid|parallelogram|prism|cylinder|sphere|hypotenuse|base|"
    r"height|width|length|perimeter|area|volume)\b",
    re.I,
)
HOW_MANY_RE = re.compile(r"\bhow many\b|\bnumber of\b", re.I)
PROBABILITY_RE = re.compile(r"\bprobability\b", re.I)
PERCENT_RE = re.compile(r"\bpercent(?:age)?\b|%", re.I)
LENGTH_RE = re.compile(
    r"\b(length|distance|area|volume|perimeter|height|width)\b", re.I
)
INTERIOR_ANGLE_RE = re.compile(
    r"interior\s+angle|(?:\btriangle\b.*\bangle\b)|(?:\bangle\b.*\btriangle\b)",
    re.I,
)
ANGLE_RE = re.compile(r"\bangle\b|\bdegrees\b", re.I)
MEAN_RE = re.compile(r"\bmean\b|\bmedian\b", re.I)
YEAR_RE = re.compile(r"^(?:19|20)\d{2}$")

TRANSFORM_NAMES: tuple[str, ...] = (
    "times2",
    "div2",
    "times10",
    "div10",
    "plus1",
    "minus1",
    "signFlip",
    "reciprocal",
    "square",
    "sqrt",
    "swapAdjacentDigits",
    "dropTrailingZero",
    "addTrailingZero",
    "plusTenPercentRounded",
    "minusTenPercentRounded",
)

S5_BRANCHES: tuple[str, ...] = (
    "s4_unique",
    "s3_depth1_unique",
    "s2_s1_unique_hub",
    "lower_central_survivors",
    "letter_B",
)

TEKS_SOLVE_TAGS = {
    "6.10(A)",
    "6.10(B)",
    "7.11(A)",
    "7.11(B)",
    "8.8(A)",
    "8.8(B)",
    "8.8(C)",
    "A.5(A)",
    "A.5(B)",
    "A.5(C)",
    "A.5(D)",
    "A.8(A)",
    "A.8(B)",
}

SOLVING_CELLS = {
    ("nyregents", "algebra-i"),
    ("nyregents", "algebra-ii"),
    ("teks", "alg1"),
    ("eqao", "g9"),
}

PI = math.pi
MATCH_ABS = 0.01
MATCH_REL = 1e-4
MAX_SEEDS = 12
MAX_CLOSURE_VALUES = 4000
MAX_ABS_VALUE = 1e12


def values_match(left: float, right: float) -> bool:
    if not math.isfinite(left) or not math.isfinite(right):
        return False
    scale = max(1.0, abs(left), abs(right))
    return abs(left - right) <= MATCH_REL * scale or abs(left - right) < MATCH_ABS


def choice_keys(item: dict[str, Any]) -> list[str]:
    return sorted((item.get("choices") or {}).keys())


def format_chance_k(item: dict[str, Any]) -> float | None:
    n_choices = len(item.get("choices") or {})
    return 1.0 / n_choices if n_choices > 0 else None


def clean_numeric_text(text: str) -> str:
    stripped = (
        text.strip()
        .replace("\u2212", "-")
        .replace("\u2013", "-")
        .replace("\u2014", "-")
    )
    return re.sub(r"(?<=\d),(?=\d)", "", stripped)


def parse_option_number(text: str) -> float | None:
    cleaned = clean_numeric_text(text)
    fraction = FRACTION_RE.match(cleaned)
    if fraction:
        denom = float(fraction.group(2))
        if denom == 0:
            return None
        value = float(fraction.group(1)) / denom
        return value if math.isfinite(value) else None
    leading = LEADING_NUMBER_RE.match(cleaned)
    if not leading:
        return None
    value = float(leading.group(1))
    return value if math.isfinite(value) else None


def option_candidate_value(text: str) -> float | None:
    cleaned = clean_numeric_text(text)
    matched = OPTION_EQ_RE.match(cleaned)
    if matched:
        return parse_option_number(matched.group(2))
    return parse_option_number(cleaned)


def decimal_places(text: str) -> int:
    cleaned = clean_numeric_text(text)
    match = re.search(r"\.(\d+)", cleaned)
    return len(match.group(1)) if match else 0


def parsed_numeric_options(item: dict[str, Any]) -> list[tuple[str, float, str]]:
    choices = item.get("choices") or {}
    parsed: list[tuple[str, float, str]] = []
    for key in choice_keys(item):
        text = str(choices.get(key, ""))
        value = parse_option_number(text)
        if value is not None:
            parsed.append((key, value, text))
    parsed.sort(key=lambda row: (row[1], row[0]))
    return parsed


def lower_central_key(pairs: list[tuple[str, float]]) -> str | None:
    if not pairs:
        return None
    ordered = sorted(pairs, key=lambda row: (row[1], row[0]))
    mid_value = ordered[math.floor((len(ordered) - 1) / 2)][1]
    winners = [key for key, value in ordered if value == mid_value]
    return winners[0] if winners else None


def extract_stem_numbers(item: dict[str, Any]) -> list[float]:
    parts = [str(item.get("stem") or "")]
    figure = item.get("figure") or {}
    transcription = figure.get("transcription")
    if transcription:
        parts.append(str(transcription))
    text = " ".join(parts)
    found: list[float] = []
    for match in STEM_FRACTION_RE.finditer(text):
        denom = float(match.group(2))
        if denom == 0:
            continue
        value = float(match.group(1)) / denom
        if math.isfinite(value):
            found.append(value)
    for match in STEM_NUMBER_RE.finditer(text):
        value = float(match.group(0))
        if math.isfinite(value):
            found.append(value)
    unique: list[float] = []
    for value in found:
        if any(values_match(value, existing) for existing in unique):
            continue
        unique.append(value)
        if len(unique) >= MAX_SEEDS:
            break
    return unique


def swap_adjacent_digit_values(text: str) -> list[float]:
    cleaned = clean_numeric_text(text)
    sign = ""
    body = cleaned
    if body.startswith("-"):
        sign = "-"
        body = body[1:]
    chars = list(body)
    digit_positions = [index for index, char in enumerate(chars) if char.isdigit()]
    values: list[float] = []
    for offset in range(len(digit_positions) - 1):
        left_index = digit_positions[offset]
        right_index = digit_positions[offset + 1]
        swapped = chars[:]
        swapped[left_index], swapped[right_index] = swapped[right_index], swapped[left_index]
        try:
            value = float(sign + "".join(swapped))
        except ValueError:
            continue
        if math.isfinite(value):
            values.append(value)
    return values


def drop_trailing_zero_values(value: float, text: str) -> list[float]:
    out: list[float] = []
    if abs(value - round(value)) < 1e-9:
        integer = int(round(value))
        if abs(integer) >= 10 and integer % 10 == 0:
            out.append(integer / 10.0)
    cleaned = clean_numeric_text(text)
    body = cleaned[1:] if cleaned.startswith("-") else cleaned
    sign = "-" if cleaned.startswith("-") else ""
    if re.search(r"0$", body) and len(re.sub(r"\D", "", body)) >= 2:
        trimmed = re.sub(r"0$", "", body)
        trimmed = trimmed.rstrip(".")
        try:
            produced = float(sign + trimmed)
        except ValueError:
            produced = None
        if produced is not None and math.isfinite(produced):
            out.append(produced)
    return out


def transform_values(name: str, value: float, text: str) -> list[float]:
    places = decimal_places(text)
    produced: list[float] = []
    if name == "times2":
        produced = [2.0 * value]
    elif name == "div2":
        produced = [value / 2.0]
    elif name == "times10":
        produced = [10.0 * value]
    elif name == "div10":
        produced = [value / 10.0]
    elif name == "plus1":
        produced = [value + 1.0]
    elif name == "minus1":
        produced = [value - 1.0]
    elif name == "signFlip":
        produced = [-value]
    elif name == "reciprocal":
        if value != 0:
            produced = [1.0 / value]
    elif name == "square":
        produced = [value * value]
    elif name == "sqrt":
        if value >= 0:
            produced = [math.sqrt(value)]
    elif name == "swapAdjacentDigits":
        produced = swap_adjacent_digit_values(text)
    elif name == "dropTrailingZero":
        produced = drop_trailing_zero_values(value, text)
    elif name == "addTrailingZero":
        produced = [10.0 * value]
    elif name == "plusTenPercentRounded":
        produced = [round(value * 1.1, places)]
    elif name == "minusTenPercentRounded":
        produced = [round(value * 0.9, places)]
    return [item for item in produced if math.isfinite(item) and abs(item) <= MAX_ABS_VALUE]


def s1_edges_by_transform(
    item: dict[str, Any],
) -> dict[str, dict[str, set[str]]]:
    parsed = parsed_numeric_options(item)
    edges: dict[str, dict[str, set[str]]] = {name: {} for name in TRANSFORM_NAMES}
    for name in TRANSFORM_NAMES:
        for src_key, src_value, src_text in parsed:
            targets: set[str] = set()
            for produced in transform_values(name, src_value, src_text):
                for dst_key, dst_value, _dst_text in parsed:
                    if dst_key == src_key:
                        continue
                    if values_match(produced, dst_value):
                        targets.add(dst_key)
            if targets:
                edges[name][src_key] = targets
    return edges


def hub_from_edges(
    parsed: list[tuple[str, float, str]],
    edges_by_transform: dict[str, dict[str, set[str]]],
    transform_names: tuple[str, ...] | list[str],
    tie: str,
    rng: Any | None,
) -> tuple[str | None, dict[str, int], bool]:
    parsed_keys = {key for key, _value, _text in parsed}
    out_degree: dict[str, set[str]] = {key: set() for key in parsed_keys}
    for name in transform_names:
        for src, targets in edges_by_transform.get(name, {}).items():
            if src not in parsed_keys:
                continue
            out_degree.setdefault(src, set()).update(target for target in targets if target in parsed_keys)
    degrees = {key: len(targets) for key, targets in out_degree.items()}
    if not degrees or max(degrees.values()) < 1:
        return None, degrees, False
    max_degree = max(degrees.values())
    tied = sorted(key for key, degree in degrees.items() if degree == max_degree)
    unique = len(tied) == 1
    if unique:
        return tied[0], degrees, True
    if tie == "random" and rng is not None:
        index = int(math.floor(rng.random() * len(tied)))
        return tied[index], degrees, False
    tied_pairs = [(key, next(value for k, value, _text in parsed if k == key)) for key in tied]
    picked = lower_central_key(tied_pairs)
    if picked is None:
        picked = sorted(tied_pairs, key=lambda row: (row[1], row[0]))[0][0]
    return picked, degrees, False


@dataclass
class ChannelResult:
    answer: str | None
    chance: float | None
    fired: bool
    branch: str
    extra: dict[str, Any] = field(default_factory=dict)


def apply_s1(
    item: dict[str, Any],
    *,
    transform_names: tuple[str, ...] | list[str] | None = None,
    tie: str = "lower-central",
    rng: Any | None = None,
    edges_by_transform: dict[str, dict[str, set[str]]] | None = None,
) -> ChannelResult:
    parsed = parsed_numeric_options(item)
    chance = format_chance_k(item)
    if len(parsed) < 3 or chance is None:
        return ChannelResult(None, None, False, "s1", {"reason": "fewer than 3 numeric options"})
    names = list(transform_names or TRANSFORM_NAMES)
    edges = edges_by_transform if edges_by_transform is not None else s1_edges_by_transform(item)
    answer, degrees, unique = hub_from_edges(parsed, edges, names, tie, rng)
    if answer is None:
        return ChannelResult(None, chance, False, "s1", {"reason": "max out-degree 0", "degrees": degrees})
    return ChannelResult(
        answer,
        chance,
        True,
        "s1",
        {
            "degrees": degrees,
            "uniqueHub": unique,
            "nParsed": len(parsed),
            "chanceParsed": 1.0 / len(parsed),
        },
    )


def stem_constraint_predicates(item: dict[str, Any]) -> list[Callable[[float], bool]]:
    stem = str(item.get("stem") or "")
    predicates: list[Callable[[float], bool]] = []
    if HOW_MANY_RE.search(stem):
        predicates.append(lambda x: x >= 0 and abs(x - round(x)) < 1e-6)
    if PROBABILITY_RE.search(stem):
        predicates.append(lambda x: 0.0 <= x <= 1.0)
    if PERCENT_RE.search(stem):
        predicates.append(lambda x: 0.0 <= x <= 100.0)
    if LENGTH_RE.search(stem):
        predicates.append(lambda x: x > 0)
    if INTERIOR_ANGLE_RE.search(stem):
        predicates.append(lambda x: 0.0 < x < 180.0)
    elif ANGLE_RE.search(stem):
        predicates.append(lambda x: 0.0 < x < 360.0)
    if MEAN_RE.search(stem):
        data = extract_stem_numbers(item)
        if len(data) == 1:
            only = data[0]
            if abs(only - round(only)) < 1e-9 and YEAR_RE.match(str(int(round(only)))):
                data = []
        if len(data) >= 2:
            low = min(data)
            high = max(data)
            predicates.append(lambda x, low=low, high=high: low <= x <= high)
    return predicates


def s2_survivors(item: dict[str, Any]) -> tuple[list[str], list[Callable[[float], bool]]]:
    predicates = stem_constraint_predicates(item)
    keys = choice_keys(item)
    choices = item.get("choices") or {}
    if not predicates:
        return keys, predicates
    survivors: list[str] = []
    for key in keys:
        text = str(choices.get(key, ""))
        value = parse_option_number(text)
        if value is None:
            survivors.append(key)
            continue
        if all(predicate(value) for predicate in predicates):
            survivors.append(key)
    return survivors, predicates


def apply_s2(item: dict[str, Any], *, tie: str = "lower-central", rng: Any | None = None) -> ChannelResult:
    keys = choice_keys(item)
    chance_k = format_chance_k(item)
    if not keys or chance_k is None:
        return ChannelResult(None, None, False, "s2", {"reason": "no choices"})
    survivors, predicates = s2_survivors(item)
    key_survives = str(item.get("key")) in survivors
    extra = {
        "nSurvivors": len(survivors),
        "nConstraints": len(predicates),
        "keywordMatched": len(predicates) > 0,
        "keySurvives": key_survives,
        "exactlyOneSurvivor": len(survivors) == 1,
        "eliminated": len(survivors) < len(keys),
    }
    if not survivors:
        return ChannelResult(None, None, False, "s2", extra)
    chance = 1.0 / len(survivors)
    parsed_survivors = [
        (key, parse_option_number(str((item.get("choices") or {}).get(key, ""))))
        for key in survivors
    ]
    numeric_survivors = [(key, value) for key, value in parsed_survivors if value is not None]
    answer: str | None
    if len(survivors) == 1:
        answer = survivors[0]
        extra["pickRule"] = "unique-survivor"
    elif len(numeric_survivors) == len(survivors) and numeric_survivors:
        if tie == "random" and rng is not None and len(numeric_survivors) >= 1:
            mid = lower_central_key(numeric_survivors)
            # random among options sharing the lower-central value, else among all survivors
            if mid is None:
                index = int(math.floor(rng.random() * len(survivors)))
                answer = survivors[index]
            else:
                mid_value = next(value for key, value in numeric_survivors if key == mid)
                tied = [key for key, value in numeric_survivors if value == mid_value]
                index = int(math.floor(rng.random() * len(tied)))
                answer = tied[index]
        else:
            answer = lower_central_key(numeric_survivors)
        extra["pickRule"] = "lower-central-survivors"
    else:
        if tie == "random" and rng is not None:
            index = int(math.floor(rng.random() * len(survivors)))
            answer = survivors[index]
        else:
            answer = survivors[0]
        extra["pickRule"] = "first-letter-survivors"
    return ChannelResult(answer, chance, answer is not None, "s2", extra)


def closure_values(
    item: dict[str, Any],
    *,
    max_depth: int = 2,
    include_geometry_extras: bool = True,
) -> dict[int, list[float]]:
    seeds = extract_stem_numbers(item)
    by_depth: dict[int, list[float]] = {0: [], 1: [], 2: []}
    seen: dict[float, float] = {}

    def add(depth: int, value: float) -> None:
        if not math.isfinite(value) or abs(value) > MAX_ABS_VALUE:
            return
        if len(seen) >= MAX_CLOSURE_VALUES:
            return
        key = round(value, 8)
        if key in seen:
            return
        seen[key] = value
        by_depth[depth].append(value)

    for seed in seeds:
        add(0, seed)
    depth0 = list(by_depth[0])

    def binary(left: float, right: float) -> list[float]:
        out = [left + right, left - right, left * right]
        if abs(right) > 1e-12:
            out.append(left / right)
        return out

    if max_depth >= 1:
        for left, right in itertools.product(depth0, depth0):
            for value in binary(left, right):
                add(1, value)
        if include_geometry_extras:
            for seed in depth0:
                add(1, seed * seed)
                if seed >= 0:
                    add(1, math.sqrt(seed))
            if GEOMETRY_RE.search(str(item.get("stem") or "")):
                for seed in depth0:
                    add(1, seed * PI)
                for left, right in itertools.product(depth0, depth0):
                    add(1, left * right / 2.0)

    if max_depth >= 2:
        depth01 = depth0 + by_depth[1]
        if len(seen) < MAX_CLOSURE_VALUES:
            for left, right in itertools.product(depth01, depth01):
                if len(seen) >= MAX_CLOSURE_VALUES:
                    break
                for value in binary(left, right):
                    add(2, value)
    return by_depth


def option_min_depths(
    item: dict[str, Any],
    *,
    max_depth: int = 2,
    include_geometry_extras: bool = True,
) -> dict[str, int]:
    by_depth = closure_values(
        item,
        max_depth=max_depth,
        include_geometry_extras=include_geometry_extras,
    )
    layers = [
        (0, by_depth[0]),
        (1, by_depth[1]),
        (2, by_depth[2]),
    ]
    depths: dict[str, int] = {}
    for key, value, _text in parsed_numeric_options(item):
        for depth, values in layers:
            if depth > max_depth:
                continue
            if any(values_match(value, candidate) for candidate in values):
                depths[key] = depth
                break
    return depths


def apply_s3(
    item: dict[str, Any],
    *,
    tie: str = "lower-central",
    rng: Any | None = None,
    max_depth: int = 2,
    include_geometry_extras: bool = True,
) -> ChannelResult:
    chance = format_chance_k(item)
    parsed = parsed_numeric_options(item)
    if chance is None:
        return ChannelResult(None, None, False, "s3", {"reason": "no choices"})
    depths = option_min_depths(
        item,
        max_depth=max_depth,
        include_geometry_extras=include_geometry_extras,
    )
    extra = {
        "nInDepth1": sum(1 for depth in depths.values() if depth <= 1),
        "nHit": len(depths),
        "uniqueDepth1": sum(1 for depth in depths.values() if depth <= 1) == 1,
        "depths": depths,
    }
    if not depths:
        return ChannelResult(None, chance, False, "s3", extra)
    min_depth = min(depths.values())
    candidates = [key for key, depth in depths.items() if depth == min_depth]
    extra["minDepth"] = min_depth
    if len(candidates) == 1:
        return ChannelResult(candidates[0], chance, True, "s3", extra)
    pairs = [
        (key, next(value for k, value, _text in parsed if k == key))
        for key in candidates
    ]
    if tie == "random" and rng is not None:
        index = int(math.floor(rng.random() * len(candidates)))
        answer = candidates[index]
    else:
        answer = lower_central_key(pairs) or sorted(candidates)[0]
    return ChannelResult(answer, chance, True, "s3", extra)


def normalize_math_text(text: str) -> str:
    replaced = (
        text.replace("×", "*")
        .replace("·", "*")
        .replace("÷", "/")
        .replace("^", "**")
        .replace("√", "sqrt")
        .replace("\u2212", "-")
        .replace("\u2013", "-")
        .replace("\u2014", "-")
        .replace("−", "-")
    )
    replaced = PI_RE.sub("pi", replaced)
    replaced = UNIT_WORD_RE.sub(" ", replaced)
    replaced = re.sub(r"(\d)\s*([A-Za-z])", r"\1*\2", replaced)
    replaced = re.sub(r"(\d)\s*\(", r"\1*(", replaced)
    replaced = re.sub(r"([A-Za-z])\s*\(", r"\1*(", replaced)
    replaced = re.sub(r"\)\s*(\d|[A-Za-z(])", r")*\1", replaced)
    return replaced


def single_letter_variables(text: str) -> set[str]:
    stripped = PI_RE.sub(" ", text)
    return {match.group(0).lower() for match in re.finditer(r"(?<![A-Za-z])[A-Za-z](?![A-Za-z])", stripped)}


@dataclass
class Equation:
    left: str
    rel: str
    right: str
    variable: str


LEAD_PROSE_RE = re.compile(
    r"^.*\b(equation|inequality|expression|formula|solve|makes|represented by)\s+",
    re.I,
)
TRAIL_PROSE_RE = re.compile(
    r"[,;:]?\s*\b(what|which|true|then|when|for|and|the|a|an|is|of|to|in|based|record)\b.*$",
    re.I,
)


def isolate_math(side: str) -> str:
    text = LEAD_PROSE_RE.sub("", side)
    text = TRAIL_PROSE_RE.sub("", text)
    return text.strip().strip("?.,;:")


def _eligible_equation_side(text: str) -> str | None:
    stripped = isolate_math(text)
    if not stripped or "{" in stripped:
        return None
    return stripped[-80:] if len(stripped) > 80 else stripped


def extract_equations(stem: str) -> list[Equation]:
    found: list[Equation] = []
    seen: set[tuple[str, str, str]] = set()
    # Overlapping 80-character windows around each relation token (prereg v1).
    for token in RELATION_TOKEN_RE.finditer(stem):
        left_raw = stem[max(0, token.start() - 80) : token.start()]
        right_raw = stem[token.end() : token.end() + 80]
        left = _eligible_equation_side(left_raw)
        right = _eligible_equation_side(right_raw)
        if left is None or right is None:
            continue
        left_bits = re.split(r"(?<=[.?!:])\s+", left)
        left = left_bits[-1].strip() if left_bits else left
        left = re.sub(r"^(?:where|if|given|and|or|for)\s+", "", left, flags=re.I)
        if not re.search(r"\d", left + " " + right):
            continue
        if not re.search(r"[\+\-*/^()]|\d[A-Za-z]|[A-Za-z]\d", left + " " + right):
            continue
        variables = single_letter_variables(left + " " + right)
        if len(variables) != 1:
            continue
        key = (left, token.group(0), right)
        if key in seen:
            continue
        seen.add(key)
        found.append(Equation(left=left, rel=token.group(0), right=right, variable=next(iter(variables))))
    if not found:
        for match in EQUATION_RE.finditer(stem):
            left = _eligible_equation_side(match.group("left")[-80:])
            right = _eligible_equation_side(match.group("right")[:80])
            if left is None or right is None:
                continue
            variables = single_letter_variables(left + " " + right)
            if len(variables) != 1:
                continue
            found.append(
                Equation(left=left, rel=match.group("rel"), right=right, variable=next(iter(variables)))
            )
    return found


def evaluate_side(expression: str, variable: str, value: float) -> float | None:
    try:
        parsed = sympy.sympify(normalize_math_text(expression), evaluate=True)
        symbol = sympy.Symbol(variable)
        # also bind uppercase/lowercase of the same letter
        mapping = {symbol: value, sympy.Symbol(variable.upper()): value, sympy.Symbol(variable.lower()): value}
        result = parsed.subs(mapping)
        numeric = complex(result.evalf())
        if abs(numeric.imag) > 1e-8:
            return None
        real = float(numeric.real)
        return real if math.isfinite(real) else None
    except (SympifyError, TypeError, ValueError, OverflowError, ZeroDivisionError, AttributeError):
        return None


def option_satisfies(equation: Equation, value: float) -> bool:
    left = evaluate_side(equation.left, equation.variable, value)
    right = evaluate_side(equation.right, equation.variable, value)
    if left is None or right is None:
        return False
    rel = equation.rel
    if rel in {"=", "=="}:
        return values_match(left, right)
    if rel in {"≠", "!="}:
        return not values_match(left, right)
    if rel in {"<", "lt"}:
        return left < right and not values_match(left, right)
    if rel in {">"}:
        return left > right and not values_match(left, right)
    if rel in {"≤", "<="}:
        return left < right or values_match(left, right)
    if rel in {"≥", ">="}:
        return left > right or values_match(left, right)
    return False


def apply_s4(item: dict[str, Any]) -> ChannelResult:
    chance = format_chance_k(item)
    stem = str(item.get("stem") or "")
    equations = extract_equations(stem)
    extra: dict[str, Any] = {
        "nEquations": len(equations),
        "equations": [
            {"left": eq.left, "rel": eq.rel, "right": eq.right, "variable": eq.variable}
            for eq in equations[:5]
        ],
    }
    if chance is None or not equations:
        return ChannelResult(None, chance, False, "s4", extra)
    choices = item.get("choices") or {}
    for equation in equations:
        hits: list[str] = []
        parsed_any = False
        for key in choice_keys(item):
            value = option_candidate_value(str(choices.get(key, "")))
            if value is None:
                continue
            left = evaluate_side(equation.left, equation.variable, value)
            right = evaluate_side(equation.right, equation.variable, value)
            if left is None or right is None:
                continue
            parsed_any = True
            if option_satisfies(equation, value):
                hits.append(key)
        if not parsed_any:
            continue
        extra["used"] = {
            "left": equation.left,
            "rel": equation.rel,
            "right": equation.right,
            "variable": equation.variable,
        }
        extra["nHits"] = len(hits)
        extra["hits"] = hits
        if len(hits) != 1:
            return ChannelResult(None, chance, False, "s4", extra)
        return ChannelResult(hits[0], chance, True, "s4", extra)
    extra["nHits"] = 0
    extra["hits"] = []
    return ChannelResult(None, chance, False, "s4", extra)


SYMPY_TRANSFORMATIONS = standard_transformations + (
    convert_xor,
    implicit_multiplication_application,
)

MINUS_TRANSLATION = str.maketrans(
    {
        "\u2212": "-",  # unicode minus
        "\u2013": "-",  # en dash
        "\u2014": "-",  # em dash
        "\u2010": "-",
        "\u2011": "-",
        "\u2012": "-",
        "\u00ad": "-",
        "\u0003": "-",  # documented Regents OCR minus (v1 hand-check)
        "−": "-",
        "–": "-",
        "—": "-",
    }
)

RELATION_TOKEN_V2_RE = re.compile(r"<=|>=|==|!=|≤|≥|≠|<|>|=")
ORDERED_PAIR_RE = re.compile(
    r"\(\s*(-?\d+(?:\.\d+)?(?:\s*/\s*-?\d+)?)\s*,\s*"
    r"(-?\d+(?:\.\d+)?(?:\s*/\s*-?\d+)?)\s*\)"
)
XY_PAIR_RE = re.compile(
    r"(?i)x\s*=\s*(-?\d+(?:\.\d+)?(?:\s*/\s*-?\d+)?)\s*,\s*"
    r"y\s*=\s*(-?\d+(?:\.\d+)?(?:\s*/\s*-?\d+)?)"
)
MATH_SIDE_RE = re.compile(r"[0-9A-Za-z]")
SUPERSCRIPT_TRANSLATION = str.maketrans({"²": "**2", "³": "**3"})
MATH_OPERATOR_CHARS = set("0123456789.+-*/^(),")
MATH_WORDS = {"pi", "sqrt", "sin", "cos", "tan", "log", "ln", "abs"}
MATH_STOPWORDS = {
    "and",
    "of",
    "the",
    "is",
    "what",
    "which",
    "if",
    "then",
    "given",
    "equation",
    "inequality",
    "solution",
    "value",
    "set",
    "this",
    "to",
    "for",
    "solve",
    "makes",
    "true",
    "when",
    "where",
    "find",
    "record",
    "based",
    "that",
    "with",
    "from",
    "into",
    "pair",
    "ordered",
}


def normalize_minus_text(text: str) -> str:
    return text.translate(MINUS_TRANSLATION)


def normalize_math_text_v2(text: str) -> str:
    replaced = normalize_minus_text(text)
    replaced = replaced.translate(SUPERSCRIPT_TRANSLATION)
    replaced = (
        replaced.replace("×", "*")
        .replace("·", "*")
        .replace("÷", "/")
        .replace("^", "**")
        .replace("√", "sqrt")
        .replace("≤", "<=")
        .replace("≥", ">=")
        .replace("≠", "!=")
    )
    replaced = PI_RE.sub("pi", replaced)
    replaced = UNIT_WORD_RE.sub(" ", replaced)
    replaced = re.sub(r"\s+", " ", replaced).strip()
    return replaced


def parse_scalar_token(text: str) -> float | None:
    cleaned = clean_numeric_text(normalize_minus_text(text))
    fraction = FRACTION_RE.match(cleaned.strip())
    if fraction:
        denom = float(fraction.group(2))
        if denom == 0:
            return None
        value = float(fraction.group(1)) / denom
        return value if math.isfinite(value) else None
    try:
        value = float(cleaned.strip())
    except ValueError:
        return parse_option_number(cleaned)
    return value if math.isfinite(value) else None


def option_candidate_pair(text: str) -> tuple[float, float] | None:
    cleaned = normalize_minus_text(text)
    matched = ORDERED_PAIR_RE.search(cleaned)
    if matched:
        left = parse_scalar_token(matched.group(1))
        right = parse_scalar_token(matched.group(2))
        if left is not None and right is not None:
            return (left, right)
    matched_xy = XY_PAIR_RE.search(cleaned)
    if matched_xy:
        left = parse_scalar_token(matched_xy.group(1))
        right = parse_scalar_token(matched_xy.group(2))
        if left is not None and right is not None:
            return (left, right)
    return None


def parse_math_expression_v2(text: str) -> Any | None:
    cleaned = normalize_math_text_v2(text)
    if not cleaned or not MATH_SIDE_RE.search(cleaned):
        return None
    try:
        return parse_expr(
            cleaned,
            transformations=SYMPY_TRANSFORMATIONS,
            evaluate=True,
        )
    except (
        SympifyError,
        SyntaxError,
        TypeError,
        ValueError,
        OverflowError,
        AttributeError,
        KeyError,
        tokenize.TokenError,
        RecursionError,
        IndexError,
    ):
        return None


def _consume_math_word(text: str, index: int, direction: int) -> tuple[str, int] | None:
    if direction < 0:
        end = index
        start = index
        while start > 0 and text[start - 1].isalpha():
            start -= 1
        word = text[start:end]
        if not word:
            return None
        return word, start
    start = index
    end = index
    while end < len(text) and text[end].isalpha():
        end += 1
    word = text[start:end]
    if not word:
        return None
    return word, end


def take_math_left(text: str) -> str:
    index = len(text)
    while index > 0:
        char = text[index - 1]
        if char.isspace() or char in MATH_OPERATOR_CHARS:
            index -= 1
            continue
        if char.isalpha():
            consumed = _consume_math_word(text, index, -1)
            if consumed is None:
                break
            word, start = consumed
            lowered = word.lower()
            if lowered in MATH_STOPWORDS:
                break
            if len(word) == 1 or lowered in MATH_WORDS:
                index = start
                continue
            break
        break
    text = text[index:].strip().strip("?.,;:")
    return re.sub(r"^[A-Za-z]\s+(?=[A-Za-z](?:\s*[+\-*/]|\s+[A-Za-z]))", "", text).strip()


def take_math_right(text: str) -> str:
    index = 0
    length = len(text)
    while index < length:
        char = text[index]
        if char == "?":
            break
        if char.isspace() or char in MATH_OPERATOR_CHARS:
            index += 1
            continue
        if char.isalpha():
            consumed = _consume_math_word(text, index, 1)
            if consumed is None:
                break
            word, end = consumed
            lowered = word.lower()
            if lowered in MATH_STOPWORDS:
                break
            if len(word) == 1 or lowered in MATH_WORDS:
                index = end
                continue
            break
        break
    return text[:index].strip().strip("?.,;:")


def extract_equations_v2(stem: str) -> list[Equation]:
    normalized = normalize_minus_text(stem)
    found: list[Equation] = []
    seen: set[tuple[str, str, str]] = set()
    chunks = [normalized] + [chunk.strip() for chunk in re.split(r"\band\b", normalized, flags=re.I)]
    for chunk in chunks:
        if not chunk:
            continue
        for token in RELATION_TOKEN_V2_RE.finditer(chunk):
            rel = token.group(0)
            if rel == "==":
                rel = "="
            left = take_math_left(chunk[: token.start()])
            right = take_math_right(chunk[token.end() :])
            if not left or not right or "{" in left or "{" in right:
                continue
            if not re.search(r"\d", left + " " + right):
                continue
            if parse_math_expression_v2(left) is None or parse_math_expression_v2(right) is None:
                continue
            variables = single_letter_variables(normalize_math_text_v2(left + " " + right))
            if len(variables) == 0 or len(variables) > 2:
                continue
            key = (left, rel, right)
            if key in seen:
                continue
            seen.add(key)
            variable = "x" if "x" in variables else sorted(variables)[0]
            found.append(Equation(left=left, rel=rel, right=right, variable=variable))
    return found


def equation_variables(equation: Equation) -> set[str]:
    return single_letter_variables(normalize_math_text_v2(equation.left + " " + equation.right))


def evaluate_side_v2(expression: str, mapping: dict[str, float]) -> float | None:
    parsed = parse_math_expression_v2(expression)
    if parsed is None:
        return None
    try:
        bound: dict[Any, float] = {}
        for name, value in mapping.items():
            bound[sympy.Symbol(name)] = value
            bound[sympy.Symbol(name.upper())] = value
            bound[sympy.Symbol(name.lower())] = value
        result = parsed.subs(bound)
        numeric = complex(result.evalf())
        if abs(numeric.imag) > 1e-8:
            return None
        real = float(numeric.real)
        return real if math.isfinite(real) else None
    except (
        SympifyError,
        TypeError,
        ValueError,
        OverflowError,
        ZeroDivisionError,
        AttributeError,
        KeyError,
    ):
        return None


def relation_holds(rel: str, left: float, right: float) -> bool:
    if rel in {"=", "=="}:
        return values_match(left, right)
    if rel in {"≠", "!="}:
        return not values_match(left, right)
    if rel in {"<", "lt"}:
        return left < right and not values_match(left, right)
    if rel in {">"}:
        return left > right and not values_match(left, right)
    if rel in {"≤", "<="}:
        return left < right or values_match(left, right)
    if rel in {"≥", ">="}:
        return left > right or values_match(left, right)
    return False


def option_satisfies_v2(equation: Equation, mapping: dict[str, float]) -> bool:
    left = evaluate_side_v2(equation.left, mapping)
    right = evaluate_side_v2(equation.right, mapping)
    if left is None or right is None:
        return False
    return relation_holds(equation.rel, left, right)


def pair_variable_order(variables: set[str]) -> list[str] | None:
    if len(variables) != 2:
        return None
    if variables == {"x", "y"}:
        return ["x", "y"]
    if variables == {"a", "b"}:
        return ["a", "b"]
    return sorted(variables)


def apply_s4_v2(item: dict[str, Any]) -> ChannelResult:
    chance = format_chance_k(item)
    stem = str(item.get("stem") or "")
    equations = extract_equations_v2(stem)
    extra: dict[str, Any] = {
        "nEquations": len(equations),
        "equations": [
            {
                "left": eq.left,
                "rel": eq.rel,
                "right": eq.right,
                "variable": eq.variable,
                "variables": sorted(equation_variables(eq)),
            }
            for eq in equations[:8]
        ],
        "version": 2,
    }
    if chance is None or not equations:
        return ChannelResult(None, chance, False, "s4", extra)
    choices = item.get("choices") or {}
    keys = choice_keys(item)
    scalars: dict[str, float] = {}
    pairs: dict[str, tuple[float, float]] = {}
    for key in keys:
        text = str(choices.get(key, ""))
        pair = option_candidate_pair(text)
        if pair is not None:
            pairs[key] = pair
        value = option_candidate_value(text)
        if value is not None:
            scalars[key] = value

    one_var_equations = [eq for eq in equations if len(equation_variables(eq)) == 1]
    two_var_equations = [eq for eq in equations if len(equation_variables(eq)) == 2]

    def record_unique(hits: list[str], used: dict[str, Any], parsed_any: bool) -> ChannelResult | None:
        extra["used"] = used
        extra["nHits"] = len(hits)
        extra["hits"] = hits
        extra["parsedAny"] = parsed_any
        if not parsed_any:
            return None
        if len(hits) != 1:
            return ChannelResult(None, chance, False, "s4", extra)
        return ChannelResult(hits[0], chance, True, "s4", extra)

    if one_var_equations and scalars:
        for equation in one_var_equations:
            variable = next(iter(equation_variables(equation)))
            hits: list[str] = []
            parsed_any = False
            for key, value in scalars.items():
                left = evaluate_side_v2(equation.left, {variable: value})
                right = evaluate_side_v2(equation.right, {variable: value})
                if left is None or right is None:
                    continue
                parsed_any = True
                if option_satisfies_v2(equation, {variable: value}):
                    hits.append(key)
            result = record_unique(
                hits,
                {
                    "left": equation.left,
                    "rel": equation.rel,
                    "right": equation.right,
                    "variable": variable,
                    "kind": "scalar",
                },
                parsed_any,
            )
            if result is not None:
                return result
            if parsed_any:
                return ChannelResult(None, chance, False, "s4", extra)

    system = two_var_equations
    if len(one_var_equations) >= 2:
        joined_vars: set[str] = set()
        for equation in one_var_equations:
            joined_vars |= equation_variables(equation)
        if len(joined_vars) == 2:
            system = one_var_equations + two_var_equations
    if system and pairs:
        variables: set[str] = set()
        for equation in system:
            variables |= equation_variables(equation)
        order = pair_variable_order(variables)
        if order is not None:
            hits = []
            parsed_any = False
            for key, pair in pairs.items():
                mapping = {order[0]: pair[0], order[1]: pair[1]}
                ok = True
                evaluated = 0
                for equation in system:
                    left = evaluate_side_v2(equation.left, mapping)
                    right = evaluate_side_v2(equation.right, mapping)
                    if left is None or right is None:
                        ok = False
                        break
                    evaluated += 1
                    if not option_satisfies_v2(equation, mapping):
                        ok = False
                        break
                if evaluated == 0:
                    continue
                parsed_any = True
                if ok:
                    hits.append(key)
            result = record_unique(
                hits,
                {
                    "equations": [
                        {"left": eq.left, "rel": eq.rel, "right": eq.right, "variable": eq.variable}
                        for eq in system[:4]
                    ],
                    "variables": order,
                    "kind": "system" if len(system) >= 2 else "pair",
                },
                parsed_any,
            )
            if result is not None:
                return result
            if parsed_any:
                return ChannelResult(None, chance, False, "s4", extra)

    extra["nHits"] = 0
    extra["hits"] = []
    return ChannelResult(None, chance, False, "s4", extra)


def is_solving_item(item: dict[str, Any]) -> bool:
    authority = str(item.get("authority"))
    claim = str(item.get("claim"))
    if (authority, claim) in SOLVING_CELLS:
        return True
    if authority == "teks" and str(item.get("officialTag") or "") in TEKS_SOLVE_TAGS:
        return True
    if authority == "timss" and re.search(r"algebra", str(item.get("contentDomain") or ""), re.I):
        return True
    return False


def letter_b(item: dict[str, Any]) -> str:
    keys = choice_keys(item)
    if "B" in keys:
        return "B"
    return keys[0]


def apply_s5(
    item: dict[str, Any],
    *,
    branch_order: tuple[str, ...] | list[str] | None = None,
    rng: Any | None = None,
    s1_edges: dict[str, dict[str, set[str]]] | None = None,
) -> ChannelResult:
    chance_k = format_chance_k(item)
    keys = choice_keys(item)
    if chance_k is None or not keys:
        return ChannelResult(None, None, False, "s5", {"reason": "no choices"})
    order = list(branch_order or S5_BRANCHES)
    tie = "random" if rng is not None else "lower-central"

    s4 = apply_s4(item)
    s3 = apply_s3(item, tie=tie, rng=rng)
    s2 = apply_s2(item, tie=tie, rng=rng)
    survivors = s2_survivors(item)[0] if s2.extra.get("nSurvivors", 0) or s2.fired else choice_keys(item)
    if not survivors:
        survivors = keys

    unique_depth1 = None
    if s3.extra.get("uniqueDepth1"):
        unique_depth1 = next(
            (key for key, depth in (s3.extra.get("depths") or {}).items() if depth <= 1),
            None,
        )

    survivor_item = {
        **item,
        "choices": {key: (item.get("choices") or {}).get(key) for key in survivors},
    }
    s1_on_survivors = apply_s1(
        survivor_item,
        tie=tie,
        rng=rng,
        edges_by_transform=s1_edges,
    )
    unique_hub = s1_on_survivors.answer if s1_on_survivors.extra.get("uniqueHub") else None

    numeric_survivors = [
        (key, parse_option_number(str((item.get("choices") or {}).get(key, ""))))
        for key in survivors
    ]
    numeric_pairs = [(key, value) for key, value in numeric_survivors if value is not None]
    lower = lower_central_key(numeric_pairs) if numeric_pairs else None
    if lower is None:
        lower = survivors[0]

    for branch in order:
        if branch == "s4_unique" and s4.fired and s4.answer:
            return ChannelResult(s4.answer, chance_k, True, "s5", {"usedBranch": "s4_unique", "chanceK": chance_k})
        if branch == "s3_depth1_unique" and unique_depth1:
            return ChannelResult(
                unique_depth1,
                chance_k,
                True,
                "s5",
                {"usedBranch": "s3_depth1_unique", "chanceK": chance_k},
            )
        if branch == "s2_s1_unique_hub" and unique_hub:
            chance = 1.0 / len(survivors)
            return ChannelResult(
                unique_hub,
                chance,
                True,
                "s5",
                {"usedBranch": "s2_s1_unique_hub", "chanceK": chance_k, "nSurvivors": len(survivors)},
            )
        if branch == "lower_central_survivors":
            chance = 1.0 / len(survivors)
            if rng is not None and numeric_pairs:
                mid = lower_central_key(numeric_pairs)
                if mid is not None:
                    mid_value = next(value for key, value in numeric_pairs if key == mid)
                    tied = [key for key, value in numeric_pairs if value == mid_value]
                    index = int(math.floor(rng.random() * len(tied)))
                    picked = tied[index]
                else:
                    index = int(math.floor(rng.random() * len(survivors)))
                    picked = survivors[index]
            else:
                picked = lower
            return ChannelResult(
                picked,
                chance,
                True,
                "s5",
                {"usedBranch": "lower_central_survivors", "chanceK": chance_k, "nSurvivors": len(survivors)},
            )
        if branch == "letter_B":
            return ChannelResult(
                letter_b(item),
                chance_k,
                True,
                "s5",
                {"usedBranch": "letter_B", "chanceK": chance_k},
            )
    return ChannelResult(letter_b(item), chance_k, True, "s5", {"usedBranch": "letter_B", "chanceK": chance_k})


def constraint_keyword_matched(item: dict[str, Any]) -> bool:
    return len(stem_constraint_predicates(item)) > 0


def s5_from_precomputed(
    item: dict[str, Any],
    *,
    s4_unique: str | None,
    s3_depth1_unique: str | None,
    survivors: list[str],
    unique_hub: str | None,
    lower_central: str | None,
    branch_order: tuple[str, ...] | list[str] | None = None,
    rng: Any | None = None,
    numeric_pairs: list[tuple[str, float]] | None = None,
) -> ChannelResult:
    chance_k = format_chance_k(item)
    keys = choice_keys(item)
    if chance_k is None or not keys:
        return ChannelResult(None, None, False, "s5", {"reason": "no choices"})
    remaining = survivors if survivors else keys
    lower = lower_central or remaining[0]
    pairs = numeric_pairs or []
    for branch in list(branch_order or S5_BRANCHES):
        if branch == "s4_unique" and s4_unique:
            return ChannelResult(s4_unique, chance_k, True, "s5", {"usedBranch": "s4_unique", "chanceK": chance_k})
        if branch == "s3_depth1_unique" and s3_depth1_unique:
            return ChannelResult(
                s3_depth1_unique,
                chance_k,
                True,
                "s5",
                {"usedBranch": "s3_depth1_unique", "chanceK": chance_k},
            )
        if branch == "s2_s1_unique_hub" and unique_hub:
            chance = 1.0 / len(remaining)
            return ChannelResult(
                unique_hub,
                chance,
                True,
                "s5",
                {"usedBranch": "s2_s1_unique_hub", "chanceK": chance_k, "nSurvivors": len(remaining)},
            )
        if branch == "lower_central_survivors":
            chance = 1.0 / len(remaining)
            if rng is not None and pairs:
                mid = lower_central_key(pairs)
                if mid is not None:
                    mid_value = next(value for key, value in pairs if key == mid)
                    tied = [key for key, value in pairs if value == mid_value]
                    index = int(math.floor(rng.random() * len(tied)))
                    picked = tied[index]
                else:
                    index = int(math.floor(rng.random() * len(remaining)))
                    picked = remaining[index]
            elif rng is not None:
                index = int(math.floor(rng.random() * len(remaining)))
                picked = remaining[index]
            else:
                picked = lower
            return ChannelResult(
                picked,
                chance,
                True,
                "s5",
                {"usedBranch": "lower_central_survivors", "chanceK": chance_k, "nSurvivors": len(remaining)},
            )
        if branch == "letter_B":
            return ChannelResult(
                letter_b(item),
                chance_k,
                True,
                "s5",
                {"usedBranch": "letter_B", "chanceK": chance_k},
            )
    return ChannelResult(letter_b(item), chance_k, True, "s5", {"usedBranch": "letter_B", "chanceK": chance_k})

