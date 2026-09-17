import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { answersMatch } from "./channels.ts";
import { writeControls } from "./generate_controls.ts";
import { MIN_N_WITNESS } from "./programs/fitted.ts";
import { chanceRate } from "./programs/apriori.ts";
import {
  applyCueProgram,
  enumeratePrograms,
  fitSearch,
  percentile,
  randomPassRates,
  type CueProgram,
} from "./programs/search.ts";
import { ItemSchema } from "./schema.ts";
import { bootstrapCi, mean } from "./stats.ts";
import type { Item } from "./types.ts";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");

const PLANTED_ATOMIC: Record<string, string> = {
  "flaw-longest": "search/atom:longest",
  "flaw-stem-repeat": "search/atom:overlap",
  "flaw-absolute": "search/atom:noAbsolute",
  "flaw-position": "search/atom:positionC",
  "flaw-grammar": "search/atom:grammarAgree",
  "flaw-implausible": "search/atom:specificity",
};

function loadItems(filePath: string): Item[] {
  return fs
    .readFileSync(filePath, "utf8")
    .split(/\r?\n/)
    .filter((l) => l.trim())
    .map((l) => ItemSchema.parse(JSON.parse(l)));
}

function scoreProgram(program: CueProgram, items: Item[]): { n: number; hits: number; flags: number[]; chance: number } {
  const flags: number[] = [];
  const chances: number[] = [];
  for (const item of items) {
    const r = applyCueProgram(program, item);
    if (r.skipped || !r.answer) continue;
    flags.push(answersMatch(item.key, r.answer) ? 1 : 0);
    chances.push(chanceRate(item) ?? 0.25);
  }
  return {
    n: flags.length,
    hits: flags.reduce<number>((a, b) => a + b, 0),
    flags,
    chance: chances.length ? mean(chances) : 0.25,
  };
}

export function runMethodControls(): void {
  const ctrlPath = path.join(ROOT, "data/synthetic-controls.jsonl");
  if (!fs.existsSync(ctrlPath)) writeControls();
  const items = loadItems(ctrlPath);
  const train = items.filter((it) => it.clusterId === "train");
  const holdout = items.filter((it) => it.clusterId === "holdout");
  const fit = fitSearch(train, 20260916);
  const atoms = enumeratePrograms().filter((p) => p.kind === "atomic");
  const toScore = [...atoms, ...fit.selected];
  function p95On(subset: Item[], k: number): number {
    const rates = randomPassRates(fit.randoms.filter((p) => p.complexity === k), subset)[k] ?? [];
    return rates.length ? percentile(rates, 0.95) : 1;
  }

  const perClaim: Record<string, { programs: object[]; found: boolean; plantedAtomic?: object }> = {};
  const claims = [...new Set(holdout.map((it) => it.claim))];
  for (const claim of claims) {
    const subset = holdout.filter((it) => it.claim === claim);
    const programs = [];
    let found = false;
    for (const p of toScore) {
      const s = scoreProgram(p, subset);
      if (!s.n) continue;
      const ci = bootstrapCi(s.flags, 800, 17);
      const pass = s.n ? s.hits / s.n : 0;
      const beatsChance = ci[0] > s.chance;
      const p95 = p95On(subset, p.complexity);
      const aboveRandom = pass >= p95;
      const eligible = beatsChance && s.n >= MIN_N_WITNESS && aboveRandom;
      const row = {
        programId: p.id,
        nScored: s.n,
        nCorrect: s.hits,
        passRate: pass,
        chanceRate: s.chance,
        ci95: ci,
        randomP95: p95,
        beatsChance,
        aboveRandomP95: aboveRandom,
        witnessEligible: eligible,
      };
      programs.push(row);
      if (eligible) found = true;
    }
    perClaim[claim] = { programs, found };
  }

  const flawClaims = claims.filter((c) => c.startsWith("flaw-"));
  let plantedHits = 0;
  const planted = [];
  for (const claim of flawClaims) {
    const subset = holdout.filter((it) => it.claim === claim);
    const atomId = PLANTED_ATOMIC[claim];
    const atom = atoms.find((p) => p.id === atomId);
    if (!atom) continue;
    const s = scoreProgram(atom, subset);
    const ci = bootstrapCi(s.flags, 800, 19);
    const pass = s.n ? s.hits / s.n : 0;
    const p95 = p95On(subset, 1);
    const eligible = s.n >= MIN_N_WITNESS && ci[0] > s.chance && pass >= p95;
    planted.push({
      claim,
      plantedProgram: atomId,
      nScored: s.n,
      passRate: pass,
      chanceRate: s.chance,
      ci95: ci,
      randomP95: p95,
      witnessEligible: eligible,
    });
    if (eligible) plantedHits += 1;
  }

  const cleanRows = perClaim.clean?.programs ?? [];
  const cleanFalsePos = cleanRows.filter((r) => (r as { witnessEligible?: boolean }).witnessEligible);
  const recallTypes = flawClaims.length ? plantedHits / flawClaims.length : 0;
  const fpr = cleanFalsePos.length > 0;

  const out = {
    generatedAt: new Date().toISOString(),
    nItems: items.length,
    nTrain: train.length,
    nHoldout: holdout.length,
    nPerFlawType: 100,
    nCleanMatched: items.filter((it) => it.claim === "clean").length,
    realPublicFlawSet:
      "None obtained. Clever Hans (arXiv 2410.11672) reports n-gram predictability on existing LLM benchmarks but does not ship a labeled Haladyna-flaw item file. BenchMarker writing-flaw labels need an LLM judge. Costello et al. 2018 labels were not a public download. No real cue-flaw set was invented.",
    programSpace: fit.log,
    witnessBar: {
      minN: MIN_N_WITNESS,
      rule: "held-out pass rate at or above the 95th percentile of random programs of matched complexity AND lower 95% bootstrap CI excludes chance AND n >= 10",
    },
    randomP95: {
      1: p95On(holdout.filter((it) => it.claim === "clean"), 1),
      2: p95On(holdout.filter((it) => it.claim === "clean"), 2),
      3: p95On(holdout.filter((it) => it.claim === "clean"), 3),
    },
    recallPlantedFlawTypes: recallTypes,
    plantedTypeHits: plantedHits,
    plantedTypeN: flawClaims.length,
    planted,
    falsePositiveOnClean: fpr,
    nCleanProgramsEligible: cleanFalsePos.length,
    searcherFoundAnyFlawType: flawClaims.filter((c) => perClaim[c]?.found).length / (flawClaims.length || 1),
    note: "Synthetic only. A null on real items is not certified by these controls; controls ask whether the searcher can detect planted unique cues.",
  };
  const dest = path.join(ROOT, "exports/method-controls.json");
  fs.writeFileSync(dest, JSON.stringify(out, null, 2));
  console.log(
    `method-controls: recallTypes=${recallTypes.toFixed(2)} fpr=${fpr} space=${fit.log.programSpaceSize} -> ${dest}`,
  );
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  runMethodControls();
}
