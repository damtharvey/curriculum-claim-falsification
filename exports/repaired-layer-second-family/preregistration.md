# Second VLM family for verification transcription (preregistration)

- Written: 2026-09-17T14:05Z, before any LLaVA scoring of Algebra I or Algebra II items.
- Purpose: review weakness 2 in `paper/reviews/weaknesses-without-excuse.md`. The repaired-layer verified set is the 431 items on which two readings of one model family (Qwen2-VL-7B-Instruct) agree. This addendum transcribes the same 606 crops with a second family and recomputes the verified set as items where the two families agree under the print-fidelity thresholds.
- Scoring of LLaVA transcriptions starts only after `preregistration.sha256` records the sha256 of this file. The runner refuses to transcribe if the file has changed.
- One-sided wording (locked): a pass does not require the tagged operation. Nothing here says students did not learn.
- Does not edit `paper/`. Writes only to `exports/repaired-layer-second-family/` and `scripts/`.

## Population (locked)

Algebra I and Algebra II withheld-quantity masked-stem primary items, 606 ids, from `exports/addendum-gpu/masked-stem-algebra-primary-item-ids.json`, the same list as `exports/repaired-layer/`.

| cell | n |
|---|---:|
| Algebra I (`claim = algebra-i`) | 358 |
| Algebra II (`claim = algebra-ii`) | 248 |

## Comparison target (locked)

Transcription 1 is the Qwen2-VL-7B-Instruct stem and options already stored on `exports/repaired-layer/repaired-items.jsonl` (`stem`, `options`), which are the print-fidelity fields `vlmStem` / `vlmOptions` (model `Qwen/Qwen2-VL-7B-Instruct` revision `eed13092ef92e448dd6875b2a00151bd3f7db0ac`). Do not re-run Qwen. Do not compare LLaVA to the census text layer. Do not compare LLaVA to transcription 2.

## Model (locked)

- `llava-hf/llava-v1.6-vicuna-13b-hf`, local snapshot revision `745cfbdb14dfeff9bcc6eb731937102e88ea3024`. Preferred because it is a different family from Qwen2-VL and fits 32 GB in bf16. `LlavaNextForConditionalGeneration`, `torch.bfloat16`, `device_map="cuda"`, `attn_implementation="sdpa"`, `local_files_only=True`. CUDA required; no CPU path. No download.
- Greedy decoding (`do_sample=False`), `max_new_tokens=640`, seed 20260916. The model is never asked to solve or to pick an answer.

## Page images (locked)

Reuse the stored print-fidelity crops and page renders already on disk (`pngs` on `exports/print-faithful/fidelity-items.jsonl`, stage `calibration` or `census`, files under `exports/print-faithful/pages/`). Do not re-run the locator. If a listed PNG is missing, re-render that item from the stored clip at 150 DPI with the original 8 pt pad; do not invent a new crop. Continuation images listed in `pngs` are attached in listed order.

## Transcription prompt (locked)

One user message, the page image(s) followed by this text with `{qnum}` replaced. Same wording as `exports/print-faithful/preregistration.md`.

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

Parser, option-label map, and stem post-processing are the functions in `scripts/print_fidelity_lib.py` (`parse_json_object`, `transcribed_options`, `clean_vlm_stem`, `cut_echoed_options`).

## Agreement rule (locked)

Compare LLaVA to transcription 1 by calling `score_fidelity` on a copy of the item whose `stem` and `choices` are transcription 1. Thresholds are those of `exports/print-faithful/preregistration.md`: stem F1 >= 0.8 with precision >= 0.8 and recall >= 0.8, each transcription-1 option scores >= 0.9 against LLaVA, and the option counts are equal. An item is `verified_cross_family` iff that call returns verdict `faithful`. Every other item, including unparseable LLaVA output or unusable transcription 1, is `not_verified_cross_family`.

## Reporting (locked)

No language-model re-scoring. Join `exports/repaired-layer/scores-{7b,14b,phi4}-repaired.jsonl` and `scores-{7b,14b,phi4}-repaired-isomorph_rank_preserving.jsonl`. The scored text is transcription 1.

Report:

1. Cross-family verified count of 606, and the overlap with the existing Qwen–Qwen `repaired_verified` set.
2. Masked-stem rates per model on (a) cross-family verified, (b) verified by both checks (`repaired_verified` and `verified_cross_family`), for Algebra I and Algebra II: n, passes, pass rate, chance 0.25 (also mean 1/k), bootstrap 95% percentile CI (`random.Random.randrange`, 1000 replicates, seed `21 + n`), modal key letter and frequency, bar. Bar: n >= 10, lower CI strictly above 0.25, lower CI strictly above the subset modal-letter frequency.
3. Verb-class execution versus recognition-or-interpretation on the cross-family verified set, join `exports/standards-split/item-standards.jsonl` with the locked cluster table, same n / rate / CI / bar. Mixed-class items are counted, not a claimed row.
4. Rank-preserving isomorph on the cross-family verified set, join the repaired-layer isomorph scores (items whose perturbation failed are excluded). Same n / rate / CI / bar.

## Honesty clause (locked)

If a claimed-cell rate on the cross-family verified set does not clear its bar, the README says so in the first section. This addendum does not replace the Qwen–Qwen verified set in `exports/repaired-layer/` and does not edit `paper/`.

## Outputs

`exports/repaired-layer-second-family/`: this file, `preregistration.sha256`, `transcriptions-llava.jsonl`, `verdicts.jsonl`, `results.json`, `README.md`. Script: `scripts/run_second_family_transcription.py`.
