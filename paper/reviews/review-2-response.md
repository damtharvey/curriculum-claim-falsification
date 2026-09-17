# Response to review 2 (`icml-style-review-2.md`)

Status at 2026-09-17. Weaknesses 1 to 3 and what is being done.

## W1. Headline object vs the strongest result (masked-stem Algebra I and II)

Plan: make the tag per item and split by what the standard names. NYSED rating guides map every Regents question to a CCSS cluster (for example `A-REI.B`), so the split is on cluster heading text under a pre-registered verb-class rule (`execution` / `recognition_or_interpretation` / `mixed`), then joined to the saved per-item masked-stem predictions for Qwen2.5-7B, Qwen2.5-14B, and Phi-4. Witness bar per cell: n >= 10, lower CI above chance and above the modal letter, stated one-sided.

Done in this job: extraction scripts (`scripts/extract_regents_standards.py`, `scripts/regents_glyph_reader.py`, `scripts/fetch_ccss_cluster_text.py`) and `exports/standards-split/README.md`. Not done: the item-standards file, the standards text, the preregistration, the classification, the join, the tables. See `exports/standards-split/README.md` for the exact state and the steps to finish. No hit rates by standard were looked at.

## W2. Measurement layer is not the printed test

Handled by the print-faithful rescoring job (`exports/print-faithful/`, other worker). Not touched here.

## W3. Missing program priors

Verified and cited in `paper/related.tex` with entries in `paper/references.bib`:

- Watson, Ma, Tejwani, Chang, Ahn, Sundararajan (2018), WWW '18 Companion, doi 10.1145/3184558.3186340. Key `Watson_2018`.
- Moore, Costello, Nguyen, Stamper (2024), SAQUET, AIED 2024, LNCS, doi 10.1007/978-3-031-64299-9_3. Key `Moore_2024`.
- Fang, Oberski, Nguyen (2025), PATCH, GEM² workshop at ACL 2025, ACL Anthology 2025.gem-1.68 (arXiv 2404.01799). Key `fang-etal-2025-patch`.
- Mirzadeh, Alizadeh, Shahrokhi, Tuzel, Bengio, Farajtabar (2025), GSM-Symbolic, ICLR 2025, OpenReview AjXkRZIvjB (arXiv 2410.05229). Key `mirzadeh2025gsmsymbolic`.

All four exist as the review describes; none was skipped. The bib has not been recompiled after these additions. Billing changes (contribution bullets, abstract) belong to the integration pass.
