# Printed-page audit

Script: `scripts/print_page_audit.py`. Artifact: `exports/print-audit/audit.json`.

Twenty census rows, seed 20260916: 10 New York Regents geometry lower-central hits, 10 Algebra I withheld-quantity Qwen 14B hits. Compared to source exam PDFs under `data/raw/` with pymupdf text and rendered pages. No optical character recognition. No invented items.

Hand labels (printed page, not the heuristic):

| Label | n |
|---|---:|
| match | 8 |
| ocr_glue | 8 |
| truncated | 3 |
| wrong_item | 1 |
| pdf_missing | 0 |

Rendered page PNGs are local only (`exports/print-audit/pages/`).
