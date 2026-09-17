# Repaired text layer for Algebra I and Algebra II masked-stem items

Review-2 post-rebuttal W2 / N1: the print-faithful subset is selected (pre-2023 forms, word options over-represented). This addendum repairs the text layer from the page image for every Algebra I (358) and Algebra II (248) masked-stem primary item, then rescores the withheld-quantity population. W8 / N4: Qwen2.5-14B isomorph letters are re-run at batch size 1 and reported with a floor label.

Preregistration: `preregistration.md`, sha256 `87ec5754c1b696b25366547793365610a13084f1230247b898f564ea9f92caee`, frozen before verification transcription and before language-model scoring. Seed 20260916. Masking hash v1. CUDA letter-logprob argmax reused from `scripts/score_choices_only_local_lm.py`. Does not edit `paper/`.

A pass does not require the tagged operation. Nothing here says students did not learn.

## Verification counts

Transcription 1 is the stored print-fidelity VLM output (Qwen2-VL-7B-Instruct `eed13092…`). Transcription 2 is a second pass with different prompt wording and a 6 pt extra crop margin, same model. `repaired_verified` means the two transcriptions agree under the print-fidelity thresholds (stem F1 >= 0.8 with precision and recall >= 0.8, each option >= 0.9, option counts equal).

Overall: verified 431 / unverified 175 of 606. Transcription 1 usable 591.

| old verdict | repaired_verified | repaired_unverified |
|---|---:|---:|
| faithful | 246 | 53 |
| not_faithful | 185 | 107 |
| unverified | 0 | 15 |

Algebra I: verified 263 / unverified 95 of 358.

| old verdict | repaired_verified | repaired_unverified |
|---|---:|---:|
| faithful | 150 | 34 |
| not_faithful | 113 | 55 |
| unverified | 0 | 6 |

Algebra II: verified 168 / unverified 80 of 248.

| old verdict | repaired_verified | repaired_unverified |
|---|---:|---:|
| faithful | 96 | 19 |
| not_faithful | 72 | 52 |
| unverified | 0 | 9 |

Withheld-quantity scoring population (usable transcription 1, key present, masked_token_count >= 1): 574. Unusable transcription 1: 15. Key missing from repaired options: 0. Below one mask: 17.

## Per model: original text-layer vs repaired-all vs repaired-verified

Bar: n >= 10, lower bootstrap 95% CI strictly above chance 0.25 and strictly above the subset modal-letter frequency. Bootstrap: `random.Random.randrange`, 1000 replicates, seed `21 + n`. Original rates are the saved masked-stem predictions on the census text layer, not rerun.

| model | cell | subset | n | pass | rate | chance | 95% CI | modal (freq) | bar |
|---|---|---|---:|---:|---:|---:|---|---|---|
| Qwen2.5-7B-Instruct | Algebra I | original text-layer | 358 | 139 | 0.388 | 0.250 | [0.341, 0.439] | B (0.271) | yes |
| Qwen2.5-7B-Instruct | Algebra I | repaired all | 343 | 173 | 0.504 | 0.250 | [0.449, 0.560] | C (0.271) | yes |
| Qwen2.5-7B-Instruct | Algebra I | repaired verified | 261 | 141 | 0.540 | 0.250 | [0.479, 0.598] | B (0.287) | yes |
| Qwen2.5-7B-Instruct | Algebra II | original text-layer | 248 | 91 | 0.367 | 0.250 | [0.306, 0.423] | C (0.278) | yes |
| Qwen2.5-7B-Instruct | Algebra II | repaired all | 231 | 100 | 0.433 | 0.250 | [0.368, 0.498] | C (0.286) | yes |
| Qwen2.5-7B-Instruct | Algebra II | repaired verified | 167 | 75 | 0.449 | 0.250 | [0.371, 0.527] | C (0.275) | yes |
| Qwen2.5-14B-Instruct | Algebra I | original text-layer | 358 | 149 | 0.416 | 0.250 | [0.363, 0.469] | B (0.271) | yes |
| Qwen2.5-14B-Instruct | Algebra I | repaired all | 343 | 178 | 0.519 | 0.250 | [0.464, 0.574] | C (0.271) | yes |
| Qwen2.5-14B-Instruct | Algebra I | repaired verified | 261 | 144 | 0.552 | 0.250 | [0.494, 0.613] | B (0.287) | yes |
| Qwen2.5-14B-Instruct | Algebra II | original text-layer | 248 | 89 | 0.359 | 0.250 | [0.298, 0.415] | C (0.278) | yes |
| Qwen2.5-14B-Instruct | Algebra II | repaired all | 231 | 96 | 0.416 | 0.250 | [0.351, 0.481] | C (0.286) | yes |
| Qwen2.5-14B-Instruct | Algebra II | repaired verified | 167 | 72 | 0.431 | 0.250 | [0.353, 0.503] | C (0.275) | yes |
| Phi-4 | Algebra I | original text-layer | 358 | 151 | 0.422 | 0.250 | [0.374, 0.472] | B (0.271) | yes |
| Phi-4 | Algebra I | repaired all | 343 | 169 | 0.493 | 0.250 | [0.443, 0.545] | C (0.271) | yes |
| Phi-4 | Algebra I | repaired verified | 261 | 129 | 0.494 | 0.250 | [0.437, 0.559] | B (0.287) | yes |
| Phi-4 | Algebra II | original text-layer | 248 | 86 | 0.347 | 0.250 | [0.286, 0.407] | C (0.278) | yes |
| Phi-4 | Algebra II | repaired all | 231 | 94 | 0.407 | 0.250 | [0.342, 0.472] | C (0.286) | yes |
| Phi-4 | Algebra II | repaired verified | 167 | 69 | 0.413 | 0.250 | [0.335, 0.491] | C (0.275) | yes |

## Verb-class on the repaired layer

Join `exports/standards-split/item-standards.jsonl` with the locked cluster table. Execution versus recognition-or-interpretation. Mixed-class items are not a claimed row.

| model | cell | class | n | rate | 95% CI | modal (freq) | bar |
|---|---|---|---:|---:|---|---|---|
| Qwen2.5-7B-Instruct | Algebra I | execution / repaired all | 159 | 0.503 | [0.428, 0.585] | B (0.302) | yes |
| Qwen2.5-7B-Instruct | Algebra I | recognition / repaired all | 148 | 0.493 | [0.419, 0.574] | C (0.277) | yes |
| Qwen2.5-7B-Instruct | Algebra I | execution / verified | 130 | 0.546 | [0.454, 0.631] | B (0.323) | yes |
| Qwen2.5-7B-Instruct | Algebra I | recognition / verified | 105 | 0.514 | [0.429, 0.610] | B (0.267) | yes |
| Qwen2.5-7B-Instruct | Algebra II | execution / repaired all | 108 | 0.444 | [0.352, 0.537] | C (0.306) | yes |
| Qwen2.5-7B-Instruct | Algebra II | recognition / repaired all | 88 | 0.466 | [0.364, 0.568] | B (0.307) | yes |
| Qwen2.5-7B-Instruct | Algebra II | execution / verified | 83 | 0.494 | [0.386, 0.602] | D (0.301) | yes |
| Qwen2.5-7B-Instruct | Algebra II | recognition / verified | 57 | 0.474 | [0.351, 0.614] | B (0.263) | yes |
| Qwen2.5-14B-Instruct | Algebra I | execution / repaired all | 159 | 0.478 | [0.403, 0.547] | B (0.302) | yes |
| Qwen2.5-14B-Instruct | Algebra I | recognition / repaired all | 148 | 0.534 | [0.453, 0.608] | C (0.277) | yes |
| Qwen2.5-14B-Instruct | Algebra I | execution / verified | 130 | 0.515 | [0.423, 0.600] | B (0.323) | yes |
| Qwen2.5-14B-Instruct | Algebra I | recognition / verified | 105 | 0.543 | [0.448, 0.629] | B (0.267) | yes |
| Qwen2.5-14B-Instruct | Algebra II | execution / repaired all | 108 | 0.426 | [0.333, 0.519] | C (0.306) | yes |
| Qwen2.5-14B-Instruct | Algebra II | recognition / repaired all | 88 | 0.432 | [0.341, 0.534] | B (0.307) | yes |
| Qwen2.5-14B-Instruct | Algebra II | execution / verified | 83 | 0.422 | [0.313, 0.530] | D (0.301) | yes |
| Qwen2.5-14B-Instruct | Algebra II | recognition / verified | 57 | 0.491 | [0.368, 0.614] | B (0.263) | yes |
| Phi-4 | Algebra I | execution / repaired all | 159 | 0.453 | [0.371, 0.528] | B (0.302) | yes |
| Phi-4 | Algebra I | recognition / repaired all | 148 | 0.507 | [0.426, 0.581] | C (0.277) | yes |
| Phi-4 | Algebra I | execution / verified | 130 | 0.477 | [0.385, 0.562] | B (0.323) | yes |
| Phi-4 | Algebra I | recognition / verified | 105 | 0.495 | [0.400, 0.590] | B (0.267) | yes |
| Phi-4 | Algebra II | execution / repaired all | 108 | 0.444 | [0.352, 0.546] | C (0.306) | yes |
| Phi-4 | Algebra II | recognition / repaired all | 88 | 0.386 | [0.284, 0.489] | B (0.307) | no |
| Phi-4 | Algebra II | execution / verified | 83 | 0.458 | [0.349, 0.566] | D (0.301) | yes |
| Phi-4 | Algebra II | recognition / verified | 57 | 0.368 | [0.246, 0.491] | B (0.263) | no |

## Rank-preserving isomorph on repaired options

Same numeral substitution as `scripts/perturb_option_numerals.py`, applied to transcription-1 options. Rank-preserving arm only. Items whose perturbation raised or timed out (`perturbFailed`, n=5) are excluded from this table; items with no numeral stay in.

| model | cell | subset | n | rate | 95% CI | modal (freq) | bar |
|---|---|---|---:|---:|---|---|---|
| Qwen2.5-7B-Instruct | Algebra I | rank-preserving / repaired all | 342 | 0.471 | [0.418, 0.523] | C (0.272) | yes |
| Qwen2.5-7B-Instruct | Algebra I | rank-preserving / verified | 260 | 0.500 | [0.438, 0.562] | B (0.288) | yes |
| Qwen2.5-7B-Instruct | Algebra II | rank-preserving / repaired all | 227 | 0.392 | [0.330, 0.454] | C (0.282) | yes |
| Qwen2.5-7B-Instruct | Algebra II | rank-preserving / verified | 165 | 0.412 | [0.339, 0.485] | C (0.273) | yes |
| Qwen2.5-14B-Instruct | Algebra I | rank-preserving / repaired all | 342 | 0.430 | [0.377, 0.482] | C (0.272) | yes |
| Qwen2.5-14B-Instruct | Algebra I | rank-preserving / verified | 260 | 0.465 | [0.404, 0.527] | B (0.288) | yes |
| Qwen2.5-14B-Instruct | Algebra II | rank-preserving / repaired all | 227 | 0.374 | [0.308, 0.436] | C (0.282) | yes |
| Qwen2.5-14B-Instruct | Algebra II | rank-preserving / verified | 165 | 0.394 | [0.321, 0.473] | C (0.273) | yes |
| Phi-4 | Algebra I | rank-preserving / repaired all | 342 | 0.409 | [0.357, 0.459] | C (0.272) | yes |
| Phi-4 | Algebra I | rank-preserving / verified | 260 | 0.419 | [0.354, 0.477] | B (0.288) | yes |
| Phi-4 | Algebra II | rank-preserving / repaired all | 227 | 0.352 | [0.291, 0.414] | C (0.282) | yes |
| Phi-4 | Algebra II | rank-preserving / verified | 165 | 0.382 | [0.315, 0.461] | C (0.273) | yes |

## Catalog lower-central on repaired options

No new transcription. Geometry and EQAO grade 6 fired sets use stored print-fidelity transcription 1 when it exists.

- **NY Regents geometry lower-central**: original fired n=279, missing transcription 1 n=2, rule still fires n=246, pass 80/246 = 0.325, item CI [0.264, 0.382], chance 0.250, item bar yes.
- **EQAO grade 6 lower-central**: original fired n=40, missing transcription 1 n=2, rule still fires n=38, pass 18/38 = 0.474, item CI [0.316, 0.632], chance 0.250, item bar yes.

## 14B isomorph amendment

Rerun of Qwen2.5-14B original masked-stem letters on the census text layer, batch size 1, seed 20260916, then both option-numeral arms. Floor remains 0.98.

Label: **below_floor**. Letter agreement with `exports/addendum-gpu/masked-stem-14b-items.jsonl`: 592/606 = 0.9769 (floor 0.98).
Disagreeing ids (14):
- `nyregents-algebra-i-2020-jan-q12`: rerun B vs saved D
- `nyregents-algebra-i-2019-jan-q21`: rerun C vs saved A
- `nyregents-algebra-i-2026-jun-q6`: rerun A vs saved C
- `nyregents-algebra-i-2025-aug-q6`: rerun A vs saved C
- `nyregents-algebra-i-2015-jan-q8`: rerun A vs saved B
- `nyregents-algebra-i-unknown-unk-q6`: rerun C vs saved A
- `nyregents-algebra-i-2016-jan-q11`: rerun A vs saved B
- `nyregents-algebra-ii-2023-jan-q5`: rerun D vs saved B
- `nyregents-algebra-ii-2023-jan-q19`: rerun B vs saved C
- `nyregents-algebra-ii-2018-jan-q18`: rerun A vs saved B
- `nyregents-algebra-ii-2024-jun-q1`: rerun B vs saved D
- `nyregents-algebra-ii-2024-jan-q8`: rerun B vs saved D
- `nyregents-algebra-ii-2016-jun-q18`: rerun D vs saved A
- `nyregents-algebra-ii-2020-jan-q4`: rerun C vs saved B
This is not a pass of the isomorph control. Rank-preserving and scrambled arms are reported below so a reader can see them.

| subset | n | original | rank-preserving | scrambled | paired Δ preserving | preserving bar |
|---|---:|---|---|---|---|---|
| Algebra I all | 358 | 0.408 [0.355, 0.458] | 0.360 [0.313, 0.413] | 0.316 [0.271, 0.366] | -0.057 [-0.114, 0.000] | yes |
| Algebra I faithful | 184 | 0.418 [0.348, 0.489] | 0.380 [0.315, 0.457] | 0.370 [0.304, 0.446] | -0.051 [-0.132, 0.029] | yes |
| Algebra I faithful and recognition | 83 | 0.446 [0.337, 0.554] | 0.386 [0.289, 0.494] | 0.410 [0.301, 0.518] | -0.089 [-0.214, 0.054] | yes |
| Algebra I faithful and execution | 75 | 0.307 [0.213, 0.413] | 0.333 [0.227, 0.440] | 0.293 [0.187, 0.400] | +0.030 [-0.076, 0.136] | no |
| Algebra II all | 248 | 0.363 [0.302, 0.423] | 0.323 [0.262, 0.379] | 0.294 [0.238, 0.351] | -0.044 [-0.119, 0.026] | no |
| Algebra II faithful | 115 | 0.374 [0.287, 0.452] | 0.339 [0.252, 0.435] | 0.278 [0.200, 0.365] | -0.038 [-0.160, 0.085] | no |

## Files

- `preregistration.md`, `preregistration.sha256`
- `verification-items.jsonl`, `repaired-items.jsonl`, `repaired-masked-items.jsonl`
- `perturbed-items-isomorph_rank_preserving.jsonl`
- `scores-{7b,14b,phi4}-repaired.jsonl`, `scores-{7b,14b,phi4}-repaired-isomorph_rank_preserving.jsonl`
- `scores-14b-amendment-{original,isomorph_rank_preserving,isomorph_rank_scrambled}.jsonl`
- `results.json`

Script: `scripts/run_repaired_layer.py`.
