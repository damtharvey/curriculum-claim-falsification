# Adaptive test-taker strategy channels — version 1 preregistration

- Version: 1
- Written: 2026-09-16T20:34:35Z
- Frozen items: `data/items.jsonl` (2405 keyed public items; 2245 selected-response)
- Frozen exports read but not modified: `exports/rule-chance.json`, `exports/comparisons.json`, `exports/method-controls.json`, `exports/apriori-cell-table.json`
- Scoring starts only after `preregistration.sha256` records the sha256 of this file
- One-sided claim shape (locked): a pass does not require the tagged operation; failure to find a witness does not certify the tag; we never say students did not learn
- Witness bar (locked): n >= 10 scored items in a cell; lower 95% item bootstrap CI (mulberry32, seed 11, 1000 replicates, same as `runner/src/run.ts`) strictly above chance; for composite channels S1 and S5 the pass rate must also exceed the random-program p95 defined below
- Chance for a rule that eliminates options is the mean over items of 1 / (number of remaining options), not 0.25
- Primary Holm family remains the 105 pre-registered a priori tests in `exports/apriori-cell-table.json`
- This addendum is a second family, pre-registered today. Holm is reported within this family and pooled with the 105. E2's 22 extra tests are not in either of those two counts unless the paper pass chooses to merge all three
- Cells: every (`authority`, `claim`) pair in `data/items.jsonl` that has at least 10 selected-response items. Each channel is scored on every such cell. A (channel, cell) row enters the Holm family if and only if n scored >= 10 and chance > 0
- Selected-response only. Numeric-constructed items are not scored (no option graph, no survivors, no letters)
- Tie-breaking named "lower-central" is the frozen catalog index: sort parsed option values ascending, pick the option whose value equals the value at index floor((n-1)/2), first letter in A–D order among options with that value (`addendum_lib.lower_central_key`)
- Last-resort letter for S5 is **B**. Per-cell modal key letters computed on these same items would leak the key distribution into the program. Frozen `exports/comparisons.json` and `exports/rule-chance.json` do not store a position prior. The GPU addendum's per-cell modals are the same items. Version 1 therefore uses the global letter B, which is also the usual four-option key mode in those frozen tables
- Unbound execution in the existing 15-rule catalog (`invert-and-multiply`, `coefficient-adjacent-to-x`, `percent-of`, `percent-change`, `unit-rate`, `y-equals-kx`, `area-lw`, `volume-lwh`, `mean-of-listed-numbers`) is already implemented in `runner/src/programs/apriori.ts` and already scored in `exports/rule-chance.json`. Those rates are reused as a comparison only; they are not this addendum's S3 program. S3 is the depth-2 arithmetic closure defined here
- If a rule must change after seeing pass rates, version 1 numbers stay on disk and a `preregistration-v2.md` with its own hash is written. Version 1 files are never overwritten with version 2 numbers
- Bootstrap and binomial tests match `scripts/addendum_lib.py`. One-sided binomial p-value is P(X >= nCorrect) under Binomial(n, chance)
- Random-program p95 uses 200 variants, mulberry32 seed 20260916, percentile definition: sort the 200 rates and take index floor(0.95 * 200) = index 190 (the 191st value), matching `runner/src/programs/search.ts` percentile usage in spirit (upper 95th of the random-program distribution)
- Control items: `data/real-controls-openbookqa.jsonl` and `data/real-controls-swag.jsonl` are on disk. Eval split matches `runner/src/run_real_controls.ts` `loadSplitCapped(..., 1500, 400)`: first 400 items whose `split` is test, validation, or dev. Strategies are scored on that hold-out only, not trained
- Hand-check sample (IDs filled into `hand-check.json` by the scorer using this rule, then judged): selected-response items sorted by `id`. S2 sample = first 15 whose stem matches a constraint keyword below. S4 sample = first 15 not in the S2 sample for which `extract_equations(stem)` is non-empty under the S4 regex. Judgments are recorded after scoring; the selection rule is fixed here

## Numeric parsing (shared)

`parse_option_number(text)`:

1. Strip; replace unicode minus (U+2212, U+2013, U+2014) with ASCII `-`; strip thousands commas between digits
2. If the whole string matches `^(-?\d+)\s*/\s*(-?\d+)$`, return that ratio (denominator 0 rejects)
3. Else leading signed decimal: `^[^\d-]*(-?\d+(?:\.\d+)?)` as in `addendum_lib.parse_leading_number`
4. Else None

Two numbers match if they are finite and `abs(a-b) <= 1e-4 * max(1, abs(a), abs(b))` or `abs(a-b) < 0.01` (same windows as `channels.ts` `matchNumericToChoice`).

Stem numbers: the same decimal and simple-fraction patterns over `stem` plus `figure.transcription` when present, in reading order, unique by the match relation above, cap 12 seeds.

## S1. Distractor-derivation hub

Literature: Haladyna and Downing (1989) item-writing taxonomy (write distractors from common student errors); Haladyna, Downing, and Rodriguez (2002) same guideline; Rodriguez (2005) on distractor functioning. The program does not use the key.

Applies when at least three options parse as numbers.

Fixed transform set T, in this order:

1. `times2`: x -> 2x
2. `div2`: x -> x/2
3. `times10`: x -> 10x
4. `div10`: x -> x/10
5. `plus1`: x -> x+1
6. `minus1`: x -> x-1
7. `signFlip`: x -> -x
8. `reciprocal`: x -> 1/x if x != 0, else skip
9. `square`: x -> x^2
10. `sqrt`: x -> sqrt(x) if x >= 0, else skip
11. `swapAdjacentDigits`: every swap of two adjacent digits in the option's digit string (sign and decimal point held in place; "123" yields 213 and 132). Skip if fewer than two digits
12. `dropTrailingZero`: if the integer nearest to x that matches x (integer options) is divisible by 10 and |x| >= 10, emit x/10; also, if the digit string ends in 0, emit the number with that 0 dropped
13. `addTrailingZero`: if x is an integer, emit 10x; else emit 10x (one extra trailing zero in the place-value sense)
14. `plusTenPercentRounded`: emit round(x * 1.1, d) where d is the number of digits after the decimal in the source option text, or d = 0 if the source is an integer
15. `minusTenPercentRounded`: emit round(x * 0.9, d) with the same d. Python round (banker's round) is accepted because it is the language default; d is the parameter, not a fit

Directed graph on parsed options: edge a -> b (a != b) if some T in the set sends the value of a to a number that matches b. Out-degree of a is the number of distinct other options reachable in one transform, not the number of matching transforms.

Require max out-degree >= 1; otherwise abstain (no derivation structure).

Pick the option with strictly highest out-degree. If several share the maximum, pick lower-central among those tied options. If lower-central is undefined (fewer than three tied values), pick the tied option with the smallest value, then first letter.

Chance: 1 / k with k = number of choices on the item (the rule picks one option; it does not eliminate). Report also 1 / n_parsed.

Metrics per cell: n, rate, chance, CI, unique-hub share (among scored items, fraction whose max out-degree belongs to exactly one option), coverage = n scored / n selected in cell.

Random-program p95: 200 variants. Variant v draws a uniform random subset of exactly 10 transforms from the 15 (matched complexity: a large proper subset of the error catalog) using mulberry32; tie-break among max out-degree options is uniform random over those options instead of lower-central. Same apply/abstain rule. p95 is the 95th percentile of the 200 per-cell pass rates. Witnesses must clear it.

## S2. Constraint elimination

Literature: Millman, Bishop, and Ebel (1965) elimination strategies (use the question to discard impossible options). Haladyna et al. (2002) on implausible distractors. Shallow stem keywords only. No solving.

Keyword rules, applied to the stem (case-insensitive). If several match, the allowed set is the intersection.

| Keywords in stem | Allowed set for the parsed option value |
|---|---|
| `how many` or `number of` | nonnegative integer: x >= 0 and abs(x - round(x)) < 1e-6 |
| `probability` | [0, 1] |
| `percent` or `percentage` or a `%` token | [0, 100] |
| `length`, `distance`, `area`, `volume`, `perimeter`, `height`, `width` | x > 0 |
| `interior` plus `angle`, or (`triangle` and `angle`) | (0, 180) |
| `angle` or `degrees` (and the interior-triangle rule did not fire) | (0, 360) |
| `mean` or `median`, and the stem contains at least two parsed numbers treated as data | [min, max] of those stem numbers (exclude a trailing years-looking 19xx/20xx only if it is the only number; no other exclusions) |
| anything else | no constraint |

An option is a survivor if it does not parse as a number (text options are not killed by numeric constraints) or if it parses and lies in the allowed set. If no constraint matched, every option survives.

If zero survivors remain, emit no answer (abstain on the pick); the item still counts in key-survival as key-not-surviving.

Pick:

- 1 survivor: that letter
- all survivors parse as numbers: lower-central among survivors (two survivors: index 0, the smaller)
- mix of text and numbers: first letter in sorted A–D order among survivors

Chance per item: 1 / n_survivors when n_survivors >= 1; undefined when abstaining. Cell chance is the mean of per-item 1 / n_survivors over scored items.

Report per cell: mean remaining options; share of items with exactly one survivor; key-survival rate (fraction of selected items in the cell whose published key letter is among survivors — if this is far below 1 the constraint rule is wrong); pick rate against effective chance; coverage of keyword-matched items; pick rate on the keyword-matched subset (not a second Holm family unless n>=10, and even then it is a sensitivity column, not a family test).

Family test: pick rate on all selected items in the cell with an emitted answer, n>=10, CI above effective chance. S2 is not composite in the S1/S5 sense; no random-program p95.

## S3. Arithmetic closure (unbound execution)

Literature: this paper's unbound-execution channel (formulas applied to stem numerals without binding them to the situation); Millman, Bishop, and Ebel (1965) "use the numbers given." Companion to the already-run catalog formulas, which remain in `exports/rule-chance.json`.

Seeds: up to 12 numbers from stem plus figure transcription, reading order, uniqueness by the match relation.

Depth 0: the seeds.

Depth 1: every + - × ÷ of an ordered pair from depth 0 (skip ÷ by 0 and non-finite or abs > 1e12); plus a^2 and sqrt(a) for each seed a >= 0 for sqrt. If the stem matches a geometry word (`triangle`, `circle`, `radius`, `diameter`, `circumference`, `rectangle`, `square`, `trapezoid`, `parallelogram`, `prism`, `cylinder`, `sphere`, `hypotenuse`, `base`, `height`, `width`, `length`, `perimeter`, `area`, `volume`), also a × π and a × b / 2 for seeds a, b at depth 1. π = 3.141592653589793.

Depth 2: + - × ÷ on ordered pairs from the depth-0-and-1 set, same skips, cap 4000 distinct values (first-seen by rounded 8-decimal key).

An option appears at depth d if its parsed value matches a value whose first appearance is at depth d (0, 1, or 2).

Pick the option that appears at the smallest depth. If several share that depth, lower-central among them. If none appear, abstain.

Chance among fired items: 1 / k.

Family rate: among items where the rule fires (an option is picked). Sensitivity, not family: imputed rate = (nCorrectFired + sum_{abstain} 1/k) / n_selected, i.e. abstentions counted as chance guesses in expectation.

Also report the share of selected items in the cell for which exactly one option is in the depth-1 set (S0 ∪ depth-1 values).

No random-program p95 (fixed a priori operator set, not a searched composite).

## S4. Backsolving

Literature: Millman, Bishop, and Ebel (1965) substitution strategy; the verify-versus-solve distinction in multiple-choice algebra (substitute a listed candidate rather than produce the unknown).

Fire only if the stem contains a parseable single-variable equation or inequality.

Regex (search, overlapping candidates of at most 80 characters per side):

```
(?P<left>[0-9A-Za-z.\s+\-*/×·÷^()√π]+)
\s*(?P<rel>==|≠|!=|≤|≥|<=|>=|=|<|>)\s*
(?P<right>[0-9A-Za-z.\s+\-*/×·÷^()√π]+)
```

Reject a candidate if either side contains `{`, or both sides have no single-letter variable, or after stripping `pi`/`π` the sides together contain more than one distinct single-letter variable matching `\b[A-Za-z]\b`. Units as trailing letters glued to numbers (`3m`) are tokenized as numbers before this count by inserting a space before a trailing unit letter that is not x, y, n, t, k, p.

The first surviving candidate is parsed with sympy (`sympify`, convert `^` to `**`, `×·` to `*`, `÷` to `/`, implicit multiplication `2x` -> `2*x`). Failure to parse is not a fire.

Each option yields a candidate value: `parse_option_number` on the option, or on the right-hand side if the option matches `^[A-Za-z]\s*=\s*(.+)$`. Non-numeric options are not substituted.

Substitute the value for the unique variable. Equality holds under the numeric match rule. Inequalities use the corresponding Python comparison on evaluated floats. A substitution that errors does not satisfy.

If exactly one option satisfies, pick it. Otherwise abstain (including 0 or 2+ hits).

Chance among fired: 1 / k.

Family: fired items, n>=10, CI above 1/k. Sensitivity: imputed rate with abstentions as chance guesses.

Breakout (reporting, not extra Holm tests):

Solving-tagged cells, pre-registered from tag names rather than from pass rates:

- `nyregents` / `algebra-i` and `nyregents` / `algebra-ii` (Regents Algebra I/II; CCSS A-REI lives at this course grain; items in this corpus do not carry `A-REI` strings on `officialTag`)
- `teks` / `alg1` (TEKS Algebra I)
- TEKS solve student-expectation subset, pooled as a derived row `teks` / `solve-se` if n>=10: `officialTag` in {`6.10(A)`, `6.10(B)`, `7.11(A)`, `7.11(B)`, `8.8(A)`, `8.8(B)`, `8.8(C)`, `A.5(A)`, `A.5(B)`, `A.5(C)`, `A.5(D)`, `A.8(A)`, `A.8(B)`}
- `eqao` / `g9` (the algebra-bearing EQAO assessment in this corpus; g3 and g6 are not)
- derived `timss` / `algebra`: `authority == timss` and `contentDomain` matches `/algebra/i`

"The rest" is every other (`authority`, `claim`) cell. Report S4 family rows on all cells including these, and additionally the pooled solving-tagged vs pooled rest fired rates.

No random-program p95.

## S5. Portfolio (test-wise taker)

One program. Fixed branch order, decided now:

1. S4 if unique satisfying option
2. else S3 if exactly one option is in the depth-1 set (unique at depth 1); pick that option
3. else S2 elimination, then S1 hub among survivors if that hub is unique (strict max out-degree among survivors with max degree >= 1)
4. else lower-central among numeric survivors; if that is undefined, first letter among survivors
5. else letter B if B is a choice, else the first letter in sorted order

Always emits an answer when the item has choices (step 5). Coverage 1 on selected items.

Per item, record the branch actually used. Effective chance:

- branches 1 and 2: 1 / k (testing, not elimination)
- branches 3 and 4: 1 / n_survivors
- branch 5: 1 / k

Headline cell rate against the mean effective chance of the branches used, and also against mean 1/k. Witness bar uses effective chance plus random-program p95.

Random-program p95: 200 variants. Each variant shuffles the five branch slots uniformly and replaces lower-central / unique-hub tie-breaks with uniform random choice among the candidates at that slot. Letter B remains B (it is a frozen prior, not a tie-break). Same apply-on-selected-items rule.

Headline cells (also in the family if n>=10, which they are): `nyregents` / `geometry`, `eqao` / `g6`, `timss` / `knowing`, `timss` / `applying`, `timss` / `reasoning`.

## Family index

Family rows are sorted by `channel`, `authority`, `claim`. `familyIndex` is 0-based in that order among rows with n>=10 and chance>0. Holm at alpha=0.05 on those p-values. Pooled Holm concatenates the 105 a priori p-values (same sort as `exports/apriori-cell-table.json` `family`) with this family's p-values.

S1 and S5 rows that do not also exceed p95 are not witnesses even if CI > chance; they still enter Holm on the binomial p-value against chance (Holm is the multiple-test correction for chance, not a substitute for the machine bar).

## Outputs

`exports/addendum-strategies/`: this file, `preregistration.sha256`, `s1-hub.json`, `s2-elimination.json`, `s3-closure.json`, `s4-backsolve.json`, `s5-portfolio.json`, `random-program-p95.json`, `controls.json`, `hand-check.json`, `strategy-cell-table.json`, `README.md`. Scripts: `scripts/strategy_channels.py`, `scripts/run_strategy_channels.py`.

## What this family is allowed to change in the paper

The paper is not frozen for this pass. A later writing pass may:

- add S5 (and any S1–S4) per-cell witnesses that clear the bar, including p95 for S1/S5
- recompute Holm on 105 + m
- treat general unbound closure (S3) as the numeric unbound channel if it clears; the catalog formulas stay as already reported
- leave geometry and EQAO middle-value witnesses in place unless this family produces a strictly stronger one-sided statement on those same cells; this family does not retract them

This family cannot say students did not learn, and cannot treat a TIMSS null as certified if these programs also fail.

## S4 version 2 (2026-09-16)

- Written: 2026-09-16T21:05:00Z
- Version-1 `extract_equations` / `apply_s4` and `s4-backsolve.json` stay on disk and are not overwritten
- Scoring of S4 version 2 starts only after `preregistration-v2.sha256` records the sha256 of this file
- Reason: version 1 fired on 1 of 1186 solving-tagged items. The v1 hand-check found one genuine inequality (`nyregents-algebra-i-2020-jan-q3`) that failed because U+0003 replaced a minus. Most algebra stems embed the equation in prose, use unicode minus, implicit multiplication, or ordered-pair options
- Same witness bar, chance 1/k among fired, imputed abstention-as-chance sensitivity, solving-tagged breakouts, and no random-program p95 as version 1
- Family rows: every (`authority`, `claim`) cell with n selected >= 10, scored on fired items, enter Holm iff n fired >= 10 and chance > 0. Version 2 Holm is reported in `s4-backsolve-v2.json` and is not pooled into the frozen 67/172 families unless a later writing pass chooses to
- Hand-check: selected-response items on which version 2 fires, sorted by `id`, first 30. Judgment is parse correct / wrong / ambiguous. If the published key does not satisfy the extracted equation on a fired item, count it as parse error or data error

### Minus and relations

Before parsing, replace as minus: U+2212, U+2013, U+2014, U+2010, U+2011, U+2012, U+00AD, ASCII hyphen-minus, and U+0003 (the OCR minus documented on the version-1 hand-check item). Relations recognized: `=`, `<`, `>`, `≤`, `≥`, `<=`, `>=`, `==`, `≠`, `!=`.

### Equation span

From each relation token, take the longest left and right spans that are math (digits, single-letter variables, `pi`/`sqrt`/`sin`/`cos`/`tan`/`log`/`ln`/`abs`, and `+-*/^()`), stopping at English stopwords. A leading stray variable left by phrases such as "values of x and y x + y" is dropped. Stems are also split on `\band\b` so a system can yield two equations. Both sides must parse with sympy (`parse_expr` with `convert_xor` and `implicit_multiplication_application`). Keep equations with 1 or 2 distinct single-letter variables.

This covers the registered prose forms: "Solve for x: 3x − 4 = 11", "What is the solution of 2(x − 3) = 8?", "If 5x + 2 = 17, what is x?".

### Substitution

Option values: `parse_option_number` (fractions, decimals, negatives, `X = value`) and ordered pairs `(a, b)` or `x = a, y = b`. Numeric match uses the version-1 windows.

- One-variable equation and scalar options: substitute into the first equation that evaluates for at least one option. Fire iff exactly one option satisfies
- Two-variable equation(s) and ordered-pair options: map `(first, second)` to `(x, y)` if those letters appear, else sorted variable names. If two equations share those two variables, the pair must satisfy both. Fire iff exactly one pair satisfies
- Otherwise abstain, including 0 or 2+ hits

### Outputs

`s4-backsolve-v2.json`, `s4-v2-hand-check.json`. Command: `python scripts/run_strategy_channels.py --s4-version 2`.

sha256 of this file immediately before S4 version 2 scoring (also in `preregistration-v2.sha256`): `c5b10dee55f2b762e9a9aa1aac2524e477b3101c8d2550ccf2456ce4105911d2`

