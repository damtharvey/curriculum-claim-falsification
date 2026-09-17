/**
 * Synthetic MC items from the Haladyna / Downing / Rodriguez item-writing-flaw taxonomy.
 * Generated programmatically. Not real exam items.
 */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { mulberry32 } from "./stats.ts";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const LETTERS = ["A", "B", "C", "D"] as const;

export const FLAW_TYPES = [
  "longest",
  "stem-repeat",
  "absolute",
  "position",
  "grammar",
  "implausible",
] as const;

export type FlawType = (typeof FLAW_TYPES)[number];

const LICENSE =
  "Synthetic method-control items generated from the Haladyna, Downing, and Rodriguez item-writing-flaw taxonomy. Not a public exam. For searcher validation only.";
const SOURCE = "https://doi.org/10.1177/0146621602026002002";

function itemBase(id: string, claim: string, stem: string, choices: Record<string, string>, key: string, clusterId: string) {
  return {
    id,
    corpus: "synthetic-haladyna",
    authority: "synthetic",
    claim,
    stem,
    choices,
    key,
    responseType: "selected" as const,
    sourceUrl: SOURCE,
    licenseNote: LICENSE,
    role: "target" as const,
    clusterId,
  };
}

function shuffle<T>(xs: T[], rng: () => number): T[] {
  const out = [...xs];
  for (let i = out.length - 1; i > 0; i--) {
    const j = Math.floor(rng() * (i + 1));
    [out[i], out[j]] = [out[j]!, out[i]!];
  }
  return out;
}

export function generateControls(nPerType = 100): unknown[] {
  const rng = mulberry32(20260916);
  const rows: unknown[] = [];
  for (const flaw of FLAW_TYPES) {
    for (let i = 0; i < nPerType; i++) {
      const split = i < nPerType / 2 ? "train" : "holdout";
      const n0 = 10 + Math.floor(rng() * 40);
      const nums = [n0, n0 + 3, n0 + 7, n0 + 11];
      const token = `batch${i}`;
      if (flaw === "longest") {
        const keyLetter = LETTERS[Math.floor(rng() * 4)]!;
        const choices: Record<string, string> = {};
        for (const L of LETTERS) {
          choices[L] = L === keyLetter ? `the calibrated reading after rounding for ${token}` : `${nums[LETTERS.indexOf(L)]}`;
        }
        rows.push(
          itemBase(`syn-flaw-longest-${i}`, "flaw-longest", `Which report of the measured length in trial ${i} is correct?`, choices, keyLetter, split),
        );
        const cleanChoices: Record<string, string> = {};
        const order = shuffle([...nums], rng);
        LETTERS.forEach((L, j) => {
          cleanChoices[L] = `value ${order[j]}`;
        });
        const cleanKey = LETTERS[Math.floor(rng() * 4)]!;
        rows.push(
          itemBase(`syn-clean-longest-${i}`, "clean", `Which report of the measured length in trial ${i} is correct?`, cleanChoices, cleanKey, split),
        );
      } else if (flaw === "stem-repeat") {
        const keyLetter = LETTERS[Math.floor(rng() * 4)]!;
        const choices: Record<string, string> = {};
        for (const L of LETTERS) {
          choices[L] = L === keyLetter ? `use the ${token} reading` : `use the spare reading ${nums[LETTERS.indexOf(L)]}`;
        }
        rows.push(
          itemBase(
            `syn-flaw-stem-repeat-${i}`,
            "flaw-stem-repeat",
            `A technician records the ${token} reading. Which option names that same ${token} quantity?`,
            choices,
            keyLetter,
            split,
          ),
        );
        const cleanChoices: Record<string, string> = {};
        LETTERS.forEach((L, j) => {
          cleanChoices[L] = `use reading ${nums[j]}`;
        });
        rows.push(
          itemBase(
            `syn-clean-stem-repeat-${i}`,
            "clean",
            `A technician records the ${token} reading. Which option names a listed quantity?`,
            cleanChoices,
            LETTERS[Math.floor(rng() * 4)]!,
            split,
          ),
        );
      } else if (flaw === "absolute") {
        const keyLetter = LETTERS[Math.floor(rng() * 4)]!;
        const choices: Record<string, string> = {};
        const abs = ["always 12", "never 15", "only 18", "every 21"];
        let a = 0;
        for (const L of LETTERS) {
          choices[L] = L === keyLetter ? `about ${n0} in typical cases` : abs[a++]!;
        }
        rows.push(
          itemBase(`syn-flaw-absolute-${i}`, "flaw-absolute", `Which statement about the count in trial ${i} is the best report?`, choices, keyLetter, split),
        );
        const cleanChoices: Record<string, string> = {};
        LETTERS.forEach((L, j) => {
          cleanChoices[L] = `about ${nums[j]} in typical cases`;
        });
        rows.push(
          itemBase(`syn-clean-absolute-${i}`, "clean", `Which statement about the count in trial ${i} is the best report?`, cleanChoices, LETTERS[Math.floor(rng() * 4)]!, split),
        );
      } else if (flaw === "position") {
        const choices: Record<string, string> = {
          A: `value ${nums[0]}`,
          B: `value ${nums[1]}`,
          C: `value ${nums[2]}`,
          D: `value ${nums[3]}`,
        };
        rows.push(
          itemBase(`syn-flaw-position-${i}`, "flaw-position", `Which listed value is tagged as the key for trial ${i}?`, choices, "C", split),
        );
        const cleanKey = LETTERS[Math.floor(rng() * 4)]!;
        rows.push(
          itemBase(`syn-clean-position-${i}`, "clean", `Which listed value is tagged as the key for trial ${i}?`, { ...choices }, cleanKey, split),
        );
      } else if (flaw === "grammar") {
        const keyLetter = LETTERS[Math.floor(rng() * 4)]!;
        const vowels = ["orange", "apple", "igloo", "ulna"];
        const cons = ["box", "crate", "drum", "frame"];
        const choices: Record<string, string> = {};
        let v = 0;
        let c = 0;
        for (const L of LETTERS) {
          choices[L] = L === keyLetter ? cons[c++]! : vowels[v++]!;
        }
        rows.push(
          itemBase(`syn-flaw-grammar-${i}`, "flaw-grammar", `The worker selected a`, choices, keyLetter, split),
        );
        const cleanChoices: Record<string, string> = {};
        LETTERS.forEach((L, j) => {
          cleanChoices[L] = cons[j] ?? `tool${j}`;
        });
        rows.push(
          itemBase(`syn-clean-grammar-${i}`, "clean", `The worker selected a`, cleanChoices, LETTERS[Math.floor(rng() * 4)]!, split),
        );
      } else {
        const keyLetter = LETTERS[Math.floor(rng() * 4)]!;
        const choices: Record<string, string> = {};
        const junk = ["zxq vbb", "qwx nnp", "vvt kkj", "mmp yyw"];
        let j = 0;
        for (const L of LETTERS) {
          choices[L] = L === keyLetter ? "water" : junk[j++]!;
        }
        rows.push(
          itemBase(`syn-flaw-implausible-${i}`, "flaw-implausible", `Which word is a real English word in list ${i}?`, choices, keyLetter, split),
        );
        const cleanChoices: Record<string, string> = { A: "water", B: "house", C: "light", D: "earth" };
        rows.push(
          itemBase(`syn-clean-implausible-${i}`, "clean", `Which word is a real English word in list ${i}?`, cleanChoices, LETTERS[Math.floor(rng() * 4)]!, split),
        );
      }
    }
  }
  return rows;
}

export function writeControls(): void {
  const rows = generateControls(100);
  const out = path.join(ROOT, "data/synthetic-controls.jsonl");
  fs.writeFileSync(out, rows.map((r) => JSON.stringify(r)).join("\n") + "\n");
  console.log(`wrote ${rows.length} synthetic controls -> ${out}`);
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  writeControls();
}
