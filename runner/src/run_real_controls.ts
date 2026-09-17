import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { answersMatch } from "./channels.ts";
import { MIN_N_WITNESS } from "./programs/fitted.ts";
import { chanceRate } from "./programs/apriori.ts";
import { applyCueProgram, enumeratePrograms, fitSearch, percentile, randomPassRates } from "./programs/search.ts";
import { ItemSchema } from "./schema.ts";
import { bootstrapCi, mean } from "./stats.ts";
import type { Item } from "./types.ts";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");

const PUBLISHED: Record<string, { number: number; chance: number; pointer: string; note: string }> = {
  openbookqa: {
    number: 0.496,
    chance: 0.25,
    pointer: "Mihaylov et al. EMNLP 2018 Table 2, Plausible Answer Detector test 49.6% (ignores the question)",
    note: "choices-only / question-ignored detector",
  },
  swag: {
    number: 0.436,
    chance: 0.25,
    pointer: "Zellers et al. EMNLP 2018 Table 3, LSTM+ELMo ending-only 43.6%. BERT-Large ending-only 74.8% is Zellers et al. ACL 2019 (HellaSwag) Figure 4 on SWAG.",
    note: "endings-only",
  },
  arct: {
    number: 0.61,
    chance: 0.5,
    pointer: "Niven and Kao ACL 2019 Table 2: pick the warrant with not is right 61% of the time (coverage 64%). Warrant-only BERT 71%.",
    note: "not cue / warrant-only",
  },
  race: {
    number: 0.25,
    chance: 0.25,
    pointer: "Lai et al. 2017 chance is 25%. Si et al. arXiv 1910.12391 train BERT without passage (P-Remove) well above chance; exact cell filled after scoring.",
    note: "options-only; published P-Remove is question+options, not options alone",
  },
  commonsenseqa: {
    number: 0.2,
    chance: 0.2,
    pointer: "Talmor et al. NAACL 2019 chance 20% for five options. No official choices-only number; recovered rate is reported against chance.",
    note: "choices-only vs chance; no official published choices-only accuracy",
  },
};

function loadSplitCapped(filePath: string, trainCap: number, evalCap: number): { train: Item[]; hold: Item[] } {
  const train: Item[] = [];
  const hold: Item[] = [];
  const raw = fs.readFileSync(filePath, "utf8").split(/\r?\n/);
  for (const line of raw) {
    if (!line.trim()) continue;
    const parsed = ItemSchema.parse(JSON.parse(line));
    const sp = splitOf(parsed);
    if (sp === "train") {
      if (train.length < trainCap) train.push(parsed);
    } else if (["test", "validation", "dev"].includes(sp)) {
      if (hold.length < evalCap) hold.push(parsed);
    }
    if (train.length >= trainCap && hold.length >= evalCap) break;
  }
  if (hold.length < 32) {
    for (const line of raw) {
      if (!line.trim()) continue;
      const parsed = ItemSchema.parse(JSON.parse(line));
      if (splitOf(parsed) !== "train" && hold.length < evalCap) hold.push(parsed);
      if (hold.length >= evalCap) break;
    }
  }
  return { train, hold };
}

function splitOf(item: Item): string {
  const rec = item as Item & { split?: string };
  if (rec.split) return rec.split;
  const id = item.id;
  if (id.includes("-train-")) return "train";
  if (id.includes("-validation-") || id.includes("-dev-")) return "dev";
  if (id.includes("-test-")) return "test";
  return "all";
}

function notCue(item: Item): { answer: string | null; skipped: boolean } {
  const choices = item.choices ?? {};
  const hits = Object.entries(choices).filter(([, t]) => /\bnot\b/i.test(t));
  if (hits.length !== 1) return { answer: null, skipped: true };
  return { answer: hits[0]![0], skipped: false };
}

export function runRealControls(): void {
  const files = [
    ["openbookqa", path.join(ROOT, "data/real-controls-openbookqa.jsonl")],
    ["swag", path.join(ROOT, "data/real-controls-swag.jsonl")],
    ["arct", path.join(ROOT, "data/real-controls-arct.jsonl")],
    ["race", path.join(ROOT, "data/real-controls-race.jsonl")],
    ["commonsenseqa", path.join(ROOT, "data/real-controls-commonsenseqa.jsonl")],
  ] as const;

  const datasets: object[] = [];
  for (const [name, filePath] of files) {
    if (!fs.existsSync(filePath)) {
      datasets.push({ name, status: "missing", path: filePath });
      continue;
    }
    const { train: trainSet, hold } = loadSplitCapped(filePath, 1500, 400);
    if (trainSet.length + hold.length < 40) {
      datasets.push({ name, status: "too-small", nItems: trainSet.length + hold.length, path: filePath });
      continue;
    }
    const fit = fitSearch(trainSet, 20260916);
    const atoms = enumeratePrograms().filter((p) => p.kind === "atomic");
    const scored = [];
    for (const p of [...atoms, ...fit.selected]) {
      const flags: number[] = [];
      for (const item of hold) {
        const r = applyCueProgram(p, item);
        if (r.skipped || !r.answer) continue;
        flags.push(answersMatch(item.key, r.answer) ? 1 : 0);
      }
      if (flags.length < 8) continue;
      const ci = bootstrapCi(flags, 800, 23);
      const pass = mean(flags);
      const chance = chanceRate(hold[0]!) ?? 1 / Object.keys(hold[0]!.choices ?? { A: 1, B: 1, C: 1, D: 1 }).length;
      const rand = randomPassRates(fit.randoms.filter((r) => r.complexity === p.complexity), hold)[p.complexity] ?? [];
      const p95 = rand.length ? percentile(rand, 0.95) : 1;
      scored.push({
        programId: p.id,
        n: flags.length,
        passRate: pass,
        ci95: ci,
        chance,
        randomP95: p95,
        witnessEligible: flags.length >= MIN_N_WITNESS && ci[0] > chance && pass >= p95,
      });
    }
    let cue: object | null = null;
    if (name === "arct") {
      const flags: number[] = [];
      for (const item of hold) {
        const r = notCue(item);
        if (r.skipped || !r.answer) continue;
        flags.push(answersMatch(item.key, r.answer) ? 1 : 0);
      }
      if (flags.length) {
        const ci = bootstrapCi(flags, 800, 29);
        cue = {
          programId: "arct-not-unigram",
          n: flags.length,
          passRate: mean(flags),
          ci95: ci,
          chance: 0.5,
        };
      }
    }
    const eligible = scored.filter((s) => s.witnessEligible);
    const best = [...scored].sort((a, b) => b.passRate - a.passRate)[0];
    const pub = PUBLISHED[name];
    datasets.push({
      name,
      nItems: trainSet.length + hold.length,
      nTrain: trainSet.length,
      nEval: hold.length,
      published: pub,
      bestHeldOut: best ?? null,
      nWitnessEligiblePrograms: eligible.length,
      recoveredMinusPublished: best && pub ? best.passRate - pub.number : null,
      arctNotCue: cue,
      programSpace: fit.log,
    });
  }

  const dest = path.join(ROOT, "exports/method-controls.json");
  let prior: Record<string, unknown> = {};
  if (fs.existsSync(dest)) prior = JSON.parse(fs.readFileSync(dest, "utf8")) as Record<string, unknown>;
  prior.realPublicCueSets = datasets;
  prior.generatedAt = new Date().toISOString();
  fs.writeFileSync(dest, JSON.stringify(prior, null, 2));
  console.log(`real controls written into ${dest} (${datasets.length} datasets)`);
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  runRealControls();
}
