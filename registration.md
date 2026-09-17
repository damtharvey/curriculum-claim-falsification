# OSF registration: public-release census of assessment requirement

**Title.** Does the assessment require the skill? A public-release census of requirement versus mention.

**Status.** Protocol draft. Do not submit with results. This document registers the method, corpora, witness bar, and power plan only.

## Research questions

1. For released items tagged with a competency (Utah Core / CCSS standard, or TIMSS knowing / applying / reasoning), do programs that lack a named operation in that tag still pass under the published key?
2. Are bypassable items the ones students found easy, hard, or neither, on TIMSS 2011 public-release percent correct?
3. Do admitted programs transfer across corpora that share a claim or operation?

We will not estimate whether students learned the skill, rank countries or states, or claim that absence of a witness certifies the tag.

## Data

Public-release items only.

- TIMSS 2011 grade 4 and grade 8 mathematics public-release items (NCES / IEA). TIMSS 2011 is the last cycle whose texts, keys, scoring guides, domain tags, and percent correct are public without a permission process. No IEA request for 2015+.
- Released state and national items as ingested when keys and stems are recoverable without inventing graphics: NYSED, STAAR, MCAS, PISA released mathematics, NAPLAN 2012-2016 papers that include both items and keys. EQAO, Eureka/EngageNY, Illustrative Mathematics, and Siyavula only if a public scoring key is present.
- Practice problems: retrieval pool only, never targets.
- Out of scope: TIMSS 2015+ restricted-use, operational RISE items, paywalled RISE-prep.

Each item stores sourceUrl and licenseNote.

## Method positive controls (searcher validation)

Before interpreting a census null, run a held-out benchmark where witnesses are known:

- Synthetic items generated from the Haladyna, Downing, and Rodriguez item-writing-flaw taxonomy (longest key, stem-word repeat, absolute distractors, position bias, grammatical cue, implausible distractors), with a matched clean set and a train/holdout split.
- Any public real set with documented cue-flaw labels, if one can be obtained without API keys. If none is obtainable, record that and do not invent labels.

Report recall of planted flaws and false-positive rate on clean items at the same witness bar as the census.

## Claims and operations

Claims are quoted from the authority. Operations: retrieve, execute, bind, distinguish, explain, transfer. TIMSS items keep knowing / applying / reasoning. We do not re-author TIMSS items with CCSS codes.

## Channels

1. Item-writing cues (no model), including a searched feature library, not only a fixed 15-rule list.
2. Partial input: rules on stem n-grams and stem-option overlap (no model on the stem); choices-only may use a language model behind the filter if credentials exist.
3. Instruction only, when curricula with keys are ingested.
4. Unbound execution of a cited formula catalog.

Stem-only with a language model is not a channel.

## Program-space search

Feature library: option length rank, position, stem-option token overlap, number repeats, absolute terms, option numeric rank (min/median/max), option specificity, grammatical agreement with the stem, distractor distinctiveness, plus the numeric formula catalog. Search enumerates conjunctions and signed weights up to a complexity cap, plus greedy and evolutionary search. Fit on a training split (by corpus). Score only held-out. Log the size of the program space. Random-weight programs of matched complexity are a baseline distribution and are not witnesses.

## Witness bar

A program is a witness on a claim only if:

- the lower 95% bootstrap CI of the pass rate exceeds format chance, and
- n scored is at least 10, and
- for searched or fitted programs, the held-out pass rate is at or above the 95th percentile of random programs of matched complexity.

Singleton matches are logged, not claimed. Chance for four-option selected items is 1/n options. Chance for numeric unbound programs is 0.

Witness definition (verbatim): A witness is a program that is admitted under the a priori or held-out fitted rules, that never receives the published key, that lacks at least one operation the item's tag names as necessary, and that nevertheless scores as correct under the published scoring rule. A witness refutes the claim that a pass on that item requires the tagged operation. Failure of searched programs does not certify the tag.

## Power plan

For each claim and corpus, compute the minimum detectable bypass rate at the current n and bar (smallest observed rate whose bootstrap CI excludes chance; optionally the true rate with 80% power). Every null is reported as: no witness found; minimum detectable rate X. Claims with n below 10 cannot clear the bar.

## Outcomes

For each item and tagged operation, \(E[t,o] \in \{0,1\}\): 0 if a witness exists, 1 if no admitted program passed. Beside pass rates: chance rate, random-program baseline, complexity, bootstrap CI, power. Disputes where a reference solver disagrees with the published key are held out of the shortlist until reviewed.

## Analysis

Descriptive. Bypass rate by claim and by channel, only from witness-eligible programs. For TIMSS, relation between \(E\) and published percent correct if any cell is 0. No student microdata. No ranking of education systems. No results are deposited under this protocol until the searcher controls and power table exist.

## Exclusion and expansion

Later corpora use this protocol. Restricted-use TIMSS, if granted later, is a version 2 replication and is not analyzed under this registration.
