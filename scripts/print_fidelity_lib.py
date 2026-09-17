#!/usr/bin/env python3
"""Print-fidelity check: compare census text-layer items to a VLM transcription of the page."""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import sys
import unicodedata
from dataclasses import asdict, dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

import fitz

sys.path.insert(0, str(Path(__file__).resolve().parent))
from addendum_lib import ROOT, middle_value_option, score_program
from vlm_backsolve_lib import question_number

OUT_DIR = ROOT / "exports" / "print-faithful"
PAGES_DIR = OUT_DIR / "pages"
PREREG_PATH = OUT_DIR / "preregistration.md"
PREREG_SHA_PATH = OUT_DIR / "preregistration.sha256"
FIDELITY_ITEMS_PATH = OUT_DIR / "fidelity-items.jsonl"
CALIBRATION_PATH = OUT_DIR / "calibration.json"
DEV_ITEMS_PATH = OUT_DIR / "dev-items.jsonl"
POPULATION_PATH = OUT_DIR / "population.json"
AUDIT_PATH = ROOT / "exports" / "print-audit" / "audit.json"
ALGEBRA_PRIMARY_IDS_PATH = ROOT / "exports" / "addendum-gpu" / "masked-stem-algebra-primary-item-ids.json"
PRIMARY_IDS_PATH = ROOT / "exports" / "addendum-gpu" / "masked-stem-primary-item-ids.json"

MODEL_ID = "Qwen/Qwen2-VL-7B-Instruct"
MODEL_REVISION = "eed13092ef92e448dd6875b2a00151bd3f7db0ac"
SNAPSHOT_PATH = (
    Path.home()
    / ".cache"
    / "huggingface"
    / "hub"
    / "models--Qwen--Qwen2-VL-7B-Instruct"
    / "snapshots"
    / MODEL_REVISION
)
SEED = 20260916
DPI = 150
MAX_NEW_TOKENS = 640
CONTINUATION_MIN_HEADING_Y_PT = 150.0
CROP_PAD_PT = 8.0

STEM_F1_THRESHOLD = 0.8
STEM_PRECISION_THRESHOLD = 0.8
STEM_RECALL_THRESHOLD = 0.8
OPTION_MATCH_THRESHOLD = 0.9
FIELD_EXTRA_SHARE_THRESHOLD = 0.2
CALIBRATION_GRID_STEM = (0.7, 0.8, 0.9)
CALIBRATION_GRID_OPTION = (0.8, 0.9)
CALIBRATION_MIN_AGREEMENT = 16

CELL_ALGEBRA_I = "nyregents::algebra-i::masked-stem-primary"
CELL_ALGEBRA_II = "nyregents::algebra-ii::masked-stem-primary"
CELL_GEOMETRY_LC = "nyregents::geometry::lower-central-fired"
CELL_EQAO_G6_LC = "eqao::g6::lower-central-fired"
CELL_GEOMETRY_PHI4 = "nyregents::geometry::masked-stem-primary"

VERDICT_FAITHFUL = "faithful"
VERDICT_NOT_FAITHFUL = "not_faithful"
VERDICT_UNVERIFIED = "unverified"

DIGIT_LABELS = {"1": "A", "2": "B", "3": "C", "4": "D", "5": "E"}
FGHJ_LABELS = {"F": "A", "G": "B", "H": "C", "J": "D", "K": "E"}
LETTER_ORDER = ("A", "B", "C", "D", "E")
MATH_WORD_DROP = {"sqrt", "pi", "percent", "degree", "degrees", "minus"}
KEEP_TEX_NAMES = {"sin", "cos", "tan", "sec", "csc", "cot", "arcsin", "arccos", "arctan", "log", "ln"}
LATEX_COMMAND_RE = re.compile(r"\\([a-zA-Z]+)")
BRACKET_DESCRIPTION_RE = re.compile(
    r"\[[^\]]*\b(?:diagram|graph|figure|image|picture|table|chart|drawing|shown|axes|number line|dot plot|box plot)\b[^\]]*\]",
    re.I,
)
ECHO_MIN_OPTION_TOKENS = 2
ECHO_MIN_OPTIONS_FOUND = 2
LETTER_DIGIT_BOUNDARY_RE = re.compile(r"(?<=[a-z])(?=[0-9])|(?<=[0-9])(?=[a-z])")
TOKEN_RE = re.compile(r"[a-z0-9]+")
LENGTH_UNIT_RE = r"(?:centimet(?:er|re)s?|millimet(?:er|re)s?|kilomet(?:er|re)s?|met(?:er|re)s?|inch(?:es)?|feet|foot|yards?|miles?|units?)"
UNIT_REPLACEMENTS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\bdegrees?\s+celsius\b"), " c "),
    (re.compile(r"\bsquare\s+(" + LENGTH_UNIT_RE + r")\b"), r" \1 2 "),
    (re.compile(r"\b(" + LENGTH_UNIT_RE + r")\s+squared?\b"), r" \1 2 "),
    (re.compile(r"\bcubic\s+(" + LENGTH_UNIT_RE + r")\b"), r" \1 3 "),
    (re.compile(r"\b(" + LENGTH_UNIT_RE + r")\s+cubed\b"), r" \1 3 "),
    (re.compile(r"\bcentimet(?:er|re)s?\b"), " cm "),
    (re.compile(r"\bmillimet(?:er|re)s?\b"), " mm "),
    (re.compile(r"\bkilomet(?:er|re)s?\b"), " km "),
    (re.compile(r"\bmet(?:er|re)s?\b"), " m "),
    (re.compile(r"\bkilograms?\b"), " kg "),
    (re.compile(r"\bmilligrams?\b"), " mg "),
    (re.compile(r"\bgrams?\b"), " g "),
    (re.compile(r"\bmillilit(?:er|re)s?\b"), " ml "),
    (re.compile(r"\blit(?:er|re)s?\b"), " l "),
    (re.compile(r"\binch(?:es)?\b"), " in "),
    (re.compile(r"\bfeet\b|\bfoot\b"), " ft "),
)

TRANSCRIPTION_PROMPT_TEMPLATE = """You are a transcription tool. Do not solve the problem and do not say which option is correct.

The image shows part of a printed exam page. Transcribe only the multiple-choice item numbered {qnum}. Ignore page headers, page footers, other items, and the words "Use this space for computations".

Transcribe exactly what is printed:
1. "stem": the question text of item {qnum}, from the first word after the item number up to the last word before the first answer option, including any sentence that continues after a diagram or table. Do not put any answer option inside the stem. If the item has a table, transcribe the table cells row by row inside the stem. Do not describe diagrams, graphs, or pictures, and do not transcribe labels that appear only inside a diagram or graph.
2. "options": every printed answer option of item {qnum}, keyed by its printed label exactly as printed ("1", "2", "3", "4" or "A", "B", "C", "D", "E"). Write each option's content exactly as printed, as one JSON string per option; if an option spans several lines, join the lines with "; ". Do not add options that are not printed. Do not omit any printed option.

Write mathematics in plain text: exponents as x^2, fractions as 5/3, mixed numbers as 2 1/3, roots as sqrt(10), coordinates as (-1, -3), subscripts as a_n, and keep symbols such as degrees, pi, <=, >=, and the minus sign as printed.

Reply with a JSON object and nothing else:
{{"stem": "...", "options": {{"1": "...", "2": "...", "3": "...", "4": "..."}}}}
"""


@dataclass
class FidelityScore:
    stem_f1: float
    stem_precision: float
    stem_recall: float
    option_scores: dict[str, float]
    option_matched: dict[str, bool]
    n_options_text_layer: int
    n_options_transcribed: int
    option_count_equal: bool
    glue_fields: list[str]
    truncated_fields: list[str]
    flags: list[str]
    verdict: str
    category: str


def require_cuda() -> None:
    import torch

    if not torch.cuda.is_available():
        raise RuntimeError("CUDA GPU is required; torch.cuda.is_available() is False.")
    if torch.cuda.device_count() < 1:
        raise RuntimeError("CUDA GPU is required; torch.cuda.device_count() is 0.")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def dump_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# Population


def build_population(items: list[dict[str, Any]]) -> dict[str, list[str]]:
    """Return item id -> list of claimed-cell labels the item belongs to."""
    by_id = {str(item["id"]): item for item in items}
    algebra_ids = [str(i) for i in json.loads(ALGEBRA_PRIMARY_IDS_PATH.read_text(encoding="utf-8"))]
    primary_ids = [str(i) for i in json.loads(PRIMARY_IDS_PATH.read_text(encoding="utf-8"))]
    membership: dict[str, list[str]] = {}

    def add(item_id: str, cell: str) -> None:
        membership.setdefault(item_id, [])
        if cell not in membership[item_id]:
            membership[item_id].append(cell)

    for item_id in algebra_ids:
        item = by_id[item_id]
        if item["claim"] == "algebra-i":
            add(item_id, CELL_ALGEBRA_I)
        elif item["claim"] == "algebra-ii":
            add(item_id, CELL_ALGEBRA_II)
        else:
            raise RuntimeError(f"unexpected claim in algebra primary ids: {item_id}")
    for item_id in primary_ids:
        item = by_id[item_id]
        if item.get("authority") == "nyregents" and item.get("claim") == "geometry":
            add(item_id, CELL_GEOMETRY_PHI4)
    geometry = [
        item
        for item in items
        if item.get("authority") == "nyregents"
        and item.get("claim") == "geometry"
        and item.get("responseType") == "selected"
    ]
    for scored in score_program(geometry, middle_value_option):
        add(str(scored.item["id"]), CELL_GEOMETRY_LC)
    eqao = [
        item
        for item in items
        if item.get("authority") == "eqao"
        and item.get("claim") == "g6"
        and item.get("responseType") == "selected"
    ]
    for scored in score_program(eqao, middle_value_option):
        add(str(scored.item["id"]), CELL_EQAO_G6_LC)
    return membership


def population_counts(membership: dict[str, list[str]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for cells in membership.values():
        for cell in cells:
            counts[cell] = counts.get(cell, 0) + 1
    counts["union"] = len(membership)
    return counts


def audited_ids() -> dict[str, dict[str, Any]]:
    payload = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    return {str(row["id"]): row for row in payload["rows"]}


def development_ids(items: list[dict[str, Any]], membership: dict[str, list[str]], n_per_cell: int, seed: int) -> list[str]:
    """Disjoint development items: same PDFs and layout, not in the population or the audit."""
    import random

    excluded = set(membership) | set(audited_ids())
    pools: dict[str, list[str]] = {"geometry": [], "algebra-i": [], "algebra-ii": [], "eqao": []}
    for item in items:
        if item.get("responseType") != "selected" or not (item.get("choices") or {}):
            continue
        item_id = str(item["id"])
        if item_id in excluded:
            continue
        if item.get("authority") == "nyregents" and item.get("claim") in pools:
            pools[str(item["claim"])].append(item_id)
        elif item.get("authority") == "eqao":
            pools["eqao"].append(item_id)
    rng = random.Random(seed)
    chosen: list[str] = []
    for name in sorted(pools):
        pool = sorted(pools[name])
        rng.shuffle(pool)
        chosen.extend(pool[:n_per_cell])
    return chosen


# ---------------------------------------------------------------------------
# Page rendering


@dataclass
class ItemPages:
    pdf: str | None
    page_index: int | None
    clip: tuple[float, float, float, float] | None
    locate_reason: str
    png_paths: list[str]
    continuation_page_index: int | None
    stem_hits_on_page: int


def stem_needles(item: dict[str, Any]) -> tuple[list[str], list[str]]:
    stem_words = [tok.lower() for tok in re.findall(r"[A-Za-z]{4,}", str(item.get("stem") or ""))]
    option_words = [
        tok.lower()
        for text in (item.get("choices") or {}).values()
        for tok in re.findall(r"[A-Za-z0-9]{3,}", str(text))
    ]
    return stem_words[:12], option_words[:12]


def needle_hits(blob: str, needles: tuple[list[str], list[str]]) -> tuple[int, int]:
    stem_words, option_words = needles
    return (
        sum(1 for needle in stem_words if needle in blob),
        sum(1 for needle in option_words if needle in blob),
    )


def best_text_page(document: fitz.Document, item: dict[str, Any]) -> tuple[int | None, int]:
    needles = stem_needles(item)
    if len(needles[0]) + len(needles[1]) < 3:
        return None, 0
    best_index: int | None = None
    best_hits: tuple[int, int] = (0, 0)
    for page_index in range(len(document)):
        hits = needle_hits(document[page_index].get_text("text").lower(), needles)
        if hits > best_hits:
            best_hits = hits
            best_index = page_index
    if sum(best_hits) < 3:
        return None, sum(best_hits)
    return best_index, sum(best_hits)


def regents_heading_y(page: fitz.Page, number: int) -> list[float]:
    """Bare-number Regents question headings in the left column; option labels such as (1) are not headings."""
    from vlm_backsolve_lib import line_records

    pattern = re.compile(rf"^{number}(?!\d)\s+[A-Za-z\(\"“]")
    found: list[float] = []
    for x0, y0, text, _rect in line_records(page):
        if x0 > page.rect.width * 0.42:
            continue
        if pattern.match(text.strip()):
            found.append(y0)
    return found


def regents_crop(document: fitz.Document, item: dict[str, Any], qnum: int) -> tuple[int, fitz.Rect, int] | None:
    """Among bare-number headings for qnum, pick the crop whose text best matches the census stem, then the census options."""
    needles = stem_needles(item)
    best: tuple[int, tuple[int, int], fitz.Rect] | None = None
    for page_index in range(len(document)):
        page = document[page_index]
        for top in regents_heading_y(page, qnum):
            next_tops = [y for y in regents_heading_y(page, qnum + 1) if y > top + 20]
            bottom = min(next_tops) if next_tops else None
            y0 = max(page.rect.y0, top - CROP_PAD_PT)
            y1 = page.rect.y1 if bottom is None else min(page.rect.y1, bottom + CROP_PAD_PT)
            if y1 - y0 < 72.0:
                y1 = page.rect.y1
            rect = fitz.Rect(page.rect.x0, y0, page.rect.x1, y1)
            hits = needle_hits(page.get_text("text", clip=rect).lower(), needles)
            if best is None or hits > best[1]:
                best = (page_index, hits, rect)
    if best is None:
        return None
    return best[0], best[2], sum(best[1])


def locate_item(document: fitz.Document, item: dict[str, Any]) -> tuple[int | None, fitz.Rect | None, str, int]:
    qnum = question_number(item)
    if item.get("authority") == "eqao" or qnum is None:
        page_index, hits = best_text_page(document, item)
        if page_index is None:
            return None, None, "page_not_found", hits
        return page_index, document[page_index].rect, "text_page", hits
    found = regents_crop(document, item, qnum)
    if found is not None:
        page_index, rect, hits = found
        return page_index, rect, "question_crop", hits
    page_index, hits = best_text_page(document, item)
    if page_index is None:
        return None, None, "page_not_found", hits
    return page_index, document[page_index].rect, "text_page", hits


def continuation_clip(document: fitz.Document, page_index: int, clip: fitz.Rect, qnum: int | None) -> tuple[int, fitz.Rect] | None:
    """If the item crop runs to the page bottom and the next item starts well below the top of the next page, return that top region."""
    if qnum is None:
        return None
    page = document[page_index]
    if abs(clip.y1 - page.rect.y1) > 1e-3:
        return None
    if page_index + 1 >= len(document):
        return None
    next_page = document[page_index + 1]
    next_tops = regents_heading_y(next_page, qnum + 1)
    if not next_tops:
        return None
    next_top = min(next_tops)
    if next_top < CONTINUATION_MIN_HEADING_Y_PT:
        return None
    rect = fitz.Rect(next_page.rect.x0, next_page.rect.y0, next_page.rect.x1, min(next_page.rect.y1, next_top + CROP_PAD_PT))
    return page_index + 1, rect


def render_item_pages(
    item: dict[str, Any],
    pdf_index: dict[str, Path],
    document_cache: dict[Path, fitz.Document],
    pages_dir: Path,
    force: bool = False,
) -> ItemPages:
    from vlm_backsolve_lib import resolve_pdf

    item_id = str(item["id"])
    pdf = resolve_pdf(item, pdf_index)
    if pdf is None:
        return ItemPages(None, None, None, "pdf_missing", [], None, 0)
    if pdf not in document_cache:
        document_cache[pdf] = fitz.open(pdf)
    document = document_cache[pdf]
    page_index, clip, reason, hits = locate_item(document, item)
    if page_index is None or clip is None:
        return ItemPages(str(pdf.relative_to(ROOT)), None, None, reason, [], None, hits)
    matrix = fitz.Matrix(DPI / 72.0, DPI / 72.0)
    main_png = pages_dir / f"{item_id}.png"
    pages_dir.mkdir(parents=True, exist_ok=True)
    if force or not main_png.exists() or main_png.stat().st_size < 100:
        pix = document[page_index].get_pixmap(matrix=matrix, clip=clip)
        pix.save(str(main_png))
    png_paths = [str(main_png.relative_to(ROOT))]
    continuation = None if reason != "question_crop" else continuation_clip(document, page_index, clip, question_number(item))
    continuation_index: int | None = None
    if continuation is not None:
        continuation_index, rect = continuation
        cont_png = pages_dir / f"{item_id}-continuation.png"
        if force or not cont_png.exists() or cont_png.stat().st_size < 100:
            pix = document[continuation_index].get_pixmap(matrix=matrix, clip=rect)
            pix.save(str(cont_png))
        png_paths.append(str(cont_png.relative_to(ROOT)))
    return ItemPages(
        pdf=str(pdf.relative_to(ROOT)),
        page_index=page_index,
        clip=(clip.x0, clip.y0, clip.x1, clip.y1),
        locate_reason=reason,
        png_paths=png_paths,
        continuation_page_index=continuation_index,
        stem_hits_on_page=hits,
    )


# ---------------------------------------------------------------------------
# VLM


def load_vlm() -> tuple[Any, Any]:
    import torch
    from transformers import AutoProcessor, Qwen2VLForConditionalGeneration

    require_cuda()
    if not SNAPSHOT_PATH.exists():
        raise RuntimeError(f"cached snapshot missing: {SNAPSHOT_PATH}")
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
    os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
    torch.manual_seed(SEED)
    torch.cuda.manual_seed_all(SEED)
    processor = AutoProcessor.from_pretrained(str(SNAPSHOT_PATH), local_files_only=True)
    model = Qwen2VLForConditionalGeneration.from_pretrained(
        str(SNAPSHOT_PATH),
        torch_dtype=torch.bfloat16,
        device_map="cuda",
        local_files_only=True,
        attn_implementation="sdpa",
    )
    model.eval()
    return processor, model


def transcription_prompt(qnum: int) -> str:
    return TRANSCRIPTION_PROMPT_TEMPLATE.format(qnum=qnum).rstrip() + "\n"


def generate_transcription(processor: Any, model: Any, image_paths: list[Path], prompt: str) -> str:
    import torch
    from qwen_vl_utils import process_vision_info

    content: list[dict[str, str]] = [{"type": "image", "image": str(path)} for path in image_paths]
    content.append({"type": "text", "text": prompt})
    messages = [{"role": "user", "content": content}]
    text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    image_inputs, video_inputs = process_vision_info(messages)
    processor_kwargs: dict[str, Any] = {
        "text": [text],
        "images": image_inputs,
        "padding": True,
        "return_tensors": "pt",
    }
    if video_inputs:
        processor_kwargs["videos"] = video_inputs
    inputs = processor(**processor_kwargs).to(model.device)
    with torch.inference_mode():
        output_ids = model.generate(**inputs, max_new_tokens=MAX_NEW_TOKENS, do_sample=False)
    generated = output_ids[0, inputs["input_ids"].shape[1] :]
    return processor.batch_decode([generated], skip_special_tokens=True)[0].strip()


INVALID_JSON_ESCAPE_RE = re.compile(r'\\(?=[A-Za-z]{2})|\\(?!["\\/bfnrtu])')


def parse_json_object(text: str) -> dict[str, Any] | None:
    """Strip an optional markdown fence and raw_decode from the first brace. If that fails, double backslashes that start a LaTeX command (two or more letters) or an invalid JSON escape and decode once more."""
    stripped = text.strip()
    stripped = re.sub(r"^```(?:json)?\s*", "", stripped)
    stripped = re.sub(r"\s*```$", "", stripped)
    start = stripped.find("{")
    if start < 0:
        return None
    body = stripped[start:]
    payload: Any = None
    try:
        payload, _end = json.JSONDecoder().raw_decode(body)
    except json.JSONDecodeError:
        candidate = INVALID_JSON_ESCAPE_RE.sub(r"\\\\", body)
        try:
            payload, _end = json.JSONDecoder().raw_decode(candidate)
        except json.JSONDecodeError:
            return None
    if not isinstance(payload, dict):
        return None
    return payload


def map_option_label(raw: str) -> str | None:
    label = raw.strip().strip("()").strip().upper()
    if not label:
        return None
    if label in DIGIT_LABELS:
        return DIGIT_LABELS[label]
    if label in FGHJ_LABELS:
        return FGHJ_LABELS[label]
    if label in LETTER_ORDER:
        return label
    return None


def transcribed_options(payload: dict[str, Any]) -> dict[str, str]:
    raw = payload.get("options")
    mapped: dict[str, str] = {}
    if isinstance(raw, dict):
        for key, value in raw.items():
            letter = map_option_label(str(key))
            if letter is None or letter in mapped:
                continue
            text = "" if value is None else str(value)
            if text.strip():
                mapped[letter] = text
    elif isinstance(raw, list):
        for index, value in enumerate(raw):
            if index >= len(LETTER_ORDER):
                break
            if isinstance(value, dict):
                label = value.get("label") or value.get("key") or LETTER_ORDER[index]
                letter = map_option_label(str(label)) or LETTER_ORDER[index]
                text = str(value.get("text") or value.get("content") or value.get("value") or "")
            else:
                letter = LETTER_ORDER[index]
                text = str(value)
            if text.strip() and letter not in mapped:
                mapped[letter] = text
    return mapped


# ---------------------------------------------------------------------------
# Normalization and scoring


def replace_tex_command(match: re.Match[str]) -> str:
    name = match.group(1)
    return f" {name} " if name.lower() in KEEP_TEX_NAMES else " "


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = LATEX_COMMAND_RE.sub(replace_tex_command, text)
    text = text.replace("_", "").replace("{", "").replace("}", "")
    text = text.lower()
    for pattern, replacement in UNIT_REPLACEMENTS:
        text = pattern.sub(replacement, text)
    text = LETTER_DIGIT_BOUNDARY_RE.sub(" ", text)
    return text


def strip_leading_item_number(vlm_stem: str, qnum: int | None) -> str:
    if qnum is None:
        return vlm_stem
    return re.sub(rf"^\s*\(?{qnum}\)?[.)]?\s+", "", vlm_stem, count=1)


def strip_bracket_descriptions(vlm_stem: str) -> str:
    return BRACKET_DESCRIPTION_RE.sub(" ", vlm_stem)


def cut_echoed_options(stem_tokens: list[str], vlm_options: dict[str, str]) -> list[str]:
    """If the model echoed two or more of its own transcribed options inside the stem, cut the stem at the first echo."""
    option_token_lists = [tokens(text) for text in vlm_options.values()]
    option_token_lists = [toks for toks in option_token_lists if len(toks) >= ECHO_MIN_OPTION_TOKENS]
    positions: list[int] = []
    for option_tokens in option_token_lists:
        width = len(option_tokens)
        for start in range(0, len(stem_tokens) - width + 1):
            if stem_tokens[start : start + width] == option_tokens:
                positions.append(start)
                break
    if len(positions) < ECHO_MIN_OPTIONS_FOUND:
        return stem_tokens
    return stem_tokens[: min(positions)]


def clean_vlm_stem(payload: dict[str, Any], qnum: int | None) -> str:
    stem = str(payload.get("stem") or "")
    stem = strip_leading_item_number(stem, qnum)
    return strip_bracket_descriptions(stem)


def tokens(text: str) -> list[str]:
    return [tok for tok in TOKEN_RE.findall(normalize_text(text)) if tok not in MATH_WORD_DROP]


def compact(text: str) -> str:
    return "".join(tokens(text))


def multiset_overlap(left: list[str], right: list[str]) -> int:
    counts: dict[str, int] = {}
    for tok in right:
        counts[tok] = counts.get(tok, 0) + 1
    overlap = 0
    for tok in left:
        if counts.get(tok, 0) > 0:
            counts[tok] -= 1
            overlap += 1
    return overlap


def precision_recall_f1(text_layer: str, transcription: str) -> tuple[float, float, float]:
    """Precision: share of text-layer tokens found in the transcription. Recall: share of transcription tokens found in the text layer."""
    return precision_recall_f1_tokens(tokens(text_layer), tokens(transcription))


def precision_recall_f1_tokens(left: list[str], right: list[str]) -> tuple[float, float, float]:
    if not left and not right:
        return 1.0, 1.0, 1.0
    if not left or not right:
        return 0.0, 0.0, 0.0
    overlap = multiset_overlap(left, right)
    precision = overlap / len(left)
    recall = overlap / len(right)
    if overlap == 0:
        return precision, recall, 0.0
    return precision, recall, 2 * precision * recall / (precision + recall)


def character_ratio(text_layer: str, transcription: str) -> float:
    left = compact(text_layer)
    right = compact(transcription)
    if not left and not right:
        return 1.0
    if not left or not right:
        return 0.0
    return SequenceMatcher(None, left, right, autojunk=False).ratio()


def option_score(text_layer: str, transcription: str) -> float:
    if compact(text_layer) == compact(transcription):
        return 1.0
    _p, _r, f1 = precision_recall_f1(text_layer, transcription)
    return max(f1, character_ratio(text_layer, transcription))


def census_options(item: dict[str, Any]) -> dict[str, str]:
    out: dict[str, str] = {}
    for raw_key, value in (item.get("choices") or {}).items():
        letter = str(raw_key).strip().upper()[:1]
        out[letter] = str(value)
    return out


def score_fidelity(
    item: dict[str, Any],
    payload: dict[str, Any] | None,
    *,
    stem_threshold: float = STEM_F1_THRESHOLD,
    option_threshold: float = OPTION_MATCH_THRESHOLD,
) -> FidelityScore:
    text_options = census_options(item)
    letters = sorted(text_options)
    vlm_options = {} if payload is None else transcribed_options(payload)
    vlm_stem = "" if payload is None else clean_vlm_stem(payload, question_number(item))
    if payload is None or not vlm_options or not vlm_stem.strip():
        reason = "vlm_unparseable" if payload is None else ("vlm_no_options" if not vlm_options else "vlm_no_stem")
        return FidelityScore(
            stem_f1=0.0,
            stem_precision=0.0,
            stem_recall=0.0,
            option_scores={letter: 0.0 for letter in letters},
            option_matched={letter: False for letter in letters},
            n_options_text_layer=len(letters),
            n_options_transcribed=len(vlm_options),
            option_count_equal=False,
            glue_fields=[],
            truncated_fields=[],
            flags=[reason],
            verdict=VERDICT_UNVERIFIED,
            category=reason,
        )
    vlm_stem_tokens = cut_echoed_options(tokens(vlm_stem), vlm_options)
    stem_precision, stem_recall, stem_f1 = precision_recall_f1_tokens(tokens(str(item.get("stem") or "")), vlm_stem_tokens)
    option_scores: dict[str, float] = {}
    option_matched: dict[str, bool] = {}
    glue_fields: list[str] = []
    truncated_fields: list[str] = []
    if stem_precision < 1.0 - FIELD_EXTRA_SHARE_THRESHOLD:
        glue_fields.append("stem")
    if stem_recall < 1.0 - FIELD_EXTRA_SHARE_THRESHOLD:
        truncated_fields.append("stem")
    for letter in letters:
        text = text_options[letter]
        transcribed = vlm_options.get(letter, "")
        score = option_score(text, transcribed)
        option_scores[letter] = round(score, 4)
        option_matched[letter] = score >= option_threshold
        precision, recall, _f1 = precision_recall_f1(text, transcribed)
        if transcribed and precision < 1.0 - FIELD_EXTRA_SHARE_THRESHOLD:
            glue_fields.append(letter)
        if transcribed and recall < 1.0 - FIELD_EXTRA_SHARE_THRESHOLD:
            truncated_fields.append(letter)
    n_matched = sum(1 for letter in letters if option_matched[letter])
    option_count_equal = len(vlm_options) == len(letters)
    flags: list[str] = []
    if stem_f1 < stem_threshold:
        flags.append("stem_low")
    if "stem" in glue_fields:
        flags.append("stem_glue")
    if "stem" in truncated_fields:
        flags.append("stem_truncated")
    if not option_count_equal:
        flags.append("option_count_mismatch")
    missing_letters = [letter for letter in letters if letter not in vlm_options]
    if missing_letters:
        flags.append("option_missing_in_transcription")
    extra_letters = sorted(set(vlm_options) - set(letters))
    if extra_letters:
        flags.append("option_extra_in_transcription")
    if n_matched < len(letters):
        flags.append("option_low")
    wrong_option_set = n_matched < math.ceil(len(letters) / 2) if letters else True
    if wrong_option_set:
        flags.append("wrong_option_set")
    option_glue = [letter for letter in glue_fields if letter != "stem"]
    option_truncated = [letter for letter in truncated_fields if letter != "stem"]
    if option_glue:
        flags.append("option_glue")
    if option_truncated:
        flags.append("option_truncated")
    faithful = (
        stem_f1 >= stem_threshold
        and "stem" not in glue_fields
        and "stem" not in truncated_fields
        and option_count_equal
        and n_matched == len(letters)
        and len(letters) > 0
    )
    verdict = VERDICT_FAITHFUL if faithful else VERDICT_NOT_FAITHFUL
    if faithful:
        category = "match"
    elif wrong_option_set:
        category = "wrong_item"
    elif glue_fields:
        category = "ocr_glue"
    elif truncated_fields or missing_letters or extra_letters:
        category = "truncated"
    else:
        category = "option_mismatch"
    return FidelityScore(
        stem_f1=round(stem_f1, 4),
        stem_precision=round(stem_precision, 4),
        stem_recall=round(stem_recall, 4),
        option_scores=option_scores,
        option_matched=option_matched,
        n_options_text_layer=len(letters),
        n_options_transcribed=len(vlm_options),
        option_count_equal=option_count_equal,
        glue_fields=glue_fields,
        truncated_fields=truncated_fields,
        flags=flags,
        verdict=verdict,
        category=category,
    )


def numeric_faithful(item: dict[str, Any], vlm_options: dict[str, str]) -> bool | None:
    """Catalog-specific check: the leading number the lower-central rule parses from each text-layer option equals the one parsed from the transcription, and the option counts agree."""
    from addendum_lib import parse_leading_number

    text_options = census_options(item)
    if not vlm_options:
        return None
    if len(vlm_options) != len(text_options):
        return False
    for letter, text in text_options.items():
        if letter not in vlm_options:
            return False
        if parse_leading_number(text) != parse_leading_number(vlm_options[letter]):
            return False
    return True


def trailing_junk_only(item: dict[str, Any], vlm_options: dict[str, str], score: FidelityScore) -> bool:
    """Not faithful, but the stem passes, option counts agree, and every transcribed option is a token prefix of its text-layer option."""
    if score.verdict != VERDICT_NOT_FAITHFUL:
        return False
    if "stem" in score.glue_fields or "stem" in score.truncated_fields or "stem_low" in score.flags:
        return False
    if not score.option_count_equal:
        return False
    text_options = census_options(item)
    for letter, text in text_options.items():
        if letter not in vlm_options:
            return False
        text_tokens = tokens(text)
        vlm_tokens = tokens(vlm_options[letter])
        if not vlm_tokens or text_tokens[: len(vlm_tokens)] != vlm_tokens:
            return False
    return True


def fidelity_row(
    item: dict[str, Any],
    cells: list[str],
    pages: ItemPages,
    raw_vlm: str,
    payload: dict[str, Any] | None,
    score: FidelityScore,
    stage: str,
) -> dict[str, Any]:
    vlm_options = {} if payload is None else transcribed_options(payload)
    return {
        "id": item["id"],
        "cells": cells,
        "authority": item.get("authority"),
        "claim": item.get("claim"),
        "qnum": question_number(item),
        "stage": stage,
        "pdf": pages.pdf,
        "pageIndex": pages.page_index,
        "clip": pages.clip,
        "locateReason": pages.locate_reason,
        "pngs": pages.png_paths,
        "continuationPageIndex": pages.continuation_page_index,
        "stemHitsOnPage": pages.stem_hits_on_page,
        "textLayerStem": item.get("stem"),
        "textLayerOptions": census_options(item),
        "key": str(item.get("key") or "").strip().upper(),
        "rawVlm": raw_vlm,
        "vlmStem": None if payload is None else clean_vlm_stem(payload, question_number(item)),
        "vlmOptions": {} if payload is None else transcribed_options(payload),
        "stem_f1": score.stem_f1,
        "stem_precision": score.stem_precision,
        "stem_recall": score.stem_recall,
        "option_match": score.option_scores,
        "option_matched": score.option_matched,
        "printed_option_count": score.n_options_transcribed,
        "text_layer_option_count": score.n_options_text_layer,
        "option_count_equal": score.option_count_equal,
        "glue_fields": score.glue_fields,
        "truncated_fields": score.truncated_fields,
        "flags": score.flags,
        "verdict": score.verdict,
        "category": score.category,
        "numeric_faithful": numeric_faithful(item, vlm_options),
        "trailing_junk_only": trailing_junk_only(item, vlm_options, score),
    }


def rescore_row(row: dict[str, Any], item: dict[str, Any], stem_threshold: float, option_threshold: float) -> dict[str, Any]:
    payload = parse_json_object(str(row.get("rawVlm") or ""))
    score = score_fidelity(item, payload, stem_threshold=stem_threshold, option_threshold=option_threshold)
    vlm_options = {} if payload is None else transcribed_options(payload)
    updated = dict(row)
    updated.update(
        {
            "vlmStem": None if payload is None else clean_vlm_stem(payload, question_number(item)),
            "vlmOptions": vlm_options,
            "numeric_faithful": numeric_faithful(item, vlm_options),
            "trailing_junk_only": trailing_junk_only(item, vlm_options, score),
            "stem_f1": score.stem_f1,
            "stem_precision": score.stem_precision,
            "stem_recall": score.stem_recall,
            "option_match": score.option_scores,
            "option_matched": score.option_matched,
            "printed_option_count": score.n_options_transcribed,
            "option_count_equal": score.option_count_equal,
            "flags": score.flags,
            "verdict": score.verdict,
            "category": score.category,
            "glue_fields": score.glue_fields,
            "truncated_fields": score.truncated_fields,
        }
    )
    return updated


def confusion_matrix(rows: list[dict[str, Any]], audit: dict[str, dict[str, Any]]) -> dict[str, Any]:
    labels_human = ["match", "ocr_glue", "truncated", "wrong_item"]
    labels_machine = ["match", "ocr_glue", "truncated", "wrong_item", "option_mismatch", "vlm_unparseable", "vlm_no_options", "vlm_no_stem"]
    matrix: dict[str, dict[str, int]] = {h: {m: 0 for m in labels_machine} for h in labels_human}
    binary = {
        "human_match_machine_faithful": 0,
        "human_match_machine_not": 0,
        "human_dirty_machine_faithful": 0,
        "human_dirty_machine_not": 0,
        "machine_unverified": 0,
    }
    per_item: list[dict[str, Any]] = []
    for row in rows:
        human = audit[str(row["id"])]["label"]
        machine = str(row["category"])
        matrix[human][machine] += 1
        human_clean = human == "match"
        machine_clean = row["verdict"] == VERDICT_FAITHFUL
        if row["verdict"] == VERDICT_UNVERIFIED:
            binary["machine_unverified"] += 1
        elif human_clean and machine_clean:
            binary["human_match_machine_faithful"] += 1
        elif human_clean:
            binary["human_match_machine_not"] += 1
        elif machine_clean:
            binary["human_dirty_machine_faithful"] += 1
        else:
            binary["human_dirty_machine_not"] += 1
        per_item.append(
            {
                "id": row["id"],
                "human": human,
                "machine": machine,
                "verdict": row["verdict"],
                "stem_f1": row["stem_f1"],
                "option_match": row["option_match"],
                "flags": row["flags"],
                "humanNotes": audit[str(row["id"])].get("notes"),
            }
        )
    n = len(rows)
    agree_binary = binary["human_match_machine_faithful"] + binary["human_dirty_machine_not"]
    agree_category = sum(matrix[h][h] for h in labels_human)
    return {
        "n": n,
        "humanLabels": labels_human,
        "machineCategories": labels_machine,
        "matrix": matrix,
        "binary": binary,
        "binaryAgreement": agree_binary,
        "binaryAgreementRate": agree_binary / n if n else 0.0,
        "categoryAgreement": agree_category,
        "categoryAgreementRate": agree_category / n if n else 0.0,
        "perItem": per_item,
    }


def item_pngs_absolute(row: dict[str, Any]) -> list[Path]:
    return [ROOT / png for png in row.get("pngs") or []]


def score_to_dict(score: FidelityScore) -> dict[str, Any]:
    return asdict(score)
