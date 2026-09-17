# Choices-only local LM (exploratory)

## Question

On selected-response items whose option strings pass the sibling mechanical clean-option filter, does a local instruction-tuned language model beat chance (mean of 1/k) from the option list alone, with the stem withheld?

## Method

- Model: `Qwen/Qwen2.5-7B-Instruct`, Hugging Face cache revision `a09a35458c702b33eeacc393d103063234e8bc28`, bf16, RTX 5090. Repository `.venv`.
- Filter: sibling `exports/addendum/choices-only-clean-filter.json` used verbatim. Keep list 1496 of 2245 selected-response items. Nine keep-list items were skipped at score time because the key is not a single option letter (multi-select or missing letter), not because the filter was changed.
- Prompt: options only, original order with letters, no stem, no source or exam name. Exact strings are in `choices-only-local-lm.json` `promptTemplate`.
- Score: next-token log-probabilities over option letters after the chat template; greedy argmax over letters (max of the bare letter token and the space-prefixed letter token). Not free generation.
- Chance: mean of 1/k per item. Bootstrap: `random.Random.randrange`, 1000 replicates, 95% percentile CI, seed `21 + n`, matching `scripts/score_choices_only.py`.
- Position control: always pick the most common key letter among scored items (B).
- With-stem sanity: same model, 200 clean items, stem included, next-token letter argmax (no chain of thought).
- Label: exploratory. The paper's witness bar is per cell, n >= 10, lower CI above chance. This run does not change the frozen paper.

## Numbers

- n scored (choices-only): **1487**
- overall rate: **0.301** vs chance **0.250**, 95% CI **[0.277, 0.326]**. Lower CI above chance (pooled). Pooled is not a paper cell.
- position baseline (always B): **0.275**. The model does not collapse to B (chosen letters: D 508, C 457, A 289, B 233).
- with-stem sanity: **0.460** n=200, CI [0.385, 0.525] vs chance 0.250. Pipeline is not broken; letter-argmax without reasoning is still a weak math solver.
- wall time: 84 s (model load 14 s).

### Per-source (n >= 10), lower CI above chance

- `staar` n=246 rate=0.350 CI [0.293, 0.415] chance=0.250
- `nyregents` n=919 rate=0.288 CI [0.260, 0.317] chance=0.250
- Others (EQAO, NAPLAN, NYSED, PISA, TIMSS 1995) do not clear.

### Cells with lower CI above chance (n >= 10)

- `nyregents::algebra-i` n=408 rate=0.309 CI [0.265, 0.355] chance=0.250
- `teks::g3` n=27 rate=0.444 CI [0.259, 0.630] chance=0.250 (thin)
- `teks::g7` n=18 rate=0.500 CI [0.278, 0.722] chance=0.250 (thin)

Geometry, algebra-ii, EQAO g6, and TIMSS knowing / applying / reasoning do not clear.

### Subagent overlap

Disk has 2242 per-item `composer-2.5-fast` rows, not 488. Overlap with this clean scored set: n=1484. Correctness agreement 0.598. Original-letter agreement 0.322 (subagent used shuffled options; letters mapped back). Subagent rate on the overlap 0.361 vs local 0.302.

## Does this change what the paper can claim?

No. Exploratory only. The frozen PDF already refuses choices-only because option strings were dirty. This is a clean-option local-LM rerun after that filter. The pooled rate and the two thin TEKS cells should not be claimed. `nyregents::algebra-i` clears the per-cell bar here (n=408, lower CI 0.265 > 0.25) but is not in the mentor PDF and is a different channel from the catalog rules. Do not deposit.

## What a writer should cite

From `exports/addendum-gpu/choices-only-local-lm.json`:

- `modelId`, `modelRevision`
- `filter.used_verbatim`, `filter.filter_source`
- `overall.n`, `overall.passRate`, `overall.chance`, `overall.ci95`, `overall.witnessBarEligible`
- `positionBaseline.letter`, `positionBaseline.rate`
- `chosenLetterCounts`
- `perSource`, `perCell` (only n >= 10)
- `cellsLowerCiAboveChance`
- `withStemSanity.passRate`, `withStemSanity.ci95`
- `subagentAgreement`
- `promptTemplate`
- `versions`, `wallTimeSeconds`

Per-item rows: `exports/addendum-gpu/choices-only-local-lm-items.jsonl` fields `id`, `n_options`, `chosen_letter`, `key`, `correct`, `logprobs`.

## Position baseline and memorization (follow-up)

Analysis only of the 7B choices-only run. Script: `scripts/analyze_choices_only_position_memorization.py`. Artifact: `exports/addendum-gpu/position-and-memorization.json`. Existing 7B JSON and item rows were not modified.

Sanity: clean keep list 1496, n scored 1487, overall rate 0.3012777404169469, chance 0.2503922887245012, CI [0.27706792199058505, 0.3261600537995965] match `choices-only-local-lm.json` exactly.

### Per-cell modal-letter baseline (n >= 10)

For each cell, the best constant-letter guess is the modal key letter (ties take the earlier letter in A-E). The three cells whose 7B lower CI is above chance (mean 1/k) are the same three whose lower CI is **not** above that cell's modal-letter frequency. No n >= 10 cell has lower CI above the modal letter.

| cell | n | model rate | 95% CI | modal letter | modal frequency | verdict |
|---|---:|---:|---|---|---:|---|
| `nyregents::algebra-i` | 408 | 0.309 | [0.265, 0.355] | B (111/408) | 0.272 | lower CI above chance, **does not beat position** |
| `teks::g3` | 27 | 0.444 | [0.259, 0.630] | B (8/27) | 0.296 | lower CI above chance, **does not beat position** (thin) |
| `teks::g7` | 18 | 0.500 | [0.278, 0.722] | B (6/18) | 0.333 | lower CI above chance, **does not beat position** (thin) |

Algebra I point estimate 0.309 is above modal 0.272, but the lower CI 0.265 is not. TEKS g3 and g7 point estimates sit well above their modal letters; the intervals are too wide to clear the modal frequency.

### Options-content signal net of position

Among 448 correct 7B picks, 122 (0.272) are items whose key is that cell's modal letter. On the 1026 items whose key is **not** the cell modal letter, rate is **0.318** CI [0.288, 0.347] vs chance 0.250 (lower CI above chance). So the model is not only harvesting position: there is leftover option-string signal after removing modal-key items.

Same split, n >= 10 cells only: non-modal rate 0.316 [0.290, 0.345] n=1016. Per source, non-modal lower CI above chance for `nyregents` 0.307 [0.275, 0.343] n=668, `staar` 0.341 [0.269, 0.413] n=167, `eqao` 0.348 [0.258, 0.449] n=89.

### Recency / memorization

Year from `item.year` when it is 19xx/20xx, else a year delimited in the id or corpus. 1471/1487 scored items parse; 16 `nyregents-algebra-i-unknown-unk-*` ids are unparsed. Buckets: before 2015, 2015 to 2019, 2020 and later. Pre-2015 Regents are widely posted; EQAO 2023 sits in 2020 and later.

**Accuracy does not fall monotonically with recency.** 7B on the clean scored set:

| bucket | n | local 7B | Composer (same items) | Composer minus local |
|---|---:|---:|---:|---:|
| before 2015 | 178 | 0.303 [0.236, 0.376] | 0.416 [0.343, 0.489] | +0.112 |
| 2015 to 2019 | 578 | 0.311 [0.272, 0.351] | 0.336 [0.298, 0.375] | +0.024 |
| 2020 and later | 712 | 0.296 [0.263, 0.330] | 0.365 [0.329, 0.399] | +0.069 |
| unparsed | 16 | 0.188 | 0.500 | +0.312 |

Overlap n=1484 (three clean scored ids have no Composer row). Local 2015-2019 is the highest 7B bucket, not the oldest. Newest minus oldest for 7B is only -0.008. Composer on the same items is highest on pre-2015 (0.416) and the Composer-minus-local gap is largest there (+0.112), which is the direction a leaked-exam memorization story would predict for Composer, not for 7B.

Composer on all 2242 disk rows (dirty options included): before 2015 0.370 n=265; 2015-2019 0.329 n=827; 2020+ 0.340 n=1131. Still not monotone. NY Regents alone on the clean 7B set: before 2015 0.324 n=37; 2015-2019 0.299 n=442; 2020+ 0.278 n=424. Point estimates fall, but the pre-2015 cell is thin and its CI covers the later rates.

This follow-up does not change what the paper can claim. Algebra I still does not beat its own position baseline on the CI test used for chance.

## 14B rerun (same options-only protocol)

`Qwen/Qwen2.5-14B-Instruct` revision `cf98f3b3bbb457ad9e2bb7baf9a0125b6b88caa8`, bf16, `device_map="cuda"`, batch size 1, RTX 5090 (peak about 29.0 GB of 32 GB; no CPU offload, no quantization). Same prompt, clean list, seed `20260916`, letter-logprob argmax. Script: `scripts/score_choices_only_local_lm.py`. Artifacts: `choices-only-local-lm-14b.json`, `choices-only-local-lm-14b-items.jsonl`. With-stem sanity skipped (options-only only). Wall 437 s.

- n scored: **1487** (same keep list; 9 unscorable keys skipped, same ids)
- pooled rate: **0.301** vs chance **0.250**, 95% CI **[0.276, 0.323]**. Same 448/1487 as 7B; not the same items (letter agreement 0.457, all 1487 logprob maps differ).
- position baseline (always B): **0.275**
- chosen letters: C 625, B 451, D 352, A 57, E 2 (7B was D-heavy; 14B is C-heavy)
- Composer overlap rate remains 0.361. Pooled 14B does not sit between 7B and Composer; it matches 7B.

| cell | 14B rate | 95% CI | modal freq (from keys) | vs chance | vs position |
|---|---:|---|---:|---|---|
| `nyregents::algebra-i` n=408 | 0.321 | [0.279, 0.363] | 0.272 | clears | **beats position** (lower CI 0.279 > 0.272) |
| `teks::g3` n=27 | 0.259 | [0.111, 0.444] | 0.296 | does not clear | does not beat position |
| `teks::g7` n=18 | 0.333 | [0.111, 0.556] | 0.333 | does not clear | does not beat position |

14B also has `eqao::g6` n=50 rate 0.400 CI [0.280, 0.540] vs chance 0.254 (clears chance; modal frequency 0.400, so it does not beat position). Exploratory. Do not deposit.

## Masked-stem plus options (exploratory)

### Question

Can a local instruction-tuned LM beat chance, and beat the per-cell modal-letter frequency, when it sees the question type, units, and the option set, but every given quantity in the stem is replaced by `[N]`?

This is a flexible test-wise channel: the taker can use item type and options, and cannot compute the numerical answer from the stem.

### Method

- Same clean keep list as choices-only (1496 ids, 1487 scoreable). Preregistration: `masked-stem-preregistration.md`, sha256 `af473bb6cd9d46dc74e034f4460d56a808273fe83ffaf457cd7d122c40ae80e8`, hashed before scoring.
- Prompt: masked stem plus options in original order with letters. Instruction: pick the letter of the correct answer. Greedy letter-logprob argmax after the chat template, seed `20260916`. Script: `scripts/score_choices_only_local_lm.py --prompt-mode masked-stem`.
- Options-only numbers were not rerun. Paired increment uses the existing 7B and 14B options-only item files.
- Position control: per-cell modal-letter frequency from `position-and-memorization.json`.
- Witness bar for this channel: per cell n >= 10, lower CI above chance, and lower CI above that cell's modal-letter frequency. Label exploratory unless a cell clears both. Do not deposit.

### Masking audit

40-item sample in `masked-stem-audit-sample.json` (seed `20260916`). Drops: **0**. Second sweep: **0**. Sample leak flags: **0**. No remaining digits or listed number words on the 1487 stems after the first pass.

### 7B (`Qwen/Qwen2.5-7B-Instruct` rev `a09a35458c702b33eeacc393d103063234e8bc28`)

- n=1487, rate **0.405** vs chance **0.250**, 95% CI **[0.380, 0.431]**. Lower CI above chance and above always-B **0.275**.
- vs options-only (same items): McNemar n01 (masked right, options wrong) **348**, n10 **194**, both correct 254, both wrong 691. Share masked-only 0.234, options-only 0.130.
- Non-modal-key items: 0.383 [0.354, 0.412] n=1016 vs chance 0.250.
- Wall 130 s (load 13 s). Chosen letters: B 449, C 439, D 358, A 235, E 6.

Cells with n >= 10 whose lower CI clears **both** chance and the modal-letter frequency:

| cell | n | rate | 95% CI | chance | modal | verdict |
|---|---:|---:|---|---:|---:|---|
| `nyregents::algebra-i` | 408 | 0.417 | [0.365, 0.466] | 0.250 | B 0.272 | clears both |
| `nyregents::algebra-ii` | 280 | 0.382 | [0.325, 0.443] | 0.250 | C 0.275 | clears both |
| `nyregents::geometry` | 231 | 0.359 | [0.294, 0.420] | 0.250 | B 0.273 | clears both |
| `teks::g5` | 44 | 0.523 | [0.364, 0.682] | 0.250 | D 0.273 | clears both |
| `teks::g8` | 27 | 0.741 | [0.556, 0.889] | 0.250 | B 0.333 | clears both (thin) |
| `timss::knowing` | 35 | 0.571 | [0.429, 0.743] | 0.244 | A 0.343 | clears both |

Named cells that do **not** clear both:

- `eqao::g6` n=50 rate 0.480 [0.340, 0.620] vs chance 0.254 (clears chance) vs modal B 0.400 (lower CI 0.340 does not beat position).
- `timss::applying` n=28 rate 0.357 [0.179, 0.536] vs chance 0.248, modal 0.393: neither.
- `timss::reasoning` n=58 rate 0.328 [0.224, 0.448] vs chance 0.258, modal 0.276: neither.

### 14B (`Qwen/Qwen2.5-14B-Instruct` rev `cf98f3b3bbb457ad9e2bb7baf9a0125b6b88caa8`)

bf16, `device_map="cuda"`, batch 1, RTX 5090. Same items and prompt as 7B.

- n=1487, rate **0.425** vs chance **0.250**, 95% CI **[0.399, 0.450]**. Lower CI above chance and above always-B **0.275**.
- vs options-only (same items): McNemar n01 **350**, n10 **166**, both correct 282, both wrong 689. Share masked-only 0.235, options-only 0.112.
- Non-modal-key items: 0.393 [0.363, 0.423] n=1016 vs chance 0.250.
- Wall 447 s (load 2.3 s). Chosen letters: C 535, B 441, D 298, A 209, E 4.

Cells with n >= 10 whose lower CI clears **both** chance and the modal-letter frequency:

| cell | n | rate | 95% CI | chance | modal | verdict |
|---|---:|---:|---|---:|---:|---|
| `nyregents::algebra-i` | 408 | 0.436 | [0.385, 0.485] | 0.250 | B 0.272 | clears both |
| `nyregents::algebra-ii` | 280 | 0.379 | [0.321, 0.432] | 0.250 | C 0.275 | clears both |
| `nyregents::geometry` | 231 | 0.390 | [0.329, 0.455] | 0.250 | B 0.273 | clears both |
| `eqao::g9` | 44 | 0.477 | [0.318, 0.614] | 0.256 | C 0.295 | clears both |
| `teks::g8` | 27 | 0.704 | [0.519, 0.852] | 0.250 | B 0.333 | clears both (thin) |
| `timss::knowing` | 35 | 0.657 | [0.514, 0.800] | 0.244 | A 0.343 | clears both |

Named cells that do **not** clear both:

- `eqao::g6` n=50 rate 0.500 [0.360, 0.640] vs chance 0.254 (clears chance) vs modal B 0.400 (lower CI 0.360 does not beat position).
- `timss::applying` n=28 rate 0.357 [0.179, 0.536] vs chance 0.248, modal 0.393: neither.
- `timss::reasoning` n=58 rate 0.362 [0.241, 0.483] vs chance 0.258, modal 0.276: neither.

`teks::g5` cleared both on 7B and is chance-only on 14B (lower CI 0.273, modal 0.273). `eqao::g9` is the reverse: 14B only.

### Does this change what the paper can claim?

No deposit, and the frozen PDF is unchanged. Exploratory. The paper's geometry witness cell (`nyregents::geometry`, n=231) and Algebra I (n=408) clear this channel's stricter bar (lower CI above chance and above the modal-letter frequency) on both 7B and 14B. EQAO grade 6 clears chance on both models and does not beat its modal letter B at 0.400. TIMSS knowing (n=35) clears both; applying (n=28) and reasoning (n=58) do not. Pooled rate is not a paper cell. Do not treat this as a catalog witness.

## Masked-stem withheld-quantity populations (construct fix)

The first-run pooled rates (7B 0.405, 14B 0.425 on 1487 items) mix stems where quantities were withheld with stems where nothing was withheld. On a zero-quantity stem the model can still perform the tagged operation. Primary population is `masked_token_count >= 1`. `>= 2` is robustness. Per-item `masked_token_count` and `stem_chars_masked_share` are in `masked-stem-item-mask-stats.jsonl` and `masked-stem-populations.json`.

Population sizes (all / >= 1 / >= 2):

| cell | all | >= 1 | >= 2 |
|---|---:|---:|---:|
| pooled | 1487 | 1215 | 1068 |
| Algebra I | 408 | 358 | 338 |
| Algebra II | 280 | 248 | 234 |
| geometry | 231 | 166 | 142 |
| EQAO grade 6 | 50 | 40 | 24 |
| TIMSS knowing | 35 | 22 | 13 |

272 items had `masked_token_count = 0`.

### Primary (`masked_token_count >= 1`)

| cell | 7B rate | 7B 95% CI | 14B rate | 14B 95% CI | chance | modal on pop. | 7B vs chance / modal | 14B vs chance / modal |
|---|---:|---|---:|---|---:|---:|---|---|
| pooled | 0.376 | [0.351, 0.402] | 0.388 | [0.360, 0.416] | 0.251 | always-B 0.275 | chance and always-B | chance and always-B |
| Algebra I | 0.388 | [0.341, 0.439] | 0.416 | [0.363, 0.469] | 0.250 | 0.271 | **still clears both** | **still clears both** |
| Algebra II | 0.367 | [0.306, 0.423] | 0.359 | [0.298, 0.415] | 0.250 | 0.278 | **still clears both** | **still clears both** |
| geometry | 0.319 | [0.253, 0.392] | 0.301 | [0.235, 0.373] | 0.250 | 0.289 | chance only; **does not beat modal** | **does not clear chance** |
| EQAO g6 | 0.400 | [0.225, 0.575] | 0.425 | [0.300, 0.575] | 0.255 | 0.475 | **does not clear chance** | chance only; not modal |
| TIMSS knowing | 0.500 | [0.318, 0.682] | 0.591 | [0.409, 0.773] | 0.248 | 0.409 | chance only; **does not beat modal** | chance; beats full-1487 modal 0.343, not pop. modal 0.409 |

First-run cells that still clear chance and modal on >= 1:

- 7B: Algebra I, Algebra II, TEKS g5, TEKS g8. Geometry and TIMSS knowing do **not**.
- 14B: Algebra I, Algebra II. Geometry does **not** (lower CI 0.235 < chance). TIMSS knowing clears chance and the original 1487 modal 0.343, not the restricted-set modal 0.409. TEKS g8 and EQAO g9 keep chance vs the original modal only.

EQAO grade 6 first-run cleared chance not position; on >= 1, 7B no longer clears chance.

TIMSS knowing item judgments (all 35): cue 12, knowledge 18, unclear 5. On the >= 1 survivors (n=22): cue 12, knowledge 7, unclear 3. Zero-mask knowing items are mostly tagged-operation knowledge (decimals, rectangle properties, milliliters). The high first-run knowing rate is partly those unmasked knowledge items. Item listing: `masked-stem-timss-eqao-items.json`.

McNemar vs options-only on >= 1: 7B n01=259 n10=172; 14B n01=243 n10=149.

On >= 2 (robustness, n=1068): 7B 0.367 [0.338, 0.395]; 14B 0.376 [0.345, 0.405]. Algebra I still clears both models. Geometry, EQAO g6, and TIMSS knowing (n=13) do not.

### Contamination

Per-item mean token log-prob and Min-20% of the original unmasked stem plus options, scored with 7B. Higher log-prob is lower perplexity.

On >= 1, 7B accuracy by mean-logprob quartile: Q1 0.349, Q4 0.439 (Spearman 0.091). 14B picks on the same signal: Q4 minus Q1 = 0.120, Spearman 0.107. Recency is flat for masked-stem 7B: before 2015 0.416 n=178; 2015-2019 0.409 n=579; 2020-2023 0.399 n=383; 2024 and later 0.402 n=331. 2024 and later items on disk are NY Regents (261, including June 2024 n=28 and August 2024 n=25) and EQAO (70). Options-only 7B is 0.303 / 0.311 / 0.316 / 0.272. The membership signal does not indicate memorization as the driver.

Option-permutation 7B on >= 1 (position removed by construction): pooled 0.385 [0.357, 0.412] n=1215, vs unpermuted 0.376. Algebra I 0.405 [0.355, 0.453]; geometry 0.367 [0.289, 0.440]; EQAO g6 0.525 [0.375, 0.675]; TIMSS knowing 0.500 [0.318, 0.727]. Content remains after shuffling letters.

### Version 2 masking (7B)

Preregistration sha256 `8e6186728bf247d8349f1d94b68280b49eeebac7684c7ebeaf80f29345a43ae5`. Named figures, bindings, leftover coefficients. v2 `masked_token_count >= 1` n=1286 (71 of the 272 v1 zeros gained a placeholder). Rate 0.368 [0.341, 0.396]. On the v1 >= 1 overlap n=1215, v2 0.370 vs v1 0.376, delta **-0.007** (McNemar 50 v2-only correct, 58 v1-only). Extra masking does not create the channel.

Exploratory. Do not deposit. Frozen PDF unchanged.

## Second family, information ladder, and cue attribution (2026-09-16 15:20 MDT)

Primary population remains `masked_token_count >= 1` (n=1215; Algebra I 358; Algebra II 248). Same letter-logprob argmax scorer: `scripts/score_choices_only_local_lm.py`. GPU jobs: `scripts/run_masked_stem_followup_gpu.py`. Exploratory. Do not deposit.

### A. Second model family

`mistralai/Mistral-7B-Instruct-v0.3` revision `c170c708c41dac9275d15a8fff4eca08d52bab71` (local snapshot; no download). Ungated instruct, not Qwen. Options-only and masked-stem plus options on the same 1215 primary ids.

| cell | n | masked-stem rate | 95% CI | chance | modal on pop. | vs chance | vs modal | McNemar n01 / n10 vs options-only |
|---|---:|---:|---|---:|---:|---|---|---|
| pooled | 1215 | 0.277 | [0.249, 0.304] | 0.251 | always-B 0.279 | does not clear | does not | 174 / 140 |
| Algebra I | 358 | 0.302 | [0.257, 0.349] | 0.250 | B 0.271 | **clears chance** | **does not beat modal** | 51 / 27 |
| Algebra II | 248 | 0.262 | [0.210, 0.319] | 0.250 | C 0.278 | does not | does not | 32 / 23 |
| geometry | 166 | 0.295 | [0.229, 0.373] | 0.250 | B 0.289 | does not | does not | 26 / 25 |
| EQAO g6 | 40 | 0.150 | [0.050, 0.275] | 0.255 | B 0.475 | does not | does not | 4 / 5 |
| TIMSS knowing | 22 | 0.364 | [0.136, 0.545] | 0.248 | A 0.409 | does not | does not | 2 / 4 |

Paired options-only on the same ids: pooled **0.249** [0.224, 0.272] n=1215 (at chance). Algebra I options-only 0.235 [0.196, 0.279]. Verdict: **Algebra I does not clear both bars on this non-Qwen model.** It clears chance and not the population modal letter. Algebra II clears neither. The masked-stem increment over options-only is modest (pooled n01=174, n10=140).

Cite `exports/addendum-gpu/masked-stem-mistral-7b-primary.json`: `modelId`, `modelRevision`, `namedCells`, `vsOptionsOnly`, `algebraIClearsBothOnNonQwen`. Item rows: `masked-stem-mistral-7b-items.jsonl`, `options-only-mistral-7b-items.jsonl`. Scorer summaries: `masked-stem-mistral-7b.json`, `options-only-mistral-7b.json`.

### B. Information ladder (Algebra I and Algebra II, primary items)

Full stem scored now for these two cells only, letter argmax, no chain of thought. Figure file: `exports/addendum-gpu/information-ladder.json`.

Algebra I n=358, chance 0.250, modal B 0.271 [0.226, 0.318]:

| rung | 7B | 7B 95% CI | 14B | 14B 95% CI |
|---|---:|---|---:|---|
| chance (mean 1/k) | 0.250 | n/a | 0.250 | n/a |
| modal letter B | 0.271 | [0.226, 0.318] | 0.271 | [0.226, 0.318] |
| options-only | 0.313 | [0.268, 0.360] | 0.332 | [0.285, 0.380] |
| masked-stem plus options | 0.388 | [0.341, 0.439] | 0.416 | [0.363, 0.469] |
| with-stem (full item) | 0.508 | [0.461, 0.559] | 0.575 | [0.525, 0.626] |

Algebra II n=248, chance 0.250, modal C 0.278 [0.222, 0.331]:

| rung | 7B | 7B 95% CI | 14B | 14B 95% CI |
|---|---:|---|---:|---|
| chance | 0.250 | n/a | 0.250 | n/a |
| modal letter C | 0.278 | [0.222, 0.331] | 0.278 | [0.222, 0.331] |
| options-only | 0.274 | [0.218, 0.335] | 0.286 | [0.234, 0.343] |
| masked-stem plus options | 0.367 | [0.306, 0.423] | 0.359 | [0.298, 0.415] |
| with-stem | 0.403 | [0.339, 0.464] | 0.440 | [0.379, 0.500] |

With-stem artifacts: `with-stem-algebra-7b.json`, `with-stem-algebra-14b.json` and matching `-items.jsonl`. Cite `information-ladder.json` `models.*.cells.*.rungs`.

### C. What 14B is reading (Algebra I primary, masked-stem)

`exports/addendum-gpu/masked-stem-cue-attribution.json`. Hub rule: `apply_s1` / `hub_from_edges` in `scripts/strategy_channels.py`.

| split | when key is that cue | when it is not |
|---|---|---|
| lower-central numeric | 0.341 [0.232, 0.451] n=82 | 0.438 [0.377, 0.496] n=276 |
| modal letter B | 0.454 [0.351, 0.557] n=97 | 0.402 [0.341, 0.464] n=261 |
| S1 hub | 0.370 [0.239, 0.500] n=46 | 0.423 [0.369, 0.478] n=312 |
| unique longest option | 0.333 [0.190, 0.476] n=42 | 0.427 [0.373, 0.481] n=316 |

Residual (none of those four points at the key): **0.442 [0.368, 0.521] n=163** vs chance 0.250. Lower CI above chance. The flexible reader uses cues outside this catalog.

Per option type: algebraic 0.462 [0.354, 0.585] n=65; text 0.452 [0.378, 0.521] n=188; numeric 0.310 [0.211, 0.423] n=71 (does not clear chance); mixed 0.385 [0.192, 0.577] n=26; ordered pairs 0.250 [0.000, 0.625] n=8.

Cite `splits`, `residual`, `perOptionType`.

### D. Talk examples

`exports/addendum-gpu/masked-stem-examples.json`. Six Algebra I primary hits where 14B is correct, key is not modal B, and key is not lower-central:

- `nyregents-algebra-i-2015-jun-q1`: 110 and 900 live in the options; leftover linear story maps larger dollar amount to production.
- `nyregents-algebra-i-2023-jun-q8`: leftover growth model; exponent is the number of time periods.
- `nyregents-algebra-i-2017-aug-q17`: constant per-day deduction is still a linear story.
- `nyregents-algebra-i-2017-aug-q22`: minus sign on r remains; strong negative correlation.
- `nyregents-algebra-i-2023-jan-q22`: three zeros listed, so the three-factor polynomial that includes x.
- `nyregents-algebra-i-2014-jun-q22`: 60 and 0.05 repeated in the option formulas; base-plus-per-megabyte.

Three high-confidence misses: `nyregents-algebra-i-2026-jun-q17`, `nyregents-algebra-i-2023-jan-q11`, `nyregents-algebra-i-2024-aug-q6` (named-property and growth/decay sign).

GPU wall for the four scoring jobs: 194 s (Mistral options-only 59 s, Mistral masked-stem 59 s, 7B with-stem 17 s, 14B with-stem 60 s). Nothing cut.

## Scorer capability (masked-stem vs family, 2026-09-16)

Primary population `masked_token_count >= 1` (n=1215; Algebra I 358; Algebra II 248). Same letter-logprob argmax as the Qwen and Mistral runs. Exploratory. Do not deposit.

Hypothesis: the masked-stem plus options channel needs a capable scorer, not a Qwen scorer.

### Phi-4 (`microsoft/phi-4`)

- revision: `2db69c1c3e91a05d2c64a3185acfbaf36f744e25`
- pooled masked-stem: 0.401 [0.374, 0.426] n=1215
- pooled options-only: 0.291 [0.266, 0.316]
- Algebra I masked-stem: 0.422 [0.374, 0.472] vs chance 0.250 and modal B 0.271; verdict **clears both**
- Algebra II masked-stem: 0.347 [0.286, 0.407] vs chance 0.250 and modal C 0.278; verdict **clears both**
- Algebra I residual (163 items where no catalog cue points at the key): 0.380 [0.307, 0.460]
- Algebra I option types: algebraic_expression 0.369 [0.262, 0.477] n=65; text 0.473 [0.404, 0.543] n=188; numeric 0.366 [0.254, 0.479] n=71; mixed 0.308 [0.115, 0.500] n=26; ordered_pair 0.500 [0.125, 0.875] n=8
- with-stem ceiling: Algebra I 0.497; Algebra II 0.427

### Mistral-7B-Instruct-v0.3 with-stem ceiling

- Algebra I: 0.304 [0.257, 0.352]
- Algebra II: 0.290 [0.230, 0.347]
- Masked-stem (already on disk): Algebra I 0.302 verdict chance only; Algebra II 0.262 verdict neither

### Gemma-2-9B-it

- cached: True
- scored: False
- revision: `11c9b309abf73637e4b6f9a3fa1e92e615547819`
- skip: Weights were already cached, but google/gemma-2-9b-it apply_chat_template raises TemplateError: System role not supported. The shared scorer always sends a system message, so this family was not scored.

### Scorer table (with-stem ceiling vs masked-stem)

| scorer | family | Algebra I with-stem | Algebra I masked-stem | Algebra I verdict | Algebra II with-stem | Algebra II masked-stem | Algebra II verdict |
|---|---|---:|---:|---|---:|---:|---|
| Mistral 7B | mistral | 0.304 [0.257, 0.352] | 0.302 [0.257, 0.349] | chance only | 0.290 [0.230, 0.347] | 0.262 [0.210, 0.319] | neither |
| Qwen 7B | qwen | 0.508 [0.461, 0.559] | 0.388 [0.341, 0.439] | clears both | 0.403 [0.339, 0.464] | 0.367 [0.306, 0.423] | clears both |
| Qwen 14B | qwen | 0.575 [0.525, 0.626] | 0.416 [0.363, 0.469] | clears both | 0.440 [0.379, 0.500] | 0.359 [0.298, 0.415] | clears both |
| Phi-4 | phi | 0.497 [0.447, 0.553] | 0.422 [0.374, 0.472] | clears both | 0.427 [0.367, 0.488] | 0.347 [0.286, 0.407] | clears both |
| Gemma 2 9B | gemma | n/a n/a | n/a n/a | n/a | n/a n/a | n/a n/a | n/a |

Reading: Masked-stem tracks capability rather than Qwen: Mistral 7B ceiling 0.304 (chance only) masked-stem 0.302 (chance only); capable non-Qwen and Qwen scorers clear both (Qwen 7B ceiling 0.508 (clears both) masked-stem 0.388 (clears both); Qwen 14B ceiling 0.575 (clears both) masked-stem 0.416 (clears both); Phi-4 ceiling 0.497 (clears both) masked-stem 0.422 (clears both)).

GPU runner wall: 751.3621354103088; cut: gemma_options_only: Weights were already cached, but google/gemma-2-9b-it apply_chat_template raises TemplateError: System role not supported. The shared scorer always sends a system message, so this family was not scored.. Jobs: phi4_options_only=complete, phi4_masked_stem=complete, phi4_with_stem_algebra=complete, mistral_with_stem_algebra=complete, gemma_options_only=failed.

Cite `exports/addendum-gpu/scorer-capability-table.json`:

- `hypothesis`
- `residualItemIds` (the 163 Algebra I items)
- `scorers.phi-4.modelRevision`
- `scorers.phi-4.pooledMaskedStem`, `pooledOptionsOnly`, `vsOptionsOnly`
- `scorers.phi-4.algebraI` / `algebraII` (`passRate`, `ci95`, `verdict`, `vsOptionsOnly`)
- `scorers.phi-4.algebraIOptionTypes`
- `scorers.phi-4.algebraIResidualNoCatalogCue`
- `scorers.phi-4.withStemCeiling`
- `scorers.mistral-7b-instruct-v0.3.withStemCeiling`
- `gemmaSkip`
- `scorerTable`
- `reading`
- `runnerStatusPath`

Phi-4 item rows: `masked-stem-phi4-items.jsonl`, `options-only-phi4-items.jsonl`. With-stem summaries: `with-stem-algebra-phi4.json`, `with-stem-algebra-mistral.json`.
