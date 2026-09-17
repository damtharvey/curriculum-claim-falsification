# Curriculum Claim Falsification

Minds and Machines (CHAT), 15-17 September 2026.

This repository is the **Curriculum Claim Falsification** project, also called CHAT: Does the Assessment Require the Skill? Independent git history begins 2026-09-16.

## One-sided claim

An assessment item carries a published tag: a standard code, or a TIMSS cognitive domain such as reasoning. A passing score is then read as evidence of that competency.

This project searches for programs that lack the tagged operation and still pass under the published key. Each such program is a witness that the tag overstates what a pass shows.

- A program that passes refutes the tag for that item.
- A program that fails proves nothing beyond the programs we tried.

We never say students did not learn the skill.

Full spec: `curriculum_claim_falsification_proposal.md`. Hackathon logistics: `CHAT-hackathon-plan.md`. Live snapshot: `STATUS.md`. Protocol-only OSF draft: `registration.md`.

## Layout

- `runner/` TypeScript requirement-matrix runner
- `scripts/` ingest, census tables, GPU language-model scoring
- `data/` public-release items and source PDFs (see `data/README.md`)
- `claims/`, `rules/`, `fixtures/`
- `exports/` matrices, witnesses, addenda, human rater packet
- `paper/` acmart preprint

## Setup

A GPU is required for language-model scripts. There is no CPU fallback.

### Node (runner)

```bash
npm install
chmod +x validate
```

`package-lock.json` is in the tree. Reinstall `node_modules` from that lockfile; it was not copied.

### Python (ingest and tables)

The original `.venv` was omitted (about 479 MiB). Create one with `uv`:

```bash
uv venv .venv
source .venv/bin/activate
uv pip install numpy pandas pymupdf pdfplumber pillow requests pyyaml sympy openpyxl datasets huggingface_hub
```

### Python (language models)

These scripts need a CUDA build of PyTorch and a GPU. Models are **not** in this repo; they are read from `~/.cache/huggingface/hub`.

```bash
source .venv/bin/activate
uv pip install torch transformers accelerate
```

Install a CUDA wheel that matches the machine. The original runs used torch 2.12.1+cu130, transformers 4.57.6, on an RTX 5090. `scripts/run_masked_stem_followup_gpu.py` and `scripts/run_masked_stem_scorer_capability_gpu.py` expect `.venv/bin/python` at this repository root.

## Runner

```bash
./validate items data/items.jsonl
./validate claims claims/utah-core-6-8.json
./validate rules rules/apriori.json
python3 scripts/parse_timss.py
npx tsx runner/src/cli.ts run --resume
```

Exports land in `exports/matrix.json`, `exports/witnesses.json`, `exports/comparisons.json`. Trials append to `exports/trials.jsonl` and resume by skipping completed `(itemId, programId)` pairs.

Bedrock is used only for choices-only, critique, labeler, and constructed-response grading. If credentials are absent, those backends are skipped.

## Paper

```bash
make -C paper
```

Needs `pdflatex` and `bibtex`. Mentor copy: `paper/mentor-packet/paper.pdf`. Email body: `paper/mentor-packet/cover.md`. Do not send `paper.md`.

## Human rater packet

Send `exports/human-masked-stem/rater-packet.txt`, not a PDF.

## Opening this repository

Open this repository root in the editor. No git remote is configured yet.
