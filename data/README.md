# Public-release source files

This directory holds ingested item JSONL. Source PDFs live under `data/raw/` on the machine that fetched them; that tree is not in git.

Hugging Face model weights are **not** stored here. Language-model scripts download snapshots into `~/.cache/huggingface/hub` on first run with `--allow-download`.

## Tracked census

`data/items.jsonl` is in git (about 2.0 MiB, **2405** keyed items: 2245 selected, 160 numeric). That is the frozen N the paper uses. A clone does not need to re-parse PDFs to rerun catalog, strategy, masked-stem, or human scoring.

Per-corpus jsonl next to it (`staar.jsonl`, `nyregents.jsonl`, TIMSS, PISA, EQAO, NAPLAN, NYSED, MCAS) is also tracked and is what `scripts/collect_items.py` concatenates. Eureka was never in this census.

## What git does not contain

| Pattern | Why omitted | How to restore |
|---|---|---|
| `data/raw/` (PDFs, HTML, extracted `.txt`) | about 728 MiB | `bash scripts/bootstrap_data.sh --download-pdfs` |
| `data/real-controls*.jsonl` | 3 to 76 MiB | `python scripts/download_real_controls.py` |
| `data/synthetic-controls.jsonl` | generated controls | runner `npx tsx runner/src/cli.ts controls` |
| Hugging Face weights | must not be committed | GPU scripts with `--allow-download` |

Original working copy (2026-09-16) had about 997 PDFs under `data/raw/`:

| `data/raw/` subdir | PDF count | Size |
|---|---:|---:|
| naplan | 91 | 154 MiB |
| staar | 261 | 134 MiB |
| regents-geo | 233 | 123 MiB |
| regents-alg1 | 178 | 92 MiB |
| regents-alg2 | 144 | 79 MiB |
| nysed | 40 | 61 MiB |
| (raw root, including TIMSS 2011 and MCAS) | 26 | 40 MiB |
| timss | 8 | 20 MiB |
| pisa | 7 | 13 MiB |
| eqao | 9 | 12 MiB |

## Bootstrap

System tools: `curl`, `uv`, `node` (runner only). Parsers use **pymupdf**. There is no CPU OCR fallback and no silent skip of required corpus jsonl.

```bash
# Frozen items.jsonl already present: no recensus.
bash scripts/bootstrap_data.sh

# Fetch the public PDFs the census used (STAAR URL guessing is slow).
bash scripts/bootstrap_data.sh --download-pdfs

# Rebuild items.jsonl from PDFs plus transcribed writers.
bash scripts/bootstrap_data.sh --force-parse
```

Required public-release years are those already implemented: STAAR released math forms, NY Regents Algebra I / Geometry / Algebra II, NYSED grades 3-8, NAPLAN 2012-2016 numeracy, TIMSS 2011 and earlier public-release mathematics, PISA released math, EQAO released math, MCAS 2019 grade 7. Do not add later years as required.

If `data/items.jsonl` is missing, bootstrap downloads (unless `--skip-download`), extracts TIMSS 2011 text with pymupdf, runs the existing parse writers, then `scripts/collect_items.py`, and **exits non-zero** if a required corpus file is missing or empty. A rebuilt file whose row count is not 2405 is a warning; keep the tracked file for the paper N.

STAAR grade 5 2015/2020/2023 forms were still unfetched at freeze. Keys are never invented. Graphic options without a text layer stay out of `items.jsonl`.
