#!/usr/bin/env python3
"""Locate solving-tagged items on exam PDFs, parse VLM equation JSON, substitute options."""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import fitz

sys.path.insert(0, str(Path(__file__).resolve().parent))
from addendum_lib import ROOT, bootstrap_ci_mulberry, binomial_sf
from ingest_lib import RAW
from print_page_audit import prefer_exam_pdf
from strategy_channels import (
    TEKS_SOLVE_TAGS,
    Equation,
    evaluate_side_v2,
    is_solving_item,
    normalize_math_text_v2,
    normalize_minus_text,
    pair_variable_order,
    parse_math_expression_v2,
    relation_holds,
    single_letter_variables,
)

DPI = 150
CROP_PAD_PT = 8.0
MIN_CROP_HEIGHT_PT = 72.0
STEM_PREFIX_CHARS = 90
PAGES_DIR = ROOT / "exports" / "addendum-vlm" / "pages"
PREREG_PATH = ROOT / "exports" / "addendum-vlm" / "preregistration.md"

REGENTS_ID_RE = re.compile(
    r"^nyregents-(algebra-i|algebra-ii|geometry)-(\d{4}|unknown)-(jan|jun|aug|unk)-q(\d+)$",
    re.I,
)
QUESTION_SUFFIX_RE = re.compile(r"-q(\d+)$", re.I)
TIMSS_CODE_RE = re.compile(r"(M\d{6})", re.I)
PAGE_POINTER_RE = re.compile(r"^(?P<name>.+\.pdf):p(?P<page>\d+)$", re.I)
UNIT_TAIL_RE = re.compile(
    r"\s*(?:cm|mm|km|kg|mg|ml|lb|ft|in|yd|mph|m|s|h|%|degrees?|metres?|meters?)\s*$",
    re.I,
)
STRICT_FRACTION_RE = re.compile(r"^(-?\d+)\s*/\s*(-?\d+)$")
STRICT_DECIMAL_RE = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)$")
LETTER_EQ_RE = re.compile(r"^[A-Za-z]\s*=\s*(.+)$")
XY_PAIR_RE = re.compile(
    r"^[xy]\s*=\s*([^,;]+)\s*[,;]\s*[xy]\s*=\s*(.+)$",
    re.I,
)
PAREN_PAIR_RE = re.compile(
    r"^\(\s*([+-]?(?:\d+(?:\.\d*)?|\.\d+))\s*,\s*([+-]?(?:\d+(?:\.\d*)?|\.\d+))\s*\)$"
)
RELATION_RE = re.compile(r"==|≠|!=|≤|≥|<=|>=|=|<|>")
FRAC_RE = re.compile(r"\\frac\s*\{([^{}]+)\}\s*\{([^{}]+)\}")
SQRT_BRACE_RE = re.compile(r"\\sqrt\s*\{([^{}]+)\}")
SQRT_BARE_RE = re.compile(r"\\sqrt\s*([A-Za-z0-9]+)")
HAT_BRACE_RE = re.compile(r"\^\{([^{}]+)\}")
HAT_BARE_RE = re.compile(r"\^([A-Za-z0-9]+)")
KEPT_TEX_COMMANDS = {
    "sin",
    "cos",
    "tan",
    "log",
    "ln",
    "abs",
    "pi",
    "sqrt",
    "exp",
}
FGHJ_MAP = {"F": "A", "G": "B", "H": "C", "J": "D"}
LETTER_ORDER = ("A", "B", "C", "D")

EXTRACT_PROMPT_TEMPLATE = """You are a transcription tool, not a tutor.

The page image may contain several items. Use only the item whose printed stem begins with:
{stem_prefix}

Transcribe:
1. every displayed equation or inequality in that item that involves an unknown (the relation a student could substitute into);
2. the printed multiple-choice option contents for that item, keyed by letter A,B,C,D. If the page uses F,G,H,J, map F->A, G->B, H->C, J->D.

Do not solve. Do not say which option is correct. Do not compute a value for the unknown.

Reply with a JSON object and nothing else:
{{"has_equation": true, "equations": [{{"latex": "...", "ascii": "..."}}], "options": {{"A": "...", "B": "...", "C": "...", "D": "..."}}}}
If that item has no equation or inequality, use has_equation false and equations [].
ascii uses * for multiplication, ** for powers, sqrt(...) for roots, and a single relation from = < > <= >= !=.
"""

VERIFY_PROMPT_TEMPLATE = """You are checking substitution, not solving by algebra.

Use only the item whose printed stem begins with:
{stem_prefix}

For each printed option A,B,C,D (map F,G,H,J to A,B,C,D), answer whether that option's printed value satisfies the displayed equation or inequality in the item. Do not solve for the unknown. Do not explain.

JSON only:
{{"A": "yes"|"no"|"unreadable", "B": "yes"|"no"|"unreadable", "C": "yes"|"no"|"unreadable", "D": "yes"|"no"|"unreadable"}}
"""


@dataclass
class PageTarget:
    pdf: Path | None
    page_index: int | None
    clip: tuple[float, float, float, float] | None
    png_path: Path
    locate_reason: str


def index_pdfs() -> dict[str, Path]:
    index: dict[str, Path] = {}
    if not RAW.exists():
        return index
    for path in RAW.rglob("*"):
        if path.is_file() and path.suffix.lower() == ".pdf":
            index[path.name.lower()] = path
    return index


def url_pdf_name(url: str) -> str:
    parsed = urlparse(url)
    fragment = parsed.fragment.strip()
    if fragment.lower().endswith(".pdf"):
        return Path(fragment.split("/")[-1]).name.lower()
    return Path(parsed.path).name.lower()


def parse_page_pointer(pointer: str | None) -> tuple[str | None, int | None]:
    if not pointer:
        return None, None
    match = PAGE_POINTER_RE.match(pointer.strip())
    if match:
        return Path(match.group("name")).name.lower(), int(match.group("page"))
    if pointer.lower().endswith(".pdf"):
        return Path(pointer).name.lower(), None
    return None, None


def stem_prefix(stem: str) -> str:
    cleaned = re.sub(r"[\x00-\x1f]", " ", stem)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned[:STEM_PREFIX_CHARS]


def question_number(item: dict[str, Any]) -> int | None:
    item_id = str(item.get("id") or "")
    match = REGENTS_ID_RE.match(item_id)
    if match:
        return int(match.group(4))
    suffix = QUESTION_SUFFIX_RE.search(item_id)
    if suffix:
        return int(suffix.group(1))
    return None


def timss_item_code(item: dict[str, Any]) -> str | None:
    match = TIMSS_CODE_RE.search(str(item.get("id") or ""))
    return match.group(1).upper() if match else None


def resolve_pdf(item: dict[str, Any], pdf_index: dict[str, Path]) -> Path | None:
    pointer_name, _pointer_page = parse_page_pointer(item.get("pagePointer"))
    candidates = [
        pointer_name,
        url_pdf_name(str(item.get("sourceUrl") or "")),
    ]
    for name in candidates:
        if not name:
            continue
        found = prefer_exam_pdf(name, pdf_index)
        if found is not None:
            return found
        if name in pdf_index:
            return pdf_index[name]
    return None


def is_question_heading(text: str, number: int) -> bool:
    stripped = text.strip()
    if stripped.startswith("("):
        paren = re.match(rf"^\(\s*{number}\s*\)\s*(.+)$", stripped)
        return bool(paren and len(paren.group(1).strip()) >= 16)
    split_paren = re.match(rf"^{number}\)\s+(.+)$", stripped)
    if split_paren and len(split_paren.group(1).strip()) >= 16:
        return True
    if re.match(rf"^{number}(?!\d)(?:\.|\))\s+\S", stripped):
        return True
    return bool(re.match(rf"^{number}(?!\d)\s+[A-Za-z\(\"]", stripped))


def line_records(page: fitz.Page) -> list[tuple[float, float, str, fitz.Rect]]:
    rows: list[tuple[float, float, str, fitz.Rect]] = []
    payload = page.get_text("dict")
    for block in payload.get("blocks") or []:
        if block.get("type") != 0:
            continue
        for line in block.get("lines") or []:
            spans = line.get("spans") or []
            text = "".join(str(span.get("text") or "") for span in spans)
            bbox = line.get("bbox")
            if not text.strip() or not bbox:
                continue
            rect = fitz.Rect(bbox)
            rows.append((rect.x0, rect.y0, text, rect))
    rows.sort(key=lambda row: (row[1], row[0]))
    return rows


def heading_y(page: fitz.Page, number: int, stem: str) -> float | None:
    prefix_tokens = {
        tok for tok in re.findall(r"[a-z0-9]+", stem.lower()) if len(tok) >= 3
    }
    matches: list[tuple[int, float]] = []
    for x0, y0, text, _rect in line_records(page):
        if x0 > page.rect.width * 0.42:
            continue
        if not is_question_heading(text, number):
            continue
        line_tokens = set(re.findall(r"[a-z0-9]+", text.lower()))
        overlap = len(prefix_tokens & line_tokens) if prefix_tokens else 0
        matches.append((overlap, y0))
    if not matches:
        return None
    matches.sort(key=lambda row: (-row[0], row[1]))
    return matches[0][1]


def search_code_y(page: fitz.Page, code: str) -> float | None:
    hits = page.search_for(code)
    if not hits:
        hits = page.search_for(code.lower())
    if not hits:
        return None
    hits.sort(key=lambda rect: (rect.y0, rect.x0))
    return float(hits[0].y0)


def clip_rect(page: fitz.Page, top: float, bottom: float | None) -> fitz.Rect:
    page_rect = page.rect
    y0 = max(page_rect.y0, top - CROP_PAD_PT)
    y1 = page_rect.y1 if bottom is None else min(page_rect.y1, bottom + CROP_PAD_PT)
    if y1 <= y0 or (y1 - y0) < MIN_CROP_HEIGHT_PT:
        return page_rect
    return fitz.Rect(page_rect.x0, y0, page_rect.x1, y1)


def locate_in_document(
    document: fitz.Document,
    item: dict[str, Any],
    preferred_page: int | None,
) -> tuple[int | None, fitz.Rect | None, str]:
    qnum = question_number(item)
    code = timss_item_code(item)
    stem = str(item.get("stem") or "")
    page_indices = list(range(len(document)))
    if preferred_page is not None and 0 <= preferred_page < len(document):
        page_indices = [preferred_page] + [i for i in page_indices if i != preferred_page]
    for page_index in page_indices:
        page = document[page_index]
        top: float | None = None
        if qnum is not None:
            top = heading_y(page, qnum, stem)
        if top is None and code:
            top = search_code_y(page, code)
        if top is None:
            continue
        bottom: float | None = None
        if qnum is not None:
            next_top = heading_y(page, qnum + 1, "")
            if next_top is not None and next_top > top + 20:
                bottom = next_top
        elif code is not None:
            bottom = min(page.rect.y1, top + 360.0)
        return page_index, clip_rect(page, top, bottom), "question_crop"
    stem_page = find_stem_page(document, stem)
    if stem_page is not None:
        page = document[stem_page]
        top = heading_y(page, qnum, stem) if qnum is not None else None
        if top is None and code:
            top = search_code_y(page, code)
        if top is not None:
            bottom: float | None = None
            if qnum is not None:
                next_top = heading_y(page, qnum + 1, "")
                if next_top is not None and next_top > top + 20:
                    bottom = next_top
            return stem_page, clip_rect(page, top, bottom), "stem_question_crop"
        return stem_page, page.rect, "stem_page"
    if preferred_page is not None and 0 <= preferred_page < len(document):
        page = document[preferred_page]
        return preferred_page, page.rect, "full_page_pointer"
    if len(document) == 1:
        page = document[0]
        return 0, page.rect, "full_page_single"
    return None, None, "page_not_found"


def find_stem_page(document: fitz.Document, stem: str) -> int | None:
    tokens = [tok.lower() for tok in re.findall(r"[A-Za-z]{4,}", stem)[:8]]
    if len(tokens) < 3:
        return None
    needles = tokens[:5]
    best: tuple[int, int] | None = None
    for page_index in range(len(document)):
        blob = document[page_index].get_text("text").lower()
        hits = sum(1 for needle in needles if needle in blob)
        if hits >= min(3, len(needles)):
            scored = (hits, -page_index)
            if best is None or scored > (best[0], -best[1]):
                best = (hits, page_index)
    return None if best is None else best[1]


def build_page_target(
    item: dict[str, Any],
    pdf_index: dict[str, Path],
    document_cache: dict[Path, fitz.Document],
) -> PageTarget:
    png_path = PAGES_DIR / f"{item['id']}.png"
    pdf = resolve_pdf(item, pdf_index)
    if pdf is None:
        return PageTarget(None, None, None, png_path, "pdf_missing")
    if pdf not in document_cache:
        document_cache[pdf] = fitz.open(pdf)
    document = document_cache[pdf]
    _name, pointer_page = parse_page_pointer(item.get("pagePointer"))
    preferred = None if pointer_page is None else pointer_page - 1
    page_index, clip, reason = locate_in_document(document, item, preferred)
    clip_tuple = None if clip is None else (clip.x0, clip.y0, clip.x1, clip.y1)
    return PageTarget(pdf, page_index, clip_tuple, png_path, reason)


def render_target(
    target: PageTarget,
    document: fitz.Document | None = None,
) -> bool:
    if target.pdf is None or target.page_index is None:
        return False
    owns_document = document is None
    if document is None:
        document = fitz.open(target.pdf)
    page = document[target.page_index]
    clip = None if target.clip is None else fitz.Rect(*target.clip)
    matrix = fitz.Matrix(DPI / 72.0, DPI / 72.0)
    pix = page.get_pixmap(matrix=matrix, clip=clip)
    target.png_path.parent.mkdir(parents=True, exist_ok=True)
    pix.save(str(target.png_path))
    if owns_document:
        document.close()
    return True


def latex_to_ascii(latex: str) -> str:
    text = latex.strip()
    for fence in (r"\(", r"\)", r"\[", r"\]", "$$", "$"):
        text = text.replace(fence, "")
    text = text.replace(r"\left", "").replace(r"\right", "")
    text = text.replace(r"\cdot", "*").replace(r"\times", "*").replace(r"\div", "/")
    text = text.replace(r"\leq", "<=").replace(r"\le", "<=")
    text = text.replace(r"\geq", ">=").replace(r"\ge", ">=")
    text = text.replace(r"\neq", "!=").replace(r"\ne", "!=")
    text = text.replace(r"\pi", "pi")
    while True:
        updated = FRAC_RE.sub(r"(\1)/(\2)", text)
        if updated == text:
            break
        text = updated
    text = SQRT_BRACE_RE.sub(r"sqrt(\1)", text)
    text = SQRT_BARE_RE.sub(r"sqrt(\1)", text)
    text = HAT_BRACE_RE.sub(r"**(\1)", text)
    text = HAT_BARE_RE.sub(r"**\1", text)

    def keep_or_drop(match: re.Match[str]) -> str:
        name = match.group(1)
        return name if name in KEPT_TEX_COMMANDS else " "

    text = re.sub(r"\\([a-zA-Z]+)", keep_or_drop, text)
    text = text.replace("{", "(").replace("}", ")")
    return re.sub(r"\s+", " ", text).strip()


def split_relation(text: str) -> tuple[str, str, str] | None:
    equals = list(re.finditer(r"(?<![<>=!])=(?![=])", text))
    if equals:
        token = equals[0]
        rel = "="
    else:
        match = RELATION_RE.search(text)
        if match is None:
            return None
        token = match
        rel = match.group(0)
    left = text[: token.start()].strip()
    right = text[token.end() :].strip()
    right = RELATION_RE.split(right, maxsplit=1)[0].strip()
    if rel == "==":
        rel = "="
    if not left or not right:
        return None
    return left, rel, right


def equations_from_ascii(blobs: list[str]) -> list[Equation]:
    found: list[Equation] = []
    seen: set[tuple[str, str, str]] = set()
    for blob in blobs:
        pieces = re.split(r"\band\b", blob, flags=re.I)
        for piece in pieces:
            split = split_relation(piece)
            if split is None:
                continue
            left, rel, right = split
            if parse_math_expression_v2(left) is None:
                continue
            if parse_math_expression_v2(right) is None:
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


def parse_json_object(text: str) -> dict[str, Any] | None:
    stripped = text.strip()
    stripped = re.sub(r"^```(?:json)?\s*", "", stripped)
    stripped = re.sub(r"\s*```$", "", stripped)
    start = stripped.find("{")
    if start < 0:
        return None
    try:
        payload, _end = json.JSONDecoder().raw_decode(stripped[start:])
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    return payload


def map_option_letter(raw: str) -> str | None:
    letter = raw.strip().upper()[:1]
    letter = FGHJ_MAP.get(letter, letter)
    if letter in LETTER_ORDER:
        return letter
    return None


def parse_strict_scalar(text: str) -> float | None:
    cleaned = UNIT_TAIL_RE.sub("", clean_option_text(text)).strip()
    wrapped = LETTER_EQ_RE.match(cleaned)
    if wrapped:
        cleaned = wrapped.group(1).strip()
        cleaned = UNIT_TAIL_RE.sub("", cleaned).strip()
    fraction = STRICT_FRACTION_RE.match(cleaned)
    if fraction:
        denom = float(fraction.group(2))
        if denom == 0:
            return None
        value = float(fraction.group(1)) / denom
        return value if abs(value) < 1e12 else None
    if not STRICT_DECIMAL_RE.match(cleaned):
        return None
    value = float(cleaned)
    return value if abs(value) < 1e12 else None


def clean_option_text(text: str) -> str:
    cleaned = normalize_minus_text(text).replace("$", "")
    cleaned = re.sub(r"(?<=\d),(?=\d)", "", cleaned)
    return re.sub(r"\s+", " ", cleaned).strip()


def parse_strict_option(text: str) -> float | tuple[float, float] | None:
    cleaned = clean_option_text(text)
    pair_match = PAREN_PAIR_RE.match(cleaned)
    if pair_match:
        return (float(pair_match.group(1)), float(pair_match.group(2)))
    xy_match = XY_PAIR_RE.match(cleaned)
    if xy_match:
        left = parse_strict_scalar(xy_match.group(1))
        right = parse_strict_scalar(xy_match.group(2))
        if left is not None and right is not None:
            return (left, right)
    return parse_strict_scalar(cleaned)


def equation_variables(equation: Equation) -> set[str]:
    return single_letter_variables(normalize_math_text_v2(equation.left + " " + equation.right))


def extract_equations_from_payload(payload: dict[str, Any]) -> list[Equation]:
    blobs: list[str] = []
    raw_equations = payload.get("equations") or []
    if isinstance(raw_equations, dict):
        raw_equations = [raw_equations]
    for entry in raw_equations:
        if isinstance(entry, str):
            ascii_math = entry
            latex = ""
        elif isinstance(entry, dict):
            ascii_math = str(entry.get("ascii") or "").strip()
            latex = str(entry.get("latex") or "").strip()
        else:
            continue
        blob = ascii_math if ascii_math else latex_to_ascii(latex)
        if blob:
            blobs.append(blob)
    return equations_from_ascii(blobs)


def option_map_from_payload(payload: dict[str, Any]) -> dict[str, str]:
    raw = payload.get("options") or {}
    mapped: dict[str, str] = {}
    if not isinstance(raw, dict):
        return mapped
    for key, value in raw.items():
        letter = map_option_letter(str(key))
        if letter is None:
            continue
        mapped[letter] = str(value)
    return mapped


def unique_satisfier(
    equations: list[Equation],
    option_texts: dict[str, str],
) -> tuple[str | None, str, dict[str, Any]]:
    extra: dict[str, Any] = {
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
        "nEquations": len(equations),
    }
    if not equations:
        extra["hits"] = []
        return None, "no_equation", extra
    scalars: dict[str, float] = {}
    pairs: dict[str, tuple[float, float]] = {}
    for letter, text in option_texts.items():
        parsed = parse_strict_option(text)
        if isinstance(parsed, tuple):
            pairs[letter] = parsed
        elif parsed is not None:
            scalars[letter] = parsed
    extra["parsedScalars"] = {k: scalars[k] for k in sorted(scalars)}
    extra["parsedPairs"] = {k: list(pairs[k]) for k in sorted(pairs)}
    one_var = [eq for eq in equations if len(equation_variables(eq)) == 1]
    two_var = [eq for eq in equations if len(equation_variables(eq)) == 2]
    if one_var and scalars:
        for equation in one_var:
            variable = next(iter(equation_variables(equation)))
            hits: list[str] = []
            evaluated = False
            for letter, value in scalars.items():
                mapping = {variable: value}
                left = evaluate_side_v2(equation.left, mapping)
                right = evaluate_side_v2(equation.right, mapping)
                if left is None or right is None:
                    continue
                evaluated = True
                if relation_holds(equation.rel, left, right):
                    hits.append(letter)
            extra["used"] = {
                "kind": "scalar",
                "variable": variable,
                "left": equation.left,
                "rel": equation.rel,
                "right": equation.right,
            }
            extra["hits"] = hits
            if not evaluated:
                continue
            if len(hits) == 1:
                return hits[0], "unique", extra
            if len(hits) == 0:
                return None, "zero_hits", extra
            return None, "multiple_hits", extra
    system = two_var
    if len(one_var) >= 2:
        joined: set[str] = set()
        for equation in one_var:
            joined |= equation_variables(equation)
        if len(joined) == 2:
            system = one_var + two_var
    if system and pairs:
        variables: set[str] = set()
        for equation in system:
            variables |= equation_variables(equation)
        order = pair_variable_order(variables)
        if order is not None:
            hits = []
            evaluated = False
            for letter, pair in pairs.items():
                mapping = {order[0]: pair[0], order[1]: pair[1]}
                ok = True
                n_eval = 0
                for equation in system:
                    left = evaluate_side_v2(equation.left, mapping)
                    right = evaluate_side_v2(equation.right, mapping)
                    if left is None or right is None:
                        ok = False
                        break
                    n_eval += 1
                    if not relation_holds(equation.rel, left, right):
                        ok = False
                        break
                if n_eval == 0:
                    continue
                evaluated = True
                if ok:
                    hits.append(letter)
            extra["used"] = {
                "kind": "system" if len(system) >= 2 else "pair",
                "variables": order,
            }
            extra["hits"] = hits
            if evaluated:
                if len(hits) == 1:
                    return hits[0], "unique", extra
                if len(hits) == 0:
                    return None, "zero_hits", extra
                return None, "multiple_hits", extra
    extra["hits"] = []
    if not scalars and not pairs:
        return None, "no_parsed_options", extra
    return None, "zero_hits", extra


def chance_k(item: dict[str, Any]) -> float:
    n_choices = len(item.get("choices") or {})
    if n_choices <= 0:
        n_choices = 4
    return 1.0 / n_choices


def is_teks_solve_se(item: dict[str, Any]) -> bool:
    return str(item.get("officialTag") or "") in TEKS_SOLVE_TAGS


def is_timss_algebra(item: dict[str, Any]) -> bool:
    return bool(
        item.get("authority") == "timss"
        and re.search(r"algebra", str(item.get("contentDomain") or ""), re.I)
    )


def cell_label(authority: str, claim: str) -> str:
    return f"{authority}/{claim}"


def summarize_cell(rows: list[dict[str, Any]]) -> dict[str, Any]:
    n_eligible = len(rows)
    fired = [row for row in rows if row.get("fired")]
    n_fired = len(fired)
    hits = sum(1 for row in fired if row.get("correct"))
    flags = [1 if row.get("correct") else 0 for row in fired]
    chance_values = [float(row["chance"]) for row in fired]
    chance = sum(chance_values) / n_fired if n_fired else 0.0
    rate = hits / n_fired if n_fired else 0.0
    ci = bootstrap_ci_mulberry(flags) if n_fired else (0.0, 0.0)
    binomial = binomial_sf(hits, n_fired, chance) if n_fired and chance > 0 else 1.0
    imputed_hits = hits + sum(
        float(row["chance"]) for row in rows if not row.get("fired")
    )
    imputed_rate = imputed_hits / n_eligible if n_eligible else 0.0
    coverage = n_fired / n_eligible if n_eligible else 0.0
    n_image = sum(1 for row in rows if row.get("hasImage"))
    clears = n_fired >= 10 and ci[0] > chance
    return {
        "nEligible": n_eligible,
        "nWithImage": n_image,
        "nFiredUnique": n_fired,
        "hits": hits,
        "rate": rate,
        "chance": chance,
        "ci95": [ci[0], ci[1]],
        "binomialPGreater": binomial,
        "coverage": coverage,
        "rateWithAbstentionAsChance": imputed_rate,
        "clearsBar": clears,
    }


def load_prompt_block(title: str) -> str:
    text = PREREG_PATH.read_text(encoding="utf-8")
    pattern = re.compile(
        rf"## {re.escape(title)}.*?```\n(.*?)```",
        re.S,
    )
    match = pattern.search(text)
    if match is None:
        raise RuntimeError(f"prompt block missing from preregistration: {title}")
    return match.group(1).strip() + "\n"


def extraction_prompt(prefix: str) -> str:
    return EXTRACT_PROMPT_TEMPLATE.format(stem_prefix=prefix).rstrip() + "\n"


def verify_prompt(prefix: str) -> str:
    return VERIFY_PROMPT_TEMPLATE.format(stem_prefix=prefix).rstrip() + "\n"
