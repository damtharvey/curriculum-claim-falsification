# ICML-style review

Paper: *Does the Assessment Require the Skill? A Public-Release Census of Requirement versus Mention*

Venue context (not scored): Minds & Machines hackathon preprint, acmart/sigplan, 11 pages. Formatting, length, and venue are out of scope for this review. The scores below apply the scientific bar only (claims/evidence, prior work, originality, significance, clarity of argument, reproducibility).

## Compact dimension ratings (1–5)

| Dimension | Score | Note |
|-----------|------:|------|
| Originality | 3 | Witness/requirement framing on tagged public exams is distinctive; the LM channel is a close neighbor of existing choices-only MCQA work. |
| Importance | 3 | The validity question is real; the supported positives are item-subsets, not exam-level or TIMSS-domain refutations. |
| Claims and evidence | 3 | One-sided wording is disciplined; a few claimed rows do not survive the paper’s own splits or exports. |
| Experimental soundness | 3 | Pre-registration, Holm families, and a failed replication are above field average; OCR construct and missing human ratings are not. |
| Clarity of argument | 3 | Claims are mostly precise; the unused requirement matrix and dense family-counting make the lead hard to keep straight. |
| Community value | 4 | Reusable census, hashed protocols, and an honest null-plus-failed-replication are useful even when positives are modest. |
| Prior work | 2 | Core adjacent papers on choices-only LLMs and middle-key psychometrics are missing. |

---

## 1. Summary

The paper asks whether matching the published key of a tagged mathematics item requires the tagged operation, or whether a program that lacks that operation (or the given quantities) can still match the key. The object is a one-sided witness: a pass on a matched item does not require the tagged operation; failure to find a witness does not certify the tag. Students are not measured.

On 2,405 public-release items (New York Regents, STAAR/TEKS, EQAO, TIMSS 2011 and earlier public cycles, plus smaller PISA/NAPLAN/MCAS/NYSED sets), three Holm-corrected families are scored: 105 a priori catalog item-writing rules, 67 hashed adaptive strategies, and 68 withheld-quantity masked-stem language-model tests.

Headline results as stated: (i) no catalog row survives Holm; two per-cell catalog witnesses remain, both a signed lower-central numeric cue (Regents geometry 90/279 = 0.323; EQAO grade 6 20/40 = 0.500); (ii) arithmetic closure on STAAR grade 5 is the only strategy Holm reject on the discovery set (21/40 = 0.525) and fails a powered replication (21/64 = 0.328, CI covers chance); (iii) a letter-argmax reader exists on Qwen2.5-7B, Qwen2.5-14B, and Phi-4 for withheld-quantity Regents Algebra I and Algebra II, and on Phi-4 only for geometry; Mistral-7B-Instruct-v0.3 is a weak solver and does not clear the same bar; (iv) no catalog, strategy, or partial-input program clears its channel bar on TIMSS knowing, applying, or reasoning at clustered floors the paper places near 0.40. Controls recover published shallow-cue rates on OpenBookQA and SWAG. Human masked-stem ratings and backsolving are marked unfinished.

---

## 2. Claims and Evidence

The logical claim is well posed. “Require” is treated as necessity: if a program that lacks operation *o* matches the published key, then *o* is not necessary for a pass on that item. The paper repeatedly scopes this to the matched subset and refuses the converse. That is the right claim for a falsification census, and it is better than the usual “students do not know X” overread.

**Supported.**

- *Catalog existence on named items.* The EQAO grade 6 example (tenths-digit stem; key recovered as the second-smallest option) is a clean existence proof: the program never inspects tenths digits. Geometry 90/279 = 0.323 with item CI [0.265, 0.380] and clustered CI still above 0.25 is a small but real lift on a large cell. Neither row survives Holm on 105 tests; the paper says so. Algebra II is correctly left unclaimed because the interval sits on chance. Spot-check against `exports/apriori-cell-table.json` matches (105 tests, 0 Holm rejects, 90/279 and 20/40).
- *Strategy discovery-then-replication.* STAAR grade 5 closure 21/40, Holm in the 67-test family, then a hashed parse repair and later administrations yielding 21/64 = 0.328 with CI [0.219, 0.438] is the strongest methodological result in the paper. Reporting a failed replication instead of stretching the discovery row is rare and credible. Depth-1 / no-geometry-extras robustness on the discovery set, and the note that 13/40 discovery stems contain artifact numerals, are the right caveats.
- *Algebra I / II masked-stem, capable scorers.* Withheld-quantity Algebra I (n=358) and Algebra II (n=248) clear chance and the cell modal letter on Qwen 7B, Qwen 14B, and Phi-4. The information ladder (options-only < masked-stem < with-stem) is the right design. Cue attribution on Qwen 14B Algebra I, with residual 0.442 on 163 items where four catalog cues do not point at the key, is the evidence that this is not just lower-central or longest-option. Phi-4 Algebra I non-modal-key rate 0.387 (n=261, CI above 0.25) agrees. Contamination probes (recency flat, option permutation, version-2 masking, mean-logprob quartiles) are adequate as negative evidence for rote exam memorization. Mistral’s with-stem ceiling matching its masked-stem rate is the right control for “the channel needs a solver.” TEKS grade 5/8 7B-only rows are correctly unclaimed.
- *TIMSS as a null, not a certification.* The paper does not claim TIMSS tags are valid. That discipline should be kept.

**Not fully supported, or weaker than the prose.**

1. *Phi-4 geometry is not the same object as Algebra I/II.* The paper claims geometry on Phi-4 at 67/166 = 0.404, CI [0.331, 0.476], versus chance 0.250 and modal B 0.289. The export `exports/addendum-gpu/masked-stem-phi4.json` reports a non-modal-key split on that same n=166: 0.229 (n=118, CI [0.161, 0.305]), which does not beat chance. Combined with 67 total hits, that is about 40/48 on B-keyed items and 27/118 otherwise. The cell-level bar (lower CI above the modal frequency) can be cleared by a letter prior. Qwen geometry already fails the same bar. Geometry on Phi-4 should not be listed with Algebra I/II as a form-recognition witness. The Algebra I residual analysis is exactly the check this row needed and did not get in the paper.

2. *Masked-stem “does not require the tagged operation” is not the same inference as the catalog.* Limitations correctly say the model has the operations and that the withheld object is information. The abstract’s last sentence still treats LM-matched items as cases where accountability is “reading the wrong quantity” for the tagged skill. The January 2023 Algebra I zeros example is the problem: recovering the three-factor option from three placeholders is knowledge of the tagged concept (zeros as factors), not a content-free cue. Adjacent MCQA work (Balepur et al., ACL 2024) already shows that choices-only success can be abductive reconstruction of the question rather than a surface shortcut. The paper’s own “it may require recognizing the form the wording names” is the accurate claim; the accountability sentence is a step stronger than that.

3. *EQAO grade 6 is index-specific and small.* n=40, only the pre-registered lower-central index clears, upper-central is 0.250. The clustered CI [0.417, 0.588] is tighter than the item CI [0.350, 0.650] with three years. Clustered intervals are usually wider; with k=3 the bootstrap is poorly calibrated. The per-cell existence claim can stand; “a stable middle-value property of EQAO grade 6” cannot.

4. *TIMSS clustered floors in the paper do not match the clustered-power export.* Table 2 reports clustered floors 0.400 / 0.407 / 0.421. `exports/addendum/power-by-cell.json` gives 0.415 / 0.426 / 0.441 on selected-response n=65/54/68. Using the smaller numbers makes the null look more powered than the addendum. Independent-item floors 0.358/0.353/0.372 match `exports/cell-power.json`. The TIMSS null is still a null; it is not an informative “we would have seen 0.40.” Public TIMSS n is small, later cycles are unavailable, and the first-run TIMSS knowing rate 0.657 was carried by unmasked items. That last point is well reported.

5. *The requirement matrix E[t,o] is not delivered.* The introduction defines an item-by-operation table over retrieve/execute/bind/distinguish/explain/transfer. Results are cell-level pass rates for programs, not that matrix. Shared operations are not scored as columns.

6. *Construct of the item file.* The human-rater packet documents multiple Algebra I census rows whose OCR/options do not match the printed item (glued equations, truncated stems, sign errors, footer leak). STAAR replication found the same class of last-option leaks. Catalog and LM rates are computed on this text layer. Parse error is not a rival program that lacks the tagged operation; it is a different item.

Human 40-item ratings are marked unfinished. Until they exist, the LM channel is a fact about letter-argmax models, not about whether a human can match the key from the same slice.

---

## 3. Relation to Prior Work

The related-work section is three paragraphs. It correctly distinguishes MathFish (Lucy et al., 2024: label agreement with a publisher) from requirement, cites Kane (1992) and Messick (1995) for validity as argument, cites Gururangan et al. (2018) and Poliak et al. (2018) for partial-input baselines, cites Millman (1965) and Haladyna et al. (2002) for catalogs, and cites Tatsuoka (1983) for Q-matrices. That skeleton is right. It is not enough for the claims the paper then makes.

**Missing, and it changes the evaluation.**

- *Balepur, Ravichander, and Rudinger, ACL 2024, “Artifacts or Abduction: How Do LLMs Answer Multiple-Choice Questions Without the Question?”* This is the paper the LM channel is a special case of. They show choices-only LLMs beat majority on ARC, MMLU, and HellaSwag, argue against memorization as the whole story, and distinguish surface artifacts from abductive question inference. The present paper’s options-only rung, modal-letter bar, and contamination probes are the same experimental family, now on curriculum-tagged math with a withheld-quantity stem. Without this citation, “partial-input on public mathematics items” reads as more novel than it is. Follow-ups in the same line (Balepur and Rudinger, KnowLLM 2024; Balepur et al., ACL 2025 on MCQA evaluation) are also uncited.
- *Attali and Bar-Hillel, Journal of Educational Measurement 2003, “Guess Where.”* Test makers and takers hide and seek keys in middle *positions*. The paper’s lower-central rule is middle *numeric rank*, which is a different cue, and that distinction is worth making. Omitting the position-middle literature makes the numeric-central witness look more unprecedented than it is. Haladyna and Rodriguez (2013), *Developing and Validating Test Items*, is the current handbook for the catalog the authors operationalize.
- *TIMSS Q-matrix / cognitive-diagnosis work after 1983.* Sen and colleagues (2019) and later G-DINA papers on TIMSS 2011 already treat expert domain tags as misspecifiable Q-matrix entries, using student responses. The present paper’s adversarial, student-free counterpart is a real difference; it still has to say so against that literature, not only Tatsuoka (1983). The TIMSS 2011 frameworks citation is necessary but not a validity literature.
- *AERA/APA/NCME Standards* and construct-irrelevant variance: the accountability sentence is a score-use claim. The standards for that inference are not cited.

Characterization of cited work is fair. MathFish is not strawmanned. OpenBookQA 0.496 and SWAG 0.436 are the right control targets; recovered 0.450 (longest option) and 0.565 (searched, n=62) are in the right direction. RACE n=8 does not belong in a witness table.

The methodology of hashed-then-scored programs plus Holm on a census of released items is not how Balepur or the CDM papers proceed. That is a genuine difference, and it should be written as such rather than as a gap in 2018 NLI.

---

## 4. Strengths

**S1.** The one-sided witness is the right scientific object. The paper never claims that students failed to learn, does not treat a TIMSS null as certification, and writes explicit refutation conditions. That is rarer than the census size.

**S2.** Family-wise correction is taken seriously. Catalog 105, strategy 67, LM 68, and a 172-test programmatic sensitivity are defined; Algebra II, searched n=11–20 rows, TEKS 7B-only cells, and options-only are held back. The STAAR grade 5 row is reported as a discovery Holm reject that failed replication, not as a confirmed unbound-execution law.

**S3.** The Algebra I/II masked-stem design is a real increment on choices-only: withhold quantities, drop zero-mask items, require the lower CI above chance *and* the cell modal letter, add a weak solver, a second family, permutation, and a residual split. The zeros example is pedagogically clear even if its interpretation is disputed.

**S4.** Method controls (synthetic planted cues; OpenBookQA/SWAG) are the right prerequisite for a TIMSS null. Without them the null would be uninterpretable.

**S5.** Reproducibility artifacts are unusually complete for this kind of census: model revisions, hash of frozen rule files, seeds, clean-option filter, and per-item GPU rows. That is community value independent of the talk.

---

## 5. Weaknesses

**W1. (Major) Prior work on the LM channel is not the 2018 NLI papers.** Balepur et al. (ACL 2024) is the comparison that determines whether the LM results are a new measurement or a curriculum-tagged replication of choices-only MCQA. It is uncited. This is the main originality and positioning failure. Fix: one related-work paragraph plus a table that says what this census adds (withheld quantities, publisher tags, Holm, TIMSS cells).

**W2. (Major) Phi-4 geometry should not be claimed on the current split.** Non-modal-key accuracy 0.229 (n=118) is at or below chance. The cell bar is being carried by B-keyed items. Qwen already fails geometry. Listing geometry with Algebra I/II overstates what the LM family showed. Algebra I/II, including residuals, can stay.

**W3. (Major) Catalog positives are small, uncorrected, and one of them is index-fragile.** 0 Holm rejects in 105 tests is the family-wise result. Geometry +7.3 points over chance on 279 items is a test-wiseness residue of the kind Haladyna catalogs already warn writers about, not a new mechanism. EQAO 20/40 is an existence example, not a stable cell property. Treat them as replication candidates, which the paper already says, and do not let them share billing with the LM ladder in the abstract’s last sentence.

**W4. (Major) Related work does not support the validity/accountability punchline.** Kane/Messick plus Tatsuoka 1983 cannot carry “accountability is reading the wrong quantity.” Missing: Attali and Bar-Hillel (2003), modern TIMSS CDM, the testing standards, and the choices-only LLM line. Without that, the last sentence of the abstract is a use-claim without a use-literature.

**W5. (Moderate) The item text layer is a construct problem.** Human-packet mismatches and STAAR last-option leaks show that some scored strings are not the published item. A witness on a corrupted option set does not refute the printed tag. This matters more for small-n cells (EQAO 40, STAAR 40, TEKS 18) than for Algebra I n=358, but it is not confined to STAAR.

**W6. (Moderate) TIMSS power language is slightly stronger than the export, and the n is small.** Clustered floors should match `power-by-cell.json`. Public TIMSS knowing/applying/reasoning cannot rule out a 0.35 bypass. The paper’s limitations already say a later search can find a witness; the clustered-floor sentence should not be the memorable TIMSS takeaway.

**W7. (Moderate) The requirement matrix and shared operations are unused.** Either show E[t,o] for claimed cells or drop the matrix from the introduction. Instruction-only was specified and not run; backsolving is unmeasured because equations are images. Those are honest, but they mean two of the named test-taker strategies were never tested.

**W8. (Minor-to-moderate) Three Holm families, one scoring day.** Catalog vs strategy vs LM as separate families is defensible if locked before looking. The GPU addendum files still label the LM runs exploratory. The paper’s hashed masking rules help; they do not replace a single locked family list. This would matter more at a journal than for the present draft.

---

## 6. Questions for Authors

**Q1.** For Phi-4 geometry on the withheld-quantity n=166, what is accuracy on items whose key is not B? The export’s 0.229 (n=118) would, if confirmed, remove geometry from the claimed LM set. Does that change the abstract?

**Q2.** On the zeros example, is the tagged operation “compute with the given zeros” or “know that n zeros correspond to n factors”? If the latter, why is a masked-stem hit a witness against the tag rather than evidence that the tag is about form? (This is the difference between the catalog tenths-digit item and the LM algebra items.)

**Q3.** Why is the EQAO clustered CI tighter than the item CI with three years? Which bootstrap is the claimed interval, and why should a reader trust k=3 clustering as strengthening?

**Q4.** How is Table 2’s TIMSS clustered triple (0.400, 0.407, 0.421) computed from `exports/addendum/power-by-cell.json` (0.415, 0.426, 0.441)? If it is a design-effect rescaling of nItems, please state the formula. If it is a transcription mix with `cell-power.json`’s 80% independent floors, that should be corrected.

**Q5.** How many of the 90 geometry lower-central hits and 139 Algebra I masked-stem hits survive a hand check against the printed page (not the OCR row)? Even a 20-item sample would bound W5.

**Q6.** Will the 40-item human masked-stem sheet be in before the talk, and is the pre-registered quantity agreement with a capable model or above-chance human accuracy? A human at chance on that sheet would leave the LM result intact as a model fact and would block the accountability sentence for those items.

**Q7.** Why not cite Balepur et al. (2024) as the LM baseline and Attali and Bar-Hillel (2003) as the middle-key psychometric baseline? If the numeric-rank cue is meant to be distinct from letter-position middle bias, that sentence is currently missing.

---

## 7. Minor Issues / Typos

- Abstract reports geometry CI [0.265, 0.380] (item); the introduction bullet reports clustered [0.265, 0.374]. Name which interval in the abstract.
- Abstract: “a reader exists across two model families, Qwen2.5-7B-Instruct, Qwen2.5-14B-Instruct, and Phi-4” is grammatically a two/three clash. Fine once parsed; awkward in a first sentence of results.
- Navy WIP lines (human ratings, backsolving, unfetched STAAR 2015/2020/2023) should not survive in a version that is cited as finished, even for a talk. Either drop the sentence or keep one limitations bullet without the inline marker.
- Table 1 (controls): RACE n=8 is below the paper’s own n=10 bar; it adds a row without a result.
- Table 3 (lower-central slice) Holm on 17 cells is correctly labeled exploratory; the caption is long enough that a reader can miss that.
- `masked-stem-phi4.json` stores geometry `modalFrequency` 0.2727 and `modalCount` 63 (the n=231 cell) next to n=166 and a non-modal n=118 that implies modal count 48. The paper’s 0.289 is the withheld figure. The JSON fields should not be mixed.
- Instruction-only is mentioned once in methods and never again; delete or move to limitations.

---

## 8. Overall Recommendation

**Overall: 3 (Weak Accept)**

The paper has a real, carefully scoped scientific object and several results that a skeptical reader can keep: a failed STAAR replication, a catalog family-wise null, two small per-cell catalog existence rows, and a withheld-quantity Algebra I/II effect on capable models that is not explained by the four catalog cues, with a weak solver that fails. That is more honest measurement than most shortcut-learning papers.

It is not a 4 because the LM channel is not situated against Balepur et al. (2024), the Phi-4 geometry claim is not supported by the non-modal split already sitting in the export, the accountability sentence overreaches the form-recognition interpretation the authors themselves write, and the psychometric/CDM literature that owns this question is almost absent. The catalog “witnesses” are uncorrected and small. Fix W1–W2 and the last-sentence scope and this becomes a clearly useful empirical note. Leave them in and a reviewer will treat the lead as “LLMs can do choices-only on Regents,” which the literature already contains.

This score does not use page count, acmart, or hackathon formatting.

---

## 9. Confidence Score

**Confidence: 4**

The arguments, exports, and adjacent LLM-MCQA and test-wiseness literatures were checked. TIMSS cognitive-diagnosis modeling is not this reviewer’s home subfield; a CDM specialist might weight W4 differently. Human ratings and a printed-page audit of the 90+139 hits were not re-run here.

---

## Hackathon-adjusted

**Still worth changing before Thursday, because they change what a listener can trust:**

- Do not lead with Phi-4 geometry. The non-modal split is already on disk and contradicts “question type plus option form.” Algebra I/II plus the zeros example (with the form-recognition wording, not the accountability overread) is the LM story.
- Keep the one-sided claim and the STAAR failed replication. Those are the talk’s credibility.
- Say out loud: catalog geometry/EQAO did not survive Holm; EQAO is the second-smallest index, n=40; TIMSS is a null at n≈50–80, not a validation of the tags.
- Do not say accountability systems are “reading the wrong quantity” for Algebra I/II masked-stem hits unless you mean “the givens were not used,” which is weaker and true.
- If there is time for one citation slide: Balepur et al. 2024 (choices-only LLMs) and Haladyna/Millman (catalogs). That blocks the obvious “this is just choices-only” question.

**ICML-scale, do not spend tonight on:**

- Expanding to a 9-page main-conference paper, adding Gemma, OCR-rebuilding the full 2,405-item file, fetching restricted TIMSS, filling E[t,o], running instruction-only, getting n≥10 backsolving, or rewriting related work into a survey.
- Bonferroni vs Holm debates, extra random-program p95 tables, or polishing acmart.
- Human 40-item ratings: useful if they arrive; not a reason to rewrite the Algebra I/II claim tonight. If they are not in, say so in one clause and move on.

**Talk-safe one-liner:** A program that never looks at tenths digits can still hit some published keys; a capable LM can still hit some Algebra I/II keys when the numbers are gone; TIMSS public items did not yield such a program in this search; a STAAR unbound-execution spike did not replicate.
