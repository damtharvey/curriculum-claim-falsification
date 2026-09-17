#!/usr/bin/env python3
"""Post-hoc locator repair: re-transcribe Regents items whose crop changes when diagram labels such as '8 cm' are excluded from headings."""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import fitz

sys.path.insert(0, str(Path(__file__).resolve().parent))
import print_fidelity_lib as fidelity
from addendum_lib import load_items
from vlm_backsolve_lib import index_pdfs, line_records, question_number, resolve_pdf

RELOCATED_PATH = fidelity.OUT_DIR / "relocated-items.jsonl"
RELOCATED_PAGES_DIR = fidelity.PAGES_DIR / "relocated"
STRICT_HEADING_NOTE = (
    "Post hoc, not pre-registered. The pre-registered heading pattern ^{qnum}(?!\\d)\\s+[A-Za-z(\"“] accepts a diagram label such as "
    "'8 cm' in the left column as the heading of question 8. The repair requires an uppercase letter, '(' or a quote after the number, "
    "which every Regents Part I stem satisfies. Only items whose crop changes are re-transcribed; the pre-registered rows are kept."
)


def strict_regents_heading_y(page: fitz.Page, number: int) -> list[float]:
    pattern = re.compile(rf"^{number}(?!\d)\s+[A-Z(\"“]")
    found: list[float] = []
    for x0, y0, text, _rect in line_records(page):
        if x0 > page.rect.width * 0.42:
            continue
        if pattern.match(text.strip()):
            found.append(y0)
    return found


def crop_key(page_index: int | None, clip: Any) -> tuple[Any, ...]:
    if page_index is None or clip is None:
        return (None,)
    values = clip if isinstance(clip, (list, tuple)) else (clip.x0, clip.y0, clip.x1, clip.y1)
    return (page_index, tuple(round(float(value), 1) for value in values))


def main() -> None:
    fidelity.require_cuda()
    calibration = json.loads(fidelity.CALIBRATION_PATH.read_text(encoding="utf-8"))
    stem_threshold = float(calibration["thresholds"]["chosenThresholds"]["stem"])
    option_threshold = float(calibration["thresholds"]["chosenThresholds"]["option"])
    items_by_id = {str(item["id"]): item for item in load_items()}
    rows = [row for row in fidelity.load_jsonl(fidelity.FIDELITY_ITEMS_PATH) if row.get("stage") in ("calibration", "census")]
    pdf_index = index_pdfs()
    document_cache: dict[Path, fitz.Document] = {}
    original_heading = fidelity.regents_heading_y
    changed: list[dict[str, Any]] = []
    for row in rows:
        item = items_by_id[str(row["id"])]
        if item.get("authority") != "nyregents":
            continue
        pdf = resolve_pdf(item, pdf_index)
        if pdf is None:
            continue
        if pdf not in document_cache:
            document_cache[pdf] = fitz.open(pdf)
        fidelity.regents_heading_y = strict_regents_heading_y
        page_index, clip, reason, hits = fidelity.locate_item(document_cache[pdf], item)
        fidelity.regents_heading_y = original_heading
        if crop_key(page_index, clip) != crop_key(row.get("pageIndex"), row.get("clip")):
            changed.append({"row": row, "item": item, "page_index": page_index, "clip": clip, "reason": reason, "hits": hits})
    print(f"crops that change under the strict heading rule: {len(changed)} of {sum(1 for r in rows if items_by_id[str(r['id'])].get('authority') == 'nyregents')}", flush=True)
    if not changed:
        RELOCATED_PATH.write_text("", encoding="utf-8")
        return
    processor, model = fidelity.load_vlm()
    RELOCATED_PAGES_DIR.mkdir(parents=True, exist_ok=True)
    out_rows: list[dict[str, Any]] = []
    for entry in changed:
        item = entry["item"]
        row = entry["row"]
        fidelity.regents_heading_y = strict_regents_heading_y
        pages = fidelity.render_item_pages(item, pdf_index, document_cache, RELOCATED_PAGES_DIR, force=True)
        fidelity.regents_heading_y = original_heading
        qnum = question_number(item)
        if qnum is None or not pages.png_paths:
            raise RuntimeError(f"cannot relocate {item['id']}")
        raw = fidelity.generate_transcription(processor, model, [fidelity.ROOT / png for png in pages.png_paths], fidelity.transcription_prompt(qnum))
        payload = fidelity.parse_json_object(raw)
        score = fidelity.score_fidelity(item, payload, stem_threshold=stem_threshold, option_threshold=option_threshold)
        new_row = fidelity.fidelity_row(item, row["cells"], pages, raw, payload, score, "relocated")
        new_row["scoredAt"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        new_row["preregisteredVerdict"] = row["verdict"]
        new_row["preregisteredCategory"] = row["category"]
        new_row["preregisteredPageIndex"] = row["pageIndex"]
        new_row["preregisteredClip"] = row["clip"]
        new_row["note"] = STRICT_HEADING_NOTE
        out_rows.append(new_row)
        print(
            f"{item['id']}: page {row['pageIndex']} -> {pages.page_index}; verdict {row['verdict']} -> {score.verdict} ({score.category})",
            flush=True,
        )
    for document in document_cache.values():
        document.close()
    RELOCATED_PATH.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in out_rows), encoding="utf-8")
    flips = [r for r in out_rows if r["verdict"] != r["preregisteredVerdict"]]
    print(json.dumps({"nRelocated": len(out_rows), "nVerdictChanged": len(flips), "changed": [(r["id"], r["preregisteredVerdict"], r["verdict"]) for r in flips]}, indent=2))


if __name__ == "__main__":
    main()
