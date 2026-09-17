#!/usr/bin/env python3
"""Shared text-layer MC extraction. Never invents missing choices or keys."""

from __future__ import annotations

import re
from typing import Iterable

from ingest_lib import choice_ok, clean_ws

LETTER_MAP = {"F": "A", "G": "B", "H": "C", "J": "D"}
COUNTRY_START = re.compile(
    r"^(Singapore|Korea|Hong Kong|Chinese Taipei|Finland|Russian Federation|"
    r"Japan|Israel|Hungary|Sweden|England|Australia|Italy|Lithuania|Malaysia|"
    r"Norway|Kazakhstan|Turkey|New Zealand|United States|Slovenia|Ukraine|"
    r"Armenia|Georgia|Tunisia|Romania|United Arab Emirates|Iran|Macedonia|"
    r"Qatar|Chile|Thailand|Palestinian|Lebanon|Bahrain|Indonesia|Saudi Arabia|"
    r"Oman|Jordan|Morocco|Syrian|Ghana|Estonia|Latvia|Slovak|Bulgaria|Moldova|"
    r"Netherlands|Belgium|Serbia|Cyprus|Egypt|Philippines|Botswana|Scotland|"
    r"South Africa|Chile|International average|Overall Percent|Copyright|"
    r"Country average|Education system|Percent correct|Main Topic|"
    r"Content Domain|Cognitive Domain|Item Number|Correct Response|"
    r"TIMSS |IEA )",
    re.I,
)
FIGURE_STEM = re.compile(
    r"\b(which graph|which (dot )?plot|which diagram|which figure|which table|"
    r"shown in the (graph|diagram|figure|grid)|the graph below|the figure below|"
    r"the diagram below|the scatter plot)\b",
    re.I,
)


def flatten(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def normalize_letter(letter: str) -> str:
    letter = letter.upper()
    return LETTER_MAP.get(letter, letter)


def looks_like_figure(stem: str) -> bool:
    return bool(FIGURE_STEM.search(stem))


def extract_lettered_choices(
    lines: Iterable[str],
    letters: str = "ABCD",
) -> tuple[list[str], dict[str, str]]:
    """Split stem vs lettered options. Letters may sit on their own line."""
    letter_re = re.compile(rf"^([{re.escape(letters)}])(?:[\.\)\]])?(?:\s+(.*))?$")
    stem_parts: list[str] = []
    choices: dict[str, str] = {}
    order: list[str] = []
    current: str | None = None
    started = False
    for raw in lines:
        s = raw.strip()
        if not s:
            continue
        if COUNTRY_START.match(s):
            break
        cm = letter_re.match(s)
        if cm:
            raw_letter = cm.group(1).upper()
            if raw_letter not in letters.upper():
                continue
            letter = normalize_letter(raw_letter)
            rest = (cm.group(2) or "").strip()
            if letter in choices and letter in order and order[-1] != letter:
                continue
            if letter not in choices:
                choices[letter] = rest
                order.append(letter)
            elif rest:
                choices[letter] = (choices[letter] + " " + rest).strip()
            current = letter
            started = True
            continue
        if started and current is not None:
            if re.match(r"^(Page |Mathematics|GO ON|STOP|Algebra|Geometry)", s):
                continue
            choices[current] = (choices[current] + " " + s).strip()
            continue
        stem_parts.append(s)
    cleaned = {k: clean_ws(v) for k, v in choices.items() if choice_ok(v)}
    return stem_parts, cleaned


def split_inline_numbered_choices(line: str) -> list[str]:
    """'(1) foo (3) bar' on one line -> two fragments."""
    parts = re.split(r"(?=\(\d\))", line)
    return [p.strip() for p in parts if p.strip()]


def extract_paren_choices(lines: Iterable[str]) -> tuple[list[str], dict[str, str]]:
    num_to_letter = {"1": "A", "2": "B", "3": "C", "4": "D"}
    stem_parts: list[str] = []
    choices: dict[str, str] = {}
    current: str | None = None
    started = False
    expanded: list[str] = []
    for raw in lines:
        for frag in split_inline_numbered_choices(raw):
            expanded.append(frag)
    for s in expanded:
        s = s.strip()
        if not s:
            continue
        cm = re.match(r"^\((\d)\)\s*(.*)$", s)
        if cm and cm.group(1) in num_to_letter:
            letter = num_to_letter[cm.group(1)]
            rest = cm.group(2).strip()
            choices[letter] = rest
            current = letter
            started = True
            continue
        if started and current is not None:
            if s.startswith("Page ") or "Use this space" in s:
                continue
            choices[current] = (choices[current] + " " + s).strip()
            continue
        stem_parts.append(s)
    cleaned = {k: clean_ws(v) for k, v in choices.items() if choice_ok(v)}
    return stem_parts, cleaned
