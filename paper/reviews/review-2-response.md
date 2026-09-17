# Response to review 2 (`icml-style-review-2.md`)

Status at 2026-09-17, after the print-fidelity check (`exports/print-faithful/`, commit `2e3ec8c`), the standards split (`exports/standards-split/`, commit `b99d2a1`), the integration pass on the paper body (`8d28f39`, writing `8dff566`), and the option-numeral isomorph control (`exports/isomorph-options/`, commit `462f963`; integrated at `b6ea3d3`, writing `94f3ff1`). Per weakness: what changed, where.

## What is claimed now

| row | before (text layer) | now (print-faithful) | status |
|---|---|---|---|
| NY Regents Algebra I masked-stem, Qwen2.5-7B / 14B / Phi-4 | 0.388 / 0.416 / 0.422, n=358, claimed | 0.467 / 0.429 / 0.467, n=184, all clear chance and modal B 0.255 | **claimed**, with the caveat that the row is carried by recognition-or-interpretation-tagged items; execution-tagged faithful subset (n=75) clears on no model |
| Same row under the option-numeral isomorph control (rank-preserving arm), Qwen2.5-7B / Phi-4 | not run | 0.391 [0.321, 0.462] / 0.408 [0.342, 0.478], n=184; paired difference -0.110 [-0.199, -0.015] / -0.081 [-0.169, 0.015]; both clear chance and modal B 0.255 | form component survives a change of every option value on both scored models; 7B has a numeral-specific component on recognition-tagged items (0.530 to 0.361, no longer clears modal D 0.265 at n=83); 14B not scored (original-letter reproduction 592/606 = 0.977, floor 0.98) |
| NY Regents Algebra II masked-stem, three models | 0.367 / 0.359 / 0.347, n=248, claimed | 0.348 / 0.383 / 0.348, n=115; lower CIs above chance, none above modal B 0.296 | **no longer claimed**; text-layer rows kept as the dirty-layer reference |
| NY Regents geometry lower-central | 90/279 = 0.323 [0.265, 0.380], per-cell witness | 32/99 = 0.323 [0.232, 0.414], covers chance; not-faithful 0.326 | **no longer a per-cell witness**; text-layer residue |
| EQAO grade 6 lower-central | 20/40 = 0.500 [0.350, 0.650], per-cell witness | 8/14 = 0.571 [0.286, 0.857] | claimed, thin, replication candidate; fails the post-hoc strict filter (5/10) |
| Algebra I image-channel backsolving | 14/15, coverage 0.025 | unchanged (reads the page image) | existence row, unchanged |
| STAAR grade 5 closure | Holm reject, failed replication | unchanged | not a discovery, unchanged |
| TIMSS knowing / applying / reasoning | null at n 50 to 80 | unchanged | power-limited non-refutation, billed as such everywhere |
| Catalog family | 105 tests, 0 Holm | unchanged | 0 Holm; residues stated as residues |

## W1. Headline object vs the strongest result (masked-stem Algebra I and II)

Done. Every item in the two algebra masked-stem populations now carries its publisher's tag: the NYSED rating guide maps each Regents question to a CCSS cluster (`exports/standards-split/item-standards.jsonl`, 606/606; 58 guides; three read paths for the guides whose PDF fonts have no character map). The cluster heading verbs were classified under a pre-registered rule (`preregistration.md`, sha `c87a5ae0...`, written before any prediction was joined) as execution / recognition-or-interpretation / mixed; Algebra I is 164 / 151 / 43 items.

Result (`execution-subset.json`, Table `tab:verbclass` in `results.tex`, paragraph "Which tags carry the Algebra I row"): on execution-tagged, print-faithful Algebra I items (n=75) no model clears the channel bar (Qwen 7B 0.360 [0.253, 0.480] vs modal 0.293; Qwen 14B 0.333 [0.240, 0.440]; Phi-4 0.387 [0.293, 0.507], lower bound equal to modal). The recognition-or-interpretation class carries the row (faithful n=83: 0.518 / 0.446 / 0.506 vs modal 0.265, all three clear). The paper now takes the reviewer's option (a): the LM channel is an information-withholding result. Contribution bullet 4 (`intro.tex`), the "What the channel measures" paragraph, the item-22 example (now labelled with its tag, `A-APR.B`, a recognition tag), Limitations, and "What would refute these claims" all say that on the matched items a pass does not require the given quantities, and do not say a pass omits the tagged operation. The item-22 example additionally discloses that the census text layer of that form encodes operators as control bytes and that the item is not print-faithful; it is kept as an illustration only.

Not done: an item-level coding of tags (the split classifies the cluster heading text). Stated in `limitations.tex`.

## W2. Measurement layer is not the printed test

Done (`exports/print-faithful/`, other worker; integrated here). All 955 items in the claimed cells were transcribed from page images by Qwen2-VL-7B-Instruct and compared to the text layer under pre-registered thresholds (sha `0211585e...`; calibration on the 20-item hand audit 17/20, thresholds unchanged): 434 faithful, 502 not faithful, 19 unverified. Every claimed row was recomputed on the faithful subset (Table `tab:faithful`, Section "The text layer against the printed page"). Consequences are in the table above: Algebra I stays and was deflated by the dirt; Algebra II drops; geometry lower-central drops; EQAO grade 6 stays at n=14. Method (`method.tex`, new subsection "Print fidelity and the tag's verb class") states the check; `appendix.tex` carries thresholds, hashes, counts, and the two disclosed post-hoc variants. Limitations state that the faithful subset is not random (pre-2023 forms and word options over-represented) and that residual VLM misreads move items out of the faithful subset, never in.

The 20-item audit count is corrected from 8/8/3/1 to 9/8/2/1: `2023-jan-q8` had been labelled truncated because the audit tool wrote a 400-character preview of the stem; the census stem is complete and matches the print.

## W3. Catalog and TIMSS findings billed above their evidence

Done. Catalog: 105 tests, 0 Holm; the two per-cell rows are now stated as one replication candidate (EQAO grade 6, n=14 faithful, thin) and one text-layer residue (geometry). `tab:witnesses` shows text-layer and print-faithful rows side by side; `tab:middle` marks geometry as failing on print-faithful items. TIMSS: the null is stated as power-limited at n of about 50 to 80 with the clustered floors 0.415 / 0.426 / 0.441 in the contribution bullet, the results, and the limitations. The one-sided claim in Limitations covers the 8 matched faithful EQAO items, the matched faithful Algebra I items, and the 14 image-backsolving items; geometry is removed from it.

## W4. Missing program priors

Done at `6f98bd5` and compiled in this pass. Watson et al. (2018), SAQUET (Moore et al., 2024), PATCH (Fang et al., 2025), and GSM-Symbolic (Mirzadeh et al., 2025) are cited in `related.tex` with entries in `references.bib`; the bib compiles (bibtex warnings are missing-address fields only).

The GSM-Symbolic-style isomorphic-numeral experiment on the options (Q4) is now run (`exports/isomorph-options/`, commit `462f963`; paper at `b6ea3d3`). Preregistration sha `997242b9...`, written before scoring; seed 20260916; masking hash v1. Every numeral in the option strings of the 606 masked-stem Algebra I and II items is replaced by a value-changing, form-preserving isomorph (same digit count, sign, decimal places, comma grouping; consistent substitution within an item; key letter and masked stem unchanged). Primary arm preserves the rank order of the options' leading numbers; secondary arm scrambles it. 61 Algebra I items with no option numeral are unchanged and excluded from the paired difference. Original letters were re-scored from the same model load with a 0.98 agreement floor against the saved predictions: 7B 595/606 = 0.982, Phi-4 606/606 = 1.000, 14B 592/606 = 0.977, so 14B's perturbed arms were not scored.

Result (Table `tab:isomorph`, paragraph "Option-numeral isomorphs" in `results.tex`): Algebra I print-faithful (n=184), rank-preserving: Qwen 7B 0.473 to 0.391 [0.321, 0.462], paired -0.110 [-0.199, -0.015], still clears chance 0.25 and modal B 0.255; Phi-4 0.467 to 0.408 [0.342, 0.478], paired -0.081 [-0.169, 0.015], clears. Pre-registered reading: Phi-4 form-based, 7B mixed (a drop that does not reach chance). Recognition-tagged faithful (n=83): 7B 0.530 to 0.361 (no longer clears modal D 0.265), Phi-4 0.506 to 0.398 (clears). Execution-tagged faithful (n=75): unchanged within intervals, not clearing on either model on the primary arm. Algebra II faithful: unchanged, not clearing. `related.tex` no longer says the substitution has not been run.

## W5. Score-use significance

Not addressed with new data. The paper keeps its student-free object and now claims less (Algebra I only, on print-faithful items, as an information-withholding result). No new human or student data.

## W6. Family splitting and addenda

Disclosed, not changed. The print-fidelity check and the standards split are recomputations of existing rows from saved predictions, hashed before the join, and add no Holm tests.

## W7. Clarity

Partly addressed in this pass: `tab:witnesses` and `tab:middle` now say which rows are claimed after the print check; `tab:masked` caption points to `tab:faithful`; the LM section says at its start that rates are on the text layer unless a paragraph says print-faithful. Writing passes `8dff566` and `94f3ff1` rewrote the abstract (237 words: Algebra I only, claims on print-faithful items, two rows dropped, recognition-tagged items carry the row, the recovery survives a change of the option values), contribution bullet 4, and the captions of `tab:witnesses`, `tab:faithful`, `tab:verbclass`, and `tab:isomorph`; the first-reader record is `paper/abstract-intro-review.json`.

## W8. Contamination

Addressed by the option-numeral isomorph control described under W4 (Table `tab:isomorph`; Limitations paragraph on the numeral-specific component; Appendix `app:lm` paragraph with the preregistration hash, seed, floor, and bootstrap seeds). Interpretation written into the paper: the reader has a form component that survives a change of every option value in both scored models; Qwen 7B additionally has a numeral-specific component on recognition-tagged items, which the control cannot split between memorized option values and value cues that survive the masking; the earlier probes plus this control do not support item memorization as the whole effect and do not rule out a memorized share. Not changed: no paraphrase or stem-rewriting protocol (the stem is already masked; version-2 masking is the stem-side probe); Qwen 14B is excluded by the reproduction floor and its Algebra I row rests on the earlier probes alone.

## W9. Reproducibility from the PDF

Partly: the truncated hashes in Appendix A (image addendum preregistration `d6ee8caf...`, VLM revision `eed13092...`) are now printed in full, and the three new preregistration hashes (print fidelity `0211585e...`, verb classes `c87a5ae0...`, isomorph control `997242b9...`) are printed in full. No code URL yet (anonymous review).

## Minor issues

- Table 4 "yes (not claimed)" for Algebra II lower-central is unchanged; the geometry and EQAO rows in that table now carry their print-faithful status.
- 350,535 trials, proprietary assistant naming, Bonferroni in the abstract: not changed in this pass.
