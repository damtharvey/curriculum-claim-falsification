/**
 * Channel view constructors and surface-feature extraction.
 * Ported from runner/src/channels.ts — key is never on the view.
 */

import type { Item, ItemView, SurfaceFeatures } from "./types.js";

const ABSOLUTE = /\b(always|never|all|none|only|every|impossible|certainly)\b/i;

export function tokenize(text: string): string[] {
  return text
    .toLowerCase()
    .split(/[^a-z0-9]+/g)
    .filter((t) => t.length >= 2);
}

export function extractNumberTokens(text: string): string[] {
  return text.match(/-?\d+(?:[.,]\d+)?/g) ?? [];
}

export function extractNumbers(text: string): number[] {
  const out: number[] = [];
  for (const tok of extractNumberTokens(text)) {
    const n = Number(tok.replace(/,/g, ""));
    if (Number.isFinite(n)) out.push(n);
  }
  return out;
}

export function parseLeadingNumber(text: string): number | null {
  const m = text.trim().match(/^[^\d-]*(-?\d+(?:\.\d+)?)/);
  if (!m) return null;
  const n = Number(m[1]);
  return Number.isFinite(n) ? n : null;
}

export function choiceKeys(item: Item): string[] {
  return Object.keys(item.choices ?? {}).sort();
}

export function surfaceFeatures(item: Item): SurfaceFeatures {
  const choices = item.choices ?? {};
  const keys = choiceKeys(item);
  const optionLengths: Record<string, number> = {};
  const absoluteTerms: Record<string, boolean> = {};
  const stemOverlap: Record<string, number> = {};
  const stemNumbersRepeated: Record<string, boolean> = {};
  const numericValues: Record<string, number | null> = {};
  const stemTokens = new Set(tokenize(item.stem).filter((t) => t.length >= 4));
  const stemNums = extractNumberTokens(item.stem);
  let maxLen = -1;
  const longest: string[] = [];
  for (const k of keys) {
    const text = choices[k] ?? "";
    optionLengths[k] = text.length;
    if (text.length > maxLen) {
      maxLen = text.length;
      longest.length = 0;
      longest.push(k);
    } else if (text.length === maxLen) {
      longest.push(k);
    }
    absoluteTerms[k] = ABSOLUTE.test(text);
    const optTokens = tokenize(text);
    stemOverlap[k] = optTokens.filter((t) => stemTokens.has(t)).length;
    stemNumbersRepeated[k] = stemNums.some((n) => text.includes(n));
    numericValues[k] = parseLeadingNumber(text);
  }
  const parsed = keys
    .map((k) => ({ k, v: numericValues[k] }))
    .filter((x): x is { k: string; v: number } => x.v !== null)
    .sort((a, b) => a.v - b.v);
  let middleValueKeys: string[] = [];
  if (parsed.length >= 3) {
    const mid = parsed[Math.floor((parsed.length - 1) / 2)]!.v;
    middleValueKeys = parsed.filter((x) => x.v === mid).map((x) => x.k);
  }
  return {
    optionLengths,
    longest,
    absoluteTerms,
    stemOverlap,
    stemNumbersRepeated,
    numericValues,
    middleValueKeys,
    positions: keys,
  };
}

export function itemCuesView(item: Item, programId: string): ItemView {
  return {
    itemId: item.id,
    channel: "item-cues",
    programId,
    choices: item.choices,
    surface: surfaceFeatures(item),
  };
}

export function choicesOnlyView(item: Item, programId: string): ItemView {
  return {
    itemId: item.id,
    channel: "partial-input",
    programId,
    choices: item.choices,
    surface: surfaceFeatures({ ...item, stem: "" }),
  };
}

export function stemNgramView(item: Item, programId: string): ItemView {
  return {
    itemId: item.id,
    channel: "partial-input",
    programId,
    stem: item.stem,
    choices: item.choices,
    numbers: extractNumbers(item.stem),
    numberTokens: extractNumberTokens(item.stem),
    surface: surfaceFeatures(item),
  };
}

export function unboundView(item: Item, programId: string): ItemView {
  return {
    itemId: item.id,
    channel: "unbound-exec",
    programId,
    stem: item.stem,
    choices: item.choices,
    numbers: extractNumbers(item.stem),
    numberTokens: extractNumberTokens(item.stem),
  };
}

export function answersMatch(expected: string, got: string): boolean {
  const a = expected.trim();
  const b = got.trim();
  if (a.toLowerCase() === b.toLowerCase()) return true;
  const na = Number(a.replace(/,/g, ""));
  const nb = Number(b.replace(/,/g, ""));
  if (Number.isFinite(na) && Number.isFinite(nb)) {
    const scale = Math.max(1, Math.abs(na));
    return Math.abs(na - nb) <= 1e-6 * scale || Math.abs(na - nb) < 0.005;
  }
  const fa = parseFraction(a);
  const fb = parseFraction(b);
  if (fa !== null && fb !== null) return Math.abs(fa - fb) < 1e-6;
  return false;
}

export function parseFraction(text: string): number | null {
  const m = text.trim().match(/^(-?\d+)\s*\/\s*(-?\d+)$/);
  if (!m) return null;
  const d = Number(m[2]);
  if (d === 0) return null;
  return Number(m[1]) / d;
}

export function matchNumericToChoice(
  value: number,
  choices: Record<string, string> | undefined,
): string | null {
  if (!choices) return null;
  for (const [k, text] of Object.entries(choices)) {
    const n = parseLeadingNumber(text);
    const f = parseFraction(text);
    const cand = n ?? f;
    if (cand === null) continue;
    const scale = Math.max(1, Math.abs(cand));
    if (Math.abs(cand - value) <= 1e-4 * scale || Math.abs(cand - value) < 0.01) {
      return k;
    }
  }
  return null;
}

export function formatNumber(n: number): string {
  if (Number.isInteger(n)) return String(n);
  const s = n.toPrecision(8);
  return String(Number(s));
}

export function viewFor(rule: { id: string; channel: string }, item: Item): ItemView {
  if (rule.channel === "item-cues") return itemCuesView(item, rule.id);
  if (rule.channel === "unbound-exec") return unboundView(item, rule.id);
  if (rule.id === "stem-option-overlap" || rule.id === "option-repeating-stem-numbers") {
    return stemNgramView(item, rule.id);
  }
  if (rule.channel === "partial-input") return choicesOnlyView(item, rule.id);
  return unboundView(item, rule.id);
}
