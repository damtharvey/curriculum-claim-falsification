# Repaired text layer and 14B isomorph amendment (preregistration)

- Written: 2026-09-17T06:50Z, before any verification transcription, repaired-layer language-model scoring, repaired isomorph scoring, or the 14B amendment rescore.
- Purpose: review-2 post-rebuttal W2 / N1 (the print-faithful subset is selected: pre-2023 forms, word options over-represented; a VLM miss moves an item out, never in) and W8 / N4 (Qwen2.5-14B was excluded from the isomorph control at 592/606 = 0.977 versus a 0.98 floor). This addendum **repairs** the text layer for every Algebra I and Algebra II masked-stem primary item from the page image instead of filtering, then rescores the full repaired population. It also re-runs the 14B original masked-stem letters at batch size 1 and, whatever the agreement, scores the rank-preserving and scrambled option-numeral arms with an explicit floor label.
- Scoring of verification images, repaired masked-stem items, repaired isomorphs, and the 14B amendment starts only after `preregistration.sha256` records the sha256 of this file. The runner refuses to score if the file has changed.
- One-sided wording (locked): a pass does not require the tagged operation. Nothing here says students did not learn.
- Does not edit `paper/`. Writes only to `exports/repaired-layer/` and `scripts/`.

## Population (locked)

Algebra I and Algebra II withheld-quantity masked-stem primary items, 606 ids, from `exports/addendum-gpu/masked-stem-algebra-primary-item-ids.json` (every id is also in `exports/addendum-gpu/masked-stem-7b-items.jsonl`, `masked-stem-14b-items.jsonl`, and `masked-stem-phi4-items.jsonl`).

| cell | n |
|---|---:|
| Algebra I (`claim = algebra-i`) | 358 |
| Algebra II (`claim = algebra-ii`) | 248 |

Census keys, authority, and claim stay those of `data/items.jsonl`. The repaired stem and options replace the census text layer.

## Transcription 1, the repaired source text (locked)

Reuse the print-fidelity VLM pass. Model `Qwen/Qwen2-VL-7B-Instruct` revision `eed13092ef92e448dd6875b2a00151bd3f7db0ac`, prompt, crops, parser, and stem post-processing locked in `exports/print-faithful/preregistration.md` (sha256 `0211585e9361d3771e04df5e118050ede761971da286f0b1333a7aac289737d6`). Per-item stored fields `rawVlm`, `vlmStem`, `vlmOptions` on `exports/print-faithful/fidelity-items.jsonl` (stage `calibration` or `census`) are transcription 1.

If a stored row has a parseable stem and at least two option letters, do not re-transcribe it. If a stored row is unparseable (empty stem, no options, or empty `rawVlm`) do not invent text and do not run a new cell; leave the item without a repaired stem. Do not transcribe items outside this Algebra I / Algebra II primary list for the language-model rows.

## Transcription 2, independent verification (locked)

Same model, same revision, same snapshot, greedy decoding, `max_new_tokens=640`, seed 20260916, CUDA, no CPU path. Two deliberate differences from transcription 1:

1. Crop margin. The stored print-fidelity clip is expanded by 6 pt on the top and bottom (the original 8 pt pad becomes 14 pt) and intersected with the page rectangle. Left and right stay page-wide. A continuation clip, when the stored row has one, is expanded the same way. Render at 150 DPI into `exports/repaired-layer/pages-verify/`. Do not re-run the locator.
2. Prompt wording, below. `{qnum}` is the printed item number (the `-q<n>` suffix).

```
Copy the printed multiple-choice question numbered {qnum} from this exam-page image. Do not solve it and do not name the correct choice.

Skip headers, footers, other questions, and the computations box labeled "Use this space for computations".

Output:
1. "stem": the wording of question {qnum} starting after the printed item number and stopping before the first answer choice. Keep any sentence that continues after a table or figure. If a table is printed, copy its cells row by row into the stem. Do not describe diagrams, graphs, or pictures. Do not copy labels that appear only inside a diagram. Do not put answer choices in the stem.
2. "options": every printed answer choice of question {qnum}, keyed by the printed marker exactly as printed ("1", "2", "3", "4" or "A", "B", "C", "D", "E"). Each value is one JSON string; if a choice wraps across lines, join those lines with "; ". Include every printed choice and no unprinted choice.

Write mathematics in plain text: exponents as x^2, fractions as 5/3, mixed numbers as 2 1/3, roots as sqrt(10), coordinates as (-1, -3), subscripts as a_n. Keep degrees, pi, <=, >=, and the minus sign.

Return a JSON object and nothing else:
{"stem": "...", "options": {"1": "...", "2": "...", "3": "...", "4": "..."}}
```

Parser, option-label map, and stem post-processing are the functions in `scripts/print_fidelity_lib.py` (`parse_json_object`, `transcribed_options`, `clean_vlm_stem`, `cut_echoed_options`).

## Agreement rule (locked)

Compare transcription 1 to transcription 2 with the same token thresholds as the print-fidelity check, by calling `score_fidelity` on a copy of the item whose `stem` and `choices` are transcription 1. An item is `repaired_verified` iff that call returns verdict `faithful`: stem F1 >= 0.8 with precision >= 0.8 and recall >= 0.8, every transcription-1 option scores >= 0.9 against transcription 2, and the option counts are equal. Every other item, including unparseable transcription 1 or 2, is `repaired_unverified`.

Report counts for Algebra I and Algebra II, and the overlap of `{repaired_verified, repaired_unverified}` with the old print-fidelity verdicts `{faithful, not_faithful, unverified}`.

## Repaired items and masking (locked)

`repaired-items.jsonl`: `id`, `stem`, `options`, `key` from transcription 1 (options keyed A-D/E as already mapped), plus `claim`, `authority`, `old_verdict`, `repair_verdict`. Key letter is the census key, never a VLM guess.

Apply `scripts/score_choices_only_local_lm.py` `mask_stem` version 1 (masking hash v1, `exports/addendum-gpu/masked-stem-preregistration.md` sha256 `af473bb6cd9d46dc74e034f4460d56a808273fe83ffaf457cd7d122c40ae80e8`) to the repaired stem. Options are not masked. Record `masked_token_count`. The withheld-quantity scoring population is items with a usable transcription 1, a census key present among the repaired options, and `masked_token_count >= 1`. Write `repaired-masked-items.jsonl`.

## Language-model scoring on the repaired layer (locked)

Same models, revisions, seed, and letter-logprob rule as `scripts/score_choices_only_local_lm.py` / `scripts/score_isomorph_options.py`. CUDA required. Prompt mode `masked-stem`, mask version 1, seed 20260916.

- `Qwen/Qwen2.5-7B-Instruct` `a09a35458c702b33eeacc393d103063234e8bc28`, bf16, batch size 4.
- `Qwen/Qwen2.5-14B-Instruct` `cf98f3b3bbb457ad9e2bb7baf9a0125b6b88caa8`, bf16, batch size 1, `device_map="cuda"`.
- `microsoft/phi-4` `2db69c1c3e91a05d2c64a3185acfbaf36f744e25`, bf16, batch size 1, `device_map="cuda"`.

Per model and cell (Algebra I, Algebra II), on (a) all repaired withheld-quantity items and (b) `repaired_verified` only: n, passes, pass rate, chance 0.25 (also mean 1/k), bootstrap 95% percentile CI (`random.Random.randrange`, 1000 replicates, seed `21 + n`), modal key letter and frequency on that subset, bar. Bar: n >= 10, lower CI strictly above 0.25, lower CI strictly above the subset modal-letter frequency.

Compare those rates to the original text-layer rates on the same 358 / 248 primary ids from the saved prediction files (no language-model rerun of the text layer).

## Verb-class split (locked)

Join `exports/standards-split/item-standards.jsonl` with the locked cluster table in `scripts/split_masked_stem_by_standard.py`. On the repaired withheld-quantity population, report execution versus recognition-or-interpretation for each model, on all repaired and on `repaired_verified`, for Algebra I and Algebra II. Same n / rate / CI / bar. Mixed-class items are counted, not a claimed row.

## Rank-preserving isomorph on repaired options (locked)

Reuse `scripts/perturb_option_numerals.py` (`perturb_choices`, seed 20260916, arm `isomorph_rank_preserving`, per-item RNG `sha256(f"{seed}:{arm}:{item_id}")[:16]`). Perturb the repaired option strings, not the census options. Keep the repaired masked stem and the census key letter. Items with no numeral are unchanged and are included in the pass rate. If perturbation raises, exclude that item from the isomorph arm and count it. Score the rank-preserving arm for all three models. Report n, rate, CI, modal letter, bar on Algebra I / Algebra II, all repaired and verified. The scrambled arm is not scored on the repaired layer.

## Catalog lower-central on repaired options (locked)

Pure Python. No new transcription. If `exports/print-faithful/fidelity-items.jsonl` has transcription 1 for the geometry lower-central fired set (`nyregents::geometry::lower-central-fired`, n=279) and the EQAO grade 6 fired set (`eqao::g6::lower-central-fired`, n=40), replace those items' options with transcription 1 and rerun `addendum_lib.middle_value_option` through `score_program` / `summarize_scored` (item bootstrap mulberry32 seed 11, 1000 replicates; cluster bootstrap seed 20260916, 2000 replicates). Report n original fired, n missing transcription 1, n on which the rule still fires, passes, rate, chance, item 95% CI, cluster 95% CI, item bar (n >= 10 and item lower CI above chance). If a cell has no print-faithful transcriptions, say so and skip. Do not transcribe new cells.

## Part 2: 14B isomorph amendment (locked)

Pre-registered because the original isomorph control stopped 14B at 0.977. This amendment is not a silent loosening of that floor.

Rerun Qwen2.5-14B original masked-stem scoring on the **census text-layer** 606-item algebra primary population (not the repaired layer), batch size 1, seed 20260916, bf16, `device_map="cuda"`, letter-logprob argmax, prompt mode `masked-stem`, mask version 1. Masked stems must match the saved `masked_stem` field on `exports/addendum-gpu/masked-stem-14b-items.jsonl`.

Measure letter agreement with that saved file. Floor remains 0.98.

- If agreement >= 0.98, label `clears_floor`, score rank-preserving and scrambled arms on the original (text-layer) options already produced by `scripts/perturb_option_numerals.py` in `exports/isomorph-options/`, and report as in that addendum (n, rate, CI, bar, paired difference on non-`no_numeral` items).
- If agreement is still < 0.98, label `below_floor`. Report the agreement, every disagreeing id, and still score both perturbed arms so a reader can see them. Do not call it a pass. Do not score these arms as a claimed control.

## Honesty clause (locked)

If the repaired-all Algebra I rate does not clear the channel bar for a model, the README says so in the first section. `repaired_verified` is a sensitivity, not a filter that restores a selected subset as the claimed cell. The 14B amendment below 0.98 is not a pass.

## Outputs

`exports/repaired-layer/`: this file, `preregistration.sha256`, `verification-items.jsonl`, `repaired-items.jsonl`, `repaired-masked-items.jsonl`, `perturbed-items-isomorph_rank_preserving.jsonl`, `scores-*.jsonl`, `results.json`, `README.md`. Script: `scripts/run_repaired_layer.py`.
