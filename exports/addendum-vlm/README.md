# VLM image backsolving

Extract the displayed equation from a page PNG with a cached instruct VLM, then substitute each transcribed option in sympy. The model is not asked to solve and is not asked to pick a letter.

Preregistration was hashed **before** scoring: `exports/addendum-vlm/preregistration.md` sha256 `d6ee8cafd35d04bba7bfd4d4d364ee6f274d715e9b6b7020c454dbdfbd994732`.

## Cached vision models inspected

| Hugging Face id | revision | used |
|---|---|---|
| `Qwen/Qwen2-VL-7B-Instruct` | `eed13092ef92e448dd6875b2a00151bd3f7db0ac` | **yes** (7B instruct, bf16, RTX 5090) |
| `Qwen/Qwen2-VL-2B-Instruct` | `895c3a49bc3fa70a340399125c650a463535e71c` | no |
| `liuhaotian/llava-v1.5-7b` | `4481d270cc22fd5c4d1bb5df129622006ccd9234` | no |
| `llava-hf/llava-v1.6-vicuna-13b-hf` | `745cfbdb14dfeff9bcc6eb731937102e88ea3024` | no |

No `Qwen2.5-VL` download. No bitsandbytes. CUDA required; `.venv` torch 2.14.0+cu130.

## Algebra I (named cell that can clear or fail the bar)

- n eligible (solving-tagged selected-response): **598**
- n with page image: **598**
- n fired unique: **17**
- hits: **14**
- rate among fired: **0.824**
- chance (mean 1/k): **0.25**
- 95% CI (mulberry32 seed 11, 1000): **[0.647, 1.000]**
- coverage (fired / eligible): **0.028**
- rate with abstentions as chance: **0.266**
- **clears witness bar: yes** (n fired >= 10 and lower CI > chance)

Abstentions on Algebra I: no_equation 297, no_parsed_options 238, zero_hits 34, extract_unparseable 8, multiple_hits 4.

## Other cells with n fired >= 10

None. Closest: `teks/alg1` 6/67, `nyregents/algebra-ii` 6/442, `teks/solve-se` 5/21 (rate 1.0, CI [1,1], n too small). EQAO g9 fired 0/52. TIMSS algebra fired 1/14.

Overall: 31 unique fires on 1186 solving-tagged selected-response items.

## Hand-check (30 fired items, sorted by id)

Visual check of PNG vs extracted latex/ascii:

- parse_correct **25**
- parse_wrong **5**
- parse_ambiguous **0**
- key-does-not-satisfy **6**

The five wrong extracts: two missing/wrong relations on a displayed system or inequality; one function item with no equation (`x=2` invented); two word problems where the VLM wrote a formula that was not on the page (compound interest; ticket prices). Those last two are the model solving, which the prompt forbids. They are in the scored file; they were not dropped after looking.

## Exploratory yes/no arm

Not run. Trigger was Algebra I n fired < 10. Observed n fired = 17.

## Unblocks "backsolving unmeasured"?

**Yes, as a measured existence row, not a 67-family Holm test.** Original unique-satisfier n fired = 17 >= 10 in Algebra I. After the audit below, honest n fired = 15 still >= 10 and the lower CI still clears chance. Coverage stays about 2.5%. This channel still does not say students did not learn.

## Audit (paper numbers)

Original `backsolve-extract.json` numbers above are not overwritten. Derived file: `backsolve-extract-honest.json`. Note: `audit-note.md`.

Honest Algebra I (displayed equations only; invent-and-solve and `parse_wrong` recoded as abstain):

- n eligible: **598**
- n fired unique: **15**
- hits: **14**
- rate: **0.933**
- chance: **0.25**
- 95% CI: **[0.800, 1.000]**
- coverage: **15/598 = 0.025**
- **clears witness bar: yes**
- **Holm family member: no**

Dropped: `nyregents-algebra-i-2024-jan-q2` (invented `x=2`, no displayed equation); `nyregents-algebra-i-2018-jan-q10` (`parse_wrong`, incomplete two-graph extract). Kept as miss: `nyregents-algebra-i-2014-aug-q5` (`parse_correct`, item asks which point is not on the graph).

## Files

- `preregistration.md`, `preregistration.sha256`
- `backsolve-extract.json`, `backsolve-extract-items.jsonl` (original scored unique-satisfier)
- `backsolve-extract-honest.json`, `audit-note.md` (Algebra I recode)
- `hand-check.json`
- `page-index.jsonl`, PNGs under `pages/` (gitignored)
- scripts: `scripts/vlm_backsolve_lib.py`, `scripts/render_solving_item_pages.py`, `scripts/run_vlm_backsolve_extract.py`
