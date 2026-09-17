# Option-numeral isomorphs on the masked-stem channel (preregistration)

- Written: 2026-09-17T05:50Z, before any original or perturbed GPU scoring for this addendum.
- Purpose: review-2 weakness 4 question 4 and weakness 8. The masked-stem Algebra I claim is that a capable letter-argmax reader recovers the New York Regents key from question type plus option form when every given quantity in the stem is hidden. Released Regents forms are widely mirrored. The contamination alternative is that the reader recovers a memorized item (year, question number, option letter) rather than the form of the options. This control replaces the numerals in the option strings with value-changing, form-preserving isomorphs and rescores the same masked stem, the same key letter, the same models, and the same letter-logprob rule. Scoring starts only after `preregistration.sha256` records the sha256 of this file. The runner refuses to score if the file has changed.
- One-sided wording (locked): a pass does not require the tagged operation. Nothing here says students did not learn.
- Does not edit `paper/`. Writes only to `exports/isomorph-options/` and `scripts/`.

## Question (locked)

Does the reader recover the New York Regents Algebra I key from the form of the options, or from memorized item numbers?

## Population (locked)

Algebra I and Algebra II withheld-quantity masked-stem primary items from `exports/addendum-gpu/masked-stem-algebra-primary-item-ids.json` (606 ids; every item has at least one `[N]` under masking hash v1, `exports/addendum-gpu/masked-stem-preregistration.md` sha256 `af473bb6cd9d46dc74e034f4460d56a808273fe83ffaf457cd7d122c40ae80e8`). Census options and keys from `data/items.jsonl`. Masked stems recomputed with `scripts/score_choices_only_local_lm.py` `mask_stem` version 1; they must match the saved `masked_stem` field on the per-item prediction files.

| subset | definition | n |
|---|---|---:|
| Algebra I all | `claim = algebra-i` in the primary list | 358 |
| Algebra I print-faithful | verdict `faithful` on `exports/print-faithful/fidelity-items.jsonl` (stage calibration or census) | 184 |
| Algebra I faithful and recognition | print-faithful and verb class `recognition_or_interpretation` from `exports/standards-split/item-standards.jsonl` plus the locked cluster table in `exports/standards-split/execution-subset.json` | 83 |
| Algebra I faithful and execution | print-faithful and verb class `execution` | 75 |
| Algebra II all | `claim = algebra-ii` in the primary list | 248 |
| Algebra II print-faithful | same print-faithful rule | 115 |

Algebra I all is the primary population. Algebra I print-faithful is the claimed cell. Algebra I faithful and recognition / execution are the verb-class split. Algebra II is a secondary reference (the cell is not claimed on print-faithful items). Mixed-class items are not a pre-registered row.

## Perturbation (locked)

Seed `20260916`. Per item and arm, the RNG is `random.Random(int(sha256(f"{seed}:{arm}:{item_id}")[:16], 16))`, so the map does not depend on processing order.

Within each item, parse every numeral in the option strings, left to right:

- Integers, including coefficients and exponents written with ASCII digits (`3x^2`, `x2` on the dirty layer, `-4`).
- Decimals, including leading-dot forms (`.5`, `.20`) and trailing zeros (`3.00`). Decimals are one token; the digits inside them are not also integers.
- Comma-grouped integers (`12,000`). Digit count ignores commas. `(0,2)` is two integers, not a grouped integer, because the group after the comma is not three digits.
- Fractions `a/b` with optional signs and optional spaces around `/`. Numerator and denominator are integer literals. The denominator must be nonzero after replacement.

A minus is a sign when it is ASCII hyphen-minus, Unicode minus, or en-dash, it sits immediately before a digit or a leading-dot decimal, and the previous character is not alphanumeric and not a decimal point. Otherwise the minus stays an operator and the following digits are an unsigned integer. Variables, operators, units, words, option letters, and letter order are not changed. The key letter is not changed. Roman numerals (`I`, `II`, `III`) and number words (`one`, `zero`) are not numerals.

Replacement grain: each distinct atomic literal, identified by its exact matched text inside the item. The same text in two options, or in a fraction numerator and a standalone integer, maps to the same new text (consistent substitution). A signed literal is not the same key as its unsigned counterpart (`-4` is not `4`).

Each replacement is value-changing and form-preserving:

- Integer: same digit count and sign; zero is unsigned and is replaced by a positive one-digit integer. Destination strings in the item are injective.
- Decimal: same number of digits before the point (including a leading `0`), same number of decimal places, same leading-dot form, same sign.
- Comma-grouped integer: same digit count and sign, commas re-inserted in thousands groups.
- Fraction: numerator and denominator each replaced by a same-digit-count integer of the same sign; denominator nonzero.

Primary arm `isomorph_rank_preserving`. The option-level leading number is the first numeral token in that option (fraction value `a/b`, otherwise the parsed number). Options with no numeral do not participate. Unique leading tokens are sorted by original numeric value then by matched text. For each unique leading token a same-form replacement is drawn. The whole leading tuple is rejected and redrawn until the pairwise order of the new values equals the pairwise order of the originals, ties remaining ties. That is the rule "sort original leading numbers, sample new ones, sort, assign by rank" restricted so that a token never receives a replacement of a different kind or digit count. Remaining non-leading atomic literals are then drawn independently under the same form and injectivity rules.

Secondary arm `isomorph_rank_scrambled`. The same atomic replacement, with no rank-order constraint.

Items with no numeral token in any option are unchanged under both arms. They are the `no_numeral` subset. They are included in pass rates. They are excluded from the paired (perturbed minus original) difference.

Per item the substitution map, the original and perturbed option strings, whether the item is `no_numeral`, and the leading numbers before and after are recorded on `perturbed-items-{arm}.jsonl`.

Five before/after option sets are printed to the README. Digit counts, signs, decimal places, nonzero denominators, consistent substitution, and rank order on the rank-preserving arm are checked with assertions before any GPU scoring of the perturbed arms.

## Scoring (locked)

Same masked stem, perturbed options, same key letter position, same models, same letter-logprob rule as `scripts/score_choices_only_local_lm.py`: chat template with `add_generation_prompt=True`, next-token log-softmax, max of the bare letter token and the space-prefixed letter token, greedy argmax, ties keep the earlier option. Seed `20260916`. CUDA required; no CPU path. Masking hash v1. Prompt mode `masked-stem`, mask version 1.

Models, same revisions as `paper/appendix.tex`, local snapshots:

- `Qwen/Qwen2.5-7B-Instruct` `a09a35458c702b33eeacc393d103063234e8bc28`, bf16, `device_map` `.to(cuda)`, batch size 4.
- `Qwen/Qwen2.5-14B-Instruct` `cf98f3b3bbb457ad9e2bb7baf9a0125b6b88caa8`, bf16, `device_map="cuda"`, batch size 1.
- `microsoft/phi-4` `2db69c1c3e91a05d2c64a3185acfbaf36f744e25`, bf16, `device_map="cuda"`, batch size 1.

The original options are re-scored (not copied from disk) so that original and perturbed letters come from one model load. Letter agreement with the saved predictions in `exports/addendum-gpu/masked-stem-{7b,14b,phi4}-items.jsonl` must be at least 0.98 on the 606 ids. If it is not, scoring of the perturbed arms stops and the agreement is reported.

Output: `scores-{model}-{arm}.jsonl` with `id`, `predicted_letter`, `logprobs` per letter, plus `key`, `correct`, `n_options`, `claim`, `arm` so the rates can be recomputed.

## Statistics (locked)

Per model and per subset in the population table:

- Original pass rate (re-run).
- Rank-preserving pass rate.
- Scrambled pass rate.
- n, chance (mean 1/k, which is 0.25 on this population), modal key-letter frequency of the subset (ties take the earliest letter in A-E), bootstrap 95% percentile CI of the pass rate (`random.Random.randrange`, 1000 replicates, seed `21 + n`, rows in `masked-stem-algebra-primary-item-ids.json` order restricted to the subset).
- Whether the rate clears the channel bar: n >= 10 and the lower bootstrap 95% CI strictly above chance 0.25 and strictly above that subset's modal-letter frequency.
- Paired bootstrap 95% CI of (perturbed minus original) on items that are not `no_numeral`, same percentile method, seed `31 + n`, 1000 replicates. Reported for each perturbed arm.

`no_numeral` counts are reported for Algebra I and Algebra II.

## Pre-registered reading (locked, stated before scoring)

Applied to Algebra I print-faithful, primary arm `isomorph_rank_preserving`, each model separately.

- If the perturbed rate on the faithful subset clears the channel bar and the paired difference CI includes 0, the reader is form-based and the contamination concern is not supported.
- If the perturbed rate falls to chance (lower bootstrap 95% CI is not strictly above 0.25), the original rate is not a form effect.

A drop that stays above chance, a bar miss with a difference CI that includes 0, or disagreement between models, is mixed and is not either polar reading. The scrambled arm is reported; it is not the primary reading. Algebra II print-faithful is a reference row, not a claim.

## What this does not do

It does not edit `paper/`. It does not change the print-faithful verdicts or the verb-class table. It does not substitute numerals in the already-masked stem. It does not permute option letters.
