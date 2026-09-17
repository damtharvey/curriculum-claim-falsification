# CHAT: Does the Assessment Require the Skill?

Minds & Machines, 15–17 September 2026. Presentations Thursday 17 September, 15:00–17:00.

Snapshot: Wednesday 2026-09-16 about 17:55 MDT. Working tree: this repository. Research spec `curriculum_claim_falsification_proposal.md`. Status `STATUS.md`.

Nothing is frozen. Continuous integration through Thursday morning. Harvey owns all build, science, and paper. Alejandra Moctezuma (Utah Valley University) owns mentor outreach. Coy is out. No arXiv or OSF deposit. Mentor comments that arrive later do not change the talk.

Paper: `acmart` `sigplan,screen,nonacm,review`, author-year, 11 pages. Authors Harvey Dam (University of Utah) and Alejandra Moctezuma (Utah Valley University). Navy `\wip` marks unfinished work. Built PDF is `paper/main.pdf`; mentor copy is `paper/mentor-packet/paper.pdf`.

## 1. The claim

An item comes with a published tag saying what answering it requires: a standard code, or a TIMSS cognitive domain such as reasoning. A passing score is read as evidence of that competency.

We search for programs that lack the tagged operation and still pass under the published key. Each one is a witness that the tag overstates what a pass shows.

The result is one-sided:

- A program that passes refutes the tag for that item.
- A program that fails proves nothing beyond the programs we tried.

We never say students did not learn the skill.

## 2. Who does what

Two people. Coy is out.

| Person | Owns | Does not own |
|---|---|---|
| Harvey | Claims, runner, ingestion, census, paper, slides, demo, license calls, registration text | Recruiting reviewers |
| Alejandra | Mentor outreach and review intake | Code, data, paper prose, slides unless Harvey asks |

Harvey runs agents against the whole tree. Nothing waits on Coy.

### Alejandra: mentors

Send from `paper/mentor-packet/`:

- Paste `cover.md` as the email body. It asks for a read and unstructured feedback or a short review. Not a questionnaire.
- Attach only `paper.pdf`. Nothing else.

Do not attach `paper.md` (stale dump), `witnesses.json`, choices-only rates, searched rows with n below 30, or the human rater key.

Record one row per mentor in `paper/mentor-log.md`: name, when contacted, whether they agreed, comments received, Harvey's response.

She decides who on the list to try first. Harvey decides what the packet claims. Comments tonight help the paper if they arrive; they do not change Thursday's talk.

## 3. Where the work is (continuous integration)

Three Holm families, never one mixed pool. Pass does not require the tagged operation. Never "students didn't learn."

**Catalog family (105 a priori tests): 0 Holm rejects.** Five rows clear the per-cell bar. Per-cell witnesses kept as replication candidates:

- NY Regents geometry, lower-central, 90/279 = 0.323, item CI [0.265, 0.380]. Clustered CI still excludes chance.
- EQAO grade 6, 20/40 = 0.500, item CI [0.350, 0.650]. Index-specific: only the pre-registered lower-central index clears.

Algebra II lower-central 0.298 n=372 sits on the bar; not claimed. Searched n=11–20 rows are not claimed (fail late held-out).

**Strategy family (67 tests):** S3 arithmetic closure on STAAR grade 5, 21/40 = 0.525, was the Holm reject on the frozen 2019/2021/2022 census. Powered replication on held-out 2013/2014/2016 plus 2017/2018 after option-leak repair failed: combined 21/64 = 0.328, CI [0.219, 0.438] covers chance. Not a confirmed discovery. Backsolving unmeasured (equations are images; no cell n fired ≥ 10).

**LM partial-input (masked stem, quantities withheld, primary population `masked_token_count≥1`; Holm family 68 tests with n≥10 on that population).** Claimed: Algebra I and Algebra II on Qwen2.5-7B, Qwen2.5-14B, and Phi-4; geometry on Phi-4 only (67/166 = 0.404, CI [0.331, 0.476] versus chance 0.250 and modal letter 0.289). Mistral-7B is a weak solver (with-stem ceiling ≈ masked-stem). TEKS grade 5 and grade 8 Qwen-7B-only rows not claimed. Contamination probes negative. TIMSS knowing / applying / reasoning: no catalog, strategy, or partial-input channel clears on the withheld-quantity population at the paper's clustered floors 0.400 / 0.407 / 0.421.

`% REPLICATION SLOT` and `% SECOND FAMILY SLOT` in `results.tex` are filled (STAAR non-replication; Phi-4 including geometry). Navy `\wip` still true for human ratings, unfetched STAAR grade 5 2015/2020/2023 forms, and backsolving.

Built (unchanged bar: n ≥ 10, lower 95% CI above chance; searched/fitted also above random-program p95):

- TypeScript runner, validator CLI, claims files, 1847-program search
- 2405 keyed public items (2245 selected, 160 numeric). NY Regents 1448, STAAR 445, EQAO 149, TIMSS 2011 129, earlier TIMSS 106, PISA 70, NYSED 27, NAPLAN 21, MCAS 10
- Synthetic Haladyna recall 6/6, FPR 0 (circular). OpenBookQA longest-option 0.450 vs published 0.496. SWAG searched 0.565 vs published ending-only 0.436
- Census 350535 trials. Fitted n-grams fail cross-corpus and fail temporal held-out (state-pooled 0.257, n=1243)
- Choices-only remains exploratory, not a witness. Clean filter 1496/2245. Local 7B and 14B both 0.301 n=1487; proprietary 0.359 n=1493. 7B does not beat any cell modal-letter baseline. 14B Algebra I options-only lower CI exceeds modal B; still unclaimed. The claimed LM object is masked-stem, not options-only.

`witnesses.json` still has hundreds of item-level rows (`nWitnessesClaimed` 516 is item-level; do not cite). Shortlist only claimed rows. Algebra II catalog middle-value is not slide material.

Human masked-stem 40-item sheet: `exports/human-masked-stem/rater-packet.txt` being cleaned in one pass (in flight as of 17:45). Send the `.txt`, not a PDF. Forty items are required for the registered bar. Scores not in.

No UI. No deposit.

## 4. Admission rules (unchanged)

A program is admitted only one of two ways.

1. **A priori rule.** Taken verbatim from a catalog, with no fitted parameters. Cited per rule (Millman et al.; Haladyna, Downing, and Rodriguez; Gururangan et al.; Poliak et al.). Scored on every item.
2. **Fitted program.** Trained on items disjoint from those it is scored on: another corpus with the same claim or operation, or a held-out split. Reported accuracy is held-out only. Headline form is cross-corpus.

Beside every pass rate we report chance, a random-program baseline of matched complexity, program complexity, and a bootstrap CI.

A **claim-level witness** is a program whose held-out pass rate on a named claim clears the bar above. An item the program happens to get right is a trace, not a result. Shortlist only from claim-level witnesses.

Positive controls: for every claim, at least one item that every admitted program fails and the reference solver passes. A claim without one is labeled not discriminating.

The hashed strategy programs and the masked-stem LM channel are additional families, each Holm-corrected on its own, under the same one-sided bar.

## 5. Remaining work (Wednesday evening through Thursday morning)

The PDF is not frozen. Thursday talk 15:00–17:00. Mentor comments do not change the talk.

1. Finish the human 40-item masked-stem sheet (`rater-packet.txt`), send it, score when replies land. Do not cut n.
2. Optional slides from the current PDF. Backup: the PDF on a laptop.
3. Rebuild `paper/main.pdf` and copy to `paper/mentor-packet/paper.pdf` if science changes. Alejandra's attachment is always that copy.
4. **No deposit.** Mentors are reading a draft. No arXiv. No OSF.

Parked, not scheduled: STAAR grade 5 2015/2020/2023 forms; backsolving (equation images); NYSED OCR; TIMSS 2015+ with IEA permission; dirty-option strip-and-rescore; a scorer larger than 14B; replication of the two catalog witnesses on new administrations.

## 6. Human attention

| Task | Who | When |
|---|---|---|
| Mentor email: `cover.md` body, `paper.pdf` only | Alejandra | Wednesday; comments do not change the talk |
| Collect comments | Alejandra | If they arrive; later comments still useful for the paper |
| Human 40-item sheet (`rater-packet.txt` only) | Harvey (send); raters work alone | In flight as of 17:45; scores not in |
| What the paper and slides may claim | Harvey | Continuous through Thursday morning |
| License: EQAO item text is public released questions; TIMSS public-release for any TIMSS example | Harvey | Wednesday |
| Optional slides from the current PDF | Harvey | Wednesday evening |
| Thursday |  | The talk 15:00–17:00. No work block. |

## 7. Judging

| Criterion | What we show |
|---|---|
| Impact | Which tagged items, in released assessments, do not require the tagged skill, if any claim-level witness exists. Catalog: two per-cell witnesses that fail Holm. Strategy: one Holm reject that failed replication. LM: existential partial-input reader on Algebra I/II (two families) and geometry (Phi-4). TIMSS: a search that recovers planted cues and still finds no channel at the stated floors. |
| Innovation | A requirement matrix built by adversarial search with no student response data. |
| Design | Executable traces, channels that each lack a named operation, held-out and random-program baselines, power on every cell, three Holm families. |
| Presentation | A judge picks a claim and watches a program on a real released item, or watches the search fail on a TIMSS reasoning item the reference passes. |
| Feasibility | Public items only. Protocol is written. It is not submitted until the result is. |
| Data quality | Published keys; disputes parked; license noted per item. Mentor comments on the draft if they arrive. |
| Ethics | No student data. One-sided claims. No ranking of countries, states, or publishers. |

## 8. Timeline

| When | Milestone | Who |
|---|---|---|
| Wed through ~17:55 MDT | Paper at 11 pages with catalog, failed STAAR replication, and LM (Qwen + Phi-4) in the PDF | Harvey |
| Wed evening | Human 40-item packet in flight; mentors may still be contacted | Harvey, Alejandra |
| Wed evening–Thu morning | Rebuilds if science changes; optional slides from the current PDF | Harvey |
| Thu 15:00–17:00 | Present. Mentor comments do not change this talk. | Harvey, Alejandra |

Alejandra pings Harvey if a mentor replies. Replies can enter a later rebuild of the paper. They do not change the talk.

## 9. Risks

- **Item-level hits treated as results.** `witnesses.json` will tempt a slide. Shortlist only claim-level rows. Algebra II middle-value is not slide material.
- **STAAR closure sold as a discovery.** 21/40 Holm-rejected on the census and failed powered replication. Say that.
- **Dirty options.** Country-table suffixes and page footers make choices-only not stem-blind. Strip before claiming. Choices-only is not a witness.
- **Grade labels as claims.** EQAO g6 and TEKS g3 are not TIMSS reasoning. A middle-value hit on a grade label is a cue finding, not a cognitive-domain refutation. EQAO is index-specific.
- **Human n cut.** The registered bar needs the 40-item sheet. A prefix is not a new draw.
- **Thin searched n.** n=11 to 20 with 1847 programs searched needs the random p95, not a headline.
- **Mentors unavailable.** Present anyway. Their comments are for the paper, not a gate on the demo, and they do not change the talk.
- **Reuse terms.** Show TIMSS 2011 public-release text. Aggregate the rest until Harvey clears the license note.
- **Reviewers ask why TIMSS is 2011.** Last cycle whose texts, keys, scoring guides, tags, and percent correct are public without a permission process. Newer cycles are a later revision.
- **Multiplicity.** 105 catalog tests; the two claimed catalog rows fail Holm. The paper reports that and keeps them as per-cell witnesses. Do not hide it on a slide.
- **Overclaiming.** Every surface says "passing does not require X." None says "students do not learn X."
