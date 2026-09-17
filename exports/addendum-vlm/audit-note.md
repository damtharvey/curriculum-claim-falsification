# Algebra I image-backsolve audit

Scored file `backsolve-extract.json` is unchanged. Paper numbers come from the derived file `backsolve-extract-honest.json`.

Recomputed from `backsolve-extract-items.jsonl` with `scripts/addendum_lib.py` `bootstrap_ci_mulberry` (mulberry32 seed 11, 1000 replicates), same as the scoring script.

## Original unique-satisfier (do not use as the claim)

- Cell: New York Regents Algebra I, solving-tagged selected-response
- n eligible: 598 (all with a page PNG)
- n fired unique: 17
- hits: 14
- rate: 14/17 = 0.824
- chance (mean 1/k): 0.25
- 95% CI: [0.647, 1.000]
- coverage: 17/598 = 0.028
- All 17 Algebra I fires are in `hand-check.json`

## Recode rule

1. Extracted equation must be a displayed equation on the page. Invent-and-solve (a formula the vision-language model wrote that is not printed) is a construct violation: abstain, not a hit.
2. `parse_wrong` is abstain (the unique-satisfier result is not a substitution into the printed relation).
3. `parse_correct` and the published key's transcribed option does not satisfy: error. Keep as a fired miss. Dropping those misses would inflate the rate.

## Dropped (Algebra I)

| id | original | recode | why |
|---|---|---|---|
| `nyregents-algebra-i-2024-jan-q2` | fired miss | abstain `invented_equation` | No displayed equation. Function/relation item. Model invented `x=2` from an option. Prompt forbids solving. |
| `nyregents-algebra-i-2018-jan-q10` | fired miss | abstain `parse_wrong` | Page shows two graphs `y=x^2-3` and `y=3x-4`. Extract kept only the first. Incomplete displayed-system extract. |

Both were misses in the original 14/17, so recoding them as abstain raises the rate and does not create hits.

## Kept as error

| id | original | recode | why |
|---|---|---|---|
| `nyregents-algebra-i-2014-aug-q5` | fired miss | error | Equation `y=x^2+3x-6` matches the page (`parse_correct`). Item asks which point is **not** on the graph. Unique satisfier picks a point that is on the graph. Genuine miss. |

## Honest fired set

- n fired: 15
- hits: 14
- rate: 14/15 = 0.933
- chance: 0.25
- 95% CI: [0.800, 1.000]
- coverage: 15/598 = 0.025
- rate with abstentions as chance: 0.267
- one-sided binomial P(X>=14 | n=15, p=0.25) = 4.28e-8
- **clears witness bar: yes** (n fired >= 10 and lower CI 0.800 > chance 0.25)

This addendum is **not** a member of the 67 strategy Holm tests. Bill it as an existence row measured after the catalog: n fired, coverage, one-sided. Coverage 2.5% is the population statement. Substitution recovers the key on rare unique displayed-equation items. It does not recover Algebra I keys in general.

Other cells still have n fired < 10 (Algebra II 6, TEKS Algebra I 6, TEKS solve-SE 5). Their invent-and-solve fires (compound interest; ticket-price formula) are outside the Algebra I honest set.

Hand-check of 30 fired items overall remains parse_correct 25, parse_wrong 5, key-does-not-satisfy 6. The five wrong extracts were not dropped from the original scored file.
