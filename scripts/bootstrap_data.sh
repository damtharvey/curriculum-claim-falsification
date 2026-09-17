#!/usr/bin/env bash
# Download public-release PDFs and rebuild data/items.jsonl when it is missing.
#
# Required tools:
#   curl     PDF and HTML fetch (this script)
#   uv       create .venv (README.md)
#   node     TypeScript runner, not this script
#   npm      install runner deps from package-lock.json
#
# PDF text extraction uses pymupdf inside Python. poppler pdftotext is not
# required and is not an OCR fallback.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if ! command -v curl >/dev/null 2>&1; then
  echo "curl is required" >&2
  exit 1
fi
if [[ ! -x .venv/bin/python ]]; then
  echo "missing .venv/bin/python at the repository root. Create it with uv; see README.md." >&2
  exit 1
fi

exec .venv/bin/python scripts/bootstrap_data.py "$@"
