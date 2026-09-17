# VLM image backsolving (verify-versus-solve) — preregistration

- Written: 2026-09-17T02:08:11Z
- Channel: extract the displayed equation from a page **image**, then substitute each option in Python (sympy / numeric). The vision-language model is not asked to solve and is not asked to pick an answer letter.
- Frozen items: `data/items.jsonl` (2405 keyed public items). Solving-tagged selected-response only.
- Scoring starts only after `preregistration.sha256` records the sha256 of this file.
- One-sided (locked): a pass does not require the tagged operation (here: solve). Failure to fire does not certify the tag. We never say students did not learn.
- Witness bar (locked): n fired >= 10 in a named cell; lower 95% item bootstrap CI (mulberry32, seed 11, 1000 replicates, same as `scripts/addendum_lib.py` `bootstrap_ci_mulberry`) strictly above chance. Chance among fired items is the mean of 1/k, k = number of choices on that item.
- Abstain unless exactly one option satisfies. Coverage = n fired unique / n solving-tagged selected-response in the cell. Also report the imputed rate that counts each abstention as a chance guess (1/k).
- This addendum does not enter the frozen catalog Holm family unless a later writing pass chooses to. It is the missing image channel for S4 (text-layer backsolving fired on 2 of 598 Algebra I items).

## Model (locked)

- Hugging Face id: `Qwen/Qwen2-VL-7B-Instruct`
- Local snapshot revision sha: `eed13092ef92e448dd6875b2a00151bd3f7db0ac`
- Why this model: cached instruct VLM, 7B class, fits RTX 5090 32GB in bf16. Cached peers inspected and not used for scoring: `Qwen/Qwen2-VL-2B-Instruct` (`895c3a49bc3fa70a340399125c650a463535e71c`), `liuhaotian/llava-v1.5-7b` (`4481d270cc22fd5c4d1bb5df129622006ccd9234`), `llava-hf/llava-v1.6-vicuna-13b-hf` (`745cfbdb14dfeff9bcc6eb731937102e88ea3024`). No bitsandbytes path. No `Qwen2.5-VL-7B-Instruct` download.
- Load: `Qwen2VLForConditionalGeneration`, `torch.bfloat16`, `device_map="cuda"`, `attn_implementation="sdpa"`, `local_files_only=True`. CUDA is required. There is no CPU device map.
- Decoding: greedy (`do_sample=False`), `max_new_tokens=400`. Seed 20260917.

## Images

- Source: local `data/raw/` PDFs already on disk. Render with pymupdf to PNG at 150 DPI (`scripts/render_solving_item_pages.py`). No EasyOCR. No PDF text layer as the equation.
- Crop: if a question-number (or TIMSS item-code) text box is found, clip from that y to the next question y on the same page, full page width, 8 pt pad. Otherwise the full page. The prompt still names the item by stem prefix.
- Stem prefix: census `stem` with control characters stripped, whitespace collapsed, first 90 characters. Used only to point at the item on a multi-item page, not as the equation.

## Population (locked)

Solving-tagged selected-response, same cells as strategy S4:

- `nyregents` / `algebra-i` (priority cell; Regents Algebra I; CCSS A-REI lives at this course grain; `officialTag` is the course name, not an `A-REI` string)
- `nyregents` / `algebra-ii`
- `teks` / `alg1`
- derived `teks` / `solve-se` if n solving-tagged selected >= 1: `officialTag` in {`6.10(A)`, `6.10(B)`, `7.11(A)`, `7.11(B)`, `8.8(A)`, `8.8(B)`, `8.8(C)`, `A.5(A)`, `A.5(B)`, `A.5(C)`, `A.5(D)`, `A.8(A)`, `A.8(B)`}
- `eqao` / `g9`
- derived `timss` / `algebra`: `authority == timss` and `contentDomain` matches `/algebra/i`

Eligible in a cell = those solving-tagged selected-response items. An item without a rendered PNG still counts in the coverage denominator and is an abstention (`no_image`).

## Extraction prompt (locked)

The user message is this template with `{stem_prefix}` replaced. The only image is the PNG. No option letters are requested as an answer.

```
You are a transcription tool, not a tutor.

The page image may contain several items. Use only the item whose printed stem begins with:
{stem_prefix}

Transcribe:
1. every displayed equation or inequality in that item that involves an unknown (the relation a student could substitute into);
2. the printed multiple-choice option contents for that item, keyed by letter A,B,C,D. If the page uses F,G,H,J, map F->A, G->B, H->C, J->D.

Do not solve. Do not say which option is correct. Do not compute a value for the unknown.

Reply with a JSON object and nothing else:
{"has_equation": true, "equations": [{"latex": "...", "ascii": "..."}], "options": {"A": "...", "B": "...", "C": "...", "D": "..."}}
If that item has no equation or inequality, use has_equation false and equations [].
ascii uses * for multiplication, ** for powers, sqrt(...) for roots, and a single relation from = < > <= >= !=.
```

Parser: strip an optional markdown fence; `json.JSONDecoder.raw_decode` from the first `{`. Failure is abstention `extract_unparseable`.

## Sympy substitution rule (locked)

1. For each object in `equations`, take `ascii` if it is a non-empty string, otherwise convert `latex` with the rewrite in `scripts/vlm_backsolve_lib.py` `latex_to_ascii` (frac, sqrt, cdot/times, le/ge/neq, superscripts; remaining unknown TeX commands become spaces).
2. Split on the first `=` if present, else the first relation token among `== != ≠ ≤ ≥ <= >= < >`. Require a non-empty left and right.
3. Parse each side with sympy `parse_expr` using `standard_transformations + convert_xor + implicit_multiplication_application`, after the S4 v2 minus/operator normalization in `strategy_channels.normalize_math_text_v2`. Parse failure drops that equation.
4. Keep equations whose distinct single-letter variables (after dropping `pi`) are 1 or 2.
5. Option values come from the VLM `options` map, not from census OCR strings (the text layer is known to smash minus signs). Strict parse only: optional `X =` wrapper; optional trailing unit word; whole-string signed decimal or simple fraction `a/b`; or an ordered pair `(a, b)` / `x=a, y=b`. Leading-number grabs from algebraic expressions are rejected.
6. F/G/H/J keys mapped to A/B/C/D. Extra letters ignored. An option that does not strict-parse cannot satisfy.
7. One-variable equation and scalar options: substitute the unique variable; equality uses the S4 numeric match windows (`abs(a-b) <= 1e-4 * max(1,|a|,|b|)` or `abs(a-b) < 0.01`); inequalities use the corresponding float comparison. A substitution that errors does not satisfy. If several extracted one-variable equations exist, use the first for which at least one option evaluates on both sides.
8. Two-variable equation(s) and pair options: map `(first, second)` to `(x, y)` if those letters appear, else sorted names. If two or more extracted equations share those variables, the pair must satisfy all of them that evaluate.
9. Fire iff exactly one option letter satisfies. Otherwise abstain (`no_equation`, `extract_unparseable`, `no_parsed_options`, `zero_hits`, `multiple_hits`, `no_image`).

Census `choices` and `key` are used only after the pick: `correct` is pick == key. They are not inputs to substitution.

## Exploratory arm (not the witness)

If, after the extract+sympy pass, Algebra I has n fired < 10, run a second labelled arm on Algebra I items that have a PNG: the VLM answers yes/no per option letter for whether that printed option satisfies the shown equation. Same JSON discipline; unique `yes` fires; otherwise abstain. Outputs `backsolve-vlm-verify.json` and `backsolve-vlm-verify-items.jsonl`. This arm is exploratory. It does not clear the witness bar and is not mixed into `backsolve-extract.json`.

Verify prompt:

```
You are checking substitution, not solving by algebra.

Use only the item whose printed stem begins with:
{stem_prefix}

For each printed option A,B,C,D (map F,G,H,J to A,B,C,D), answer whether that option's printed value satisfies the displayed equation or inequality in the item. Do not solve for the unknown. Do not explain.

JSON only:
{"A": "yes"|"no"|"unreadable", "B": "yes"|"no"|"unreadable", "C": "yes"|"no"|"unreadable", "D": "yes"|"no"|"unreadable"}
```

## Hand-check

Fired extract+sympy items sorted by `id`, first 30. For each, compare extracted latex/ascii to the PNG. Judgment: `parse_correct` / `parse_wrong` / `parse_ambiguous`. Count how many of those 30 have a published key whose transcribed option does not satisfy the extracted equation (`key_does_not_satisfy`).

## Outputs

`exports/addendum-vlm/`: this file, `preregistration.sha256`, `README.md`, `backsolve-extract.json`, `backsolve-extract-items.jsonl`, `hand-check.json`, PNGs under `pages/`. Scripts: `scripts/vlm_backsolve_lib.py`, `scripts/render_solving_item_pages.py`, `scripts/run_vlm_backsolve_extract.py`.

## What this may change in the paper

A later writing pass may replace “backsolving unmeasured” with this cell’s coverage, fired n, rate, and CI, including a fail of the witness bar. n fired >= 10 in a named cell unblocks that sentence even if the rate does not clear. This family cannot say students did not learn.
