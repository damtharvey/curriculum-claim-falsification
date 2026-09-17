# Masked-stem plus options (preregistration)

Written 2026-09-16 before any masked-stem GPU scoring. Exploratory addendum channel. Does not edit the frozen paper.

## Question

On the sibling clean selected-response keep list, can a local instruction-tuned language model beat chance, and beat the per-cell modal-letter frequency, when it sees the question type, units, and the option set, but every given quantity in the stem is hidden?

This models a flexible test-wise taker who reads the item type and the options but cannot compute the numerical answer.

## Items

- Keep list: `exports/addendum/choices-only-clean-filter.json` used verbatim (1496 ids).
- Score the same 1487 items that were scoreable as a single option letter in the existing choices-only local-LM runs. The nine keep-list items with a non-single-letter key are skipped for the same reason as before, not by changing the filter.
- Do not rescore options-only. Compare to `exports/addendum-gpu/choices-only-local-lm-items.jsonl` (7B) and `choices-only-local-lm-14b-items.jsonl` (14B) already on disk.

## Channel

Prompt the model with:

1. The stem after quantity masking (below).
2. The options in original order with letters, unmasked.

Instruction: pick the letter of the correct answer. The model is told that numeric quantities in the question were replaced by `[N]`.

No source name, exam name, or chain of thought. Scoring is greedy letter argmax from next-token log-probabilities after the chat template, identical to `scripts/score_choices_only_local_lm.py` (max of the bare letter token and the space-prefixed letter token; ties keep the earlier option). Seed `20260916`.

## Masking rules (stem only; options untouched)

Replace each of the following with the placeholder `[N]`. Keep units, operators, and question wording.

- Numerals: ASCII and Unicode digits, comma-grouped integers, signed numbers, years, item counts, measured values.
- Decimals, including leading-dot forms such as `.5`.
- Percentages: the numeric part; keep `%` or the word percent as a unit.
- Currency amounts: the numeric part; keep `$` or named currency words as a unit.
- Fractions: `a/b`, mixed numbers, Unicode vulgar fractions, and hyphenated word fractions such as `one-third` and `nine-tenths`.
- Number words: zero, one through twenty, thirty, forty, fifty, sixty, seventy, eighty, ninety, hundred, thousand, million, billion.
- Scale words that name a given multiplier: twice, thrice.
- Standalone quantity fraction words: half, halves, quarter, quarters.
- Variable-value assignments: the assigned numeric value (so `KC = 8` and OCR `KC 5 8` become `KC = [N]` / `KC [N] [N]`). Coefficients in expressions such as `3x+2` are numerals and become `[N]x+[N]`.

Do not mask ordinal or place-value wording when it is not a given amount (`third floor`, `tenths digit`, `fourth-degree`, `tenth term`), except the numerals attached to those phrases.

If a stem still contains a computable quantity after that pass (a leftover digit, leftover listed number word, a coordinate pair with a leftover numeral, a table of leftover values, or an unmasked expression such as `3x+2`), run a second sweep that replaces remaining digits and listed number words with `[N]`. If a computable quantity still remains, drop the item and count the drop. Prefer remasking to dropping so the paired 1487-item comparison stays intact.

## Masking audit

Before scoring, draw a 40-item sample with `random.Random(20260916).sample` from the scoreable keep-list items, save original stem and masked stem to `exports/addendum-gpu/masked-stem-audit-sample.json`, and record leak flags plus any drops. A reader should be able to verify that no computable quantity leaked in the sample.

## Models

- `Qwen/Qwen2.5-7B-Instruct` revision `a09a35458c702b33eeacc393d103063234e8bc28`, bf16, GPU, no CPU fallback.
- `Qwen/Qwen2.5-14B-Instruct` revision `cf98f3b3bbb457ad9e2bb7baf9a0125b6b88caa8`, bf16, `device_map="cuda"`, batch size 1.

Hardware: RTX 5090 32 GB. Require CUDA.

## Metrics (per model)

Pooled:

- Pass rate vs mean chance (1/k) with bootstrap CI (`random.Random.randrange`, 1000 replicates, seed `21 + n`, same as choices-only).
- Pass rate vs the always-B baseline 0.275 (the modal key letter on the 1487 scored items).
- Increment over options-only on the same items and same model: share where masked-stem is correct and options-only is not; the reverse share; McNemar counts (n01, n10, both correct, both wrong).

Per source and per cell with n >= 10:

- Rate and CI.
- Whether the lower CI clears chance.
- Whether the lower CI clears that cell's modal-letter frequency from `exports/addendum-gpu/position-and-memorization.json` (ties: earliest letter in A-E).
- Rate on items whose key is not the cell modal letter.

Named cells to report even if thin:

- Witness cells already in the frozen paper: `nyregents::geometry`, `eqao::g6`.
- `nyregents::algebra-i`.
- TIMSS `timss::knowing`, `timss::applying`, `timss::reasoning` (few TIMSS items survive the clean filter; report n).

## Witness bar for this channel

Exploratory unless a cell has n >= 10, lower CI above chance, and lower CI above that cell's modal-letter frequency. Pooled rate is not a paper cell. Do not deposit. Do not edit `paper/`.

## Outputs

- `exports/addendum-gpu/masked-stem-preregistration.md` and `.sha256` (this file, hashed before scoring)
- `masked-stem-7b.json`, `masked-stem-7b-items.jsonl`
- `masked-stem-14b.json`, `masked-stem-14b-items.jsonl`
- `masked-stem-audit-sample.json`
- Section appended to `exports/addendum-gpu/README.md`

Script: `scripts/score_choices_only_local_lm.py` with `--prompt-mode masked-stem`. Do not write a new scorer. Do not modify `data/`, `exports/addendum/`, `exports/addendum-strategies/`, or the earlier GPU JSON files.
