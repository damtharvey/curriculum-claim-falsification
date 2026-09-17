export function mulberry32(seed: number): () => number {
  let a = seed >>> 0;
  return () => {
    a += 0x6d2b79f5;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export function mean(xs: number[]): number {
  if (!xs.length) return 0;
  return xs.reduce((a, b) => a + b, 0) / xs.length;
}

export function bootstrapCi(
  values: number[],
  nBoot = 1000,
  seed = 1,
): [number, number] {
  if (!values.length) return [0, 0];
  const rng = mulberry32(seed);
  const n = values.length;
  const stats: number[] = [];
  for (let b = 0; b < nBoot; b++) {
    let s = 0;
    for (let i = 0; i < n; i++) {
      s += values[Math.floor(rng() * n)]!;
    }
    stats.push(s / n);
  }
  stats.sort((a, b) => a - b);
  const lo = stats[Math.floor(0.025 * nBoot)]!;
  const hi = stats[Math.min(nBoot - 1, Math.floor(0.975 * nBoot))]!;
  return [lo, hi];
}

export function complexityFeatureCount(ruleId: string): number {
  const features: Record<string, number> = {
    "longest-option": 1,
    "stem-option-overlap": 1,
    "option-repeating-stem-numbers": 1,
    "avoid-absolute-terms": 1,
    "middle-value-option": 1,
    "position-c": 1,
    "invert-and-multiply": 2,
    "coefficient-adjacent-to-x": 1,
    "percent-of": 2,
    "percent-change": 3,
    "unit-rate": 2,
    "y-equals-kx": 2,
    "area-lw": 2,
    "volume-lwh": 3,
    "mean-of-listed-numbers": 1,
    "stem-ngram-classifier": 1,
    "random-choice": 0,
    "fitted-stem-ngram/state-to-timss": 8,
    "fitted-stem-ngram/timss-to-state": 8,
    "fitted-stem-overlap/state-to-timss": 4,
    "fitted-stem-overlap/timss-to-state": 4,
    "fitted-numeric-formula/state-to-timss": 2,
    "fitted-numeric-formula/timss-to-other": 2,
    "random-ngram-weights/state-to-timss": 8,
    "random-ngram-weights/timss-to-state": 8,
  };
  return features[ruleId] ?? 1;
}
