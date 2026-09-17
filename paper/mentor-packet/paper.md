# Does the assessment require the skill?

**Abstract.** Released mathematics items carry a published tag: a curriculum standard, or a cognitive domain such as reasoning. A correct answer is then read as evidence of that competency. We ask a narrower question. Does matching the published key require the tagged operation, or is there an executable program that lacks that operation and still matches the key? On 2405 public-release items we search a priori item-writing rules and a 1847-program feature space, fit on one corpus and scored on another, against a bar that chance and random programs of matched complexity do not clear. The search recovers documented shallow-cue rates on OpenBookQA and SWAG, so it is not blind. It finds no such program on Trends in International Mathematics and Science Study (TIMSS) items tagged knowing, applying, or reasoning, at a bar that would have seen a bypass of about 0.35. It does find one: pick the lower-central numeric option (second-smallest of four), which beats chance on New York Regents geometry (0.323, n=279) and on an Education Quality and Accountability Office (EQAO) grade 6 set (0.500, n=40), including an item whose stem asks for a tenths digit and whose key is the second-smallest of the four numbers. A pass on those items does not require the tagged operation. That is a fact about keys and programs, not about whether students learned the content.

## 1. Introduction

An assessment item arrives with a claim about what answering it requires. Utah Core and the Common Core State Standards (CCSS) print a standard code. TIMSS prints knowing, applying, or reasoning. A passing score is then used as evidence of that competency: in accountability, in curriculum evaluation, and in research that treats tagged items as operationalizations of skills.

That inference is an argument, not a definition (Kane; Messick). It can be wrong even when the publisher's tag is sincere. The item may be answerable from a surface cue, from the choices without the stem, or from a formula that never binds symbols to the situation the standard names.

This paper searches for those rival explanations as programs. A program that lacks an operation the tag names, never sees the published key, and still matches the key under the published scoring rule is a **witness**. A witness refutes the claim that a pass on that item requires the tagged operation. A search that finds no witness does not certify the tag beyond the programs that were tried. We do not estimate whether students learned the skill, whether humans use the shortcuts, or which curriculum is better. We never say students do not learn X.

The object is a requirement matrix \(E[t,o]\). For item \(t\) and named operation \(o\), the entry is 0 if some admitted program that lacks \(o\) answers \(t\) correctly, and 1 if none of the searched programs that lack \(o\) do. Operations are shared across authorities so that tags can be compared: retrieve, execute, bind, distinguish, explain, transfer. TIMSS items keep knowing, applying, and reasoning. We do not assign CCSS codes to TIMSS items.

Version 1 is a public-release census. TIMSS 2011 is the last cycle whose item texts, keys, scoring guides, domain tags, and percent correct are public together, with no permission process. From 2015, IEA keeps most items secured; restricted-use grants typically cap example items and forbid the comparisons this census needs. Recency of showable items comes from released state and provincial tests, not from a later TIMSS cycle.

## 2. Related work

Standards labeling matches item text to a code. MathFish and related classifiers ask whether a labeler agrees with a publisher. Agreement between labelers is not a test of whether the tagged operation is required to pass. We keep the publisher's tag and search for programs that pass without it.

Shortcut learning and partial-input baselines (Geirhos et al.; Gururangan et al.; Poliak et al.) show that models and rules can answer from the wrong slice of the input. Item-writing and test-wiseness catalogs (Millman, Bishop, and Ebel; Haladyna, Downing, and Rodriguez) list surface cues that can determine a choice without content. Those catalogs are our channels, not claims about students.

Q-matrix and cognitive-diagnosis methods estimate which skills an item requires from student response data. \(E\) is the adversarial counterpart that uses none. Comparisons to percent correct, when we make them, use only the statistics TIMSS already published with the public-release items.

## 3. Method

### Claims and corpora

Each claim is quoted from its authority. Utah Core grades 6–8 use Utah State Board of Education Core Guides. CCSS seed codes are checked against the same wording. TIMSS uses the 2011 framework definitions of knowing, applying, and reasoning.

Targets are released summative items and end-of-unit assessments with scoring rules. Practice problems are never targets. This census contains 2405 keyed public items (2245 selected-response, 160 numeric): New York Regents 1448, State of Texas Assessments of Academic Readiness (STAAR) 445, EQAO 149, TIMSS 2011 129, earlier TIMSS public-release 106, Programme for International Student Assessment (PISA) 70, New York State Education Department (NYSED) 27, National Assessment Program Literacy and Numeracy (NAPLAN) 21, Massachusetts Comprehensive Assessment System (MCAS) 10. Operational Utah RISE items are secure and are not used. TIMSS 2015 and later are not used.

### Channels

A channel fixes the information and the instruction set, and therefore the operations the program lacks.

- **Item-writing cues.** Option length, position, absolute terms, numeric middle value. Lacks every content operation.
- **Partial input.** Stem–option overlap and stem-number copying as rules. A language model that sees only the choices is the same channel when the stem is actually withheld. A model on the stem is an unrestricted solver and is forbidden.
- **Unbound execution.** A formula catalog (percent-of, unit rate, \(y=kx\), and so on) applied to numerals in the stem without binding symbols to the situation. Lacks bind and explain. This is the channel that applies to numeric items.

Instruction-only (worked examples from the same unit) is specified but was not run: curriculum scoring keys were not in the public files we could ingest.

### Admission and the witness bar

Two kinds of program are admitted.

1. **A priori rules**, taken from the catalogs with a citation each and no fitted parameters, scored on every item they apply to.
2. **Fitted or searched programs**, trained on items disjoint from those they are scored on. Headline form is cross-corpus: fit on state items, score on TIMSS, or the reverse. Reported accuracy is held-out only.

A program is a witness on a claim only if n scored is at least 10, the lower 95% bootstrap confidence interval of the pass rate exceeds format chance, and (for searched or fitted programs) the pass rate is at or above the 95th percentile of random programs of matched complexity. Chance for four-option selected items is 0.25. A singleton match is logged, not claimed. Random-weight programs are the baseline, never witnesses.

The searched class is a feature library of eleven surface cues, enumerated as conjunctions and signed weights up to complexity 3, plus greedy and evolutionary search: 1847 programs logged. Fourteen selected on the training corpus are scored on the other corpus only.

### Controls

Before a census null means anything, the same searcher has to find witnesses where they are known to exist. We run a synthetic Haladyna-flaw set (circular: the planted cues are the features) and, as the primary control, public multiple-choice corpora whose authors already published an options-only or question-ignored number.

## 4. Results

### Controls

On 1200 synthetic four-option items, each planted atomic program scored 50/50 on holdout, confidence interval [1, 1]. Recall of planted flaw types is 6/6. False-positive rate on matched clean holdout is 0. That shows the searcher fires when a unique surface cue is planted. It does not show that real released items contain such cues.

On public cue sets, the same 1847-program space, fit on a train split and scored held-out:

| corpus | published cue number | recovered held-out pass | n | witness |
|---|---|---:|---:|---|
| OpenBookQA | 0.496, plausible-answer detector that ignores the question (Mihaylov et al., 2018, Table 2) | 0.450 (longest option) | 329 | yes |
| SWAG | 0.436, ending-only LSTM+ELMo (Zellers et al., 2018, Table 3) | 0.565 (searched combination) | 62 | yes |
| RACE | (no official options-only number; chance 0.25) | 0.375 | 8 | no, n below 10 |
| CommonsenseQA | chance 0.20 | 0.227 | 22 | no |
| ARCT | 0.61 not-cue (not obtained) |  | 0 | not run |

The searcher recovers documented shallow cues on at least two corpora whose authors already published an options-only or question-ignored number. A TIMSS null is therefore not "the tool never finds anything."

### Power

A claim cannot clear the bar below n=10. For larger n, the minimum detectable bypass rate is the smallest observed pass rate whose bootstrap interval excludes chance. No cell in this census can detect a bypass below 0.15: that floor sits above four-option chance. After expanding from 208 to 2405 items, TIMSS knowing / applying / reasoning sit at n=81 / 68 / 86, with minimum detectable rates 0.358 / 0.353 / 0.372 (they were 0.434 / 0.432 / 0.500 at n=53 / 44 / 32). New York Regents Algebra I, n=598, can see down to 0.284.

### Census: what we claim

350535 local trials. Fitted stem n-gram and overlap programs, state to TIMSS and the reverse, do not beat chance on holdout (state to TIMSS applying+reasoning: 36/122 = 0.295, interval [0.213, 0.377], chance 0.254). Unbound unit-rate, \(y=kx\), and percent-of do not clear the bar on TIMSS, PISA, or NAPLAN numeric items.

No searched or a priori program cleared the bar on TIMSS knowing, applying, or reasoning. Failure to find a witness at a bar that can now see a bypass of about 0.35 does not certify those tags. It shows that this program space, on these public items, did not refute them.

We claim two a priori rows. Both are the central-numeric-option rule from the test-wiseness catalogs (Millman, Bishop, and Ebel; Haladyna, Downing, and Rodriguez): parse a leading signed number from each option; if at least three parse, sort them and pick the option at index \(\lfloor (n-1)/2 \rfloor\). For four options that is the second-smallest number, not the average of the two central values.

| authority | claim | n | pass | 95% CI | chance |
|---|---|---:|---:|---|---:|
| NY Regents | geometry | 279 | 0.323 | [0.265, 0.380] | 0.25 |
| EQAO | grade 6 | 40 | 0.500 | [0.350, 0.650] | 0.25 |

New York Regents Algebra II, same program, is 0.298 with interval [0.253, 0.344]. The lower end sits on chance. We do not claim it. Searched programs that clear the machine bar on TEKS grade 6 and on Regents Algebra I / geometry have n between 11 and 20. We do not claim them in this draft: the n is the witness floor, and 1847 programs were searched.

A language-model choices-only channel was run on 488 items with the stem withheld in the prompt. Option strings in TIMSS files often still contain country names from percent-correct tables; STAAR and Regents files often still contain page footers. Those rates are not a stem-removed condition. We do not report them as witnesses.

### An item the central-number rule answers

EQAO 2023 grade 6, released questions. Stem: "Which number has 4 as its tenths digit?"

A. 92.174 B. 85.043 C. 79.451 D. 43.256

Published key: C. File tag: B1-KU (grade 6, knowledge and understanding).

The sorted numbers are 43.256, 79.451, 85.043, 92.174. The rule picks index \(\lfloor (4-1)/2 \rfloor = 1\), which is 79.451, option C. The program never reads the stem and does not inspect tenths digits. Matching the key on this item does not require identifying a tenths digit. Whether a student's C should be read as evidence of that skill is the question we want education reviewers to answer.

The geometry row is the same program on 279 Part I items. Several of our text-layer stems are too messy to print; the rate is the result, not a single photographed page.

Passing those items does not require the tagged operation for this program. EQAO grade 6 and NY Regents geometry are exam or grade labels, not TIMSS reasoning. We do not rank Ontario, New York, or TIMSS.

## 5. What this does not show

We did not measure students. A witness is a fact about a key and a program. It is not a claim that students use the program.

We did not exhaust the class of programs that lack the tagged operation. A later search can find a TIMSS witness this one missed.

We did not finish a clean choices-only condition. Until option fields contain only option text, a model that sees those strings has not been shown to answer without the stem.

We did not ingest every public paper. STAAR 2013–2018, most NYSED 2018 graphic stems, TIMSS 2007, and later restricted TIMSS cycles are out of this file.

Constructed-response items are not headline cells. Scoring guides that reduce to a value are matching; explanations were not graded for this draft.

## 6. Release

Programs, filters, trials, and this text are in `temp/chat-assessment/`. The protocol is written and not yet timestamped. We will not plant a preprint while Algebra II sits on the bar, while searched n is 11, or while choices-only options still contain footers. Mentors are asked to read this draft as the paper, not as a preview of a longer one.

## References (to verify in copy-editing)

Geirhos et al., shortcut learning. Gururangan et al., annotation artifacts. Haladyna, Downing, and Rodriguez (2002), item-writing guidelines. Kane, argument-based validity. Messick, validity. Mihaylov et al. (2018), OpenBookQA. Millman, Bishop, and Ebel (1965), test-wiseness. Poliak et al., hypothesis-only baselines. Zellers et al. (2018), SWAG. TIMSS 2011 assessment framework and public-release items (IEA / NCES).
