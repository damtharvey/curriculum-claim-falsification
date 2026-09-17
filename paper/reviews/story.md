# The one story

A pass on a tagged assessment item, in any subject, is read as evidence of the tagged competency, and that reading assumes the pass requires it; an assessment bypass, a solver that lacks the tagged competency by an explicit restriction on its operations or its information yet passes under the published scoring rule, refutes that requirement without students, and any assessment whose tag text, item text, keys, and scoring rule are public can be searched for one; we run the search first on public-release mathematics items, where those inputs are public and machine-checkable, and we find bypasses: on New York Regents Algebra I and II a language model that never sees the given quantities recovers the key in two model families and the recovery survives a change of option values, so a pass there does not require computing on the givens; small capability-restricted programs match keys on a few cells; TIMSS cognitive-domain cells, at the public sizes, yield no bypass; the claim is one-sided and student-free, and it is made on items re-read from the printed page because the released text layer often differs from the print.

Every section exists to support that sentence. The introduction states it, general phenomenon first and mathematics as the instantiation; Method defines its terms once, in the order bypass and restriction kinds (domain-neutral), items (where mathematics enters), families, bar and Holm, controls, print fidelity, codings; Results delivers it in the order measurement layer, language-model bypass, capability-restricted rows, TIMSS null and controls; Related Work says who studied one piece of it before; Limitations lists the real weaknesses of what was done, each with what it affects and what would fix it; the Conclusion restates what was asked, what each family showed, what it means for reading a tagged pass, what the method needs elsewhere, and the one-sided close.

# Framing pass (on f5fb3d4)

Mathematics first enters the body in Method 3.2, first sentence: "This census instantiates the method on public-release mathematics items." In the introduction it enters in paragraph 3: "We run the search first on public-release mathematics items, because ..." In the abstract: "We instantiate the search on public-release mathematics items, where tags, keys, and scoring rules are public, under a pre-registered bar."

| Idea | Home | Elsewhere |
|---|---|---|
| Why the tagged-pass reading matters across subjects (accountability, procurement, research outcome measures) | Intro para 1 | abstract, one clause |
| Restriction kinds are domain-neutral; one non-mathematics example of each (lexical policy on a causal-inference item; passage-withheld reader on a reading-comprehension item, which partial-input baselines already show) | Intro para 2 (examples); Method 3.1 (neutral definitions) | none |
| Why mathematics first (public standards, keys, scoring rules, item text; developed shortcut catalog) | Intro para 3, one sentence | Method 3.2 says only "instantiates" |
| Object and bar are general; census and findings are the mathematics instantiation | Intro contribution lead-in and bullets 1, 3 | Related Work last paragraph, one clause |
| What the method needs to run on another domain (tag text, item text, keys, executable scoring rule, machine-enforceable restriction) | Conclusion para 2 | abstract last sentence, one clause; removed from Limitations |
| Design choices formerly in Limitations (student-free, one-sided, vulnerability measure not a probability, matched-items-only coverage) | Intro para 2 (one-sided, student-free); Method 3.1 (vulnerability measure; matched items only) | Conclusion close (one-sided), stated as the close, not as an apology; removed from Limitations and Related Work ("Those catalogs are our programs, not claims about students") |
| Public-release only, TIMSS 2011 cutoff, selected-response floor, family splitting | Method 3.2 and 3.4 | removed from Limitations |
| Instruction-only channel specified and not run | Limitations (weakness, with the reason and the fix) | removed from Method 3.3 |
| Constructed-response scoring | Limitations (weakness) | removed from the old ingestion paragraph |

Limitations now hold ten weaknesses, each as one paragraph opening with the limitation: page instrument and 175 unverified items; item demand measured by language-model coders; template memorization untested; Qwen 14B text-layer arms below the floor; human sheet with one rater; EQAO and geometry rows small and unreplicated; STAAR replication limited to fetched forms and a hand-checked parse; instruction-only family not run; constructed-response items scored only where the guide reduces to a value; ingestion incomplete. The subset a reviewer would call inexcusable, with cost and whether it can still be done, is in `paper/reviews/weaknesses-without-excuse.md` and not in the paper.

The page target is dropped (no venue chosen): 19 pages, 0 overfull. No number changed; the only numbers in the new Limitations and Conclusion are already in Results or the appendix.

# Redundancy map (writing pass on fe7e282)

Format: idea -> home -> removed from (or cut to a clause in).

| Idea | Home | Removed from / cut to a clause |
|---|---|---|
| Bypass definition (policy lacking the tagged competency by explicit restriction, never sees the key, passes under the published rule) | Method 3.1 The object, in words | Intro para 3 formal notation (S, C, T, R, `S not-models C`, `Pass(S,T,R)`) deleted; intro bullet 1 cut to one sentence; Method Channels notation deleted; Related Work last paragraph cut to one clause; Results partial-input opening paragraph deleted |
| Two restriction kinds (capability vs information) and what each refutes | Method 3.1 | Intro para 3 (kept one clause in the story sentence); intro bullet 1 detail; Results partial-input para 2 deleted; Results item 22 argument trimmed; Results "What the channel measures" closing sentences deleted; Limitations language-model paragraph deleted |
| One-sidedness (a bypass says nothing about students; a null does not certify the tag) | Intro para 2 (story) + Limitations para 1 (scope) | Abstract (rewritten); intro para 3 three closing sentences; intro bullet 1 ("uses no student data and never yields..."); Method Channels; Related Work last paragraph ("Failure to find a program does not certify..."; "not a claim about whether students learned"); Results Census ("does not certify those tags"), partial-input ("not a claim that the model reasons, and not a claim that students guess"), lower-central paragraph ("The one-sided claim covers only the matched subset..."), "What would refute" subsection; Limitations para 2 (matched-subset list) |
| Students not measured / vulnerability caveat (pass rate is a vulnerability measure, never a probability a student lacks the competency) | Limitations para 1 | Intro paragraph after the ladder; Method Channels; Limitations language-model paragraph ("The model is not a student") |
| Claim ladder (mention, opportunity, requirement, discrimination, retention) | Intro para 2, one sentence in words | Intro Table 1 (claim ladder) deleted; capitalized level name "Requirement" dropped from intro bullet 1 and Method Channels |
| Holm families (105 catalog, 67 strategy, 68 language-model, each corrected on its own; 172 pool is a sensitivity) | Method 3.4 The witness bar and the Holm families | Intro bullet 2 (cut to "Holm-corrected separately"); Method catalog paragraph, Method language-model paragraph, Method Admission ("separate families... not members of the 105"); Related Work last paragraph; Results partial-input (68-test family definition repeated verbatim), Results Census (105 definition), Results Strategies ("three Holm families, never one mixed pool"), Results image backsolving and Limitations ("not a 67-family Holm test") |
| Witness bar (n >= 10, lower 95% CI above chance, machine bar; language-model bar adds the modal letter) | Method 3.4 | Method language-model paragraph (bar restated); Results partial-input para 1 (bar restated); Method image addendum bar moved into 3.4 |
| Print-fidelity procedure (filter thresholds, repair, verified population) | Method 3.6 Print fidelity | Intro bullet 2 long sentence (cut to "measured on the item as printed"); intro bullet 4 clause; Results opening paragraph deleted; Results partial-input para 3 (repaired-layer procedure repeated) deleted; Results "Repair" paragraph procedure sentences deleted (counts kept); Limitations instrument paragraph counts deleted (caveat kept) |
| Print-fidelity result (audit counts, 955/434/502/19, 606/431/175, verified fractions) | Results 4.1, first in Results | Limitations para 5 counts; Results partial-input para 3 counts; Results "An item the lower-central rule answers" fidelity sentence |
| TIMSS public-release reason (2011 last public cycle; IEA secures 2015+) | Method 3.2 Items and tags | Intro final paragraph deleted; intro bullet 3 clause; Limitations "later restricted TIMSS cycles" clause |
| TIMSS null is power-limited (floors) | Results 4.4 TIMSS and the controls | Results Census paragraph ("Failure to find a witness on public selected-response n of 65, 54, 68..."); Results "What would refute" final paragraph; Limitations para 3 (floors repeated; kept only "a later search can find a TIMSS witness this one missed"); intro bullet 4 ("power-limited non-refutation") |
| Masking rule and clean-option filter and letter rule | Method 3.3 Partial-input language models | Results partial-input para 1 (filter and letter rule restated); Results "Masked stem plus options" opening (masking rule restated) |
| Isomorph control definition | Method 3.3 | Results "Option-numeral isomorphs" (definition restated; kept one clause and the numbers); Related Work ("and we run that substitution on the option strings..." cut to one clause) |
| Lower-central rule definition | Method 3.3 Catalog rules | Method Admission paragraph merged into it; Results Census ("the lower-central signed variant of the catalog numeric-central-value cue in Section 3") |
| Verb-class rule and two blind coders | Method 3.7 Two codings of what an item asks | Results "Which items carry the rows" (rubric, blindness, and coder names restated); Limitations coder paragraph (rubric and blindness restated; kept the no-human-validation caveat and the Fan and Bialo citation) |
| The statement made (information) vs the statement not made (operation) | Results 4.2, one paragraph after the coder results | Abstract (rewritten to one clause); intro bullet 4 (one clause); Method 3.1 keeps only the definitional consequence; Results partial-input para 2, "What the channel measures", item 22 paragraph, and "What would refute" language-model paragraph; Limitations coder paragraph ("We therefore do not state...") |
| Mistral is a weak solver, not a missing cue | Results 4.2 Holm paragraph | Results "Scorer dependence" paragraph merged; Limitations language-model paragraph; "What would refute" |
| Geometry Phi-4 and TEKS rows not claimed | Results 4.2 Holm paragraph | Limitations language-model paragraph |
| EQAO and geometry rows are per-cell existence rows, replication candidates, not Holm survivors | Results 4.3 Catalog rules (once) + Table 4 caption | Results Census (stated three times); Limitations para 6 (entire paragraph deleted; the 5/10 strict cut lives in Appendix A.4); "What would refute" |
| STAAR closure discovery and failed replication | Results 4.3 Strategy programs | Limitations para 7 deleted; "What would refute" STAAR paragraph deleted |
| Image backsolving coverage 15/598 | Results 4.3 Image-channel backsolving | Limitations para 8 deleted; "What would refute" paragraph deleted |
| Controls (synthetic + public cue corpora) | Method 3.5 (design) + Results 4.4 (result) | Intro bullet 2 and bullet 4 clauses; Results "Strategy controls" paragraph merged into strategy paragraph |
| "What would refute these claims" subsection | deleted; each refutation condition is the bar in Method 3.4 | its unique clauses moved: shared-transcription-error caveat to Limitations para 3; "had the rank-preserving rate fallen to chance" to Results isomorph paragraph; "a further coding or third scorer" to Results 4.2 statement paragraph |

Count: 23 ideas homed; 71 restatements removed or cut to a clause.

# Abstract (second commit of the writing pass on 7f3e3e2)

Rewritten last from the first-reader test alone: 227 words (LaTeX-stripped count), no numbers beyond the two cell names and the two model families; first paragraph is the tag, the reading, the assumption, the bypass, and one-sidedness; second paragraph is the findings in the story's order and the page re-read. Record: `paper/abstract-intro-review.json`.

# Abstract (second commit of the framing pass)

Rewritten last: 242 words. First paragraph is tags in general (standard codes, cognitive domains, rubric criteria), the reading of a pass as evidence in accountability, procurement, and research, the assumption, the bypass as a general student-free test, and one-sidedness. Second paragraph instantiates on public-release mathematics items, gives the findings in the story's order and the page re-read, and closes with the scope sentence: a method demonstration on one subject, and what the search needs to run elsewhere. Record: `paper/abstract-intro-review.json`.

# Build

- Before: 23 pages, 0 overfull, body (intro through limitations) pages 1 to 16, appendix pages 18 to 23.
- After: 18 pages, 0 overfull, 0 undefined references, body pages 1 to 11, references 11 to 12, appendix 13 to 18. Body source 14,172 to 9,800 words.
- No number changed. The only number in the new body that was not in the old body or abstract is 0.591, the Qwen 14B TIMSS knowing rate already in Table B.2 (tab:masked), now cited in the TIMSS section.
