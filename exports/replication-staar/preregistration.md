# STAAR replication set — preregistration

- Written: 2026-09-16T21:20:00Z
- Scoring and replication-form parsing start only after `preregistration.md.sha256` records the sha256 of this file
- Frozen discovery census (read only): `data/items.jsonl` (2405 items; STAAR 445; forms `staar-{year}-{grade}-qN` for English 2019, 2021, 2022, grades 3–8 and Algebra I)
- Frozen discovery results (read only): `exports/addendum-strategies/README.md`, `s3-closure.json`, `s3-teks-g5-robustness.json`, `exports/apriori-cell-table.json`, `exports/rule-chance.json`
- Inventory (written before this file; no item parse): `exports/replication-staar/inventory.json` (writtenAt 2026-09-16T21:16:52Z)
- Replication items go to `exports/replication-staar/items.jsonl` only. Do not append to `data/items.jsonl`
- One-sided claim shape (locked): a pass does not require the tagged operation; failure to find a witness does not certify the tag; we never say students did not learn
- Parser: `scripts/parse_staar_bulk.py` reused. If a new form's key table does not match `KEY_FLAT`, a minimal regex extension is allowed and must be recorded in `results.json` `parserChanges`. Do not guess keys
- No neural model. Text layer only (pymupdf, same as the parser)

## Inventory freeze (candidates)

Text-extractable English test+key pairs whose (year, grade) is absent from the census. Priority order: grade 5, then 3, 4, 6, 7, 8, Algebra I.

Registered replication forms (10):

1. staar-2013-5-english
2. staar-2014-5-english
3. staar-2016-5-english
4. staar-2014-3-english
5. staar-2016-4-english
6. staar-2014-6-english
7. staar-2016-6-english
8. staar-2016-7-english
9. staar-2013-8-english
10. staar-2014-alg1-english

Cut, not scored:

- Census English 2019/2021/2022 (already in discovery)
- Spanish of census years (same administration, other language)
- Spanish of other years (not in the registered English set)
- Samplers, practice, redesign, rationales, item-analysis, expectations
- Image-only or unreadable PDFs (10 scanned/image-only test-or-key files; 8 files of exactly 1,048,576 bytes, treated as truncated)
- Test without key (all 2015 English tests; 2023–2026 keys on disk have no matching test PDF)
- Key without extractable test (2013-3, 2013-4, 2013-6, 2013-7, 2013-alg1, 2014-4, 2014-7, 2015-alg1, 2016-3)
- 2017, 2018, 2020: no complete pair on disk

Grade 5 is the primary cell. All 10 forms are parsed. Rules that name a grade are scored only on that grade's replication items.

## Chance, CI, witness bar

- Chance is 1/k per item, k = number of choices. Cell chance is the mean of 1/k over scored items
- Selected-response only. Numeric-constructed items are parsed into the jsonl but are not scored
- 95% percentile bootstrap CI: `random.Random.randrange`, 1000 replicates, seed 11, same indexing as `scripts/score_choices_only.py`: sort the 1000 rates; lower = index `int(0.025 * (1000 - 1))`; upper = index `int(0.975 * (1000 - 1))`
- Witness bar on the replication set alone: n >= 10 scored items and lower 95% CI strictly above chance
- Pooled discovery+replication is reported separately and labelled `pooledDiscoveryAndReplication`. It is not the replication verdict

## Primary: S3 arithmetic closure on grade 5

Registered program (same as discovery version 1): depth 2, geometry extras on, lower-central tie-break among min-depth options. Implementation: `scripts/strategy_channels.py` `apply_s3(..., max_depth=2, include_geometry_extras=True, tie="lower-central")`.

Discovery (unfiltered, frozen): 21/40 = 0.525, CI [0.375, 0.675], chance 0.250, n selected = 60.

Prediction: on replication grade-5 items alone, the filtered S3 rate is above 0.25 and the lower 95% CI is above 0.25.

Two runs on the same replication grade-5 items:

- **Primary:** S3 with the artifact filter below applied to the stem before seed extraction
- **Secondary report:** S3 unfiltered (identical program to discovery)

Also report, on the filtered primary run: tie-break decomposition (n decided by unique min depth vs lower-central among min-depth options; hits in each), closure density (mean options in the closure per fired item; unique depth-1 count and key rate), and per-administration counts (form = year).

### Power: minimum n for 80 percent power to detect 0.45

H0 chance p0 = 0.25. Alternative p1 = 0.45. Success event = lower 95% CI > 0.25 (the witness bar, ignoring the n>=10 clause which is already met).

Wald closed form, two-sided 95% (z_{0.975} = 1.959964) and 80% power (z_{0.80} = 0.841621):

n = (z_{0.975} sqrt(p0(1-p0)) + z_{0.80} sqrt(p1(1-p1)))^2 / (p1-p0)^2 = 40.16, which rounds up to 41.

Exact binomial with Wald lower 95% CI: smallest n >= 10 such that P(Wald lower bound of k/n > 0.25 | X ~ Binomial(n, 0.45)) >= 0.80. That n is **46** (k* = 18, rate* = 0.391, power = 0.828). At n = 45 power is 0.794, under the 80 percent line.

**Registered minimum n for the grade-5 primary (filtered) run: 46 fired items.** If n_fired < 46, the grade-5 closure result is **underpowered** even if the point estimate is above 0.25; the paper may say the replication was underpowered, not that the result replicated. If n_fired >= 46 and the lower CI is not above 0.25, it **did not replicate**. If n_fired >= 46 and lower CI > 0.25, it **replicated**.

## Artifact filter (registered before seeing replication results)

Applied to stem text (and `figure.transcription` if present) **before** `extract_stem_numbers`. Discovery robustness judgments in `s3-teks-g5-robustness.json` named five artifact classes. Mechanical rules, in this order:

1. **Thousands separators.** Replace every comma that sits between a digit and exactly three trailing digits (`(?<=\d),(?=\d{3}(?:\D|$))`) with nothing, so `1,012` is the seed 1012, not 1 and 12. Matches the discovery items `staar-2021-5-q5`, `q31`, `staar-2022-5-q21`.
2. **Page or footer numbers.** Delete, case-insensitive: `Page` + digits; `GRADE` + a single digit 3–8; the word `STAAR`; TEA item codes `\b\d{5}_\d\b`; lines that are only `Mathematics`, `GO ON`, `STOP`, or `Texas Education Agency`. Matches footer `GRADE 5` on `staar-2022-5-q3`.
3. **Answer-choice labels.** Delete standalone option markers `(A)`–`(D)`, `(F)`–`(J)`, and a letter A–D/F–H/J followed by `.` or `)` at a token boundary. Labels are not seeds.
4. **Item numbers.** If the item id ends in `qN`, delete a leading token that is exactly N. Delete `Item` + digits.
5. **Suffix after the last question mark.** Keep numbers only in the prefix through the last `?`. The suffix is page chrome, axis dump, or a leaked previous/next item (`staar-2019-5-q36`).
6. **Axis ticks and chart chrome**, only if the kept prefix matches `(?i)coordinate|grid|axis|scatter|bar chart|bar graph|stem-and-leaf|dot plot|\bplot\b|\bgraph\b`:
   - If at least 8 distinct isolated single-digit integers 0–9 appear, delete all isolated single-digit integers (axis 0–9 sweep: `staar-2019-5-q3`, `staar-2021-5-q25`).
   - Delete any space-separated run of at least 4 integers that form an arithmetic sequence with common difference in {1, 2, 5, 10, 15} (bar labels 45,55,65,75,85: `staar-2019-5-q35`; scatter ticks: `staar-2021-5-q35`).
   - If `stem-and-leaf` is present, delete remaining isolated single-digit integers (`staar-2022-5-q1`).
   - Delete repeated age-bin tokens `\d{1,2}\s*[-–]\s*\d{1,2}` (`staar-2022-5-q15`).

Unfiltered S3 uses the stem as parsed, no steps 1–6.

The filtered run is primary. Do not retune the filter after seeing replication rates. If the filter is too aggressive (n_fired collapses), report that as a construct result; do not loosen it in this version.

## Secondary rules (pre-specified; STAAR cells that cleared the per-cell bar only)

Witness bar as above. Chance 1/k.

### unit-rate on grade 5

Discovery (`exports/apriori-cell-table.json` / `exports/rule-chance.json`): programId `unit-rate`, authority `teks`, claim `g5`, n=12, 5/12=0.417, CI [0.167, 0.750], chance 0.146, `clearsPerCellBar: true` (unclaimed). Catalog implementation: `runner/src/programs/apriori.ts` `unit-rate`. Stem numbers from `extractNumbers` (comma-joined tokens). If fewer than two nonzero numbers, abstain. Candidates a/b and b/a from the first two nonzero stem numbers, first match to a numeric option wins.

Tested on replication grade-5 selected items only. Prediction: rate above chance with lower CI above chance if n>=10.

### TEKS stem-repeat on Algebra I

The only STAAR `option-repeating-stem-numbers` cell that cleared the per-cell bar is **teks / alg1**: n=43, 17/43=0.395, CI [0.256, 0.535], chance 0.25, `clearsPerCellBar: true` (unclaimed). Other TEKS grades did not clear; they are not tested as secondary claims.

Catalog: stem number tokens (string form) that appear as substrings of an option; pick the first letter among hits. Abstain if no hit. Tested on replication Algebra I selected items only. Prediction: rate above chance with lower CI above chance if n>=10.

### Negative control: lower-central on every STAAR grade cell

Discovery `middle-value-option` on TEKS did **not** clear any STAAR grade (g3 0.278 n=36 CI [0.139, 0.444]; g4 0.314 n=35 CI [0.171, 0.486]; g5 0.347 n=49 CI [0.224, 0.490]; g6 0.327 n=52 CI [0.192, 0.462]; g7 0.317 n=41 CI [0.171, 0.463]; g8 0.267 n=45 CI [0.156, 0.400]; alg1 0.213 n=61 CI [0.115, 0.328]). Program: `addendum_lib.lower_central_key` / `middle_value_option` (sort parsed leading option numbers, value at index floor((n-1)/2), first letter among that value). Abstain if fewer than 3 numeric options.

Tested on each replication grade cell that has scored items: g3, g4, g5, g6, g7, g8, alg1. **Prediction: stays at chance** (lower CI not above chance). A clear on replication would be a negative-control failure, not a new witness in this addendum.

## Parse protocol

For each registered form, run `parse_keys` then `parse_items` from `scripts/parse_staar_bulk.py`. Record per form: n keys recovered, n items parsed, n with a key, n selected with 4 parseable numeric options, n parse failures (keys with no kept item).

Stop for that form, do not guess keys, if any of:

- zero keys recovered after the recorded parser
- keys recovered but zero selected items with the key letter inside the parsed choices
- hand-check finds a key/item number mismatch (the answer table does not align with parsed item numbers)

Hand-check: 20 items drawn with `random.Random(20260916)` from parsed selected-response replication items, without replacement. Compare stem, options, and key against the PDF text layer. Record `parse-hand-check.json` with counts agree / disagree / uncertain. If 3 or more disagree on the key, stop scoring and report parse failure.

## What the paper may say (pre-committed)

- Replicated: filtered S3 grade 5, n_fired >= 46, lower 95% CI > 0.25. The paper may add a replication sentence to the g5 closure witness. One-sided wording only.
- Did not replicate: n_fired >= 46 and lower CI <= 0.25. The paper may not claim g5 closure as a replicated witness.
- Underpowered: n_fired < 46. The paper may not treat this run as a replication of the g5 closure result.
- Pooled estimates are descriptive and are not the replication verdict.
- Secondary unit-rate and stem-repeat may be mentioned only if they clear the bar on replication items alone.
- Lower-central remaining at chance supports that the g5 closure result is not a restatement of middle-value on STAAR.

## Outputs

- `exports/replication-staar/inventory.json` (already written)
- `exports/replication-staar/preregistration.md` and `.sha256`
- `exports/replication-staar/items.jsonl`
- `exports/replication-staar/parse-hand-check.json`
- `exports/replication-staar/results.json`
- `exports/replication-staar/README.md`

## Version 2 option-leak repair (2026-09-16T21:42:00Z)

Hashed as `preregistration-v2.sha256` before any rescoring of repaired items. Version-1 files (`items.jsonl`, `results.json`, `parse-hand-check.json`, `preregistration.md.sha256`) are not overwritten.

The version-1 hand-check of 20 items found six option defects and zero key mismatches: five last-choice leaks of the next page or next item (`staar-2016-7-q28`, `staar-2016-4-q30`, `staar-2016-7-q3`, `staar-2016-4-q43`, `staar-2016-6-q35`) and one stacked-fraction pairing (`staar-2013-5-q35`). Those six cases are the derivation set. The rule below is mechanical and is applied to **every** replication item before any version-2 score is computed. It is not retuned after seeing version-2 rates.

### Last-option footer / page-number leak

Cause in the version-1 parser: `extract_lettered_choices` skips footer lines (`Mathematics`, `Page N`, `GO ON`, `STOP`) and then keeps appending later lines to the last option. The five leak cases all continue after `Mathematics` / `Page N` into the next page or the next item.

For each selected-response item:

1. Locate the item start in the test PDF text layer (same `looks_like_item_start` rule as `parse_items`). The item PDF page number P is the last `---PAGE P---` marker before that start.
2. Rebuild the last lettered option (stored as D; F/G/H/J mapped as in version 1) from that item's lines, **stopping** at the first footer line or at the next item start. Footer lines, matching the five cases: a line that begins with `Mathematics`, `Page` + digits, `GO ON`, `STOP`, `STAAR`, `Texas Education Agency`, `BE SURE YOU HAVE RECORDED`, or `---PAGE`. The next item start is a later item number whose rest passes `looks_like_item_start`.
3. If the rebuilt last option still contains an inline footer (`Mathematics Page` + digits, `Page` + digits, `GO ON`, `STOP`, `BE SURE YOU HAVE RECORDED`, `---PAGE`), cut at the first such match.
4. If after that cut the last option has **two or more tokens** and the last token equals the decimal representation of P, strip that token. A last option whose only token equals P is left unchanged (a numeric answer that happens to equal the page number is not a leak).

A, B, and C are not rewritten by this step. Stems are not rewritten by this step.

### Stacked-fraction rejoin

Cause: stacked `num/den` choices are emitted as `num` then letter then `den`, so the first numerator remains after the last `?` in the stem, A/B/C each hold `den next_num`, and D holds the last denominator (`staar-2013-5-q35` PDF `6/10, 3/5, 8/20, 18/30` parsed as stem leftover `6` and options `10 3` / `5 8` / `20 18` / `30`).

If and only if all of the following hold, rejoin using the same `num/den` form as `FRACTION_RE` in `strategy_channels.py` (`^(-?\d+)\s*/\s*(-?\d+)$`):

- the stem matches `(.*\?)\s+(\d+)\s*$` (prefix through the last question mark, then one leftover integer N0)
- options A, B, C each match `^(\d+)\s+(\d+)$`
- option D matches `^(\d+)$`

Then set A=`N0/A_first`, B=`A_second/B_first`, C=`B_second/C_first`, D=`C_second/D`, and replace the stem with the prefix through the last `?`. Applied after the last-option repair.

### Tests rerun on repaired items

Same programs, chance, CI, witness bar, artifact filter, and power floor n=46 as above. Primary remains filtered S3 grade 5. Also report unfiltered S3 grade 5, unit-rate grade 5, TEKS stem-repeat Algebra I, and lower-central on every grade cell.

Registered prediction (unchanged): on repaired replication grade-5 items alone, the filtered S3 lower 95% CI is strictly above 0.250. The power floor is reported separately from whether that prediction is met. A met prediction is not described as underpowered.

Hand-check: 20 items drawn with `random.Random(202609162)` from repaired selected-response replication items (version-1 seed was 20260916). Compare stem, options, and key against the PDF text layer. Record `parse-hand-check-v2.json`. Stop scoring only if 3 or more disagree on the key.

Outputs (version 2 only): `items-repaired.jsonl`, `parse-hand-check-v2.json`, `results-v2.json`, `preregistration-v2.sha256`.

## Extension: additional grade-5 administrations ( 2026-09-16T21:59:54Z )

Hashed as `preregistration-extended.sha256` before any score is computed on the new forms. Version-1 and version-2 files are not overwritten. The extension is additional English STAAR grade-5 mathematics paper administrations of the same population as the registered primary cell. Same S3 program (depth 2, geometry extras, lower-central tie-break), same stem-artifact filter, same chance 1/k, same 95% percentile bootstrap (seed 11, 1000, `random.Random.randrange`), same witness bar, same power floor n=46.

### Forms in this extension

Targeted fetch of English grade-5 test+key pairs for 2015, 2017, 2018, 2020, and 2023. Log: `fetch-log-g5.md`.

To be scored if a text-extractable English test+key pair is on disk after that fetch:

- 2017 English grade 5 (`staar-2017-5-english`)
- 2018 English grade 5 (`staar-2018-5-english`)

Not scored, no complete extractable pair:

- 2015: test PDF already on disk; paper answer key not on the TEA 2020-12-30 released-test table and not found at the URLs tried
- 2020: no English g5 math test or key on the TEA released-test table (COVID year)
- 2023: operational test PDF not released; answer key on disk is not scored without the test
- Census years 2019/2021/2022 remain excluded
- Spanish, samplers, practice, redesign, rationales, online keys, scanned PDFs (no OCR)

New forms are parsed with `parse_keys_from_pdf` / `parse_items` (same as version 1) and then the version-2 last-option / stacked-fraction repair, applied to every item before scoring.

### Scores that will be computed (after this hash)

Filtered S3 grade 5 on:

1. the version-1 44 repaired replication items
2. the new forms alone
3. combined (version-1 repaired + new forms)

Unfiltered S3 on the same three sets is reported. Registered prediction on each filtered set: lower 95% CI strictly above 0.250. The power floor n=46 is reported separately. A met prediction is not described as underpowered. Combined n versus 46 is reported.

Outputs: `items-extended.jsonl` (version-1 repaired items plus new forms; `items.jsonl` stays the version-1 parse), `results-extended.json`, `preregistration-extended.sha256`.
