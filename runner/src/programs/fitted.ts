/**
 * Admission rule 2: fitted programs trained on items disjoint from those scored.
 * Keys of the scored items are never used in training. Traces record the train slice.
 */

import { extractNumbers, surfaceFeatures, tokenize } from "../channels.ts";
import type { Item } from "../types.ts";
import { answersMatch, formatNumber, matchNumericToChoice } from "../channels.ts";
import { mulberry32 } from "../stats.ts";
import type { ProgramResult } from "./apriori.ts";

export const STATE_CORPORA = new Set(["nysed", "staar", "mcas", "nyregents", "eqao"]);
export const TIMSS_CORPORA = new Set([
  "timss2011",
  "timss2007",
  "timss2003",
  "timss1999",
  "timss1995",
  "pisa",
  "naplan",
]);
export const TIMSS_HEADLINE_CLAIMS = new Set(["applying", "reasoning"]);

export const MIN_N_WITNESS = 10;

export interface NgramModel {
  keyCount: Map<string, number>;
  distCount: Map<string, number>;
  keyTotal: number;
  distTotal: number;
  trainN: number;
  trainIds: string[];
}

export interface OverlapModel {
  weight: Map<string, number>;
  trainN: number;
  trainIds: string[];
}

export type FormulaId =
  | "div-a-b"
  | "div-b-a"
  | "mul-ab"
  | "add-ab"
  | "sub-abs"
  | "mul-abc"
  | "percent-of"
  | "percent-down"
  | "percent-up"
  | "mean"
  | "square";

export interface FormulaModel {
  formulaId: FormulaId;
  trainHits: number;
  trainN: number;
  trainIds: string[];
  catalogHits: Record<string, number>;
}

function optionText(item: Item, letter: string): string {
  return item.choices?.[letter] ?? "";
}

export function optionFeatures(item: Item, letter: string): string[] {
  const opt = optionText(item, letter);
  const stemToks = tokenize(item.stem).filter((t) => t.length >= 3);
  const optToks = tokenize(opt).filter((t) => t.length >= 3);
  const stemSet = new Set(stemToks);
  const feats: string[] = [];
  for (const t of optToks) {
    feats.push(`o:${t}`);
    if (stemSet.has(t)) feats.push(`ov:${t}`);
  }
  const compact = opt.toLowerCase().replace(/[^a-z0-9]+/g, " ");
  for (let i = 0; i <= compact.length - 3 && i < 60; i++) {
    feats.push(`c3:${compact.slice(i, i + 3)}`);
  }
  const surf = surfaceFeatures(item);
  if (surf.longest.includes(letter)) feats.push("cue:longest");
  if (surf.middleValueKeys.includes(letter)) feats.push("cue:middle");
  if (surf.stemNumbersRepeated[letter]) feats.push("cue:numrepeat");
  feats.push(`pos:${letter}`);
  feats.push(`len:${Math.min(8, Math.floor((surf.optionLengths[letter] ?? 0) / 12))}`);
  return feats;
}

export function trainNgram(train: Item[]): NgramModel {
  const keyCount = new Map<string, number>();
  const distCount = new Map<string, number>();
  let keyTotal = 0;
  let distTotal = 0;
  const selected = train.filter((it) => it.responseType === "selected" && it.choices);
  for (const item of selected) {
    const letters = Object.keys(item.choices ?? {});
    for (const letter of letters) {
      const feats = optionFeatures(item, letter);
      const isKey = letter.toUpperCase() === item.key.toUpperCase();
      const bag = isKey ? keyCount : distCount;
      if (isKey) keyTotal += feats.length;
      else distTotal += feats.length;
      for (const f of feats) bag.set(f, (bag.get(f) ?? 0) + 1);
    }
  }
  return {
    keyCount,
    distCount,
    keyTotal: keyTotal || 1,
    distTotal: distTotal || 1,
    trainN: selected.length,
    trainIds: selected.map((it) => it.id),
  };
}

function logProb(count: number, total: number, vocab: number): number {
  return Math.log((count + 1) / (total + vocab));
}

function scoreOption(model: NgramModel, item: Item, letter: string): number {
  const feats = optionFeatures(item, letter);
  const vocab = new Set([...model.keyCount.keys(), ...model.distCount.keys()]).size + 1;
  let s = 0;
  for (const f of feats) {
    s +=
      logProb(model.keyCount.get(f) ?? 0, model.keyTotal, vocab) -
      logProb(model.distCount.get(f) ?? 0, model.distTotal, vocab);
  }
  return s;
}

export function applyNgram(model: NgramModel, item: Item): ProgramResult {
  const letters = Object.keys(item.choices ?? {}).sort();
  if (!letters.length) {
    return { answer: null, skipped: true, skipReason: "no choices", trace: [] };
  }
  let best = -Infinity;
  let winners: string[] = [];
  const scores: Record<string, number> = {};
  for (const letter of letters) {
    const s = scoreOption(model, item, letter);
    scores[letter] = s;
    if (s > best) {
      best = s;
      winners = [letter];
    } else if (s === best) winners.push(letter);
  }
  return {
    answer: winners[0]!,
    skipped: false,
    trace: [
      `fitted-ngram trainN=${model.trainN}`,
      `scores=${JSON.stringify(scores)}`,
      `pick ${winners[0]}`,
    ],
  };
}

/** Same features, weights from a seed, never the keys. Matched-complexity random program. */
export function applyRandomNgram(item: Item, seed: number): ProgramResult {
  const letters = Object.keys(item.choices ?? {}).sort();
  if (!letters.length) {
    return { answer: null, skipped: true, skipReason: "no choices", trace: ["random-ngram"] };
  }
  const rng = mulberry32(seed);
  const weight = new Map<string, number>();
  let best = -Infinity;
  let winners: string[] = [];
  const scores: Record<string, number> = {};
  for (const letter of letters) {
    let s = 0;
    for (const f of optionFeatures(item, letter)) {
      if (!weight.has(f)) weight.set(f, rng() * 2 - 1);
      s += weight.get(f)!;
    }
    scores[letter] = s;
    if (s > best) {
      best = s;
      winners = [letter];
    } else if (s === best) winners.push(letter);
  }
  return {
    answer: winners[0]!,
    skipped: false,
    trace: [`random-ngram-weights seed=${seed}`, `pick ${winners[0]}`],
  };
}

export function trainOverlap(train: Item[]): OverlapModel {
  const keyHits = new Map<string, number>();
  const distHits = new Map<string, number>();
  const selected = train.filter((it) => it.responseType === "selected" && it.choices);
  for (const item of selected) {
    const stem = new Set(tokenize(item.stem).filter((t) => t.length >= 3));
    for (const [letter, text] of Object.entries(item.choices ?? {})) {
      const opt = new Set(tokenize(text).filter((t) => t.length >= 3));
      const isKey = letter.toUpperCase() === item.key.toUpperCase();
      const bag = isKey ? keyHits : distHits;
      for (const t of stem) {
        if (opt.has(t)) bag.set(t, (bag.get(t) ?? 0) + 1);
      }
    }
  }
  const weight = new Map<string, number>();
  const toks = new Set([...keyHits.keys(), ...distHits.keys()]);
  for (const t of toks) {
    const k = (keyHits.get(t) ?? 0) + 1;
    const d = (distHits.get(t) ?? 0) + 1;
    weight.set(t, Math.log(k / d));
  }
  return { weight, trainN: selected.length, trainIds: selected.map((it) => it.id) };
}

export function applyOverlap(model: OverlapModel, item: Item): ProgramResult {
  const letters = Object.keys(item.choices ?? {}).sort();
  if (!letters.length) {
    return { answer: null, skipped: true, skipReason: "no choices", trace: [] };
  }
  const stem = tokenize(item.stem).filter((t) => t.length >= 3);
  const scores: Record<string, number> = {};
  let best = -Infinity;
  let winners: string[] = [];
  for (const letter of letters) {
    const opt = new Set(tokenize(optionText(item, letter)).filter((t) => t.length >= 3));
    let s = 0;
    for (const t of stem) {
      if (opt.has(t)) s += model.weight.get(t) ?? 0;
    }
    scores[letter] = s;
    if (s > best) {
      best = s;
      winners = [letter];
    } else if (s === best) winners.push(letter);
  }
  if (best <= 0) {
    return {
      answer: null,
      skipped: true,
      skipReason: "no positive weighted overlap",
      trace: [`fitted-overlap trainN=${model.trainN}`, `scores=${JSON.stringify(scores)}`],
    };
  }
  return {
    answer: winners[0]!,
    skipped: false,
    trace: [`fitted-overlap trainN=${model.trainN}`, `scores=${JSON.stringify(scores)}`, `pick ${winners[0]}`],
  };
}

function emit(value: number, item: Item, trace: string[]): ProgramResult {
  if (!Number.isFinite(value)) {
    return { answer: null, skipped: true, skipReason: "non-finite", trace };
  }
  if (item.choices) {
    const hit = matchNumericToChoice(value, item.choices);
    if (hit) return { answer: hit, skipped: false, trace: [...trace, `matched ${hit}`] };
    for (const [k, text] of Object.entries(item.choices)) {
      if (answersMatch(text, formatNumber(value))) {
        return { answer: k, skipped: false, trace: [...trace, `matched text ${k}`] };
      }
    }
    return { answer: null, skipped: true, skipReason: "no matching choice", trace };
  }
  return { answer: formatNumber(value), skipped: false, trace };
}

const FORMULAS: Record<FormulaId, (nums: number[], stem: string) => number | null> = {
  "div-a-b": (n) => (n.length >= 2 && n[1] !== 0 ? n[0]! / n[1]! : null),
  "div-b-a": (n) => (n.length >= 2 && n[0] !== 0 ? n[1]! / n[0]! : null),
  "mul-ab": (n) => (n.length >= 2 ? n[0]! * n[1]! : null),
  "add-ab": (n) => (n.length >= 2 ? n[0]! + n[1]! : null),
  "sub-abs": (n) => (n.length >= 2 ? Math.abs(n[0]! - n[1]!) : null),
  "mul-abc": (n) => (n.length >= 3 ? n[0]! * n[1]! * n[2]! : null),
  "percent-of": (n, stem) => {
    const pm = stem.match(/(\d+(?:\.\d+)?)\s*%/);
    if (!pm) return null;
    const p = Number(pm[1]);
    const other = n.find((x) => x !== p);
    return other === undefined ? null : (p / 100) * other;
  },
  "percent-down": (n, stem) => {
    const pm = stem.match(/(\d+(?:\.\d+)?)\s*%/);
    if (!pm) return null;
    const p = Number(pm[1]);
    const other = n.find((x) => x !== p);
    return other === undefined ? null : other * (1 - p / 100);
  },
  "percent-up": (n, stem) => {
    const pm = stem.match(/(\d+(?:\.\d+)?)\s*%/);
    if (!pm) return null;
    const p = Number(pm[1]);
    const other = n.find((x) => x !== p);
    return other === undefined ? null : other * (1 + p / 100);
  },
  mean: (n) => (n.length >= 2 ? n.reduce((a, b) => a + b, 0) / n.length : null),
  square: (n) => (n.length >= 1 ? n[0]! * n[0]! : null),
};

export function applyFormula(formulaId: FormulaId, item: Item): ProgramResult {
  const nums = extractNumbers(item.stem);
  const value = FORMULAS[formulaId](nums, item.stem);
  if (value === null) {
    return { answer: null, skipped: true, skipReason: `formula ${formulaId} abstained`, trace: [] };
  }
  return emit(value, item, [`fitted-formula ${formulaId}`, `nums=${nums.join(",")}`]);
}

export function trainFormula(train: Item[]): FormulaModel | null {
  const numeric = train.filter((it) => it.responseType === "numeric" || (it.choices && extractNumbers(it.stem).length >= 2));
  const usable = numeric.filter((it) => it.responseType === "numeric");
  if (!usable.length) return null;
  const catalogHits: Record<string, number> = {};
  let best: FormulaId = "div-a-b";
  let bestHits = -1;
  for (const id of Object.keys(FORMULAS) as FormulaId[]) {
    let hits = 0;
    for (const item of usable) {
      const r = applyFormula(id, item);
      if (!r.skipped && r.answer && answersMatch(item.key, r.answer)) hits += 1;
    }
    catalogHits[id] = hits;
    if (hits > bestHits) {
      bestHits = hits;
      best = id;
    }
  }
  return {
    formulaId: best,
    trainHits: bestHits,
    trainN: usable.length,
    trainIds: usable.map((it) => it.id),
    catalogHits,
  };
}

export function isStateItem(item: Item): boolean {
  return STATE_CORPORA.has(item.corpus);
}

export function isTimssItem(item: Item): boolean {
  return TIMSS_CORPORA.has(item.corpus);
}

export function isTimssHeadline(item: Item): boolean {
  return isTimssItem(item) && TIMSS_HEADLINE_CLAIMS.has(item.claim);
}
