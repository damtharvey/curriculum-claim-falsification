# STAAR replication

Written 2026-09-16T22:01:00Z. Version-1 hash `55bd9dedd293fd9292893adc018f91fb4e6ce0ab58a86e4c7a7676cbb04d7e46` (2026-09-16T21:20:11Z). Version-2 repair hash `e25e1d42ed13145733b3a8952eaed2a6132d50d649defb071c969f82723b9f71` (2026-09-16T21:44:16Z). Extension hash `81ea35c330e803740506d41cbd09451d275004628a87a74f2e81173fc0ef7a10` (2026-09-16T21:59:54Z).

## Verdict

Registered prediction: filtered S3 grade 5, lower 95% CI strictly above 0.250. Power floor n=46 is reported separately.

- **Version-1 items (unrepaired): prediction met.** 18/44 = 0.409, CI [0.273, 0.545]. Power floor not reached (n=44).
- **Version-1 items after the version-2 repair: prediction not met.** 17/44 = 0.386, CI [0.250, 0.545]. Power floor not reached (n=44). This null is underpowered and is not read as a failed replication.
- **Extended set (repaired 2013/2014/2016 plus 2017/2018): prediction not met.** 21/64 = 0.328, CI [0.219, 0.438]. Power floor reached (n=64). This null is not underpowered.

## Repair rule (version 2)

Last option rebuilt from the PDF text layer, stopping at the first footer line (`Mathematics`, `Page N`, `GO ON`, `STOP`, `STAAR`, TEA, answer-document line, `---PAGE`) or the next item. Inline footers cut. Trailing token equal to the item PDF page number stripped only when at least two tokens remain. Stacked four-option fractions rejoined to `num/den` when the stem has one leftover integer after `?`, A/B/C are two integers, and D is one integer. Applied to every replication item before rescoring. 42 last-option repairs and 3 stacked rejoins on 228 items.

Hand-check v2 (seed 202609162, 20 items not in the version-1 sample): **agree 14, disagree 4, uncertain 2**, key mismatches 0. The four option disagrees are stacked layouts the repair does not cover (quadratic formula, inequality, division identity, missing fractions). Two figure-only items left uncertain (clocks, bar graphs). Version-1 last-option leak case 2016-7-q3 now agrees.

## S3 grade 5

Discovery frozen: 21/40 = 0.525, CI [0.375, 0.675].

- Version-1 unrepaired filtered: 18/44, CI [0.273, 0.545].
- Repaired filtered: 17/44, CI [0.250, 0.545]. Per administration: 2013 3/12, 2014 5/16, 2016 9/16.
- New forms alone filtered: 4/20 = 0.200, CI [0.050, 0.400]. 2017 1/11, 2018 3/9.
- Combined filtered: 21/64 = 0.328, CI [0.219, 0.438].
- Repaired unfiltered: 18/47, CI [0.255, 0.511]. Combined unfiltered does not clear the bar.

## Grade-4 negative control

On repaired items, lower-central is still 10/17 = 0.588, CI [0.353, 0.824] and still clears. All 10 hits survive the last-option repair. Five of those hits are leading-number parse artifacts (identical leading values on equations, thousands commas, first digit in a sentence). On the 9 clean scored items: 5/9 = 0.556, CI [0.222, 0.889], which does not clear. Not reported as an unregistered observation and not a witness. Details: `grade4-negative-control.json`.

## Extension fetch

English grade-5 paper test+key pairs from the TEA 2020-12-30 released-test table (archive.org): **2017 and 2018** found, text-extractable, parsed (2017: 36 keys, 24 items, 21 selected; 2018: 36 keys, 21 items, 20 selected). Log: `fetch-log-g5.md`.

Not found or cut:

- 2015 key (test PDF already on disk; no 2015 math form on that TEA table)
- 2020 test and key (not on the table)
- 2023 operational test PDF (key on disk; TEA no longer releases the paper form)
- Census 2019/2021/2022
- Spanish, samplers, practice, redesign, rationales, online keys
- Scanned PDFs (no OCR)

## Outputs

Version 1: `items.jsonl`, `parse-hand-check.json`, `results.json`.
Version 2: `items-repaired.jsonl`, `parse-hand-check-v2.json`, `results-v2.json`, `preregistration-v2.sha256`.
Extension: `items-extended.jsonl`, `results-extended.json`, `preregistration-extended.sha256`.
