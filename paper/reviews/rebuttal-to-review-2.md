# Author response to Reviewer 2

Review: `paper/reviews/icml-style-review-2.md`, written against `origin/main` HEAD `8c086c7`. This response covers the revision `3a8fde2..HEAD` (commits `6f98bd5`, `2e3ec8c`, `b99d2a1`, `8d28f39`, `8dff566`, `462f963`, `b6ea3d3`, `94f3ff1`). Section and table numbers below refer to the PDF at `94f3ff1` (`paper/main.pdf`, 19 pages). The working ledger behind this response is `paper/reviews/review-2-response.md`.

We thank the reviewer for a review whose weaknesses could be turned into experiments. Three of them were: a mechanical print-fidelity check of every item in the claimed cells (W2, Q1), a pre-registered verb-class split of every publisher's tag in the two algebra populations (W1, Q2), and a pre-registered option-numeral isomorph control on the masked-stem reader (W4, W8, Q4). Each was hashed before scoring or before any prediction was joined to a tag. No new Holm test was added. The paper claims less than it did: Algebra II masked-stem and New York Regents geometry lower-central are no longer claimed, and the language-model row is stated as an information-withholding result on recognition-tagged items rather than as a witness that a pass omits the tagged operation.

## What is claimed now

| Row | At `8c086c7` (text layer) | Now (print-faithful items) | Status |
|---|---|---|---|
| NY Regents Algebra I masked-stem, Qwen2.5-7B / 14B / Phi-4 | 0.388 / 0.416 / 0.422, n=358, claimed | 0.467 / 0.429 / 0.467, n=184; all clear chance 0.250 and modal B 0.255 (Table 10) | claimed; carried by recognition-or-interpretation-tagged items (n=83: 0.518 / 0.446 / 0.506 vs modal D 0.265, Table 11); execution-tagged faithful items (n=75) clear on no model |
| Same row, option-numeral isomorph control, rank-preserving arm, Qwen2.5-7B / Phi-4 | not run | 0.391 [0.321, 0.462] / 0.408 [0.342, 0.478], n=184; paired difference -0.110 [-0.199, -0.015] / -0.081 [-0.169, 0.015]; both clear (Table 6) | form component survives a change of every option value on both scored models; Qwen 7B has a numeral-specific component on recognition-tagged items (0.530 to 0.361, no longer clears modal D 0.265); Qwen 14B not scored (reproduction 592/606 = 0.977, floor 0.98) |
| NY Regents Algebra II masked-stem, three models | 0.367 / 0.359 / 0.347, n=248, claimed | 0.348 / 0.383 / 0.348, n=115; lower CIs 0.261 / 0.287 / 0.270 above chance, none above modal B 0.296 (Table 10) | no longer claimed; text-layer rows kept in Table 8 as the dirty-layer reference |
| NY Regents geometry lower-central | 90/279 = 0.323 [0.265, 0.380], per-cell witness | 32/99 = 0.323 [0.232, 0.414]; not-faithful 0.326 (Table 3) | no longer a per-cell witness; text-layer residue |
| EQAO grade 6 lower-central | 20/40 = 0.500 [0.350, 0.650], per-cell witness | 8/14 = 0.571 [0.286, 0.857] (Table 3) | claimed as a thin replication candidate; fails the disclosed post-hoc strict filter (5/10) |
| Algebra I image-channel backsolving | 14/15, coverage 15/598 = 0.025 | unchanged (reads the page image) | existence row, unchanged |
| STAAR grade 5 arithmetic closure | discovery Holm reject 21/40 = 0.525; powered replication 21/64 = 0.328 [0.219, 0.438] | unchanged | not a discovery, unchanged |
| TIMSS knowing / applying / reasoning | null at public selected-response n=65 / 54 / 68; clustered 80% floors 0.415 / 0.426 / 0.441 | unchanged | power-limited non-refutation, billed as such in the abstract, contribution bullet 4, Section 4.3, and Section 5 |
| Catalog family | 105 tests, 0 Holm | unchanged | 0 Holm; residues stated as residues |

## W1. The headline object and the strongest positive result are different experiments

What changed. Every item in the two algebra masked-stem populations (358 Algebra I, 248 Algebra II) now carries its publisher's tag, the CCSS cluster the NYSED rating guide assigns to that question (606 of 606 joined; Appendix A.5). The verbs of each cluster heading were classified under a rule written and hashed before any prediction was joined to a tag (`c87a5ae0...`, printed in full in Appendix A.5) as execution, recognition or interpretation, or mixed; Algebra I is 164 / 151 / 43 items. Section 3.4 states the rule; Section 4.6, paragraph "Which tags carry the Algebra I row", and Table 11 give the rows. On execution-tagged, print-faithful Algebra I items (n=75) no model clears the channel bar: Qwen 7B 27/75 = 0.360 [0.253, 0.480] clears chance but not modal B 0.293; Qwen 14B 25/75 = 0.333 [0.240, 0.440] clears neither; Phi-4 29/75 = 0.387 [0.293, 0.507] has a lower bound equal to the modal frequency (22/75). The recognition-or-interpretation class carries the row: on those faithful items (n=83) all three models clear (0.518, 0.446, 0.506 against modal D 0.265). We took the reviewer's option (a). The scope paragraph of Section 1, contribution bullet 4, the paragraph "What the channel measures" in Section 4.5, the item-22 example (now labelled with its tag, A-APR.B, a recognition tag), Section 5, and "What would refute these claims" say that on the matched items a pass does not require the given quantities, and none of them says a pass omits the tagged operation. The item-22 example also discloses that the census text layer of that form encodes operators as control bytes and that the item is not print-faithful; it is kept as an illustration only.

What we did not change. The split classifies the text of the cluster heading, not each item's demand; an item-level coding of the tags was not done, and Section 5 says so. The title and subtitle are unchanged; they describe the catalog and strategy families, and the language-model row is now labelled in the abstract and the body as the information-withholding result it is.

## W2. The measurement layer is not the printed test

What changed. All 955 items in the claimed cells (Algebra I masked-stem 358, Algebra II masked-stem 248, geometry lower-central fired 279, EQAO grade 6 lower-central fired 40, geometry masked-stem 166, with 136 geometry items in both geometry cells) were transcribed from the rendered page image by Qwen2-VL-7B-Instruct, never asked to solve or pick a letter, and compared to the text layer token by token under thresholds hashed before any population item was scored (`0211585e...`, Appendix A.4). Calibration on the 20 hand-audited items agreed on 17 of 20 against a pre-registered floor of 16, so the thresholds were not adjusted. Verdicts: 434 print-faithful, 502 not faithful, 19 unverified. Section 3.4 states the check; Section 4.6 and Table 10 recompute every row claimed on the text layer on the faithful subset and on its complement with the same bootstraps and bars. Algebra I masked-stem clears on faithful items for all three models (0.467 / 0.429 / 0.467, n=184, against chance 0.250 and modal B 0.255) and its faithful rate is above its not-faithful rate on every model (0.292 / 0.393 / 0.363), so the dirty layer deflated that row. Algebra II masked-stem does not clear the modal-letter bar on faithful items on any model (lower CIs 0.261 / 0.287 / 0.270 against modal 0.296) and is no longer claimed. Geometry lower-central keeps its rate on faithful items (32/99 = 0.323) and loses its interval ([0.232, 0.414]); it is no longer a per-cell witness. EQAO grade 6 clears on 14 faithful items (8/14 = 0.571 [0.286, 0.857]) and is billed as thin. The 20-item audit count is corrected from 8 / 8 / 3 / 1 to 9 / 8 / 2 / 1: January 2023 item 8 had been labelled truncated because the audit tool printed a 400-character preview of the stem; the census stem is complete and matches the print.

What we did not change. We filter to faithful items rather than repair the text layer, so the claims are existence claims on items whose text matches the print and not rate estimates on the full cell; Section 4.6 and Section 5 say the faithful subset over-represents administrations before 2023 and, in Algebra I, items with word options (40 percent against 10 percent). The check errs in one direction (a transcription mistake moves an item out of the faithful subset, never into it), which is stated in Section 5.

## W3. Catalog and TIMSS findings billed above their evidence

What changed. The abstract says the item-writing rules yield no family-wise discovery and that one rule beats chance on one cell and awaits replication. Contribution bullet 4 names EQAO grade 6 as the replication candidate and New York Regents geometry as not claimed. Table 3 shows the text-layer and print-faithful rows side by side, and Table 4 marks geometry as failing on print-faithful items. The 17-cell one-rule Holm slice remains labelled exploratory in Section 4.3. TIMSS is stated as a power-limited non-refutation in the abstract (each cell about 50 to 80 public items), in contribution bullet 4, in Sections 4.2 and 4.3 (clustered floors 0.415 / 0.426 / 0.441 on selected-response n=65 / 54 / 68), and in Section 5. The one-sided claim in Section 5 covers the 8 matched faithful EQAO items, the matched faithful Algebra I items, and the 14 image-backsolving items; geometry is removed from it.

What we did not change. The TIMSS null stays in the contribution list because a null at that n with a searcher validated on OpenBookQA and SWAG is a statement about what this program space can and cannot see on those public items, and the power floors are printed next to it.

## W4. Closest priors are missing

What changed. Watson et al. (2018), the SAQUET item-writing-flaw detectors (Moore et al., 2024), PATCH (Fang et al., 2025), and GSM-Symbolic (Mirzadeh et al., 2025) are cited in Section 2 (commit `6f98bd5`). The increment over Watson et al. is stated against that paper: a priori hashed rules rather than a fitted classifier, tagged public mathematics, Holm correction within each family, and no student reference. The collective-advance paragraph names those four vertices before saying what remains unscored. The GSM-Symbolic-style substitution the reviewer asked for is now run on the option strings (commit `462f963`, integrated at `b6ea3d3`): Section 4.5, paragraph "Option-numeral isomorphs", Table 6, Section 5, and Appendix A.2. Preregistration `997242b9...` (printed in full in Appendix A.2) was written before scoring; seed 20260916; masking version 1. Every numeral in the option strings of the 606 masked-stem Algebra I and II items is replaced by a value-changing, form-preserving isomorph (same digit count, sign, decimal places, and comma grouping; consistent substitution within an item; masked stem and key letter unchanged). The primary arm preserves the rank order of the options' leading numbers and a secondary arm scrambles it. The 61 Algebra I items with no option numeral are unchanged and excluded from the paired difference. Original letters were re-scored from the same model load under a pre-registered 0.98 agreement floor against the saved predictions: Qwen 7B 595/606 = 0.982 and Phi-4 606/606 = 1.000 cleared; Qwen 14B 592/606 = 0.977 did not, so its perturbed arms were not scored. On the 184 print-faithful Algebra I items, rank-preserving: Qwen 7B 0.473 to 0.391 [0.321, 0.462], paired difference -0.110 [-0.199, -0.015], still clears chance and modal B 0.255; Phi-4 0.467 to 0.408 [0.342, 0.478], paired difference -0.081 [-0.169, 0.015], clears. Under the pre-registered reading Phi-4 is form-based and Qwen 7B is mixed, a drop that does not reach chance. On recognition-tagged faithful items (n=83) Qwen 7B goes from 0.530 to 0.361 and no longer clears modal D 0.265; Phi-4 goes from 0.506 to 0.398 and clears. Execution-tagged faithful items (n=75) are unchanged within their intervals and do not clear on the primary arm. Algebra II faithful rows are unchanged and do not clear. Section 2 no longer says the substitution has not been run.

What we did not change. We did not run Watson et al.'s classifier on our items or add an IRT analysis; the object here is a hashed a priori program, and the comparison to that line is stated in prose rather than as a column.

## W5. Score-use significance is not evidenced

What changed. The paper claims less: Algebra I only, on print-faithful items, as an information-withholding result on recognition-tagged items, with a value-change control. No new human or student data were collected.

What we did not change. The object is student-free by construction, and the paper says in Section 1, Section 5, and the abstract that a witness is a fact about a key and a program and is not a claim that students use the program or failed to learn. Closing the score-use argument with examinee data is a different study.

## W6. Family splitting and addenda as analysis path

What changed. Nothing in the family structure. The three additions in this revision (print-fidelity check, verb-class split, isomorph control) are recomputations or controls on existing rows from saved per-item predictions, each hashed before scoring or before the join (`0211585e...`, `c87a5ae0...`, `997242b9...`), and none adds a Holm test. Section 3 and Appendix A state which hash covers which step.

What we did not change. The three families (105 catalog, 67 strategy, 68 language-model tests) and the scoring-day lock are as described; the image addendum and the four post-primary catalog cues remain disclosed addenda outside those counts.

## W7. Clarity at the Strong-Accept bar

What changed. Two writing passes (`8dff566`, `94f3ff1`) rewrote the abstract (237 words) so that it says Algebra I only, that claims are made on items whose text matches the printed page, that two rows that cleared on the text layer fail there, that recognition-tagged items carry the language-model row, and that the recovery survives a change of the option values. Contribution bullet 4 says which rows survived the print check and which are not claimed. Section 4.5 opens by saying that its rates are on the text layer unless a paragraph says print-faithful and that the print-faithful recomputation is Section 4.6. The captions of Tables 3, 4, 6, 8, 10, and 11 say which rows are claimed, and gloss lower-central (second-smallest numeric option) and masked-stem (given quantities withheld) where those terms appear. The first-reader record is `paper/abstract-intro-review.json`.

What we did not change. The status vocabulary (per-cell bar, family-wise, claimed, not claimed) remains, because the paper's discipline is that a row can clear a per-cell bar and still not be claimed; Table 4's Algebra II entry still reads "yes (not claimed)" with the caption stating why.

## W8. Contamination and leakage controls

What changed. The option-numeral isomorph control described under W4 is the isomorphic-item test the reviewer named: same masked stem, same key letter, same models, same letter rule, every option value changed with the form kept. Table 6 gives original, rank-preserving, and scrambled rates with paired differences on faithful items and on the two verb classes. Section 5 states the interpretation: the reader has a form component that survives a change of every option value in both scored models; Qwen 7B additionally has a numeral-specific component on recognition-tagged items, which the control cannot split between memorized option values and value cues that survive the masking; the earlier probes (log-probability quartiles, recency, permutation, version-2 masking) plus this control do not support item memorization as the whole effect and do not rule out a memorized share. Appendix A.2 records the preregistration hash, seed, floor, agreement counts, no-numeral counts, bootstrap seeds (21+n and 31+n, 1,000 replicates), and one before-and-after option set.

What we did not change. No paraphrase or stem-rewriting protocol was run, because the stem's quantities are already replaced by placeholders and version-2 masking is the stem-side probe. Qwen 14B is excluded from the control by the reproduction floor, and its Algebra I row rests on the earlier probes alone, which Section 5 states.

## W9. Reproducibility from the PDF alone

What changed. Every hash named in the text is printed in full in Appendix A: the strategy rule file, the image-addendum preregistration and VLM revision (previously truncated), masking versions 1 and 2, the print-fidelity preregistration, the verb-class rule, and the isomorph preregistration. Model revisions, seeds, filter counts, thresholds, and bootstrap seeds are in Appendix A.

What we did not change. No code or data URL is in the PDF while the review is anonymous, and no item-id table was added beyond the two worked items; the frozen JSONL and scripts will be released with the de-anonymized version.

## Q1. Do the intervals still clear on the print-faithful subset?

Answered by the full-population check rather than a sample (W2). Algebra I masked-stem: yes, on all three models (0.467 / 0.429 / 0.467, n=184, lower CIs 0.391 / 0.359 / 0.397 against chance 0.250 and modal 0.255; Table 10). Algebra II masked-stem: no, the lower CIs (0.261 / 0.287 / 0.270) are above chance but below modal 0.296, so the row is not claimed. Geometry lower-central: no, 32/99 = 0.323 with interval [0.232, 0.414], so the row is not claimed. EQAO grade 6: yes at n=14, 8/14 = 0.571 [0.286, 0.857], billed as thin.

## Q2. Execution on the givens versus recognition of a form

Answered (W1). On the text layer Algebra I is 164 execution, 151 recognition or interpretation, and 43 mixed; on print-faithful items 75, 83, and 26. The claimed hits sit in the recognition-or-interpretation class (all three models clear at n=83) and in the mixed class (n=26); the execution class clears on no model at n=75. Contribution bullet 1 keeps the object as defined. The scope paragraph of Section 1 and contribution bullet 4 state the language-model channel as an information-withholding result: what the model lacks is the given quantities, not an operation, and on the matched items a pass does not require those quantities.

## Q3. Watson et al. (2018)

Cited and positioned in Section 2 (W4). We did not run their classifier on our items, so there is no numeric comparison on a shared item set; our census has no AAAS science items, and their features (length, stem-option and option-option similarity, keyword cues) overlap the catalog rules whose per-cell rates are in Tables 3 and 4. A student percent-correct column was not added: the object is defined without student data, and Section 5 keeps the boundary that a witness is a fact about a key and a program.

## Q4. Isomorphic numeral substitution in the options versus the stem

Answered by the isomorph control (W4, W8, Table 6). In the options: on print-faithful Algebra I the masked-stem rate tracks option-form isomorphism on both scored models (rank-preserving 0.391 and 0.408, both above the bar), with a partial collapse on Qwen 7B recognition-tagged items (0.530 to 0.361) that does not reach chance. The scrambled arm is reported and is not the primary reading (Qwen 7B 0.391, Phi-4 0.446 on faithful items). In the stem: the stem's numerals are already replaced by placeholders in the masked condition, so substitution there is empty; the stem-side probe is version-2 masking (named figures, bindings, leftover coefficients), which changes the rate by -0.007. Qwen 14B was not scored on the perturbed arms because its re-scored original letters agreed with the saved letters on 0.977 of 606 items, below the pre-registered 0.98 floor.

## Q5. Constraint elimination killing the published key

Not changed. The two intersections (probability with percent-point options; interior-angle (0,180) on a rectangle angle-sum) are logged in the strategy addendum (`exports/addendum-strategies/README.md`) as errors of the constraint rule, not as tag-program mismatches, and Section 4.4 reports key-survival on every headline cell (geometry 0.985, EQAO grade 6 0.906, TEKS grade 8 0.877; hand check 13 of 15 keys kept). The publisher's tags of those two items were not joined: the verb-class split covers the two algebra masked-stem populations only.

## Q6. Instruction-only

Not changed. It is a data-access problem: the protocol lists instruction-only as a channel to be run when curricula with scoring keys are ingested, and no public file we could ingest carried them. Had it run it would have been its own family with Holm inside, as the other channels are, and its absence did not alter how the three scored families were defined.

## Minor issues

- Abstract correction vocabulary: the abstract now names Holm only ("each Holm-corrected for multiple testing on its own"); Bonferroni appears in Section 4.3 as a second cut on the same family.
- Table 1 RACE row: unchanged; the row reads "no (n<10)" and the caption says RACE yields no witness here.
- Table 4 Algebra II "yes (not claimed)": unchanged; the caption states that Algebra II clears the per-cell bar and is not claimed, and Section 4.3 gives the reason (lower end of the interval on chance).
- Truncated hashes: fixed; every hash is printed in full (W9).
- 350,535 local trials: unchanged in the paper; the number is the line count of the trial log `exports/trials-census.jsonl` (one record per program applied to one item, skipped trials included; 294 program ids over 2,405 items), not a product of 1,847 programs and a cell count, and the paper does not yet give that arithmetic.
- Proprietary options-only assistant: unchanged and still unnamed.
- TIMSS 2011 public-together claim: unchanged; no IEA release-policy citation was added.
- Title and subtitle: unchanged (W1).

## Still open after this revision

An item-level coding of the tags (W1). A repaired text layer rather than a faithful-item filter (W2). Student or examinee data (W5, Q3). A locked protocol naming the families before any pass rate existed (W6). Qwen 14B under the isomorph control (W8). A code URL in the PDF (W9). The title and subtitle against the information-withholding restatement, the 350,535-trial arithmetic, the unnamed proprietary scorer, and the IEA citation (minor issues).
