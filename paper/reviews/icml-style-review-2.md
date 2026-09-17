# ICML-style review (independent pass)

**Paper:** Does the Assessment Require the Skill?  
**Subtitle:** Matching released mathematics keys without the tagged operation  
**Artifact:** `paper/main.pdf` at `origin/main` HEAD `8c086c7`  
**Venue framing:** hackathon preprint (acmart sigplan screen, nonacm, review, anonymous). Length and template are ignored. Claims, evidence, prior work, originality, significance, clarity, and reproducibility are scored at a Strong-Accept bar.

This review was written as a cold read of the live PDF and TeX. Scores were fixed before looking at `paper/reviews/icml-style-review.md`. A short post-score note on that earlier review is at the end.

---

## 1. Summary

This paper asks whether a published tag on a released mathematics item (a curriculum standard, or a TIMSS cognitive domain such as knowing, applying, or reasoning) is required for a pass. The authors treat that requirement as a one-sided falsifiable claim about programs: a program that lacks the tagged operation, never sees the published key, and still matches under the published scoring rule is a *witness* that a pass does not require that operation. A search that finds no such program does not certify the tag. Students are not measured, and the paper never claims that students failed to learn a skill.

The census covers 2,405 keyed public-release items from nine authorities (New York Regents, STAAR, EQAO, TIMSS 2011 and earlier public cycles, PISA, NYSED, NAPLAN, MCAS). Three program families are scored, each Holm-corrected on its own:

1. **Catalog item-writing rules** (15 a priori programs; 105 (rule, cell) tests with \(n \ge 10\)).
2. **Adaptive strategies** (hub, constraint elimination, arithmetic closure, backsolving, a fixed-order portfolio; 67 tests), plus a later image-channel backsolving addendum that is not in those 67.
3. **Partial-input language models** (options-only as a ladder; masked-stem with given quantities replaced by `[N]` as the claimed channel; Qwen2.5-7B/14B-Instruct, Phi-4, Mistral-7B-Instruct-v0.3; 68 Holm tests on the withheld-quantity population).

A synthetic Haladyna-flaw set and public options-only/question-ignored numbers on OpenBookQA and SWAG are used as method controls before census nulls are read. Programs are hashed before scoring. Implementation hashes, model revisions, and seeds are in Appendix A.

Reported findings, as billed:

- The catalog family has **no Holm survivor**. Two per-cell existence rows beat chance and are offered as replication candidates, not family-wise discoveries: lower-central numeric rank on New York Regents geometry (\(90/279 = 0.323\), item 95% CI \([0.265, 0.380]\)) and on EQAO grade 6 (\(20/40 = 0.500\), CI \([0.350, 0.650]\)).
- STAAR grade 5 arithmetic closure is the only Holm reject in the 67-test strategy family on the frozen 2019/2021/2022 cell (\(21/40 = 0.525\)). A registered prediction on held-out administrations fails after a pre-registered option-leak repair; the powered combined set is \(21/64 = 0.328\), CI \([0.219, 0.438]\).
- Image-channel backsolving (transcribe a displayed equation, then substitute options) matches \(14/15\) unique honest fires on Algebra I solving-tagged items, coverage \(15/598 = 0.025\). Not a Holm test and not a census of Algebra I.
- Qwen2.5 and Phi-4 recover withheld-quantity Algebra I and Algebra II keys above chance and above the cell modal-letter frequency. Phi-4 geometry meets the cell bar but not the non-modal-key split and is not claimed. Mistral clears neither cell on both bars. TIMSS knowing, applying, and reasoning stay null across catalog, strategy, and partial-input channels at public selected-response \(n\) of about 50–80.
- One human rater on a 40-item Algebra I masked-stem sheet scores \(15/40 = 0.375\), CI \([0.225, 0.525]\): an uninformative null.
- A 20-item printed-page audit (10 geometry lower-central hits, 10 Algebra I masked-stem hits) finds 8 full matches, 8 glue cases, 3 truncations, and 1 wrong option set.

The stated contributions are the object, the bar, the census, and what the census found.

---

## 2. Claims and Evidence

The paper is more careful than most empirical ML submissions about what it does *not* claim. The one-sided wording is held in the abstract, the contribution bullets, the results, and the limitations. STAAR closure’s Holm reject is not sold as a confirmed law. Phi-4 geometry is unclaimed. Mistral is reported as a miss. TIMSS is not certified. Image backsolving is billed at its coverage. The human sheet is billed as uninformative. That discipline is real evidence of scientific hygiene, not marketing.

The load-bearing positive claims still need to be checked against the object in Section 1 and against how adjacent work tests similar hypotheses.

### Claim A. A program lacking the tagged operation can match the key (one-sided).

**Catalog and strategy channels.** Lower-central and arithmetic closure genuinely lack content operations. The EQAO tenths-digit example is a clean illustration: the rule never reads the stem. Geometry lower-central on 279 numeric-option items is a small lift over \(0.25\) (CI lower bound \(0.265\)). After 105 tests, five uncorrected clears and two claimed existence rows is the rate one expects from a hunt; Holm and Bonferroni both kill the family. The paper says this. A Strong-Accept reviewer still treats “what the census found” as a catalog **null**, with two small per-cell residues that have not been replicated.

EQAO grade 6 is specific to index \(\lfloor(n-1)/2\rfloor\) (second-smallest). Upper-central on that cell is chance. That is reported. It means the row is not a test of the catalog’s “middle value” cue; it is a test of one discrete side of a four-option sort. \(n = 40\) items the rule fires on, pooled across three years, is thin for a named existence claim even at the per-cell bar.

**Language-model channel.** This is the strongest numeric result (Algebra I \(\approx 0.39\)–\(0.42\) on \(n = 358\); Algebra II \(\approx 0.35\)–\(0.37\) on \(n = 248\); two model families; Holm rejects against chance). It does **not** instantiate Claim A’s wording. Limitations §5 states the fact directly: “The language-model channel has the operations. What is withheld is information.” Contribution bullet 1 still frames the object as a program that *lacks the tagged operation*. Masked-stem tests whether the **given quantities** are required, not whether the tagged skill is absent from the scorer. Adjacent number-substitution work (Mirzadeh et al., GSM-Symbolic, ICLR 2025) shows that changing numerals often *hurts* LM math accuracy; that is the complementary experiment. Recovering the key with numerals withheld is consistent with schema/form matching on the remaining wording plus the **unmasked option strings**. The January 2023 Algebra I item 22 example (three `[N]` zeros, three-factor option C) is excellent and honest. For many Algebra I/II tags, relating zeros to factors, or recognizing the named form, *is* the tagged operation. Withholding the particular zeros then tests a weaker claim: the arithmetic instance is not required. That is still a validity-relevant fact. It is not the object advertised in the first contribution bullet.

Options remain fully visible, including numbers and algebraic forms. Balepur, Ravichander, and Rudinger (ACL 2024) already show that choices-only LMs beat majority on general MCQA by artifacts or abductive reconstruction of the question. This census is that construction on tagged mathematics, which the related-work paragraph correctly says is not the first choices-only result. The increment is the withheld-quantity population, the tag, Holm inside a TIMSS-including census, and the contamination probes. The probes (token log-probability quartiles, recency buckets, option permutation, version-2 extra masking) are negative and useful. They are not isomorphic-item tests. Released Regents forms are mirrored widely (e.g. public exam archives). Letter-argmax on item-unique wording plus options can still be training-set familiarity with the *form class*, which is exactly the mechanism the authors name.

### Claim B. Family discipline: no row that beats chance in one cell is billed as a family-wise discovery.

Mostly held. Catalog: 0 Holm. Strategy: one Holm reject, then a powered replication fail. LM: claimed cells are those that also clear the registered channel bar (chance **and** modal letter) on capable scorers; TEKS grade 5/8 7B-only rows are not claimed; options-only Algebra I on 14B is not claimed.

The discipline is bought with **family splitting**. Catalog 105, strategy 67, LM 68, a 172-test programmatic sensitivity that still excludes the LM family, options-only parked as a ladder, image backsolving hashed later and kept out of the 67, a 17-cell one-rule Holm slice labeled exploratory after seeing which rule cleared, and four extra catalog cues scored after primary scoring. Each cut is disclosed. At a Strong-Accept bar this is still a researcher degree of freedom: the image addendum is scored because text-layer unique fires were 6/1,186; the LM family is defined on the withheld-quantity subset after first-run TIMSS knowing was “carried by items where nothing was withheld.” Pre-registration on the scoring day, as described, is weaker than a locked protocol that names the families before any pass rate exists.

### Claim C. TIMSS knowing / applying / reasoning stay null.

Supported as a statement about this program space at this public \(n\). Table 2 clustered 80% floors are \(0.415 / 0.426 / 0.441\) on selected-response \(n = 65 / 54 / 68\). Bypass rates in the low thirties would not have been seen. The clean-option filter keeps 17 TIMSS 2011 items for the LM channel; withheld-quantity TIMSS knowing is \(n = 22\). Contribution bullet 4 lists the TIMSS null next to the Algebra I/II recoveries. Adjacent TIMSS work already treats expert attribute tags as misspecifiable (Terzi and Sen 2019; later country-specific Q-matrix papers). A student-free null at \(n \approx 50\)–\(80\) does not add much to that literature unless it is billed only as a power-limited non-refutation, which the limitations section does and the contribution list underplays.

### Claim D. Image backsolving: 14/15, coverage 15/598.

The protocol (VLM transcribes; substitution is symbolic; invented formulas abstain; two recodes) is the right construct for “does not require solving.” Coverage \(0.025\) means the row is a rare unique-equation subset. Katz, Bennett, and Berger (2000) already documented plug-in of numbered options as an SAT mathematics strategy; the authors cite that paper and correctly say this is the strategy as a program, not a student protocol. Existence at \(n = 15\) with CI \([0.800, 1.000]\) is fine as an existence measurement. It is not evidence that Algebra I tags are generally answerable by substitution.

### Claim E. Measurement layer equals the printed item.

A 20-item audit against source PDFs (no OCR) finds **8/8/3/1** (match / glue / truncated / wrong option set). Twelve of twenty sampled rows are dirty. Rates in the paper are computed on the text layer. Limitations say a witness on a corrupted option set does not refute the printed tag. That sentence is correct and, at a Strong-Accept bar, **caps every text-layer claim** until the dirty rows are dropped or repaired and the CIs recomputed. Glue on geometry option D “after a correct leading number” may spare lower-central more than it spares masked-stem LMs. Algebra I June 2023 item 3 (printed lines vs census inequalities) is a different item. One wrong option set in a 10-item Algebra I sample does not, by itself, delete \(n = 358\); it does put a non-zero contamination rate on the text layer that the Holm machinery never sees.

### Claim F. Humans, students, and score use.

The introduction motivates accountability, curriculum evaluation, and research uses of tagged passes (AERA/APA/NCME 2014; Kane; Messick). The design then refuses student data. The one human rater is uninformative at \(n = 40\). Watson et al. (WWW Companion 2018) scored domain-naive linguistic guessers against *student* percent-correct on AAAS science MCQs; G-DINA Q-matrix work on TIMSS 2011 uses response vectors. This paper’s object is student-free by construction. That is a legitimate object. It does not close the score-use argument that opens the paper. A pass that a program can match is not yet a pass that an examinee can match without the skill. The authors know this. The abstract still leads with accountability uses.

**Supplementary material.** Appendix A (hashes, revisions, seeds, filter counts) was reviewed. It fixes the reported numbers and does not add a student analysis, a cleaned text layer, or a code URL in the PDF.

**Baselines relative to adjacent papers.** Method controls recover OpenBookQA question-ignored 0.496 with longest-option 0.450, and beat SWAG ending-only 0.436 with a searched 0.565. That is the right kind of tool check, and it matches how Gururangan et al. (2018), Poliak et al. (2018), and Balepur et al. (2024) establish that a partial-input scorer fires where cues are known. Missing as experimental counterparts: (i) Watson et al. 2018-style domain-naive guessers with student accuracy as a reference; (ii) GSM-Symbolic-style isomorphic numeral substitution on the same Algebra I/II items; (iii) IRT discrimination of witness vs non-witness items, as in recent IWF–IRT work (e.g. Moore and colleagues’ IRT analyses of item-writing flaws). Without (i)–(iii), the Algebra I/II rates are model facts on a dirty text layer, not a validity argument about score use.

---

## 3. Relation to Prior Work

The related-work section is structured well: standards labeling (MathFish; Lucy et al. 2024) is distinguished from requirement-to-pass; shortcut and partial-input NLP (Geirhos; Gururangan; Poliak; McCoy; Kaushik and Lipton; Agrawal VQA); choices-only LMs (Balepur et al. 2024, 2025; Balepur and Rudinger 2024); contamination (Magar and Schwartz; Sainz et al.); item-writing and test-wiseness catalogs (Millman; Haladyna; White and Zammarelli; Attali and Bar-Hillel); SAT plug-in (Katz et al.); CDMs and DIF (Tatsuoka; de la Torre and Chiu; Terzi and Sen; Holland and Thayer); argument-based validity (Kane; Messick; AERA standards). The closing paragraph that these literatures together still do not score a one-sided program witness on tagged public mathematics, Holm-corrected by family, is a fair description of the **packaged** object. It is not a fair description of the nearest neighbors.

**Cited accurately enough:** MathFish asks whether a labeler agrees with a publisher; this paper keeps the publisher tag. Balepur et al. are not over-claimed as “first choices-only on math.” Terzi and Sen are used as the student-data counterpart. Katz et al. are used for backsolving. That is good.

**Missing papers that change the novelty and baseline story:**

1. **Watson, Ma, Tejwani, Chang, Ahn, and Sundararajan, “Human-level Multiple Choice Question Guessing Without Domain Knowledge,” WWW Companion 2018.** A domain-naive linguistic classifier (length, stem–option similarity, option–option similarity, logical keywords) is trained to pick MCQ keys *without topic knowledge*; accuracy above chance is treated as evidence that the item is a poor measure of domain skill; the guesser is compared to student percent-correct on AAAS Project 2061 science items. This is the closest prior to the catalog/strategy object. It is not cited. The present paper’s increment over Watson et al. is tagged public *mathematics*, a priori hashed programs rather than a fitted MLP, Holm, TIMSS cells, and the refusal to talk about students. That increment is real and must be stated against this paper, not only against Haladyna’s prose catalogs.

2. **Moore, Costello, Nguyen, and Stamper, SAQUET, AIED 2024** (and the 19-criterion IWF rubric line). Automatic scoring of item-writing flaws, including longest-option, absolute terms, convergence, word repeats, grammatical cues. The catalog family here is a pass-rate witness, not a flaw detector, but SAQUET is the current programmatic baseline for “turn Haladyna into code.” Four extra catalog cues added after primary scoring overlap this toolkit.

3. **Fang, Oberski, and Nguyen, PATCH, 2024 / GEM 2025.** LLMs (including Qwen-VL) are scored on released **TIMSS 2011** grade-8 mathematics items with IRT, against human populations. Same public TIMSS cycle this census treats as the last showable international set. PATCH asks how well models *solve* the items; this paper asks whether a partial-input program can match keys without the tag. Both papers need to appear in the same paragraph. A TIMSS LM null on 17 clean-option items is hard to interpret next to PATCH’s full-item IRT study unless that contrast is written.

4. **Mirzadeh et al., GSM-Symbolic, ICLR 2025.** Accuracy drops when numerals in grade-school problems are substituted. That is the obvious control for “keys recovered with quantities withheld”: if form recognition is doing the work, isomorphic numerals should preserve the masked-stem hit pattern; if execution on the givens is doing the work, unmasked with-stem should be brittle to substitution in the GSM-Symbolic sense. Neither experiment is present.

5. **Automatic IWF and MCQ-shortcut toolkits after 2023**, including NLP detection linked to IRT difficulty/discrimination, and concurrent education-inspired MCQA audit tools that flag choices-only shortcuts. Even if concurrent work is not required for comparison, SAQUET (2024) is not concurrent.

**Methodology vs field standards.** Educational measurement validates tags with student responses (CDM, DIF, IRT). NLP validates partial-input artifacts with ablation of the question and with contamination checks. This paper’s student-free program witness is a third protocol. It is not wrong. It is under-compared to the first two. The collective-advance paragraph is present and is the right shape; it needs the Watson/SAQUET/PATCH/GSM-Symbolic nodes.

I know the validity, shortcut-learning, choices-only, and CDM literatures well enough to score this; I am not a TIMSS scaling specialist.

---

## 4. Strengths

**S1. A falsifiable object with a one-sided stop rule.** Turning “this item requires operation \(X\)” into “a hashed program that lacks \(X\) matched the key” is the right kind of claim for a measurement paper. The stop rule (a miss does not certify the tag; a match does not imply students use the program) is held in the abstract and the body. Adjacent CDM papers estimate attributes from responses; MathFish estimates labeler agreement. Neither is this object.

**S2. Family-wise honesty on the catalog and on STAAR closure.** 105 tests, 0 Holm; two existence rows labeled as such. The only strategy Holm reject is subjected to a registered prediction, a parse repair hashed before rescoring, a power floor of 46, and a combined \(21/64\) that covers chance. Reporting that fail, including artifact numerals on 13/40 discovery stems, is substantially above the field’s usual “we found a cue” write-up.

**S3. LM claims are sliced instead of pooled.** Withheld-quantity vs nothing-withheld, modal-letter bar, non-modal-key split (the Phi-4 geometry kill), capable vs weak scorer (Mistral with-stem ceiling equals masked-stem), residual after four catalog cues, option-type split, permutation and extra-masking probes. Qwen 7B TEKS grade 5/8 clears are not promoted. This is how an existence claim about models should look.

**S4. Method controls before census nulls.** Recovering published OpenBookQA and SWAG partial-input numbers in the same 1,847-program space is the correct prerequisite for reading a TIMSS null as “the searcher can fire.”

**S5. Reproducibility hooks in the appendix.** Frozen strategy hash, masking-rule hashes, Hugging Face revisions, seed 20260916, clean-option filter counts, and the mechanical letter-token rule. That is more than most empirical papers put in an appendix, even without a URL in the PDF.

**S6. Concrete items.** The EQAO tenths-digit lower-central walk-through and the masked zeros-of-\(g(x)\) example let a reader see the mechanism instead of only a rate.

---

## 5. Weaknesses

**W1. (Critical for a Strong Accept.) The headline object and the strongest positive result are different experiments.**  
Catalog/strategy programs lack content operations. The LM channel withholds quantities and keeps question type, units, operators, and full option strings; the model still has the operations (Limitations, paragraph on the LM channel). Algebra I/II masked-stem rates are then used in contribution bullet 4 as evidence that “a pass does not require executing the tagged computation on the givens.” That sentence is narrower than contribution bullet 1 and than the title. For structural algebra tags, form recognition of the wording **is** a reading of the tag. A Strong-Accept paper would either (a) move the LM channel to a separate claim about *information* rather than *operations*, or (b) show that the publisher’s tag names execution on the givens rather than recognition of the form. The item-22 example currently argues for (a). The contribution list argues for (b) without an item-by-tag coding of whether the CCSS/Regents language names execution.

**W2. (Critical.) The measurement layer is not the printed test.**  
The 20-item PDF audit is 8 matches, 8 glue, 3 truncations, 1 wrong option set. Lower-central parses leading numbers from options; masked-stem LMs see whatever the ingest wrote. Thirteen STAAR grade 5 closure stems contain artifact numerals (axis ticks, footers, leaked neighbors). Text-layer backsolving barely fires because equations are images. These are not independent nits: they are one ingest construct. A Strong-Accept version recomputes every claimed CI on a print-faithful subset (or scores from page images end-to-end) and treats the current text layer as a sensitivity. Until that is done, geometry \(0.323\) and Algebra I \(0.416\) are rates on a noisy proxy.

**W3. (Major.) Catalog “findings” are uncorrected residues after a 105-test hunt; TIMSS “findings” are power-limited non-refutations.**  
Geometry’s lower CI is \(0.015\) above chance. EQAO is \(n = 40\) and index-specific. Five uncorrected clears, two claimed. The 17-cell one-rule Holm that keeps EQAO and drops geometry is labeled exploratory, which is correct and also means there is no primary catalog discovery. TIMSS clustered floors \(\approx 0.42\)–\(0.44\) at \(n \approx 50\)–\(80\), and LM TIMSS cells after filtering are \(n = 22\)–\(42\). Listing these next to Algebra I/II recoveries in the contribution bullets overweights nulls and small residues relative to the only large, replicated-across-families positive (masked-stem Algebra I/II), which is the channel that does not lack the operation (W1).

**W4. (Major.) Closest priors are missing, so originality is overstated relative to the packaged object.**  
Watson et al. (2018) already score domain-naive programs against keys as a validity screen. SAQUET (2024) already compiles Haladyna into runnable detectors. PATCH already runs LMs on TIMSS 2011 public items. GSM-Symbolic already varies numerals to test whether math items are executed or matched as forms. The related-work paragraph that “taken together they still do not score this object” survives only if those four are absent. With them, the paper is a tagged-mathematics census with Holm and a withheld-quantity LM protocol, which is a real but narrower increment.

**W5. (Major.) Score-use significance is not evidenced.**  
Kane/Messick/AERA open the paper. The design then forbids the data those frameworks use. One rater, 40 items, \(\kappa = 0.212\) vs Qwen 14B on 28 overlapping rows, uninformative vs chance. No IRT, no DIF, no examinee shortcut protocols (contrast Katz et al., who videotaped students). The community that would change practice (state testing programs, TIMSS scaling, curriculum evaluators) cannot act on a model fact plus two uncorrected lower-central rows. The ML community that would change eval practice already has Balepur et al. on choices-only and GSM-Symbolic on numeral brittleness. The intersection (tagged public math, Holm census, hashed programs) is the value; it is currently too small, and too bound to a dirty text layer, to move either community at a Strong-Accept level.

**W6. (Moderate.) Family splitting and addenda as analysis path.**  
Image backsolving is an addendum because the text layer did not yield \(n \ge 10\). LM Holm is restricted to withheld-quantity after first-run TIMSS knowing was inflated by unmasked items. Extra catalog cues (longest, convergence, overlap, mean of others) are post-primary. All disclosed. A locked analysis graph, with addenda labeled as such in the abstract (the abstract already hedges image backsolving; it should similarly hedge that the LM family definition is post-first-run), would be required for a 4.

**W7. (Moderate.) Clarity at the Strong-Accept bar.**  
A cold ML reviewer can recover the claims, but only by working. Three Holm families, a 172-test sensitivity, per-cell vs family-wise vs “clears the bar and is not claimed,” discovery vs replication STAAR, clustered vs item bootstrap, fire-on \(n\) vs cell \(n\), withheld-quantity vs all-scored, capable vs weak scorer, and “existence row like geometry” for image backsolving are too many status bits for the results section. The contribution bullets are the right four nouns (object, bar, census, findings). The findings paragraph and §4 then reintroduce a rate sheet. Table captions help; the Algebra II lower-central row in Table 4 (“yes (not claimed)”) still requires a private glossary. This is not a template complaint. It is a first-reader complaint.

**W8. (Moderate.) Contamination and leakage controls are weaker than the adjacent LM-eval standard.**  
Negligible Spearman between unmasked log-probability and masked accuracy, flat recency, permutation within noise, and version-2 masking \(\Delta \approx -0.007\) are evidence against *verbatim stem* memorization. GSM1k / isomorphic-item / paraphrase protocols (Zhang et al. 2024 NeurIPS Datasets; SAT isomorphic checks in recent standardized-test LLM papers) are the standard when the items are public exams. Regents Algebra I/II are among the most copied math items on the web. The claim is existential and could be true without contamination; the probes do not yet match the threat model.

**W9. (Minor–moderate.) Reproducibility from the PDF alone.**  
Appendix A is good. The PDF has no anonymous code/data statement, no item-id table beyond two examples, and truncated image-addendum hashes (`d6ee8caf…`, `eed13092…`). The public repo (outside the PDF) is actually strong. For anonymous review the PDF should still say that hashed frozen files and `items.jsonl` will be released, and should print full sha256 for every hashed artifact named in the text.

---

## 6. Questions for Authors

**Q1.** After dropping or repairing the 12 non-matching print-audit rows, and after a full pass of the same audit protocol on a random sample of geometry fires and Algebra I masked-stem hits large enough to bound the dirty rate, do the geometry lower-central interval and the Algebra I/II masked-stem intervals still clear their registered bars? (If either interval includes chance on the print-faithful subset, W2 becomes a reject-level construct failure for that row.)

**Q2.** For the claimed Algebra I/II masked-stem hits, what fraction of publisher tags name *execution on the givens* versus *recognition of a named form* (zeros \(\leftrightarrow\) factors, function family, inequality direction, etc.)? If most claimed hits are form tags, will you restate contribution bullet 1 so that the LM channel is an information-withholding result, not an operation-lacking witness? (This is the difference between a 3 and a 4 on claims support.)

**Q3.** Why is Watson et al. (WWW Companion 2018) not discussed? Their domain-naive guesser is scored against keys as a validity screen. What, numerically, does your a priori catalog add on items they could have scored, and why is student percent-correct not even an optional column where TIMSS already publishes it?

**Q4.** On the withheld-quantity Algebra I/II hits, what happens under GSM-Symbolic-style numeral substitution in the *options* (isomorphic keys) versus substitution only in the (already masked) stem? If masked-stem accuracy tracks option-form isomorphism, that supports form recognition; if it collapses, that supports a different mechanism. (This is the contamination/form experiment the current log-probability quartiles do not replace.)

**Q5.** Constraint elimination kills the published key on two specified intersections (probability with percent-point options; interior-angle \((0,180)\) on a rectangle). Are those items tagged for the skill the keyword rule misunderstands, and did you log them as parser bugs or as tag/program mismatches?

**Q6.** Instruction-only (worked examples from the same unit) is specified and unrun. Is that a data-access problem only, or would including it have changed the family definitions? (If it would have been a fourth Holm family, the current three-family split needs that counterfactual in the protocol.)

Answers to Q1–Q2 would change my overall score. Q3–Q4 would change originality and claims support. Q5–Q6 are local.

---

## 7. Minor Issues / Typos

- Abstract glosses Holm as “a family-wise multiple-testing adjustment,” which is helpful, then never names Bonferroni except in §4.3; pick one primary correction in the abstract.
- Table 1: RACE recovered \(n = 8\) is a control miss because of the \(n < 10\) bar, not because cues are absent; the caption is fair, the table still looks like four corpora of equal status.
- Table 4 Algebra II “yes (not claimed)” will be misread as a contradiction by anyone who has not memorized §4.3.
- Image-addendum hashes in Appendix A.1 are truncated; strategy and masking hashes are printed in full. Print all of them.
- “350,535 local trials” is not reconcilable from the main text with 1,847 programs \(\times\) cells; give the arithmetic or drop the number.
- Proprietary options-only assistant at \(0.359\) (\(n = 1493\)) is unnamed; either name it or cut it. Recency gaps vs 7B are not interpretable without the model class.
- TIMSS 2011 “last cycle whose items, keys, scoring guides, domain tags, and percent correct are public together” is a strong operational claim; a citation to the IEA release policy would help.
- The title asks whether the assessment requires the skill; the paper answers whether a *program* can match a *key*. Those are aligned only under W1’s restatement.

---

## 8. Ratings

Evaluated against a Strong-Accept paper in empirical ML / measurement, not against workshop leniency.

| Dimension | Rating | Note |
|-----------|--------|------|
| Originality | Medium | Packaged object is real; Watson 2018, SAQUET, Balepur 2024, PATCH, GSM-Symbolic already occupy the vertices. |
| Importance | Medium | Score-use is important; evidence does not reach the users named in the intro. |
| Claims / evidence | Medium | Honest scoping; W1–W2 prevent a high. |
| Experimental soundness | Medium–high protocol, medium data | Hashes, Holm, replication fail, controls: high. Text layer, family split, TIMSS \(n\): not. |
| Clarity | Medium–low | Recoverable, not first-reader clean. |
| Community value | Medium | Object + bar + hashed census could be reused if the text layer is cleaned and code is pointed to from the PDF. |
| Prior work | Medium–low | Collective-advance paragraph is present; nearest programmatic priors are not. |
| Reproducibility | Medium–high given the appendix; medium from PDF-only | Revisions and hashes are enough to rebuild scorers; items need the frozen JSONL. |

**Soundness (1–4):** 3 — claims that are made are mostly supported; the object/LM mismatch and the text layer keep this from 4.  
**Presentation (1–4):** 2 — dense, status-bit heavy; examples and tables carry the paper.  
**Contribution (1–4):** 3 — a usable protocol and a careful census; not yet a result that changes tag interpretation in the field.

---

## 9. Overall Recommendation

**Overall: 3 (Weak Accept)**

The paper does something worth doing: it turns a tag into a one-sided program test, hashes the programs, splits correction by family, reports a catalog null, reports a strategy Holm reject that fails replication, and reports an LM withheld-quantity existence result in two model families with the geometry and Mistral misses left on the table. That is more scientific honesty than the median empirical submission.

It is not a Strong Accept, and it is not yet an Accept, because the result that would matter (Algebra I/II) is not the object in the first bullet (W1), because the rates sit on a text layer that fails a 20-item print audit at 12/20 (W2), and because the catalog/TIMSS “findings” are uncorrected or underpowered residues that the contribution list still elevates (W3), while the nearest programmatic priors are missing (W4). Fixing W1 in prose without fixing W2 is not enough. Fixing W2 without restating the LM claim is not enough.

I would use this census as a protocol to steal from. I would not yet use its rates as evidence that accountability tags are reading the wrong quantity.

If Q1 shows that print-faithful intervals still clear, and Q2 produces an item-level tag coding that either supports execution-on-givens or moves the LM result out of the operation-lacking object, I would consider 4 after a related-work revision (Watson, SAQUET, PATCH, GSM-Symbolic). Until then, 3.

---

## 10. Confidence Score

**Confidence: 4**

I read the PDF end-to-end, the TeX for related work, method, limitations, and appendix, and I checked the numbered claims against the tables. I searched the 2018–2026 literature on choices-only MCQA, item-writing-flaw programs, TIMSS Q-matrices, TIMSS LLM benchmarks, and numeral-substitution math eval. I am not a TIMSS IRT vendor and I did not recompute the bootstrap intervals from raw flags.

---

## 11. Post-score glance at `icml-style-review.md` (not used for scoring)

Consulted only after Sections 8–10 were written. That review was Overall 3 Weak Accept. I did not copy its wording, dimension table, or weakness list.

**Review-1 W1–W8 versus the live PDF:**

| Review-1 | Status in live PDF | Still a 5/5 hit? |
|----------|--------------------|------------------|
| W1 Balepur uncited | Fixed. Balepur 2024/2025 and Balepur–Rudinger 2024 are in §2. | No. Remaining prior-work gap is Watson 2018, SAQUET, PATCH, GSM-Symbolic (this W4). |
| W2 Phi-4 geometry claimed | Fixed. Unclaimed; non-modal split is in the text. | No. |
| W3 Catalog residues billed with the LM ladder | Mostly fixed in the abstract (replication candidates, not discoveries). Contribution bullet 4 still lists them beside Algebra I/II. | Partially: this W3. |
| W4 Validity literature thin | Fixed enough: AERA standards, Attali and Bar-Hillel, Terzi and Sen, Haladyna and Rodriguez 2013, collective-advance paragraph. | Residual: this W4/W5 (score-use still unclosed; nearest *program* priors still missing). |
| W5 Dirty text layer | Audit now reported (8/8/3/1). CIs not recomputed on a print-faithful subset. | Yes: this W2. |
| W6 TIMSS clustered floors mismatched export | Fixed. Table 2 now 0.415/0.426/0.441. Power-limited null still billed as a finding. | Residual: this W3. |
| W7 Requirement matrix unused; backsolving unmeasured | Matrix gone from the intro. Image backsolving measured at 14/15, coverage 0.025. Instruction-only still unrun. | Residual only for instruction-only (Q6). |
| W8 Three Holm families, scoring-day lock | Still the procedure; now disclosed in more detail. | Residual: this W6. |

**Already in the paper (do not re-litigate as if absent):** one-sided wording; catalog 105 / 0 Holm; STAAR G5 Holm then powered replication fail; LM Algebra I/II on Qwen2.5 and Phi-4 with Mistral miss; image 14/15 not Holm; human 15/40 uninformative; print audit reported; short abstract; subtitle; object/bar/census/findings bullets; appendix hashes.

Those fixes are why this pass is also a 3 rather than a 2. They do not clear this pass’s W1 (object vs LM channel) or W2 (audit without recomputed CIs), which are the two items that still block a 4.
