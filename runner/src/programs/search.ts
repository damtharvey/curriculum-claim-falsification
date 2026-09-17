import type { Item } from "../types.ts";
import type { ProgramResult } from "./apriori.ts";
import { FEATURE_NAMES, featureMatrix, uniqueMax, type FeatureName } from "../features.ts";
import { mulberry32 } from "../stats.ts";

export interface CueProgram {
  id: string;
  kind: "atomic" | "conjunction" | "weighted" | "greedy" | "evo" | "random";
  features: FeatureName[];
  weights: Partial<Record<FeatureName, number>>;
  complexity: number;
}

export interface SearchLog {
  programSpaceSize: number;
  enumerated: number;
  greedyEvaluated: number;
  evoEvaluated: number;
  randomEvaluated: number;
  selectedForHeldOut: number;
  complexityCap: number;
  featureLibrary: FeatureName[];
}

const COMPLEXITY_CAP = 3;

function combos<T>(xs: T[], k: number): T[][] {
  if (k === 0) return [[]];
  if (k > xs.length) return [];
  const [head, ...tail] = xs;
  return [...combos(tail, k - 1).map((c) => [head!, ...c]), ...combos(tail, k)];
}

export function enumeratePrograms(): CueProgram[] {
  const out: CueProgram[] = [];
  for (const f of FEATURE_NAMES) {
    out.push({
      id: `search/atom:${f}`,
      kind: "atomic",
      features: [f],
      weights: { [f]: 1 },
      complexity: 1,
    });
  }
  for (const pair of combos([...FEATURE_NAMES], 2)) {
    if (pair.length !== 2) continue;
    out.push({
      id: `search/and:${pair.join("+")}`,
      kind: "conjunction",
      features: pair,
      weights: Object.fromEntries(pair.map((f) => [f, 1])),
      complexity: 2,
    });
  }
  const signs = [-1, 1] as const;
  for (let k = 1; k <= COMPLEXITY_CAP; k++) {
    for (const feats of combos([...FEATURE_NAMES], k)) {
      if (feats.length !== k) continue;
      const signRows: number[][] = [[]];
      for (let i = 0; i < k; i++) {
        const next: number[][] = [];
        for (const row of signRows) {
          for (const s of signs) next.push([...row, s]);
        }
        signRows.splice(0, signRows.length, ...next);
      }
      for (const row of signRows) {
        const weights: Partial<Record<FeatureName, number>> = {};
        feats.forEach((f, i) => {
          weights[f] = row[i];
        });
        const id = `search/w:${feats.map((f, i) => `${f}${row[i]! >= 0 ? "+" : "-"}${Math.abs(row[i]!)}`).join(",")}`;
        if (k === 1 && row[0] === 1) continue;
        if (k === 2 && row.every((s) => s === 1)) continue;
        out.push({ id, kind: "weighted", features: feats, weights, complexity: k });
      }
    }
  }
  return out;
}

export function applyCueProgram(program: CueProgram, item: Item): ProgramResult {
  const letters = Object.keys(item.choices ?? {}).sort();
  if (!letters.length) {
    return { answer: null, skipped: true, skipReason: "no choices", trace: [program.id] };
  }
  const matrix = featureMatrix(item);
  const scores: Record<string, number> = {};
  for (const k of letters) {
    let s = 0;
    if (program.kind === "conjunction") {
      const vals = program.features.map((f) => matrix[k]?.[f] ?? 0);
      s = vals.every((v) => v > 0) ? vals.reduce((a, b) => a + b, 0) : 0;
    } else {
      for (const f of program.features) {
        s += (program.weights[f] ?? 0) * (matrix[k]?.[f] ?? 0);
      }
    }
    scores[k] = s;
  }
  const pick =
    program.kind === "random"
      ? uniqueMax(scores, { requirePositive: false, allowTieFirst: true })
      : uniqueMax(scores);
  if (!pick) {
    return {
      answer: null,
      skipped: true,
      skipReason: "no unique positive score",
      trace: [program.id, `scores=${JSON.stringify(scores)}`],
    };
  }
  return {
    answer: pick,
    skipped: false,
    trace: [program.id, `scores=${JSON.stringify(scores)}`, `pick ${pick}`],
  };
}

function passRate(program: CueProgram, items: Item[]): { n: number; rate: number } {
  let n = 0;
  let hit = 0;
  for (const item of items) {
    if (item.responseType !== "selected") continue;
    const r = applyCueProgram(program, item);
    if (r.skipped || !r.answer) continue;
    n += 1;
    if (r.answer.toUpperCase() === item.key.toUpperCase()) hit += 1;
  }
  return { n, rate: n ? hit / n : 0 };
}

function randomProgram(rng: () => number, complexity: number, index: number): CueProgram {
  const pool = [...FEATURE_NAMES];
  const features: FeatureName[] = [];
  while (features.length < complexity && pool.length) {
    const i = Math.floor(rng() * pool.length);
    features.push(pool.splice(i, 1)[0]!);
  }
  const weights: Partial<Record<FeatureName, number>> = {};
  for (const f of features) weights[f] = rng() < 0.5 ? -1 : 1;
  return {
    id: `search/random:k${complexity}:${index}`,
    kind: "random",
    features,
    weights,
    complexity,
  };
}

export function greedySearch(train: Item[], rng: () => number): { program: CueProgram; evaluated: number } {
  let chosen: FeatureName[] = [];
  let evaluated = 0;
  let bestRate = -1;
  for (let step = 0; step < COMPLEXITY_CAP; step++) {
    let stepBest: FeatureName | null = null;
    let stepRate = bestRate;
    for (const f of FEATURE_NAMES) {
      if (chosen.includes(f)) continue;
      const cand: CueProgram = {
        id: `search/greedy:${[...chosen, f].join("+")}`,
        kind: "greedy",
        features: [...chosen, f],
        weights: Object.fromEntries([...chosen, f].map((x) => [x, 1])),
        complexity: chosen.length + 1,
      };
      evaluated += 1;
      const { rate } = passRate(cand, train);
      if (rate > stepRate || (rate === stepRate && rng() < 0.1)) {
        stepRate = rate;
        stepBest = f;
      }
    }
    if (!stepBest || stepRate <= bestRate) break;
    chosen = [...chosen, stepBest];
    bestRate = stepRate;
  }
  if (!chosen.length) chosen = ["longest"];
  return {
    program: {
      id: `search/greedy:${chosen.join("+")}`,
      kind: "greedy",
      features: chosen,
      weights: Object.fromEntries(chosen.map((x) => [x, 1])),
      complexity: chosen.length,
    },
    evaluated,
  };
}

export function evolveSearch(train: Item[], rng: () => number): { program: CueProgram; evaluated: number } {
  const pop = 24;
  const gens = 6;
  let evaluated = 0;
  let people: CueProgram[] = [];
  for (let i = 0; i < pop; i++) {
    people.push(randomProgram(rng, 1 + Math.floor(rng() * COMPLEXITY_CAP), i));
  }
  let best = people[0]!;
  let bestRate = -1;
  for (let g = 0; g < gens; g++) {
    const scored = people.map((p) => {
      evaluated += 1;
      return { p, rate: passRate(p, train).rate };
    });
    scored.sort((a, b) => b.rate - a.rate);
    if (scored[0]!.rate > bestRate) {
      bestRate = scored[0]!.rate;
      best = scored[0]!.p;
    }
    const keep = scored.slice(0, 8).map((s) => s.p);
    people = [...keep];
    while (people.length < pop) {
      const parent = keep[Math.floor(rng() * keep.length)]!;
      const child: CueProgram = {
        id: `search/evo:g${g}:${people.length}`,
        kind: "evo",
        features: [...parent.features],
        weights: { ...parent.weights },
        complexity: parent.complexity,
      };
      if (rng() < 0.5 && child.features.length) {
        const f = child.features[Math.floor(rng() * child.features.length)]!;
        child.weights[f] = (child.weights[f] ?? 1) * -1;
      } else if (child.features.length < COMPLEXITY_CAP) {
        const extra = FEATURE_NAMES.find((f) => !child.features.includes(f));
        if (extra) {
          child.features.push(extra);
          child.weights[extra] = rng() < 0.5 ? -1 : 1;
          child.complexity = child.features.length;
        }
      }
      people.push(child);
    }
  }
  return {
    program: { ...best, id: `search/evo:${best.features.join("+")}`, kind: "evo" },
    evaluated,
  };
}

export interface SearchFit {
  selected: CueProgram[];
  randoms: CueProgram[];
  log: SearchLog;
  trainN: number;
}

export function fitSearch(train: Item[], seed = 20260916): SearchFit {
  const rng = mulberry32(seed);
  const selectedTrain = train.filter((it) => it.responseType === "selected" && it.choices);
  const enumerated = enumeratePrograms();
  const ranked = enumerated
    .map((p) => ({ p, ...passRate(p, selectedTrain) }))
    .filter((x) => x.n >= 8)
    .sort((a, b) => b.rate - a.rate);
  const greedy = greedySearch(selectedTrain, rng);
  const evo = evolveSearch(selectedTrain, rng);
  const top = ranked.slice(0, 12).map((x) => x.p);
  const selected = [...top, greedy.program, evo.program];
  const randoms: CueProgram[] = [];
  for (let k = 1; k <= COMPLEXITY_CAP; k++) {
    for (let i = 0; i < 40; i++) randoms.push(randomProgram(rng, k, 1000 * k + i));
  }
  return {
    selected,
    randoms,
    trainN: selectedTrain.length,
    log: {
      programSpaceSize: enumerated.length + greedy.evaluated + evo.evaluated + randoms.length,
      enumerated: enumerated.length,
      greedyEvaluated: greedy.evaluated,
      evoEvaluated: evo.evaluated,
      randomEvaluated: randoms.length,
      selectedForHeldOut: selected.length,
      complexityCap: COMPLEXITY_CAP,
      featureLibrary: [...FEATURE_NAMES],
    },
  };
}

export function randomPassRates(randoms: CueProgram[], evalItems: Item[]): Record<number, number[]> {
  const byK: Record<number, number[]> = { 1: [], 2: [], 3: [] };
  for (const p of randoms) {
    const { rate, n } = passRate(p, evalItems);
    if (n >= 8) byK[p.complexity]?.push(rate);
  }
  return byK;
}

export function percentile(xs: number[], p: number): number {
  if (!xs.length) return 1;
  const s = [...xs].sort((a, b) => a - b);
  const i = Math.min(s.length - 1, Math.max(0, Math.ceil(p * s.length) - 1));
  return s[i]!;
}
