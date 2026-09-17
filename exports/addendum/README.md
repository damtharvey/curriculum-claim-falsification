# Addendum experiments (2026-09-16)

Science-only. Frozen paper N is the 18:55Z exports. Nothing here edits `paper/` or regenerates `comparisons.json` / `rule-chance.json` / `method-controls.json` / `data/items.jsonl`.

Witness bar (unchanged): n >= 10, lower 95% CI above chance; searched or fitted rules also above random-program p95.

## E1. Dependence and stability of the two witnesses — done

Question: do NY Regents geometry and EQAO grade 6 middle-value rates survive clustering by administration, and was the pre-registered lower-central index a post-hoc pick?

Method: same `floor((k-1)/2)` rule as `runner/src/features.ts`. Item bootstrap matches `runner/src/stats.ts` (mulberry32, seed 11, 1000). Cluster bootstrap resamples administrations (year-session for Regents, year for EQAO), 2000 replicates, seed 20260916. Five numeric definitions scored on the same k>=3 items.

Cite: `exports/addendum/e1-witness-dependence.json` fields `cells[authority=nyregents claim=geometry].middleValueLowerCentral` and `cells[authority=eqao claim=g6].middleValueLowerCentral`.

### Geometry (claimed)

- Reproduced: n=279, 90/279=0.323, item CI [0.265, 0.380], chance 0.25.
- Cluster CI [0.265, 0.374]. Lower bound still exceeds 0.25. **Strengthens.**
- 27 administrations. Rate > chance in 19, < in 7, = in 1. Sign test p=0.014 (one-sided).
- 15 administrations have n>=10; only 2018-aug individually clears the item bar (11 items, 0.545, CI [0.273, 0.818]). Single forms are underpowered. The claim remains the pooled cell.
- Sensitivity (same 279 items): lower-central 0.323 [0.265, 0.380] clears; upper-central 0.330 [0.272, 0.387] also clears and is slightly higher; nearest-to-mean 0.312 [0.258, 0.366] clears; smallest 0.219 and largest 0.219 do not. Report the higher upper-central number. Extremes fail, so this is a central-tendency cue, not “any numeric pick.”

### EQAO grade 6 (claimed)

- Reproduced: n=40, 20/40=0.500, item CI [0.350, 0.650], chance 0.254.
- Cluster CI [0.417, 0.588]. **Strengthens** (tighter, still above chance). Only three years, so the cluster interval is coarse.
- All three years exceed chance by rate: 2023 10/17=0.588, 2024 5/12=0.417, 2025 5/11=0.455. Sign test p=0.125 (3/3; underpowered).
- Only 2023 individually clears the item bar (CI [0.353, 0.824]).
- Sensitivity: **only pre-registered lower-central clears**. Upper-central 0.250 [0.125, 0.400]; nearest-to-mean 0.375 [0.225, 0.525]; smallest 0.200; largest 0.200. The cue is the second-smallest value, not “a middle option.”

### Algebra II (not a witness; report only)

- n=372, 0.298, item CI [0.253, 0.344], cluster CI [0.255, 0.341]. Both still sit on the bar. **Leave unclaimed.**
- 17/25 administrations have rate > chance, sign p=0.017. Zero administrations with n>=10 individually clear the item bar.
- Only lower-central clears even the pooled bar. Upper-central 0.266 CI [0.223, 0.309] does not.

## E2. Literature-derived a priori cues — done

Missing mechanical Millman / Haladyna cues added (longest-option, stem-option-overlap, avoid-absolute, middle-value, position-c already existed):

- `most-qualified-hedged-option`
- `convergence-option` (text tokens and numeric digit/value elements)
- `grammatical-fit-option` (a/an stem)
- `mean-of-other-options`

Run only those four on frozen `data/items.jsonl`. Cite: `exports/addendum/apriori-cues-extended.json`.

- New family tests (n>=10 and chance>0): **22** (convergence 5, mean-of-other-options 17). Hedge and grammatical never uniquely applied at n>=10 on this math set.
- Combined family: **105 + 22 = 127**. Bonferroni cut 0.05/127 = 0.000394. Holm/Bonferroni on the new family: 0 rejects. Combined Holm should be recomputed on 127, not 105.
- One per-cell clear, not Holm: `mean-of-other-options` on NY Regents geometry, n=156, 0.327, CI [0.256, 0.404], p=0.019. Related to the existing middle-value witness; do not treat as an independent claimed row.
- TIMSS: no new cue clears. Convergence on reasoning n=16 rate 0.500 CI [0.250, 0.750] (lower bound equals chance). Mean-of-others on applying 0.071, knowing 0.353, reasoning 0.189, none clear.

**Geometry witness: unchanged** (related mean-of-others is a sibling, not a replacement). **EQAO: unchanged. TIMSS null: unchanged.**

Programs also live in `runner/src/programs/apriori_extended.ts` and `rules/apriori-extended.json`. Do not merge into the frozen 15-rule census.

## E3. Clean-option choices-only — done, exploratory

Filter, not a new LM round. Existing `composer-2.5-fast` predictions in `exports/choices-only/scored.jsonl` (2242 items, opaque ids, shuffled options, transcript tool_use audit) were reused on items whose option strings pass a mechanical contamination filter. No new subagent calls. Strip-and-rescore would be a different protocol and was not run.

Cite filter: `exports/addendum/choices-only-clean-filter.json` (`nKept`, `rules`, `byCorpus`).
Cite scores: `exports/addendum/choices-only-clean-score.json` (`overall`, `perCorpus`).

- Selected items 2245 → kept 1496 (66.6%), dropped 749. Main drop reasons: exam-footer 515, length>120 204, country/jurisdiction fragment 147, STAAR item codes 83.
- TIMSS 2011 selected: 81 → 17 kept (country-table suffixes). TIMSS 1995: 79 → 78.
- NY Regents: 1448 → 919. STAAR: 388 → 246. EQAO: 149 → 142.
- Clean subset already scored: 1493. Rate **0.359 [0.334, 0.384]** vs chance 0.25. Still above chance after dropping dirty options.
- Per source (exploratory): NY Regents 918, 0.353 [0.322, 0.386]; STAAR 244, 0.377 [0.316, 0.439]; EQAO 142, 0.352 [0.275, 0.430]; TIMSS 1995 78, 0.423 [0.308, 0.538]; TIMSS 2011 17, 0.588 [0.353, 0.824] (too filtered to interpret as a TIMSS cognitive-domain result).

**Choices-only remains unclaimed** (channel is still not a stem-blind construct proof; this is a cleaner subset of the same dirty-channel run). The rate did not collapse to chance, so contamination is not the whole story.

## E4. Held-out searched / fitted — done

Temporal split: sort administrations by year then session; first half train, second half test. Cite: `exports/addendum/held-out-searched.json`.

Frozen searched programs (n=11 to 20) on late administrations:

| cell | late n | late rate | late CI | random p95 | clears |
|---|---:|---:|---|---:|---|
| TEKS g6 | 9 | 0.556 | [0.222, 0.889] | 0.395 | no |
| Algebra I overlap/min | 6 | 0.500 | [0.167, 0.833] | 0.301 | no |
| Algebra I longest/overlap/max | 7 | 0.286 | [0.000, 0.571] | 0.301 | no |
| Geometry overlap/min/distinctive | 10 | 0.500 | [0.200, 0.800] | 0.290 | no |

Fitted n-grams, train early / test late: state-pooled 0.257 n=1243 CI [0.233, 0.281]; geometry 0.259 n=224; algebra I 0.256 n=316; algebra II 0.219 n=228; TEKS g6 0.263 n=38. None beat chance.

One refit of the 1562-program search on STAAR 2019 (scored n=8) then tested on 2021–2022 reached 0.643 n=14 CI [0.357, 0.857] vs p95 0.395 (`search/w:longest+1,positionC+1,numRepeat-1`). Do not claim: train n below 10, one training form, search over 1562 programs.

**Searched n=11–20 rows stay unclaimed. Weakens any temptation to promote them.**

## E5. Clustered power — done

Cite: `exports/addendum/power-by-cell.json` field `min_detectable_rate_clustered`. DGP is Bernoulli(p) with observed administration sizes; inference is the E1 cluster bootstrap; 80% power, 120 trials, 400 boots.

17 cells with n_selected >= 10, all with at least two administrations.

| cell | n selected | clusters | clustered MDR | paper unclustered (n items) |
|---|---:|---:|---:|---|
| NY Algebra I | 598 | 33 | 0.303 | 0.284 |
| NY Algebra II | 442 | 25 | 0.308 | 0.290 |
| NY geometry | 408 | 27 | 0.309 | 0.294 |
| EQAO g6 | 53 | 3 | 0.415 | 0.396 |
| TIMSS knowing | 65 | 6 | 0.415 | 0.358 (n=81) |
| TIMSS applying | 54 | 6 | 0.426 | 0.353 (n=68) |
| TIMSS reasoning | 68 | 5 | 0.441 | 0.372 (n=86) |

Smallest clustered floor: 0.303 (Algebra I). TIMSS nulls need a higher bypass rate to be detectable at 80% power once cycle×grade clustering is respected. **TIMSS null slightly weaker as an informative non-finding, not reversed.** Geometry observed 0.323 is still above the clustered floor on the full geometry cell.

## Claim impact

- Geometry middle-value witness: **strengthens** (cluster CI still excludes 0.25; sign test p=0.014; extremes fail). Upper-central is 0.330, so say that number exists.
- EQAO g6 middle-value witness: **strengthens** on clustering; **specification-dependent** (only lower-central clears). Keep the pre-registered rule. Do not sell it as “middle option” in general.
- TIMSS null: **unchanged as a null**; clustered MDR is higher (0.415 / 0.426 / 0.441), so power language should use those floors if clustering is mentioned. New a priori cues do not clear TIMSS.
- Choices-only: **still unclaimed.** Clean subset 0.359 [0.334, 0.384] vs 0.25.

## Family-wise correction

Existing a priori family: 105 tests.
E2 new tests: 22.
**Total: 127.** Holm/Bonferroni at α=0.05 should use m=127 (cut 0.000394). Neither claimed middle-value row survives that cut (EQAO binomial p=0.00070, geometry p=0.00383). That fact was already in the paper for m=105; m=127 does not rescue them.

## Files

- `exports/addendum/e1-witness-dependence.json`
- `exports/addendum/apriori-cues-extended.json`
- `exports/addendum/choices-only-clean-filter.json`
- `exports/addendum/choices-only-clean-item-ids.json`
- `exports/addendum/choices-only-clean-score.json`
- `exports/addendum/held-out-searched.json`
- `exports/addendum/power-by-cell.json`
- `exports/addendum/README.md` (this file)
- `scripts/addendum_lib.py`
- `scripts/run_e1_witness_dependence.py`
- `scripts/run_e2_apriori_cues_extended.py`
- `scripts/run_e3_choices_only_clean.py`
- `scripts/run_e4_held_out_searched.py`
- `scripts/run_e5_clustered_power.py`
- `runner/src/programs/apriori_extended.ts`
- `rules/apriori-extended.json`

## Reviewer questions not closed

- License reuse of EQAO / Regents / TIMSS item text in a mentor PDF is Author A's call, not this addendum.
- Some Regents geometry ids parse as `2015-unk` / `2016-unk` / `2017-unk` (session missing in the id). Clustering still has 27 groups; merging unk into year would not move the cluster CI across 0.25.
- E3 did not launch new `composer-2.5-fast` subagents. A strip-and-rescore (rewrite dirty option strings, then score) is a different experiment.
- Clustered power is on selected-response n, not the paper’s nItems (TIMSS nItems include numeric constructed). Sibling unclustered power from `comparisons.json` uses nItems.
- No student data, no claim that students did not learn.
