#!/usr/bin/env python3
"""Replace option numerals with form-preserving isomorphs (seed 20260916)."""

from __future__ import annotations

import hashlib
import json
import random
import sys
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

from score_choices_only_local_lm import load_items  # noqa: E402

OUT_DIR = ROOT / "exports" / "isomorph-options"
PREREG_PATH = OUT_DIR / "preregistration.md"
PREREG_SHA_PATH = OUT_DIR / "preregistration.sha256"
ALGEBRA_IDS_PATH = ROOT / "exports" / "addendum-gpu" / "masked-stem-algebra-primary-item-ids.json"
SEED = 20260916
ARM_PRESERVING = "isomorph_rank_preserving"
ARM_SCRAMBLED = "isomorph_rank_scrambled"
ARMS = (ARM_PRESERVING, ARM_SCRAMBLED)
SIGN_CHARS = frozenset("-−–")
MAX_SAMPLE_ATTEMPTS = 20000
MAX_LEADING_TUPLE_ATTEMPTS = 50000
EXAMPLE_IDS = (
    "nyregents-algebra-i-2016-jun-q7",
    "nyregents-algebra-i-2018-jun-q1",
    "nyregents-algebra-i-2018-jun-q6",
    "nyregents-algebra-i-2015-jan-q8",
    "nyregents-algebra-i-2017-jan-q8",
)


@dataclass(frozen=True)
class NumeralSpan:
    start: int
    end: int
    kind: str
    text: str
    value: Decimal
    negative: bool
    sign_char: str | None
    digit_count: int
    decimal_places: int | None
    leading_dot: bool
    integer_digits: int | None
    numerator_text: str | None
    denominator_text: str | None
    numerator_value: int | None
    denominator_value: int | None
    slash_text: str | None


@dataclass(frozen=True)
class AtomicForm:
    kind: str
    text: str
    value: Decimal
    negative: bool
    sign_char: str | None
    digit_count: int
    decimal_places: int | None
    leading_dot: bool
    integer_digits: int | None


def check_preregistration() -> str:
    if not PREREG_PATH.exists():
        raise RuntimeError(f"preregistration missing: {PREREG_PATH}")
    if not PREREG_SHA_PATH.exists():
        raise RuntimeError(f"preregistration sha256 missing: {PREREG_SHA_PATH}")
    recorded = PREREG_SHA_PATH.read_text(encoding="utf-8").split()[0]
    actual = hashlib.sha256(PREREG_PATH.read_bytes()).hexdigest()
    if recorded != actual:
        raise RuntimeError(
            f"preregistration.md sha256 {actual} does not match recorded {recorded}"
        )
    return recorded


def rng_for(item_id: str, arm: str) -> random.Random:
    digest = hashlib.sha256(f"{SEED}:{arm}:{item_id}".encode("utf-8")).hexdigest()
    return random.Random(int(digest[:16], 16))


def previous_allows_sign(text: str, index: int) -> bool:
    if index == 0:
        return True
    previous = text[index - 1]
    return not (previous.isalnum() or previous == ".")


def is_digit(character: str) -> bool:
    return "0" <= character <= "9"


def signed_value(magnitude: Decimal, negative: bool) -> Decimal:
    return -magnitude if negative else magnitude


def make_integer(
    start: int,
    end: int,
    text: str,
    digits: str,
    negative: bool,
    sign_char: str | None,
) -> NumeralSpan:
    magnitude = int(digits)
    value = Decimal(-magnitude if negative else magnitude)
    return NumeralSpan(
        start=start,
        end=end,
        kind="integer",
        text=text,
        value=value,
        negative=negative,
        sign_char=sign_char,
        digit_count=len(digits),
        decimal_places=None,
        leading_dot=False,
        integer_digits=len(digits),
        numerator_text=None,
        denominator_text=None,
        numerator_value=None,
        denominator_value=None,
        slash_text=None,
    )


def make_comma_integer(
    start: int,
    end: int,
    text: str,
    digits: str,
    negative: bool,
    sign_char: str | None,
) -> NumeralSpan:
    magnitude = int(digits)
    value = Decimal(-magnitude if negative else magnitude)
    return NumeralSpan(
        start=start,
        end=end,
        kind="comma_integer",
        text=text,
        value=value,
        negative=negative,
        sign_char=sign_char,
        digit_count=len(digits),
        decimal_places=None,
        leading_dot=False,
        integer_digits=len(digits),
        numerator_text=None,
        denominator_text=None,
        numerator_value=None,
        denominator_value=None,
        slash_text=None,
    )


def make_decimal(
    start: int,
    end: int,
    text: str,
    integer_digits_text: str,
    fraction_digits: str,
    leading_dot: bool,
    negative: bool,
    sign_char: str | None,
) -> NumeralSpan:
    if leading_dot:
        magnitude = Decimal(fraction_digits) / (Decimal(10) ** len(fraction_digits))
        integer_digits = 0
    else:
        whole = integer_digits_text if integer_digits_text else "0"
        magnitude = Decimal(whole + "." + fraction_digits)
        integer_digits = len(integer_digits_text)
    value = signed_value(magnitude, negative)
    return NumeralSpan(
        start=start,
        end=end,
        kind="decimal",
        text=text,
        value=value,
        negative=negative,
        sign_char=sign_char,
        digit_count=integer_digits + len(fraction_digits),
        decimal_places=len(fraction_digits),
        leading_dot=leading_dot,
        integer_digits=integer_digits,
        numerator_text=None,
        denominator_text=None,
        numerator_value=None,
        denominator_value=None,
        slash_text=None,
    )


def make_fraction(
    start: int,
    end: int,
    text: str,
    numerator_text: str,
    denominator_text: str,
    numerator_value: int,
    denominator_value: int,
    slash_text: str,
    negative: bool,
    sign_char: str | None,
) -> NumeralSpan:
    if denominator_value == 0:
        raise RuntimeError(f"fraction with zero denominator: {text!r}")
    value = Decimal(numerator_value) / Decimal(denominator_value)
    return NumeralSpan(
        start=start,
        end=end,
        kind="fraction",
        text=text,
        value=value,
        negative=negative,
        sign_char=sign_char,
        digit_count=len(numerator_text.lstrip("".join(SIGN_CHARS))),
        decimal_places=None,
        leading_dot=False,
        integer_digits=None,
        numerator_text=numerator_text,
        denominator_text=denominator_text,
        numerator_value=numerator_value,
        denominator_value=denominator_value,
        slash_text=slash_text,
    )


def read_digits(text: str, index: int) -> tuple[str, int]:
    start = index
    while index < len(text) and is_digit(text[index]):
        index += 1
    return text[start:index], index


def find_numerals(text: str) -> list[NumeralSpan]:
    spans: list[NumeralSpan] = []
    index = 0
    length = len(text)
    while index < length:
        sign_char: str | None = None
        sign_start = index
        if text[index] in SIGN_CHARS and previous_allows_sign(text, index):
            next_index = index + 1
            if next_index < length and (
                is_digit(text[next_index])
                or (
                    text[next_index] == "."
                    and next_index + 1 < length
                    and is_digit(text[next_index + 1])
                )
            ):
                sign_char = text[index]
                index = next_index
        if index >= length:
            break
        token_start = sign_start if sign_char is not None else index
        if text[index] == "." and index + 1 < length and is_digit(text[index + 1]):
            fraction_digits, index = read_digits(text, index + 1)
            raw = text[token_start:index]
            spans.append(
                make_decimal(
                    start=token_start,
                    end=index,
                    text=raw,
                    integer_digits_text="",
                    fraction_digits=fraction_digits,
                    leading_dot=True,
                    negative=sign_char is not None,
                    sign_char=sign_char,
                )
            )
            continue
        if not is_digit(text[index]):
            index = sign_start + 1 if sign_char is not None else index + 1
            continue
        integer_digits_text, index = read_digits(text, index)
        if index < length and text[index] == ",":
            trial = index
            groups = 0
            grouped_digits = integer_digits_text
            comma_ok = True
            while trial < length and text[trial] == ",":
                trial += 1
                group, trial = read_digits(text, trial)
                if len(group) != 3:
                    comma_ok = False
                    break
                grouped_digits += group
                groups += 1
            continues_as_decimal = (
                comma_ok
                and trial < length
                and text[trial] == "."
                and trial + 1 < length
                and is_digit(text[trial + 1])
            )
            if comma_ok and groups >= 1 and not continues_as_decimal:
                index = trial
                raw = text[token_start:index]
                spans.append(
                    make_comma_integer(
                        start=token_start,
                        end=index,
                        text=raw,
                        digits=grouped_digits,
                        negative=sign_char is not None,
                        sign_char=sign_char,
                    )
                )
                continue
        if (
            index < length
            and text[index] == "."
            and index + 1 < length
            and is_digit(text[index + 1])
        ):
            fraction_digits, index = read_digits(text, index + 1)
            raw = text[token_start:index]
            spans.append(
                make_decimal(
                    start=token_start,
                    end=index,
                    text=raw,
                    integer_digits_text=integer_digits_text,
                    fraction_digits=fraction_digits,
                    leading_dot=False,
                    negative=sign_char is not None,
                    sign_char=sign_char,
                )
            )
            continue
        cursor = index
        while cursor < length and text[cursor] in " \t":
            cursor += 1
        if cursor < length and text[cursor] == "/":
            slash_start = index
            cursor += 1
            while cursor < length and text[cursor] in " \t":
                cursor += 1
            denominator_sign_char: str | None = None
            denominator_sign_start = cursor
            if cursor < length and text[cursor] in SIGN_CHARS:
                if cursor + 1 < length and is_digit(text[cursor + 1]):
                    denominator_sign_char = text[cursor]
                    cursor += 1
            if cursor < length and is_digit(text[cursor]):
                denominator_digits, after_den = read_digits(text, cursor)
                den_is_decimal = (
                    after_den < length
                    and text[after_den] == "."
                    and after_den + 1 < length
                    and is_digit(text[after_den + 1])
                )
                if not den_is_decimal:
                    numerator_text = text[token_start:index]
                    denominator_text = text[denominator_sign_start:after_den]
                    numerator_value = int(integer_digits_text)
                    if sign_char is not None:
                        numerator_value = -numerator_value
                    denominator_value = int(denominator_digits)
                    if denominator_sign_char is not None:
                        denominator_value = -denominator_value
                    raw = text[token_start:after_den]
                    spans.append(
                        make_fraction(
                            start=token_start,
                            end=after_den,
                            text=raw,
                            numerator_text=numerator_text,
                            denominator_text=denominator_text,
                            numerator_value=numerator_value,
                            denominator_value=denominator_value,
                            slash_text=text[slash_start:denominator_sign_start],
                            negative=numerator_value < 0,
                            sign_char=sign_char,
                        )
                    )
                    index = after_den
                    continue
        raw = text[token_start:index]
        spans.append(
            make_integer(
                start=token_start,
                end=index,
                text=raw,
                digits=integer_digits_text,
                negative=sign_char is not None,
                sign_char=sign_char,
            )
        )
    return spans


def uncovered_digit_indices(text: str, spans: list[NumeralSpan]) -> list[int]:
    covered = [False] * len(text)
    for span in spans:
        for index in range(span.start, span.end):
            covered[index] = True
    return [
        index
        for index, character in enumerate(text)
        if is_digit(character) and not covered[index]
    ]


def format_signed_integer(value: int, sign_char: str | None) -> str:
    if value < 0:
        prefix = sign_char if sign_char is not None else "-"
        return f"{prefix}{abs(value)}"
    return str(value)


def format_comma_integer(value: int, sign_char: str | None) -> str:
    body = f"{abs(value):,}"
    if value < 0:
        prefix = sign_char if sign_char is not None else "-"
        return prefix + body
    return body


def integer_bounds(digit_count: int, negative: bool) -> tuple[int, int]:
    if digit_count < 1:
        raise RuntimeError(f"digit count must be >= 1, got {digit_count}")
    if negative:
        if digit_count == 1:
            return (-9, -1)
        high = 10 ** digit_count - 1
        low = 10 ** (digit_count - 1)
        return (-high, -low)
    if digit_count == 1:
        return (0, 9)
    low = 10 ** (digit_count - 1)
    high = 10 ** digit_count - 1
    return (low, high)


def sample_integer_value(
    rng: random.Random,
    original: int,
    digit_count: int,
    negative: bool,
    forbidden_values: set[int],
    nonzero: bool,
) -> int:
    low, high = integer_bounds(digit_count, negative)
    blocked = set(forbidden_values)
    blocked.add(original)
    if nonzero:
        blocked.add(0)
    span = high - low + 1
    if span <= 64:
        candidates = [value for value in range(low, high + 1) if value not in blocked]
        if not candidates:
            candidates = [
                value
                for value in range(low, high + 1)
                if value != original and (not nonzero or value != 0)
            ]
        if not candidates:
            raise RuntimeError(
                f"no integer candidate digit_count={digit_count} negative={negative} original={original}"
            )
        return candidates[rng.randrange(len(candidates))]
    for _ in range(MAX_SAMPLE_ATTEMPTS):
        sampled = rng.randint(low, high)
        if sampled in blocked:
            continue
        return sampled
    for _ in range(MAX_SAMPLE_ATTEMPTS):
        sampled = rng.randint(low, high)
        if sampled == original or (nonzero and sampled == 0):
            continue
        return sampled
    raise RuntimeError(
        f"no integer candidate digit_count={digit_count} negative={negative} original={original}"
    )


def atomic_form_from_span(span: NumeralSpan) -> AtomicForm:
    if span.kind == "fraction":
        raise RuntimeError("fraction spans are not a single atomic form")
    return AtomicForm(
        kind=span.kind,
        text=span.text,
        value=span.value,
        negative=span.negative,
        sign_char=span.sign_char,
        digit_count=span.digit_count,
        decimal_places=span.decimal_places,
        leading_dot=span.leading_dot,
        integer_digits=span.integer_digits,
    )


def integer_form_from_text(text: str, value: int) -> AtomicForm:
    sign_char = text[0] if text and text[0] in SIGN_CHARS else None
    digits = text[1:] if sign_char is not None else text
    return AtomicForm(
        kind="integer",
        text=text,
        value=Decimal(value),
        negative=value < 0,
        sign_char=sign_char,
        digit_count=len(digits),
        decimal_places=None,
        leading_dot=False,
        integer_digits=len(digits),
    )


def collect_atomic_forms(spans: list[NumeralSpan]) -> dict[str, AtomicForm]:
    forms: dict[str, AtomicForm] = {}
    for span in spans:
        if span.kind == "fraction":
            if span.numerator_text is None or span.numerator_value is None:
                raise RuntimeError("fraction missing numerator")
            if span.denominator_text is None or span.denominator_value is None:
                raise RuntimeError("fraction missing denominator")
            if span.numerator_text not in forms:
                forms[span.numerator_text] = integer_form_from_text(
                    span.numerator_text, span.numerator_value
                )
            if span.denominator_text not in forms:
                forms[span.denominator_text] = integer_form_from_text(
                    span.denominator_text, span.denominator_value
                )
            continue
        if span.text not in forms:
            forms[span.text] = atomic_form_from_span(span)
    return forms


def sample_decimal_text(
    rng: random.Random,
    form: AtomicForm,
    forbidden_texts: set[str],
    forbidden_values: set[Decimal],
) -> tuple[str, Decimal]:
    if form.decimal_places is None:
        raise RuntimeError("decimal form missing places")
    places = form.decimal_places
    scale = 10 ** places
    for _ in range(MAX_SAMPLE_ATTEMPTS):
        if form.leading_dot:
            fraction = rng.randrange(0, scale)
            magnitude = Decimal(fraction) / Decimal(scale)
            text_body = f".{fraction:0{places}d}"
        else:
            if form.integer_digits is None:
                raise RuntimeError("decimal form missing integer digits")
            if form.integer_digits == 0:
                raise RuntimeError("non-leading-dot decimal with 0 integer digits")
            if form.integer_digits == 1:
                integer_part = rng.randrange(0, 10)
            else:
                low = 10 ** (form.integer_digits - 1)
                high = 10 ** form.integer_digits - 1
                integer_part = rng.randint(low, high)
            fraction = rng.randrange(0, scale)
            magnitude = Decimal(integer_part) + (Decimal(fraction) / Decimal(scale))
            text_body = f"{integer_part}.{fraction:0{places}d}"
        value = signed_value(magnitude, form.negative)
        text = (
            f"{form.sign_char}{text_body}"
            if form.negative and form.sign_char is not None
            else (
                f"-{text_body}"
                if form.negative
                else text_body
            )
        )
        if text == form.text or value == form.value:
            continue
        if text in forbidden_texts or value in forbidden_values:
            continue
        return text, value
    raise RuntimeError(f"could not sample decimal for {form.text!r}")


def sample_atomic(
    rng: random.Random,
    form: AtomicForm,
    forbidden_texts: set[str],
    forbidden_int_values: set[int],
    forbidden_dec_values: set[Decimal],
    nonzero: bool,
) -> tuple[str, Decimal]:
    if form.kind in ("integer", "comma_integer"):
        original = int(form.value)
        blocked_ints = set(forbidden_int_values)
        for _ in range(MAX_SAMPLE_ATTEMPTS):
            sampled = sample_integer_value(
                rng,
                original=original,
                digit_count=form.digit_count,
                negative=form.negative,
                forbidden_values=blocked_ints,
                nonzero=nonzero,
            )
            text = (
                format_comma_integer(sampled, form.sign_char)
                if form.kind == "comma_integer"
                else format_signed_integer(sampled, form.sign_char)
            )
            if text in forbidden_texts or text == form.text:
                blocked_ints.add(sampled)
                continue
            return text, Decimal(sampled)
        raise RuntimeError(f"could not sample integer for {form.text!r}")
    if form.kind == "decimal":
        return sample_decimal_text(rng, form, forbidden_texts, forbidden_dec_values)
    raise RuntimeError(f"unknown atomic kind {form.kind}")


def sample_fraction_pair(
    rng: random.Random,
    span: NumeralSpan,
    atomic_map: dict[str, str],
    forbidden_texts: set[str],
    forbidden_int_values: set[int],
) -> dict[str, str]:
    if span.numerator_text is None or span.denominator_text is None:
        raise RuntimeError("fraction missing parts")
    if span.numerator_value is None or span.denominator_value is None:
        raise RuntimeError("fraction missing values")
    num_form = integer_form_from_text(span.numerator_text, span.numerator_value)
    den_form = integer_form_from_text(span.denominator_text, span.denominator_value)
    for _ in range(MAX_SAMPLE_ATTEMPTS):
        proposed: dict[str, str] = {}
        local_forbidden_texts = set(forbidden_texts)
        local_forbidden_ints = set(forbidden_int_values)
        if span.numerator_text in atomic_map:
            new_num_text = atomic_map[span.numerator_text]
            new_num = int(
                new_num_text[1:] if new_num_text[:1] in SIGN_CHARS else new_num_text
            )
            if new_num_text[:1] in SIGN_CHARS:
                new_num = -new_num
        else:
            new_num_text, new_num_dec = sample_atomic(
                rng,
                num_form,
                local_forbidden_texts,
                local_forbidden_ints,
                set(),
                nonzero=False,
            )
            new_num = int(new_num_dec)
            proposed[span.numerator_text] = new_num_text
            local_forbidden_texts.add(new_num_text)
            local_forbidden_ints.add(new_num)
        if span.denominator_text in atomic_map:
            new_den_text = atomic_map[span.denominator_text]
            new_den = int(
                new_den_text[1:] if new_den_text[:1] in SIGN_CHARS else new_den_text
            )
            if new_den_text[:1] in SIGN_CHARS:
                new_den = -new_den
        else:
            new_den_text, new_den_dec = sample_atomic(
                rng,
                den_form,
                local_forbidden_texts,
                local_forbidden_ints,
                set(),
                nonzero=True,
            )
            new_den = int(new_den_dec)
            if new_den == 0:
                continue
            proposed[span.denominator_text] = new_den_text
        if new_den == 0:
            continue
        new_value = Decimal(new_num) / Decimal(new_den)
        if new_value == span.value:
            continue
        return proposed
    raise RuntimeError(f"could not sample fraction for {span.text!r}")


def leading_value_after_map(span: NumeralSpan, atomic_map: dict[str, str]) -> Decimal:
    if span.kind == "fraction":
        if span.numerator_text is None or span.denominator_text is None:
            raise RuntimeError("fraction missing parts")
        new_num_text = atomic_map[span.numerator_text]
        new_den_text = atomic_map[span.denominator_text]
        new_num = int(new_num_text[1:] if new_num_text[:1] in SIGN_CHARS else new_num_text)
        if new_num_text[:1] in SIGN_CHARS:
            new_num = -new_num
        new_den = int(new_den_text[1:] if new_den_text[:1] in SIGN_CHARS else new_den_text)
        if new_den_text[:1] in SIGN_CHARS:
            new_den = -new_den
        if new_den == 0:
            raise RuntimeError("mapped fraction denominator is 0")
        return Decimal(new_num) / Decimal(new_den)
    new_text = atomic_map[span.text]
    parsed = find_numerals(new_text)
    if len(parsed) != 1:
        raise RuntimeError(f"replacement {new_text!r} did not parse as one numeral")
    return parsed[0].value


def pairwise_order(values: list[Decimal]) -> list[int]:
    order: list[int] = []
    for left in range(len(values)):
        for right in range(left + 1, len(values)):
            if values[left] < values[right]:
                order.append(-1)
            elif values[left] > values[right]:
                order.append(1)
            else:
                order.append(0)
    return order


def propose_leading_token(
    rng: random.Random,
    span: NumeralSpan,
    atomic_map: dict[str, str],
    forbidden_texts: set[str],
    forbidden_ints: set[int],
    forbidden_decs: set[Decimal],
) -> tuple[dict[str, str], str, Decimal | None]:
    if span.kind == "fraction":
        proposed = sample_fraction_pair(
            rng, span, atomic_map, forbidden_texts, forbidden_ints
        )
        return proposed, "fraction", None
    form = atomic_form_from_span(span)
    new_text, new_value = sample_atomic(
        rng,
        form,
        forbidden_texts,
        forbidden_ints,
        forbidden_decs,
        nonzero=False,
    )
    return {span.text: new_text}, form.kind, new_value


def rank_constraint_ok(
    original_value: Decimal,
    new_value: Decimal,
    previous_original: Decimal | None,
    previous_new: Decimal | None,
) -> bool:
    if previous_original is None or previous_new is None:
        return True
    if original_value > previous_original:
        return new_value > previous_new
    if original_value == previous_original:
        return new_value == previous_new
    return new_value < previous_new


def sample_leading_map(
    rng: random.Random,
    leadings: list[NumeralSpan],
    preserve_rank: bool,
) -> dict[str, str]:
    unique: list[NumeralSpan] = []
    seen: set[str] = set()
    for span in leadings:
        if span.text in seen:
            continue
        seen.add(span.text)
        unique.append(span)
    unique.sort(key=lambda span: (span.value, span.text))
    attempts = MAX_LEADING_TUPLE_ATTEMPTS if preserve_rank else 1
    for _ in range(attempts):
        atomic_map: dict[str, str] = {}
        forbidden_texts: set[str] = set()
        forbidden_ints: set[int] = set()
        forbidden_decs: set[Decimal] = set()
        previous_original: Decimal | None = None
        previous_new: Decimal | None = None
        failed = False
        for span in unique:
            placed = False
            for _inner in range(MAX_SAMPLE_ATTEMPTS):
                try:
                    proposed, sampled_kind, sampled_value = propose_leading_token(
                        rng,
                        span,
                        atomic_map,
                        forbidden_texts,
                        forbidden_ints,
                        forbidden_decs,
                    )
                except RuntimeError:
                    continue
                conflict = False
                for source, dest in proposed.items():
                    if source in atomic_map and atomic_map[source] != dest:
                        conflict = True
                        break
                    if dest in forbidden_texts and atomic_map.get(source) != dest:
                        conflict = True
                        break
                if conflict:
                    continue
                tentative = dict(atomic_map)
                tentative.update(proposed)
                try:
                    new_value = leading_value_after_map(span, tentative)
                except RuntimeError:
                    continue
                if preserve_rank and not rank_constraint_ok(
                    span.value, new_value, previous_original, previous_new
                ):
                    continue
                for source, dest in proposed.items():
                    atomic_map[source] = dest
                    forbidden_texts.add(dest)
                if sampled_kind in ("integer", "comma_integer") and sampled_value is not None:
                    forbidden_ints.add(int(sampled_value))
                elif sampled_kind == "decimal" and sampled_value is not None:
                    forbidden_decs.add(sampled_value)
                previous_original = span.value
                previous_new = new_value
                placed = True
                break
            if not placed:
                failed = True
                break
        if failed:
            continue
        if not preserve_rank:
            return atomic_map
        new_values = [leading_value_after_map(span, atomic_map) for span in unique]
        if pairwise_order(new_values) == pairwise_order([span.value for span in unique]):
            return atomic_map
    if not preserve_rank:
        raise RuntimeError("could not sample scrambled leading map")
    raise RuntimeError("could not sample rank-preserving leading map")


def apply_atomic_map(
    text: str, spans: list[NumeralSpan], atomic_map: dict[str, str]
) -> str:
    pieces: list[str] = []
    cursor = 0
    for span in spans:
        pieces.append(text[cursor : span.start])
        if span.kind == "fraction":
            if span.numerator_text is None or span.denominator_text is None:
                raise RuntimeError("fraction missing parts")
            if span.slash_text is None:
                raise RuntimeError("fraction missing slash text")
            new_num = atomic_map[span.numerator_text]
            new_den = atomic_map[span.denominator_text]
            pieces.append(new_num + span.slash_text + new_den)
        else:
            pieces.append(atomic_map[span.text])
        cursor = span.end
    pieces.append(text[cursor:])
    return "".join(pieces)


def complete_atomic_map(
    rng: random.Random,
    forms: dict[str, AtomicForm],
    atomic_map: dict[str, str],
) -> dict[str, str]:
    forbidden_texts = set(atomic_map.values())
    forbidden_ints: set[int] = set()
    forbidden_decs: set[Decimal] = set()
    for source, dest in atomic_map.items():
        form = forms[source]
        if form.kind in ("integer", "comma_integer"):
            parsed = find_numerals(dest)
            if len(parsed) != 1:
                raise RuntimeError(f"mapped integer {dest!r} did not parse")
            forbidden_ints.add(int(parsed[0].value))
        elif form.kind == "decimal":
            parsed = find_numerals(dest)
            if len(parsed) != 1:
                raise RuntimeError(f"mapped decimal {dest!r} did not parse")
            forbidden_decs.add(parsed[0].value)
    for source in sorted(forms):
        if source in atomic_map:
            continue
        form = forms[source]
        nonzero = False
        new_text, new_value = sample_atomic(
            rng, form, forbidden_texts, forbidden_ints, forbidden_decs, nonzero=nonzero
        )
        atomic_map[source] = new_text
        forbidden_texts.add(new_text)
        if form.kind in ("integer", "comma_integer"):
            forbidden_ints.add(int(new_value))
        else:
            forbidden_decs.add(new_value)
    return atomic_map


def leading_numbers(choices: dict[str, str]) -> dict[str, str | None]:
    out: dict[str, str | None] = {}
    for letter, text in choices.items():
        spans = find_numerals(text)
        out[letter] = str(spans[0].value) if spans else None
    return out


def rank_order_preserved(original: dict[str, str], perturbed: dict[str, str]) -> bool:
    original_values: dict[str, Decimal] = {}
    perturbed_values: dict[str, Decimal] = {}
    for letter, text in original.items():
        spans = find_numerals(text)
        if not spans:
            continue
        original_values[letter] = spans[0].value
        new_spans = find_numerals(perturbed[letter])
        if not new_spans:
            return False
        perturbed_values[letter] = new_spans[0].value
    letters = list(original_values)
    for left_index, left in enumerate(letters):
        for right in letters[left_index + 1 :]:
            old_cmp = (original_values[left] > original_values[right]) - (
                original_values[left] < original_values[right]
            )
            new_cmp = (perturbed_values[left] > perturbed_values[right]) - (
                perturbed_values[left] < perturbed_values[right]
            )
            if old_cmp != new_cmp:
                return False
    return True


def assert_form_preserved(original: dict[str, str], perturbed: dict[str, str]) -> None:
    for letter, text in original.items():
        old_spans = find_numerals(text)
        new_spans = find_numerals(perturbed[letter])
        if len(old_spans) != len(new_spans):
            raise RuntimeError(
                f"span count changed on {letter}: {len(old_spans)} -> {len(new_spans)}"
            )
        for old_span, new_span in zip(old_spans, new_spans):
            if old_span.kind != new_span.kind:
                raise RuntimeError(
                    f"kind changed on {letter}: {old_span.kind} -> {new_span.kind}"
                )
            if old_span.negative != new_span.negative:
                raise RuntimeError(f"sign changed on {letter} {old_span.text}")
            if old_span.kind in ("integer", "comma_integer"):
                if old_span.digit_count != new_span.digit_count:
                    raise RuntimeError(
                        f"digit count changed {old_span.text} -> {new_span.text}"
                    )
            if old_span.kind == "decimal":
                if old_span.decimal_places != new_span.decimal_places:
                    raise RuntimeError(
                        f"decimal places changed {old_span.text} -> {new_span.text}"
                    )
                if old_span.leading_dot != new_span.leading_dot:
                    raise RuntimeError(
                        f"leading-dot form changed {old_span.text} -> {new_span.text}"
                    )
                if old_span.integer_digits != new_span.integer_digits:
                    raise RuntimeError(
                        f"integer digits changed {old_span.text} -> {new_span.text}"
                    )
            if old_span.kind == "fraction":
                if old_span.numerator_text is None or new_span.numerator_text is None:
                    raise RuntimeError("fraction numerator missing")
                if old_span.denominator_text is None or new_span.denominator_text is None:
                    raise RuntimeError("fraction denominator missing")
                old_num_digits = len(
                    old_span.numerator_text.lstrip("".join(SIGN_CHARS))
                )
                new_num_digits = len(
                    new_span.numerator_text.lstrip("".join(SIGN_CHARS))
                )
                old_den_digits = len(
                    old_span.denominator_text.lstrip("".join(SIGN_CHARS))
                )
                new_den_digits = len(
                    new_span.denominator_text.lstrip("".join(SIGN_CHARS))
                )
                if old_num_digits != new_num_digits or old_den_digits != new_den_digits:
                    raise RuntimeError(
                        f"fraction digit counts changed {old_span.text} -> {new_span.text}"
                    )
                if new_span.denominator_value == 0:
                    raise RuntimeError("perturbed denominator is 0")
            if old_span.kind != "fraction" and old_span.value == new_span.value:
                raise RuntimeError(
                    f"value did not change for {old_span.text} -> {new_span.text}"
                )
        skeleton_old = skeleton_without_numerals(text, old_spans)
        skeleton_new = skeleton_without_numerals(perturbed[letter], new_spans)
        if skeleton_old != skeleton_new:
            raise RuntimeError(
                f"non-numeral skeleton changed on {letter}: {skeleton_old!r} vs {skeleton_new!r}"
            )


def skeleton_without_numerals(text: str, spans: list[NumeralSpan]) -> str:
    pieces: list[str] = []
    cursor = 0
    for span in spans:
        pieces.append(text[cursor : span.start])
        pieces.append("\x00")
        cursor = span.end
    pieces.append(text[cursor:])
    return "".join(pieces)


def perturb_choices(
    choices: dict[str, str],
    arm: str,
    rng: random.Random,
) -> tuple[dict[str, str], dict[str, str], bool]:
    ordered_letters = list(choices.keys())
    spans_by_letter = {letter: find_numerals(choices[letter]) for letter in ordered_letters}
    all_spans = [span for letter in ordered_letters for span in spans_by_letter[letter]]
    if not all_spans:
        return dict(choices), {}, True
    forms = collect_atomic_forms(all_spans)
    leadings = [
        spans_by_letter[letter][0]
        for letter in ordered_letters
        if spans_by_letter[letter]
    ]
    if arm == ARM_PRESERVING:
        atomic_map = sample_leading_map(rng, leadings, preserve_rank=True)
        atomic_map = complete_atomic_map(rng, forms, atomic_map)
    elif arm == ARM_SCRAMBLED:
        atomic_map = {}
        atomic_map = complete_atomic_map(rng, forms, atomic_map)
    else:
        raise RuntimeError(f"unknown arm {arm}")
    perturbed: dict[str, str] = {}
    for letter in ordered_letters:
        perturbed[letter] = apply_atomic_map(
            choices[letter], spans_by_letter[letter], atomic_map
        )
    assert_form_preserved(choices, perturbed)
    if arm == ARM_PRESERVING and not rank_order_preserved(choices, perturbed):
        raise RuntimeError("rank order was not preserved")
    for letter, text in choices.items():
        leftover = uncovered_digit_indices(text, spans_by_letter[letter])
        if leftover:
            raise RuntimeError(f"uncovered digits in {letter}: {leftover}")
        leftover_new = uncovered_digit_indices(perturbed[letter], find_numerals(perturbed[letter]))
        if leftover_new:
            raise RuntimeError(f"uncovered digits after perturb in {letter}: {leftover_new}")
    return perturbed, atomic_map, False


def load_algebra_items() -> list[dict[str, Any]]:
    item_ids = [str(item_id) for item_id in json.loads(ALGEBRA_IDS_PATH.read_text(encoding="utf-8"))]
    items_by_id = load_items()
    out: list[dict[str, Any]] = []
    for item_id in item_ids:
        item = items_by_id[item_id]
        if str(item.get("authority")) != "nyregents":
            raise RuntimeError(f"{item_id} is not a nyregents item")
        claim = str(item.get("claim"))
        if claim not in ("algebra-i", "algebra-ii"):
            raise RuntimeError(f"{item_id} has claim {claim}")
        choices = item.get("choices") or {}
        if len(choices) != 4:
            raise RuntimeError(f"{item_id} has {len(choices)} options")
        out.append(item)
    if len(out) != 606:
        raise RuntimeError(f"expected 606 algebra primary items, got {len(out)}")
    return out


def dump_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> None:
    prereg_sha = check_preregistration()
    items = load_algebra_items()
    examples: list[dict[str, Any]] = []
    no_numeral_ids: dict[str, list[str]] = {"algebra-i": [], "algebra-ii": []}
    for arm in ARMS:
        rows: list[dict[str, Any]] = []
        for item_index, item in enumerate(items):
            item_id = str(item["id"])
            if item_index % 50 == 0:
                print(f"  {arm} {item_index}/{len(items)} {item_id}", flush=True)
            choices = dict(item["choices"])
            rng = rng_for(item_id, arm)
            try:
                perturbed, substitution_map, no_numeral = perturb_choices(choices, arm, rng)
            except RuntimeError as error:
                raise RuntimeError(f"{item_id} arm={arm}: {error}") from error
            claim = str(item["claim"])
            if no_numeral and arm == ARM_PRESERVING:
                no_numeral_ids[claim].append(item_id)
            if perturbed.keys() != choices.keys():
                raise RuntimeError(f"letter order changed on {item_id}")
            if list(perturbed.keys()) != list(choices.keys()):
                raise RuntimeError(f"letter insertion order changed on {item_id}")
            if str(item.get("key", "")).strip().upper() not in perturbed:
                raise RuntimeError(f"key missing after perturb on {item_id}")
            row = {
                "id": item_id,
                "arm": arm,
                "claim": claim,
                "authority": item.get("authority"),
                "key": str(item.get("key", "")).strip().upper(),
                "choices": perturbed,
                "originalChoices": choices,
                "substitutionMap": substitution_map,
                "noNumeral": no_numeral,
                "leadingNumbersOriginal": leading_numbers(choices),
                "leadingNumbersPerturbed": leading_numbers(perturbed),
                "rankPreserved": rank_order_preserved(choices, perturbed)
                if not no_numeral
                else True,
                "seed": SEED,
            }
            rows.append(row)
            if arm == ARM_PRESERVING and item_id in EXAMPLE_IDS:
                examples.append(
                    {
                        "id": item_id,
                        "claim": claim,
                        "original": choices,
                        "rankPreserving": perturbed,
                        "substitutionMap": substitution_map,
                        "noNumeral": no_numeral,
                    }
                )
        out_path = OUT_DIR / f"perturbed-items-{arm}.jsonl"
        dump_jsonl(out_path, rows)
        print(
            f"wrote {out_path.relative_to(ROOT)} n={len(rows)} no_numeral="
            f"{sum(1 for row in rows if row['noNumeral'])}",
            flush=True,
        )
    scrambled_by_id = {
        str(json.loads(line)["id"]): json.loads(line)
        for line in (OUT_DIR / f"perturbed-items-{ARM_SCRAMBLED}.jsonl").read_text(
            encoding="utf-8"
        ).splitlines()
        if line.strip()
    }
    for example in examples:
        scrambled = scrambled_by_id[example["id"]]
        example["rankScrambled"] = scrambled["choices"]
        example["scrambledSubstitutionMap"] = scrambled["substitutionMap"]
    if len(examples) != len(EXAMPLE_IDS):
        missing = [item_id for item_id in EXAMPLE_IDS if item_id not in {row["id"] for row in examples}]
        raise RuntimeError(f"example ids missing from algebra primary list: {missing}")
    payload = {
        "preregistrationSha256": prereg_sha,
        "seed": SEED,
        "noNumeral": {
            "algebra-i": {"n": len(no_numeral_ids["algebra-i"]), "ids": no_numeral_ids["algebra-i"]},
            "algebra-ii": {"n": len(no_numeral_ids["algebra-ii"]), "ids": no_numeral_ids["algebra-ii"]},
        },
        "examples": examples,
    }
    examples_path = OUT_DIR / "sanity-examples.json"
    examples_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {examples_path.relative_to(ROOT)}", flush=True)
    print("no_numeral Algebra I", len(no_numeral_ids["algebra-i"]), flush=True)
    print("no_numeral Algebra II", len(no_numeral_ids["algebra-ii"]), flush=True)
    print("examples:", flush=True)
    for example in examples:
        print(f"  {example['id']}", flush=True)
        print(f"    original {json.dumps(example['original'], ensure_ascii=False)}", flush=True)
        print(
            f"    preserving {json.dumps(example['rankPreserving'], ensure_ascii=False)}",
            flush=True,
        )
        print(
            f"    scrambled {json.dumps(example['rankScrambled'], ensure_ascii=False)}",
            flush=True,
        )


if __name__ == "__main__":
    main()
