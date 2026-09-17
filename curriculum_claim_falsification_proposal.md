# Does the Assessment Require the Skill?

An assessment item carries a published claim about what answering it requires: a standard code, a curriculum tag, or a cognitive-process label such as reasoning. A passing score is then read as evidence of that competency. This project searches for rival explanations of the same score that do not go through the claimed competency, and it publishes each one as an executable witness.

\[
S \not\models C
\qquad\text{but}\qquad
\operatorname{Pass}(S,T,R)=1
\]

\(C\) is the claimed competency, \(T\) the published items, \(R\) the published scoring rule, and \(S\) a program whose inputs and operations exclude an operation the claim names as necessary.

The semantics are one-sided. A program that passes refutes the claim that passing requires \(C\). A search that finds no such program does not certify the claim beyond the program class searched. The project does not estimate whether students learn, whether humans use the discovered shortcuts, or which curriculum is better.

## Object

For each item \(t\) and each named operation \(o\), let \(\mathcal F_{\neg o}\) be the class of programs that lack \(o\) (defined by their inputs and their instruction set, below). The **requirement matrix** is

\[
E[t,o] =
\begin{cases}
1 & \text{no } f \in \mathcal F_{\neg o} \text{ answers } t \text{ correctly under } R \\
0 & \text{some } f \in \mathcal F_{\neg o} \text{ does; that } f \text{ and its trace are the witness}
\end{cases}
\]

A **requirement certificate** for a claim \((C, T, R, \tau)\) is the statement that every searched \(f \in \mathcal F_{I(C)}\) scores below \(\tau\) on \(T\), together with the search that was run. \(E\) is the adversarial, response-data-free counterpart of an expert Q-matrix or cognitive-domain tag, and the paper's comparisons are between \(E\) and those expert claims.

Operations are drawn from a fixed vocabulary so that claims from different authorities are comparable: recognize or retrieve; execute a procedure; bind symbols to a situation; distinguish between cases; explain or justify; transfer across representations.

## Claims

Each claim is quoted from its authority together with that authority's own operationalization.

| Authority | Claim form | Operationalization used |
|---|---|---|
| Utah Core Standards, grades 6–8 ([USBE PDF](https://schools.utah.gov/curr/mathematics/_mathematics_/_core/_utah_core_standards_tab_/CoreStandardsMiddleSchool.pdf)) | Standard code and text | Utah State Board of Education (USBE) Core Guides: Concepts and Skills to Master per standard |
| Common Core State Standards (CCSS), grades 6–8 | Standard code and text | Same codes as Utah Core in nearly all cases; verified per code |
| Trends in International Mathematics and Science Study (TIMSS), grade 8 | Cognitive domain per item: knowing, applying, reasoning | TIMSS assessment framework definitions of the three domains |
| Programme for International Student Assessment (PISA), mathematics | Process per item: formulate, employ, interpret | PISA framework definitions |
| Curriculum publishers | Standard tags on lessons and items | The tagged standard's operationalization above |

Mathematical Practices standards are not used. Seed standards, chosen because their text names an operation beyond execution:

| Code | Standard | Named operation |
|---|---|---|
| **7.RP.2.a** | Decide whether two quantities are in a proportional relationship, e.g. by testing equivalent ratios or graphing and observing whether the graph is a straight line through the origin. | Distinguish |
| **7.RP.2.b** | Identify the constant of proportionality (unit rate) in tables, graphs, equations, diagrams, and verbal descriptions of proportional relationships. | Bind to situation |
| **7.RP.2.c** | Represent proportional relationships by equations. For example, if total cost \(t\) is proportional to the number \(n\) of items purchased at a constant price \(p\), the relationship can be expressed as \(t = pn\). | Bind to situation |
| **7.RP.2.d** | Explain what a point \((x, y)\) on the graph of a proportional relationship means in terms of the situation, with special attention to \((0, 0)\) and \((1, r)\) where \(r\) is the unit rate. | Explain |
| **7.RP.3** | Use proportional relationships to solve multi-step ratio and percent problems. Examples: simple interest, tax, markups and markdowns, gratuities and commissions, fees, percent increase and decrease, percent error. | Bind (part/whole, before/after) |
| **7.EE.2** | Understand that rewriting an expression in different forms in a problem context can shed light on the problem and how the quantities in it are related. For example, \(a + 0.05a = 1.05a\) means that “increase by 5%” is the same as “multiply by 1.05.” | Bind to situation |
| **7.SP.1** | Generalizations about a population from a sample are valid only if the sample is representative. Random sampling is more likely to produce representative samples and support valid inferences. | Distinguish |
| **6.RP.2** | Understand the concept of a unit rate \(a/b\) associated with a ratio \(a:b\) with \(b \neq 0\), and use rate language in the context of a ratio relationship. | Bind to situation |
| **6.NS.1.c** | Explain the meaning of quotients in fraction division problems. For example, create a story context for \((2/3) \div (3/4)\) and use a visual fraction model to show the quotient. | Explain |
| **6.SP.1** | Recognize a statistical question as one that anticipates variability in the data related to the question and accounts for it in the answers. | Distinguish |

Every further standard whose Core Guide names an operation beyond execution and whose corpora contain items is included.

## Corpora

Items are used only where the score-to-competence inference is actually drawn: end-of-unit assessments with scoring rules, and released summative items. Practice problems are used for the memorizer channel's retrieval pool, not as targets.

| Corpus | Grades | Tags | Response type | Access |
|---|---|---|---|---|
| TIMSS public-release items, 2011 and earlier ([NCES](https://nces.ed.gov/timss/released-questions.asp)) | 8 (and 4) | Content domain, cognitive domain, key, scoring guide, per-country percent correct | Mixed selected and constructed | Last cycle whose item texts can be published with the statistics this paper needs; see below |
| PISA released mathematics items | 15-year-olds | Content category, process, key, coding guide | Mixed | Public (OECD) |
| New York State Education Department (NYSED) annotated released questions | 3–8 | CCSS code, key, rationale | Mostly selected; some constructed with rubrics | Public; reuse terms confirmed per year |
| State of Texas Assessments of Academic Readiness (STAAR) released tests | 3–8 | Texas standard, key | Selected and griddable | Public |
| Massachusetts MCAS released items | 3–8 | Standard, key, rubric | Mixed | Public |
| Education Quality and Accountability Office (EQAO) released assessments, Ontario | 6, 9 | Ontario expectation, key, scoring | Mixed | Public |
| National Assessment Program Literacy and Numeracy (NAPLAN) past papers, Australia | 7, 9 | Australian Curriculum code, key | Mostly selected | Public for 2012–2016 papers |
| Illustrative Mathematics / Open Up Resources | 6–8 | CCSS code, key, rubric | Mostly constructed | CC BY 4.0; unit assessments via free account |
| Eureka Math / EngageNY | 6–8 | CCSS code, key, rubric | Mostly constructed | CC BY-NC-SA |
| Siyavula and the Sasol Inzalo Senior Phase booklet, South Africa | 7–9 | CAPS topic | Constructed | CC BY-NC-SA |

Utah Core codes anchor the standards; CCSS-tagged corpora map onto them directly. TIMSS and PISA carry their own claims and are scored against those. The public [RISE mathematics blueprint](https://utahrise.org/content/contentresources/en/Math-Public-Facing-Blueprint_.pdf) records which Utah standards the state's grades 3–8 summative test weights; operational RISE items are secure and are not used.

**Why TIMSS 2011, not 2015–2023.** The object is the published relation between an item and its cognitive-domain tag, not a ranking of current student populations. TIMSS 2011 is the last cycle for which IEA released item texts, keys, scoring guides, domain codes, and per-country percent correct together, with no further permission required to reproduce those items as witnesses ([NCES](https://nces.ed.gov/timss/released-questions.asp)). From 2015, IEA keeps most items secured for trend measurement. The remainder are restricted-use: access is by [permission request](https://www.iea.nl/data-tools/permission-requests) (typically 3–6 weeks), grants usually allow publishing at most five items as examples, and typical conditions forbid comparisons to international results and conclusions about the study as a whole. Those conditions rule out the TIMSS analyses below (whether items tagged reasoning are answered without reasoning operations; whether bypassable items are the ones students found easy) and rule out publishing traces. The knowing / applying / reasoning definitions in the 2011 framework are the same three-domain structure later cycles use; what changed is release policy, not the claim type. Recency of the *items that can be shown* comes from the other rows: current Illustrative Mathematics, NYSED, STAAR, MCAS, EQAO. An IEA request for 2015+ restricted-use items is filed in parallel for a later replication if the grant language allows the same analyses; it does not delay or replace the public-release census.

## Channels

A channel fixes the information \(I\) and the instruction set available to a program, and therefore the operations it lacks. The channels come from catalogs of known rival explanations, not from invented student types.

| Channel | Available to the program | Operations lacked | Source |
|---|---|---|---|
| Partial input | Stem tokens and n-grams; or the choices with the stem removed; stem–option overlap | Bind, distinguish, explain | Shortcut learning; hypothesis-only and choices-only baselines (Geirhos et al.; Gururangan et al.; Poliak et al.; n-gram Clever Hans solvers) |
| Item-writing cues | Option length, position, grammatical agreement, absolute terms, distractor implausibility | All content operations | Test-wiseness and multiple-choice item-writing taxonomies (Millman et al.; Haladyna, Downing, and Rodriguez) |
| Instruction without the new inference | Nearest worked examples from the same unit, with number substitution | Bind, distinguish, transfer | Evidence-centered design: opportunity is not competence |
| Unbound execution | A formula catalog and substitution, with no binding of symbols to the situation; templated explanations | Bind, explain | The claim's own verbs (interpret, explain, distinguish) |

Programs are code. A language model may draft a program; it is not the restriction. A model is used as a backend only on the partial-input channel, where the input filter is the restriction; on the other channels the instruction set is the restriction and cannot be imposed on a model.

## Search discipline

Retaining whatever passes on \(T\) would fit \(T\). Two kinds of program are admitted:

1. **A priori rules** taken verbatim from the catalogs (longest option, stem–option overlap, invert-and-multiply, coefficient adjacent to \(x\)). These have no fitted parameters and are scored on every item.
2. **Fitted programs** trained on items disjoint from those scored: items from another corpus tagged to the same claim, or a held-out split within a corpus. Reported accuracy is held-out only. Cross-corpus generalization (fit on NYSED, score on TIMSS) is the headline form.

Every witness trace records how the rule was obtained and shows that the scored item's key was not available to it. Chance rates for selected-response items and a random-program baseline of matched complexity are reported next to every pass rate. Program complexity (feature count and description length) is reported so that minimal witnesses can be preferred.

## Scoring

Headline entries of \(E\) use items with deterministic keys: selected response, numeric, griddable, matching.

Constructed-response items are scored by human graders applying the published rubric or scoring guide (TIMSS two-digit coding, curriculum rubrics) to a shuffled set of program outputs and competent reference outputs, blind to source. The result for such an item is whether graders award passing credit to program output under the published rule. Model graders are not used for headline entries. Templated text satisfying rubrics has precedent in automated essay scoring (Perelman's BABEL against e-rater); here the template is bound to a specific lacked operation.

## Validation

- Every headline key is verified by a competent reference solver and a human.
- A reviewer who did not write the program confirms that the trace uses only the channel's inputs and instruction set and does not perform the lacked operation. Disagreements are published as disagreements.
- **Positive controls:** for each claim, items on which every searched program fails and the reference passes. Without such items for a claim, that claim's bypasses are reported as not discriminating.
- Items sharing a stimulus are treated as one cluster for counting.

## Comparisons

- \(E\) against the authority's tag: for TIMSS public-release items, the fraction tagged reasoning or applying that a partial-input or unbound-execution program answers; for standards, the fraction of items tagged to a bind / distinguish / explain standard that a program lacking that operation answers. These are tests of the published tag, not of current TIMSS country scores.
- \(E\) against per-item percent correct on the same public-release items (TIMSS publishes it): whether bypassable items were the ones students found easy, hard, or neither.
- A standards labeler (embedding match or model tag) on the same items, to show that a label agrees with the publisher while \(E\) does not.
- An unconstrained model critique asked to find shortcuts, to show which witnesses executable search finds that critique does not.
- Expert Q-matrix or cognitive-domain validation methods, which need student response data; \(E\) needs none.

## Repairs

For selected headline witnesses, a patched item on which the witness program fails and the reference passes is shown as an existence demonstration. No claim is made about the patched item's validity.

## Release

- The requirement matrix over all corpora, with one witness trace per zero entry and the search record per one entry.
- Programs, input filters, and instruction sets as code; scoring scripts; grader packets and blind grading results.
- A filterable page, one card per witness: authority, claim text and operationalization, corpus and item, channel, lacked operation, program, score, trace, and any patch. TIMSS item text appears only for public-release cycles. Restricted-use items, if later granted, are reported in aggregate with at most the number of example items the grant allows.
- A pre-registered census protocol (corpora, channels, admission rules, chance and random-program baselines) with a public timestamp, so later expansions run the same protocol.
- A short preprint on requirement versus mention, with related work on standards labeling (MathFish), argument-based validity and adversarial rebuttal (Kane; Messick; VAAI), shortcut and partial-input baselines, item-writing and test-wiseness catalogs, and Q-matrix validation.

## Evaluation

The result holds if a reader can run a witness on its channel's inputs, see it pass under the published rule, and see which named operation it lacks; if witnesses are obtained under the admission rules above and beat chance and the random-program baseline; if each reported claim has positive controls; and if at least one channel's witnesses transfer across corpora tagged to the same claim.
