"""Extract the question-to-standard map from NYSED Regents rating guides.

Every Algebra I and Algebra II rating guide ends with a table titled "Map to the
Learning Standards" whose rows are (question, type, credits, cluster). The cluster
column is a Common Core State Standards (CCSS) cluster code such as ``A-REI.B``.
This script reads that table for every administration in the masked-stem primary
population and writes one row per primary item.

Outputs (all under ``exports/standards-split/``):

- ``item-standards.jsonl``: item id, standard code, source pdf, page, question type,
  credits, and how the row was read.
- ``rating-guide-tables.json``: the full parsed table per rating guide, including
  constructed-response rows, so a reader can check the parse against the PDF.
- ``coverage.json``: items with a code over population, per cell, plus the read
  method counts and the glyph-reader evaluation.

Three read methods, recorded per row:

- ``text_layer``: the PDF text layer decodes to characters (47 of 56 guides).
- ``glyph_table``: the v202, June 2022, and August 2022 guides embed a Calibri
  subset whose ToUnicode map is broken; a glyph table derived from the v202 file's
  fixed header words decodes it. Any glyph outside the table decodes to U+FFFD and
  can never form a code.
- ``visual_glyph_match``: the remaining guides with unusable text layers embed
  CID-keyed subsets with no character mapping at all. Their glyphs are rendered and matched against templates from
  text-layer guides (``regents_glyph_reader``); a match below the score or margin
  floor raises.

Rows where two codes are overprinted at one cell (a correction drawn over a white
box; June 2018 Algebra II questions 2 and 3) are resolved by the same renderer:
the code that reads back as itself is the visible one.
"""

from __future__ import annotations

import argparse
import collections
import json
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable

import pymupdf

from regents_glyph_reader import RENDER_ZOOM, GlyphTemplateLibrary, build_template_library, is_table_body_span

REPO_ROOT = Path(__file__).resolve().parent.parent
PRIMARY_IDS_PATH = REPO_ROOT / "exports/addendum-gpu/masked-stem-algebra-primary-item-ids.json"
ITEMS_PATH = REPO_ROOT / "data/items.jsonl"
RAW_DIRECTORIES = {
    "algebra-i": REPO_ROOT / "data/raw/regents-alg1",
    "algebra-ii": REPO_ROOT / "data/raw/regents-alg2",
}
OUTPUT_DIRECTORY = REPO_ROOT / "exports/standards-split"

# Template sources for the visual reader: text-layer guides spanning both courses,
# both font flavours (TrueType and CFF Calibri), and the 2015 to 2026 span.
TEMPLATE_GUIDES = (
    "regents-alg1/algone12015-rg.pdf",
    "regents-alg1/algone62018-rg.pdf",
    "regents-alg1/algone12024-rg.pdf",
    "regents-alg1/algone-12025-rg.pdf",
    "regents-alg2/algtwo12017-rg.pdf",
    "regents-alg2/algtwo-12026-rg.pdf",
)
# Characters the table can contain: cluster codes, digits, and the two type words.
REQUIRED_TEMPLATE_LABELS = frozenset("ABCDEFILNPQRST0123456789-.MultipleChoiceConstructedResponse")

ITEM_ID_PATTERN = re.compile(r"^nyregents-(algebra-i{1,2})-(\d{4}|unknown)-(jan|jun|aug|unk)-q(\d+)$")
EXAM_FILENAME_PATTERN = re.compile(r"^(alg(?:one|two)-?(?:\d+|v\d+))-?exam")
# The separator after the category letter is a hyphen; one guide prints a period
# (August 2024 Algebra II question 10 reads ``S.CP.B``). The period before the
# cluster letter is occasionally absent from the text layer (January 2016 Algebra I
# question 2 reads ``N-QA``). Both are normalised against the known domains.
CLUSTER_CODE_PATTERN = re.compile(r"^([A-Z])[-.]([A-Z]{1,3})\.?([A-Z])$")
KNOWN_DOMAINS: dict[str, frozenset[str]] = {
    "N": frozenset({"RN", "Q", "CN", "VM"}),
    "A": frozenset({"SSE", "APR", "CED", "REI"}),
    "F": frozenset({"IF", "BF", "LE", "TF"}),
    "G": frozenset({"CO", "SRT", "C", "GPE", "GMD", "MG"}),
    "S": frozenset({"ID", "IC", "CP", "MD"}),
}
ROW_BUCKET_POINTS = 4.0
FRAGMENT_GAP_POINTS = 2.5
MAX_CLUSTER_FRAGMENTS = 4
TYPE_WORD_WINDOW_POINTS = 14.0
QUESTION_TYPE_WORDS = {"Multiple": "Multiple Choice", "Constructed": "Constructed Response"}
MULTIPLE_CHOICE_QUESTION_COUNT = 24
MIN_TABLE_CHARACTERS = 40
UNDECODABLE = "\ufffd"

# One Calibri subset encoding recurs in the v202, June 2022, and August 2022 guides:
# the text layer holds glyph ids that land in Latin Extended-A/B (lowercase), the
# Greek block (digits at 0x3EC + d, hyphen 0x372, period 0x358), and the C0 control
# range (uppercase). The table below was read off the fixed header words of the v202
# guide (Map to the Learning Standards, Algebra I, Question, Type, Credits, Cluster,
# Multiple Choice, Constructed Response) and the domain letters of its cluster codes.
# A page is decoded with it only when most of its table characters fall in those
# ranges; any glyph outside the table decodes to U+FFFD and can never form a code.
LATIN_EXTENDED_GLYPH_TABLE: dict[int, str] = {
    0x03: " ",
    # Glyph 0x20 sits between the period and the cluster letter of every code in this
    # encoding and prints nothing; it is a non-printing glyph, not a word break.
    0x20: "",
    0x04: "A",
    0x11: "B",
    0x12: "C",
    0x18: "D",
    0x1C: "E",
    0x26: "F",
    0x2F: "I",
    0x3E: "L",
    0x44: "M",
    0x45: "N",
    0x57: "P",
    0x59: "Q",
    0x5A: "R",
    0x5E: "S",
    0x64: "T",
    0x102: "a",
    0x10F: "b",
    0x110: "c",
    0x11A: "d",
    0x11E: "e",
    0x150: "g",
    0x15A: "h",
    0x15D: "i",
    0x16F: "l",
    0x176: "n",
    0x17D: "o",
    0x189: "p",
    0x18C: "r",
    0x190: "s",
    0x19A: "t",
    0x1B5: "u",
    0x1C7: "y",
    0x372: "-",
    0x358: ".",
}
for digit in range(10):
    LATIN_EXTENDED_GLYPH_TABLE[0x3EC + digit] = str(digit)
GLYPH_TABLE_CODE_POINTS = frozenset(code for code in LATIN_EXTENDED_GLYPH_TABLE if code >= 0x100)

CharacterReader = Callable[[pymupdf.Page, dict[str, object]], str]


@dataclass
class Word:
    x0: float
    x1: float
    y_center: float
    text: str
    characters: list[dict[str, object]]


def normalize_cluster_code(word: str) -> str | None:
    """Return the canonical cluster code, or None when the word is not a full code.

    A dotted word with an unknown domain raises. A dot-less word with an unknown
    domain is a fragment such as ``F-IF`` and returns None so the caller keeps merging.
    """
    match = CLUSTER_CODE_PATTERN.match(word)
    if match is None:
        return None
    category, domain, cluster_letter = match.groups()
    known = category in KNOWN_DOMAINS and domain in KNOWN_DOMAINS[category]
    if not known:
        if "." in word[2:]:
            raise ValueError(f"unknown CCSS domain in cluster code {word!r}")
        return None
    return f"{category}-{domain}.{cluster_letter}"


def text_layer_reader(_page: pymupdf.Page, character: dict[str, object]) -> str:
    return str(character["c"])


def glyph_table_reader(glyph_table: dict[int, str]) -> CharacterReader:
    def read(_page: pymupdf.Page, character: dict[str, object]) -> str:
        return glyph_table.get(ord(str(character["c"])), UNDECODABLE)

    return read


def visual_reader(library: GlyphTemplateLibrary, source: str, zoom: float) -> CharacterReader:
    def read(page: pymupdf.Page, character: dict[str, object]) -> str:
        return library.read(page, character, source, zoom)

    return read


def page_spans(page: pymupdf.Page) -> list[dict[str, object]]:
    raw = page.get_text("rawdict")
    return [span for block in raw["blocks"] for line in block.get("lines", []) for span in line["spans"]]


def page_encoding(spans: list[dict[str, object]]) -> str:
    """Classify how the Calibri table spans on a page encode their characters.

    ``text``: ordinary characters. ``glyph_table``: the Latin Extended subset encoding
    above. ``cid_unmapped``: sequential glyph ids in the C0 control range with no
    character mapping, read visually. Pages whose table is not set in Calibri (the
    2014 guides use NewCaledonia) are ``text``.
    """
    counts = collections.Counter()
    for span in spans:
        if not is_table_body_span(span):
            continue
        for character in span["chars"]:
            code = ord(str(character["c"]))
            if code in (0x20, 0x01, 0x03):
                continue
            if 0x21 <= code < 0x7F:
                counts["text"] += 1
            elif code in GLYPH_TABLE_CODE_POINTS:
                counts["glyph_table"] += 1
            elif code < 0x20:
                counts["control"] += 1
            else:
                counts["other"] += 1
    total = sum(counts.values())
    if total < MIN_TABLE_CHARACTERS:
        return "text"
    if counts["text"] > total / 2:
        return "text"
    if counts["glyph_table"] > total / 2:
        return "glyph_table"
    if counts["control"] > total / 2:
        return "cid_unmapped"
    raise ValueError(f"cannot classify table encoding from character counts {dict(counts)}")


def span_words(page: pymupdf.Page, spans: list[dict[str, object]], reader: CharacterReader) -> list[Word]:
    """Split table-body spans into words at blank characters, keeping character boxes."""
    words: list[Word] = []
    for span in spans:
        current: list[tuple[str, dict[str, object]]] = []

        def flush() -> None:
            if not current:
                return
            boxes = [tuple(float(v) for v in character["bbox"]) for _label, character in current]
            x0 = min(box[0] for box in boxes)
            x1 = max(box[2] for box in boxes)
            y_center = (min(box[1] for box in boxes) + max(box[3] for box in boxes)) / 2.0
            words.append(Word(x0, x1, y_center, "".join(label for label, _character in current), [c for _l, c in current]))
            current.clear()

        for character in span["chars"]:
            label = reader(page, character)
            if label == "":
                continue
            if label.isspace():
                flush()
                continue
            current.append((label, character))
        flush()
    return words


def merge_code_fragments(words: list[Word]) -> list[Word]:
    """Merge fragments such as ``F-``, ``IF``, ``.A`` back into one cluster code word.

    Fragments of one code can sit in different spans with vertical centres a few
    points apart, so words are first grouped into rows (a new row starts where the
    vertical gap exceeds ``ROW_BUCKET_POINTS``) and ordered left to right within a row.
    """
    by_y = sorted(words, key=lambda w: w.y_center)
    rows: list[list[Word]] = []
    for word in by_y:
        if rows and word.y_center - rows[-1][-1].y_center <= ROW_BUCKET_POINTS:
            rows[-1].append(word)
        else:
            rows.append([word])
    ordered = [word for row in rows for word in sorted(row, key=lambda w: w.x0)]
    merged: list[Word] = []
    index = 0
    while index < len(ordered):
        word = ordered[index]
        consumed = 1
        if normalize_cluster_code(word.text) is None:
            joined_text = word.text
            joined_characters = list(word.characters)
            last_x1 = word.x1
            for extra in range(1, MAX_CLUSTER_FRAGMENTS):
                if index + extra >= len(ordered):
                    break
                following = ordered[index + extra]
                gap = following.x0 - last_x1
                if abs(following.y_center - word.y_center) > ROW_BUCKET_POINTS or not -FRAGMENT_GAP_POINTS <= gap < FRAGMENT_GAP_POINTS:
                    break
                joined_text += following.text
                joined_characters.extend(following.characters)
                last_x1 = following.x1
                if normalize_cluster_code(joined_text) is not None:
                    word = Word(word.x0, last_x1, word.y_center, joined_text, joined_characters)
                    consumed = extra + 1
                    break
        merged.append(word)
        index += consumed
    return merged


def rows_from_words(
    words: list[Word],
    page: pymupdf.Page,
    page_number: int,
    source: str,
    library: GlyphTemplateLibrary,
    read_method: str,
    render_scale: float | None,
) -> list[dict[str, object]]:
    code_words = [w for w in words if normalize_cluster_code(w.text) is not None]
    type_words = [w for w in words if w.text in QUESTION_TYPE_WORDS]
    rows_by_question: dict[int, dict[str, object]] = {}
    grouped: dict[int, list[Word]] = collections.defaultdict(list)
    for code_word in code_words:
        same_row = [w for w in words if abs(w.y_center - code_word.y_center) <= ROW_BUCKET_POINTS and w.x0 < code_word.x0]
        integers = sorted((w for w in same_row if w.text.isdigit()), key=lambda w: w.x0)
        if len(integers) != 2:
            raise ValueError(f"{source} page {page_number}: row for {code_word.text} at y={code_word.y_center:.1f} has {len(integers)} integer cells")
        grouped[int(integers[0].text)].append(code_word)
        nearby_types = [w for w in type_words if abs(w.y_center - code_word.y_center) <= TYPE_WORD_WINDOW_POINTS]
        if not nearby_types:
            raise ValueError(f"{source} page {page_number}: no question type near {code_word.text}")
        nearest_type = min(nearby_types, key=lambda w: abs(w.y_center - code_word.y_center))
        rows_by_question.setdefault(
            int(integers[0].text),
            {"question": int(integers[0].text), "questionType": QUESTION_TYPE_WORDS[nearest_type.text], "credits": int(integers[1].text), "page": page_number},
        )
    rows: list[dict[str, object]] = []
    for question, candidates in sorted(grouped.items()):
        codes = sorted({normalize_cluster_code(w.text) for w in candidates})
        method = read_method
        if len(codes) > 1:
            visible = [w for w in candidates if library.word_is_visible(page, w.characters, w.text)]
            visible_codes = sorted({normalize_cluster_code(w.text) for w in visible})
            if len(visible_codes) != 1:
                raise ValueError(f"{source} page {page_number}: question {question} has overprinted codes {codes}; visible {visible_codes}")
            codes = visible_codes
            method = f"{read_method}+visual_overprint_resolution"
        row = dict(rows_by_question[question])
        row["cluster"] = codes[0]
        printed = sorted({w.text for w in candidates if normalize_cluster_code(w.text) == codes[0]})
        row["clusterAsPrinted"] = printed[0]
        row["readMethod"] = method
        if render_scale is not None:
            row["renderScale"] = round(render_scale, 4)
        rows.append(row)
    return rows


def parse_map_rows(pdf_path: Path, library: GlyphTemplateLibrary) -> list[dict[str, object]]:
    """Parse every (question, type, credits, cluster) row from a rating guide."""
    document = pymupdf.open(pdf_path)
    rows: list[dict[str, object]] = []
    for page_index in range(len(document)):
        page = document[page_index]
        spans = page_spans(page)
        encoding = page_encoding(spans)
        render_scale: float | None = None
        if encoding == "glyph_table":
            spans = [span for span in spans if is_table_body_span(span)]
            reader, method = glyph_table_reader(LATIN_EXTENDED_GLYPH_TABLE), "glyph_table"
        elif encoding == "cid_unmapped":
            spans = [span for span in spans if is_table_body_span(span)]
            zoom = library.page_zoom(page, spans, pdf_path.name)
            render_scale = zoom / RENDER_ZOOM
            reader, method = visual_reader(library, pdf_path.name, zoom), "visual_glyph_match"
        else:
            reader, method = text_layer_reader, "text_layer"
        words = merge_code_fragments(span_words(page, spans, reader))
        rows.extend(rows_from_words(words, page, page_index + 1, pdf_path.name, library, method, render_scale))
    document.close()
    if not rows:
        raise ValueError(f"{pdf_path.name}: no map rows found")
    return rows


def validate_table(pdf_name: str, rows: list[dict[str, object]]) -> None:
    questions = [int(row["question"]) for row in rows]
    if len(questions) != len(set(questions)):
        duplicates = [q for q, count in collections.Counter(questions).items() if count > 1]
        raise ValueError(f"{pdf_name}: duplicate question numbers {duplicates}")
    if set(questions) != set(range(1, max(questions) + 1)):
        raise ValueError(f"{pdf_name}: question numbers {sorted(set(questions))} are not contiguous from 1")
    multiple_choice = sorted(int(row["question"]) for row in rows if row["questionType"] == "Multiple Choice")
    if multiple_choice != list(range(1, MULTIPLE_CHOICE_QUESTION_COUNT + 1)):
        raise ValueError(f"{pdf_name}: multiple-choice questions are {multiple_choice}")


def rating_guide_path(course: str, source_url: str) -> Path:
    exam_filename = source_url.rsplit("/", 1)[-1]
    match = EXAM_FILENAME_PATTERN.match(exam_filename)
    if match is None:
        raise ValueError(f"cannot derive an administration stem from {source_url}")
    candidates = sorted(RAW_DIRECTORIES[course].glob(f"{match.group(1)}-rg*.pdf"))
    if len(candidates) != 1:
        raise FileNotFoundError(f"{source_url}: expected one rating guide for {match.group(1)}, found {candidates}")
    return candidates[0]


def load_primary_items() -> list[dict[str, object]]:
    primary_ids = set(json.loads(PRIMARY_IDS_PATH.read_text()))
    items = [json.loads(line) for line in ITEMS_PATH.read_text().splitlines() if line.strip()]
    primary_items = [item for item in items if item["id"] in primary_ids]
    if len(primary_items) != len(primary_ids):
        raise ValueError(f"{len(primary_ids)} primary ids, {len(primary_items)} found in items.jsonl")
    return primary_items


def relative(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT))


def write_jsonl(path: Path, rows: Iterable[dict[str, object]]) -> None:
    with path.open("w") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def build_library() -> GlyphTemplateLibrary:
    template_paths = [REPO_ROOT / "data/raw" / name for name in TEMPLATE_GUIDES]
    library = build_template_library(template_paths)
    missing = sorted(REQUIRED_TEMPLATE_LABELS - set(library.templates))
    if missing:
        raise ValueError(f"glyph template library lacks labels {missing}")
    return library


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--output-directory", type=Path, default=OUTPUT_DIRECTORY)
    arguments = parser.parse_args()
    output_directory: Path = arguments.output_directory
    output_directory.mkdir(parents=True, exist_ok=True)

    started = time.time()
    library = build_library()
    print(f"glyph template library: {len(library.templates)} labels from {library.source_files} in {time.time() - started:.1f}s")

    primary_items = load_primary_items()
    tables: dict[str, dict[str, object]] = {}
    item_rows: list[dict[str, object]] = []
    for item in sorted(primary_items, key=lambda row: row["id"]):
        id_match = ITEM_ID_PATTERN.match(item["id"])
        if id_match is None:
            raise ValueError(f"unexpected item id {item['id']}")
        course = id_match.group(1)
        question_number = int(id_match.group(4))
        guide_path = rating_guide_path(course, item["sourceUrl"])
        guide_key = relative(guide_path)
        if guide_key not in tables:
            rows = parse_map_rows(guide_path, library)
            validate_table(guide_path.name, rows)
            methods = sorted({str(row["readMethod"]) for row in rows})
            print(f"{guide_path.name}: {len(rows)} rows, read by {methods}")
            tables[guide_key] = {"course": course, "sourceExamUrl": item["sourceUrl"], "readMethods": methods, "rows": rows}
        row_by_question = {int(row["question"]): row for row in tables[guide_key]["rows"]}
        if question_number not in row_by_question:
            raise KeyError(f"{item['id']}: question {question_number} missing from {guide_key}")
        row = row_by_question[question_number]
        if row["questionType"] != "Multiple Choice":
            raise ValueError(f"{item['id']}: rating guide lists question {question_number} as {row['questionType']}")
        item_rows.append(
            {
                "id": item["id"],
                "cell": f"nyregents::{course}",
                "question": question_number,
                "standard": row["cluster"],
                "standardAsPrinted": row["clusterAsPrinted"],
                "standardLevel": "ccss_cluster",
                "questionType": row["questionType"],
                "credits": row["credits"],
                "sourcePdf": guide_key,
                "page": row["page"],
                "readMethod": row["readMethod"],
            }
        )

    write_jsonl(output_directory / "item-standards.jsonl", item_rows)
    (output_directory / "rating-guide-tables.json").write_text(json.dumps(tables, indent=1, ensure_ascii=False) + "\n")

    population_by_cell = collections.Counter(f"nyregents::{ITEM_ID_PATTERN.match(i['id']).group(1)}" for i in primary_items)
    covered_by_cell = collections.Counter(row["cell"] for row in item_rows)
    codes_by_cell: dict[str, collections.Counter[str]] = collections.defaultdict(collections.Counter)
    for row in item_rows:
        codes_by_cell[row["cell"]][str(row["standard"])] += 1
    coverage = {
        "primaryIdsPath": relative(PRIMARY_IDS_PATH),
        "populationTotal": len(primary_items),
        "coveredTotal": len(item_rows),
        "ratingGuidesRead": len(tables),
        "readMethodCounts": dict(collections.Counter(str(row["readMethod"]) for row in item_rows)),
        "guidesByReadMethod": {
            method: sorted(k for k, t in tables.items() if method in t["readMethods"])
            for method in sorted({m for t in tables.values() for m in t["readMethods"]})
        },
        "glyphTemplateGuides": list(TEMPLATE_GUIDES),
        "standardLevel": "ccss_cluster",
        "standardLevelNote": (
            "NYSED maps each Regents question to a CCSS cluster (for example A-REI.B), "
            "not to a numbered standard. The unit of the split is therefore the cluster heading."
        ),
        "cells": {
            cell: {
                "population": population_by_cell[cell],
                "covered": covered_by_cell[cell],
                "distinctCodes": len(codes_by_cell[cell]),
                "codeCounts": dict(sorted(codes_by_cell[cell].items())),
            }
            for cell in sorted(population_by_cell)
        },
    }
    (output_directory / "coverage.json").write_text(json.dumps(coverage, indent=1) + "\n")
    print(json.dumps({k: v for k, v in coverage.items() if k != "cells"}, indent=1))
    for cell, summary in coverage["cells"].items():
        print(cell, summary["covered"], "/", summary["population"], "codes", summary["distinctCodes"])
    print(f"done in {time.time() - started:.1f}s")


if __name__ == "__main__":
    main()
