#!/usr/bin/env python3
"""20-item printed-page audit of census rows against local exam PDFs. No OCR."""

from __future__ import annotations

import json
import random
import re
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
from addendum_lib import ITEMS_PATH, ROOT, load_items, middle_value_option
from ingest_lib import RAW, extract_pdf_pages, render_page_png
from parse_helpers import extract_paren_choices
from parse_regents import exam_stem, is_exam, is_key_file, parse_key_pdf, parse_key_xlsx

SEED = 20260916
OUT_DIR = ROOT / "exports" / "print-audit"
PAGES_DIR = OUT_DIR / "pages"
GLUE_RE = re.compile(
    r"(?i)(\[over\]|computations\.|---page\s+\d+|geometry\s+[–—'-]\s+"
    r"(jan|june|aug)|algebra(?:\s*ii?)?\s+[–—'-]|use this space|"
    r"\bpage\s+\d+\b)"
)
ID_RE = re.compile(
    r"^nyregents-(algebra-i|algebra-ii|geometry)-(\d{4}|unknown)-(jan|jun|aug|unk)-q(\d+)$",
    re.I,
)
FOOTER_LEAK_RE = re.compile(
    r"(?i)(algebra|geometry)\s+[–—'′-]\s+(jan|june|aug)|\[over\]|computations\."
)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def index_pdfs() -> dict[str, Path]:
    index: dict[str, Path] = {}
    if not RAW.exists():
        return index
    for path in RAW.rglob("*"):
        if path.is_file() and path.suffix.lower() in {".pdf", ".xlsx", ".xls"}:
            index[path.name.lower()] = path
    return index


def prefer_exam_pdf(name: str, index: dict[str, Path]) -> Path | None:
    low = name.lower()
    if low in index:
        candidate = index[low]
        if "-lt" in low:
            non_lt = low.replace("-exam-lt.pdf", "-exam.pdf").replace("examlt.pdf", "exam.pdf")
            if non_lt in index:
                return index[non_lt]
        return candidate
    if "-exam-lt.pdf" in low:
        alt = low.replace("-exam-lt.pdf", "-exam.pdf")
        if alt in index:
            return index[alt]
    return None


def parse_item_id(item_id: str) -> tuple[str, str, str, int] | None:
    match = ID_RE.match(item_id)
    if not match:
        return None
    return match.group(1).lower(), match.group(2), match.group(3).lower(), int(match.group(4))


def question_block(pages: list[str], qnum: int) -> tuple[int | None, str]:
    joined = "\n".join(f"---PAGE {i + 1}---\n{page}" for i, page in enumerate(pages))
    start = re.search(rf"(?m)^\s*{qnum}\s+\S", joined)
    if not start:
        start = re.search(rf"(?m)^\s*{qnum}\b", joined)
    if not start:
        return None, ""
    rest = joined[start.start() :]
    nxt = re.search(rf"(?m)^\s*{qnum + 1}\s+\S", rest[1:])
    part = re.search(r"(?i)\bPart\s+II\b", rest[1:])
    ends: list[int] = []
    if nxt:
        ends.append(1 + nxt.start())
    if part:
        ends.append(1 + part.start())
    block = rest[: min(ends)] if ends else rest[:2500]
    page_hit = re.search(r"---PAGE (\d+)---", joined[: start.start() + 1])
    page_idx = int(page_hit.group(1)) - 1 if page_hit else None
    return page_idx, block


def normalize(text: str) -> str:
    text = text.lower()
    text = text.replace("–", "-").replace("—", "-").replace("′", "'")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def token_set(text: str) -> set[str]:
    return {tok for tok in normalize(text).split() if len(tok) >= 2}


def option_overlap(census: dict[str, str], pdf_choices: dict[str, str]) -> float:
    if not census:
        return 0.0
    hits = 0
    for letter, text in census.items():
        pdf_text = pdf_choices.get(letter, "")
        a = token_set(text)
        b = token_set(pdf_text)
        if not a:
            continue
        if len(a & b) / len(a) >= 0.5 or normalize(text)[:24] in normalize(pdf_text):
            hits += 1
    return hits / max(len(census), 1)


def classify_row(
    *,
    pdf_found: bool,
    block: str,
    census_stem: str,
    census_choices: dict[str, str],
    pdf_choices: dict[str, str],
    census_key: str,
    printed_key: str | None,
) -> str:
    if not pdf_found:
        return "pdf_missing"
    if not block.strip():
        return "unreadable"
    glue_in_census = any(GLUE_RE.search(v) for v in [census_stem, *census_choices.values()])
    overlap = option_overlap(census_choices, pdf_choices) if pdf_choices else 0.0
    stem_tokens = token_set(census_stem)
    block_tokens = token_set(block)
    stem_share = (len(stem_tokens & block_tokens) / len(stem_tokens)) if stem_tokens else 0.0
    truncated = len(census_stem) < 40 and len(block) > 120
    wrong_options = overlap < 0.5 and bool(pdf_choices)
    key_mismatch = printed_key is not None and printed_key != census_key
    if key_mismatch or (wrong_options and stem_share < 0.35):
        return "wrong_item"
    if glue_in_census or any(FOOTER_LEAK_RE.search(v) for v in census_choices.values()):
        return "ocr_glue"
    if truncated and stem_share < 0.6:
        return "truncated"
    if overlap >= 0.75 and stem_share >= 0.4:
        return "match"
    if stem_share >= 0.5 and overlap >= 0.5:
        return "match"
    if truncated:
        return "truncated"
    if glue_in_census:
        return "ocr_glue"
    if wrong_options:
        return "wrong_item"
    return "match"


def scoring_keys_for(exam_path: Path, index: dict[str, Path]) -> dict[int, str]:
    stem = exam_stem(exam_path.name)
    keys: dict[int, str] = {}
    for name, path in index.items():
        if not is_key_file(path.name):
            continue
        if exam_stem(path.name) != stem:
            continue
        parsed = parse_key_xlsx(path) if path.suffix.lower() in {".xlsx", ".xls"} else parse_key_pdf(path)
        if len(parsed) > len(keys):
            keys = parsed
    return keys


def geometry_hits(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for item in items:
        if item.get("authority") != "nyregents" or item.get("claim") != "geometry":
            continue
        if item.get("responseType") != "selected":
            continue
        pick = middle_value_option(item)
        if pick is None:
            continue
        if str(item.get("key", "")).upper() == pick.upper():
            hits.append(item)
    return hits


def algebra_masked_hits(
    items_by_id: dict[str, dict[str, Any]],
    mask_by_id: dict[str, int],
    scored: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for row in scored:
        item_id = str(row.get("id", ""))
        item = items_by_id.get(item_id)
        if item is None:
            continue
        if item.get("authority") != "nyregents" or item.get("claim") != "algebra-i":
            continue
        if mask_by_id.get(item_id, 0) < 1:
            continue
        if not row.get("correct"):
            continue
        hits.append(item)
    return hits


def sample_with_pdf(
    pool: list[dict[str, Any]],
    k: int,
    rng: random.Random,
    index: dict[str, Path],
) -> list[dict[str, Any]]:
    ranked = sorted(pool, key=lambda item: str(item["id"]))
    rng.shuffle(ranked)
    chosen: list[dict[str, Any]] = []
    missing: list[dict[str, Any]] = []
    for item in ranked:
        url_name = Path(urlparse(str(item.get("sourceUrl", ""))).path).name
        if prefer_exam_pdf(url_name, index) is not None:
            chosen.append(item)
        else:
            missing.append(item)
        if len(chosen) == k:
            break
    if len(chosen) < k:
        chosen.extend(missing[: k - len(chosen)])
    return chosen


def audit_item(
    item: dict[str, Any],
    *,
    slice_name: str,
    index: dict[str, Path],
) -> dict[str, Any]:
    parsed = parse_item_id(str(item["id"]))
    qnum = parsed[3] if parsed else None
    url_name = Path(urlparse(str(item.get("sourceUrl", ""))).path).name
    pdf = prefer_exam_pdf(url_name, index)
    block = ""
    page_idx: int | None = None
    pdf_choices: dict[str, str] = {}
    printed_key: str | None = None
    page_png: str | None = None
    if pdf is not None and qnum is not None:
        pages = extract_pdf_pages(pdf)
        page_idx, block = question_block(pages, qnum)
        lines = [ln for ln in block.splitlines() if not ln.startswith("---PAGE")]
        _stem_parts, pdf_choices = extract_paren_choices(lines)
        keys = scoring_keys_for(pdf, index)
        printed_key = keys.get(qnum)
        if page_idx is not None:
            dest = PAGES_DIR / f"{item['id']}-p{page_idx + 1:03d}.png"
            render_page_png(pdf, page_idx, dest, dpi=120)
            page_png = str(dest.relative_to(ROOT))
    census_choices = {str(k): str(v) for k, v in (item.get("choices") or {}).items()}
    label = classify_row(
        pdf_found=pdf is not None,
        block=block,
        census_stem=str(item.get("stem", "")),
        census_choices=census_choices,
        pdf_choices=pdf_choices,
        census_key=str(item.get("key", "")).upper(),
        printed_key=printed_key.upper() if printed_key else None,
    )
    return {
        "id": item["id"],
        "slice": slice_name,
        "qnum": qnum,
        "sourceUrl": item.get("sourceUrl"),
        "pdf": str(pdf.relative_to(ROOT)) if pdf is not None else None,
        "pdfPage": None if page_idx is None else page_idx + 1,
        "pagePng": page_png,
        "censusKey": str(item.get("key", "")).upper(),
        "printedKey": printed_key,
        "censusStem": str(item.get("stem", ""))[:400],
        "censusChoices": census_choices,
        "pdfChoices": pdf_choices,
        "pdfBlockPreview": re.sub(r"\s+", " ", block)[:800],
        "label": label,
        "labelSource": "script_heuristic",
        "notes": "",
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    PAGES_DIR.mkdir(parents=True, exist_ok=True)
    index = index_pdfs()
    items = load_items()
    items_by_id = {str(item["id"]): item for item in items}
    geo_pool = geometry_hits(items)
    mask_rows = load_jsonl(ROOT / "exports" / "addendum-gpu" / "masked-stem-item-mask-stats.jsonl")
    mask_by_id = {str(row["id"]): int(row["masked_token_count"]) for row in mask_rows}
    scored_14b = load_jsonl(ROOT / "exports" / "addendum-gpu" / "masked-stem-14b-items.jsonl")
    alg_pool = algebra_masked_hits(items_by_id, mask_by_id, scored_14b)
    rng_geo = random.Random(SEED)
    rng_alg = random.Random(SEED + 1)
    geo_sample = sample_with_pdf(geo_pool, 10, rng_geo, index)
    alg_sample = sample_with_pdf(alg_pool, 10, rng_alg, index)
    rows = [audit_item(item, slice_name="geometry_lower_central_hit", index=index) for item in geo_sample]
    rows.extend(audit_item(item, slice_name="algebra_i_masked_stem_hit", index=index) for item in alg_sample)
    counts: dict[str, int] = {}
    for row in rows:
        counts[row["label"]] = counts.get(row["label"], 0) + 1
    payload = {
        "seed": SEED,
        "nRequested": 20,
        "nGeometryPool": len(geo_pool),
        "nAlgebraIMaskedStemHitPool": len(alg_pool),
        "nPdfsIndexed": len(index),
        "rawTreePresent": RAW.exists(),
        "ocrUsed": False,
        "classification": [
            "match",
            "ocr_glue",
            "truncated",
            "wrong_item",
            "pdf_missing",
            "unreadable",
        ],
        "counts": counts,
        "rows": rows,
        "cite": "exports/print-audit/audit.json",
    }
    dest = OUT_DIR / "audit.json"
    dest.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("wrote", dest)
    print("geometry pool", len(geo_pool), "algebra pool", len(alg_pool), "pdfs", len(index))
    print("counts", json.dumps(counts, sort_keys=True))
    for row in rows:
        print(row["slice"], row["id"], row["label"], row["pdf"])


if __name__ == "__main__":
    main()
