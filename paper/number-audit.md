# Number audit

Source of record for numbers in the paper after the ICML-style science pass. Independent floors: `exports/cell-power.json`. Clustered 80% floors: `exports/addendum/power-by-cell.json`. Catalog family: `exports/apriori-cell-table.json`. Print audit: `exports/print-audit/audit.json`.

## Census

- Items: 2405 keyed (2245 selected, 160 numeric).
- Local trials: 350535.
- Searched program space: 1847.

## Catalog family (105 tests, 0 Holm)

- Family: every (rule, cell) with n scored at least 10 and positive format chance. One PISA numeric unit-rate row with chance 0 excluded.
- Holm rejects: 0. Bonferroni rejects: 0.
- Per-cell existence, not family-wise: NY Regents geometry lower-central 90/279 = 0.323, item CI [0.265, 0.380], clustered CI [0.265, 0.374].
- Per-cell existence, index-specific: EQAO grade 6 lower-central 20/40 = 0.500, item CI [0.350, 0.650], clustered CI [0.417, 0.588] (k=3, descriptive). Upper-central on that cell is 0.250.
- Algebra II lower-central 0.298 n=372 sits on chance; not claimed.

## Strategy family (67 tests)

- Hash before scoring: a0eda4bd... recorded 2026-09-16 20:36:16 UTC.
- Discovery Holm reject: STAAR grade 5 arithmetic closure 21/40 = 0.525, CI [0.375, 0.675].
- Powered replication after option-leak repair: combined 21/64 = 0.328, CI [0.219, 0.438], covers chance.
- 172-test pool with the 105 catalog tests: same single Holm reject.
- Text-layer backsolving: no cell n fired >= 10 (6 unique fires / 1186 solving-tagged stems).
- Image-channel backsolving (Qwen2-VL-7B-Instruct rev eed13092..., hashed before scoring, not in the 67 Holm family). Original unique-satisfier Algebra I 14/17 = 0.824, CI [0.647, 1.000], coverage 17/598 = 0.028. Honest displayed-equation set: 14/15 = 0.933, n=15, CI [0.800, 1.000], chance 0.25, coverage 15/598 = 0.025. Clears per-cell bar. Dropped: 2024-jan-q2 invented x=2; 2018-jan-q10 parse_wrong. Kept miss: 2014-aug-q5 not-on-graph. Source: `exports/addendum-vlm/backsolve-extract-honest.json`.

## Language-model family (68 tests)

- Withheld-quantity Algebra I n=358: Qwen 7B 0.388, Qwen 14B 0.416, Phi-4 0.422; all clear chance 0.250 and modal B 0.271.
- Algebra II n=248: Qwen 7B 0.367, Qwen 14B 0.359, Phi-4 0.347; all clear chance 0.250 and modal C 0.278.
- Phi-4 geometry 67/166 = 0.404 meets the cell bar versus modal B 0.289; non-modal-key 0.229 n=118, CI [0.161, 0.305], at or below chance. Not claimed. Table row unlabeled.
- Qwen 14B Algebra I residual (none of four catalog cues): 0.442 n=163.
- Human masked-stem sheet: 15/40 = 0.375, CI [0.225, 0.525]. Uninformative null. Not a human witness.

## TIMSS floors

Do not use 0.400 / 0.407 / 0.421. Those mixed independent floors with a design-effect rescaling that does not match `power-by-cell.json`.

Knowing / applying / reasoning:

| Domain | Tagged n | Selected n | Independent floor | Clustered 80% floor |
|---|---:|---:|---:|---:|
| knowing | 81 | 65 | 0.358 | 0.415 |
| applying | 68 | 54 | 0.353 | 0.426 |
| reasoning | 86 | 68 | 0.372 | 0.441 |

Independent: `exports/cell-power.json` `minObservablePassRate3`. Clustered: `exports/addendum/power-by-cell.json` `min_detectable_rate_clustered` on selected-response items, administration resampling, 80% power, seed 77+n. Memorable claim: null at n about 50 to 80, not that a 0.40 bypass would have been seen.

## Print audit (n=20)

Seed 20260916. Ten geometry lower-central hits from the 90-hit pool. Ten Algebra I withheld-quantity Qwen 14B hits from the 149-hit pool. Local PDFs under `data/raw/`. No optical character recognition.

Hand labels vs printed page: match 8, ocr_glue 8, truncated 3, wrong_item 1, pdf_missing 0.

Wrong option set: `nyregents-algebra-i-2023-jun-q3` (printed y=2x lines; census inequalities).
