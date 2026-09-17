### Verb-class counts per cell (items; pre-registered classes)

| cell | all | faithful | execution | execution and faithful | execution_strict | execution_strict and faithful | recognition_or_interpretation | recognition and faithful | mixed | mixed and faithful |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Algebra I | 358 | 184 | 164 | 75 | 133 | 66 | 151 | 83 | 43 | 26 |
| Algebra II | 248 | 115 | 120 | 56 | 86 | 41 | 93 | 38 | 35 | 21 |

### Masked-stem rows by verb class (saved per-item predictions, seed 20260916)

Bar: n >= 10, lower 95% CI above chance (mean 1/k) and above the modal key-letter frequency of that subset.

| model | cell | subset | n | pass | rate | chance | 95% CI | modal letter (freq, this subset) | lower CI > chance | lower CI > modal | bar cleared |
|---|---|---|---:|---:|---:|---:|---|---|---|---|---|
| Qwen2.5-7B-Instruct | Algebra I | all | 358 | 139 | 0.388 | 0.250 | [0.341, 0.439] | B (0.271) | yes | yes | yes |
| Qwen2.5-7B-Instruct | Algebra I | faithful | 184 | 86 | 0.467 | 0.250 | [0.391, 0.543] | B (0.255) | yes | yes | yes |
| Qwen2.5-7B-Instruct | Algebra I | execution | 164 | 48 | 0.293 | 0.250 | [0.220, 0.360] | B (0.299) | no | no | no |
| Qwen2.5-7B-Instruct | Algebra I | execution_and_faithful | 75 | 27 | 0.360 | 0.250 | [0.253, 0.480] | B (0.293) | yes | no | no |
| Qwen2.5-7B-Instruct | Algebra I | execution_strict | 133 | 37 | 0.278 | 0.250 | [0.203, 0.353] | B (0.323) | no | no | no |
| Qwen2.5-7B-Instruct | Algebra I | execution_strict_and_faithful | 66 | 23 | 0.348 | 0.250 | [0.242, 0.455] | B (0.333) | no | no | no |
| Qwen2.5-7B-Instruct | Algebra I | recognition_or_interpretation | 151 | 66 | 0.437 | 0.250 | [0.358, 0.510] | C (0.272) | yes | yes | yes |
| Qwen2.5-7B-Instruct | Algebra I | recognition_or_interpretation_and_faithful | 83 | 43 | 0.518 | 0.250 | [0.410, 0.614] | D (0.265) | yes | yes | yes |
| Qwen2.5-7B-Instruct | Algebra I | mixed | 43 | 25 | 0.581 | 0.250 | [0.442, 0.721] | C (0.302) | yes | yes | yes |
| Qwen2.5-7B-Instruct | Algebra I | mixed_and_faithful | 26 | 16 | 0.615 | 0.250 | [0.423, 0.808] | C (0.346) | yes | yes | yes |
| Qwen2.5-7B-Instruct | Algebra II | all | 248 | 91 | 0.367 | 0.250 | [0.306, 0.423] | C (0.278) | yes | yes | yes |
| Qwen2.5-7B-Instruct | Algebra II | faithful | 115 | 40 | 0.348 | 0.250 | [0.261, 0.435] | B (0.296) | yes | no | no |
| Qwen2.5-7B-Instruct | Algebra II | execution | 120 | 47 | 0.392 | 0.250 | [0.308, 0.483] | C (0.300) | yes | yes | yes |
| Qwen2.5-7B-Instruct | Algebra II | execution_and_faithful | 56 | 22 | 0.393 | 0.250 | [0.250, 0.518] | C (0.286) | no | no | no |
| Qwen2.5-7B-Instruct | Algebra II | execution_strict | 86 | 34 | 0.395 | 0.250 | [0.291, 0.488] | C (0.291) | yes | no | no |
| Qwen2.5-7B-Instruct | Algebra II | execution_strict_and_faithful | 41 | 17 | 0.415 | 0.250 | [0.268, 0.561] | D (0.366) | yes | no | no |
| Qwen2.5-7B-Instruct | Algebra II | recognition_or_interpretation | 93 | 33 | 0.355 | 0.250 | [0.258, 0.441] | B (0.312) | yes | no | no |
| Qwen2.5-7B-Instruct | Algebra II | recognition_or_interpretation_and_faithful | 38 | 12 | 0.316 | 0.250 | [0.184, 0.474] | B (0.395) | no | no | no |
| Qwen2.5-7B-Instruct | Algebra II | mixed | 35 | 11 | 0.314 | 0.250 | [0.171, 0.486] | A (0.257) | no | no | no |
| Qwen2.5-7B-Instruct | Algebra II | mixed_and_faithful | 21 | 6 | 0.286 | 0.250 | [0.095, 0.476] | A (0.333) | no | no | no |
| Qwen2.5-14B-Instruct | Algebra I | all | 358 | 149 | 0.416 | 0.250 | [0.363, 0.469] | B (0.271) | yes | yes | yes |
| Qwen2.5-14B-Instruct | Algebra I | faithful | 184 | 79 | 0.429 | 0.250 | [0.359, 0.500] | B (0.255) | yes | yes | yes |
| Qwen2.5-14B-Instruct | Algebra I | execution | 164 | 62 | 0.378 | 0.250 | [0.311, 0.457] | B (0.299) | yes | yes | yes |
| Qwen2.5-14B-Instruct | Algebra I | execution_and_faithful | 75 | 25 | 0.333 | 0.250 | [0.240, 0.440] | B (0.293) | no | no | no |
| Qwen2.5-14B-Instruct | Algebra I | execution_strict | 133 | 49 | 0.368 | 0.250 | [0.286, 0.451] | B (0.323) | yes | no | no |
| Qwen2.5-14B-Instruct | Algebra I | execution_strict_and_faithful | 66 | 21 | 0.318 | 0.250 | [0.212, 0.424] | B (0.333) | no | no | no |
| Qwen2.5-14B-Instruct | Algebra I | recognition_or_interpretation | 151 | 63 | 0.417 | 0.250 | [0.344, 0.490] | C (0.272) | yes | yes | yes |
| Qwen2.5-14B-Instruct | Algebra I | recognition_or_interpretation_and_faithful | 83 | 37 | 0.446 | 0.250 | [0.349, 0.554] | D (0.265) | yes | yes | yes |
| Qwen2.5-14B-Instruct | Algebra I | mixed | 43 | 24 | 0.558 | 0.250 | [0.395, 0.698] | C (0.302) | yes | yes | yes |
| Qwen2.5-14B-Instruct | Algebra I | mixed_and_faithful | 26 | 17 | 0.654 | 0.250 | [0.462, 0.846] | C (0.346) | yes | yes | yes |
| Qwen2.5-14B-Instruct | Algebra II | all | 248 | 89 | 0.359 | 0.250 | [0.298, 0.415] | C (0.278) | yes | yes | yes |
| Qwen2.5-14B-Instruct | Algebra II | faithful | 115 | 44 | 0.383 | 0.250 | [0.287, 0.461] | B (0.296) | yes | no | no |
| Qwen2.5-14B-Instruct | Algebra II | execution | 120 | 48 | 0.400 | 0.250 | [0.317, 0.475] | C (0.300) | yes | yes | yes |
| Qwen2.5-14B-Instruct | Algebra II | execution_and_faithful | 56 | 23 | 0.411 | 0.250 | [0.286, 0.536] | C (0.286) | yes | no | no |
| Qwen2.5-14B-Instruct | Algebra II | execution_strict | 86 | 35 | 0.407 | 0.250 | [0.302, 0.512] | C (0.291) | yes | yes | yes |
| Qwen2.5-14B-Instruct | Algebra II | execution_strict_and_faithful | 41 | 16 | 0.390 | 0.250 | [0.244, 0.537] | D (0.366) | no | no | no |
| Qwen2.5-14B-Instruct | Algebra II | recognition_or_interpretation | 93 | 31 | 0.333 | 0.250 | [0.247, 0.419] | B (0.312) | no | no | no |
| Qwen2.5-14B-Instruct | Algebra II | recognition_or_interpretation_and_faithful | 38 | 13 | 0.342 | 0.250 | [0.211, 0.500] | B (0.395) | no | no | no |
| Qwen2.5-14B-Instruct | Algebra II | mixed | 35 | 10 | 0.286 | 0.250 | [0.143, 0.429] | A (0.257) | no | no | no |
| Qwen2.5-14B-Instruct | Algebra II | mixed_and_faithful | 21 | 8 | 0.381 | 0.250 | [0.190, 0.571] | A (0.333) | no | no | no |
| Phi-4 | Algebra I | all | 358 | 151 | 0.422 | 0.250 | [0.374, 0.472] | B (0.271) | yes | yes | yes |
| Phi-4 | Algebra I | faithful | 184 | 86 | 0.467 | 0.250 | [0.397, 0.538] | B (0.255) | yes | yes | yes |
| Phi-4 | Algebra I | execution | 164 | 60 | 0.366 | 0.250 | [0.293, 0.439] | B (0.299) | yes | no | no |
| Phi-4 | Algebra I | execution_and_faithful | 75 | 29 | 0.387 | 0.250 | [0.293, 0.507] | B (0.293) | yes | no | no |
| Phi-4 | Algebra I | execution_strict | 133 | 45 | 0.338 | 0.250 | [0.256, 0.421] | B (0.323) | yes | no | no |
| Phi-4 | Algebra I | execution_strict_and_faithful | 66 | 26 | 0.394 | 0.250 | [0.273, 0.500] | B (0.333) | yes | no | no |
| Phi-4 | Algebra I | recognition_or_interpretation | 151 | 69 | 0.457 | 0.250 | [0.377, 0.536] | C (0.272) | yes | yes | yes |
| Phi-4 | Algebra I | recognition_or_interpretation_and_faithful | 83 | 42 | 0.506 | 0.250 | [0.398, 0.614] | D (0.265) | yes | yes | yes |
| Phi-4 | Algebra I | mixed | 43 | 22 | 0.512 | 0.250 | [0.372, 0.674] | C (0.302) | yes | yes | yes |
| Phi-4 | Algebra I | mixed_and_faithful | 26 | 15 | 0.577 | 0.250 | [0.385, 0.769] | C (0.346) | yes | yes | yes |
| Phi-4 | Algebra II | all | 248 | 86 | 0.347 | 0.250 | [0.286, 0.407] | C (0.278) | yes | yes | yes |
| Phi-4 | Algebra II | faithful | 115 | 40 | 0.348 | 0.250 | [0.270, 0.435] | B (0.296) | yes | no | no |
| Phi-4 | Algebra II | execution | 120 | 44 | 0.367 | 0.250 | [0.283, 0.450] | C (0.300) | yes | no | no |
| Phi-4 | Algebra II | execution_and_faithful | 56 | 19 | 0.339 | 0.250 | [0.214, 0.464] | C (0.286) | no | no | no |
| Phi-4 | Algebra II | execution_strict | 86 | 32 | 0.372 | 0.250 | [0.267, 0.477] | C (0.291) | yes | no | no |
| Phi-4 | Algebra II | execution_strict_and_faithful | 41 | 15 | 0.366 | 0.250 | [0.220, 0.512] | D (0.366) | no | no | no |
| Phi-4 | Algebra II | recognition_or_interpretation | 93 | 31 | 0.333 | 0.250 | [0.237, 0.441] | B (0.312) | no | no | no |
| Phi-4 | Algebra II | recognition_or_interpretation_and_faithful | 38 | 12 | 0.316 | 0.250 | [0.184, 0.474] | B (0.395) | no | no | no |
| Phi-4 | Algebra II | mixed | 35 | 11 | 0.314 | 0.250 | [0.171, 0.486] | A (0.257) | no | no | no |
| Phi-4 | Algebra II | mixed_and_faithful | 21 | 9 | 0.429 | 0.250 | [0.238, 0.619] | A (0.333) | no | no | no |

### Per-cluster pass counts (descriptive; no per-cluster row is a claim)

#### Qwen2.5-7B-Instruct, Algebra I

| cluster | class | strict | n | pass | n faithful | pass faithful |
|---|---|---|---:|---:|---:|---:|
| A-APR.A | execution | yes | 25 | 6 | 9 | 3 |
| A-APR.B | recognition_or_interpretation | no | 9 | 2 | 5 | 2 |
| A-CED.A | execution | yes | 25 | 9 | 14 | 7 |
| A-REI.A | recognition_or_interpretation | no | 11 | 2 | 9 | 2 |
| A-REI.B | execution | yes | 36 | 6 | 18 | 4 |
| A-REI.C | execution | no | 11 | 2 | 1 | 0 |
| A-REI.D | execution | no | 20 | 9 | 8 | 4 |
| A-SSE.A | recognition_or_interpretation | no | 40 | 22 | 21 | 12 |
| A-SSE.B | execution | yes | 25 | 5 | 13 | 3 |
| F-BF.A | execution | yes | 10 | 4 | 5 | 2 |
| F-BF.B | execution | yes | 12 | 7 | 7 | 4 |
| F-IF.A | recognition_or_interpretation | no | 41 | 14 | 16 | 9 |
| F-IF.B | recognition_or_interpretation | no | 14 | 5 | 7 | 3 |
| F-IF.C | recognition_or_interpretation | no | 12 | 7 | 6 | 4 |
| F-LE.A | mixed | no | 18 | 11 | 14 | 10 |
| F-LE.B | recognition_or_interpretation | no | 13 | 9 | 10 | 7 |
| N-Q.A | mixed | no | 5 | 4 | 4 | 3 |
| N-RN.B | recognition_or_interpretation | no | 6 | 2 | 6 | 2 |
| S-ID.A | mixed | no | 13 | 7 | 5 | 2 |
| S-ID.B | mixed | no | 7 | 3 | 3 | 1 |
| S-ID.C | recognition_or_interpretation | no | 5 | 3 | 3 | 2 |

#### Qwen2.5-7B-Instruct, Algebra II

| cluster | class | strict | n | pass | n faithful | pass faithful |
|---|---|---|---:|---:|---:|---:|
| A-APR.B | recognition_or_interpretation | no | 12 | 2 | 6 | 1 |
| A-APR.C | execution | no | 5 | 2 | 0 | 0 |
| A-APR.D | execution | yes | 11 | 2 | 3 | 2 |
| A-CED.A | execution | yes | 7 | 2 | 6 | 2 |
| A-REI.A | recognition_or_interpretation | no | 5 | 3 | 0 | 0 |
| A-REI.B | execution | yes | 4 | 0 | 2 | 0 |
| A-REI.C | execution | no | 10 | 5 | 2 | 0 |
| A-REI.D | execution | no | 13 | 4 | 8 | 3 |
| A-SSE.A | recognition_or_interpretation | no | 17 | 8 | 5 | 1 |
| A-SSE.B | execution | yes | 16 | 7 | 11 | 5 |
| F-BF.A | execution | yes | 20 | 12 | 9 | 6 |
| F-BF.B | execution | yes | 11 | 5 | 4 | 1 |
| F-IF.A | recognition_or_interpretation | no | 4 | 0 | 1 | 0 |
| F-IF.B | recognition_or_interpretation | no | 20 | 6 | 11 | 3 |
| F-IF.C | recognition_or_interpretation | no | 10 | 4 | 3 | 1 |
| F-LE.A | mixed | no | 9 | 2 | 5 | 0 |
| F-LE.B | recognition_or_interpretation | no | 6 | 3 | 5 | 2 |
| F-TF.A | recognition_or_interpretation | no | 2 | 0 | 0 | 0 |
| F-TF.C | mixed | no | 3 | 1 | 1 | 0 |
| G-GPE.A | execution | yes | 8 | 2 | 2 | 0 |
| N-CN.A | execution | no | 6 | 2 | 5 | 2 |
| N-CN.C | execution | yes | 3 | 2 | 1 | 1 |
| N-Q.A | mixed | no | 1 | 1 | 1 | 1 |
| N-RN.A | mixed | no | 8 | 1 | 2 | 0 |
| S-CP.A | recognition_or_interpretation | no | 3 | 1 | 2 | 1 |
| S-CP.B | execution | yes | 6 | 2 | 3 | 0 |
| S-IC.A | recognition_or_interpretation | no | 4 | 2 | 2 | 1 |
| S-IC.B | recognition_or_interpretation | no | 10 | 4 | 3 | 2 |
| S-ID.A | mixed | no | 10 | 3 | 10 | 3 |
| S-ID.B | mixed | no | 4 | 3 | 2 | 2 |

#### Qwen2.5-14B-Instruct, Algebra I

| cluster | class | strict | n | pass | n faithful | pass faithful |
|---|---|---|---:|---:|---:|---:|
| A-APR.A | execution | yes | 25 | 8 | 9 | 3 |
| A-APR.B | recognition_or_interpretation | no | 9 | 3 | 5 | 1 |
| A-CED.A | execution | yes | 25 | 12 | 14 | 5 |
| A-REI.A | recognition_or_interpretation | no | 11 | 1 | 9 | 1 |
| A-REI.B | execution | yes | 36 | 9 | 18 | 4 |
| A-REI.C | execution | no | 11 | 6 | 1 | 0 |
| A-REI.D | execution | no | 20 | 7 | 8 | 4 |
| A-SSE.A | recognition_or_interpretation | no | 40 | 18 | 21 | 10 |
| A-SSE.B | execution | yes | 25 | 9 | 13 | 3 |
| F-BF.A | execution | yes | 10 | 4 | 5 | 3 |
| F-BF.B | execution | yes | 12 | 7 | 7 | 3 |
| F-IF.A | recognition_or_interpretation | no | 41 | 16 | 16 | 8 |
| F-IF.B | recognition_or_interpretation | no | 14 | 5 | 7 | 2 |
| F-IF.C | recognition_or_interpretation | no | 12 | 6 | 6 | 3 |
| F-LE.A | mixed | no | 18 | 12 | 14 | 11 |
| F-LE.B | recognition_or_interpretation | no | 13 | 8 | 10 | 7 |
| N-Q.A | mixed | no | 5 | 5 | 4 | 4 |
| N-RN.B | recognition_or_interpretation | no | 6 | 3 | 6 | 3 |
| S-ID.A | mixed | no | 13 | 6 | 5 | 2 |
| S-ID.B | mixed | no | 7 | 1 | 3 | 0 |
| S-ID.C | recognition_or_interpretation | no | 5 | 3 | 3 | 2 |

#### Qwen2.5-14B-Instruct, Algebra II

| cluster | class | strict | n | pass | n faithful | pass faithful |
|---|---|---|---:|---:|---:|---:|
| A-APR.B | recognition_or_interpretation | no | 12 | 0 | 6 | 0 |
| A-APR.C | execution | no | 5 | 2 | 0 | 0 |
| A-APR.D | execution | yes | 11 | 4 | 3 | 3 |
| A-CED.A | execution | yes | 7 | 2 | 6 | 2 |
| A-REI.A | recognition_or_interpretation | no | 5 | 2 | 0 | 0 |
| A-REI.B | execution | yes | 4 | 1 | 2 | 1 |
| A-REI.C | execution | no | 10 | 3 | 2 | 1 |
| A-REI.D | execution | no | 13 | 4 | 8 | 2 |
| A-SSE.A | recognition_or_interpretation | no | 17 | 7 | 5 | 1 |
| A-SSE.B | execution | yes | 16 | 6 | 11 | 4 |
| F-BF.A | execution | yes | 20 | 14 | 9 | 5 |
| F-BF.B | execution | yes | 11 | 3 | 4 | 0 |
| F-IF.A | recognition_or_interpretation | no | 4 | 1 | 1 | 0 |
| F-IF.B | recognition_or_interpretation | no | 20 | 3 | 11 | 2 |
| F-IF.C | recognition_or_interpretation | no | 10 | 3 | 3 | 2 |
| F-LE.A | mixed | no | 9 | 3 | 5 | 2 |
| F-LE.B | recognition_or_interpretation | no | 6 | 4 | 5 | 4 |
| F-TF.A | recognition_or_interpretation | no | 2 | 1 | 0 | 0 |
| F-TF.C | mixed | no | 3 | 1 | 1 | 1 |
| G-GPE.A | execution | yes | 8 | 3 | 2 | 0 |
| N-CN.A | execution | no | 6 | 4 | 5 | 4 |
| N-CN.C | execution | yes | 3 | 0 | 1 | 0 |
| N-Q.A | mixed | no | 1 | 0 | 1 | 0 |
| N-RN.A | mixed | no | 8 | 0 | 2 | 0 |
| S-CP.A | recognition_or_interpretation | no | 3 | 1 | 2 | 1 |
| S-CP.B | execution | yes | 6 | 2 | 3 | 1 |
| S-IC.A | recognition_or_interpretation | no | 4 | 2 | 2 | 1 |
| S-IC.B | recognition_or_interpretation | no | 10 | 7 | 3 | 2 |
| S-ID.A | mixed | no | 10 | 3 | 10 | 3 |
| S-ID.B | mixed | no | 4 | 3 | 2 | 2 |

#### Phi-4, Algebra I

| cluster | class | strict | n | pass | n faithful | pass faithful |
|---|---|---|---:|---:|---:|---:|
| A-APR.A | execution | yes | 25 | 6 | 9 | 2 |
| A-APR.B | recognition_or_interpretation | no | 9 | 6 | 5 | 3 |
| A-CED.A | execution | yes | 25 | 6 | 14 | 4 |
| A-REI.A | recognition_or_interpretation | no | 11 | 2 | 9 | 2 |
| A-REI.B | execution | yes | 36 | 13 | 18 | 8 |
| A-REI.C | execution | no | 11 | 5 | 1 | 0 |
| A-REI.D | execution | no | 20 | 10 | 8 | 3 |
| A-SSE.A | recognition_or_interpretation | no | 40 | 13 | 21 | 9 |
| A-SSE.B | execution | yes | 25 | 7 | 13 | 4 |
| F-BF.A | execution | yes | 10 | 6 | 5 | 4 |
| F-BF.B | execution | yes | 12 | 7 | 7 | 4 |
| F-IF.A | recognition_or_interpretation | no | 41 | 22 | 16 | 11 |
| F-IF.B | recognition_or_interpretation | no | 14 | 6 | 7 | 3 |
| F-IF.C | recognition_or_interpretation | no | 12 | 8 | 6 | 3 |
| F-LE.A | mixed | no | 18 | 10 | 14 | 9 |
| F-LE.B | recognition_or_interpretation | no | 13 | 7 | 10 | 7 |
| N-Q.A | mixed | no | 5 | 3 | 4 | 3 |
| N-RN.B | recognition_or_interpretation | no | 6 | 2 | 6 | 2 |
| S-ID.A | mixed | no | 13 | 7 | 5 | 3 |
| S-ID.B | mixed | no | 7 | 2 | 3 | 0 |
| S-ID.C | recognition_or_interpretation | no | 5 | 3 | 3 | 2 |

#### Phi-4, Algebra II

| cluster | class | strict | n | pass | n faithful | pass faithful |
|---|---|---|---:|---:|---:|---:|
| A-APR.B | recognition_or_interpretation | no | 12 | 1 | 6 | 0 |
| A-APR.C | execution | no | 5 | 1 | 0 | 0 |
| A-APR.D | execution | yes | 11 | 3 | 3 | 1 |
| A-CED.A | execution | yes | 7 | 1 | 6 | 1 |
| A-REI.A | recognition_or_interpretation | no | 5 | 1 | 0 | 0 |
| A-REI.B | execution | yes | 4 | 0 | 2 | 0 |
| A-REI.C | execution | no | 10 | 7 | 2 | 1 |
| A-REI.D | execution | no | 13 | 2 | 8 | 1 |
| A-SSE.A | recognition_or_interpretation | no | 17 | 6 | 5 | 0 |
| A-SSE.B | execution | yes | 16 | 7 | 11 | 5 |
| F-BF.A | execution | yes | 20 | 11 | 9 | 5 |
| F-BF.B | execution | yes | 11 | 7 | 4 | 2 |
| F-IF.A | recognition_or_interpretation | no | 4 | 0 | 1 | 0 |
| F-IF.B | recognition_or_interpretation | no | 20 | 8 | 11 | 2 |
| F-IF.C | recognition_or_interpretation | no | 10 | 2 | 3 | 1 |
| F-LE.A | mixed | no | 9 | 2 | 5 | 2 |
| F-LE.B | recognition_or_interpretation | no | 6 | 2 | 5 | 2 |
| F-TF.A | recognition_or_interpretation | no | 2 | 0 | 0 | 0 |
| F-TF.C | mixed | no | 3 | 1 | 1 | 0 |
| G-GPE.A | execution | yes | 8 | 1 | 2 | 0 |
| N-CN.A | execution | no | 6 | 2 | 5 | 2 |
| N-CN.C | execution | yes | 3 | 0 | 1 | 0 |
| N-Q.A | mixed | no | 1 | 1 | 1 | 1 |
| N-RN.A | mixed | no | 8 | 1 | 2 | 1 |
| S-CP.A | recognition_or_interpretation | no | 3 | 2 | 2 | 2 |
| S-CP.B | execution | yes | 6 | 2 | 3 | 1 |
| S-IC.A | recognition_or_interpretation | no | 4 | 2 | 2 | 2 |
| S-IC.B | recognition_or_interpretation | no | 10 | 7 | 3 | 3 |
| S-ID.A | mixed | no | 10 | 4 | 10 | 4 |
| S-ID.B | mixed | no | 4 | 2 | 2 | 1 |

