1. Send `rater-packet.txt`. Do not send `sheet-key.json`, `preregistration.md`, or anything else from this folder.
2. When replies come back, save `responses-<name>.txt` and from this repository root run `python scripts/score_human_masked_stem.py --rater <name>`.
3. `sheet-key.json` key letters are unchanged (all 40 still match the printed keys).
4. Drop these packet numbers from model kappa / 14B agreement. The human packet uses printed stem+options; the census row does not.

   Wrong item or wrong option set:
   - 17: census C/D glued extra equations; packet is the printed two-equation systems.
   - 22: census row is truncated and carries quadratic-root options; packet is the printed ice-cream systems (H half-gallons, P packages).
   - 26: census dropped L from p = 2L + 2w and smashed the three stacked formulas; packet is the printed formulas.
   - 28: census stem was a truncated stacked fraction; packet is the printed f(x) = (1/2)x² − ((1/4)x + 3).
   - 30: census A/B used 27; printed A/B are −7.
   - 36: census A/B were a single equation; packet restores the printed two-equation systems.
   - 37: census options were unrelated inequalities; packet is the printed I/II/III statements.

   Census OCR numbers/footers that do not match the printed option text the rater sees:
   - 6: census "26" for −6.
   - 13: census "2149"/"2143" for −149/−143.
   - 31: census "215"/"27" for −15/−7 (D is 25 in both).
   - 38: census D had a footer glued on.
   - 40: census B/D were stacked-radical OCR, not (5 ± √41)/2.

5. `rater-packet.md` is a byte-identical copy of `rater-packet.txt`.

## Results (two raters, 2026-09-17)

- survey-1 (registered primary): 15/40 = 0.375, bootstrap 95% CI [0.225, 0.525], no `R`. Does not clear chance 0.250 or modal 0.271. Underpowered null for true rates below 0.479.
- survey-2 (registered replication on the same 40 items, not pooled): 21/40 = 0.525, CI [0.375, 0.675], no `R`. Clears both bars.
- Agreement (`raters-agreement.json`): letter agreement 19/40, Cohen's kappa 0.308; both correct on 11 items, either correct on 25; pooled 36/80 = 0.450 with item-clustered bootstrap CI [0.325, 0.575] (descriptive only, per preregistration).
- Kappa with the frozen 14B letters: survey-1 0.135, survey-2 0.160.
