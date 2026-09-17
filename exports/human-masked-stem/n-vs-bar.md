# n versus the masked-stem channel bar

Registered success event (`preregistration.md`, `score_human_masked_stem.py`): lower 95% percentile bootstrap CI (`Random.randrange`, 1000 replicates, seed `21+n`, flags = k ones then n−k zeros) strictly above chance 0.25 and originally also above modal B 97/358 ≈ 0.271. Interval used below for the k table: that same bootstrap; Clopper–Pearson (equal-tailed) and Wald (z=1.96) first exceed 0.25 at the same k for every listed n. Wilson does not (sometimes one hit earlier). At n=40, CP 17/40 lower = 0.2704 clears 0.25 but not 0.271; bootstrap 17/40 lower = 0.275 clears both (matches the preregistered k=17).

A prefix of the shuffled sheet is not a new draw. Do not drop items after seeing scores.

| n | min k (boot L>0.25) | k/n | also >0.271? | CP L at k | Wald L at k | P(clear \| p=0.40) | P(clear \| p=0.425) | minutes (~30s) |
|---:|---:|---:|---|---:|---:|---:|---:|---:|
| 15 | 8 | 0.533 | no (need 9) | 0.266 | 0.281 | 0.21 | 0.28 | 7.5 |
| 20 | 10 | 0.500 | yes | 0.272 | 0.281 | 0.24 | 0.32 | 10 |
| 25 | 12 | 0.480 | yes | 0.278 | 0.284 | 0.27 | 0.36 | 12.5 |
| 30 | 13 | 0.433 | no (need 14) | 0.255 | 0.256 | 0.42 / 0.29 dual | 0.53 / 0.39 dual | 15 |
| 40 | 17 | 0.425 | yes | 0.270 | 0.272 | 0.43 | 0.56 | 20 |

80% power: none of these n, at 0.40 or 0.425 (14B on these 40). Registered 80% minimum detectable at n=40 is p=0.479. All listed designs are underpowered for a human at ~0.40. A non-clear is uninformative for true rates below that MDR, worse as n falls. Cutting n raises the observed rate you must hit (0.425 → 0.50 at n=20).

Prefix of the current order (registered A9 B11 C11 D9, lower-central 9/40): n=20 is A4 B7 C5 D4, lower-central 6/20. B share 0.35 vs registered 0.275 / population 0.271; lower-central 0.30 vs 0.225. Stratification breaks. A redrawn n=20 would need a new preregistration, not a silent prefix.

If humans match ~0.40, only n=40 is near the bar (need 17). n=30 has a weak shot at chance-only. n≤25 needs about 50% observed. Sending fewer is a protocol change.
