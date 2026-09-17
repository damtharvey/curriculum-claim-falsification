# Number audit

Source of record for numbers in the paper after the ICML-style science pass. Claims in the language-model channel are now on the repaired-verified layer (section below); text-layer and print-faithful numbers in the sections above it are the audit trail. Independent floors: `exports/cell-power.json`. Clustered 80% floors: `exports/addendum/power-by-cell.json`. Catalog family: `exports/apriori-cell-table.json`. Print audit: `exports/print-audit/audit.json`.

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

## Repaired layer (`exports/repaired-layer/results.json`, README; preregistration sha 87ec5754... written before verification and scoring)

Claims in the language-model channel are made on the repaired-verified population. Repaired-all is a sensitivity. Text layer and print-faithful filter are audit trail (Appendix, `app:trail`).

- Verification: 431 verified / 175 unverified of 606 (Algebra I 263 / 95; Algebra II 168 / 80). Overlap with filter verdicts: verified = 246 faithful + 185 not_faithful; unverified = 53 faithful + 107 not_faithful + 15 unverified. Transcription 1 unusable 15; below one mask 17; key missing 0. Withheld-quantity population 574 (343 / 231); verified 261 / 167. Verified fraction 263/358 = 0.73, 168/248 = 0.68.
- Masked-stem, repaired-verified, Algebra I n=261 (modal B 0.287): Qwen 7B 141/261 = 0.540 [0.479, 0.598]; Qwen 14B 144/261 = 0.552 [0.494, 0.613]; Phi-4 129/261 = 0.494 [0.437, 0.559]. All clear.
- Algebra II n=167 (modal C 0.275): 75/167 = 0.449 [0.371, 0.527]; 72/167 = 0.431 [0.353, 0.503]; 69/167 = 0.413 [0.335, 0.491]. All clear.
- Repaired-all Algebra I n=343 (modal C 0.271): 0.504 / 0.519 / 0.493; Algebra II n=231 (modal C 0.286): 0.433 / 0.416 / 0.407. All clear.
- One-sided binomial p vs 0.25 on verified: Algebra I all below 1e-16 (max 1.9e-17, Phi-4); Algebra II max 2.8e-6 (Phi-4). Descriptive; the bar is the bootstrap.
- Cluster verb class, verified: Algebra I execution n=130: 0.546 / 0.515 / 0.477 vs modal B 0.323 (all clear); recognition n=105: 0.514 / 0.543 / 0.495 vs B 0.267 (all clear); mixed 26. Algebra II execution n=83: 0.494 / 0.422 / 0.458 vs D 0.301 (all clear); recognition n=57: 0.474 / 0.491 / 0.368 vs B 0.263 (Phi-4 fails, lower 0.246); mixed 27.
- Isomorph rank-preserving on repaired options (`isomorph-paired.json` for paired deltas): 4 perturb failures excluded (was 5 before one rerun recovered `nyregents-algebra-ii-2023-jun-q4`). Verified Algebra I n=260 (modal B 0.288): 0.500 [0.438, 0.562] / 0.465 [0.404, 0.527] / 0.419 [0.354, 0.477]; paired (n=223): -0.049 [-0.117, +0.022] / -0.103 [-0.166, -0.040] / -0.090 [-0.157, -0.013]. Verified Algebra II n=165 (modal C 0.273): 0.412 [0.339, 0.485] / 0.394 [0.321, 0.473] / 0.382 [0.315, 0.461]; paired (n=153): -0.039 [-0.118, +0.046] / -0.046 [-0.131, +0.046] / -0.039 [-0.124, +0.039]. All n=342 / 228: 0.471 / 0.430 / 0.409 and 0.395 / 0.377 / 0.351. All clear. No reproduction floor: original and perturbed letters from one run.
- Catalog lower-central on page-read options (transcription 1 only, no second reading): geometry fired 246 of 277 with transcription (279 original, 2 missing), 80/246 = 0.325, item CI [0.264, 0.382], cluster CI [0.264, 0.387], clears item bar. EQAO grade 6: 38 of 38 (40 original, 2 missing), 18/38 = 0.474, item CI [0.316, 0.632], cluster CI [0.273, 0.588], clears. Neither survives Holm over 105.
- Qwen 14B text-layer amendment: agreement 592/606 = 0.9769, floor 0.98, label below_floor, 14 disagreeing ids listed in the README. Arms reported in Appendix `tab:amend14b`, not a pass.
- Item 2023-jan-q22: repaired_unverified (transcription 2 drops the g(x)= prefix); repaired-layer letters Qwen 7B C, Qwen 14B C, Phi-4 D; key C.

## Item-level demand coders (`exports/item-demand-coding/agreement.json`, README)

- GLM 5.2: execution 212 / recognition 116 / mixed 28 / unreadable 2. Kimi K3: 249 / 94 / 15 / 0. Cluster split: 164 / 151 / 43. Rubric sha ae93b7c6... (GLM, three lines joined by newlines) and 434ed271... (Kimi, bulleted rubric.txt); same rubric text.
- Cohen's kappa (3 classes, unreadable dropped): GLM vs Kimi 0.576 (n=356, observed 0.789); GLM vs cluster 0.071 (0.461); Kimi vs cluster 0.230 (0.564). Execution-vs-other binary GLM vs Kimi 0.575.
- Confusion GLM rows x Kimi cols: exec 195 / 8 / 9; recog 32 / 82 / 2; mixed 21 / 3 / 4. Recognition-tagged (151) coded execution: 86 by GLM, 86 by Kimi, 79 by both. Execution-tagged (164) coded recognition: 41 GLM, 18 Kimi.
- Subsets (of 358; repaired-verified in parentheses): execution_both 195 (142); recognition_both 82 (61); execution_both_and_cluster 97 (79); recognition_both_and_cluster 51 (35); execution_either 266 (193).
- Repaired-verified rows: execution_both n=142, modal B 0.303: Qwen 7B 0.401 [0.324, 0.486] yes; Qwen 14B 0.437 [0.359, 0.521] yes; Phi-4 0.352 [0.275, 0.430] no (chance yes, modal no). execution_both_and_cluster n=79, modal B 0.304: 0.430 [0.329, 0.544] yes; 0.380 [0.278, 0.494] no; 0.354 [0.266, 0.456] no. recognition_both n=61, modal A 0.295: 0.738 [0.623, 0.836] / 0.705 [0.590, 0.820] / 0.705 [0.590, 0.820], all yes; isomorph 0.639 / 0.689 / 0.607, all yes. recognition_both_and_cluster n=35, modal D 0.343: 0.657 / 0.571 / 0.657, all yes.
- Repaired-all execution_both n=188, modal C 0.287: 0.383 [0.314, 0.452] / 0.436 [0.367, 0.505] / 0.367 [0.298, 0.436]; Phi-4 clears by 0.011. Not a margin to claim on; the execution statement is not made.
- Statement kept: on the matched items a pass does not require the given quantities. Not stated: that a pass on execution items omits the tagged operation.

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
