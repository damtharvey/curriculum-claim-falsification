# Second VLM family for the verification transcription

Review weakness 2: the repaired-layer verified set used two readings of one family (Qwen2-VL-7B-Instruct). This addendum transcribes the same 606 Algebra I and Algebra II crops with LLaVA-NeXT Vicuna 13B and marks an item `verified_cross_family` when that transcription agrees with Qwen transcription 1 under the print-fidelity thresholds.

Preregistration: `preregistration.md`, sha256 `bc891e7b5894216e662b1c78dae3dc627303509ae67aa17bab1d0e520a037ef0`, frozen before LLaVA scoring. Seed 20260916. No language-model re-scoring; rates join `exports/repaired-layer/scores-*.jsonl`. Does not edit `paper/`.

A pass does not require the tagged operation. Nothing here says students did not learn.

## Honesty

Rates that do not clear the channel bar on the cross-family verified set:

- Phi-4 Algebra II cross-family verified 0.368 n=57 bar no

## Verification counts

LLaVA-NeXT Vicuna 13B (`745cfbdb…`) versus Qwen2-VL transcription 1. `verified_cross_family` means the print-fidelity thresholds hold (stem F1 >= 0.8 with precision and recall >= 0.8, each option >= 0.9, option counts equal).

Overall: cross-family verified 160 / not 446 of 606. Qwen–Qwen repaired_verified 431. Both checks 153. 5 items exceeded LLaVA's 4096-token context (two-page crops under anyres) and are `not_verified_cross_family`.

| Qwen–Qwen | verified_cross_family | not_verified_cross_family |
|---|---:|---:|
| repaired_verified | 153 | 278 |
| repaired_unverified | 7 | 168 |

Algebra I: cross-family verified 102 / not 256 of 358. Both checks 97.

| Qwen–Qwen | verified_cross_family | not_verified_cross_family |
|---|---:|---:|
| repaired_verified | 97 | 166 |
| repaired_unverified | 5 | 90 |

Algebra II: cross-family verified 58 / not 190 of 248. Both checks 56.

| Qwen–Qwen | verified_cross_family | not_verified_cross_family |
|---|---:|---:|
| repaired_verified | 56 | 112 |
| repaired_unverified | 2 | 78 |

## Per model: cross-family verified and both checks

Bar: n >= 10, lower bootstrap 95% CI strictly above chance 0.25 and strictly above the subset modal-letter frequency. Bootstrap: `random.Random.randrange`, 1000 replicates, seed `21 + n`. Predictions are the repaired-layer scores on transcription 1.

| model | cell | subset | n | pass | rate | chance | 95% CI | modal (freq) | bar |
|---|---|---|---:|---:|---:|---:|---|---|---|
| Qwen2.5-7B-Instruct | Algebra I | cross-family verified | 101 | 57 | 0.564 | 0.250 | [0.455, 0.653] | C (0.297) | yes |
| Qwen2.5-7B-Instruct | Algebra I | both checks | 96 | 54 | 0.562 | 0.250 | [0.458, 0.667] | B (0.281) | yes |
| Qwen2.5-7B-Instruct | Algebra II | cross-family verified | 57 | 26 | 0.456 | 0.250 | [0.316, 0.579] | C (0.281) | yes |
| Qwen2.5-7B-Instruct | Algebra II | both checks | 55 | 26 | 0.473 | 0.250 | [0.327, 0.600] | C (0.273) | yes |
| Qwen2.5-14B-Instruct | Algebra I | cross-family verified | 101 | 57 | 0.564 | 0.250 | [0.465, 0.663] | C (0.297) | yes |
| Qwen2.5-14B-Instruct | Algebra I | both checks | 96 | 54 | 0.562 | 0.250 | [0.458, 0.667] | B (0.281) | yes |
| Qwen2.5-14B-Instruct | Algebra II | cross-family verified | 57 | 25 | 0.439 | 0.250 | [0.316, 0.561] | C (0.281) | yes |
| Qwen2.5-14B-Instruct | Algebra II | both checks | 55 | 24 | 0.436 | 0.250 | [0.309, 0.564] | C (0.273) | yes |
| Phi-4 | Algebra I | cross-family verified | 101 | 54 | 0.535 | 0.250 | [0.426, 0.634] | C (0.297) | yes |
| Phi-4 | Algebra I | both checks | 96 | 52 | 0.542 | 0.250 | [0.438, 0.646] | B (0.281) | yes |
| Phi-4 | Algebra II | cross-family verified | 57 | 21 | 0.368 | 0.250 | [0.246, 0.491] | C (0.281) | no |
| Phi-4 | Algebra II | both checks | 55 | 21 | 0.382 | 0.250 | [0.236, 0.509] | C (0.273) | no |

## Verb-class on the cross-family verified set

Join `exports/standards-split/item-standards.jsonl` with the locked cluster table.

| model | cell | class | n | pass | rate | chance | 95% CI | modal (freq) | bar |
|---|---|---|---:|---:|---:|---:|---|---|---|
| Qwen2.5-7B-Instruct | Algebra I | execution | 44 | 23 | 0.523 | 0.250 | [0.386, 0.682] | C (0.341) | yes |
| Qwen2.5-7B-Instruct | Algebra I | recognition | 43 | 23 | 0.535 | 0.250 | [0.395, 0.674] | B (0.349) | yes |
| Qwen2.5-7B-Instruct | Algebra II | execution | 18 | 6 | 0.333 | 0.250 | [0.111, 0.556] | C (0.333) | no |
| Qwen2.5-7B-Instruct | Algebra II | recognition | 28 | 16 | 0.571 | 0.250 | [0.393, 0.750] | B (0.286) | yes |
| Qwen2.5-14B-Instruct | Algebra I | execution | 44 | 21 | 0.477 | 0.250 | [0.341, 0.614] | C (0.341) | no |
| Qwen2.5-14B-Instruct | Algebra I | recognition | 43 | 23 | 0.535 | 0.250 | [0.395, 0.674] | B (0.349) | yes |
| Qwen2.5-14B-Instruct | Algebra II | execution | 18 | 5 | 0.278 | 0.250 | [0.111, 0.500] | C (0.333) | no |
| Qwen2.5-14B-Instruct | Algebra II | recognition | 28 | 17 | 0.607 | 0.250 | [0.429, 0.786] | B (0.286) | yes |
| Phi-4 | Algebra I | execution | 44 | 20 | 0.455 | 0.250 | [0.318, 0.614] | C (0.341) | no |
| Phi-4 | Algebra I | recognition | 43 | 24 | 0.558 | 0.250 | [0.419, 0.698] | B (0.349) | yes |
| Phi-4 | Algebra II | execution | 18 | 7 | 0.389 | 0.250 | [0.167, 0.611] | C (0.333) | no |
| Phi-4 | Algebra II | recognition | 28 | 10 | 0.357 | 0.250 | [0.179, 0.536] | B (0.286) | no |

## Rank-preserving isomorph on the cross-family verified set

Join repaired-layer rank-preserving scores. Items whose perturbation failed are excluded.

| model | cell | n | pass | rate | chance | 95% CI | modal (freq) | bar |
|---|---|---:|---:|---:|---:|---|---|---|
| Qwen2.5-7B-Instruct | Algebra I | 101 | 50 | 0.495 | 0.250 | [0.406, 0.594] | C (0.297) | yes |
| Qwen2.5-7B-Instruct | Algebra II | 57 | 26 | 0.456 | 0.250 | [0.333, 0.579] | C (0.281) | yes |
| Qwen2.5-14B-Instruct | Algebra I | 101 | 45 | 0.446 | 0.250 | [0.347, 0.545] | C (0.297) | yes |
| Qwen2.5-14B-Instruct | Algebra II | 57 | 31 | 0.544 | 0.250 | [0.404, 0.667] | C (0.281) | yes |
| Phi-4 | Algebra I | 101 | 43 | 0.426 | 0.250 | [0.327, 0.515] | C (0.297) | yes |
| Phi-4 | Algebra II | 57 | 25 | 0.439 | 0.250 | [0.316, 0.561] | C (0.281) | yes |

## Files

- `preregistration.md`, `preregistration.sha256`
- `transcriptions-llava.jsonl`, `verdicts.jsonl`
- `results.json`

Script: `scripts/run_second_family_transcription.py`.
