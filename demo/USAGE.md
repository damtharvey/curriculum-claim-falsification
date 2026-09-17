# Usage Guide

How to use the CCF live demo at [https://d2nqjgx9lqdrd.cloudfront.net](https://d2nqjgx9lqdrd.cloudfront.net).

## What this demo shows

Assessment items carry published tags — a curriculum standard or cognitive domain like *reasoning*. A passing score is read as evidence of that competency. This demo lets you explore whether that inference holds by running **a priori programs** that lack the tagged operation against every item in a 2,405-item census.

A program that passes without using the tagged operation is a **witness** — it refutes the claim that passing requires that skill for that item. A program that fails proves nothing beyond the programs we tried. We never say students did not learn the skill.

## Item Explorer (`/items`)

The landing page shows all 2,405 items from the frozen census.

### Stats strip

The top row shows:
- **Items** — total keyed items (2,245 selected-response + 160 numeric)
- **Selected / Numeric** — breakdown by response type
- **A priori rules** — number of programs in the catalog
- **Witness rows** — total (item × operation) pairs where a program passed without the tagged skill

### Filtering

Use the controls to narrow down:
- **Search** — match against item ID, stem text, or claim code
- **Authority** — the standards body or assessment (timss, ccss-6-8, teks, nyregents, eqao, etc.)
- **Claim** — the specific standard or cognitive domain within that authority
- **Channel** — which restriction class the witness came from (item-cues, partial-input, unbound-exec)
- **Witnessed only** — toggle on (default) to show only items that have at least one witness

### Table columns

| Column | Meaning |
|--------|---------|
| Item | Unique item ID (click to open detail page) |
| Stem | Truncated question text |
| Authority | Standards body or assessment source |
| Claim | Standard code or cognitive domain |
| Type | Response type (selected, numeric, griddable) |
| Channel | Which channels produced witnesses for this item |
| Status | "Witness · N" if programs found, "No witness" otherwise |

Click any row to go to its detail page.

## Item Detail (`/items/:id`)

The detail page has two panels.

### Left panel — the item

- **Tags** showing authority, claim, corpus, year, grade, content domain, and response type
- **Stem** — the full question text
- **Choices** — answer options with the published key marked
- **Source** — link to the released assessment form, plus percent correct if the authority published it

### Right panel — a priori rules

When the page loads it runs all 15 a priori programs against the item. Each program operates on a restricted view — it never sees the answer key.

**Verdict banner:**

- **Witness found** (oxblood) — at least one program returned the key without the tagged operation. The banner names which operations are not required and how many programs succeeded.
- **No witness** (dashed border) — none of the searched programs returned the key. This does not certify the tag.
- **Running** (grey) — programs are still scoring.

**Results table:**

Each row shows one program:
| Column | Meaning |
|--------|---------|
| Program | Rule ID and the computation trace |
| Channel | item-cues, partial-input, or unbound-exec |
| Lacks | Operations this program does not perform (e.g., bind, explain) |
| Answer | What the program returned |
| Result | **Witness** (correct without the skill), **Miss** (wrong answer), **Abstain** (rule does not apply), or **N/A** (response type mismatch) |

Click **Run again** to re-execute the programs.

## The 15 A Priori Programs

These are the programs available in the interactive runner. None have fitted parameters — they are taken verbatim from published test-wiseness and shortcut-learning catalogs.

### Item-cues channel

These see only the answer options, never the stem. They lack all content operations.

| Program | Strategy |
|---------|----------|
| `longest-option` | Pick the longest answer choice by character count |
| `avoid-absolute-terms` | If exactly one choice lacks "always," "never," "all," etc., pick it |
| `middle-value-option` | Parse numbers from options; pick the median value |
| `position-c` | Always guess C (or the middle position) |

### Partial-input channel

These see the stem and options but rely on surface overlap, not comprehension. They lack bind, distinguish, and explain.

| Program | Strategy |
|---------|----------|
| `stem-option-overlap` | Pick the option sharing the most 4+ letter tokens with the stem |
| `option-repeating-stem-numbers` | Pick the option that repeats a number from the stem |

### Unbound-execution channel

These apply formulas without binding symbols to the situation. They lack bind and explain.

| Program | Strategy |
|---------|----------|
| `invert-and-multiply` | Take the first two fractions in the stem, compute (a/b) × (d/c) |
| `coefficient-adjacent-to-x` | Extract the number next to x in the stem |
| `percent-of` | Find p% and another number, compute (p/100) × n |
| `percent-change` | Detect increase/decrease keywords, compute n × (1 ± p/100) |
| `unit-rate` | Divide the first two non-zero numbers both ways, match a choice |
| `y-equals-kx` | Compute k = y/x from the first two numbers, apply to the third |
| `area-lw` | Detect area/rectangle/square keywords, multiply the first two numbers |
| `volume-lwh` | Detect volume/cubic keywords, multiply the first three numbers |
| `mean-of-listed-numbers` | Detect mean/average keywords, average all stem numbers ≤ 1000 |

## Configuration Pages

### Rules (`/admin/rules`)

Browse all a priori rule definitions. Each rule shows:
- **ID** — program identifier
- **Channel** — which view restriction it uses
- **Lacks** — which operations it does not perform
- **Applies to** — which response types it can score (selected, numeric, griddable)
- **Description** — what it does, with the academic citation

### Claims (`/admin/claims`)

Browse claims organized by authority file. Click an authority header to expand its claims table:
- **Code** — the standard code (e.g., 7.RP.2.a) or cognitive domain
- **Operations** — which operations the claim names as necessary
- **Items** — how many items in the census carry this claim
- **Text** — the standard text and the authority's own operationalization

### Data & Deploy (`/admin/data`)

Diagnostic page showing:
- **Runtime** — Node version, Lambda memory, AWS region
- **Data bucket** — S3 bucket name
- **API routes** — all available endpoints with descriptions
- **Data files** — every JSON file in the S3 bucket with size and last-modified timestamp

## Understanding the Results

### What a witness means

A witness is a concrete program that:
1. Never receives the published answer key
2. Lacks at least one operation the item's tag names as necessary
3. Returns the correct answer under the published scoring rule

This refutes the claim that passing this item requires the tagged operation — for this item only.

### What "no witness" means

If no program in the catalog returns the correct answer, it means exactly that: the programs we searched did not find a bypass. The tag is neither certified nor refuted. A different program class, or a model-based channel, might still find one.

### Chance and baselines

A single correct answer from a 4-option selected-response item has a 25% chance baseline. The full census applies Holm-corrected family-wise testing (see `exports/apriori-cell-table.json`). The demo runs individual items — a single item passing is a witness regardless of chance, because the program's trace shows it does not use the tagged operation.

## Tips

- Start with **Witnessed only** on (the default) to see items where programs found bypasses.
- Filter by `authority: nyregents` and `claim: algebra-i` to see the Algebra I population where masked-stem LMs also found witnesses.
- On an item detail page, expand the trace lines to see exactly how each program computed its answer.
- Compare the `item-cues` programs (which never see the stem) against `unbound-exec` programs (which see the stem but don't bind quantities to the situation).
- The `/admin/data` page confirms you're looking at the live Lambda, not a static mock.
