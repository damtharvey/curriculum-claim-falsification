# Item Demand Coding (coder-glm)

Independent coding of the 358 New York Regents **Algebra I** masked-stem primary
items (`masked_token_count >= 1`, corpus `nyregents`, id prefix `nyregents-algebra-i-`)
for what answering each item requires.

The coder was blind to the answer key and to any model prediction: the helper
`prepare_items.py` emits `items-to-code.jsonl` with only `{id, stem, options, source}`,
stripping `key`, `predicted`, and all score fields. Coding was done from the original
unmasked stem with options.

## Population and source selection

The 358-item population is the masked-stem primary population for Algebra I
(`masked_token_count >= 1`), taken from
`exports/addendum-gpu/masked-stem-item-mask-stats.jsonl`.

Source priority for each item's stem and options (recorded per item in
`items-to-code.jsonl`):

1. `exports/repaired-layer/repaired-items.jsonl` if it exists (repaired VLM) — not present.
2. `exports/print-faithful/fidelity-items.jsonl` VLM transcription (`vlmStem` +
   `vlmOptions`) — preferred over the text layer when present.
3. `data/items.jsonl` text layer (`stem` + `choices`) — fallback when no VLM
   transcription is available.

Source counts in `items-to-code.jsonl`: `vlm` 352, `text-layer` 6.

The coder did **not** read `exports/standards-split/` cluster classes before or
during coding.

## Rubric (fixed; verbatim)

```
execution: to pick the key you must operate on the specific given quantities (solve, evaluate, compute, factor with these coefficients, rewrite this expression, create an equation from these numbers, graph from this equation, find this value).
recognition_or_interpretation: you can pick the key by recognizing or interpreting the form, meaning, or property named in the wording (which expression is equivalent in form, which statement describes, identify the type of function, interpret a parameter, choose the correct definition, read a feature off a described graph) without computing on the given numbers.
mixed: needs both, or the key needs a small computation that any option-form reading would also give.
```

Rubric SHA-256 (of the three rubric lines above, joined by `\n`):
`ae93b7c651614dd622bba6ff4a9eddbe43c69b4b9ff67407d245365c18b11446`

## Counts per code

| code | count |
|---|---:|
| execution | 212 |
| recognition_or_interpretation | 116 |
| mixed | 28 |
| unreadable | 2 |
| **total** | **358** |

## Example items per code

### execution

- `nyregents-algebra-i-2014-aug-q14` — "What is the average rate of change ... from
  age 20 to age 80?" — Compute average rate of change from table values.
- `nyregents-algebra-i-2014-aug-q15` — "Which expression is equivalent to
  x^4 - 12x^2 + 36?" — Factor perfect-square trinomial with these coefficients.
- `nyregents-algebra-i-2014-aug-q6` — "What is the total profit, P(x), for the
  month?" — Compute P(x)=R(x)-C(x) by subtracting polynomials.
- `nyregents-algebra-i-2014-aug-q8` — "The value of the x-intercept for the graph
  of 4x - 5y = 40 is" — Find x-intercept by setting y=0 and solving 4x=40.
- `nyregents-algebra-i-2015-jun-q10` — "What are the zeros of the function
  f(x) = x^2 - 13x - 30?" — Find zeros by factoring with these coefficients.

### recognition_or_interpretation

- `nyregents-algebra-i-2014-aug-q2` — "y = 40 + 90x. Which statement represents
  the meaning of each part of the function?" — Interpret parameters without
  computing.
- `nyregents-algebra-i-2014-jun-q1` — "Which property justifies Emily's first
  step?" — Identify which property justifies the algebraic step.
- `nyregents-algebra-i-2016-jan-q8` — "A = 1300(1.02)^7 ... What does 1.02
  represent?" — Interpret 1.02 as 2% growth.
- `nyregents-algebra-i-2017-aug-q22` — "r = -0.896557832 ... Which phrase best
  describes the relationship?" — Interpret r as strong negative correlation.
- `nyregents-algebra-i-2018-aug-q8` — "g(x) = (x - 2)^2 + 3 is the result of
  translating f(x) ..." — Interpret translation form from vertex form.

### mixed

- `nyregents-algebra-i-2014-aug-q23` — "A realistic domain for h(t) = -16t^2 +
  144 is" — Need t>=0 recognition and root computation t=3.
- `nyregents-algebra-i-2015-jan-q13` — carnival admission + rides — Set up
  inequality from wording and solve for rides.
- `nyregents-algebra-i-2018-aug-q1` — "P(t) = 300 * 2^4t ... Which expression is
  equivalent?" — Apply power rule and compute 2^4=16 for equivalent form.
- `nyregents-algebra-i-2024-aug-q22` — "5^a + 2^b is equivalent to" — Apply
  exponent rule; needs form recognition only, no numeric evaluation.
- `nyregents-algebra-i-2026-jan-q20` — "Which expression is equivalent to
  (-2x^2)^3?" — Apply power rule and compute (-2)^3=-8 for equivalence.

## Unreadable items

Two items could not be coded because their options reference an unseen list of
equations/properties that is not present in the transcribed stem or options, so
the key cannot be determined from the item text alone.

- `nyregents-algebra-i-2022-aug-q17` — "Which of the equations below have the
  same solution?" — Options are "I and II, only" / "I and III, only" / etc., but
  the equations I, II, III are not in the transcribed stem. Coded `unreadable`,
  confidence low.
- `nyregents-algebra-i-2022-aug-q19` — "Which properties justify George's
  process?" — Options are "A and C" / "A and B" / etc., but the properties A, B,
  C, D are not in the transcribed stem. Coded `unreadable`, confidence low.

## Outputs

- `prepare_items.py` — helper that emits `items-to-code.jsonl`.
- `items-to-code.jsonl` — 358 lines, `{id, stem, options, source}`, sorted by id,
  key/prediction fields stripped.
- `codes.jsonl` — 358 lines, `{id, code, one_line_reason, confidence}`, sorted by
  id.
- `_build_codes.py` — script that wrote `codes.jsonl` from the coded decisions
  (kept for reproducibility; not part of the deliverable contract).

## Notes on coding judgments

- Factoring a polynomial with specific coefficients (e.g., `x^2 - 5x - 6`,
  `x^3 - 13x^2 - 30x`, difference of squares such as `16x^2 - 36`) is coded
  `execution`: the rubric lists "factor with these coefficients" under execution,
  and the key cannot be picked without operating on the given numbers.
- Identifying a function type (linear / exponential / quadratic) from a
  description or table, interpreting a parameter (what the slope or base
  represents), naming the property that justifies a step, and reading a feature
  off a described graph are coded `recognition_or_interpretation`.
- Items that require both a form/wording reading and a small computation (e.g.,
  recognizing a depreciation form and computing the base, applying an exponent
  rule and evaluating a small power, setting up an inequality from wording and
  solving it) are coded `mixed`.
- Items whose stem or options reference a figure (box plot, dot plot, graph,
  pattern of shaded blocks) that is not transcribed in the text are coded by what
  answering them requires (e.g., computing an IQR or a mean from the figure is
  `execution`); confidence is `medium` where the figure data is not in the text.
