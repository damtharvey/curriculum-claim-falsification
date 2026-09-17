import type { AprioriRule, Item, ItemView } from "../types.ts";
import {
  answersMatch,
  formatNumber,
  matchNumericToChoice,
  parseFraction,
  parseLeadingNumber,
} from "../channels.ts";

export interface ProgramResult {
  answer: string | null;
  skipped: boolean;
  skipReason?: string;
  trace: string[];
}

export type ProgramFn = (view: ItemView, item: Item, rule: AprioriRule) => ProgramResult;

function pickFirst(keys: string[], trace: string[]): ProgramResult {
  if (!keys.length) {
    return { answer: null, skipped: true, skipReason: "no candidate", trace };
  }
  return { answer: keys[0]!, skipped: false, trace: [...trace, `pick ${keys[0]}`] };
}

export const programs: Record<string, ProgramFn> = {
  "longest-option"(view) {
    const longest = view.surface?.longest ?? [];
    return pickFirst(longest, [`longest lengths=${JSON.stringify(view.surface?.optionLengths)}`]);
  },
  "stem-option-overlap"(view) {
    const scores = view.surface?.stemOverlap ?? {};
    const keys = Object.keys(scores);
    if (!keys.length) {
      return { answer: null, skipped: true, skipReason: "no choices", trace: [] };
    }
    let best = -1;
    const winners: string[] = [];
    for (const k of keys.sort()) {
      const s = scores[k] ?? 0;
      if (s > best) {
        best = s;
        winners.length = 0;
        winners.push(k);
      } else if (s === best) winners.push(k);
    }
    if (best <= 0) {
      return {
        answer: null,
        skipped: true,
        skipReason: "zero overlap",
        trace: [`overlap=${JSON.stringify(scores)}`],
      };
    }
    return pickFirst(winners, [`overlap=${JSON.stringify(scores)}`]);
  },
  "option-repeating-stem-numbers"(view) {
    const flags = view.surface?.stemNumbersRepeated ?? {};
    const hits = Object.keys(flags)
      .sort()
      .filter((k) => flags[k]);
    if (!hits.length) {
      return { answer: null, skipped: true, skipReason: "no stem number repeated", trace: [] };
    }
    return pickFirst(hits, [`repeats=${hits.join(",")}`]);
  },
  "avoid-absolute-terms"(view) {
    const flags = view.surface?.absoluteTerms ?? {};
    const keys = Object.keys(flags).sort();
    const without = keys.filter((k) => !flags[k]);
    const withAbs = keys.filter((k) => flags[k]);
    if (withAbs.length === 0 || without.length !== 1) {
      return {
        answer: null,
        skipped: true,
        skipReason: "rule does not uniquely apply",
        trace: [`absolute=${JSON.stringify(flags)}`],
      };
    }
    return pickFirst(without, [`avoid absolute; keep ${without[0]}`]);
  },
  "middle-value-option"(view) {
    const mids = view.surface?.middleValueKeys ?? [];
    if (!mids.length) {
      return { answer: null, skipped: true, skipReason: "fewer than 3 numeric options", trace: [] };
    }
    return pickFirst(mids, [`numericValues=${JSON.stringify(view.surface?.numericValues)}`]);
  },
  "position-c"(view) {
    const keys = Object.keys(view.choices ?? {}).sort();
    if (keys.includes("C")) return { answer: "C", skipped: false, trace: ["pick C"] };
    if (!keys.length) return { answer: null, skipped: true, skipReason: "no choices", trace: [] };
    const mid = keys[Math.floor((keys.length - 1) / 2)]!;
    return { answer: mid, skipped: false, trace: [`no C; pick middle position ${mid}`] };
  },
  "invert-and-multiply"(view, item) {
    const stem = view.stem ?? "";
    const fracs = [...stem.matchAll(/(-?\d+)\s*\/\s*(-?\d+)/g)];
    if (fracs.length < 2) {
      return { answer: null, skipped: true, skipReason: "need two fractions", trace: [stem] };
    }
    const a = Number(fracs[0]![1]);
    const b = Number(fracs[0]![2]);
    const c = Number(fracs[1]![1]);
    const d = Number(fracs[1]![2]);
    if (b === 0 || c === 0) {
      return { answer: null, skipped: true, skipReason: "zero denominator", trace: [] };
    }
    const value = (a / b) * (d / c);
    return emitValue(value, item, [`invert-and-multiply (${a}/${b})*(${d}/${c})=${value}`]);
  },
  "coefficient-adjacent-to-x"(view, item) {
    const stem = view.stem ?? "";
    const m = stem.match(/(-?\d+(?:\.\d+)?)\s*[·*]?\s*[xX]\b/);
    if (!m) {
      return { answer: null, skipped: true, skipReason: "no coefficient adjacent to x", trace: [stem] };
    }
    const value = Number(m[1]);
    return emitValue(value, item, [`coefficient ${value} adjacent to x`]);
  },
  "percent-of"(view, item) {
    const stem = view.stem ?? "";
    const pm = stem.match(/(\d+(?:\.\d+)?)\s*%/);
    if (!pm) return { answer: null, skipped: true, skipReason: "no percent token", trace: [] };
    const p = Number(pm[1]);
    const nums = (view.numbers ?? []).filter((n) => n !== p);
    if (!nums.length) return { answer: null, skipped: true, skipReason: "no other number", trace: [] };
    const n = nums[0]!;
    const value = (p / 100) * n;
    return emitValue(value, item, [`percent-of ${p}% of ${n} = ${value}`]);
  },
  "percent-change"(view, item) {
    const stem = (view.stem ?? "").toLowerCase();
    const pm = stem.match(/(\d+(?:\.\d+)?)\s*%/);
    if (!pm) return { answer: null, skipped: true, skipReason: "no percent token", trace: [] };
    const p = Number(pm[1]);
    const nums = (view.numbers ?? []).filter((n) => n !== p);
    if (!nums.length) return { answer: null, skipped: true, skipReason: "no other number", trace: [] };
    const n = nums[0]!;
    const down = /\b(decrease|markdown|discount|less|off)\b/.test(stem);
    const up = /\b(increase|markup|tax|tip|interest|more|raise)\b/.test(stem);
    if (!down && !up) {
      return { answer: null, skipped: true, skipReason: "no change polarity word", trace: [] };
    }
    const value = down ? n * (1 - p / 100) : n * (1 + p / 100);
    return emitValue(value, item, [`percent-change ${down ? "down" : "up"} ${n} ${p}% = ${value}`]);
  },
  "unit-rate"(view, item) {
    const nums = (view.numbers ?? []).filter((n) => n !== 0);
    if (nums.length < 2) {
      return { answer: null, skipped: true, skipReason: "need two numbers", trace: [] };
    }
    const a = nums[0]!;
    const b = nums[1]!;
    const candidates = [a / b, b / a];
    if (item.choices) {
      for (const v of candidates) {
        const hit = matchNumericToChoice(v, item.choices);
        if (hit) {
          return {
            answer: hit,
            skipped: false,
            trace: [`unit-rate candidates ${candidates.join(", ")}; matched ${hit}`],
          };
        }
      }
    }
    return emitValue(candidates[0]!, item, [`unit-rate ${a}/${b}`]);
  },
  "y-equals-kx"(view, item) {
    const nums = view.numbers ?? [];
    if (nums.length < 2) {
      return { answer: null, skipped: true, skipReason: "need two numbers", trace: [] };
    }
    const x = nums[0]!;
    const y = nums[1]!;
    if (x === 0) return { answer: null, skipped: true, skipReason: "x=0", trace: [] };
    const k = y / x;
    if (nums.length >= 3) {
      const value = k * nums[2]!;
      return emitValue(value, item, [`y=kx k=${k} apply to ${nums[2]}=${value}`]);
    }
    return emitValue(k, item, [`y=kx k=${k} from first pair`]);
  },
  "area-lw"(view, item) {
    const stem = (view.stem ?? "").toLowerCase();
    if (!/\b(area|rectangle|square|parallelogram)\b/.test(stem)) {
      return { answer: null, skipped: true, skipReason: "no area cue", trace: [] };
    }
    const nums = view.numbers ?? [];
    if (/\bsquare\b/.test(stem) && nums.length >= 1) {
      return emitValue(nums[0]! * nums[0]!, item, [`square area ${nums[0]}^2`]);
    }
    if (nums.length < 2) return { answer: null, skipped: true, skipReason: "need two numbers", trace: [] };
    return emitValue(nums[0]! * nums[1]!, item, [`area ${nums[0]}*${nums[1]}`]);
  },
  "volume-lwh"(view, item) {
    const stem = (view.stem ?? "").toLowerCase();
    if (!/\b(volume|cubic|box|prism)\b/.test(stem)) {
      return { answer: null, skipped: true, skipReason: "no volume cue", trace: [] };
    }
    const nums = view.numbers ?? [];
    if (nums.length < 3) return { answer: null, skipped: true, skipReason: "need three numbers", trace: [] };
    return emitValue(nums[0]! * nums[1]! * nums[2]!, item, [`volume ${nums[0]}*${nums[1]}*${nums[2]}`]);
  },
  "mean-of-listed-numbers"(view, item) {
    const stem = (view.stem ?? "").toLowerCase();
    if (!/\b(mean|average)\b/.test(stem)) {
      return { answer: null, skipped: true, skipReason: "no mean cue", trace: [] };
    }
    const nums = (view.numbers ?? []).filter((n) => n <= 1000);
    if (nums.length < 2) return { answer: null, skipped: true, skipReason: "need data", trace: [] };
    const value = nums.reduce((a, b) => a + b, 0) / nums.length;
    return emitValue(value, item, [`mean of ${nums.join(",")} = ${value}`]);
  },
};

function emitValue(value: number, item: Item, trace: string[]): ProgramResult {
  if (!Number.isFinite(value)) {
    return { answer: null, skipped: true, skipReason: "non-finite", trace };
  }
  if (item.choices) {
    const hit = matchNumericToChoice(value, item.choices);
    if (hit) return { answer: hit, skipped: false, trace: [...trace, `matched choice ${hit}`] };
    // also match letter keys if the computed value equals a letter's parsed number already handled
    for (const [k, text] of Object.entries(item.choices)) {
      if (answersMatch(text, formatNumber(value))) {
        return { answer: k, skipped: false, trace: [...trace, `matched text of ${k}`] };
      }
    }
    return { answer: null, skipped: true, skipReason: "no matching choice", trace };
  }
  return { answer: formatNumber(value), skipped: false, trace };
}

export function stemNgramClassifier(view: ItemView): ProgramResult {
  // Rules-only on the stem: same as stem-option-overlap. A model on the stem is forbidden.
  const overlap = programs["stem-option-overlap"];
  return overlap(view, { id: view.itemId } as Item, {
    id: "stem-ngram-classifier",
  } as AprioriRule);
}

export function randomChoice(item: Item, rng: () => number): ProgramResult {
  const keys = Object.keys(item.choices ?? {}).sort();
  if (!keys.length) return { answer: null, skipped: true, skipReason: "no choices", trace: ["random"] };
  const idx = Math.floor(rng() * keys.length);
  return { answer: keys[idx]!, skipped: false, trace: [`random index ${idx}`] };
}

export function chanceRate(item: Item): number | null {
  if (item.responseType === "selected") {
    const n = Object.keys(item.choices ?? {}).length;
    return n > 0 ? 1 / n : null;
  }
  return null;
}

export { parseLeadingNumber, parseFraction };
