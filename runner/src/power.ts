import { MIN_N_WITNESS } from "./programs/fitted.ts";
import { bootstrapCi, mulberry32 } from "./stats.ts";

export interface PowerRow {
  authority: string;
  claim: string;
  nItems: number;
  nSelected: number;
  chanceRate: number;
  minObservablePassRate: number | null;
  minDetectableTrueRate80: number | null;
  barNote: string;
}

function flagsFor(k: number, n: number): number[] {
  return [...Array(k).fill(1), ...Array(n - k).fill(0)];
}

export function minObservablePassRate(n: number, chance: number): number | null {
  if (n < MIN_N_WITNESS) return null;
  let lo = 0;
  let hi = n;
  let ans = n;
  while (lo <= hi) {
    const k = (lo + hi) >> 1;
    const ci = bootstrapCi(flagsFor(k, n), 400, 21 + n);
    if (ci[0] > chance) {
      ans = k;
      hi = k - 1;
    } else {
      lo = k + 1;
    }
  }
  return ans / n;
}

function powerAtK(n: number, k: number, chance: number, trials: number): number {
  const rng = mulberry32(77 + n + 10007 * k);
  const p = k / n;
  let wins = 0;
  for (let t = 0; t < trials; t++) {
    const flags: number[] = [];
    for (let i = 0; i < n; i++) flags.push(rng() < p ? 1 : 0);
    const ci = bootstrapCi(flags, 200, 31 + t);
    if (ci[0] > chance) wins += 1;
  }
  return wins / trials;
}

export function minDetectableTrueRate(n: number, chance: number, power = 0.8): number | null {
  if (n < MIN_N_WITNESS) return null;
  const trials = 200;
  let lo = 0;
  let hi = n;
  let ans = n;
  while (lo <= hi) {
    const k = (lo + hi) >> 1;
    if (powerAtK(n, k, chance, trials) >= power) {
      ans = k;
      hi = k - 1;
    } else {
      lo = k + 1;
    }
  }
  return ans / n;
}

export function powerNote(row: PowerRow): string {
  if (row.minObservablePassRate === null) {
    return `no witness found; n=${row.nItems} below witness bar (need ${MIN_N_WITNESS}); minimum detectable rate undefined`;
  }
  return `no witness found; minimum detectable rate ${row.minObservablePassRate.toFixed(3)} (80% power at ${row.minDetectableTrueRate80?.toFixed(3) ?? "n/a"})`;
}
