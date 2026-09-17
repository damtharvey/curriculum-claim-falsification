#!/usr/bin/env python3
"""Render solving-tagged selected-response PDF items to PNG. No OCR."""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from addendum_lib import ITEMS_PATH, load_items
from vlm_backsolve_lib import (
    PAGES_DIR,
    ROOT,
    build_page_target,
    index_pdfs,
    is_solving_item,
    render_target,
    stem_prefix,
)

INDEX_PATH = ROOT / "exports" / "addendum-vlm" / "page-index.jsonl"


def selected_solving(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in items:
        if item.get("responseType") != "selected":
            continue
        if not is_solving_item(item):
            continue
        if not (item.get("choices") or {}):
            continue
        rows.append(item)
    rows.sort(key=lambda row: str(row["id"]))
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--items", type=Path, default=ITEMS_PATH)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    items = selected_solving(load_items(args.items))
    if args.limit > 0:
        items = items[: args.limit]
    pdf_index = index_pdfs()
    document_cache: dict[Path, Any] = {}
    PAGES_DIR.mkdir(parents=True, exist_ok=True)
    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    counts: dict[str, int] = defaultdict(int)
    written = 0
    with INDEX_PATH.open("w", encoding="utf-8") as handle:
        for item in items:
            target = build_page_target(item, pdf_index, document_cache)
            has_png = target.png_path.exists() and target.png_path.stat().st_size > 100
            if target.pdf is not None and target.page_index is not None:
                if args.force or not has_png:
                    document = document_cache[target.pdf]
                    render_target(target, document=document)
                    written += 1
                counts[target.locate_reason] += 1
            else:
                counts[target.locate_reason] += 1
            row = {
                "id": item["id"],
                "authority": item.get("authority"),
                "claim": item.get("claim"),
                "pdf": None if target.pdf is None else str(target.pdf.relative_to(ROOT)),
                "pageIndex": target.page_index,
                "clip": target.clip,
                "png": str(target.png_path.relative_to(ROOT))
                if target.png_path.exists()
                else None,
                "locateReason": target.locate_reason,
                "stemPrefix": stem_prefix(str(item.get("stem") or "")),
            }
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    for document in document_cache.values():
        document.close()
    print(
        json.dumps(
            {
                "nItems": len(items),
                "nPngWrittenThisRun": written,
                "locateCounts": dict(counts),
                "indexPath": str(INDEX_PATH.relative_to(ROOT)),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
