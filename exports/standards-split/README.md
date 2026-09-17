# Standards split (review-2 weakness 1)

Status at 2026-09-17 05:05 UTC. Work was stopped by budget cap before any result was written. Nothing in this directory is a finding.

## What is complete

- `scripts/extract_regents_standards.py` and `scripts/regents_glyph_reader.py`: read the "Map to the Learning Standards" table of every NYSED Regents Algebra I and Algebra II rating guide for the masked-stem primary population (`exports/addendum-gpu/masked-stem-algebra-primary-item-ids.json`, 606 ids: Algebra I 358, Algebra II 248). All rating guides are already in `data/raw/regents-alg1/` and `data/raw/regents-alg2/` (`*-rg*.pdf`); none needed fetching. Three read paths, each recorded per row: text layer (most guides), a glyph table for the v202, June 2022, and August 2022 Calibri subset encoding, and template glyph matching for guides whose embedded CID font has no character mapping (August 2019, June 2019 Algebra I; January 2019, June 2022, August 2016, August 2019 Algebra II). Glyph matching was evaluated on 33,704 held-out characters from text-layer guides with 0 errors. Every parsed table is validated (questions 1..N contiguous, exactly 24 multiple-choice rows) before use.
- Finding about the source: NYSED maps each question to a CCSS **cluster** (for example `A-REI.B`, `F-IF.C`), not to a numbered standard. The unit of any verb-class split is therefore the cluster heading text.
- `scripts/fetch_ccss_cluster_text.py`: fetches cluster heading and standard text per code from thecorestandards.org domain pages into `standards-text.json`. Written, tested for one page, not run to completion.

## What is partial

- In interactive runs the extractor parsed all 33 Algebra I administrations (358 of 358 primary Algebra I items reach a cluster code) and was fixing a per-page render-scale calibration for the Algebra II guide `algtwo82016-rg.pdf` when stopped. The last full run was interrupted before writing, so **no `item-standards.jsonl`, `rating-guide-tables.json`, or `coverage.json` exists**. Coverage written to disk: 0 / 606. Coverage verified in memory: 358 / 606 (Algebra I only).

## What was not started

- `standards-text.json` (not fetched).
- `preregistration.md` and its sha256 (the verb-class rule). No hit rates by standard have been looked at, so a preregistration written later is still clean.
- Verb-class classification of codes.
- Join to per-item masked-stem predictions. Per-item files exist for all three claimed scorers: `exports/addendum-gpu/masked-stem-7b-items.jsonl`, `masked-stem-14b-items.jsonl`, `masked-stem-phi4-items.jsonl` (fields `id`, `chosen_letter`, `key`, `correct`, `cell`). No GPU is needed for the join.
- Execution-subset table and the proposed Method and Results paragraphs.

## To finish (integration worker)

1. `source .venv/bin/activate && python scripts/extract_regents_standards.py` (about 2 minutes; fix `algtwo82016` if the calibration raises).
2. `python scripts/fetch_ccss_cluster_text.py` (needs network).
3. Write `preregistration.md` with the verb-class rule on cluster heading text, hash it, classify codes, then join to the three item files and report per model and cell: n, rate, bootstrap 95% CI (1000 replicates, `random.Random(21 + n)`, as in `scripts/score_choices_only.py`), chance (mean 1/k), modal letter on the subset, bar n >= 10 with lower CI above chance and above modal frequency.
