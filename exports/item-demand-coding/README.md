# Item-level demand coding of the Algebra I masked-stem items

Two language-model coders (GLM 5.2 in `coder-glm/`, Kimi K3 in `coder-kimi/`) each coded the 358 New York Regents Algebra I masked-stem primary items for what answering the item requires, under one fixed rubric (recorded with its sha256 in each coder's README), blind to the key, to every model prediction, and to the pre-registered cluster split. Codes: `execution` (the key requires operating on the specific given quantities), `recognition_or_interpretation` (the key can be picked from the form, meaning, or property named in the wording), `mixed`, `unreadable`.

This file is written by `scripts/analyze_item_demand_coding.py` from `codes.jsonl`, the cluster classes in `exports/standards-split/`, and the saved per-item predictions in `exports/repaired-layer/` and `exports/addendum-gpu/`. Nothing is rescored. A pass does not require the tagged operation. Nothing here says students did not learn.

## Code counts

| code | GLM 5.2 | Kimi K3 | cluster split |
|---|---:|---:|---:|
| execution | 212 | 249 | 164 |
| recognition_or_interpretation | 116 | 94 | 151 |
| mixed | 28 | 15 | 43 |
| unreadable | 2 | 0 | 0 |

## Agreement (Cohen's kappa, unweighted)

Three classes (execution, recognition or interpretation, mixed); items either coder marked unreadable are dropped from that pair.

| pair | n | observed agreement | kappa |
|---|---:|---:|---:|
| GLM vs Kimi | 356 | 0.789 | 0.576 |
| GLM vs cluster split | 356 | 0.461 | 0.071 |
| Kimi vs cluster split | 358 | 0.564 | 0.230 |
| GLM vs Kimi, execution vs other | 356 | 0.803 | 0.575 |

### Confusion matrices

Rows GLM, columns Kimi.

| | execution | recognition_or_interpretation | mixed |
|---|---:|---:|---:|
| execution | 195 | 8 | 9 |
| recognition_or_interpretation | 32 | 82 | 2 |
| mixed | 21 | 3 | 4 |

Rows GLM, columns cluster.

| | execution | recognition_or_interpretation | mixed |
|---|---:|---:|---:|
| execution | 105 | 86 | 21 |
| recognition_or_interpretation | 41 | 56 | 19 |
| mixed | 17 | 8 | 3 |

Rows Kimi, columns cluster.

| | execution | recognition_or_interpretation | mixed |
|---|---:|---:|---:|
| execution | 140 | 86 | 23 |
| recognition_or_interpretation | 18 | 59 | 17 |
| mixed | 6 | 6 | 3 |

## Subsets

| subset | definition | n of 358 | cluster mix |
|---|---|---:|---|
| `execution_either` | at least one coder codes execution | 266 | execution 148, mixed 25, recognition_or_interpretation 93 |
| `execution_both` | both coders code execution | 195 | execution 97, mixed 19, recognition_or_interpretation 79 |
| `recognition_both` | both coders code recognition or interpretation | 82 | execution 16, mixed 15, recognition_or_interpretation 51 |
| `execution_both_and_cluster` | both coders and the cluster tag say execution | 97 | execution 97 |
| `recognition_both_and_cluster` | both coders and the cluster tag say recognition or interpretation | 51 | recognition_or_interpretation 51 |
| `cluster_execution` | cluster tag execution (pre-registered split) | 164 | execution 164 |
| `cluster_recognition` | cluster tag recognition or interpretation (pre-registered split) | 151 | recognition_or_interpretation 151 |

## Masked-stem rows on the coder subsets

Bar: n >= 10, lower 95% bootstrap CI strictly above chance 0.25 and strictly above the subset modal key-letter frequency. Bootstrap: random.Random.randrange, 1000 replicates, seed 21 + n, rows in primary-id order. Populations: repaired-verified (n=261 of the Algebra I withheld-quantity repaired items), repaired-all (n=343), text layer (n=358), and text layer print-faithful (n=184). Repaired rows use `exports/repaired-layer/scores-*-repaired.jsonl`; the isomorph column is the rank-preserving option-numeral arm on the repaired options (`scores-*-repaired-isomorph_rank_preserving.jsonl`; items whose perturbation failed are excluded and counted). Text-layer rows use the saved census predictions and have no isomorph column.

### Repaired, verified

| subset | model | n | pass | rate | 95% CI | modal (freq) | bar | isomorph n | isomorph rate | isomorph 95% CI | isomorph bar |
|---|---|---:|---:|---:|---|---|---|---:|---:|---|---|
| `execution_either` | Qwen2.5-7B-Instruct | 193 | 92 | 0.477 | [0.404, 0.549] | B (0.321) | yes | 192 | 0.458 | [0.385, 0.526] | yes |
| `execution_either` | Qwen2.5-14B-Instruct | 193 | 97 | 0.503 | [0.435, 0.575] | B (0.321) | yes | 192 | 0.401 | [0.328, 0.469] | yes |
| `execution_either` | Phi-4 | 193 | 81 | 0.420 | [0.352, 0.492] | B (0.321) | yes | 192 | 0.354 | [0.286, 0.422] | no |
| `execution_both` | Qwen2.5-7B-Instruct | 142 | 57 | 0.401 | [0.324, 0.486] | B (0.303) | yes | 141 | 0.418 | [0.340, 0.496] | yes |
| `execution_both` | Qwen2.5-14B-Instruct | 142 | 62 | 0.437 | [0.359, 0.521] | B (0.303) | yes | 141 | 0.333 | [0.262, 0.411] | no |
| `execution_both` | Phi-4 | 142 | 50 | 0.352 | [0.275, 0.430] | B (0.303) | no | 141 | 0.298 | [0.227, 0.376] | no |
| `recognition_both` | Qwen2.5-7B-Instruct | 61 | 45 | 0.738 | [0.623, 0.836] | A (0.295) | yes | 61 | 0.639 | [0.525, 0.754] | yes |
| `recognition_both` | Qwen2.5-14B-Instruct | 61 | 43 | 0.705 | [0.590, 0.820] | A (0.295) | yes | 61 | 0.689 | [0.574, 0.803] | yes |
| `recognition_both` | Phi-4 | 61 | 43 | 0.705 | [0.590, 0.820] | A (0.295) | yes | 61 | 0.607 | [0.492, 0.721] | yes |
| `execution_both_and_cluster` | Qwen2.5-7B-Instruct | 79 | 34 | 0.430 | [0.329, 0.544] | B (0.304) | yes | 78 | 0.423 | [0.308, 0.526] | no |
| `execution_both_and_cluster` | Qwen2.5-14B-Instruct | 79 | 30 | 0.380 | [0.278, 0.494] | B (0.304) | no | 78 | 0.333 | [0.231, 0.449] | no |
| `execution_both_and_cluster` | Phi-4 | 79 | 28 | 0.354 | [0.266, 0.456] | B (0.304) | no | 78 | 0.308 | [0.205, 0.410] | no |
| `recognition_both_and_cluster` | Qwen2.5-7B-Instruct | 35 | 23 | 0.657 | [0.486, 0.800] | D (0.343) | yes | 35 | 0.543 | [0.371, 0.714] | yes |
| `recognition_both_and_cluster` | Qwen2.5-14B-Instruct | 35 | 20 | 0.571 | [0.429, 0.714] | D (0.343) | yes | 35 | 0.571 | [0.400, 0.714] | yes |
| `recognition_both_and_cluster` | Phi-4 | 35 | 23 | 0.657 | [0.514, 0.800] | D (0.343) | yes | 35 | 0.514 | [0.343, 0.686] | no |
| `cluster_execution` | Qwen2.5-7B-Instruct | 130 | 71 | 0.546 | [0.454, 0.631] | B (0.323) | yes | 129 | 0.504 | [0.419, 0.597] | yes |
| `cluster_execution` | Qwen2.5-14B-Instruct | 130 | 67 | 0.515 | [0.423, 0.600] | B (0.323) | yes | 129 | 0.457 | [0.372, 0.535] | yes |
| `cluster_execution` | Phi-4 | 130 | 62 | 0.477 | [0.385, 0.562] | B (0.323) | yes | 129 | 0.419 | [0.333, 0.512] | yes |
| `cluster_recognition` | Qwen2.5-7B-Instruct | 105 | 54 | 0.514 | [0.429, 0.610] | B (0.267) | yes | 105 | 0.495 | [0.400, 0.590] | yes |
| `cluster_recognition` | Qwen2.5-14B-Instruct | 105 | 57 | 0.543 | [0.448, 0.629] | B (0.267) | yes | 105 | 0.419 | [0.324, 0.514] | yes |
| `cluster_recognition` | Phi-4 | 105 | 52 | 0.495 | [0.400, 0.590] | B (0.267) | yes | 105 | 0.390 | [0.305, 0.476] | yes |

### Repaired, all

| subset | model | n | pass | rate | 95% CI | modal (freq) | bar | isomorph n | isomorph rate | isomorph 95% CI | isomorph bar |
|---|---|---:|---:|---:|---|---|---|---:|---:|---|---|
| `execution_either` | Qwen2.5-7B-Instruct | 255 | 113 | 0.443 | [0.380, 0.506] | B (0.282) | yes | 254 | 0.425 | [0.366, 0.484] | yes |
| `execution_either` | Qwen2.5-14B-Instruct | 255 | 122 | 0.478 | [0.416, 0.537] | B (0.282) | yes | 254 | 0.374 | [0.315, 0.429] | yes |
| `execution_either` | Phi-4 | 255 | 108 | 0.424 | [0.365, 0.482] | B (0.282) | yes | 254 | 0.346 | [0.291, 0.406] | yes |
| `execution_both` | Qwen2.5-7B-Instruct | 188 | 72 | 0.383 | [0.314, 0.452] | C (0.287) | yes | 187 | 0.385 | [0.316, 0.455] | yes |
| `execution_both` | Qwen2.5-14B-Instruct | 188 | 82 | 0.436 | [0.367, 0.505] | C (0.287) | yes | 187 | 0.316 | [0.257, 0.380] | no |
| `execution_both` | Phi-4 | 188 | 69 | 0.367 | [0.298, 0.436] | C (0.287) | yes | 187 | 0.294 | [0.230, 0.358] | no |
| `recognition_both` | Qwen2.5-7B-Instruct | 78 | 53 | 0.679 | [0.577, 0.782] | A (0.269) | yes | 78 | 0.615 | [0.513, 0.718] | yes |
| `recognition_both` | Qwen2.5-14B-Instruct | 78 | 51 | 0.654 | [0.538, 0.756] | A (0.269) | yes | 78 | 0.641 | [0.526, 0.744] | yes |
| `recognition_both` | Phi-4 | 78 | 53 | 0.679 | [0.577, 0.769] | A (0.269) | yes | 78 | 0.590 | [0.487, 0.692] | yes |
| `execution_both_and_cluster` | Qwen2.5-7B-Instruct | 95 | 40 | 0.421 | [0.326, 0.516] | B (0.284) | yes | 94 | 0.404 | [0.319, 0.500] | yes |
| `execution_both_and_cluster` | Qwen2.5-14B-Instruct | 95 | 36 | 0.379 | [0.284, 0.474] | B (0.284) | no | 94 | 0.309 | [0.213, 0.404] | no |
| `execution_both_and_cluster` | Phi-4 | 95 | 32 | 0.337 | [0.242, 0.421] | B (0.284) | no | 94 | 0.309 | [0.213, 0.415] | no |
| `recognition_both_and_cluster` | Qwen2.5-7B-Instruct | 49 | 31 | 0.633 | [0.510, 0.776] | D (0.367) | yes | 49 | 0.571 | [0.429, 0.714] | yes |
| `recognition_both_and_cluster` | Qwen2.5-14B-Instruct | 49 | 28 | 0.571 | [0.429, 0.694] | D (0.367) | yes | 49 | 0.571 | [0.429, 0.714] | yes |
| `recognition_both_and_cluster` | Phi-4 | 49 | 32 | 0.653 | [0.510, 0.776] | D (0.367) | yes | 49 | 0.531 | [0.388, 0.673] | yes |
| `cluster_execution` | Qwen2.5-7B-Instruct | 159 | 80 | 0.503 | [0.428, 0.585] | B (0.302) | yes | 158 | 0.468 | [0.386, 0.544] | yes |
| `cluster_execution` | Qwen2.5-14B-Instruct | 159 | 76 | 0.478 | [0.403, 0.547] | B (0.302) | yes | 158 | 0.411 | [0.335, 0.487] | yes |
| `cluster_execution` | Phi-4 | 159 | 72 | 0.453 | [0.371, 0.528] | B (0.302) | yes | 158 | 0.405 | [0.329, 0.481] | yes |
| `cluster_recognition` | Qwen2.5-7B-Instruct | 148 | 73 | 0.493 | [0.419, 0.574] | C (0.277) | yes | 148 | 0.480 | [0.405, 0.554] | yes |
| `cluster_recognition` | Qwen2.5-14B-Instruct | 148 | 79 | 0.534 | [0.453, 0.608] | C (0.277) | yes | 148 | 0.419 | [0.338, 0.500] | yes |
| `cluster_recognition` | Phi-4 | 148 | 75 | 0.507 | [0.426, 0.581] | C (0.277) | yes | 148 | 0.392 | [0.311, 0.473] | yes |

### Text layer, all

| subset | model | n | pass | rate | 95% CI | modal (freq) | bar |
|---|---|---:|---:|---:|---|---|---|
| `execution_either` | Qwen2.5-7B-Instruct | 266 | 87 | 0.327 | [0.263, 0.383] | B (0.289) | no |
| `execution_either` | Qwen2.5-14B-Instruct | 266 | 97 | 0.365 | [0.312, 0.425] | B (0.289) | yes |
| `execution_either` | Phi-4 | 266 | 102 | 0.383 | [0.323, 0.444] | B (0.289) | yes |
| `execution_both` | Qwen2.5-7B-Instruct | 195 | 54 | 0.277 | [0.215, 0.344] | B (0.277) | no |
| `execution_both` | Qwen2.5-14B-Instruct | 195 | 63 | 0.323 | [0.256, 0.390] | B (0.277) | no |
| `execution_both` | Phi-4 | 195 | 72 | 0.369 | [0.303, 0.436] | B (0.277) | yes |
| `recognition_both` | Qwen2.5-7B-Instruct | 82 | 46 | 0.561 | [0.463, 0.671] | A (0.268) | yes |
| `recognition_both` | Qwen2.5-14B-Instruct | 82 | 46 | 0.561 | [0.439, 0.671] | A (0.268) | yes |
| `recognition_both` | Phi-4 | 82 | 44 | 0.537 | [0.439, 0.659] | A (0.268) | yes |
| `execution_both_and_cluster` | Qwen2.5-7B-Instruct | 97 | 19 | 0.196 | [0.124, 0.278] | B (0.289) | no |
| `execution_both_and_cluster` | Qwen2.5-14B-Instruct | 97 | 33 | 0.340 | [0.247, 0.433] | B (0.289) | no |
| `execution_both_and_cluster` | Phi-4 | 97 | 33 | 0.340 | [0.258, 0.443] | B (0.289) | no |
| `recognition_both_and_cluster` | Qwen2.5-7B-Instruct | 51 | 27 | 0.529 | [0.392, 0.667] | D (0.353) | yes |
| `recognition_both_and_cluster` | Qwen2.5-14B-Instruct | 51 | 27 | 0.529 | [0.392, 0.667] | D (0.353) | yes |
| `recognition_both_and_cluster` | Phi-4 | 51 | 25 | 0.490 | [0.353, 0.627] | D (0.353) | no |
| `cluster_execution` | Qwen2.5-7B-Instruct | 164 | 48 | 0.293 | [0.220, 0.360] | B (0.299) | no |
| `cluster_execution` | Qwen2.5-14B-Instruct | 164 | 62 | 0.378 | [0.311, 0.457] | B (0.299) | yes |
| `cluster_execution` | Phi-4 | 164 | 60 | 0.366 | [0.293, 0.439] | B (0.299) | no |
| `cluster_recognition` | Qwen2.5-7B-Instruct | 151 | 66 | 0.437 | [0.358, 0.510] | C (0.272) | yes |
| `cluster_recognition` | Qwen2.5-14B-Instruct | 151 | 63 | 0.417 | [0.344, 0.490] | C (0.272) | yes |
| `cluster_recognition` | Phi-4 | 151 | 69 | 0.457 | [0.377, 0.536] | C (0.272) | yes |

### Text layer, print-faithful

| subset | model | n | pass | rate | 95% CI | modal (freq) | bar |
|---|---|---:|---:|---:|---|---|---|
| `execution_either` | Qwen2.5-7B-Instruct | 124 | 50 | 0.403 | [0.315, 0.492] | B (0.282) | yes |
| `execution_either` | Qwen2.5-14B-Instruct | 124 | 45 | 0.363 | [0.274, 0.444] | B (0.282) | no |
| `execution_either` | Phi-4 | 124 | 49 | 0.395 | [0.306, 0.484] | B (0.282) | yes |
| `execution_both` | Qwen2.5-7B-Instruct | 91 | 31 | 0.341 | [0.242, 0.440] | C (0.275) | no |
| `execution_both` | Qwen2.5-14B-Instruct | 91 | 28 | 0.308 | [0.209, 0.396] | C (0.275) | no |
| `execution_both` | Phi-4 | 91 | 33 | 0.363 | [0.264, 0.462] | C (0.275) | no |
| `recognition_both` | Qwen2.5-7B-Instruct | 54 | 32 | 0.593 | [0.463, 0.722] | A (0.278) | yes |
| `recognition_both` | Qwen2.5-14B-Instruct | 54 | 31 | 0.574 | [0.444, 0.704] | A (0.278) | yes |
| `recognition_both` | Phi-4 | 54 | 34 | 0.630 | [0.500, 0.759] | A (0.278) | yes |
| `execution_both_and_cluster` | Qwen2.5-7B-Instruct | 43 | 10 | 0.233 | [0.116, 0.372] | D (0.279) | no |
| `execution_both_and_cluster` | Qwen2.5-14B-Instruct | 43 | 12 | 0.279 | [0.163, 0.419] | D (0.279) | no |
| `execution_both_and_cluster` | Phi-4 | 43 | 14 | 0.326 | [0.186, 0.465] | D (0.279) | no |
| `recognition_both_and_cluster` | Qwen2.5-7B-Instruct | 34 | 18 | 0.529 | [0.353, 0.676] | D (0.382) | no |
| `recognition_both_and_cluster` | Qwen2.5-14B-Instruct | 34 | 17 | 0.500 | [0.353, 0.676] | D (0.382) | no |
| `recognition_both_and_cluster` | Phi-4 | 34 | 19 | 0.559 | [0.382, 0.706] | D (0.382) | no |
| `cluster_execution` | Qwen2.5-7B-Instruct | 75 | 27 | 0.360 | [0.253, 0.480] | B (0.293) | no |
| `cluster_execution` | Qwen2.5-14B-Instruct | 75 | 25 | 0.333 | [0.240, 0.440] | B (0.293) | no |
| `cluster_execution` | Phi-4 | 75 | 29 | 0.387 | [0.293, 0.507] | B (0.293) | no |
| `cluster_recognition` | Qwen2.5-7B-Instruct | 83 | 43 | 0.518 | [0.410, 0.614] | D (0.265) | yes |
| `cluster_recognition` | Qwen2.5-14B-Instruct | 83 | 37 | 0.446 | [0.349, 0.554] | D (0.265) | yes |
| `cluster_recognition` | Phi-4 | 83 | 42 | 0.506 | [0.398, 0.614] | D (0.265) | yes |

## Files

- `coder-glm/`, `coder-kimi/`: the two blind codings (`codes.jsonl`, `items-to-code.jsonl`, rubric, README).
- `agreement.json`: everything above with subset id lists.
- Script: `scripts/analyze_item_demand_coding.py`.
