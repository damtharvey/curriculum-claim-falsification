# Masked-stem plus options, masking version 2 (preregistration)

Written 2026-09-16 before any version-2 GPU scoring. Exploratory addendum channel. Does not edit the frozen paper. Does not overwrite version-1 outputs.

## Question

After version-1 quantity masking, some stems still contain given content that lets a taker compute or recall the key without the numbers: a named figure type on a property item, a variable or function binding, or leftover coefficients in an algebraic expression. Version 2 hides those givens as well.

Primary scored population: items with version-2 `masked_token_count >= 1`. Report the delta versus version 1 on the version-1 `masked_token_count >= 1` overlap.

## Items

- Same clean keep list as version 1 (1496 ids, 1487 scoreable single-letter keys).
- Do not drop items solely because version 1 had `masked_token_count = 0`. Version 2 may withhold a named figure or binding on those stems.
- Do not rescore 14B. Version 2 GPU scoring is 7B only.
- Do not overwrite `masked-stem-7b.json`, `masked-stem-7b-items.jsonl`, or the 14B pair.

## Channel

Same prompt family as version 1, with the instruction updated to name the extra withheld classes:

Pick the letter of the correct answer. Given quantities, named figure types, and variable bindings in the question have been replaced by `[N]`.

Options stay in original order with letters, unmasked. No source name, exam name, or chain of thought. Greedy letter-logprob argmax after the chat template, seed `20260916`. Script: `scripts/score_choices_only_local_lm.py --prompt-mode masked-stem --mask-version 2`.

## Masking rules (stem only; options untouched)

Start from version 1 (numerals, decimals, percents, currency, fractions, number words, scale words, standalone quantity-fraction words, coefficients that are numerals). Then apply:

1. Named figure types that can fix a property or classification answer, replaced by `[N]`: isosceles, equilateral, scalene, regular plus a polygon name, and the names triangle, parallelogram, rhombus, rectangle, square, trapezoid, trapezium, kite, pentagon, hexagon, heptagon, octagon, decagon, quadrilateral, cube, cuboid, prism, pyramid, cylinder, cone, sphere, hemisphere, circle, including simple plurals. Do not mask the word `right` unless it is attached to a named figure type (`right triangle`). Do not mask generic words such as figure, diagram, or graph.
2. Variable and function bindings: `let x = ...`, `given f(x) = ...`, and `given f(x) 5 ...` where Regents OCR used `5` for equals after a function name. Replace the right-hand side of the binding with `[N]` up to the next comma, period, question mark, or semicolon so the question wording remains. Also replace `x = <expression>` when the right-hand side begins with a digit, sign, or `[N]`.
3. A second coefficient sweep after those replacements: any remaining numeral glued to a letter or parenthesis (`3x`, `2(`) becomes `[N]`.

Placeholder remains `[N]` for every class so scoring is unchanged. Options are never masked. Prefer remasking to dropping.

## Metrics

On the version-2 `masked_token_count >= 1` population, 7B only:

- Pooled rate vs chance, vs always-B (stated 0.275 and recomputed on the population), vs per-cell modal-letter frequency on the population.
- Per source and per cell with n >= 10.
- Named cells: Algebra I, Algebra II, geometry, EQAO grade 6, TIMSS knowing / applying / reasoning, with n in each population.
- Delta versus version 1 on the overlapping version-1 `masked_token_count >= 1` ids: rate difference, McNemar n01/n10.

## Outputs

- `exports/addendum-gpu/masked-stem-v2-preregistration.md` and `.sha256` (this file, hashed before scoring)
- `masked-stem-v2-7b.json`, `masked-stem-v2-7b-items.jsonl`

Label exploratory. Do not deposit. Do not edit `paper/`.
