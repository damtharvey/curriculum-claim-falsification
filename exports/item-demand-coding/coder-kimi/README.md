# Item-demand coding, coder kimi (independent pass)

Each of the 358 NY Regents Algebra I masked-stem items was coded for what answering it
requires, under the fixed rubric below. Coding was done blind: `prepare_items.py` emitted
only `{id, stem, options, source}` per item, and no `key`, `predicted`, or score field was
read or used. `exports/standards-split/` and `exports/item-demand-coding/coder-glm/` were
not read.

## Rubric (verbatim)

```
- `execution`: to pick the key you must operate on the specific given quantities (solve, evaluate, compute, factor with these coefficients, rewrite this expression, create an equation from these numbers, graph from this equation, find this value).
- `recognition_or_interpretation`: you can pick the key by recognizing or interpreting the form, meaning, or property named in the wording (which expression is equivalent in form, which statement describes, identify the type of function, interpret a parameter, choose the correct definition, read a feature off a described graph) without computing on the given numbers.
- `mixed`: needs both, or the key needs a small computation that any option-form reading would also give.
```

sha256 of `rubric.txt` (the text above, verbatim):
`434ed271810ece24b0aa050e9424f0caaf7e3398d5654de7318a558505b6ef18`

## Item universe and text sources

Universe: the 358 `nyregents-algebra-i-*` ids present in both
`exports/addendum-gpu/masked-stem-7b-items.jsonl` and
`exports/print-faithful/fidelity-items.jsonl` (the fidelity file is an exact subset of the
masked-stem file for Algebra I; 50 further masked-stem Algebra I items have no fidelity
record and are outside the stated 358-item universe).

Text source per item, recorded in `items-to-code.jsonl`:

- `vlm` (349): VLM transcription (`vlmStem`/`vlmOptions`) from `fidelity-items.jsonl`.
- `vlm-relocated` (2): corrected re-transcription from `relocated-items.jsonl`
  (`2017-aug-q4`, `2018-jan-q14`), whose original crops held the wrong item.
- `text` (7): PDF text layer, used only where the VLM output was unparseable or incomplete
  (the 5 `vlm_unparseable` items, `2025-jan-q10` with no VLM options, and `2022-aug-q18`
  whose VLM transcription dropped one option).

`exports/repaired-layer/repaired-items.jsonl` does not exist and was not used.

## Counts

| code | n |
|---|---:|
| execution | 249 |
| recognition_or_interpretation | 94 |
| mixed | 15 |
| unreadable | 0 |

Confidence: high 290, medium 52, low 16.

## Examples (5 per code)

### execution

- `nyregents-algebra-i-2014-aug-q14`: Compute average rate of change from specific table values (2.3-4.7)/(80-20).
- `nyregents-algebra-i-2015-jun-q10`: Factor x^2-13x-30 with these coefficients to find zeros.
- `nyregents-algebra-i-2019-jun-q22`: Compute the population standard deviation of the twelve given heights.
- `nyregents-algebra-i-2023-aug-q21`: Create the line equation from the given point and slope.
- `nyregents-algebra-i-2014-jun-q16`: Create a coin-value equation from the specific nickels/dimes numbers.

### recognition_or_interpretation

- `nyregents-algebra-i-2014-jun-q7`: Interpret the parameter 5.25 in the cost function c(r)=5.25r+125.
- `nyregents-algebra-i-2014-jun-q1`: Name the property that justifies adding 9 to both sides.
- `nyregents-algebra-i-2018-aug-q8`: Interpret translation parameters in g(x)=(x-2)^2+3 versus f(x)=x^2.
- `nyregents-algebra-i-2023-jan-q16`: Identify the function type of the halving pattern in the table.
- `nyregents-algebra-i-2022-jun-q21`: Interpret the rate parameter in each exponential equation.

### mixed

- `nyregents-algebra-i-2014-aug-q23`: Interpret realistic domain in context, but endpoint 3 requires solving -16t^2+144=0.
- `nyregents-algebra-i-2016-aug-q4`: Evaluate f(x)=-2x+6 at each table's x-values; small per-option computations.
- `nyregents-algebra-i-2019-jan-q18`: Plug (-1,2) into each candidate pair of equations; small per-option computations.
- `nyregents-algebra-i-2024-jun-q13`: Read Q1 and Q3 off the described box plot and subtract for the IQR.
- `nyregents-algebra-i-2018-jan-q8`: Evaluate the specific radicals' rationality, then apply the product property.

## Unreadable items

None. All 358 items had a readable stem and four options in the chosen source, and the
demand type was codable for every item.

Sixteen items have part of the referenced material missing from every available
transcription (a referenced table, graph, Roman-numeral list, or a sibling equation), so the
specific quantities could not all be verified, but the demand type was still inferable from
the stem wording and option forms; they are coded with `confidence: low`:

- `nyregents-algebra-i-2015-jun-q21` (referenced problem statement missing; options are equation manipulations)
- `nyregents-algebra-i-2016-jun-q15` (referenced table missing)
- `nyregents-algebra-i-2017-jan-q5` (referenced table missing)
- `nyregents-algebra-i-2017-jun-q17` (table for g(x) missing)
- `nyregents-algebra-i-2018-jun-q9` (referenced table missing)
- `nyregents-algebra-i-2018-aug-q23` (the three situations missing)
- `nyregents-algebra-i-2019-jan-q21` (definitions of f, q, p missing)
- `nyregents-algebra-i-2019-jun-q4` (definition of g(x) missing)
- `nyregents-algebra-i-2019-jun-q14` (third function C missing)
- `nyregents-algebra-i-2022-aug-q10` (data representations I/II/III missing)
- `nyregents-algebra-i-2022-aug-q17` (the three equations missing)
- `nyregents-algebra-i-2022-aug-q19` (property labels A-D missing)
- `nyregents-algebra-i-2023-jan-q21` (recursive definition missing)
- `nyregents-algebra-i-2024-jan-q8` (the equation to solve for a missing)
- `nyregents-algebra-i-2024-jun-q16` (dot-plot frequencies missing)
- `nyregents-algebra-i-2026-aug-q3` (the system missing)

## Boundary conventions applied consistently

- Equivalence items with specific coefficients (factor, expand, simplify, exponent-rule
  rewrites) are `execution`: the key cannot be picked without carrying out the rewrite.
- "Which equation/inequality/function represents this situation" with specific numbers is
  `execution` (the rubric's create-an-equation-from-these-numbers clause).
- Interpreting a named parameter, variable, term, property, function family, correlation
  type, or domain meaning is `recognition_or_interpretation`.
- Zeros-to-factors matching (given zeros, pick the factored form) is
  `recognition_or_interpretation` (factor-theorem form reading, no computation).
- Per-option plug-in checks (which point satisfies this equation, which table matches this
  function) and read-a-feature-then-subtract items (IQR from a box plot) are `mixed`.
- Range/domain items where the endpoint must be computed from the given equation (vertex
  formula, solving h(t)=0) are `execution` when the computation is the core demand, `mixed`
  when the demand is primarily contextual interpretation with one small computation.

## Files

- `prepare_items.py`: emits `items-to-code.jsonl` (358 rows, sorted by id, key/prediction
  fields stripped by construction).
- `items-to-code.jsonl`: the blinded coding input.
- `rubric.txt`: the rubric verbatim (sha256 above).
- `codes.jsonl`: 358 coding records `{id, code, one_line_reason, confidence}`, same order as
  `items-to-code.jsonl`.
