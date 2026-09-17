import { extractNumberTokens, parseLeadingNumber, tokenize } from "./channels.ts";
import type { Item } from "./types.ts";

export const FEATURE_NAMES = [
  "longest",
  "positionC",
  "overlap",
  "numRepeat",
  "noAbsolute",
  "numericMin",
  "numericMed",
  "numericMax",
  "specificity",
  "grammarAgree",
  "distinctive",
] as const;

export type FeatureName = (typeof FEATURE_NAMES)[number];

const ABSOLUTE = /\b(always|never|all|none|only|every|impossible|certainly)\b/i;
const ENGLISH = new Set(
  "the of and to a in is it you that he was for on are with as his they be at one have this from or had by hot word but what some we can out other were all there when up use your how said each she which their time if will way about many then them write would like so these her long make thing see him two more has look day could go come did number sound no most people my over know water than call first who may down side been now find any new work part take get place made live where after back little only round year came show every good me give our under name very through just form sentence great think say help low line differ turn cause much mean before move right boy old too same tell does set three want air well also play small end put home read hand port large spell add even land here must high such follow act why ask men change went light kind off need house picture try us again animal point mother world near build self earth father head stand own page should country found answer school grow study still learn plant cover food sun four between state keep eye never last let thought city tree cross farm hard start might story saw far sea draw left late run don't while press close night real life few north open seem together next white children begin got walk example ease paper group always music those both mark often letter until book last room sea".split(
    /\s+/,
  ),
);

export type FeatureMatrix = Record<string, Record<FeatureName, number>>;

export function featureMatrix(item: Item): FeatureMatrix {
  const choices = item.choices ?? {};
  const letters = Object.keys(choices).sort();
  const stemToks = new Set(tokenize(item.stem).filter((t) => t.length >= 4));
  const stemNums = extractNumberTokens(item.stem);
  const lengths = Object.fromEntries(letters.map((k) => [k, (choices[k] ?? "").length]));
  const maxLen = Math.max(0, ...Object.values(lengths));
  const nums = letters.map((k) => ({ k, v: parseLeadingNumber(choices[k] ?? "") }));
  const parsed = nums.filter((x): x is { k: string; v: number } => x.v !== null).sort((a, b) => a.v - b.v);
  const minV = parsed[0]?.v;
  const maxV = parsed[parsed.length - 1]?.v;
  const medV = parsed.length ? parsed[Math.floor((parsed.length - 1) / 2)]!.v : undefined;
  const optToks: Record<string, Set<string>> = {};
  for (const k of letters) optToks[k] = new Set(tokenize(choices[k] ?? ""));
  const stem = item.stem.trim();
  const wantsAn = /\ban\s*$/i.test(stem) || /\ban\s+_+\s*$/i.test(stem);
  const wantsA = /\ba\s*$/i.test(stem) || /\ba\s+_+\s*$/i.test(stem);

  const matrix: FeatureMatrix = {};
  for (const k of letters) {
    const text = choices[k] ?? "";
    const toks = [...(optToks[k] ?? [])];
    const overlap = toks.filter((t) => stemToks.has(t)).length;
    const first = text.trim().match(/^[A-Za-z]/)?.[0] ?? "";
    const vowel = /^[aeiou]/i.test(first);
    let grammar = 0;
    if (wantsAn) grammar = vowel ? 1 : 0;
    else if (wantsA) grammar = first && !vowel ? 1 : 0;
    const englishHits = toks.filter((t) => ENGLISH.has(t)).length;
    let sim = 0;
    let others = 0;
    for (const j of letters) {
      if (j === k) continue;
      const a = optToks[k] ?? new Set();
      const b = optToks[j] ?? new Set();
      const inter = [...a].filter((t) => b.has(t)).length;
      const union = new Set([...a, ...b]).size || 1;
      sim += inter / union;
      others += 1;
    }
    const meanSim = others ? sim / others : 0;
    matrix[k] = {
      longest: lengths[k] === maxLen && letters.filter((x) => lengths[x] === maxLen).length === 1 ? 1 : 0,
      positionC: k === "C" ? 1 : 0,
      overlap,
      numRepeat: stemNums.some((n) => text.includes(n)) ? 1 : 0,
      noAbsolute: ABSOLUTE.test(text) ? 0 : 1,
      numericMin: parsed.length >= 2 && nums.find((x) => x.k === k)?.v === minV && parsed.filter((x) => x.v === minV).length === 1 ? 1 : 0,
      numericMed: parsed.length >= 3 && nums.find((x) => x.k === k)?.v === medV && parsed.filter((x) => x.v === medV).length === 1 ? 1 : 0,
      numericMax: parsed.length >= 2 && nums.find((x) => x.k === k)?.v === maxV && parsed.filter((x) => x.v === maxV).length === 1 ? 1 : 0,
      specificity: englishHits + toks.length * 0.1,
      grammarAgree: grammar,
      distinctive: 1 - meanSim,
    };
  }
  return matrix;
}

export function uniqueMax(scores: Record<string, number>, opts?: { requirePositive?: boolean; allowTieFirst?: boolean }): string | null {
  const letters = Object.keys(scores).sort();
  if (!letters.length) return null;
  let best = -Infinity;
  let winners: string[] = [];
  for (const k of letters) {
    const s = scores[k] ?? -Infinity;
    if (s > best) {
      best = s;
      winners = [k];
    } else if (s === best) winners.push(k);
  }
  if (opts?.allowTieFirst && winners.length) {
    if (opts.requirePositive !== false && best <= 0 && !opts.allowTieFirst) return null;
    return winners[0]!;
  }
  if (winners.length !== 1) return null;
  if (opts?.requirePositive !== false && best <= 0) return null;
  return winners[0]!;
}
