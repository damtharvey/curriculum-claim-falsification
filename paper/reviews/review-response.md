# Response to the ICML-style review

Paper: *Does the Assessment Require the Skill?* Review file: `paper/reviews/icml-style-review.md`.

## Implemented (agree)

- **W1.** Balepur et al. ACL 2024 (anthology 2024.acl-long.555) is the LM neighbor: withheld-quantity stems, publisher tags, Holm, and TIMSS cells on a census, not the first choices-only result. One follow-up sentence cites KnowLLM 2024 and ACL 2025 from the Anthology.
- **W2.** Phi-4 geometry remains unclaimed. Non-modal-key 0.229 n=118 stays in the unlabeled table row.
- **W3.** Catalog family-wise result is 105 tests, 0 Holm. Geometry 0.323 and EQAO 0.500 are existence / replication candidates (EQAO index-specific, with n and CI). They do not share the last-sentence punchline with the LM ladder.
- **W4.** Load-bearing citations with real records only: Attali and Bar-Hillel, JEM 2003 (DOI 10.1111/j.1745-3984.2003.tb01099.x); Terzi and Sen, Sage Open 2019 on TIMSS 2011 G-DINA Q-matrix misspecification (DOI 10.1177/2158244019832684); AERA/APA/NCME Standards 2014 (ISBN 978-0-935302-35-6) as a score-use standard, one sentence.
- **W5.** Twenty-item printed-page audit against local PDFs (`exports/print-audit/audit.json`): 8 match, 8 glue, 3 truncated, 1 wrong option set. No OCR. Counts in results and limitations.
- **W6.** TIMSS clustered floors printed from `power-by-cell.json`: 0.415 / 0.426 / 0.441. Memorable line is a null at n about 50 to 80.
- **W7.** Requirement matrix E[t,o] dropped from the introduction. Instruction-only is one limitations bullet. Not run.
- **W8.** One method sentence: catalog family locked in the protocol draft; strategy hashed before scoring; LM family scored the same day and Holm-corrected within family. Holm pooling not reopened.
- Human 15/40 kept as an uninformative null.

## Not implemented (disagree)

- Filling E[t,o] tonight, including empty columns. The object of the paper is cell-level program pass rates. An empty matrix would pretend a product that was not scored.
- OCR-rebuilding the 2405-item file tonight. The 20-item audit bounds the construct problem; a full rebuild is a different paper.
- Fetching TIMSS 2015+ / IEA restricted items. Public TIMSS is the census; later cycles stay out.
- Treating 15/40 as a human miss or a witness. The interval covers chance. The LM claim is a model fact.
- Expanding to conference length, adding Gemma, or extra p95 tables.
- Claiming Phi-4 geometry again. The non-modal split is already on disk.
- Bonferroni instead of Holm. Bonferroni is reported as a sensitivity (still 0 catalog rejects). The primary correction stays Holm.

## Not spent

Q3 (EQAO k=3 clustered CI tighter than the item CI): existence claim uses the item interval on n=40. The clustered interval is labeled descriptive. No new bootstrap tonight.
