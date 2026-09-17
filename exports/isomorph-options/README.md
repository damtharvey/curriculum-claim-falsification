# Option-numeral isomorphs (masked-stem contamination control)

Review-2 W4 Q4 and W8. The reader sees the same masked stem and the same key letter. Numerals in the option strings are replaced by value-changing, form-preserving isomorphs. If the rate holds, the reader is using form. If it collapses toward chance, the original rate is not a form effect.

Preregistration: `preregistration.md`, sha256 `997242b9fb7437ffc2e86e2759e1373ba8ad98e231b0836ef8798a2266523e9b`, written before scoring. Seed 20260916. Masking hash v1. CUDA letter-logprob argmax reused from `scripts/score_choices_only_local_lm.py`. Does not edit `paper/`.

## Reproduction of saved original letters

- Qwen2.5-7B-Instruct: 595/606 = 0.9818 vs saved `exports/addendum-gpu/masked-stem-7b-items.jsonl`
- Qwen2.5-14B-Instruct: 592/606 = 0.9769 vs saved `exports/addendum-gpu/masked-stem-14b-items.jsonl`
- Phi-4: 606/606 = 1.0000 vs saved `exports/addendum-gpu/masked-stem-phi4-items.jsonl`

Floor was 0.98. Perturbed arms were scored only for models that cleared it. Models below the floor are listed in `results.json` `stoppedModels` and their perturbed arms were not scored.

## Pre-registered reading (Algebra I print-faithful, rank-preserving)

- Qwen2.5-7B-Instruct: mixed: neither polar reading; the rank-preserving faithful rate did not both clear the bar and have a paired difference CI that includes 0, and it did not fall to chance
- Qwen2.5-14B-Instruct: not scored: original letter agreement was below 0.98
- Phi-4: form-based: the rank-preserving faithful rate clears the channel bar and the paired difference CI includes 0; the contamination concern is not supported

## no_numeral

Items with no numeral in any option are unchanged and are excluded from the paired difference.

- Algebra I: 61
- Algebra II: 21
- Total: 82

## Rates

Bar: n >= 10 and lower bootstrap 95% CI strictly above chance 0.25 and above the subset modal-letter frequency. Paired Δ is perturbed minus original on items that are not `no_numeral`. Chance is 0.25 (mean 1/k on these 4-option items). Bootstrap: `random.Random.randrange`, 1000 replicates, rate seed `21 + n`, paired seed `31 + n`.

| model | subset | n | original | rank-preserving | scrambled | paired Δ preserving 95% CI | preserving bar | scrambled bar |
|---|---|---:|---|---|---|---|---|---|
| Qwen2.5-7B-Instruct | Algebra I all | 358 | 0.391 [0.344, 0.441] | 0.344 [0.293, 0.394] | 0.360 [0.313, 0.411] | -0.057 [-0.118, 0.003] | yes | yes |
| Qwen2.5-7B-Instruct | Algebra I faithful | 184 | 0.473 [0.397, 0.549] | 0.391 [0.321, 0.462] | 0.391 [0.321, 0.462] | -0.110 [-0.199, -0.015] | yes | yes |
| Qwen2.5-7B-Instruct | Algebra I faithful and recognition | 83 | 0.530 [0.422, 0.627] | 0.361 [0.253, 0.458] | 0.410 [0.301, 0.518] | -0.250 [-0.375, -0.125] | no | yes |
| Qwen2.5-7B-Instruct | Algebra I faithful and execution | 75 | 0.360 [0.253, 0.480] | 0.387 [0.280, 0.507] | 0.320 [0.213, 0.427] | +0.030 [-0.106, 0.152] | no | no |
| Qwen2.5-7B-Instruct | Algebra II all | 248 | 0.367 [0.306, 0.423] | 0.339 [0.282, 0.395] | 0.302 [0.246, 0.363] | -0.031 [-0.093, 0.035] | yes | no |
| Qwen2.5-7B-Instruct | Algebra II faithful | 115 | 0.348 [0.261, 0.435] | 0.357 [0.270, 0.452] | 0.287 [0.200, 0.365] | +0.009 [-0.085, 0.104] | no | no |
| Phi-4 | Algebra I all | 358 | 0.422 [0.374, 0.472] | 0.360 [0.310, 0.408] | 0.380 [0.327, 0.427] | -0.074 [-0.138, -0.017] | yes | yes |
| Phi-4 | Algebra I faithful | 184 | 0.467 [0.397, 0.538] | 0.408 [0.342, 0.478] | 0.446 [0.375, 0.516] | -0.081 [-0.169, 0.015] | yes | yes |
| Phi-4 | Algebra I faithful and recognition | 83 | 0.506 [0.398, 0.614] | 0.398 [0.289, 0.506] | 0.410 [0.301, 0.518] | -0.161 [-0.304, -0.036] | yes | yes |
| Phi-4 | Algebra I faithful and execution | 75 | 0.387 [0.293, 0.507] | 0.373 [0.267, 0.480] | 0.440 [0.333, 0.560] | -0.015 [-0.152, 0.121] | no | yes |
| Phi-4 | Algebra II all | 248 | 0.347 [0.286, 0.407] | 0.327 [0.266, 0.387] | 0.306 [0.254, 0.363] | -0.022 [-0.079, 0.031] | no | no |
| Phi-4 | Algebra II faithful | 115 | 0.348 [0.270, 0.435] | 0.339 [0.252, 0.426] | 0.330 [0.243, 0.409] | -0.009 [-0.104, 0.075] | no | no |

## Sanity examples (before / after)

Digit counts, signs, decimal places, nonzero denominators, consistent substitution, and rank order on the rank-preserving arm were asserted in `scripts/perturb_option_numerals.py` before GPU scoring.

### `nyregents-algebra-i-2018-jun-q1`

- original: `{"A": "p > -6", "C": "p > 4", "B": "p < -6", "D": "p < 4"}`
- rank-preserving: `{"A": "p > -2", "C": "p > 6", "B": "p < -2", "D": "p < 6"}`
- scrambled: `{"A": "p > -9", "C": "p > 0", "B": "p < -9", "D": "p < 0"}`

### `nyregents-algebra-i-2018-jun-q6`

- original: `{"A": "1.60x + 1.75y < 10", "C": "1.75x + 1.60y < 10", "B": "1.60x + 1.75y > 10", "D": "1.75x + 1.60y > 10"}`
- rank-preserving: `{"A": "2.27x + 3.35y < 44", "C": "3.35x + 2.27y < 44", "B": "2.27x + 3.35y > 44", "D": "3.35x + 2.27y > 44"}`
- scrambled: `{"A": "4.52x + 5.64y < 45", "C": "5.64x + 4.52y < 45", "B": "4.52x + 5.64y > 45", "D": "5.64x + 4.52y > 45"}`

### `nyregents-algebra-i-2016-jun-q7`

- original: `{"A": "6.2", "C": "8.6", "B": "7.3", "D": "8.8"}`
- rank-preserving: `{"A": "7.4", "C": "9.7", "B": "9.6", "D": "9.8"}`
- scrambled: `{"A": "8.2", "C": "4.2", "B": "4.9", "D": "2.7"}`

### `nyregents-algebra-i-2017-jan-q8`

- original: `{"A": "a1 \u0004 49; an \u0004 an \u0002 1 \u0003 21", "B": "a1 \u0004 0; an \u0004 49an \u0002 1 \u0003 21", "C": "a1 \u0004 21; an \u0004 an \u0002 1 \u0003 49", "D": "a1 \u0004 0; an \u0004 21an \u0002 1 \u0003 49"}`
- rank-preserving: `{"A": "a9 \u0004 68; an \u0004 an \u0002 9 \u0003 42", "B": "a9 \u0004 2; an \u0004 68an \u0002 9 \u0003 42", "C": "a9 \u0004 42; an \u0004 an \u0002 9 \u0003 68", "D": "a9 \u0004 2; an \u0004 42an \u0002 9 \u0003 68"}`
- scrambled: `{"A": "a8 \u0004 48; an \u0004 an \u0002 8 \u0003 57", "B": "a8 \u0004 2; an \u0004 48an \u0002 8 \u0003 57", "C": "a8 \u0004 57; an \u0004 an \u0002 8 \u0003 48", "D": "a8 \u0004 2; an \u0004 57an \u0002 8 \u0003 48"}`

### `nyregents-algebra-i-2015-jan-q8`

- original: `{"A": "2589", "C": "15,901", "B": "6510", "D": "18,490"}`
- rank-preserving: `{"A": "8756", "C": "64,488", "B": "9195", "D": "98,488"}`
- scrambled: `{"A": "9786", "C": "96,942", "B": "2934", "D": "16,110"}`

## Files

- `preregistration.md`, `preregistration.sha256`
- `perturbed-items-isomorph_rank_preserving.jsonl`, `perturbed-items-isomorph_rank_scrambled.jsonl`
- `scores-{7b,14b,phi4}-{original,isomorph_rank_preserving,isomorph_rank_scrambled}.jsonl`
- `results.json`, `sanity-examples.json`

Scripts: `scripts/perturb_option_numerals.py`, `scripts/score_isomorph_options.py`.
