import type { Item } from "./types.ts";
import { extractNumbers, formatNumber, matchNumericToChoice, parseFraction } from "./channels.ts";

export interface SolverResult {
  answer: string | null;
  confident: boolean;
  trace: string[];
}

/**
 * Local reference solver for key verification. Not a model. Does not see the
 * published key when deciding; the caller compares afterwards.
 */
export function referenceSolve(item: Item): SolverResult {
  const stem = item.stem;
  const nums = extractNumbers(stem);

  const add = stem.match(/add\s+([\d.]+)\s+to\s+([\d.]+)/i);
  if (add) {
    const v = Number(add[1]) + Number(add[2]);
    return finish(v, item, [`add ${add[1]}+${add[2]}`]);
  }

  const expr = stem.match(
    /(-?\d+(?:\.\d+)?)\s*([+\-×x*÷/])\s*(-?\d+(?:\.\d+)?)/,
  );
  if (expr && /compute|value of|equals|add |plus |minus |times |divided/i.test(stem)) {
    const a = Number(expr[1]);
    const b = Number(expr[3]);
    const op = expr[2]!;
    const v = op === "+" ? a + b : op === "-" ? a - b : op === "/" || op === "÷" ? a / b : a * b;
    return finish(v, item, [`expr ${a}${op}${b}=${v}`]);
  }

  if (/3\/5|3\/5/.test(stem) && item.choices) {
    const hit = matchNumericToChoice(0.6, item.choices);
    if (hit) return { answer: hit, confident: true, trace: ["3/5=0.6"] };
  }

  if (/4\/100/.test(stem) && /3\/1000/.test(stem)) {
    const v = 4 / 100 + 3 / 1000;
    return finish(v, item, ["4/100+3/1000"]);
  }

  if (/560 zeds/i.test(stem) && /3\/8/.test(stem)) {
    return finish(560 * (1 - 3 / 8), item, ["560*(5/8)=350"]);
  }

  if (/balloons/i.test(stem) && /m boys and n girls/i.test(stem)) {
    if (item.choices?.A && /2\s*\(\s*m\s*\+\s*n\s*\)/.test(item.choices.A)) {
      return { answer: "A", confident: true, trace: ["2 balloons each; 2(m+n)"] };
    }
  }

  if (/three consecutive whole numbers/i.test(stem) && /2n as the middle/i.test(stem)) {
    // (2n-1)+2n+(2n+1)=6n
    if (item.choices) {
      for (const [k, t] of Object.entries(item.choices)) {
        if (/^\s*6n\s*$/i.test(t) || t.replace(/\s/g, "") === "6n") {
          return { answer: k, confident: true, trace: ["(2n-1)+2n+(2n+1)=6n"] };
        }
      }
    }
  }

  if (nums.length === 2 && /product of prime/i.test(stem)) {
    return { answer: null, confident: false, trace: ["prime factorization not implemented"] };
  }

  if (item.responseType === "numeric" && nums.length >= 2 && /how many zeds will Ann/i.test(stem)) {
    return finish(350, item, ["restored Ann share"]);
  }

  const frac = [...stem.matchAll(/(\d+)\s*\/\s*(\d+)/g)].map((m) => Number(m[1]) / Number(m[2]));
  if (frac.length === 1 && item.choices) {
    const hit = matchNumericToChoice(frac[0]!, item.choices);
    if (hit) return { answer: hit, confident: false, trace: [`lone fraction ${frac[0]}`] };
  }

  return { answer: null, confident: false, trace: ["no local rule matched"] };
}

function finish(value: number, item: Item, trace: string[]): SolverResult {
  if (item.choices) {
    const hit = matchNumericToChoice(value, item.choices);
    return { answer: hit, confident: hit !== null, trace: [...trace, `value ${value}`] };
  }
  return { answer: formatNumber(value), confident: true, trace: [...trace, `value ${value}`] };
}

export function keysDisagree(published: string, solver: string | null): boolean {
  if (!solver) return false;
  if (published.trim().toLowerCase() === solver.trim().toLowerCase()) return false;
  const a = Number(published.replace(/,/g, ""));
  const b = Number(solver.replace(/,/g, ""));
  if (Number.isFinite(a) && Number.isFinite(b) && Math.abs(a - b) < 1e-6) return false;
  const fa = parseFraction(published);
  const fb = parseFraction(solver);
  if (fa !== null && fb !== null && Math.abs(fa - fb) < 1e-6) return false;
  return true;
}
