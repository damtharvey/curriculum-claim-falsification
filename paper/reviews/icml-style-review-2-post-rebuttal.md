# Reviewer 2, post-rebuttal

**Reviewer:** independent ICML-style pass (`paper/reviews/icml-style-review-2.md`) against `8c086c7`.  
**This note:** authors’ response `paper/reviews/rebuttal-to-review-2.md` and revised `paper/main.pdf` at `eb1f73f` (19 pages). Change ledger `paper/reviews/review-2-response.md` was skimmed only for pointers.  
**Bar:** same Strong-Accept bar as the original review. Effort is not a score. Evidence is.

I checked the abstract, §1 contribution bullets, §2, §3.4, §4.3–4.6 (Tables 3, 4, 6, 10, 11), §5, and Appendix A in the revised PDF. I did not recompute bootstraps from raw flags.

---

## 1. Original W1–W9 and Q1–Q6

### W1. Headline object and strongest positive are different experiments

**Partially resolved.**

§3.4 and Table 11 do the split I asked for in spirit: on print-faithful Algebra I, execution-tagged items (\(n=75\)) clear on no model (Phi-4 lower CI equals modal B \(0.293\)); recognition-or-interpretation (\(n=83\)) carries the row (\(0.518 / 0.446 / 0.506\) vs modal D \(0.265\)). Contribution bullet 4 and §4.5 “What the channel measures” now say a pass does not require the given quantities, “narrower than a pass omitting the tagged operation.” That is option (a).

It is not a full fix. The split classifies cluster-heading verbs, not item demand; §5 gives the example that “understand solving equations as a process of reasoning” sits over items that ask the solver to solve. The title, subtitle, abstract lead, and contribution bullet 1 still define the object as a program that *lacks the tagged operation*. The remaining positive is that form-tagged Algebra I keys can be recovered without the givens, which is close to what those tags already name. Item 22 is now labelled `A-APR.B` and is disclosed as not print-faithful, so it is illustration only.

### W2. The measurement layer is not the printed test

**Partially resolved.**

§3.4 and §4.6 report the mechanical check I asked for: 955 items, Qwen2-VL transcription vs text layer, hashed thresholds, calibration 17/20 against a floor of 16, verdicts 434 faithful / 502 not / 19 unverified. Table 10 recomputes every previously claimed row. Algebra I masked-stem clears on faithful items and is higher than not-faithful on every model (dirt deflated it). Algebra II and geometry lower-central fail their bars on faithful items and are dropped. That is the right consequence.

The original weakness is not gone. They filter rather than repair. The faithful subset is not a random half of any cell (§5): pre-2023 administrations and, in Algebra I, word options (40% of faithful vs 10% of not-faithful). A VLM miss moves an item out, never in. About half the claimed-cell text layer is still not the printed item. Existence on a selected subset is not a rate on the cell.

### W3. Catalog and TIMSS findings billed above their evidence

**Partially resolved.**

Abstract and contribution bullet 4 now say the catalog has no family-wise discovery; EQAO grade 6 awaits replication; geometry is not claimed. Table 3 puts text-layer and print-faithful side by side (geometry faithful \(32/99=0.323\), CI \([0.232, 0.414]\)). TIMSS is called a power-limited non-refutation in the abstract, bullet 4, §4.2–4.3, and §5, with clustered floors \(0.415/0.426/0.441\).

EQAO faithful is \(8/14=0.571\), CI \([0.286, 0.857]\), and fails the disclosed post-hoc strict filter (\(5/10\)). That is a residue, not a finding that belongs in the abstract’s “one beats chance” sentence. TIMSS remains in the contribution list. Both are better labelled than at `8c086c7`; both are still over-billed relative to Algebra I.

### W4. Closest priors missing

**Resolved.**

§2 now cites Watson et al. (2018), Moore et al. (SAQUET, 2024), Fang et al. (PATCH, 2025), and Mirzadeh et al. (GSM-Symbolic, 2025), and the collective-advance paragraph names those four vertices. The increment over Watson is stated (hashed a priori rules, tagged public mathematics, Holm, no student reference). PATCH is contrasted with the TIMSS LM null. The GSM-Symbolic-style option substitution is run (§4.5, Table 6), not only cited. They did not run Watson’s classifier on these items; that was not required to close the citation gap.

### W5. Score-use significance is not evidenced

**Unresolved.**

No new human or student data. The one rater is still \(15/40\), uninformative. The paper now claims less, which is correct and does not close Kane/Messick/AERA. §1 still opens with accountability score use. A model fact on recognition-tagged Algebra I does not tell a testing program that examinees read the wrong quantity.

### W6. Family splitting and addenda

**Unresolved.**

The 105 / 67 / 68 families, the scoring-day lock, the image addendum, and the four post-primary catalog cues are unchanged. The three new analyses are hashed recomputations and add no Holm test, which is the right way to do a revision. It does not lock the original family graph.

### W7. Clarity at the Strong-Accept bar

**Partially resolved.**

The abstract (p. 1) now says Algebra I only, print-faithful claims, two text-layer rows dropped, recognition-tagged carry, and option-value change. Contribution bullet 4 matches. Table captions on Tables 3, 4, 6, 10, and 11 state which rows are claimed. §4.5 says rates are text-layer unless a paragraph says print-faithful.

The paper is 19 pages. Dirty-layer tables (Tables 4, 7, 8) still appear before the faithful recomputation in §4.6. “Yes (not claimed)” remains in Table 4. Status vocabulary is still a private glossary. A cold reader can recover the claim; they still have to work.

### W8. Contamination and leakage controls

**Partially resolved.**

Table 6 is the isomorphic-option test I named. On 184 print-faithful Algebra I items, rank-preserving: Qwen 7B \(0.391\) \([0.321, 0.462]\), Phi-4 \(0.408\) \([0.342, 0.478]\), both still above chance and modal B \(0.255\). 7B paired drop \(-0.110\) \([-0.199, -0.015]\) is real. On the carrying recognition class, 7B falls \(0.530 \to 0.361\) and no longer clears modal D \(0.265\); Phi-4 \(0.506 \to 0.398\) still clears. §5 states that this does not split memorized values from value cues, and does not rule out a memorized share.

Qwen 14B is excluded by a \(0.98\) reproduction floor (\(592/606=0.977\)). The abstract’s “two families” and the existential 14B Algebra I row are therefore not covered by the new control. No paraphrase or stem rewrite was run.

### W9. Reproducibility from the PDF alone

**Partially resolved.**

Appendix A now prints every named hash in full (strategy file, image addendum, VLM revision, masking v1/v2, print-fidelity `0211585e…`, verb-class `c87a5ae0…`, isomorph `997242b9…`). Model revisions, seeds, thresholds, and bootstrap seeds are there. Still no code or data URL (anonymous review) and no item-id table beyond the two worked examples.

### Q1. Do intervals still clear on the print-faithful subset?

**Resolved.**

Table 10, not a sample. Algebra I: yes on all three models (\(0.467 / 0.429 / 0.467\), \(n=184\), lower CIs \(0.391 / 0.359 / 0.397\) vs chance \(0.250\) and modal \(0.255\)). Algebra II: no (lower CIs \(0.261 / 0.287 / 0.270\) vs modal \(0.296\)); unclaimed. Geometry lower-central: no (\(32/99=0.323\), \([0.232, 0.414]\)); unclaimed. EQAO: yes at \(n=14\), billed as thin.

### Q2. Execution on the givens versus recognition of a form

**Partially resolved.**

Table 11 and §4.6 “Which tags carry the Algebra I row” answer the question at the cluster-heading level. Execution-tagged faithful Algebra I clears on no model; recognition carries it. The LM channel is restated as information-withholding. The coding is not item-level, which is what I asked, and the title still names the operation-lacking object.

### Q3. Watson et al. (2018)

**Partially resolved.**

Cited and positioned in §2. No shared-item numeric comparison. No student percent-correct column. That is an incomplete answer, not a missing citation.

### Q4. Isomorphic numeral substitution in the options versus the stem

**Partially resolved.**

Option substitution is Table 6 (see W8). Stem substitution is empty by construction; version-2 masking (\(\Delta \approx -0.007\)) is the stem-side probe. 14B not scored. The 7B recognition-class collapse is the informative cell and is underplayed in the abstract.

### Q5. Constraint elimination killing the published key

**Unresolved.**

Unchanged. §4.4 still reports the two intersections and key-survival rates. Tags of those two items were not joined. Logged as rule errors in the strategy addendum, not as tag mismatches.

### Q6. Instruction-only

**Unresolved.**

Unchanged. Data-access; would have been its own Holm family; absence did not redefine the three scored families. Stated in §3.2 and §5.

### Tally

| Status | Items |
|--------|--------|
| Resolved | 2 — W4, Q1 |
| Partially resolved | 9 — W1, W2, W3, W7, W8, W9, Q2, Q3, Q4 |
| Unresolved | 4 — W5, W6, Q5, Q6 |

---

## 2. New weaknesses introduced by the revision

**N1. Faithful subset is a selected population.**  
434/955 is not a coin flip. Later Regents PDFs encode operators as digits and drop out; Algebra I faithful items are 40% word-option vs 10% not-faithful (§5, §4.6). Word and text options were already the high-rate slice in the old cue-attribution paragraph. The Algebra I lift from \(0.388\) to \(0.467\) on 7B can be option-type mix, print fidelity, or both. Existence on this subset does not estimate the cell.

**N2. The abstract’s conjunction is stronger than Table 6.**  
The abstract says two families recover recognition-tagged Algebra I keys *and* that the recovery survives a change of the option values. On the recognition class that carries the row, Qwen 7B’s rank-preserving rate is \(0.361\) \([0.253, 0.458]\) and fails modal D \(0.265\). The pooled \(n=184\) survival is real; the carrying-class survival is Phi-4 only. 14B is not in the table.

**N3. Recognition-tag restatement weakens the object toward a near-tautology.**  
If the publisher’s tag names “interpret the structure” or “understand zeros and factors,” recovering the key from form plus options without the particular numbers is close to measuring the tag, not rivaling it. Execution-tagged items, the clean title population (§3.4), do not clear. The paper now says this. The title still does not.

**N4. Qwen 14B exclusion by a \(0.98\) floor.**  
\(592/606=0.977\) is a one-item-away miss. Excluding the second Qwen model from the only new contamination control leaves “two families” resting on log-probability quartiles, recency, and permutation for 14B. A sensitivity at the observed agreement would have been cheaper than the hole.

**N5. EQAO \(n=14\) and a 19-page body.**  
The last catalog positive has CI \([0.286, 0.857]\) and fails a stricter fidelity cut. It should not share the abstract with Algebra I. Length grew by six pages of status bits, dirty-layer tables, and three new analyses. The first-reader path still hits text-layer rates before Table 10.

**N6. Verb-class proxy error is load-bearing.**  
The carrying class is defined by heading verbs hashed before the join, which is good procedure and a bad construct if items under a recognition heading are execution tasks. That error is not bounded. An item-level recode of the 83+75 faithful Algebra I items is the measurement, not a nicety.

---

## 3. Updated scores

Same scale as the original review. I do not raise a score for running the experiments; I raise a score only if the remaining claim is better supported.

| Dimension | Before | Now | Note |
|-----------|--------|-----|------|
| Originality | Medium | Medium | Priors are now cited; the packaged object is unchanged. |
| Importance | Medium | Medium | Score-use still unclosed (W5). The remaining positive is narrower. |
| Claims / evidence | Medium | Medium | Honest drops (Algebra II, geometry). Abstract conjunction (N2) and heading-verb proxy (N6) keep this from high. |
| Experimental soundness | Medium–high protocol, medium data | Medium–high protocol, medium data | Print check and isomorph are real. Selected faithful subset and 14B hole are new construct issues. |
| Clarity | Medium–low | Medium–low | Abstract is better; 19 pages and dirty-first tables are not. |
| Community value | Medium | Medium | Protocol is more stealable; rates are still subset facts. |
| Prior work | Medium–low | Medium | W4 closed. |
| Reproducibility | Medium–high appendix / medium PDF | Medium–high appendix / medium PDF | Full hashes; no URL. |

**Soundness (1–4):** 3 — dropped rows match Table 10; the advertised recognition-and-isomorph sentence does not match Table 6.  
**Presentation (1–4):** 2 — better abstract, worse length.  
**Contribution (1–4):** 3 — a tighter, smaller existence result on form-tagged Algebra I.

### Overall recommendation

**Overall: 3 (Weak Accept)**  
**Confidence: 4**

The revision did the two experiments that blocked a 4 in my first review: full-cell print-faithful recomputation (Q1) and a tag split plus restatement (W1/Q2). It dropped the rows that failed (Algebra II masked-stem, geometry lower-central). It cited the four priors and ran the option-isomorph control. That is why this is still a 3 rather than a 2.

It is not a 4. Q2 asked for an *item-level* coding; heading verbs are not that. The surviving policy-relevant object (execution-tagged, print-faithful Algebra I) clears on no model. The surviving numeric object is recognition-tagged Algebra I on a non-random faithful slice, with 7B’s carrying class failing the isomorph modal bar and 14B absent from that control. Accountability is still the opening and still unevidenced. I would use Table 10 and Table 6. I would not use the title or the abstract’s last sentence as a claim about tagged operations.

---

## 4. What would move this to a 4 (no new student data)

In priority order:

1. **Item-level tag coding of the 184 print-faithful Algebra I items** (or a pre-registered sample large enough to bound the heading-verb error). If execution items still fail and recognition items still clear, keep the information-withholding restatement and change the title, subtitle, and abstract lead so they name that object. If many “recognition” items are execution tasks, the row is not carried by form tags.

2. **Repair the Algebra I text layer, or score it from the page image**, and report the cell rate on the repaired population. Filtering to VLM-agreeing, pre-2023, word-option-heavy items is not a substitute. If the repaired cell still clears chance and modal letter, W2/N1 close.

3. **Put Qwen 14B on the isomorph arms.** Re-register a floor or report \(0.977\) as a sensitivity. Without it, drop 14B from the “two families survive a change of option values” sentence. Also rewrite that sentence so it does not conjoin recognition-tagged carry with isomorph survival for 7B (Table 6).

4. **Demote EQAO \(n=14\) and TIMSS** out of the abstract and contribution bullet 4. Catalog finding: 0 Holm. TIMSS: power-limited null, one sentence in limitations.

5. **Move dirty-layer rate tables to the appendix** and lead Results with Table 10, Table 11, and Table 6. Cut enough that a cold reader hits the claimed object before page 10. Print the 350,535-trial arithmetic or drop the number; name or cut the proprietary assistant.
