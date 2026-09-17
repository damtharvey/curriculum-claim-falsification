### Faithful fraction per cell

| cell | n | faithful (pre-registered) | faithful, strict (post hoc) | not faithful | unverified | faithful fraction | categories (not faithful and unverified) |
|---|---:|---:|---:|---:|---:|---:|---|
| `nyregents::algebra-i::masked-stem-primary` | 358 | 184 | 149 | 168 | 6 | 0.523 | ocr_glue 54, option_mismatch 1, truncated 10, vlm_no_options 1, vlm_unparseable 5, wrong_item 103 |
| `nyregents::algebra-ii::masked-stem-primary` | 248 | 115 | 88 | 124 | 9 | 0.481 | ocr_glue 50, option_mismatch 1, truncated 4, vlm_no_options 1, vlm_unparseable 8, wrong_item 69 |
| `nyregents::geometry::lower-central-fired` | 279 | 99 | 80 | 178 | 2 | 0.357 | ocr_glue 116, truncated 12, vlm_unparseable 2, wrong_item 50 |
| `eqao::g6::lower-central-fired` | 40 | 14 | 10 | 24 | 2 | 0.368 | ocr_glue 17, truncated 1, vlm_unparseable 2, wrong_item 6 |
| `nyregents::geometry::masked-stem-primary` | 166 | 109 | 93 | 57 | 0 | 0.657 | ocr_glue 24, truncated 12, wrong_item 21 |

### Catalog rows (lower-central, `middle_value_option`)

| cell | subset | n | pass | rate | chance | item 95% CI | cluster 95% CI | item bar (n >= 10, lower CI > chance) |
|---|---|---:|---:|---:|---:|---|---|---|
| NY Regents geometry | original | 279 | 90 | 0.323 | 0.250 | [0.269, 0.380] | [0.265, 0.374] | yes |
| NY Regents geometry | faithful | 99 | 32 | 0.323 | 0.250 | [0.232, 0.414] | [0.227, 0.414] | no |
| NY Regents geometry | faithful_after_relocation | 100 | 32 | 0.320 | 0.250 | [0.230, 0.410] | [0.225, 0.409] | no |
| NY Regents geometry | faithful_strict | 80 | 26 | 0.325 | 0.250 | [0.225, 0.425] | [0.210, 0.430] | no |
| NY Regents geometry | faithful_digit_suspect | 19 | 6 | 0.316 | 0.250 | [0.105, 0.526] | [0.100, 0.588] | no |
| NY Regents geometry | not_faithful | 178 | 58 | 0.326 | 0.250 | [0.253, 0.399] | [0.251, 0.401] | yes |
| NY Regents geometry | numeric_faithful | 173 | 56 | 0.324 | 0.250 | [0.254, 0.393] | [0.239, 0.404] | yes |
| NY Regents geometry | numeric_not_faithful | 104 | 34 | 0.327 | 0.250 | [0.231, 0.423] | [0.257, 0.394] | no |
| NY Regents geometry | unverified | 2 | 0 | 0.000 | 0.250 | [0.000, 0.000] | [0.000, 0.000] | no |
| EQAO grade 6 | original | 40 | 20 | 0.500 | 0.254 | [0.350, 0.650] | [0.417, 0.588] | yes |
| EQAO grade 6 | faithful | 14 | 8 | 0.571 | 0.246 | [0.286, 0.857] | [0.400, 0.714] | yes |
| EQAO grade 6 | faithful_strict | 10 | 5 | 0.500 | 0.245 | [0.200, 0.800] | [0.333, 0.600] | no |
| EQAO grade 6 | faithful_digit_suspect | 4 | 3 | 0.750 | 0.250 | [0.250, 1.000] | [0.500, 1.000] | no |
| EQAO grade 6 | not_faithful | 24 | 11 | 0.458 | 0.258 | [0.250, 0.667] | [0.400, 0.500] | no |
| EQAO grade 6 | numeric_faithful | 32 | 16 | 0.500 | 0.248 | [0.344, 0.688] | [0.333, 0.643] | yes |
| EQAO grade 6 | numeric_not_faithful | 6 | 3 | 0.500 | 0.283 | [0.167, 0.833] | [0.000, 1.000] | no |
| EQAO grade 6 | unverified | 2 | 1 | 0.500 | 0.250 | [0.000, 1.000] | [0.000, 1.000] | no |

### LM masked-stem rows (saved per-item predictions, seed 20260916)

| model | cell | subset | n | pass | rate | chance | 95% CI | modal letter (freq, this subset) | lower CI > chance | lower CI > modal | bar cleared |
|---|---|---|---:|---:|---:|---:|---|---|---|---|---|
| Qwen2.5-7B-Instruct | Algebra I | original | 358 | 139 | 0.388 | 0.250 | [0.341, 0.439] | B (0.271) | yes | yes | yes |
| Qwen2.5-7B-Instruct | Algebra I | faithful | 184 | 86 | 0.467 | 0.250 | [0.391, 0.543] | B (0.255) | yes | yes | yes |
| Qwen2.5-7B-Instruct | Algebra I | faithful_strict | 149 | 69 | 0.463 | 0.250 | [0.376, 0.544] | C (0.275) | yes | yes | yes |
| Qwen2.5-7B-Instruct | Algebra I | faithful_digit_suspect | 35 | 17 | 0.486 | 0.250 | [0.314, 0.657] | D (0.371) | yes | no | no |
| Qwen2.5-7B-Instruct | Algebra I | not_faithful | 168 | 49 | 0.292 | 0.250 | [0.220, 0.363] | C (0.286) | no | no | no |
| Qwen2.5-7B-Instruct | Algebra I | trailing_junk_only | 11 | 2 | 0.182 | 0.250 | [0.000, 0.455] | A (0.364) | no | no | no |
| Qwen2.5-7B-Instruct | Algebra I | unverified | 6 | 4 | 0.667 | 0.250 | [0.333, 1.000] | B (0.500) | no | no | no |
| Qwen2.5-7B-Instruct | Algebra II | original | 248 | 91 | 0.367 | 0.250 | [0.306, 0.423] | C (0.278) | yes | yes | yes |
| Qwen2.5-7B-Instruct | Algebra II | faithful | 115 | 40 | 0.348 | 0.250 | [0.261, 0.435] | B (0.296) | yes | no | no |
| Qwen2.5-7B-Instruct | Algebra II | faithful_strict | 88 | 31 | 0.352 | 0.250 | [0.261, 0.455] | B (0.295) | yes | no | no |
| Qwen2.5-7B-Instruct | Algebra II | faithful_digit_suspect | 27 | 9 | 0.333 | 0.250 | [0.185, 0.519] | B (0.296) | no | no | no |
| Qwen2.5-7B-Instruct | Algebra II | not_faithful | 124 | 49 | 0.395 | 0.250 | [0.306, 0.476] | C (0.323) | yes | no | no |
| Qwen2.5-7B-Instruct | Algebra II | trailing_junk_only | 6 | 2 | 0.333 | 0.250 | [0.000, 0.667] | C (0.500) | no | no | no |
| Qwen2.5-7B-Instruct | Algebra II | unverified | 9 | 2 | 0.222 | 0.250 | [0.000, 0.444] | A (0.333) | no | no | no |
| Qwen2.5-14B-Instruct | Algebra I | original | 358 | 149 | 0.416 | 0.250 | [0.363, 0.469] | B (0.271) | yes | yes | yes |
| Qwen2.5-14B-Instruct | Algebra I | faithful | 184 | 79 | 0.429 | 0.250 | [0.359, 0.500] | B (0.255) | yes | yes | yes |
| Qwen2.5-14B-Instruct | Algebra I | faithful_strict | 149 | 66 | 0.443 | 0.250 | [0.369, 0.517] | C (0.275) | yes | yes | yes |
| Qwen2.5-14B-Instruct | Algebra I | faithful_digit_suspect | 35 | 13 | 0.371 | 0.250 | [0.200, 0.543] | D (0.371) | no | no | no |
| Qwen2.5-14B-Instruct | Algebra I | not_faithful | 168 | 66 | 0.393 | 0.250 | [0.321, 0.464] | C (0.286) | yes | yes | yes |
| Qwen2.5-14B-Instruct | Algebra I | trailing_junk_only | 11 | 5 | 0.455 | 0.250 | [0.182, 0.727] | A (0.364) | no | no | no |
| Qwen2.5-14B-Instruct | Algebra I | unverified | 6 | 4 | 0.667 | 0.250 | [0.333, 1.000] | B (0.500) | no | no | no |
| Qwen2.5-14B-Instruct | Algebra II | original | 248 | 89 | 0.359 | 0.250 | [0.298, 0.415] | C (0.278) | yes | yes | yes |
| Qwen2.5-14B-Instruct | Algebra II | faithful | 115 | 44 | 0.383 | 0.250 | [0.287, 0.461] | B (0.296) | yes | no | no |
| Qwen2.5-14B-Instruct | Algebra II | faithful_strict | 88 | 30 | 0.341 | 0.250 | [0.239, 0.432] | B (0.295) | no | no | no |
| Qwen2.5-14B-Instruct | Algebra II | faithful_digit_suspect | 27 | 14 | 0.519 | 0.250 | [0.333, 0.704] | B (0.296) | yes | yes | yes |
| Qwen2.5-14B-Instruct | Algebra II | not_faithful | 124 | 42 | 0.339 | 0.250 | [0.250, 0.419] | C (0.323) | no | no | no |
| Qwen2.5-14B-Instruct | Algebra II | trailing_junk_only | 6 | 2 | 0.333 | 0.250 | [0.000, 0.667] | C (0.500) | no | no | no |
| Qwen2.5-14B-Instruct | Algebra II | unverified | 9 | 3 | 0.333 | 0.250 | [0.000, 0.667] | A (0.333) | no | no | no |
| Phi-4 | Algebra I | original | 358 | 151 | 0.422 | 0.250 | [0.374, 0.472] | B (0.271) | yes | yes | yes |
| Phi-4 | Algebra I | faithful | 184 | 86 | 0.467 | 0.250 | [0.397, 0.538] | B (0.255) | yes | yes | yes |
| Phi-4 | Algebra I | faithful_strict | 149 | 68 | 0.456 | 0.250 | [0.369, 0.530] | C (0.275) | yes | yes | yes |
| Phi-4 | Algebra I | faithful_digit_suspect | 35 | 18 | 0.514 | 0.250 | [0.343, 0.686] | D (0.371) | yes | no | no |
| Phi-4 | Algebra I | not_faithful | 168 | 61 | 0.363 | 0.250 | [0.292, 0.440] | C (0.286) | yes | yes | yes |
| Phi-4 | Algebra I | trailing_junk_only | 11 | 4 | 0.364 | 0.250 | [0.091, 0.636] | A (0.364) | no | no | no |
| Phi-4 | Algebra I | unverified | 6 | 4 | 0.667 | 0.250 | [0.333, 1.000] | B (0.500) | no | no | no |
| Phi-4 | Algebra II | original | 248 | 86 | 0.347 | 0.250 | [0.286, 0.407] | C (0.278) | yes | yes | yes |
| Phi-4 | Algebra II | faithful | 115 | 40 | 0.348 | 0.250 | [0.270, 0.435] | B (0.296) | yes | no | no |
| Phi-4 | Algebra II | faithful_strict | 88 | 30 | 0.341 | 0.250 | [0.250, 0.443] | B (0.295) | no | no | no |
| Phi-4 | Algebra II | faithful_digit_suspect | 27 | 10 | 0.370 | 0.250 | [0.185, 0.556] | B (0.296) | no | no | no |
| Phi-4 | Algebra II | not_faithful | 124 | 43 | 0.347 | 0.250 | [0.266, 0.427] | C (0.323) | yes | no | no |
| Phi-4 | Algebra II | trailing_junk_only | 6 | 3 | 0.500 | 0.250 | [0.167, 0.833] | C (0.500) | no | no | no |
| Phi-4 | Algebra II | unverified | 9 | 3 | 0.333 | 0.250 | [0.000, 0.667] | A (0.333) | no | no | no |
| Phi-4 | geometry (unclaimed) | original | 166 | 67 | 0.404 | 0.250 | [0.331, 0.476] | B (0.289) | yes | yes | yes |
| Phi-4 | geometry (unclaimed) | faithful | 109 | 46 | 0.422 | 0.250 | [0.330, 0.514] | B (0.303) | yes | yes | yes |
| Phi-4 | geometry (unclaimed) | faithful_after_relocation | 110 | 46 | 0.418 | 0.250 | [0.327, 0.509] | B (0.300) | yes | yes | yes |
| Phi-4 | geometry (unclaimed) | faithful_strict | 93 | 41 | 0.441 | 0.250 | [0.344, 0.538] | B (0.312) | yes | yes | yes |
| Phi-4 | geometry (unclaimed) | faithful_digit_suspect | 16 | 5 | 0.312 | 0.250 | [0.125, 0.562] | C (0.312) | no | no | no |
| Phi-4 | geometry (unclaimed) | not_faithful | 57 | 21 | 0.368 | 0.250 | [0.246, 0.491] | A (0.263) | no | no | no |
| Phi-4 | geometry (unclaimed) | trailing_junk_only | 5 | 0 | 0.000 | 0.250 | [0.000, 0.000] | A (0.600) | no | no | no |
