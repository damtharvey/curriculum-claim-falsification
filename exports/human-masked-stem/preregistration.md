# Human rater, masked-stem plus options (preregistration)

Written 2026-09-16T21:37:18Z, before the 40-item sample is drawn. Exploratory addendum. Does not edit the frozen paper. No GPU.

This file is hashed to `preregistration.md.sha256` before `sheet-rater.md` or `sheet-key.json` exist.

## Question

On New York Regents Algebra I selected-response items whose stems had at least one quantity withheld, can a human who sees the masked stem plus the lettered options beat chance 0.250 and beat the cell modal-letter frequency 0.271 (97/358), on the same channel bar used for the local LM: lower 95 percent bootstrap confidence interval (CI) strictly above both?

This is a flexible test-wise channel: the taker can use item type, leftover wording, and the option set, and cannot compute a numerical answer from the given quantities.

## Population (frozen)

- Cell: `nyregents::algebra-i`.
- Clean-option keep list used verbatim: `exports/addendum/choices-only-clean-filter.json` (the 1487 scoreable keep-list items).
- Primary masked-stem population: `masked_token_count >= 1` from `exports/addendum-gpu/masked-stem-item-mask-stats.jsonl` (mask version 1, placeholder `[N]`). Algebra I primary n = 358.
- Masking definition: `exports/addendum-gpu/masked-stem-preregistration.md` (sha256 `af473bb6cd9d46dc74e034f4460d56a808273fe83ffaf457cd7d122c40ae80e8`) and `scripts/score_choices_only_local_lm.py` `mask_stem(..., version=1)`. Options are not masked.
- Per-item masked stems are taken from `exports/addendum-gpu/masked-stem-14b-items.jsonl` field `masked_stem` (already stored). If a stored stem were missing, it would be regenerated with that same `mask_stem` function. Do not use mask version 2.
- Census items (`data/items.jsonl`) are read only for option strings.

Population key-letter counts on the 358 (from keys on the 14B item rows, which match the census keys):

| letter | count | share | 40 times share |
|---|---:|---:|---:|
| A | 85 | 0.237 | 9.497 |
| B | 97 | 0.271 | 10.838 |
| C | 96 | 0.268 | 10.726 |
| D | 80 | 0.223 | 8.939 |

Modal letter B, frequency 97/358 = 0.2709497206703911, written 0.271. All 358 items have four options, so chance is 0.250. Key is the lower-central numeric option on 82/358 items (`strategy_channels.lower_central_key` on `parse_option_number` pairs; undefined when no option parses as numeric). `masked_token_count` ranges from 1 to 36.

## Sample (drawn only after this file is hashed)

n = 40. Seed `202609161535` with `random.Random`.

Registered letter quotas (Python 3 `round` of 40 times share; the four integers already sum to 40): **A 9, B 11, C 11, D 9**. Each quota differs from 40 times the population share by at most one item. Sample modal-B share is 11/40 = 0.275, within one item of 0.271.

Lower-central cap: at most 12 of the 40 may have the key as the lower-central numeric option (population expectation 82/358 * 40 = 9.16).

Draw algorithm, deterministic given the seed:

1. Load the 358 ids. Sort each letter pool by id.
2. `rng = random.Random(202609161535)`.
3. For letters A, B, C, D in that order, take `rng.sample(pool, quota[letter])`.
4. If the number of selected items whose key is the lower-central numeric option is greater than 12, discard the draw and repeat step 3 with the same `rng` (rejection sampling). Raise if 10000 draws fail.
5. `rng.shuffle` the accepted 40. That order is items 1 to 40 on the sheet.

Record seed, quotas, accepted lower-central count, `masked_token_count` min and max, number of rejected draws, and the preregistration sha256 on `sheet-key.json`.

## Raters

- Rater 1: Author A. Response file `exports/human-masked-stem/responses-author-a.txt`.
- Rater 2: Author B (optional). Response file `exports/human-masked-stem/responses-author-b.txt`.

Each rater sees `sheet-rater.md` only: masked stem plus lettered options A-D. No item id, no source, no year, no key, no 14B pick, no feedback. Each works alone. No web search, no calculator beyond ordinary arithmetic, no discussion of items until that rater has finished. Record one letter per item, start time before item 1, end time after item 40, and an optional one-word cue note per item.

Do not open `sheet-key.json` until that rater's response file is written.

## Leakage rule

If a rater recognizes an item from memory, they mark `R` for that item. `R` is excluded from the primary rate, the CI, and kappa, and is counted (`nRecognized`, item numbers, ids). A leftover `R` does not replace the letter. Invalid tokens other than A-D or R are a scoring error, not a recode.

Primary n is 40 minus the number of `R` marks for that rater. If primary n is 0, scoring stops with an error.

## Prediction (primary)

On rater 1, after `R` exclusions, the human pass rate has lower 95 percent bootstrap CI strictly above 0.250 and strictly above 0.271 (97/358). That is the paper's masked-stem channel bar, applied to this sample (the n >= 10 clause is met at the registered n=40 if at most 30 items are marked `R`).

Rater 2, if present, is a replication on the same 40 items, scored the same way, not pooled with rater 1 unless a later note says so.

## Comparison (secondary, same 40 items)

Frozen 14B picks: `exports/addendum-gpu/masked-stem-14b-items.jsonl` field `chosen_letter` for `Qwen/Qwen2.5-14B-Instruct` revision `cf98f3b3bbb457ad9e2bb7baf9a0125b6b88caa8`, prompt-mode `masked-stem`, seed `20260916`. Do not rescore.

Report:

- Human rate and CI on the included items.
- 14B rate on those same included items (and on all 40, labelled separately).
- Cohen's kappa between the human letter and the 14B letter on the included items (letters A-D, not correctness). `p_o` is the agreement rate. `p_e` is the chance agreement from the product of the two empirical letter margins. `kappa = (p_o - p_e) / (1 - p_e)`. If `p_e = 1` and `p_o = 1`, kappa is 1. If `p_e = 1` and `p_o < 1`, scoring stops with an error.

Kappa has no bar. It is descriptive.

## Chance, CI, and power

- Chance is 0.250 (mean of 1/k; k=4 on every population item).
- Modal-letter frequency is 97/358 = 0.2709497206703911, written 0.271.
- 95 percent percentile bootstrap CI: `random.Random.randrange`, 1000 replicates, seed `21 + n` with n equal to the number of included items, same indexing as `scripts/score_choices_only.py`: sort the 1000 rates; lower = index `int(0.025 * (1000 - 1))`; upper = index `int(0.975 * (1000 - 1))`. Script: `scripts/score_human_masked_stem.py`.

The bar is the lower CI, not the point estimate. A point estimate above 0.271 with lower CI at or below 0.271 does not clear.

### Minimum detectable rate at n=40, 80 percent power, against 0.25

H0: p = 0.250. Success event: lower 95 percent bootstrap CI (flags = k ones followed by n-k zeros, seed `21 + 40`) is strictly above 0.25. That event first occurs at **k = 17** (rate 0.425). At k = 16 the registered bootstrap lower bound is 0.250 and does not clear.

Let X ~ Binomial(40, p1). The smallest p1 such that P(X >= 17) >= 0.80 is **0.479**. At p1 = 0.479, power is 0.800. At the 14B Algebra I primary point estimate 0.416, power for this n=40 bar is 0.51. At 0.45, power is 0.681.

Wald closed form `n = (z_{0.975} sqrt(p0 q0) + z_{0.80} sqrt(p1 q1))^2 / (p1 - p0)^2` with n=40, p0=0.25 gives p1 = 0.450. That formula is not the registered success event. The registered minimum detectable rate is **0.479**.

The same k = 17 is the first count whose bootstrap lower bound also exceeds 0.271, so the 80 percent minimum detectable rate against the modal letter at n=40 is the same 0.479.

A null at n=40 (lower CI not above 0.25) is uninformative for true rates below 0.479. It does not show that humans are at chance. If `R` marks cut n below 40, power is worse than this figure.

## What may be said after scoring

- Clears the channel bar: rater 1 included n >= 10 and lower CI > 0.250 and lower CI > 0.271. The addendum may say a human on this channel cleared the same bar as 14B on Algebra I primary, on this 40-item sample.
- Does not clear: included n >= 10 and the lower CI is not above both. The addendum may not say humans beat position on this channel. If the point estimate is above 0.271 but the lower CI is not, say that.
- Underpowered null: lower CI not above 0.250 and the implied true rate compatible with the interval includes values below 0.479. Say the n=40 test was underpowered for rates below 0.479, not that the channel is absent for humans.
- Pooled rater 1+2 is not the primary verdict.
- 14B rate on the 40 is a comparison, not a new 14B cell.

## Outputs

- `exports/human-masked-stem/preregistration.md` and `preregistration.md.sha256` (this file, hashed before the sample)
- `sheet-rater.md` (no ids, no keys, no year)
- `sheet-key.json` (not to be opened by raters before they finish)
- `scripts/score_human_masked_stem.py`
- `responses-<rater>.txt` (written by the rater)
- `results-<rater>.json` (written by the scorer)
- `README.md`

Do not modify `paper/`, `data/`, or other `exports/` directories.
