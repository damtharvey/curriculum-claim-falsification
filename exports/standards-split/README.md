# Standards split of the masked-stem rows (review-2 weakness 1)

Review-2 weakness 1 and question 2: the masked-stem Algebra I and Algebra II rows are used as evidence that a pass does not require executing the tagged computation on the givens, but for structural algebra tags recognizing the named form is a reading of the tag. This addendum reads the publisher's tag for every item in the two claimed cells, classifies each tag by whether its text names execution on given quantities or recognition and interpretation of a form, and recomputes the rows on each class and on the intersection with the print-faithful subset. Preregistration: `preregistration.md`, sha256 `c87a5ae0d897b389dbf5cda52086c1754955f7cbb5f9e7a7382f5ac7cc475488`, written after the tags and the cluster text were on disk and before any prediction file was joined to them. No GPU; every row is recomputed from saved per-item predictions.

## Result in one paragraph

Every item in the two cells carries a tag: 358 of 358 Algebra I and 248 of 248 Algebra II primary items map to a Common Core State Standards (CCSS) cluster in the New York State Education Department (NYSED) rating guide of its administration (58 guides, 33 distinct clusters). Under the pre-registered verb-class rule, Algebra I is 164 execution / 151 recognition-or-interpretation / 43 mixed items and Algebra II is 120 / 93 / 35. **On execution-tagged, print-faithful Algebra I items (n=75) no model clears the channel bar**: Qwen2.5-7B 27/75 = 0.360 [0.253, 0.480] clears chance but not modal B 0.293; Qwen2.5-14B 25/75 = 0.333 [0.240, 0.440] clears neither; Phi-4 29/75 = 0.387 [0.293, 0.507] has its lower interval equal to the modal frequency (22/75), not strictly above it. On execution-tagged items without the print filter (n=164) only Qwen 14B clears (0.378 [0.311, 0.457] against modal 0.299). **The Algebra I effect sits on items whose tag names recognition or interpretation**: on that class intersected with print-faithful (n=83) all three models clear (0.518 [0.410, 0.614], 0.446 [0.349, 0.554], 0.506 [0.398, 0.614] against chance 0.250 and modal D 0.265), as they do on the mixed class (n=26; 0.615, 0.654, 0.577 against modal C 0.346). On Algebra II no class clears on the faithful subset for any model (execution and faithful n=56: 0.393 [0.250, 0.518], 0.411 [0.286, 0.536], 0.339 [0.214, 0.464] against modal C 0.286); execution on the full cell (n=120) clears on the two Qwen models only and is superseded by the faithful result. Under the honesty clause the paper keeps the Algebra I claim at the cell level on print-faithful items and states that the execution subset did not clear. The one-sided reading is that on the recognition-tagged items a pass does not require the given quantities; since the tag there names recognizing or interpreting a form, this is an information-withholding result, not a witness that a pass omits the tagged operation.

The `all` and `faithful` rows reproduce the addendum and the print-faithful rows field for field (the script raises otherwise).

## Tag extraction

`scripts/extract_regents_standards.py` reads the "Map to the Learning Standards" table at the end of every Algebra I and Algebra II rating guide for the primary population (`exports/addendum-gpu/masked-stem-algebra-primary-item-ids.json`). Three read paths, recorded per row in `item-standards.jsonl`: text layer (50 guides, 518 items), a glyph table for the v202, June 2022, and August 2022 Calibri subset encoding (3 guides, 30 items), and template glyph matching for guides whose embedded font has no character map (August 2016, January 2019, and August 2019 Algebra II; June 2019 and August 2019 Algebra I; 57 items; template library from six text-layer guides; evaluated on 33,704 held-out characters with 0 errors). June 2018 Algebra II questions 2 and 3 have a correction overprinted on a white box; the visible code is resolved by rendering (1 item). Every parsed table is validated (questions 1..N contiguous, exactly 24 multiple-choice rows). The `algtwo82016` guide, which an earlier interactive run was still calibrating when the budget stopped it, parsed on this run under the visual reader with no change to the code; no guide was excluded. Full tables per guide: `rating-guide-tables.json`; coverage: `coverage.json`.

NYSED maps to the CCSS **cluster** (for example `A-REI.B`), not to a numbered standard. Cluster heading text and the standards beneath it were fetched from thecorestandards.org (`scripts/fetch_ccss_cluster_text.py`, `standards-text.json`, fetched 2026-09-17T05:18:08Z, sha256 per domain page recorded; the HTML cache under `ccss-html/` is gitignored).

## Verb-class rule (pre-registered)

Each imperative verb heading a top-level clause of the cluster heading is classified by the vocabulary in `preregistration.md`: execution (solve, evaluate an expression, rewrite, factor, complete the square, create, compute, graph, perform arithmetic operations, build, derive, and the rest) or recognition-or-interpretation (identify, interpret, recognize, compare, explain, understand, analyze, prove, and the rest). All execution: `execution`; all recognition: `recognition_or_interpretation`; both: `mixed`. A heading with no classifiable verb (`Extend ...`, `Use X` with no purpose verb) takes the class of its non-`(+)` numbered standards. A disclosed secondary class, `execution_strict`, drops execution clusters any of whose numbered standards is purely recognition. All 33 clusters and the verbs found are listed in the preregistration.

| class | Algebra I clusters (items) | Algebra II clusters (items) |
|---|---|---|
| execution | A-APR.A 25, A-CED.A 25, A-REI.B 36, A-REI.C 11, A-REI.D 20, A-SSE.B 25, F-BF.A 10, F-BF.B 12 (164) | A-APR.C 5, A-APR.D 11, A-CED.A 7, A-REI.B 4, A-REI.C 10, A-REI.D 13, A-SSE.B 16, F-BF.A 20, F-BF.B 11, G-GPE.A 8, N-CN.A 6, N-CN.C 3, S-CP.B 6 (120) |
| recognition_or_interpretation | A-APR.B 9, A-REI.A 11, A-SSE.A 40, F-IF.A 41, F-IF.B 14, F-IF.C 12, F-LE.B 13, N-RN.B 6, S-ID.C 5 (151) | A-APR.B 12, A-REI.A 5, A-SSE.A 17, F-IF.A 4, F-IF.B 20, F-IF.C 10, F-LE.B 6, F-TF.A 2, S-CP.A 3, S-IC.A 4, S-IC.B 10 (93) |
| mixed | F-LE.A 18, N-Q.A 5, S-ID.A 13, S-ID.B 7 (43) | F-LE.A 9, F-TF.C 3, N-Q.A 1, N-RN.A 8, S-ID.A 10, S-ID.B 4 (35) |

## Tables

Bar (the channel bar, unchanged): n >= 10, lower 95% bootstrap CI strictly above chance (mean 1/k) and strictly above the modal key-letter frequency of that subset. Bootstrap: `score_choices_only_local_lm.bootstrap_ci`, `random.Random(21 + n)`, 1000 replicates, rows in per-item file order. `faithful` = pre-registered print-faithful verdict from `exports/print-faithful/fidelity-items.jsonl`.

### Counts

| cell | all | faithful | execution | execution and faithful | execution_strict | execution_strict and faithful | recognition_or_interpretation | recognition and faithful | mixed | mixed and faithful |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Algebra I | 358 | 184 | 164 | 75 | 133 | 66 | 151 | 83 | 43 | 26 |
| Algebra II | 248 | 115 | 120 | 56 | 86 | 41 | 93 | 38 | 35 | 21 |

### Algebra I

| model | subset | n | pass | rate | chance | 95% CI | modal (freq) | > chance | > modal | bar |
|---|---|---:|---:|---:|---:|---|---|---|---|---|
| Qwen2.5-7B | all | 358 | 139 | 0.388 | 0.250 | [0.341, 0.439] | B (0.271) | yes | yes | yes |
| Qwen2.5-7B | faithful | 184 | 86 | 0.467 | 0.250 | [0.391, 0.543] | B (0.255) | yes | yes | yes |
| Qwen2.5-7B | execution | 164 | 48 | 0.293 | 0.250 | [0.220, 0.360] | B (0.299) | no | no | no |
| Qwen2.5-7B | execution and faithful | 75 | 27 | 0.360 | 0.250 | [0.253, 0.480] | B (0.293) | yes | no | **no** |
| Qwen2.5-7B | execution_strict | 133 | 37 | 0.278 | 0.250 | [0.203, 0.353] | B (0.323) | no | no | no |
| Qwen2.5-7B | execution_strict and faithful | 66 | 23 | 0.348 | 0.250 | [0.242, 0.455] | B (0.333) | no | no | no |
| Qwen2.5-7B | recognition_or_interpretation | 151 | 66 | 0.437 | 0.250 | [0.358, 0.510] | C (0.272) | yes | yes | yes |
| Qwen2.5-7B | recognition and faithful | 83 | 43 | 0.518 | 0.250 | [0.410, 0.614] | D (0.265) | yes | yes | **yes** |
| Qwen2.5-7B | mixed | 43 | 25 | 0.581 | 0.250 | [0.442, 0.721] | C (0.302) | yes | yes | yes |
| Qwen2.5-7B | mixed and faithful | 26 | 16 | 0.615 | 0.250 | [0.423, 0.808] | C (0.346) | yes | yes | yes |
| Qwen2.5-14B | all | 358 | 149 | 0.416 | 0.250 | [0.363, 0.469] | B (0.271) | yes | yes | yes |
| Qwen2.5-14B | faithful | 184 | 79 | 0.429 | 0.250 | [0.359, 0.500] | B (0.255) | yes | yes | yes |
| Qwen2.5-14B | execution | 164 | 62 | 0.378 | 0.250 | [0.311, 0.457] | B (0.299) | yes | yes | yes |
| Qwen2.5-14B | execution and faithful | 75 | 25 | 0.333 | 0.250 | [0.240, 0.440] | B (0.293) | no | no | **no** |
| Qwen2.5-14B | execution_strict | 133 | 49 | 0.368 | 0.250 | [0.286, 0.451] | B (0.323) | yes | no | no |
| Qwen2.5-14B | execution_strict and faithful | 66 | 21 | 0.318 | 0.250 | [0.212, 0.424] | B (0.333) | no | no | no |
| Qwen2.5-14B | recognition_or_interpretation | 151 | 63 | 0.417 | 0.250 | [0.344, 0.490] | C (0.272) | yes | yes | yes |
| Qwen2.5-14B | recognition and faithful | 83 | 37 | 0.446 | 0.250 | [0.349, 0.554] | D (0.265) | yes | yes | **yes** |
| Qwen2.5-14B | mixed | 43 | 24 | 0.558 | 0.250 | [0.395, 0.698] | C (0.302) | yes | yes | yes |
| Qwen2.5-14B | mixed and faithful | 26 | 17 | 0.654 | 0.250 | [0.462, 0.846] | C (0.346) | yes | yes | yes |
| Phi-4 | all | 358 | 151 | 0.422 | 0.250 | [0.374, 0.472] | B (0.271) | yes | yes | yes |
| Phi-4 | faithful | 184 | 86 | 0.467 | 0.250 | [0.397, 0.538] | B (0.255) | yes | yes | yes |
| Phi-4 | execution | 164 | 60 | 0.366 | 0.250 | [0.293, 0.439] | B (0.299) | yes | no | no |
| Phi-4 | execution and faithful | 75 | 29 | 0.387 | 0.250 | [0.293, 0.507] | B (0.293) | yes | no (equal) | **no** |
| Phi-4 | execution_strict | 133 | 45 | 0.338 | 0.250 | [0.256, 0.421] | B (0.323) | yes | no | no |
| Phi-4 | execution_strict and faithful | 66 | 26 | 0.394 | 0.250 | [0.273, 0.500] | B (0.333) | yes | no | no |
| Phi-4 | recognition_or_interpretation | 151 | 69 | 0.457 | 0.250 | [0.377, 0.536] | C (0.272) | yes | yes | yes |
| Phi-4 | recognition and faithful | 83 | 42 | 0.506 | 0.250 | [0.398, 0.614] | D (0.265) | yes | yes | **yes** |
| Phi-4 | mixed | 43 | 22 | 0.512 | 0.250 | [0.372, 0.674] | C (0.302) | yes | yes | yes |
| Phi-4 | mixed and faithful | 26 | 15 | 0.577 | 0.250 | [0.385, 0.769] | C (0.346) | yes | yes | yes |

### Algebra II

| model | subset | n | pass | rate | chance | 95% CI | modal (freq) | > chance | > modal | bar |
|---|---|---:|---:|---:|---:|---|---|---|---|---|
| Qwen2.5-7B | all | 248 | 91 | 0.367 | 0.250 | [0.306, 0.423] | C (0.278) | yes | yes | yes |
| Qwen2.5-7B | faithful | 115 | 40 | 0.348 | 0.250 | [0.261, 0.435] | B (0.296) | yes | no | no |
| Qwen2.5-7B | execution | 120 | 47 | 0.392 | 0.250 | [0.308, 0.483] | C (0.300) | yes | yes | yes |
| Qwen2.5-7B | execution and faithful | 56 | 22 | 0.393 | 0.250 | [0.250, 0.518] | C (0.286) | no | no | **no** |
| Qwen2.5-7B | execution_strict | 86 | 34 | 0.395 | 0.250 | [0.291, 0.488] | C (0.291) | yes | no | no |
| Qwen2.5-7B | execution_strict and faithful | 41 | 17 | 0.415 | 0.250 | [0.268, 0.561] | D (0.366) | yes | no | no |
| Qwen2.5-7B | recognition_or_interpretation | 93 | 33 | 0.355 | 0.250 | [0.258, 0.441] | B (0.312) | yes | no | no |
| Qwen2.5-7B | recognition and faithful | 38 | 12 | 0.316 | 0.250 | [0.184, 0.474] | B (0.395) | no | no | no |
| Qwen2.5-7B | mixed | 35 | 11 | 0.314 | 0.250 | [0.171, 0.486] | A (0.257) | no | no | no |
| Qwen2.5-7B | mixed and faithful | 21 | 6 | 0.286 | 0.250 | [0.095, 0.476] | A (0.333) | no | no | no |
| Qwen2.5-14B | all | 248 | 89 | 0.359 | 0.250 | [0.298, 0.415] | C (0.278) | yes | yes | yes |
| Qwen2.5-14B | faithful | 115 | 44 | 0.383 | 0.250 | [0.287, 0.461] | B (0.296) | yes | no | no |
| Qwen2.5-14B | execution | 120 | 48 | 0.400 | 0.250 | [0.317, 0.475] | C (0.300) | yes | yes | yes |
| Qwen2.5-14B | execution and faithful | 56 | 23 | 0.411 | 0.250 | [0.286, 0.536] | C (0.286) | yes | no (equal) | **no** |
| Qwen2.5-14B | execution_strict | 86 | 35 | 0.407 | 0.250 | [0.302, 0.512] | C (0.291) | yes | yes | yes |
| Qwen2.5-14B | execution_strict and faithful | 41 | 16 | 0.390 | 0.250 | [0.244, 0.537] | D (0.366) | no | no | no |
| Qwen2.5-14B | recognition_or_interpretation | 93 | 31 | 0.333 | 0.250 | [0.247, 0.419] | B (0.312) | no | no | no |
| Qwen2.5-14B | recognition and faithful | 38 | 13 | 0.342 | 0.250 | [0.211, 0.500] | B (0.395) | no | no | no |
| Qwen2.5-14B | mixed | 35 | 10 | 0.286 | 0.250 | [0.143, 0.429] | A (0.257) | no | no | no |
| Qwen2.5-14B | mixed and faithful | 21 | 8 | 0.381 | 0.250 | [0.190, 0.571] | A (0.333) | no | no | no |
| Phi-4 | all | 248 | 86 | 0.347 | 0.250 | [0.286, 0.407] | C (0.278) | yes | yes | yes |
| Phi-4 | faithful | 115 | 40 | 0.348 | 0.250 | [0.270, 0.435] | B (0.296) | yes | no | no |
| Phi-4 | execution | 120 | 44 | 0.367 | 0.250 | [0.283, 0.450] | C (0.300) | yes | no | no |
| Phi-4 | execution and faithful | 56 | 19 | 0.339 | 0.250 | [0.214, 0.464] | C (0.286) | no | no | **no** |
| Phi-4 | execution_strict | 86 | 32 | 0.372 | 0.250 | [0.267, 0.477] | C (0.291) | yes | no | no |
| Phi-4 | execution_strict and faithful | 41 | 15 | 0.366 | 0.250 | [0.220, 0.512] | D (0.366) | no | no | no |
| Phi-4 | recognition_or_interpretation | 93 | 31 | 0.333 | 0.250 | [0.237, 0.441] | B (0.312) | no | no | no |
| Phi-4 | recognition and faithful | 38 | 12 | 0.316 | 0.250 | [0.184, 0.474] | B (0.395) | no | no | no |
| Phi-4 | mixed | 35 | 11 | 0.314 | 0.250 | [0.171, 0.486] | A (0.257) | no | no | no |
| Phi-4 | mixed and faithful | 21 | 9 | 0.429 | 0.250 | [0.238, 0.619] | A (0.333) | no | no | no |

Per-cluster pass counts (descriptive, no per-cluster row is a claim) are in `execution-subset-tables.md` and under `lm.<model>.cells.<cell>.perCluster` in `execution-subset.json`.

## Reading the split

- The classes are not balanced on print fidelity: in Algebra I, 75 of 164 execution items are faithful against 83 of 151 recognition items. A plausible reason, not checked here, is that execution clusters (solve, rewrite, perform operations) carry more operator-dense text, which the recent Regents PDFs encode as digits.
- Execution-tagged Algebra I items have the lowest masked-stem rates of the three classes on every model (0.293 / 0.378 / 0.366 on the full class). Withholding the givens removes what those tags ask the solver to operate on; that is the direction the reviewer's reading predicts.
- The recognition class is carried by `A-SSE.A` (interpret the structure of expressions, 40 items), `F-IF.A` (function concept and notation, 41), `F-LE.B`, and `F-IF.C`; the mixed class by `F-LE.A` (construct and compare models). Per-cluster counts are descriptive.
- The classification is of the tag's text, not of each item's demand. A cluster such as `A-REI.A` (understand and explain the reasoning in solving) sits over items that ask the solver to solve a radical equation; the split cannot see that. A finer split needs an item-level coding, which this addendum does not do.

## What a writer should cite

`execution-subset.json`: `counts.<cell>.<subset>`; `lm.<model>.cells.<cell>.subsets.<subset>` with `n`, `passes`, `passRate`, `chance`, `ci95`, `modalLetter`, `modalFrequency`, `lowerCiAboveChance`, `lowerCiAboveModal`, `clearsBar`; `lm.<model>.cells.<cell>.executionAndFaithfulClearsBar`; `clusterClasses`. Per item: `item-standards.jsonl` (`id`, `standard`, `standardAsPrinted`, `sourcePdf`, `page`, `readMethod`). Coverage: `coverage.json`. Cluster text: `standards-text.json`.

## Files

- `preregistration.md`, `preregistration.sha256`
- `item-standards.jsonl` (606 rows), `rating-guide-tables.json` (58 guides), `coverage.json`
- `standards-text.json` (33 clusters; `ccss-html/` cache gitignored)
- `execution-subset.json`, `execution-subset-tables.md`

Scripts: `scripts/extract_regents_standards.py`, `scripts/regents_glyph_reader.py`, `scripts/fetch_ccss_cluster_text.py`, `scripts/split_masked_stem_by_standard.py`. Wall: extraction 49 s, fetch 24 s, join 2 s. No GPU.
