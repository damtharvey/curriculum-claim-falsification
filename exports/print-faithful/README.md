# Print-fidelity check and rescoring on the faithful subset

Review-2 weakness 2: every claimed rate was computed on a PDF text layer that a 20-item audit found to be 8 match / 8 glue / 3 truncated / 1 wrong option set, and no confidence interval had been recomputed on a print-faithful subset. This addendum classifies all 955 items in the claimed cells as print-faithful or not with a mechanical check against a vision-language model (VLM) transcription of the printed page, then recomputes every claimed row on the faithful subset and on its complement. Preregistration: `preregistration.md`, sha256 `0211585e9361d3771e04df5e118050ede761971da286f0b1333a7aac289737d6`, frozen before the first audited or population item was scored.

## Result in one paragraph

About half of the census text layer is not print-faithful (434 faithful / 502 not faithful / 19 unverified). On the faithful subset, under the pre-registered bar:

- **Algebra I masked-stem clears for all three models** (Qwen2.5-7B 0.467 [0.391, 0.543] n=184; Qwen2.5-14B 0.429 [0.359, 0.500]; Phi-4 0.467 [0.397, 0.538]; chance 0.250; modal letter B 0.255). The faithful rate is higher than the not-faithful rate for every model, so the dirt deflated this row rather than inflating it. The post-hoc strict subset (n=149) also clears.
- **Algebra II masked-stem does not clear for any model.** Faithful n=115: 7B 0.348 [0.261, 0.435], 14B 0.383 [0.287, 0.461], Phi-4 0.348 [0.270, 0.435]. Each lower CI is above chance 0.250 but none is above the subset modal-letter frequency (B, 0.296). On the strict subset (n=88) 14B and Phi-4 do not clear chance either (lower CIs 0.239, 0.250). Point estimates are close to the original 248-item rates (0.367, 0.359, 0.347); what fails is the interval against the position baseline at half the n. This result overrides the Algebra II claim in the integration pass.
- **NY Regents geometry lower-central does not clear on the faithful subset.** Faithful n=99: 32/99 = 0.323, item CI [0.232, 0.414], chance 0.250. The pass rate is identical to the original (90/279 = 0.323) and to the not-faithful complement (58/178 = 0.326), so the dirt neither inflated nor deflated the rate; the faithful subset is too small for its lower CI to clear 0.25. The pre-registered honesty clause treats this as not clearing. On the 173 items whose parsed leading numbers agree with the print (`numeric_faithful`, the exact input of the rule) the row clears marginally (56/173 = 0.324, CI [0.254, 0.393]). This result overrides the geometry catalog claim in the integration pass.
- **EQAO grade 6 lower-central clears on the faithful subset but thinly.** Faithful n=14: 8/14 = 0.571, item CI [0.286, 0.857], chance 0.246. The post-hoc strict subset (n=10) does not clear (5/10, CI [0.200, 0.800]). On `numeric_faithful` (n=32) it clears (16/32 = 0.500, CI [0.344, 0.688]). Report as clearing with n=14 and say so.
- Phi-4 geometry masked-stem (not claimed) clears on faithful (0.422 [0.330, 0.514] n=109, modal B 0.303) and strict subsets. It stays unclaimed; this addendum does not promote it.

Faithful fraction per claimed cell: Algebra I 0.523, Algebra II 0.481, geometry lower-central 0.357, EQAO grade 6 0.368.

## What the text layer gets wrong

Categories over the 521 not-faithful or unverified items (unique rows; the per-cell table below double counts the 136 items shared by the two geometry cells): `ocr_glue` 241 (page footers, diagram labels, table cells, or the next item glued onto an option or the stem), `wrong_item` 230 (option set or stem does not match the printed item, including entire option sets attached to the wrong question and the recent Regents encoding of `=`, `+`, `-` as the digits `5`, `1`, `2`), `truncated` 29 (lost fractions, radicals, minus signs, or option letters), `option_mismatch` 2, unverified 19 (the VLM returned unparseable JSON, no options, or a degenerate output). Of the 230 `wrong_item` rows, 130 have every failing option agree with the print on letters and differ only in digits (the operator-as-digit encoding); 100 differ in content. Regents administrations from 2023 onward are mostly not faithful (Algebra I 2023+: 44 faithful, 83 not; Algebra II 2023+: 28 faithful, 78 not), because those PDFs encode operators as digits.

A consequence for reading the faithful subset: it is not a random subsample. In Algebra I, 40 percent of faithful items have word options against 10 percent of not-faithful items, and pre-2023 administrations dominate. The faithful subset answers whether the claimed effect exists on items whose text is what students saw; it does not estimate the rate on the full item population.

## Method

- Model: `Qwen/Qwen2-VL-7B-Instruct`, revision `eed13092ef92e448dd6875b2a00151bd3f7db0ac` (the model used in `exports/addendum-vlm/`), bf16, `device_map="cuda"`, greedy, `max_new_tokens=640`, seed 20260916, RTX 5090. The model is asked to transcribe the stem and the options of item `qnum` from a page image; it is never asked to solve or to pick a letter. Prompt verbatim in `preregistration.md`.
- Pages: source PDFs under `data/raw/`, rendered with pymupdf at 150 DPI. Regents: crop from the bare-number question heading to the next heading (continuation image when the item runs onto the next page; 12 cases). EQAO: the full page whose text best matches the census stem and options. PNGs under `pages/` (gitignored like the other page renders; recreate with `scripts/run_print_fidelity_check.py --stage census --force-render`).
- Fidelity score: both sides normalized identically (NFKC, LaTeX commands removed except trig and log names, subscripts and braces removed, unit words to symbols, letter-digit boundaries split, alphanumeric tokens, `sqrt pi percent degree degrees minus` dropped). Stem: token precision (share of text-layer tokens present in the transcription), recall (share of transcription tokens present in the text layer), F1. Option: 1 if the compact strings are equal, else max(token F1, character-level `SequenceMatcher` ratio). Control characters and operator glyphs do not count; a digit standing in for an operator does count.
- Verdict (pre-registered thresholds, kept after calibration): `faithful` iff stem F1 >= 0.8 with precision >= 0.8 and recall >= 0.8, every option score >= 0.9, and the option counts agree. `unverified` iff the VLM output is unparseable, has no options, or has an empty stem. Otherwise `not_faithful`, with flags `stem_glue` / `stem_truncated` / `option_glue` / `option_truncated` / `option_count_mismatch` / `wrong_option_set`.
- Development: prompt, locator, parser, and normalization were tuned on 40 items outside the population and the audit (`dev-items.jsonl`, stage `dev`) before the preregistration was frozen.
- Rescoring: pure Python, no LM rerun. Catalog rows rerun `addendum_lib.middle_value_option` through `score_program` and `summarize_scored` (item bootstrap mulberry32 seed 11, 1000 replicates; cluster bootstrap by administration seed 20260916, 2000 replicates). LM rows use the saved per-item predictions in `exports/addendum-gpu/masked-stem-7b-items.jsonl`, `masked-stem-14b-items.jsonl`, `masked-stem-phi4-items.jsonl` (seed 20260916), the same percentile bootstrap as the addendum (`random.Random(21 + n)`, 1000 replicates, rows in per-item file order), and the modal key letter recomputed on each subset. The `original` rows reproduce the addendum numbers exactly.

## Calibration against the 20-item hand audit

Scored first, before the census. Rows: hand label from `exports/print-audit/audit.json`; columns: machine category.

| hand label | match | ocr_glue | truncated | wrong_item | option_mismatch | vlm_unparseable | vlm_no_options |
|---|---:|---:|---:|---:|---:|---:|---:|
| match (8) | 6 | 0 | 0 | 1 | 0 | 0 | 1 |
| ocr_glue (8) | 0 | 6 | 0 | 2 | 0 | 0 | 0 |
| truncated (3) | 1 | 1 | 0 | 1 | 0 | 0 | 0 |
| wrong_item (1) | 0 | 0 | 0 | 1 | 0 | 0 | 0 |

Binary agreement (hand match vs machine faithful; hand dirty vs machine not faithful): **17 of 20**, above the pre-registered floor of 16, so the thresholds were not adjusted (the declared grid gave 16 or 17 at every point). The three disagreements:

- `nyregents-algebra-i-2026-aug-q20`: hand `match`, machine `not_faithful`. Pre-declared in the preregistration: the census writes `g(x) 5 |x 1 4| 2 5` for `g(x) = |x + 4| - 5`; the hand audit forgave the encoding, this check does not.
- `nyregents-algebra-i-2023-jan-q8`: hand `truncated`, machine `faithful`. The hand label is an audit artifact: `print_page_audit.py` wrote a 400-character preview of the stem into `audit.json`, and the hand check read the preview as a cut stem. The stem in `data/items.jsonl` is 549 characters and complete; the transcription matches it (stem F1 0.99, all options 1.0). The audit's counts are therefore 9 match / 8 glue / 2 truncated / 1 wrong.
- `nyregents-algebra-i-2025-jan-q10`: hand `match`, machine `unverified`. The VLM put the four options inside the stem and returned no `options` key. Counted as unverified, not as dirty.

Category-level agreement is 13 of 20; the hand audit and the machine agree on the binary question and mostly on glue, and disagree on how to label an item that has both glue and a changed option set (the machine says `wrong_item` when fewer than half the options match).

## Two post-hoc checks (disclosed, not pre-registered)

1. **Strict faithful.** During the census it became clear that the pre-registered option score lets a one-digit change inside a long option pass through the character-ratio branch (`24 and 4, only` for `-4 and 4, only` scores 0.947). `faithful_strict` additionally drops any faithful item whose text-layer stem or option carries a digit token absent from the transcription (85 of 434 faithful items). Every conclusion above is stated for both the pre-registered and the strict subset; the two agree on every claimed row except EQAO grade 6, where strict (n=10) does not clear.
2. **Locator repair.** The pre-registered Regents heading pattern accepts a diagram label such as `8 cm` in the left column as the heading of question 8. Requiring an uppercase letter, `(` or a quote after the number changes the crop of 12 of 915 Regents items; re-transcribing those 12 (`scripts/relocate_print_fidelity_items.py`, `relocated-items.jsonl`) changes 3 verdicts, one of them to `faithful` (`nyregents-geometry-2019-aug-q17`). The `faithful_after_relocation` rows show the effect: geometry lower-central 32/100, CI [0.230, 0.410], still not clearing.

Other known limits of the check, all in the conservative direction (they move items out of the faithful subset, never into it): VLM misreads (a dropped repeated digit in a set, a dropped `P(x) =` prefix), EQAO accessibility alt text that the normalization does not fold (`(2, negative 6)` for `(2, -6)`; `Formula: 3 x minus 6 is greater than 30`), and 19 unverified outputs.

## Tables

### Faithful fraction per cell

| cell | n | faithful (pre-registered) | faithful, strict (post hoc) | not faithful | unverified | faithful fraction | categories (not faithful and unverified) |
|---|---:|---:|---:|---:|---:|---:|---|
| `nyregents::algebra-i::masked-stem-primary` | 358 | 184 | 149 | 168 | 6 | 0.523 | ocr_glue 54, option_mismatch 1, truncated 10, vlm_no_options 1, vlm_unparseable 5, wrong_item 103 |
| `nyregents::algebra-ii::masked-stem-primary` | 248 | 115 | 88 | 124 | 9 | 0.481 | ocr_glue 50, option_mismatch 1, truncated 4, vlm_no_options 1, vlm_unparseable 8, wrong_item 69 |
| `nyregents::geometry::lower-central-fired` | 279 | 99 | 80 | 178 | 2 | 0.357 | ocr_glue 116, truncated 12, vlm_unparseable 2, wrong_item 50 |
| `eqao::g6::lower-central-fired` | 40 | 14 | 10 | 24 | 2 | 0.368 | ocr_glue 17, truncated 1, vlm_unparseable 2, wrong_item 6 |
| `nyregents::geometry::masked-stem-primary` | 166 | 109 | 93 | 57 | 0 | 0.657 | ocr_glue 24, truncated 12, wrong_item 21 |

Faithful fraction = faithful / (faithful + not faithful). The two geometry cells share 136 items.

### Catalog rows (lower-central, `middle_value_option`)

Bar: n >= 10 and item bootstrap lower CI above chance (the paper's per-cell witness bar). `numeric_faithful`: the leading number the rule parses from each text-layer option equals the one parsed from the transcription and the counts agree.

| cell | subset | n | pass | rate | chance | item 95% CI | cluster 95% CI | item bar |
|---|---|---:|---:|---:|---:|---|---|---|
| NY Regents geometry | original | 279 | 90 | 0.323 | 0.250 | [0.269, 0.380] | [0.265, 0.374] | yes |
| NY Regents geometry | faithful | 99 | 32 | 0.323 | 0.250 | [0.232, 0.414] | [0.227, 0.414] | **no** |
| NY Regents geometry | faithful_after_relocation | 100 | 32 | 0.320 | 0.250 | [0.230, 0.410] | [0.225, 0.409] | no |
| NY Regents geometry | faithful_strict | 80 | 26 | 0.325 | 0.250 | [0.225, 0.425] | [0.210, 0.430] | no |
| NY Regents geometry | faithful_digit_suspect | 19 | 6 | 0.316 | 0.250 | [0.105, 0.526] | [0.100, 0.588] | no |
| NY Regents geometry | not_faithful | 178 | 58 | 0.326 | 0.250 | [0.253, 0.399] | [0.251, 0.401] | yes |
| NY Regents geometry | numeric_faithful | 173 | 56 | 0.324 | 0.250 | [0.254, 0.393] | [0.239, 0.404] | yes |
| NY Regents geometry | numeric_not_faithful | 104 | 34 | 0.327 | 0.250 | [0.231, 0.423] | [0.257, 0.394] | no |
| NY Regents geometry | unverified | 2 | 0 | 0.000 | 0.250 | [0.000, 0.000] | [0.000, 0.000] | no |
| EQAO grade 6 | original | 40 | 20 | 0.500 | 0.254 | [0.350, 0.650] | [0.417, 0.588] | yes |
| EQAO grade 6 | faithful | 14 | 8 | 0.571 | 0.246 | [0.286, 0.857] | [0.400, 0.714] | yes (thin) |
| EQAO grade 6 | faithful_strict | 10 | 5 | 0.500 | 0.245 | [0.200, 0.800] | [0.333, 0.600] | no |
| EQAO grade 6 | faithful_digit_suspect | 4 | 3 | 0.750 | 0.250 | [0.250, 1.000] | [0.500, 1.000] | no |
| EQAO grade 6 | not_faithful | 24 | 11 | 0.458 | 0.258 | [0.250, 0.667] | [0.400, 0.500] | no |
| EQAO grade 6 | numeric_faithful | 32 | 16 | 0.500 | 0.248 | [0.344, 0.688] | [0.333, 0.643] | yes |
| EQAO grade 6 | numeric_not_faithful | 6 | 3 | 0.500 | 0.283 | [0.167, 0.833] | [0.000, 1.000] | no |
| EQAO grade 6 | unverified | 2 | 1 | 0.500 | 0.250 | [0.000, 1.000] | [0.000, 1.000] | no |

### LM masked-stem rows (saved per-item predictions, seed 20260916)

Bar: n >= 10, lower CI above chance (mean 1/k), and lower CI above the modal key-letter frequency of that subset. `trailing_junk_only`: not faithful only because an option carries trailing junk after the printed content (the footer-glue pattern); reported so a reader sees whether that glue moved the rate.

| model | cell | subset | n | pass | rate | chance | 95% CI | modal letter (freq, this subset) | lower CI > chance | lower CI > modal | bar cleared |
|---|---|---|---:|---:|---:|---:|---|---|---|---|---|
| Qwen2.5-7B-Instruct | Algebra I | original | 358 | 139 | 0.388 | 0.250 | [0.341, 0.439] | B (0.271) | yes | yes | yes |
| Qwen2.5-7B-Instruct | Algebra I | faithful | 184 | 86 | 0.467 | 0.250 | [0.391, 0.543] | B (0.255) | yes | yes | **yes** |
| Qwen2.5-7B-Instruct | Algebra I | faithful_strict | 149 | 69 | 0.463 | 0.250 | [0.376, 0.544] | C (0.275) | yes | yes | yes |
| Qwen2.5-7B-Instruct | Algebra I | faithful_digit_suspect | 35 | 17 | 0.486 | 0.250 | [0.314, 0.657] | D (0.371) | yes | no | no |
| Qwen2.5-7B-Instruct | Algebra I | not_faithful | 168 | 49 | 0.292 | 0.250 | [0.220, 0.363] | C (0.286) | no | no | no |
| Qwen2.5-7B-Instruct | Algebra I | trailing_junk_only | 11 | 2 | 0.182 | 0.250 | [0.000, 0.455] | A (0.364) | no | no | no |
| Qwen2.5-7B-Instruct | Algebra I | unverified | 6 | 4 | 0.667 | 0.250 | [0.333, 1.000] | B (0.500) | no | no | no |
| Qwen2.5-7B-Instruct | Algebra II | original | 248 | 91 | 0.367 | 0.250 | [0.306, 0.423] | C (0.278) | yes | yes | yes |
| Qwen2.5-7B-Instruct | Algebra II | faithful | 115 | 40 | 0.348 | 0.250 | [0.261, 0.435] | B (0.296) | yes | no | **no** |
| Qwen2.5-7B-Instruct | Algebra II | faithful_strict | 88 | 31 | 0.352 | 0.250 | [0.261, 0.455] | B (0.295) | yes | no | no |
| Qwen2.5-7B-Instruct | Algebra II | faithful_digit_suspect | 27 | 9 | 0.333 | 0.250 | [0.185, 0.519] | B (0.296) | no | no | no |
| Qwen2.5-7B-Instruct | Algebra II | not_faithful | 124 | 49 | 0.395 | 0.250 | [0.306, 0.476] | C (0.323) | yes | no | no |
| Qwen2.5-7B-Instruct | Algebra II | trailing_junk_only | 6 | 2 | 0.333 | 0.250 | [0.000, 0.667] | C (0.500) | no | no | no |
| Qwen2.5-7B-Instruct | Algebra II | unverified | 9 | 2 | 0.222 | 0.250 | [0.000, 0.444] | A (0.333) | no | no | no |
| Qwen2.5-14B-Instruct | Algebra I | original | 358 | 149 | 0.416 | 0.250 | [0.363, 0.469] | B (0.271) | yes | yes | yes |
| Qwen2.5-14B-Instruct | Algebra I | faithful | 184 | 79 | 0.429 | 0.250 | [0.359, 0.500] | B (0.255) | yes | yes | **yes** |
| Qwen2.5-14B-Instruct | Algebra I | faithful_strict | 149 | 66 | 0.443 | 0.250 | [0.369, 0.517] | C (0.275) | yes | yes | yes |
| Qwen2.5-14B-Instruct | Algebra I | faithful_digit_suspect | 35 | 13 | 0.371 | 0.250 | [0.200, 0.543] | D (0.371) | no | no | no |
| Qwen2.5-14B-Instruct | Algebra I | not_faithful | 168 | 66 | 0.393 | 0.250 | [0.321, 0.464] | C (0.286) | yes | yes | yes |
| Qwen2.5-14B-Instruct | Algebra I | trailing_junk_only | 11 | 5 | 0.455 | 0.250 | [0.182, 0.727] | A (0.364) | no | no | no |
| Qwen2.5-14B-Instruct | Algebra I | unverified | 6 | 4 | 0.667 | 0.250 | [0.333, 1.000] | B (0.500) | no | no | no |
| Qwen2.5-14B-Instruct | Algebra II | original | 248 | 89 | 0.359 | 0.250 | [0.298, 0.415] | C (0.278) | yes | yes | yes |
| Qwen2.5-14B-Instruct | Algebra II | faithful | 115 | 44 | 0.383 | 0.250 | [0.287, 0.461] | B (0.296) | yes | no | **no** |
| Qwen2.5-14B-Instruct | Algebra II | faithful_strict | 88 | 30 | 0.341 | 0.250 | [0.239, 0.432] | B (0.295) | no | no | no |
| Qwen2.5-14B-Instruct | Algebra II | faithful_digit_suspect | 27 | 14 | 0.519 | 0.250 | [0.333, 0.704] | B (0.296) | yes | yes | yes |
| Qwen2.5-14B-Instruct | Algebra II | not_faithful | 124 | 42 | 0.339 | 0.250 | [0.250, 0.419] | C (0.323) | no | no | no |
| Qwen2.5-14B-Instruct | Algebra II | trailing_junk_only | 6 | 2 | 0.333 | 0.250 | [0.000, 0.667] | C (0.500) | no | no | no |
| Qwen2.5-14B-Instruct | Algebra II | unverified | 9 | 3 | 0.333 | 0.250 | [0.000, 0.667] | A (0.333) | no | no | no |
| Phi-4 | Algebra I | original | 358 | 151 | 0.422 | 0.250 | [0.374, 0.472] | B (0.271) | yes | yes | yes |
| Phi-4 | Algebra I | faithful | 184 | 86 | 0.467 | 0.250 | [0.397, 0.538] | B (0.255) | yes | yes | **yes** |
| Phi-4 | Algebra I | faithful_strict | 149 | 68 | 0.456 | 0.250 | [0.369, 0.530] | C (0.275) | yes | yes | yes |
| Phi-4 | Algebra I | faithful_digit_suspect | 35 | 18 | 0.514 | 0.250 | [0.343, 0.686] | D (0.371) | yes | no | no |
| Phi-4 | Algebra I | not_faithful | 168 | 61 | 0.363 | 0.250 | [0.292, 0.440] | C (0.286) | yes | yes | yes |
| Phi-4 | Algebra I | trailing_junk_only | 11 | 4 | 0.364 | 0.250 | [0.091, 0.636] | A (0.364) | no | no | no |
| Phi-4 | Algebra I | unverified | 6 | 4 | 0.667 | 0.250 | [0.333, 1.000] | B (0.500) | no | no | no |
| Phi-4 | Algebra II | original | 248 | 86 | 0.347 | 0.250 | [0.286, 0.407] | C (0.278) | yes | yes | yes |
| Phi-4 | Algebra II | faithful | 115 | 40 | 0.348 | 0.250 | [0.270, 0.435] | B (0.296) | yes | no | **no** |
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

Against the original population modal frequency (Algebra II C 0.278) instead of the subset modal, Algebra II faithful would clear for 14B only (lower CI 0.287) and not for 7B (0.261) or Phi-4 (0.270). The pre-registered bar uses the subset modal, and the README reports the failure.

## What a writer should cite

`rescored-rows.json`:

- `cells.<cell>.faithful`, `.notFaithful`, `.unverified`, `.faithfulFraction`, `.categories`
- `catalog.<cell>.subsets.{original,faithful,faithful_strict,not_faithful,numeric_faithful}` with `n`, `passes`, `passRate`, `chance`, `itemCi95`, `clusterCi95`, `clearsItemBar`
- `lm.<model>.cells.<cell>.subsets.{original,faithful,faithful_strict,not_faithful,trailing_junk_only}` with `n`, `passes`, `passRate`, `chance`, `ci95`, `modalLetter`, `modalFrequency`, `clearsBar`
- `claimedRowsFailingOnFaithfulSubset`
- `calibration.binaryAgreement` (17 of 20)

Per item: `fidelity-items.jsonl` (`id`, `cells`, `stem_f1`, `stem_precision`, `stem_recall`, `option_match`, `printed_option_count`, `text_layer_option_count`, `flags`, `verdict`, `category`, `numeric_faithful`, `trailing_junk_only`, `rawVlm`, `vlmStem`, `vlmOptions`, `textLayerStem`, `textLayerOptions`, `pngs`). Calibration detail: `calibration.json`. Population: `population.json`. Post-hoc locator repair: `relocated-items.jsonl`.

## Files

- `preregistration.md`, `preregistration.sha256`
- `population.json` (955 ids with cell membership)
- `dev-items.jsonl` (40 development items, outside the population)
- `calibration.json` (20 audited items, confusion matrices, threshold grid)
- `fidelity-items.jsonl` (955 rows, stages `calibration` and `census`), `census-summary.json`
- `relocated-items.jsonl` (12 re-transcribed rows, post hoc)
- `rescored-rows.json`, `rescored-tables.md`
- `pages/` (local, gitignored)

Scripts: `scripts/print_fidelity_lib.py`, `scripts/run_print_fidelity_check.py --stage dev|calibration|census`, `scripts/relocate_print_fidelity_items.py`, `scripts/rescore_print_faithful_rows.py`. GPU wall: development 3 x 70 s, calibration 36 s, census 1560 s, relocation 36 s.
