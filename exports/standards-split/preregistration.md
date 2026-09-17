# Standards split of the masked-stem Algebra I and Algebra II rows (preregistration)

- Written: 2026-09-17T05:24Z. At this time `item-standards.jsonl` (606 rows, one CCSS cluster code per primary item) and `standards-text.json` (33 clusters) exist on disk, and no per-item prediction file has been joined to either. No pass rate by cluster or by verb class has been computed or looked at.
- Purpose: review-2 weakness 1 and question 2. The claimed masked-stem rows (Algebra I and Algebra II on Qwen2.5-7B-Instruct, Qwen2.5-14B-Instruct, and Phi-4) are used as evidence that on those items a pass does not require executing the tagged computation on the givens. The reviewer objects that for structural algebra tags, recognizing the named form is a reading of the tag. This split asks, per item, whether the publisher's tag names execution on the givens or recognition and interpretation of a form, and recomputes the rows on each class.
- Joining to predictions starts only after `preregistration.sha256` records the sha256 of this file.
- One-sided wording (locked): a pass does not require the tagged operation. Nothing here says students did not learn.
- Does not edit `paper/`. Writes only to `exports/standards-split/` and `scripts/`.

## Unit of the tag (locked)

New York State Education Department (NYSED) rating guides map each Regents question to a Common Core State Standards (CCSS) cluster (for example `A-REI.B`), not to a numbered standard. The tag on an item is therefore the cluster, and the text of the tag is the cluster heading sentence as published by the CCSS, with the numbered standards beneath it as the cluster's content. Codes were read from the rating guides by `scripts/extract_regents_standards.py` (`item-standards.jsonl`; 358 of 358 Algebra I and 248 of 248 Algebra II primary items carry a code; read methods `text_layer` 518, `visual_glyph_match` 57, `glyph_table` 30, `text_layer+visual_overprint_resolution` 1). Cluster text was fetched by `scripts/fetch_ccss_cluster_text.py` from thecorestandards.org (`standards-text.json`, fetched 2026-09-17T05:18:08Z, page sha256 recorded per domain).

## Verb vocabulary (locked)

Each imperative verb that heads a top-level clause of a sentence is classified. Top-level clauses are separated by `;` or by a coordinating `and` / `,` joining two imperatives. `Use X to V` and `use them to V` take the class of the purpose verb `V`; `use X` with no purpose verb is unclassified. Sentences beginning `For example` and non-imperative sentences (`Key features include ...`, `Include ...`) are ignored. Where a verb's class depends on its object, the object is named in the list.

Execution (E), operating on given quantities to produce a value, expression, equation, function, or graph: add, apply (a theorem, rule, or identity), build, calculate, combine, complete (the square), compose, compute, construct (an equation, function, model, table, or graph), create, derive, determine, develop (a margin of error), divide, estimate, evaluate (an expression, a function, or a logarithm), express, factor, find, fit, graph, make (a function or model), multiply, perform (arithmetic operations), produce, rearrange, represent (data or an equation as a plot, graph, or table), rewrite, sketch, solve, subtract, summarize (data), transform, translate (between forms), write.

Recognition or interpretation (R), identifying, comparing, or explaining a form, relationship, or meaning: analyze, choose (among alternatives), classify, compare, construct (an argument), decide, define, describe, distinguish, evaluate (a process, a report, or a claim), explain, identify, illustrate, interpret, justify, know, make (an inference), observe, prove, reason, recognize, relate, say, show, understand.

Unclassified (carry no class and are skipped): extend, experiment, include, model (as a verb), read, use without a purpose verb, verify.

## Cluster rule (locked)

1. Heading class. Classify the verbs of the cluster heading sentence. All E: `execution`. All R: `recognition_or_interpretation`. Both: `mixed`.
2. Fallback. If the heading has no classifiable verb, classify each numbered standard under the cluster that is not marked `(+)` by all of its classifiable top-level verbs (E, R, or mixed), ignoring lettered sub-standards. The cluster is `execution` if every such standard is E, `recognition_or_interpretation` if every such standard is R, and `mixed` otherwise.
3. Primary class of every item = the class of its cluster.

Secondary, disclosed here and reported alongside: `execution_strict` is a primary-`execution` cluster none of whose non-`(+)` numbered standards is purely R under the same sentence rule. It is stricter about calling a tag execution; it is not the primary split.

## Classification of every cluster in use (locked)

Heading verbs are listed as found; `->` gives the class. Fallback clusters list the standards used.

| code | heading | heading verbs | class | strict |
|---|---|---|---|---|
| A-APR.A | Perform arithmetic operations on polynomials. | perform (E) | execution | yes (APR.1 understand R; add, subtract, multiply E: mixed) |
| A-APR.B | Understand the relationship between zeros and factors of polynomials. | understand (R) | recognition_or_interpretation | n/a |
| A-APR.C | Use polynomial identities to solve problems. | use ... to solve (E) | execution | no (APR.4 prove R, describe R: purely R) |
| A-APR.D | Rewrite rational expressions. | rewrite (E) | execution | yes (APR.6 rewrite E, write E) |
| A-CED.A | Create equations that describe numbers or relationships. | create (E) | execution | yes (CED.1 create E, solve E; CED.2 create E, graph E; CED.3 represent E, interpret R; CED.4 rearrange E) |
| A-REI.A | Understand solving equations as a process of reasoning and explain the reasoning. | understand (R), explain (R) | recognition_or_interpretation | n/a |
| A-REI.B | Solve equations and inequalities in one variable. | solve (E) | execution | yes (REI.3 solve E; REI.4 solve E) |
| A-REI.C | Solve systems of equations. | solve (E) | execution | no (REI.5 prove R: purely R) |
| A-REI.D | Represent and solve equations and inequalities graphically. | represent (E), solve (E) | execution | no (REI.10 understand R: purely R) |
| A-SSE.A | Interpret the structure of expressions. | interpret (R) | recognition_or_interpretation | n/a |
| A-SSE.B | Write expressions in equivalent forms to solve problems. | write (E), solve (E) | execution | yes (SSE.3 choose R, produce E; SSE.4 derive E, solve E) |
| F-BF.A | Build a function that models a relationship between two quantities. | build (E) | execution | yes (BF.1 write E; BF.2 write E, translate E) |
| F-BF.B | Build new functions from existing functions. | build (E) | execution | yes (BF.3 identify R, find E, illustrate R; BF.4 find E) |
| F-IF.A | Understand the concept of a function and use function notation. | understand (R), use function notation (unclassified) | recognition_or_interpretation | n/a |
| F-IF.B | Interpret functions that arise in applications in terms of the context. | interpret (R) | recognition_or_interpretation | n/a |
| F-IF.C | Analyze functions using different representations. | analyze (R) | recognition_or_interpretation | n/a |
| F-LE.A | Construct and compare linear, quadratic, and exponential models and solve problems. | construct a model (E), compare (R), solve (E) | mixed | n/a |
| F-LE.B | Interpret expressions for functions in terms of the situation they model. | interpret (R) | recognition_or_interpretation | n/a |
| F-TF.A | Extend the domain of trigonometric functions using the unit circle. | extend (unclassified); fallback TF.1 understand R, TF.2 explain R | recognition_or_interpretation | n/a |
| F-TF.C | Prove and apply trigonometric identities. | prove (R), apply (E) | mixed | n/a |
| G-GPE.A | Translate between the geometric description and the equation for a conic section | translate (E) | execution | yes (GPE.1 derive E, complete the square E; GPE.2 derive E) |
| N-CN.A | Perform arithmetic operations with complex numbers. | perform (E) | execution | no (CN.1 know R: purely R) |
| N-CN.C | Use complex numbers in polynomial identities and equations. | use (unclassified); fallback CN.7 solve E | execution | yes (CN.7 solve E) |
| N-Q.A | Reason quantitatively and use units to solve problems. | reason (R), use units to solve (E) | mixed | n/a |
| N-RN.A | Extend the properties of exponents to rational exponents. | extend (unclassified); fallback RN.1 explain R, RN.2 rewrite E | mixed | n/a |
| N-RN.B | Use properties of rational and irrational numbers. | use (unclassified); fallback RN.3 explain R | recognition_or_interpretation | n/a |
| S-CP.A | Understand independence and conditional probability and use them to interpret data | understand (R), use them to interpret (R) | recognition_or_interpretation | n/a |
| S-CP.B | Use the rules of probability to compute probabilities of compound events. | use ... to compute (E) | execution | yes (CP.6 find E, interpret R; CP.7 apply E, interpret R) |
| S-IC.A | Understand and evaluate random processes underlying statistical experiments | understand (R), evaluate a process (R) | recognition_or_interpretation | n/a |
| S-IC.B | Make inferences and justify conclusions from sample surveys, experiments, and observational studies | make an inference (R), justify (R) | recognition_or_interpretation | n/a |
| S-ID.A | Summarize, represent, and interpret data on a single count or measurement variable | summarize data (E), represent data (E), interpret (R) | mixed | n/a |
| S-ID.B | Summarize, represent, and interpret data on two categorical and quantitative variables | summarize data (E), represent data (E), interpret (R) | mixed | n/a |
| S-ID.C | Interpret linear models | interpret (R) | recognition_or_interpretation | n/a |

Item counts implied by `coverage.json` (computed from the code counts, not from predictions): Algebra I execution 164, recognition_or_interpretation 151, mixed 43 (execution_strict 133); Algebra II execution 120, recognition_or_interpretation 93, mixed 35 (execution_strict 86).

## Join and rows (locked)

Per-item predictions: `exports/addendum-gpu/masked-stem-7b-items.jsonl`, `masked-stem-14b-items.jsonl`, `masked-stem-phi4-items.jsonl` (fields `id`, `chosen_letter`, `key`, `correct`, `n_options`), produced under the frozen masked-stem preregistration with seed 20260916. Print-fidelity verdicts: `exports/print-faithful/fidelity-items.jsonl` (`verdict` in `faithful`, `not_faithful`, `unverified`; pre-registered thresholds).

For each model and each cell (Algebra I primary population, n=358; Algebra II primary population, n=248), report on the subsets `all` (must reproduce the addendum row exactly), `execution`, `recognition_or_interpretation`, `mixed`, `execution_strict`, and the intersections `execution_and_faithful`, `execution_strict_and_faithful`, `recognition_or_interpretation_and_faithful`, `mixed_and_faithful`, `faithful` (must reproduce the print-faithful row exactly): n, passes, pass rate, chance (mean 1/k), percentile bootstrap 95% CI (`score_choices_only_local_lm.bootstrap_ci`, `random.Random(21 + n)`, 1000 replicates, rows in per-item file order), the modal key letter and its frequency on that subset, and the bar. Bar (the channel bar, not loosened): n >= 10, lower CI strictly above chance, lower CI strictly above the subset modal-letter frequency. Per-cluster counts and pass counts are also written so a reader can see which clusters carry a class; no per-cluster row is a claim.

The cleanest claim population is `execution_and_faithful` on Algebra I: items whose tag names execution on the givens and whose text layer matches the printed page.

## Honesty clause (locked)

If `execution_and_faithful` on Algebra I clears the bar on a model, the paper may state, for that model, that on execution-tagged Algebra I items whose print is faithful a pass does not require executing the tagged operation on the givens. If it does not clear, the paper keeps the Algebra I claim at the cell level with the form-recognition caveat stated explicitly, and says that the execution subset did not clear. Algebra II rows are reported the same way; the print-faithful addendum already overrides the Algebra II claim, and nothing here can restore it. A class that clears on `all` but not on `_and_faithful` is reported as not clearing on the faithful population.

## Outputs

`exports/standards-split/`: this file, `preregistration.sha256`, `execution-subset.json`, tables in `README.md`. Script: `scripts/split_masked_stem_by_standard.py`.
