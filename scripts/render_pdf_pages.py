#!/usr/bin/env python3
"""Render PDF pages to PNG for vision transcription. GPU OCR is skipped (no driver)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ingest_lib import ROOT, render_page_png

OUT = ROOT / "exports" / "vision" / "pages"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf")
    parser.add_argument("--max-pages", type=int, default=40)
    parser.add_argument("--dpi", type=int, default=140)
    parser.add_argument("--prefix", default="")
    args = parser.parse_args()
    pdf = Path(args.pdf)
    import fitz

    doc = fitz.open(pdf)
    n = min(len(doc), args.max_pages)
    doc.close()
    stem = args.prefix or pdf.stem
    written: list[dict[str, str | int]] = []
    for i in range(n):
        dest = OUT / stem / f"p{i + 1:03d}.png"
        render_page_png(pdf, i, dest, dpi=args.dpi)
        written.append({"page": i + 1, "path": str(dest.relative_to(ROOT))})
        print("wrote", dest)
    manifest = OUT / stem / "manifest.json"
    manifest.write_text(json.dumps({"pdf": str(pdf), "pages": written}, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
