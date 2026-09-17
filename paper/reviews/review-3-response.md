# Response to review 3 (`icml-style-review-3.md`)

Paper: *Does the Assessment Require the Skill?* Base commit `92ce56e`. This is a writing and framing pass on the body: no new experiment, no rescoring, no claimed number changed. Per weakness: what changed and where. The post-rebuttal note to review 2 (`icml-style-review-2-post-rebuttal.md`) is answered where it overlaps (its W1, N3, N6, and priority item 1 are the same objection as R3 W1 and W3).

## Framing (Harvey, 2026-09-17)

The subtitle is removed (`main.tex`; the title stays *Does the Assessment Require the Skill?*). The paper adopts the framing of the original proposal (sections 1, 2, 5, 6.3, 8, 15.4). The object is an assessment bypass: a solver policy S that lacks the tagged competency C yet passes under the published scoring rule, S does not model C but Pass(S, T, R) = 1. A deficient policy is defined by explicit restrictions and receives only the information and operations its specification permits. The catalog, strategy, and image-backsolving programs are capability-restricted policies (the tagged operation is not in their instruction set); the masked-stem language model is an information-restricted policy (it has the operations and is denied the given quantities). Same object, two restriction kinds. A witness is a bypass. The pass rate of a deficient family on a cell is a vulnerability measure meaningful only relative to that documented family, never a probability that a student lacks the competency. The five-level claim ladder (Mention, Opportunity, Requirement, Discrimination, Retention and transfer) is in the introduction as Table 1; alignment tools address Mention and Opportunity, this paper tests Requirement, and a bypass refutes Requirement on that cell.

Where: the bypass object with its two restriction kinds is stated once in `intro.tex` (the paragraph after the validity-argument paragraph, followed by the ladder paragraph and Table 1) and once at the top of the Channels subsection of `method.tex`; the vulnerability caveat is in `intro.tex`, `method.tex`, and the first paragraph of `limitations.tex`; the closing paragraph of `related.tex` restates the object; the writing pass puts the bypass phenomenon and the Requirement level in the abstract's first paragraph and the introduction lead, and makes contribution bullet 1 the bypass object with its two restriction kinds. The existing bar, the three Holm families, and the one-sided wording are unchanged.

## W1 / Q1 (critical). Information sufficiency versus operation necessity

Agreed that the masked-stem channel tests whether the given quantities are sufficient for the pass, and that this is not the same statement as the tagged operation being unnecessary. The paper now says so in three places, in plain terms, and says why the first statement still bears on score use.

- `method.tex`, Channels: new opening paragraph, the bypass object and its two restriction kinds. A capability restriction removes an operation: the catalog, strategy, and image-backsolving policies lack the tagged operation because it is not in their instruction set, so a bypass by one of them refutes the claim that the pass requires that operation. An information restriction removes an input: the masked-stem model has the operations and is shown the item with every given quantity withheld, so a bypass by it refutes the claim that the pass requires computing on these givens; it does not refute the claim that the pass requires the abstract relation the tag names, which the policy can apply to the form of the options without the numbers. Score use rests on the first claim: a correct answer is read as evidence that the student carried the operation out on the quantities in front of them, and a key that can be matched without those quantities does not carry that evidence. Each bypass refutes Requirement on its cell for the part of the competency its policy was denied; a family that finds no bypass leaves that part unrefuted.
- `results.tex`, Section 4.3 opening (Partial-input language-model channel): one paragraph naming this as the information-restricted family, what a bypass here refutes and does not refute, with a pointer to the item codings as the way the paper asks which items the reader applies the relation on.
- `results.tex`, the zeros-of-a-polynomial item (January 2023 item 22): the interpretive sentences are rewritten. The reader may well apply the zeros-to-factors relation to the form of the options; what it does not do is compute on the given zeros, because it never sees them. The match is a witness that the pass does not require the given zeros, not a witness that it omits the relation the tag names; the first is the claim score use rests on.
- `related.tex`, closing paragraph: the object is restated as a program that lacks part of what the tag says a pass requires (the operation, or the given quantities it is to be carried out on).

Q1 answered directly: yes, on item 22 the model may be performing the tagged relation on abstract symbols. The masked-stem test does not falsify the tag's relation; it falsifies the claim that passing requires the given zeros. The paper no longer lets a reader take the first for the second.

## W2 / Q3 (major). Template memorization

`limitations.tex`, contamination paragraph, extended. The option-numeral isomorph control rules out memorization of specific values (a key recalled by its printed numbers loses its match when every option numeral changes). It does not rule out memorization of the recurring templates of Regents items, in which a stem type is paired with an option set of a fixed shape administration after administration, and a reader that had learned those templates would keep its rate under a change of values exactly as the form component does. The administration-year probe is flat across four buckets, which speaks against a template that drifted over time and leaves a stable template untouched. The test that would separate a learned template from a property of the item form is novel items written to the same templates that no model has seen, in the manner of a benchmark rewritten in the style of a public one to measure the drop (Zhang et al. 2024, GSM1k, verified); this census has no such items. No claimed number changed.

## W3 / Q2 (moderate). Reliability of the language-model item coders

`limitations.tex`, item-demand paragraph, rewritten. It now states that the item-level coding is by two language models (GLM 5.2, Kimi K3) reading stem and options under one fixed, hashed rubric, blind to the key, to every prediction, and to the cluster split; agreement with each other kappa 0.576 and with the publisher's cluster tag 0.071 and 0.230; no human coded these items and the coders were not validated against human raters, so a coder-versus-tag disagreement can be a coder error as easily as a tag error. It cites verified work on automated Q-matrix generation reliability (Fan and Bialo, IMPS 2025 proceedings, published 2026: language-model Q-matrices agreed with a validated expert Q-matrix at kappa up to 0.63, with wide variation across models and lower agreement on a later re-run). It states that the execution statement is withheld partly because one scorer misses the bar on the both-coders execution subset and partly because that subset rests on two machine codings whose agreement with each other is moderate and with the publisher is slight, and that a human coding would be the measurement that settles the execution statement either way.

Q2 answered: no human gold standard was collected; agreement was measured only between the two coders and against the publisher's tags. That is now stated.

## Relation to prior work (Section 3 of the review)

Citations verified by Crossref before being added:

- Fan, K. and Bialo, J. A. *The Use of AI Tools to Develop and Validate Q-Matrices.* Proceedings of the 90th Annual International Meeting of the Psychometric Society (IMPS 2025), published 2026. DOI 10.64028/imps2025.whsmqf4ego. Added; cited in `limitations.tex` for the reliability of automated Q-matrix construction (the reviewer's *The Use of AI Tools to Develop and Validate Q-Matrices*, 2026).
- Zhang, H. et al. *A Careful Examination of Large Language Model Performance on Grade School Arithmetic.* NeurIPS 2024, pp. 46819 to 46836. DOI 10.52202/079017-1485. Added; cited in `limitations.tex` as the model of the test that would separate a learned template from a property of the item form.

Verified to exist but not cited:

- Rios, O. and Albano, T. *Advancing Item Writing Methods with Large Language Models and Subject Matter Experts.* Applied Measurement in Education 39(1-2):110-124, 2026. DOI 10.1080/08957347.2026.2655640. Crossref has no abstract and the publisher page did not load, so the content could not be checked; the reviewer's characterization (that language models replicate cueing biases) could not be confirmed against the text, and a citation whose content we have not read is not added.
- Menze, D., Radović, S., and Seidel, N. *AI-assisted MCQ creation increases item-writing flaws through automation bias.* Frontiers in Computer Science 8:1831250, 2026. DOI 10.3389/fcomp.2026.1831250. Verified with abstract (AI-written items carry stem-to-key lexical overlap). It concerns items written by language models, not items read by them, and no sentence in the three fixes above needs it, so it is not added.

Not found on Crossref or Semantic Scholar under the titles the reviewer gives, so not cited:

- *Are Large Language Models Truly Smarter Than Humans? Benchmark Contamination, Surface-Pattern Reliance, and Behavioral Memorization Across Six Frontier Models* (2026).
- *JudgmentBench* (2026).

## Minor issues

Not changed in this pass: the Holm-family repetition across Section 2.2 paragraphs and an early displayed definition of format chance. Both are readability edits outside the three fixes above and are left for a later pass.

## Hackathon audience note

Already the paper's stated position: a witness is a fact about a key and a program, not about students; the paper never says students do not learn. The framing paragraph in `method.tex` adds why the fact bears on score use anyway: the tag is read as evidence that the student computed on the givens, and a key that can be matched without them does not carry that evidence, whatever the student did.

## Writing-correction pass (second commit)

- `main.tex`: `\subtitle{...}` removed; title unchanged.
- `abstract.tex`: first paragraph states the bypass phenomenon and the Requirement assumption before any channel is named ("a correct answer is read as evidence of that competency, a reading that assumes passing requires it. We test the requirement by searching for assessment bypasses: solver policies that lack the tagged competency, by an explicit restriction on their operations or information, yet pass under the published scoring rule"). The closing sentence on the item codings now says the bypasses are information-restricted and leaves the tagged-operation question open instead of calling the claim narrower. 242 words by a token count that includes numerals; no number added or changed.
- `intro.tex`: lead sentence states the Requirement question in plain words ("this paper asks whether that claim holds at the level of requirement: whether a solver that lacks the tagged competency can still pass under the published scoring rule"); contribution bullet 1 is the bypass object with its two restriction kinds; bullet 4 says the language-model bypasses are information-restricted and leaves the operation question open.
- `abstract-intro-review.json`: first-reader record for this pass.

## Note for Harvey: title

The subtitle is removed and the title *Does the Assessment Require the Skill?* is kept, per Harvey. The title asks the Requirement question about the tagged skill. The strongest positive rows (masked-stem Algebra I and II) are information-restricted bypasses: they refute that the pass requires computing on the given quantities, and the paper says explicitly that they do not refute the relation the tag names. The capability-restricted bypasses (image backsolving 14 of 15, the two per-cell catalog rows) address the skill directly but are small or uncorrected. Under the bypass framing the title reads as the question the paper measures a part of on each cell, refuted for the givens on the algebra cells and for the operation on the small rows, rather than a question answered with one yes. That reading is consistent with the body; whether it is the intended reading of the title is Harvey's decision, and nothing in this pass changes the title.

## Still open

From review 2 post-rebuttal: W5 (score-use evidence with students), W6 (family graph lock), Q5 (constraint-elimination key kills not joined to tags), Q6 (instruction-only), human coding of item demand, code URL.
