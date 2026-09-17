# Print-fidelity check of the census text layer (preregistration)

- Written: 2026-09-17T04:35Z, before any scoring of audited or population items.
- Purpose: review-2 weakness 2. The 20-item printed-page audit (`exports/print-audit/audit.json`, seed 20260916) found the census text layer to be 8 match / 8 glue / 3 truncated / 1 wrong option set. Every claimed rate (catalog lower-central rows, LM masked-stem Algebra I and II rows) was computed on that layer. This addendum classifies every item in the claimed cells as print-faithful or not with a mechanical check against a vision-language model (VLM) transcription of the printed page, then recomputes the claimed rates and confidence intervals on the faithful subset and on its complement.
- Scoring of the 20 audited items and of the population starts only after `preregistration.sha256` records the sha256 of this file. The runner refuses to score if the file has changed.
- One-sided wording (locked): a pass does not require the tagged operation. Nothing here says students did not learn.
- Does not edit `paper/`. Writes only to `exports/print-faithful/` and `scripts/`.

## Development set (disclosed)

Before this file was frozen, the prompt, page locator, JSON parser, and normalization rules were developed on 40 items that are outside the population and outside the 20-item audit: 10 each from NY Regents Algebra I, Algebra II, geometry, and EQAO (grades 3 and 9), drawn with `random.Random(20260916)` from selected-response items not in the population. Their transcriptions and scores are in `dev-items.jsonl` (stage `dev`). Nothing in the development set enters calibration, the census, or any rate below.

## Population (locked)

Every item in the claimed cells, from `data/items.jsonl` and the existing exports:

| cell label | definition | n |
|---|---|---:|
| `nyregents::algebra-i::masked-stem-primary` | Algebra I ids in `exports/addendum-gpu/masked-stem-algebra-primary-item-ids.json` (`masked_token_count >= 1`) | 358 |
| `nyregents::algebra-ii::masked-stem-primary` | Algebra II ids in the same file | 248 |
| `nyregents::geometry::lower-central-fired` | NY Regents geometry selected-response items on which `scripts/addendum_lib.py` `middle_value_option` fires (the claimed catalog row, 90/279) | 279 |
| `eqao::g6::lower-central-fired` | EQAO grade 6 selected-response items on which `middle_value_option` fires (the claimed catalog row, 20/40) | 40 |
| `nyregents::geometry::masked-stem-primary` | geometry ids in `exports/addendum-gpu/masked-stem-primary-item-ids.json` (the unclaimed Phi-4 cell) | 166 |

Union: 955 items (136 geometry items are in both geometry cells). All 955 have a source PDF under `data/raw/`. Membership is written to `population.json`.

## Model (locked)

- `Qwen/Qwen2-VL-7B-Instruct`, local snapshot revision `eed13092ef92e448dd6875b2a00151bd3f7db0ac` (the model used in `exports/addendum-vlm/`). `Qwen2VLForConditionalGeneration`, `torch.bfloat16`, `device_map="cuda"`, `attn_implementation="sdpa"`, `local_files_only=True`. CUDA required; no CPU path.
- Greedy decoding (`do_sample=False`), `max_new_tokens=640`, seed 20260916. The model is never asked to solve or to pick an answer.

## Page images (locked)

- Source PDFs already on disk under `data/raw/`, rendered with pymupdf at 150 DPI. No OCR engine and no PDF text layer is used as the transcription.
- NY Regents: on every page, find bare-number question headings in the left column (a line matching `^{qnum}(?!\d)\s+[A-Za-z("“]`; option labels such as `(1)` are not headings). Crop from that heading to the next heading `qnum+1` on the same page (8 pt pad), or to the page bottom. If several headings match, keep the crop whose text contains the most census stem words (ties broken by census option words). If the crop runs to the page bottom and the heading for `qnum+1` on the following page sits more than 150 pt below the top, a second image of that page from the top to that heading is attached (continuation).
- EQAO: the full page whose text contains the most census stem words and option words (these PDFs do not carry parseable question headings). The prompt names the item by its printed number.
- Item number: the `-q<n>` suffix of the item id.

## Transcription prompt (locked)

One user message, the page image(s) followed by this text with `{qnum}` replaced:

```
You are a transcription tool. Do not solve the problem and do not say which option is correct.

The image shows part of a printed exam page. Transcribe only the multiple-choice item numbered {qnum}. Ignore page headers, page footers, other items, and the words "Use this space for computations".

Transcribe exactly what is printed:
1. "stem": the question text of item {qnum}, from the first word after the item number up to the last word before the first answer option, including any sentence that continues after a diagram or table. Do not put any answer option inside the stem. If the item has a table, transcribe the table cells row by row inside the stem. Do not describe diagrams, graphs, or pictures, and do not transcribe labels that appear only inside a diagram or graph.
2. "options": every printed answer option of item {qnum}, keyed by its printed label exactly as printed ("1", "2", "3", "4" or "A", "B", "C", "D", "E"). Write each option's content exactly as printed, as one JSON string per option; if an option spans several lines, join the lines with "; ". Do not add options that are not printed. Do not omit any printed option.

Write mathematics in plain text: exponents as x^2, fractions as 5/3, mixed numbers as 2 1/3, roots as sqrt(10), coordinates as (-1, -3), subscripts as a_n, and keep symbols such as degrees, pi, <=, >=, and the minus sign as printed.

Reply with a JSON object and nothing else:
{"stem": "...", "options": {"1": "...", "2": "...", "3": "...", "4": "..."}}
```

Parser: strip an optional markdown fence; `json.JSONDecoder.raw_decode` from the first `{`. If that fails, double any backslash that starts a two-or-more-letter LaTeX command or an invalid JSON escape and decode once more; a second failure is `unverified`. Option labels `1..5` map to `A..E`, `F/G/H/J/K` map to `A..E`, `A..E` stay. Empty option strings are dropped.

Transcription stem post-processing (deterministic, from the model's own output): strip a leading item number; remove bracketed descriptions containing diagram / graph / figure / image / picture / table / chart / drawing / shown / axes / number line / dot plot / box plot; if two or more of the model's own transcribed options (each with at least two tokens) appear verbatim inside the stem, cut the stem at the first such echo.

## Fidelity score (locked)

Normalization applied identically to the text layer and to the transcription: Unicode NFKC; LaTeX commands `\name` become spaces except `sin cos tan sec csc cot arcsin arccos arctan log ln`, which become that word; `_ { }` removed; lowercase; unit words rewritten to symbols (`degrees celsius -> c`; `square <unit>` and `<unit> squared -> <unit> 2`; `cubic <unit>` and `<unit> cubed -> <unit> 3`; centimetre(s)/centimeter(s) `cm`, millimetre(s) `mm`, kilometre(s) `km`, metre(s)/meter(s) `m`, kilogram(s) `kg`, milligram(s) `mg`, gram(s) `g`, millilitre(s) `ml`, litre(s)/liter(s) `l`, inch(es) `in`, feet/foot `ft`); a space inserted at every letter-digit boundary; tokens are maximal `[a-z0-9]+` runs; the tokens `sqrt pi percent degree degrees minus` are dropped from both sides. Control characters, operator glyphs, and punctuation therefore do not count; a digit standing in for an operator (the recent Regents encoding of `=`, `+`, `-` as `5`, `1`, `2`) does count, because it changes the numeric content that the catalog rule parses and that the LM reads.

Per item:

- Stem: multiset token precision P = share of text-layer stem tokens present in the transcription stem; recall R = share of transcription stem tokens present in the text-layer stem; F1 = 2PR/(P+R).
- Each option letter present in the text layer: score = 1 if the compact normalized strings are equal, else max(token F1, `difflib.SequenceMatcher` ratio on the compact normalized strings). A letter absent from the transcription scores 0.
- Printed option count = number of transcribed option letters with non-empty content; text-layer option count = number of census choices.

Thresholds (declared here):

- Stem passes iff F1 >= 0.8 and P >= 0.8 and R >= 0.8.
- An option matches iff its score >= 0.9.
- `faithful` iff the stem passes, every text-layer option matches, and the option counts are equal.
- `unverified` iff the model output is unparseable, has no options, or has an empty stem. These items are excluded from both the faithful and the not-faithful subsets and their count is reported.
- Otherwise `not_faithful`.

Flags (recorded for every scored item): `stem_glue` if stem P < 0.8 (text-layer stem carries tokens absent from the print); `stem_truncated` if stem R < 0.8 (the print carries content absent from the text layer); `option_glue` / `option_truncated` for the same tests on any option with a non-empty transcription; `option_count_mismatch`; `wrong_option_set` if fewer than half the options (rounded up) match. Category for the confusion matrix: `match` if faithful; else `wrong_item` if `wrong_option_set`; else `ocr_glue` if any glue flag; else `truncated` if any truncated flag or missing/extra option letters; else `option_mismatch`.

Two secondary per-item indicators, also recorded: `numeric_faithful` (the leading number that `addendum_lib.parse_leading_number` reads from each text-layer option equals the one read from the transcription, and the counts agree; this is the exact input of the lower-central rule) and `trailing_junk_only` (not faithful, stem passes, counts agree, and every transcribed option is a token prefix of its text-layer option; the footer-glue pattern).

## Calibration (locked)

Step 1. Score the 20 audited items first (all are in the population). Report the 4 x 6 confusion matrix between the hand label (`match`, `ocr_glue`, `truncated`, `wrong_item`) and the machine category, and the binary agreement (hand `match` vs machine `faithful`; hand non-match vs machine `not_faithful`; `unverified` counted separately).

Step 2. If binary agreement on the 20 is at least 16, the thresholds above are final. If it is below 16, the thresholds may be adjusted once, to the grid point in stem F1 in {0.7, 0.8, 0.9} x option match in {0.8, 0.9} with the highest binary agreement (ties to the stricter pair), and the census runs with that setting. The normalization rules, prompt, and locator are not adjusted after calibration. The default and the chosen matrices are both written to `calibration.json`.

Expected disagreement, stated in advance: the hand audit labelled `nyregents-algebra-i-2026-aug-q20` `match` while noting that the census encodes `=` as `5`; this check counts that encoding as infidelity, so that item is expected to come out `not_faithful`.

## Census (locked)

Score every remaining population item with the calibrated thresholds. Resume-safe by item id. Per-item rows go to `fidelity-items.jsonl` with `id`, `cells`, `stem_f1`, `stem_precision`, `stem_recall`, `option_match`, `printed_option_count`, `text_layer_option_count`, `flags`, `verdict`, `category`, `numeric_faithful`, `trailing_junk_only`, the raw model output, the transcription, the text-layer stem and options, and the page image paths.

## Rescoring (locked)

All rescoring is pure Python from `scripts/`. No LM is rerun: per-item predictions for every claimed LM row exist on disk (`exports/addendum-gpu/masked-stem-7b-items.jsonl`, `masked-stem-14b-items.jsonl`, `masked-stem-phi4-items.jsonl`; fields `id`, `chosen_letter`, `key`, `correct`, `n_options`), produced under the frozen masked-stem preregistration with seed 20260916.

Catalog rows (`nyregents::geometry` and `eqao::g6`, lower-central): rerun `middle_value_option` through `addendum_lib.score_program` and `summarize_scored` on (a) the faithful items of the cell, (b) the not-faithful items, (c) the original fired set. Report n, passes, pass rate, chance (mean 1/k), item bootstrap 95% CI (mulberry32 seed 11, 1000 replicates, as in the paper), clustered bootstrap 95% CI by administration (seed 20260916, 2000 replicates). Bar: n >= 10 and item lower CI above chance, the paper's per-cell witness bar. Secondary: the same on the `numeric_faithful` items.

LM rows (Qwen2.5-7B-Instruct, Qwen2.5-14B-Instruct, Phi-4; Algebra I and Algebra II primary populations; Phi-4 geometry reported as the unclaimed cell): for (a) faithful, (b) not faithful, (c) the original population, report n, passes, pass rate, chance (mean 1/k), percentile bootstrap 95% CI (`random.Random(21 + n)`, 1000 replicates, the same function as the addendum), the modal key letter and its frequency computed on that subset, and the original population modal frequency. Bar: n >= 10, lower CI above chance, lower CI above the subset modal-letter frequency. Secondary: rates on `trailing_junk_only` items and on `unverified` items, so a reader sees whether footer glue moved the rate.

Faithful fraction per cell = faithful / (faithful + not faithful), with the unverified count alongside.

## Honesty clause (locked)

If the faithful-subset rate for any claimed row does not clear its bar, the README says so plainly in its first section, and that result overrides the claim in the integration pass. Wide intervals from a small faithful n are reported as not clearing, not as clearing.

## Outputs

`exports/print-faithful/`: this file, `preregistration.sha256`, `population.json`, `dev-items.jsonl`, `calibration.json`, `fidelity-items.jsonl`, `census-summary.json`, `rescored-rows.json`, `README.md`, page PNGs under `pages/`. Scripts: `scripts/print_fidelity_lib.py`, `scripts/run_print_fidelity_check.py`, `scripts/rescore_print_faithful_rows.py`.
