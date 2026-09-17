# Curriculum Claim Falsification

Minds and Machines (CHAT), 15-17 September 2026.

This repository is the **Curriculum Claim Falsification** project, also called CHAT: Does the Assessment Require the Skill? Independent git history begins 2026-09-16.

## One-sided claim

An assessment item carries a published tag: a standard code, or a TIMSS cognitive domain such as reasoning. A passing score is then read as evidence of that competency.

This project searches for programs that lack the tagged operation and still pass under the published key. Each such program is a witness that the tag overstates what a pass shows.

- A program that passes refutes the tag for that item.
- A program that fails proves nothing beyond the programs we tried.

We never say students did not learn the skill.

Protocol-only OSF draft: `registration.md`.

## Layout

- `runner/` TypeScript requirement-matrix runner
- `scripts/` ingest, census tables, GPU language-model scoring
- `data/` frozen item JSONL plus (local) source PDFs; see `data/README.md`
- `claims/`, `rules/`, `fixtures/`
- `exports/` matrices, witnesses, addenda, human rater packet

## What git does not contain

GitHub's blob limit is 100 MB. The working copy on the original machine kept large local files that are **not** in git. They can be redownloaded or recreated.

| Pattern | Why omitted | Required to rerun |
|---|---|---|
| `data/raw/` PDFs, `.txt` companions, `_html/` | ~728 MiB, 996 PDFs | Catalog / strategy / LM / human: **no** if `data/items.jsonl` is present. STAAR replication and a recensus: **yes**. `bash scripts/bootstrap_data.sh --download-pdfs` |
| `data/items.jsonl` | **Tracked** (2.0 MiB, frozen N=2405). Recreate only if deleted: `bash scripts/bootstrap_data.sh` | All experiment families |
| Per-corpus `data/*.jsonl` (STAAR, Regents, TIMSS, …) | Tracked, small | Recensus via `scripts/collect_items.py`; not needed if `items.jsonl` is present |
| `data/real-controls*.jsonl`, `data/synthetic-controls.jsonl` | 3 to 76 MiB Hugging Face dumps | Method controls only. `python scripts/download_real_controls.py` |
| `exports/trials.jsonl` and `trials-census.jsonl` / `trials-n2405.jsonl` | 125 to 126 MiB | Optional log. Paper catalog numbers live in `exports/rule-chance.json`, `exports/apriori-cell-table.json`, `exports/witnesses.json`. Recreate the log with `npx tsx runner/src/cli.ts run` |
| `exports/trial-marks.jsonl` | 89 MiB | Optional. Recreated with the census run |
| `exports/matrix.json` | 33 MiB | Optional. Recreated with the census run |
| `exports/addendum-gpu/*-items.jsonl` | Per-item GPU rows | Recreate on CUDA (see Masked-stem LM). Paper cells live in the sibling `*.json` summaries, which are tracked |
| `exports/choices-only/batches/`, `predictions/` | Bedrock scratch | E3 uses tracked `exports/choices-only/scored.jsonl` |
| `.venv/` | ~479 MiB | Install (below) |
| `node_modules/` | npm install | Install (below) |
| Hugging Face model snapshots | Must not be committed | Download on first GPU run into `~/.cache/huggingface/hub` |

`exports/human-masked-stem/rater-packet.txt` is tracked. Send that file, not a PDF.

## Setup

A GPU is required for language-model scripts. There is no CPU fallback.

### Node (runner)

```bash
npm install
chmod +x validate
chmod +x scripts/bootstrap_data.sh
```

`package-lock.json` is in the tree. Reinstall `node_modules` from that lockfile; it was not copied.

System tools: `node`, `npm`, `curl`. `uv` for the Python environment. PDF parsers use **pymupdf**, not poppler `pdftotext` and not OCR.

### Python (ingest and tables)

```bash
uv venv .venv
source .venv/bin/activate
uv pip install numpy pandas pymupdf pdfplumber pillow requests pyyaml sympy openpyxl datasets huggingface_hub
```

### Python (language models)

These scripts need a CUDA build of PyTorch and a GPU. Models are **not** in this repo. First run with `--allow-download` writes snapshots under `~/.cache/huggingface/hub`. Do not commit those files. Do not commit `HF_TOKEN`.

```bash
source .venv/bin/activate
uv pip install torch transformers accelerate
```

Install a CUDA wheel that matches the machine. Original runs used torch 2.12.1+cu130, transformers 4.57.6. `scripts/run_masked_stem_followup_gpu.py` and `scripts/run_masked_stem_scorer_capability_gpu.py` expect `.venv/bin/python` at this repository root.

## Bootstrap data

`data/items.jsonl` is in git (2405 keyed items). A clone does **not** need a full recensus for the frozen N.

```bash
# Verify the frozen census. Does not fetch PDFs.
bash scripts/bootstrap_data.sh

# Redownload public PDFs (STAAR URL guessing is slow; already-present files are skipped).
bash scripts/bootstrap_data.sh --download-pdfs

# If items.jsonl was deleted: download (unless --skip-download) and parse.
# Fails if a required corpus jsonl is missing. No OCR.
bash scripts/bootstrap_data.sh
```

Years and sources are those already in `scripts/download_public_pdfs.py` plus MCAS 2019 grade 7: STAAR, NY Regents, NYSED 3-8, NAPLAN 2012-2016, TIMSS 2011 and earlier public-release PDFs, PISA, EQAO. Do not treat later years as required.

Cue-control datasets (optional, not the 2405-item census):

```bash
source .venv/bin/activate
python scripts/download_real_controls.py
```

## Recreate exports

Frozen seeds: runner `mulberry32(20260916)`; strategy `RANDOM_SEED = 20260916`; STAAR bootstrap seed 11.

### Catalog a priori

Paper numbers: `exports/rule-chance.json`, `exports/apriori-cell-table.json`, `exports/witnesses.json`, `exports/addendum/e1-witness-dependence.json`, `exports/addendum/apriori-cues-extended.json`. Those files are tracked. The giant `exports/trials.jsonl` is optional.

```bash
./validate items data/items.jsonl
./validate claims claims/utah-core-6-8.json
./validate rules rules/apriori.json
npx tsx runner/src/cli.ts run
python scripts/build_apriori_cell_table.py
python scripts/run_e1_witness_dependence.py
python scripts/run_e2_apriori_cues_extended.py
python scripts/run_e3_choices_only_clean.py
python scripts/run_e4_held_out_searched.py
python scripts/run_e5_clustered_power.py
```

`run` writes `exports/matrix.json`, `exports/witnesses.json`, `exports/comparisons.json`, `exports/rule-chance.json`, and appends `exports/trials.jsonl`. Resume skips completed `(itemId, programId)` pairs.

Bedrock is used only for choices-only, critique, labeler, and constructed-response grading. If credentials are absent, those backends are skipped. E3 rereads the tracked `exports/choices-only/scored.jsonl` and does not call Bedrock.

### Strategy channels

Paper numbers: `exports/addendum-strategies/*.json` (tracked).

```bash
python scripts/run_strategy_channels.py
python scripts/run_strategy_channels.py --s4-version 2
python scripts/run_s3_teks_g5_robustness.py
```

### STAAR replication

Needs local PDFs (`bash scripts/bootstrap_data.sh --download-pdfs`). Results JSON is tracked; parse dumps are not.

```bash
python scripts/inventory_staar_replication.py
python scripts/run_staar_replication.py
python scripts/run_staar_replication_v2.py
python scripts/run_staar_replication_extended.py
```

Grade 5 2015/2020/2023 forms were still unfetched at freeze. Do not invent those years.

### Masked-stem LM

CUDA GPU required. No CPU fallback. One GPU with about 16 GB is enough for 7B bf16. Qwen2.5-14B and Phi-4 bf16 need one GPU with at least 32 GB. Collaborator C can rerun these jobs on AWS; do not commit model weights or per-item `*-items.jsonl`.

| Model | id | revision |
|---|---|---|
| Qwen2.5-7B-Instruct | `Qwen/Qwen2.5-7B-Instruct` | `a09a35458c702b33eeacc393d103063234e8bc28` |
| Qwen2.5-14B-Instruct | `Qwen/Qwen2.5-14B-Instruct` | `cf98f3b3bbb457ad9e2bb7baf9a0125b6b88caa8` |
| Phi-4 | `microsoft/phi-4` | `2db69c1c3e91a05d2c64a3185acfbaf36f744e25` |
| Mistral-7B-Instruct-v0.3 | `mistralai/Mistral-7B-Instruct-v0.3` | `c170c708c41dac9275d15a8fff4eca08d52bab71` |

Paper cell tables live in tracked `exports/addendum-gpu/*.json`. Per-item jsonl is omitted and rebuilt by scoring.

```bash
source .venv/bin/activate
# Primary Qwen 7B masked-stem (withheld-quantity population)
python scripts/score_choices_only_local_lm.py \
  --model-id Qwen/Qwen2.5-7B-Instruct \
  --model-revision a09a35458c702b33eeacc393d103063234e8bc28 \
  --prompt-mode masked-stem \
  --min-masked-token-count 1 \
  --allow-download \
  --summary-path exports/addendum-gpu/masked-stem-7b.json \
  --items-out exports/addendum-gpu/masked-stem-7b-items.jsonl

python scripts/score_choices_only_local_lm.py \
  --model-id Qwen/Qwen2.5-14B-Instruct \
  --model-revision cf98f3b3bbb457ad9e2bb7baf9a0125b6b88caa8 \
  --prompt-mode masked-stem \
  --min-masked-token-count 1 \
  --allow-download \
  --summary-path exports/addendum-gpu/masked-stem-14b.json \
  --items-out exports/addendum-gpu/masked-stem-14b-items.jsonl \
  --batch-size 1 \
  --device-map cuda

# Mistral follow-up and Qwen with-stem algebra ceiling
python scripts/run_masked_stem_followup_gpu.py

# Phi-4 (and Mistral with-stem). Gemma-2-9B is gated and optional; not a paper claim.
python scripts/run_masked_stem_scorer_capability_gpu.py
```

`--allow-download` pulls weights from Hugging Face on the first run. Mistral may need `HF_TOKEN` in the environment; do not write that token into the repo. Qwen and Phi-4 are public.

### Human packet

Send `exports/human-masked-stem/rater-packet.txt`. Save replies as `exports/human-masked-stem/responses-<slug>.txt`.

```bash
python scripts/score_human_masked_stem.py --rater <slug>
```
