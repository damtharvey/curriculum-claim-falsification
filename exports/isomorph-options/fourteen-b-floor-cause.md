# Qwen2.5-14B text-layer isomorph floor: cause

The text-layer isomorph original arm for Qwen2.5-14B-Instruct is `below_floor`: letter agreement with `exports/addendum-gpu/masked-stem-14b-items.jsonl` is 592/606 = 0.9769 versus the pre-registered 0.98 floor. The same 14 ids disagreed in `exports/isomorph-options/scores-14b-original.jsonl` and in `exports/repaired-layer/scores-14b-amendment-original.jsonl`. This note diagnoses that miss. It does not change the isomorph preregistration and does not promote the arms.

Written: 2026-09-17T13:56:16Z. Seed 20260916. CUDA, no CPU path.

## Cause

The cause is a systematic numeric gap between the saved torch 2.12.1+cu130 run and later torch 2.14.0+cu130 batch-1 loads of the same snapshot, prompt, mask, seed, dtype, and SDPA setting, not run-to-run kernel noise on the current torch. The two later loads are bit-identical on the 14 ids, and three bf16 repeats of those 14 items did not flip a letter. 6 of 14 later disagreements are exact ties (margin 0; the argmax keeps the earlier option). The other 8 are not near-ties: their later margins sit between 0.25 and 0.75 nats, except `nyregents-algebra-ii-2016-jun-q18`, where the saved run prefers A by 6.75 nats and later runs prefer D on the same dirty census masked stem. Isolated bf16 batch 1 agrees with the saved letters on 0 of 14. Casting the logits head to fp32 recovers 4 of 14 saved letters and does not recover the rest. `torch.use_deterministic_algorithms(True)` with bf16 SDPA matches the later letters, not the saved ones. The 0.98 floor is therefore a torch-version logit shift on 14 items, six of them exact ties.

## Evidence

Saved masked-stem 14B run: torch `2.12.1+cu130`, transformers `4.57.6`, dtype `bfloat16`, attention `sdpa`, batch size `1`.

This diagnosis: torch `2.14.0+cu130`, transformers `4.57.6`, GPU `NVIDIA GeForce RTX 5090`.

The two later batch-1 runs agree with each other on all 606 letters and, on the 14 disagreeing ids, on every per-letter logprob (max absolute difference 0). The disagreement is therefore a systematic gap between the saved torch 2.12.1 letters and later torch 2.14.0 letters, not a flip between the two later loads.

Near-tie threshold: |Δ| < 0.05 nats between the top two letters.

| run | 14 disagreeing: near-tie | 14: exact tie | 14: median margin | other 592: near-tie | other 592: median margin |
|---|---:|---:|---:|---:|---:|
| saved (torch 2.12.1) | 3/14 | 3/14 | 0.2500 | 7/592 | 5.0000 |
| isomorph original (later) | 6/14 | 6/14 | 0.2500 | 6/592 | 5.0000 |
| repaired-layer amendment (later) | 6/14 | 6/14 | 0.2500 | 6/592 | 5.0000 |

Per disagreeing id, saved versus later letters and margins:

| id | saved | later | saved margin | later margin | saved near-tie | later near-tie |
|---|---|---|---:|---:|---|---|
| `nyregents-algebra-i-2020-jan-q12` | D | B | 0.5000 | 0.0000 | false | true |
| `nyregents-algebra-i-2019-jan-q21` | A | C | 0.0000 | 0.5000 | true | false |
| `nyregents-algebra-i-2026-jun-q6` | C | A | 0.7500 | 0.5000 | false | false |
| `nyregents-algebra-i-2025-aug-q6` | C | A | 0.2500 | 0.2500 | false | false |
| `nyregents-algebra-i-2015-jan-q8` | B | A | 0.2500 | 0.0000 | false | true |
| `nyregents-algebra-i-unknown-unk-q6` | A | C | 0.0000 | 0.2500 | true | false |
| `nyregents-algebra-i-2016-jan-q11` | B | A | 1.7500 | 0.0000 | false | true |
| `nyregents-algebra-ii-2023-jan-q5` | B | D | 0.2500 | 0.5000 | false | false |
| `nyregents-algebra-ii-2023-jan-q19` | C | B | 0.0000 | 0.2500 | true | false |
| `nyregents-algebra-ii-2018-jan-q18` | B | A | 0.5000 | 0.2500 | false | false |
| `nyregents-algebra-ii-2024-jun-q1` | D | B | 0.2500 | 0.0000 | false | true |
| `nyregents-algebra-ii-2024-jan-q8` | D | B | 0.2500 | 0.0000 | false | true |
| `nyregents-algebra-ii-2016-jun-q18` | A | D | 6.7500 | 0.7500 | false | false |
| `nyregents-algebra-ii-2020-jan-q4` | B | C | 0.1250 | 0.0000 | false | true |

`nyregents-algebra-ii-2016-jun-q18` is not a near-tie: the saved run puts mass on A (margin 6.75 nats) and the later runs put mass on D. The masked stem is the census dirty encoding `c(x) \x05 log[N]x` in both files, so the shift is numerical, not a stem rewrite.

Fresh GPU settings on this machine, letters versus the saved file:

| setting | n scored | batch | head | deterministic | attn | saved letters recovered among the 14 | reproduces all saved letters | error |
|---|---:|---:|---|---|---|---:|---|---|
| bf16_batch1_isolated_14 | 14 | 1 | bf16_model_float_softmax | false | sdpa | 0 | false | — |
| bf16_batch1_all_606 | 606 | 1 | bf16_model_float_softmax | false | sdpa | 0 | false | — |
| fp32_logits_head_batch1 | 14 | 1 | fp32_head | false | sdpa | 4 | false | — |
| bf16_deterministic_batch1 | 14 | 1 | bf16_model_float_softmax | true | sdpa | 0 | false | — |

Fresh bf16 batch-1 pass over all 606: letter agreement with saved 592/606 = 0.9769; agreement with the later on-disk original scores 606/606. Margin on the 14 vs the other 592: median 0.2500 (near-tie 6/14) vs median 5.0000 (near-tie 6/592).

## Recommendation

Keep the arms labelled `below_floor`. When the 14B text-layer isomorph table is shown, disclose that two torch 2.14.0 reloads reproduce 592/606 of the saved torch 2.12.1 letters, that 6 of the 14 disagreements are exact ties on the later run, that an fp32 logits head recovers only 4 of those 14, and that one remaining id (`nyregents-algebra-ii-2016-jun-q18`) moves by several nats on the dirty census stem. A later pre-registered amendment may replace the 0.98 letter-agreement floor with a margin-based floor (agreement computed only on items whose top-two margin is at least 0.05 nats on both the saved run and the reload), but that amendment is not made here. Do not silent-pass the arms.

Do not change `exports/isomorph-options/preregistration.md`. Do not promote the 14B text-layer arms. The repaired-layer 14B control remains the same-load scoring, which does not use this floor.

## Files

- this note
- `fourteen-b-floor-evidence.json`

Script: `scripts/diagnose_14b_floor.py`.
