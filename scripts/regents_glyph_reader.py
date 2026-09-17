"""Visual glyph reading for Regents rating-guide tables whose text layer is unusable.

Eight Algebra I and Algebra II rating guides embed the Calibri table font as a
CID-keyed subset with no ToUnicode map, so the text layer holds sequential glyph
ids (0x01, 0x02, ...) that carry no character information. The glyph outlines are
intact, the per-character bounding boxes are intact, and every table uses the same
face at the same size. This module renders each character box, ink-crops it, and
matches it against templates rendered from rating guides whose text layer does
decode. A match must clear a score floor and a margin over every other label or
the reader raises; nothing is guessed.

The same reader resolves rows where two cluster codes are overprinted at one cell
(a correction drawn on top of a white box): the visible code is the one whose own
characters match what is rendered.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pymupdf

GLYPH_ALPHABET = frozenset("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-.")
# Every rating guide draws the map table from one InDesign template at one point
# size (the word "Multiple" is 37.6 to 37.8 pt wide in every guide), so a fixed zoom
# gives comparable absolute glyph sizes. Span font sizes are not used: some guides
# report them through a scaled text matrix.
RENDER_ZOOM = 16.0
INK_THRESHOLD = 128
MAX_TEMPLATES_PER_LABEL = 12
MAX_TEMPLATES_PER_FILE = 2
SIZE_TOLERANCE_PIXELS = 8
SIZE_PENALTY_PER_PIXEL = 0.02
BOX_EXTENSION_POINTS = 4.0
EDGE_MARGIN_PIXELS = 2
DESCRIPTOR_CELLS = 16
SCORE_FLOOR = 0.85
CALIBRATION_MIN_HEIGHT_PIXELS = 60
CALIBRATION_MIN_SAMPLES = 20
CALIBRATION_SCALE_RANGE = (0.9, 1.1)
MARGIN_FLOOR = 0.03
TABLE_FONT_NAME = "Calibri"


@dataclass
class GlyphImage:
    """An ink crop of one glyph: its pixel size and a pooled grayscale descriptor."""

    height: int
    width: int
    descriptor: np.ndarray


def is_table_body_span(span: dict[str, object]) -> bool:
    font_name = str(span["font"])
    return TABLE_FONT_NAME in font_name and "Bold" not in font_name


def label_components(mask: np.ndarray) -> np.ndarray:
    """Four-connected component labels for a boolean mask (0 outside the mask).

    Run-length union-find: each row is split into ink runs, runs that overlap a run
    in the previous row are joined, and the final labels are written back per run.
    """
    height, width = mask.shape
    parent: list[int] = []

    def find(index: int) -> int:
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    def union(first: int, second: int) -> None:
        root_first, root_second = find(first), find(second)
        if root_first != root_second:
            parent[root_second] = root_first

    runs_by_row: list[list[tuple[int, int, int]]] = []
    padded = np.zeros((height, width + 2), dtype=bool)
    padded[:, 1:-1] = mask
    for row in range(height):
        difference = np.diff(padded[row].astype(np.int8))
        starts = np.where(difference == 1)[0]
        ends = np.where(difference == -1)[0]
        runs: list[tuple[int, int, int]] = []
        for start, end in zip(starts.tolist(), ends.tolist()):
            run_id = len(parent)
            parent.append(run_id)
            runs.append((start, end, run_id))
            if row > 0:
                for previous_start, previous_end, previous_id in runs_by_row[row - 1]:
                    if previous_start < end and start < previous_end:
                        union(previous_id, run_id)
        runs_by_row.append(runs)
    labels = np.zeros((height, width), dtype=np.int64)
    for row, runs in enumerate(runs_by_row):
        for start, end, run_id in runs:
            labels[row, start:end] = find(run_id) + 1
    return labels


def drop_intruding_neighbors(mask: np.ndarray) -> np.ndarray:
    """Remove ink components that touch an edge of the extended character box.

    A neighbouring glyph that overhangs into this box (the tail of ``Q`` before a
    period), the line above or below a two-line cell (``Constructed`` over
    ``Response``), or a table rule continues past the box edge, so its component
    touches that edge. The box's own glyph has positive side bearings and sits inside
    the vertical extension, so it does not. Components cut by the top or bottom are
    always dropped. When every remaining component touches a side edge the glyph
    itself overhangs (``Q``) and the mask is kept; the same rule builds the
    templates, so that case is matched consistently.
    """
    labels = label_components(mask)
    margin = EDGE_MARGIN_PIXELS
    vertical_edge_labels = set(np.unique(labels[:margin, :])) | set(np.unique(labels[-margin:, :]))
    vertical_edge_labels.discard(0)
    # Ink cut by the top or bottom of the extended box can only be another line or a
    # table rule: the box already extends past the glyph's ascent and descent.
    without_vertical = mask & ~np.isin(labels, list(vertical_edge_labels))
    if not without_vertical.any():
        return without_vertical
    labels = label_components(without_vertical)
    left_labels = set(np.unique(labels[:, :margin]))
    right_labels = set(np.unique(labels[:, -margin:]))
    left_labels.discard(0)
    right_labels.discard(0)
    # A component spanning the whole box from side to side is a table rule, never a glyph.
    spanning = without_vertical & np.isin(labels, list(left_labels & right_labels))
    without_rules = without_vertical & ~spanning
    if not without_rules.any():
        return without_rules
    labels = label_components(without_rules)
    side_edge_labels = set(np.unique(labels[:, :margin])) | set(np.unique(labels[:, -margin:]))
    side_edge_labels.discard(0)
    interior = without_rules & ~np.isin(labels, list(side_edge_labels))
    if not interior.any():
        return without_rules
    return interior


def pooled_descriptor(image: np.ndarray) -> np.ndarray:
    """Area-average a grayscale crop onto a DESCRIPTOR_CELLS square grid."""
    height, width = image.shape
    row_index = np.minimum((np.arange(height) / height * DESCRIPTOR_CELLS).astype(int), DESCRIPTOR_CELLS - 1)
    column_index = np.minimum((np.arange(width) / width * DESCRIPTOR_CELLS).astype(int), DESCRIPTOR_CELLS - 1)
    pooled = np.zeros((DESCRIPTOR_CELLS, DESCRIPTOR_CELLS), dtype=np.float64)
    counts = np.zeros((DESCRIPTOR_CELLS, DESCRIPTOR_CELLS), dtype=np.float64)
    np.add.at(pooled, (row_index[:, None], column_index[None, :]), image)
    np.add.at(counts, (row_index[:, None], column_index[None, :]), 1.0)
    return (1.0 - (pooled / np.maximum(counts, 1.0)) / 255.0).astype(np.float32)


def render_glyph(page: pymupdf.Page, bbox: tuple[float, float, float, float], zoom: float = RENDER_ZOOM) -> GlyphImage | None:
    """Render one character box to an ink crop; None when the box is blank."""
    x0, y0, x1, y1 = bbox
    # Character boxes in some guides stop short of descenders, which turns ``p`` into
    # ``n``. Extend every box vertically by the same amount so templates and targets
    # are cropped alike.
    clip = pymupdf.Rect(x0, y0 - BOX_EXTENSION_POINTS, x1, y1 + BOX_EXTENSION_POINTS)
    if clip.is_empty:
        return None
    pixmap = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), clip=clip, colorspace=pymupdf.csGRAY, alpha=False)
    image = np.frombuffer(pixmap.samples, dtype=np.uint8).reshape(pixmap.height, pixmap.width)
    mask = image < INK_THRESHOLD
    if not mask.any():
        return None
    mask = drop_intruding_neighbors(mask)
    if not mask.any():
        return None
    ink_rows = np.where(mask.any(axis=1))[0]
    ink_columns = np.where(mask.any(axis=0))[0]
    cropped = image[ink_rows[0] : ink_rows[-1] + 1, ink_columns[0] : ink_columns[-1] + 1].astype(np.float32)
    cropped_mask = mask[ink_rows[0] : ink_rows[-1] + 1, ink_columns[0] : ink_columns[-1] + 1]
    softened = np.where(cropped_mask | (cropped < 255.0), cropped, 255.0).astype(np.float32)
    return GlyphImage(int(softened.shape[0]), int(softened.shape[1]), pooled_descriptor(softened))


def glyph_similarity(first: GlyphImage, second: GlyphImage) -> float:
    """Coverage similarity minus a size penalty; 0 when sizes disagree beyond tolerance.

    Cross-correlation is the wrong metric for solid glyphs such as ``-`` and ``.``,
    whose mean-centred descriptors are dominated by one anti-aliased edge row; a
    coverage distance treats those glyphs stably and still separates letter shapes.
    """
    height_difference = abs(first.height - second.height)
    width_difference = abs(first.width - second.width)
    if height_difference > SIZE_TOLERANCE_PIXELS or width_difference > SIZE_TOLERANCE_PIXELS:
        return 0.0
    coverage_similarity = float(1.0 - np.abs(first.descriptor - second.descriptor).mean())
    # ``I`` and ``l`` are both plain bars in Calibri and differ only in height, so
    # pixel size enters the score directly.
    return coverage_similarity - SIZE_PENALTY_PER_PIXEL * (height_difference + width_difference)


@dataclass
class GlyphMatch:
    label: str
    score: float
    margin: float


@dataclass
class GlyphTemplateLibrary:
    templates: dict[str, list[GlyphImage]] = field(default_factory=dict)
    source_files: list[str] = field(default_factory=list)
    missing_labels: list[str] = field(default_factory=list)
    template_sources: dict[str, dict[str, int]] = field(default_factory=dict)

    def add(self, label: str, image: GlyphImage, source: str) -> None:
        """Keep at most ``MAX_TEMPLATES_PER_FILE`` templates per label from one file."""
        bucket = self.templates.setdefault(label, [])
        if len(bucket) >= MAX_TEMPLATES_PER_LABEL:
            return
        from_this_file = self.template_sources.get(label, {}).get(source, 0)
        if from_this_file >= MAX_TEMPLATES_PER_FILE:
            return
        bucket.append(image)
        self.template_sources.setdefault(label, {})[source] = from_this_file + 1

    def match(self, image: GlyphImage) -> GlyphMatch:
        best_by_label: dict[str, float] = {}
        for label, images in self.templates.items():
            best_by_label[label] = max(glyph_similarity(image, template) for template in images)
        ranked = sorted(best_by_label.items(), key=lambda pair: pair[1], reverse=True)
        best_label, best_score = ranked[0]
        runner_up_score = ranked[1][1] if len(ranked) > 1 else 0.0
        return GlyphMatch(best_label, best_score, best_score - runner_up_score)

    def template_height(self, label: str) -> float:
        return float(np.median([template.height for template in self.templates[label]]))

    def page_zoom(self, page: pymupdf.Page, spans: list[dict[str, object]], source: str) -> float:
        """Calibrate the render zoom for one page against the template library.

        Glyph outlines in the CID-keyed subsets render one to three percent smaller
        than the same characters in the template guides (a font-program scaling
        difference, not a point-size difference), which eats the height margin that
        separates ``I`` from ``l``. A first pass at the nominal zoom matches every tall
        glyph without floors; the median ratio of template height to observed height
        over confident matches is the scale, and every glyph on the page is then
        rendered at the nominal zoom times that scale.
        """
        ratios: list[float] = []
        for span in spans:
            for character in span["chars"]:
                image = render_glyph(page, tuple(character["bbox"]))
                if image is None or image.height < CALIBRATION_MIN_HEIGHT_PIXELS:
                    continue
                match = self.match(image)
                if match.score < SCORE_FLOOR:
                    continue
                ratios.append(self.template_height(match.label) / image.height)
        if len(ratios) < CALIBRATION_MIN_SAMPLES:
            raise ValueError(f"{source}: only {len(ratios)} confident tall glyphs for zoom calibration")
        scale = float(np.median(ratios))
        if not CALIBRATION_SCALE_RANGE[0] <= scale <= CALIBRATION_SCALE_RANGE[1]:
            raise ValueError(f"{source}: calibrated glyph scale {scale:.3f} is outside {CALIBRATION_SCALE_RANGE}")
        return RENDER_ZOOM * scale

    def read(self, page: pymupdf.Page, character: dict[str, object], source: str, zoom: float = RENDER_ZOOM) -> str:
        """Return the character drawn in one rawdict char box, or a space when blank."""
        image = render_glyph(page, tuple(character["bbox"]), zoom)
        if image is None:
            return " "
        match = self.match(image)
        if match.score < SCORE_FLOOR or match.margin < MARGIN_FLOOR:
            raise ValueError(
                f"{source}: glyph at {tuple(round(v, 1) for v in character['bbox'])} matched {match.label!r} "
                f"with score {match.score:.3f} and margin {match.margin:.3f}, below the floors"
            )
        return match.label

    def word_is_visible(self, page: pymupdf.Page, characters: list[dict[str, object]], expected: str, zoom: float = RENDER_ZOOM) -> bool:
        """True when the glyphs drawn in these character boxes read as ``expected``.

        Used where two codes are overprinted at one cell: the hidden code's boxes
        show misaligned pieces of the visible code and do not read back as
        themselves.
        """
        decoded: list[str] = []
        for character in characters:
            image = render_glyph(page, tuple(character["bbox"]), zoom)
            if image is None:
                decoded.append(" ")
                continue
            match = self.match(image)
            if match.score < SCORE_FLOOR or match.margin < MARGIN_FLOOR:
                return False
            decoded.append(match.label)
        return "".join(decoded).strip() == expected


def table_pages(document: pymupdf.Document) -> list[int]:
    """Pages holding table body spans in the Calibri face."""
    pages: list[int] = []
    for page_index in range(len(document)):
        raw = document[page_index].get_text("rawdict")
        body_spans = [
            span for block in raw["blocks"] for line in block.get("lines", []) for span in line["spans"] if is_table_body_span(span)
        ]
        if len(body_spans) >= 8:
            pages.append(page_index)
    return pages


def build_template_library(reference_pdfs: list[Path]) -> GlyphTemplateLibrary:
    """Render labelled glyph templates from rating guides whose text layer decodes."""
    library = GlyphTemplateLibrary()
    for pdf_path in reference_pdfs:
        document = pymupdf.open(pdf_path)
        for page_index in table_pages(document):
            page = document[page_index]
            raw = page.get_text("rawdict")
            for block in raw["blocks"]:
                for line in block.get("lines", []):
                    for span in line["spans"]:
                        if not is_table_body_span(span):
                            continue
                        for character in span["chars"]:
                            label = str(character["c"])
                            if label not in GLYPH_ALPHABET:
                                continue
                            image = render_glyph(page, tuple(character["bbox"]))
                            if image is None:
                                continue
                            library.add(label, image, pdf_path.name)
        document.close()
        library.source_files.append(pdf_path.name)
    library.missing_labels = sorted(GLYPH_ALPHABET - set(library.templates))
    return library
