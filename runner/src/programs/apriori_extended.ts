import type { Item } from "../types.ts";
import { parseLeadingNumber, tokenize } from "../channels.ts";
import { uniqueMax } from "../features.ts";
import type { ProgramFn, ProgramResult } from "./apriori.ts";

const HEDGE =
  /\b(sometimes|often|usually|generally|typically|seldom|rarely|occasionally|frequently|ordinarily|perhaps|possibly|probably|maybe|approximately|nearly|roughly|about|around|relatively|somewhat|mostly|likely|tends|tend|may|might|could|few|many|some|most)\b/gi;

function pick(answer: string | null, trace: string[]): ProgramResult {
  if (!answer) return { answer: null, skipped: true, skipReason: "rule does not uniquely apply", trace };
  return { answer, skipped: false, trace: [...trace, `pick ${answer}`] };
}

export const extendedPrograms: Record<string, ProgramFn> = {
  "most-qualified-hedged-option"(view) {
    const choices = view.choices ?? {};
    const scores: Record<string, number> = {};
    for (const k of Object.keys(choices).sort()) {
      const hits = (choices[k] ?? "").match(HEDGE) ?? [];
      scores[k] = hits.length;
    }
    return pick(uniqueMax(scores), [`hedge=${JSON.stringify(scores)}`]);
  },
  "convergence-option"(view, item) {
    const choices = item.choices ?? {};
    const keys = Object.keys(choices).sort();
    const elements: Record<string, Set<string>> = {};
    for (const k of keys) {
      const text = choices[k] ?? "";
      const toks = new Set(tokenize(text));
      const n = parseLeadingNumber(text);
      if (n !== null) {
        toks.add(`num:${n}`);
        toks.add(`digits:${text.trim().replace(/[^\d-]/g, "")}`);
      }
      elements[k] = toks;
    }
    const scores: Record<string, number> = {};
    for (const k of keys) {
      let s = 0;
      for (const j of keys) {
        if (j === k) continue;
        for (const t of elements[k] ?? []) if (elements[j]?.has(t)) s += 1;
      }
      scores[k] = s;
    }
    return pick(uniqueMax(scores), [`convergence=${JSON.stringify(scores)}`]);
  },
  "grammatical-fit-option"(view, item) {
    const stem = item.stem.trim();
    const wantsAn = /\ban\s*$/i.test(stem) || /\ban\s+_+\s*$/i.test(stem);
    const wantsA = /\ba\s*$/i.test(stem) || /\ba\s+_+\s*$/i.test(stem);
    if (!wantsAn && !wantsA) {
      return { answer: null, skipped: true, skipReason: "stem has no a/an cue", trace: [] };
    }
    const fit: string[] = [];
    const unfit: string[] = [];
    for (const k of Object.keys(item.choices ?? {}).sort()) {
      const text = (item.choices?.[k] ?? "").trim();
      const first = text.match(/^[A-Za-z]/)?.[0] ?? "";
      const vowel = /^[aeiou]/i.test(first);
      const agrees = (wantsAn && vowel) || (wantsA && Boolean(first) && !vowel);
      if (agrees) fit.push(k);
      else unfit.push(k);
    }
    if (fit.length === 1 && unfit.length) return pick(fit[0]!, [`fit=${fit.join(",")}`]);
    return { answer: null, skipped: true, skipReason: "not a unique grammatical fit", trace: [`fit=${fit.join(",")}`] };
  },
  "mean-of-other-options"(view) {
    const values = view.surface?.numericValues ?? {};
    const parsed = Object.keys(values)
      .sort()
      .map((k) => ({ k, v: values[k] }))
      .filter((x): x is { k: string; v: number } => x.v !== null);
    if (parsed.length < 3) {
      return { answer: null, skipped: true, skipReason: "fewer than 3 numeric options", trace: [] };
    }
    const total = parsed.reduce((a, b) => a + b.v, 0);
    const dist: Record<string, number> = {};
    for (const row of parsed) dist[row.k] = Math.abs(row.v - (total - row.v) / (parsed.length - 1));
    let best = Infinity;
    const winners: string[] = [];
    for (const k of Object.keys(dist).sort()) {
      const d = dist[k]!;
      if (d < best) {
        best = d;
        winners.length = 0;
        winners.push(k);
      } else if (d === best) winners.push(k);
    }
    if (winners.length !== 1) {
      return { answer: null, skipped: true, skipReason: "tie at mean of others", trace: [`dist=${JSON.stringify(dist)}`] };
    }
    return pick(winners[0]!, [`dist=${JSON.stringify(dist)}`]);
  },
};
