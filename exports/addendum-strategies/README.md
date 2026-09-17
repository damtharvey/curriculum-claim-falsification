# Adaptive test-taker strategies (addendum, 2026-09-16)

Science-only. Pre-registered in `preregistration.md` (sha256 `a0eda4bdb02e54765bb7b49dca5e2e8ea9cd9ebb66de67b2aae074e7d555f0b4`, UTC 2026-09-16T20:36:16Z) before any scoring. Version 1 numbers were not overwritten. The paper is not frozen; a separate writing pass should cite the fields below.

Witness bar (locked): n >= 10, lower 95% item bootstrap CI (mulberry32 seed 11, 1000) strictly above chance; S1 and S5 also above random-program p95 (200 variants, seed 20260916). Chance after elimination is mean 1/remaining, not 0.25. One-sided: a pass does not require the tagged operation; we never say students did not learn.

Unbound execution in the 15-rule catalog is implemented (`runner/src/programs/apriori.ts`) and already scored in `exports/rule-chance.json`. Those rates are reused as comparison only. The new S3 program is depth-2 arithmetic closure, not a reread of invert-and-multiply / unit-rate / etc.

## Question

Do adaptive test-taker channels (distractor-derivation hub, constraint elimination, arithmetic closure, backsolving, and a fixed-order portfolio) clear the witness bar on frozen cells, and do they survive Holm as their own family and pooled with the 105 a priori tests?

## Method

Scripts: `scripts/strategy_channels.py`, `scripts/run_strategy_channels.py`. Cells are every (`authority`, `claim`) with at least 10 selected-response items (17 cells). Family rows are those with n scored >= 10 and chance > 0.

## Family count for Holm

- This addendum: **67** tests. Bonferroni cut 0.05/67 = 0.000746.
- Pooled with the 105: **172**. Bonferroni cut 0.05/172 = 0.000291.
- Clears the per-cell bar: 3 (S2 geometry, S2 EQAO g6, S3 TEKS g5).
- Holm rejects in this family: **1** (S3 TEKS g5).
- Holm rejects pooled with 105: **1** (the same row). None of the original 105 reject in the pooled list.

Cite: `exports/addendum-strategies/strategy-cell-table.json` fields `nFamilyTestsThisAddendum`, `nFamilyTestsPooledWith105`, `nHolmRejectThisFamily`, `nHolmRejectPooledWith105`, `rows[channel=s3-closure, authority=teks, claim=g5]`.

## Per channel

### S1 distractor-derivation hub

Coverage among selected items is about 0.40–0.65 on numeric-heavy cells (geometry 161/408=0.395; EQAO g6 28/53=0.528). Unique-hub share among scored items is **0.189** pooled (992 family-scored items); most hubs are ties broken by lower-central.

No cell clears the bar once p95 is required. TEKS g4 is the only chance-only clear: n=22, 0.455, CI [0.273, 0.682] vs chance 0.250, p95 0.476, so it fails the machine bar.

Geometry 0.255 n=161 CI [0.193, 0.317] vs 0.250, p95 0.311. EQAO g6 0.321 n=28 CI [0.179, 0.500] vs 0.254, p95 0.438. TIMSS knowing / applying / reasoning all miss.

Cite: `exports/addendum-strategies/s1-hub.json` `familyRows`, `uniqueHubShare`; p95 in `random-program-p95.json` `s1`.

### S2 constraint elimination

Always emits on almost every selected item. Mean remaining options stay near 4 (geometry 3.92; EQAO g6 3.77). Share with exactly one survivor is ~0–0.02. Elimination share is 2–3% on the headline cells, so the pick is mostly lower-central among all options.

Key-survival: geometry **0.985**, EQAO g6 **0.906**, TEKS g8 **0.877**, EQAO g9 **0.885**. Hand-check 13/15 keys survive; two specified intersections kill the key (probability with percent-point options; interior-angle (0,180) on a rectangle angle-sum). The constraint rule is wrong on those items. Do not treat S2 as a clean elimination witness.

Per-cell bar, not Holm:

- NY Regents geometry n=404, 0.307, CI [0.262, 0.351] vs effective chance 0.254. **Not independent of the existing middle-value witness** (elimination share 0.025). Keyword-matched subset n=162, 0.352, CI [0.278, 0.426] vs 0.260 still clears, still a sibling of lower-central.
- EQAO g6 n=51, 0.412, CI [0.275, 0.529] vs 0.268. Keyword-matched subset n=19 does **not** clear. Keep the pre-registered middle-value row as the claimed EQAO witness.

TIMSS reasoning n=66, 0.379, CI [0.258, 0.500] vs 0.263: lower bound 0.258 vs chance 0.263, does not clear.

Cite: `s2-elimination.json` `familyRows` fields `passRate`, `chanceRate`, `ci95`, `keySurvivalRate`, `meanRemainingOptions`, `shareEliminated`, `keywordMatchedSubset`.

### S3 arithmetic closure (unbound execution)

Fired coverage 0.40–0.78. Share with exactly one option in the depth-1 closure is 0.07–0.20.

**Clears and survives Holm:** TEKS g5, n=40, 21/40=0.525, CI [0.375, 0.675] vs chance 0.250, p=0.000175. Unique depth-1 share 0.167. Imputed rate with abstentions as chance guesses 0.433.

This is the same cell as the already-scored catalog `unit-rate` row in `exports/rule-chance.json` (n=12, 0.417, CI [0.167, 0.750], chance 0.146, unclaimed). S3 is a different program with larger n. A writing pass may add g5 unbound closure as a per-cell witness. It is related to that catalog row, not a second independent mechanism. One-sided only.

No other S3 cell clears. Geometry 0.196 n=224 CI [0.143, 0.250] vs 0.250 (lower bound equals chance). EQAO g6 0.185 n=27. TIMSS knowing 0.393 n=28 CI [0.214, 0.571] vs 0.248 does not clear.

Cite: `s3-closure.json` `clears[0]` and `reusedCatalogUnbound.beatsChance`.

### S4 backsolving

Family tests: **0**. One unique fire in the whole census (STAAR Algebra I 2019 q3, correct). Solving-tagged pooled coverage 1/1186. TIMSS algebra content-domain: 0 fires on 14 items.

Regents OCR breaks operators; most selected algebra items have equation-valued options, not numeric candidates for a single unknown. Hand-check: 0/15 fired; 1 genuine backsolve item (`nyregents-algebra-i-2020-jan-q3`) failed to parse because U+0003 replaced the minus.

Cite: `s4-backsolve.json` `nFamilyTests`, `breakoutsNotInFamily`; `hand-check.json` `s4Summary`.

### S5 portfolio (headline)

Fixed order: S4 unique, else S3 unique at depth 1, else S2+S1 unique hub, else lower-central among survivors, else B. Almost all mass is lower-central among survivors. S4 unique is used once (TEKS alg1). Letter B is never reached on headline cells.

Random-program p95 is required. No S5 cell clears it.

| cell | n | rate | effective chance | CI | vs 1/k | 1/k chance | p95 | bar |
|---|---:|---:|---:|---|---|---:|---:|---|
| NY Regents geometry | 408 | 0.279 | 0.253 | [0.238, 0.321] | 0.279 | 0.250 | 0.297 | no |
| EQAO g6 | 53 | 0.453 | 0.267 | [0.321, 0.585] | 0.453 | 0.253 | 0.472 | no (clears chance and 1/k; fails p95) |
| TIMSS knowing | 65 | 0.308 | 0.271 | [0.200, 0.431] | 0.308 | 0.271 | 0.292 | no |
| TIMSS applying | 54 | 0.333 | 0.254 | [0.204, 0.463] | 0.333 | 0.249 | 0.370 | no |
| TIMSS reasoning | 68 | 0.309 | 0.263 | [0.206, 0.426] | 0.309 | 0.258 | 0.338 | no |

EQAO g6 vs 1/k: CI [0.321, 0.585] vs 0.253, `againstOneOverK.clearsBar` true, still not a witness because 0.453 < p95 0.472.

Cite: `s5-portfolio.json` `headlineCells` fields `passRate`, `chanceRate`, `ci95`, `againstOneOverK`, `randomP95`, `branchCounts`.

## Controls (OpenBookQA and SWAG)

Same eval split as `runner/src/run_real_controls.ts` (first 400 test/dev). Cite `controls.json`.

| dataset | channel | n | rate | chance | CI |
|---|---|---:|---:|---:|---|
| OpenBookQA | S1 | 3 | 0.000 | 0.250 | — |
| OpenBookQA | S2 | 400 | 0.260 | 0.250 | [0.217, 0.302] |
| OpenBookQA | S3 | 0 | — | — | — |
| OpenBookQA | S4 | 0 | — | — | — |
| OpenBookQA | S5 | 400 | 0.268 | 0.250 | [0.225, 0.310] |
| SWAG | S1 | 0 | — | — | — |
| SWAG | S2 | 400 | 0.247 | 0.250 | [0.205, 0.287] |
| SWAG | S3 | 0 | — | — | — |
| SWAG | S4 | 0 | — | — | — |
| SWAG | S5 | 400 | 0.240 | 0.250 | [0.198, 0.280] |

Numeric hub, closure, and backsolve do not run on these language items. S2/S5 sit on chance (OpenBookQA S5 0.268 is letter-B / first-letter behaviour, not a math-tuned spike).

## What the paper may change

- **Geometry middle-value 0.323 n=279:** keep. S2 0.307 n=404 is the same lower-central pick with almost no elimination. S5 0.279 is weaker. Do not replace the claimed witness.
- **EQAO g6 middle-value 0.500 n=40:** keep. S5 0.453 n=53 clears chance and 1/k but not p95. S2 0.412 is not Holm and is still mostly lower-central.
- **TIMSS knowing / applying / reasoning:** still a null for these channels.
- **New per-cell witness, Holm-surviving:** S3 closure on TEKS g5, 0.525 n=40 CI [0.375, 0.675]. Related to the unclaimed catalog unit-rate row on the same cell. One-sided wording only.
- **Holm:** recompute on 105+67=172. One reject (S3 TEKS g5). The two claimed middle-value rows still fail Holm.
- **Unbound execution:** catalog formulas were already run; S3 is the general depth-2 program. Do not say the channel was missing from the census.

## Version 2

S4 equation extraction was rewritten as `extract_equations_v2` / `apply_s4_v2` (`--s4-version 2`). Version 1 functions and `s4-backsolve.json` were not overwritten. Pre-registered in `preregistration.md` (S4 version 2 section; sha256 `c5b10dee55f2b762e9a9aa1aac2524e477b3101c8d2550ccf2456ce4105911d2`, UTC 2026-09-16T21:07:00Z) before scoring.

## S3 TEKS g5 robustness (version-1 numbers unchanged)

Version 1 remains 21/40 = 0.525, CI [0.375, 0.675], p = 0.000175. Recomputed one-sided binomial p for 21/40 vs 0.25 is 0.0001748540858045603. Holm rank 0 in both the 67-test family (threshold 0.05/67 = 0.000746) and the 172-test pool (threshold 0.05/172 = 0.000291). Both reject; it is the only reject in each family.

Cite: `s3-teks-g5-robustness.json`.

**Tie-break.** 13 items decided by depth alone (6 hits, 0.462). 27 decided by the lower-central tie-break among min-depth options (15 hits, 0.556). Random tie-breaks on the same 40: expected rate 0.367; 1000-draw mean 0.371, interval [0.250, 0.475]. Observed 0.525 sits above that interval. Lower-central alone on the same 40 (ignore closure) is 13/40 = 0.325, CI [0.200, 0.475], does not clear. 21 of 40 S3 picks differ from that all-option lower-central pick. Closure is not redundant with lower-central on these items.

**Depth sensitivity.** Depth 1 only: 17/30 = 0.567, CI [0.400, 0.733], still clears. Registered depth 2: 21/40 = 0.525, CI [0.375, 0.675]. Depth 2 without square/sqrt/pi/ab/2: 20/40 = 0.500, CI [0.350, 0.650], still clears.

**Clustered by STAAR year.** 2019: 8/13 = 0.615; 2021: 8/16 = 0.500; 2022: 5/11 = 0.455. Cluster bootstrap CI [0.455, 0.615], still above 0.25. Sign test 3/3 administrations above chance, p = 0.125 (three forms; not a Holm test).

**Closure density.** Mean 3.275 options in the closure per fired item. Unique depth-1 on 10/60 selected (0.167) and 10/40 fired; that unique option is the key on 6 of those 10. That is the cleanest version of the claim, and n = 10 is the bar edge.

**Other cells.** TEKS g3, g4, g6, g7, g8, alg1, Regents Algebra I, and geometry are in the cell table. Grade 5 is the only S3 cell that clears.

**Stems.** 9 one-operation word problems (key = a op b), 18 coincidences, 13 parse artifacts (axis ticks, leaked previous items, thousands commas, stem-and-leaf digits, footer grade numbers). Any parse artifact is a construct problem. Artifact-free: 16/27 = 0.593, CI [0.370, 0.778], still clears.

## S4 backsolve version 2

Coverage among solving-tagged items: 6/1186 = 0.0051 (version 1 was 1/1186). Parseable-equation share 42/1186; unique-satisfier share 6/42 = 0.143. Rest: 1/1059 fired, 18 parseable. Rate among solving-tagged fired: 5/6 = 0.833, CI [0.500, 1.000], n = 6, does not clear (n < 10). Imputed with abstentions as chance: 0.253. No cell has n fired >= 10; family tests 0; no cell clears the witness bar. TEKS alg1 3/3, TEKS solve-SE 2/2, Algebra I 1/2, TIMSS algebra 1/1, EQAO g9 0/52.

The 2020-jan-q3 inequality now parses (`7x-2 >= 58`) but two options satisfy, so unique-satisfier abstains. The item asks which number is not in the solution set.

Hand-check is all 7 fired items (census fired 7, not 30): parse correct 4, wrong 2, ambiguous 1. Key does not satisfy: 1 (`nyregents-algebra-i-2018-jun-q8`, a which-pair-is-not-a-solution item whose unique satisfier is a pair that does satisfy).

Cite: `s4-backsolve-v2.json`, `s4-v2-hand-check.json`.

## Not finished / limits

- S4 version 2 is still not a family row. OCR on Regents stems remains the binding constraint; unicode minus and implicit multiplication were not enough to get n >= 10 in any cell.
- S3 grade 5 still mixes one-op items with parse artifacts; the unique depth-1 subset is 6 keys in 10 items.
- S2 key-survival is not ~1 on every cell; the two hand-check failures are in the specified intersection rules.
- S5 p95 variants reshuffle branch order; because lower-central dominates, p95 tracks the observed rate and blocks EQAO g6.
- Do not modify `paper/`, `data/`, `exports/addendum/`, `exports/addendum-gpu/`, or top-level `exports/*.json`.
