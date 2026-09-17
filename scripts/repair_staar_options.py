#!/usr/bin/env python3
"""Version-2 STAAR option repair: last-option footer/page leak and stacked-fraction rejoin.

Derived from the five version-1 hand-check last-option leaks and the one stacked-fraction
pairing. Applied after parse_items, before scoring. Does not change KEY_FLAT.
"""

from __future__ import annotations

import copy
import re
from typing import Any

from ingest_lib import clean_ws
from parse_helpers import extract_lettered_choices
from parse_staar_bulk import looks_like_item_start

ITEM_START = re.compile(r"^(\d{1,2})\s+(\S.*)$")
FOOTER_LINE = re.compile(
    r"(?i)^(Mathematics|Page\s+\d+|GO ON|STOP|STAAR|Texas Education Agency|"
    r"BE SURE YOU HAVE RECORDED|---PAGE)"
)
FOOTER_INLINE = re.compile(
    r"(?i)(?:Mathematics\s+)?Page\s+\d+|---PAGE\s+\d+---|BE SURE YOU HAVE RECORDED|"
    r"\bGO ON\b|\bSTOP\b"
)
PAGE_MARKER = re.compile(r"---PAGE (\d+)---")
ITEM_ID_QUESTION = re.compile(r"-q(\d+)$")
TWO_INTEGERS = re.compile(r"^(\d+)\s+(\d+)$")
ONE_INTEGER = re.compile(r"^(\d+)$")
STEM_TRAILING_INTEGER = re.compile(r"^(.*\?)\s+(\d+)\s*$")
LEADING_F_CHOICE = re.compile(r"^F\b")


def question_from_id(item_id: str) -> int | None:
    match = ITEM_ID_QUESTION.search(item_id)
    return int(match.group(1)) if match else None


def pdf_page_at(text: str, start: int) -> int | None:
    matches = list(PAGE_MARKER.finditer(text[: start + 1]))
    if not matches:
        return None
    return int(matches[-1].group(1))


def find_item_start(text: str, question: int) -> int | None:
    pattern = re.compile(rf"(?:^|\n)\s*{question}\s+(\S.*)", re.M)
    for match in pattern.finditer(text):
        rest = match.group(1).strip()
        if looks_like_item_start(rest):
            return match.start()
    return None


def strip_trailing_page_or_footer(text: str, page: int | None) -> str:
    cut = FOOTER_INLINE.split(text)[0].strip()
    tokens = cut.split()
    if page is not None and len(tokens) >= 2 and tokens[-1] == str(page):
        tokens = tokens[:-1]
    return clean_ws(" ".join(tokens))


def last_option_block(pdf_text: str, question: int) -> tuple[list[str], int | None]:
    start = find_item_start(pdf_text, question)
    if start is None:
        return [], None
    page = pdf_page_at(pdf_text, start)
    block: list[str] = []
    seen_this_item = False
    for raw in pdf_text[start:].splitlines():
        stripped = raw.strip()
        if not stripped:
            continue
        if FOOTER_LINE.match(stripped):
            break
        item_match = ITEM_START.match(stripped)
        if item_match:
            number = int(item_match.group(1))
            rest = item_match.group(2).strip()
            if seen_this_item and number != question and looks_like_item_start(rest):
                break
            if number == question and looks_like_item_start(rest):
                seen_this_item = True
        if seen_this_item:
            block.append(stripped)
    return block, page


def reconstruct_last_option(pdf_text: str, question: int) -> tuple[str | None, int | None]:
    """Last lettered option up to the first footer line or next item, not past it."""
    block, page = last_option_block(pdf_text, question)
    if not block:
        return None, page
    letters = "FGHJ" if any(LEADING_F_CHOICE.match(line) for line in block) else "ABCD"
    _stem_parts, choices = extract_lettered_choices(block, letters)
    last = choices.get("D")
    if last is None:
        return None, page
    return strip_trailing_page_or_footer(last, page), page


def rejoin_stacked_fractions(
    stem: str, choices: dict[str, str]
) -> tuple[str, dict[str, str]] | None:
    """Rejoin a split stacked-fraction option set into FRACTION_RE `num/den` form.

    Text-layer order for a four-option stacked list is numerator_A, then
    (denom_A, numerator_B) on A, (denom_B, numerator_C) on B, (denom_C, numerator_D)
    on C, and denom_D on D. The leftover first numerator sits after the last `?`
    in the stem.
    """
    if set(choices) != set("ABCD"):
        return None
    stem_match = STEM_TRAILING_INTEGER.match(stem.strip())
    if stem_match is None:
        return None
    if (
        TWO_INTEGERS.match(choices["A"]) is None
        or TWO_INTEGERS.match(choices["B"]) is None
        or TWO_INTEGERS.match(choices["C"]) is None
        or ONE_INTEGER.match(choices["D"]) is None
    ):
        return None
    first_numerator = stem_match.group(2)
    denom_a, num_b = TWO_INTEGERS.match(choices["A"]).groups()
    denom_b, num_c = TWO_INTEGERS.match(choices["B"]).groups()
    denom_c, num_d = TWO_INTEGERS.match(choices["C"]).groups()
    denom_d = ONE_INTEGER.match(choices["D"]).group(1)
    rejoined = {
        "A": f"{first_numerator}/{denom_a}",
        "B": f"{num_b}/{denom_b}",
        "C": f"{num_c}/{denom_c}",
        "D": f"{num_d}/{denom_d}",
    }
    return stem_match.group(1).strip(), rejoined


def repair_item(item: dict[str, Any], pdf_text: str) -> dict[str, Any]:
    repaired = copy.deepcopy(item)
    question = question_from_id(str(item.get("id") or ""))
    notes: dict[str, Any] = {
        "lastOptionRepaired": False,
        "stackedFractionRejoined": False,
        "pdfPage": None,
        "trailingPageTokenStripped": False,
    }
    choices = repaired.get("choices")
    if not isinstance(choices, dict) or "D" not in choices or question is None:
        repaired["repair"] = notes
        return repaired

    reconstructed, page = reconstruct_last_option(pdf_text, question)
    notes["pdfPage"] = page
    original_last = str(choices["D"])
    if reconstructed is not None and reconstructed != original_last:
        choices["D"] = reconstructed
        notes["lastOptionRepaired"] = True
    else:
        stripped = strip_trailing_page_or_footer(original_last, page)
        if stripped != original_last:
            choices["D"] = stripped
            notes["lastOptionRepaired"] = True
            notes["trailingPageTokenStripped"] = True

    stacked = rejoin_stacked_fractions(str(repaired.get("stem") or ""), choices)
    if stacked is not None:
        new_stem, new_choices = stacked
        repaired["stem"] = new_stem
        repaired["choices"] = new_choices
        notes["stackedFractionRejoined"] = True

    repaired["repair"] = notes
    return repaired


def repair_items(
    items: list[dict[str, Any]], pdf_text_by_source: dict[str, str]
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for item in items:
        source = str(item.get("sourceUrl") or "").removeprefix("file:")
        pdf_text = pdf_text_by_source.get(source)
        if pdf_text is None:
            copy_item = copy.deepcopy(item)
            copy_item["repair"] = {
                "lastOptionRepaired": False,
                "stackedFractionRejoined": False,
                "pdfPage": None,
                "missingPdfText": True,
            }
            out.append(copy_item)
            continue
        out.append(repair_item(item, pdf_text))
    return out
