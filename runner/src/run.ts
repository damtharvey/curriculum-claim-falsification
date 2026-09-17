import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import {
  answersMatch,
  choicesOnlyView,
  itemCuesView,
  stemNgramView,
  unboundView,
} from "./channels.ts";
import { appendTrial, loadCompleted, trialKey } from "./log.ts";
import { bedrockBackend, choicesOnlyModel } from "./models.ts";
import { chanceRate, programs, randomChoice, stemNgramClassifier } from "./programs/apriori.ts";
import {
  MIN_N_WITNESS,
  applyFormula,
  applyNgram,
  applyOverlap,
  applyRandomNgram,
  isStateItem,
  isTimssHeadline,
  isTimssItem,
  trainFormula,
  trainNgram,
  trainOverlap,
} from "./programs/fitted.ts";
import { ClaimSchema, ItemSchema, RulesFileSchema } from "./schema.ts";
import { minDetectableTrueRate, minObservablePassRate, powerNote } from "./power.ts";
import { applyCueProgram, fitSearch, percentile } from "./programs/search.ts";
import { keysDisagree, referenceSolve } from "./solver.ts";
import { bootstrapCi, complexityFeatureCount, mean, mulberry32 } from "./stats.ts";
import type {
  AprioriRule,
  Claim,
  ComparisonRow,
  DisputeRecord,
  FittedHeldOutRow,
  Item,
  Operation,
  RequirementCell,
  RuleChanceRow,
  TrialRecord,
  WitnessRecord,
} from "./types.ts";
import { WITNESS_DEFINITION } from "./types.ts";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");

function argValue(argv: string[], name: string, fallback: string): string {
  const i = argv.indexOf(name);
  return i >= 0 && argv[i + 1] ? argv[i + 1]! : fallback;
}

function loadItems(filePath: string): Item[] {
  const rows: Item[] = [];
  for (const line of fs.readFileSync(filePath, "utf8").split(/\r?\n/)) {
    if (!line.trim()) continue;
    rows.push(ItemSchema.parse(JSON.parse(line)));
  }
  return rows.filter((it) => it.role !== "retrieval-pool");
}

function loadClaims(dir: string): Claim[] {
  const claims: Claim[] = [];
  for (const name of fs.readdirSync(dir)) {
    if (!name.endsWith(".json")) continue;
    const raw = JSON.parse(fs.readFileSync(path.join(dir, name), "utf8")) as unknown;
    const list = Array.isArray(raw)
      ? raw
      : ((raw as { claims?: unknown }).claims ?? []);
    for (const c of list as unknown[]) {
      claims.push(ClaimSchema.parse(c));
    }
  }
  return claims;
}

function loadRules(filePath: string): AprioriRule[] {
  const raw = JSON.parse(fs.readFileSync(filePath, "utf8")) as unknown;
  const parsed = RulesFileSchema.parse(raw);
  return Array.isArray(parsed) ? parsed : parsed.rules;
}

function claimOps(claims: Claim[], item: Item): Operation[] {
  const hit = claims.find((c) => c.authority === item.authority && c.code === item.claim);
  return hit?.operations ?? [];
}

function applies(rule: AprioriRule, item: Item): boolean {
  return rule.appliesTo.includes(item.responseType);
}

function viewFor(rule: AprioriRule, item: Item) {
  if (rule.channel === "item-cues") return itemCuesView(item, rule.id);
  if (rule.channel === "unbound-exec") return unboundView(item, rule.id);
  if (rule.id === "stem-option-overlap" || rule.id === "option-repeating-stem-numbers") {
    return stemNgramView(item, rule.id);
  }
  if (rule.channel === "partial-input") return choicesOnlyView(item, rule.id);
  return unboundView(item, rule.id);
}

export async function runCensus(argv: string[]): Promise<void> {
  const itemsPath = argValue(argv, "--items", path.join(ROOT, "data/items.jsonl"));
  const claimsDir = argValue(argv, "--claims-dir", path.join(ROOT, "claims"));
  const rulesPath = argValue(argv, "--rules", path.join(ROOT, "rules/apriori.json"));
  const outDir = argValue(argv, "--out", path.join(ROOT, "exports"));
  const logPath = argValue(argv, "--log", path.join(ROOT, "exports/trials.jsonl"));
  const resume = argv.includes("--resume") || fs.existsSync(logPath);

  fs.mkdirSync(outDir, { recursive: true });

  const items = loadItems(itemsPath);
  const claims = loadClaims(claimsDir);
  const rules = loadRules(rulesPath);
  const backend = bedrockBackend();
  const done = resume ? loadCompleted(logPath) : new Set<string>();
  if (!resume && fs.existsSync(logPath)) fs.unlinkSync(logPath);

  const trials: TrialRecord[] = [];
  if (resume && fs.existsSync(logPath)) {
    for (const line of fs.readFileSync(logPath, "utf8").split(/\r?\n/)) {
      if (!line.trim()) continue;
      trials.push(JSON.parse(line) as TrialRecord);
    }
  }

  const disputes: DisputeRecord[] = [];
  const rng = mulberry32(20260916);

  for (const item of items) {
    const solver = referenceSolve(item);
    if (solver.confident && solver.answer && keysDisagree(item.key, solver.answer)) {
      disputes.push({
        itemId: item.id,
        publishedKey: item.key,
        solverAnswer: solver.answer,
        solverTrace: solver.trace,
        status: "open",
      });
    }

    for (const rule of rules) {
      const key = trialKey(item.id, rule.id);
      if (done.has(key)) continue;
      if (!applies(rule, item)) {
        const rec: TrialRecord = {
          trialId: key,
          itemId: item.id,
          programId: rule.id,
          channel: rule.channel,
          answer: null,
          correct: null,
          skipped: true,
          skipReason: `responseType ${item.responseType} not in ${rule.appliesTo.join(",")}`,
          trace: ["not applicable"],
          timestamp: new Date().toISOString(),
        };
        appendTrial(logPath, rec);
        trials.push(rec);
        done.add(key);
        continue;
      }
      const view = viewFor(rule, item);
      const fn = programs[rule.id];
      const result = fn
        ? fn(view, item, rule)
        : { answer: null, skipped: true, skipReason: "missing program", trace: [] };
      const correct =
        result.skipped || result.answer === null
          ? null
          : answersMatch(item.key, result.answer);
      const rec: TrialRecord = {
        trialId: key,
        itemId: item.id,
        programId: rule.id,
        channel: rule.channel,
        answer: result.answer,
        correct,
        skipped: result.skipped,
        skipReason: result.skipReason,
        trace: result.trace,
        timestamp: new Date().toISOString(),
      };
      appendTrial(logPath, rec);
      trials.push(rec);
      done.add(key);
    }

    // Stem n-gram classifier (rules only; identical instruction set to stem-option-overlap, named separately).
    const ngramId = "stem-ngram-classifier";
    const nkey = trialKey(item.id, ngramId);
    if (!done.has(nkey) && item.responseType === "selected") {
      const view = stemNgramView(item, ngramId);
      const result = stemNgramClassifier(view);
      const rec: TrialRecord = {
        trialId: nkey,
        itemId: item.id,
        programId: ngramId,
        channel: "partial-input",
        answer: result.answer,
        correct: result.skipped || !result.answer ? null : answersMatch(item.key, result.answer),
        skipped: result.skipped,
        skipReason: result.skipReason,
        trace: ["rules-only stem n-gram; no language model", ...result.trace],
        timestamp: new Date().toISOString(),
      };
      appendTrial(logPath, rec);
      trials.push(rec);
      done.add(nkey);
    }

    const randId = "random-choice";
    const rkey = trialKey(item.id, randId);
    if (!done.has(rkey) && item.responseType === "selected") {
      const result = randomChoice(item, rng);
      const rec: TrialRecord = {
        trialId: rkey,
        itemId: item.id,
        programId: randId,
        channel: "item-cues",
        answer: result.answer,
        correct: result.answer ? answersMatch(item.key, result.answer) : null,
        skipped: result.skipped,
        skipReason: result.skipReason,
        trace: result.trace,
        timestamp: new Date().toISOString(),
      };
      appendTrial(logPath, rec);
      trials.push(rec);
      done.add(rkey);
    }

    const modelId = "choices-only-model";
    const mkey = trialKey(item.id, modelId);
    if (!done.has(mkey) && item.responseType === "selected") {
      let answer: string | null = null;
      let skipped = true;
      let skipReason: string | undefined = "model backend unavailable";
      const trace = [`backend=${backend.name} available=${backend.available}`];
      if (backend.available && item.choices) {
        try {
          answer = await choicesOnlyModel(backend, item.choices);
          skipped = answer === null;
          skipReason = skipped ? "model did not return a letter" : undefined;
        } catch (err) {
          skipReason = (err as Error).message;
        }
      }
      const rec: TrialRecord = {
        trialId: mkey,
        itemId: item.id,
        programId: modelId,
        channel: "partial-input",
        answer,
        correct: answer ? answersMatch(item.key, answer) : null,
        skipped,
        skipReason,
        trace,
        timestamp: new Date().toISOString(),
      };
      appendTrial(logPath, rec);
      trials.push(rec);
      done.add(mkey);
    }
  }

  const stateSelected = items.filter((it) => isStateItem(it) && it.responseType === "selected");
  const timssSelected = items.filter((it) => isTimssItem(it) && it.responseType === "selected");
  const timssNumeric = items.filter((it) => isTimssItem(it) && it.responseType === "numeric");
  const otherNumeric = items.filter((it) => !isTimssItem(it) && it.responseType === "numeric");
  const ngramState = trainNgram(stateSelected);
  const ngramTimss = trainNgram(timssSelected);
  const overlapState = trainOverlap(stateSelected);
  const overlapTimss = trainOverlap(timssSelected);
  const formulaState = trainFormula(items.filter((it) => isStateItem(it)));
  const formulaTimss = trainFormula(timssNumeric);

  function recordFitted(
    item: Item,
    programId: string,
    channel: TrialRecord["channel"],
    result: { answer: string | null; skipped: boolean; skipReason?: string; trace: string[] },
  ): void {
    const key = trialKey(item.id, programId);
    if (done.has(key)) return;
    const rec: TrialRecord = {
      trialId: key,
      itemId: item.id,
      programId,
      channel,
      answer: result.answer,
      correct:
        result.skipped || result.answer === null ? null : answersMatch(item.key, result.answer),
      skipped: result.skipped,
      skipReason: result.skipReason,
      trace: result.trace,
      timestamp: new Date().toISOString(),
    };
    appendTrial(logPath, rec);
    trials.push(rec);
    done.add(key);
  }

  for (const item of timssSelected) {
    recordFitted(item, "fitted-stem-ngram/state-to-timss", "partial-input", applyNgram(ngramState, item));
    recordFitted(item, "fitted-stem-overlap/state-to-timss", "partial-input", applyOverlap(overlapState, item));
    recordFitted(
      item,
      "random-ngram-weights/state-to-timss",
      "partial-input",
      applyRandomNgram(item, 20260916),
    );
  }
  for (const item of stateSelected) {
    recordFitted(item, "fitted-stem-ngram/timss-to-state", "partial-input", applyNgram(ngramTimss, item));
    recordFitted(item, "fitted-stem-overlap/timss-to-state", "partial-input", applyOverlap(overlapTimss, item));
    recordFitted(
      item,
      "random-ngram-weights/timss-to-state",
      "partial-input",
      applyRandomNgram(item, 20260917),
    );
  }
  if (formulaState) {
    for (const item of timssNumeric) {
      recordFitted(
        item,
        "fitted-numeric-formula/state-to-timss",
        "unbound-exec",
        applyFormula(formulaState.formulaId, item),
      );
    }
  }
  if (formulaTimss) {
    for (const item of otherNumeric) {
      recordFitted(
        item,
        "fitted-numeric-formula/timss-to-other",
        "unbound-exec",
        applyFormula(formulaTimss.formulaId, item),
      );
    }
  }

  const searchState = fitSearch(stateSelected, 20260916);
  const searchTimss = fitSearch(timssSelected, 20260917);
  for (const item of timssSelected) {
    for (const p of searchState.selected) {
      recordFitted(item, `${p.id}/state-to-timss`, "item-cues", applyCueProgram(p, item));
    }
    for (const p of searchState.randoms) {
      recordFitted(item, `${p.id}/state-to-timss`, "item-cues", applyCueProgram(p, item));
    }
  }
  for (const item of stateSelected) {
    for (const p of searchTimss.selected) {
      recordFitted(item, `${p.id}/timss-to-state`, "item-cues", applyCueProgram(p, item));
    }
    for (const p of searchTimss.randoms) {
      recordFitted(item, `${p.id}/timss-to-state`, "item-cues", applyCueProgram(p, item));
    }
  }

  const cells: RequirementCell[] = [];
  const witnesses: WitnessRecord[] = [];
  const ops: Operation[] = ["retrieve", "execute", "bind", "distinguish", "explain", "transfer"];

  const trialByItem = new Map<string, TrialRecord[]>();
  for (const t of trials) {
    const arr = trialByItem.get(t.itemId) ?? [];
    arr.push(t);
    trialByItem.set(t.itemId, arr);
  }

  const ruleById = new Map(rules.map((r) => [r.id, r]));
  const itemById = new Map(items.map((it) => [it.id, it]));

  const ruleChance: RuleChanceRow[] = [];
  const programIds = [
    ...new Set(trials.map((t) => t.programId).filter((id) => id !== "random-choice")),
  ];
  const trialsByProgram = new Map<string, TrialRecord[]>();
  const randomTrialsByDirK = new Map<string, TrialRecord[]>();
  for (const t of trials) {
    const arr = trialsByProgram.get(t.programId) ?? [];
    arr.push(t);
    trialsByProgram.set(t.programId, arr);
    if (t.programId.includes("/random:k") && !t.skipped && t.correct !== null) {
      const dir = t.programId.includes("state-to-timss")
        ? "state-to-timss"
        : t.programId.includes("timss-to-state")
          ? "timss-to-state"
          : "";
      const km = t.programId.match(/random:k(\d+)/);
      const kk = km?.[1] ?? "";
      if (dir && kk) {
        const key = `${dir}::${kk}`;
        const bucket = randomTrialsByDirK.get(key) ?? [];
        bucket.push(t);
        randomTrialsByDirK.set(key, bucket);
      }
    }
  }
  for (const ck of new Set(items.map((it) => `${it.authority}::${it.claim}`))) {
    const [authority, code] = ck.split("::") as [string, string];
    const subset = items.filter((it) => it.authority === authority && it.claim === code);
    const ids = new Set(subset.map((it) => it.id));
    for (const programId of programIds) {
      const scored = (trialsByProgram.get(programId) ?? []).filter(
        (t) => ids.has(t.itemId) && !t.skipped && t.correct !== null,
      );
      if (!scored.length) continue;
      const flags = scored.map((t) => (t.correct ? 1 : 0));
      const chanceVals = scored
        .map((t) => chanceRate(itemById.get(t.itemId)!))
        .map((c) => (c === null ? 0 : c));
      const chance = chanceVals.length ? mean(chanceVals) : 0;
      const ci = bootstrapCi(flags, 1000, 11);
      const passRate = mean(flags);
      const beats = ci[0] > chance;
      const km = programId.match(/random:k(\d+)/) ?? programId.match(/atom:/) ? 1 : programId.includes("/and:") ? 2 : 3;
      const k = programId.includes("/atom:") ? 1 : programId.includes("/and:") ? 2 : km === 1 && programId.includes("random:k") ? Number((programId.match(/random:k(\d+)/) ?? [])[1] ?? 3) : Math.min(3, (programId.match(/\+/g) ?? []).length + 1);
      const dir = programId.includes("state-to-timss")
        ? "state-to-timss"
        : programId.includes("timss-to-state")
          ? "timss-to-state"
          : "NO";
      const randFlags = (randomTrialsByDirK.get(`${dir}::${k}`) ?? []).filter((t) => ids.has(t.itemId));
      const randRates: number[] = [];
      if (programId.startsWith("search/") && randFlags.length) {
        const byProg = new Map<string, number[]>();
        for (const t of randFlags) {
          const arr = byProg.get(t.programId) ?? [];
          arr.push(t.correct ? 1 : 0);
          byProg.set(t.programId, arr);
        }
        for (const flagsR of byProg.values()) {
          if (flagsR.length >= 8) randRates.push(mean(flagsR));
        }
      }
      const p95 = randRates.length ? percentile(randRates, 0.95) : programId.startsWith("search/") ? 1 : 0;
      const isRandomBaseline =
        programId.includes("/random:") || programId.includes("random-ngram");
      const aboveRandom = !programId.startsWith("search/") || passRate >= p95;
      const witnessEligible =
        !isRandomBaseline && beats && scored.length >= MIN_N_WITNESS && aboveRandom;
      const heldOut =
        programId.startsWith("fitted-") ||
        programId.startsWith("random-ngram-") ||
        programId.startsWith("search/");
      ruleChance.push({
        programId,
        claim: code,
        authority,
        nScored: scored.length,
        nCorrect: flags.reduce<number>((a, b) => a + b, 0),
        passRate,
        chanceRate: chance,
        ci95: ci,
        beatsChance: beats,
        witnessEligible,
        heldOut,
        note: witnessEligible
          ? `CI excludes chance, n>=${MIN_N_WITNESS}${programId.startsWith("search/") ? `, pass>${p95.toFixed(3)} random p95` : ""}; witness-eligible`
          : beats && scored.length < MIN_N_WITNESS
            ? `logged-singleton: CI exceeds chance but n=${scored.length}<${MIN_N_WITNESS}; not claimed`
            : beats && !aboveRandom
              ? `beats chance but not above random p95 ${p95.toFixed(3)}; not claimed`
              : "does not beat chance; passes marked non-witness, trials kept",
      });
    }
  }
  const eligible = new Set(
    ruleChance
      .filter((r) => r.witnessEligible)
      .map((r) => `${r.authority}::${r.claim}::${r.programId}`),
  );

  for (const item of items) {
    const tagged = claimOps(claims, item);
    const itemTrials = trialByItem.get(item.id) ?? [];
    for (const op of tagged.length ? tagged : ops) {
      const candidates = itemTrials.filter((t) => {
        if (t.skipped || t.correct !== true) return false;
        if (!eligible.has(`${item.authority}::${item.claim}::${t.programId}`)) return false;
        const rule = ruleById.get(t.programId);
        if (rule) return rule.lacks.includes(op);
        if (t.programId === "stem-ngram-classifier") {
          return (["bind", "distinguish", "explain"] as Operation[]).includes(op);
        }
        if (t.programId === "choices-only-model") {
          return (["bind", "distinguish", "explain"] as Operation[]).includes(op);
        }
        if (t.programId.startsWith("fitted-stem") || t.programId.startsWith("random-ngram")) {
          return (["bind", "distinguish", "explain"] as Operation[]).includes(op);
        }
        if (t.programId.startsWith("fitted-numeric")) {
          return (["bind", "explain"] as Operation[]).includes(op);
        }
        if (t.programId.startsWith("search/") && !t.programId.includes("/random:")) {
          return (["bind", "distinguish", "explain", "execute"] as Operation[]).includes(op);
        }
        return false;
      });
      const searched = itemTrials.map((t) => t.programId);
      const attempted = itemTrials.some((t) => !t.skipped);
      if (candidates.length) {
        const w = candidates[0]!;
        cells.push({
          itemId: item.id,
          operation: op,
          value: 0,
          witness: { programId: w.programId, trace: w.trace },
          searched,
          attempted,
          review: "machine",
        });
        witnesses.push({
          itemId: item.id,
          claim: item.claim,
          authority: item.authority,
          operation: op,
          programId: w.programId,
          channel: w.channel,
          howObtained:
            w.programId.startsWith("fitted-") || w.programId.startsWith("search/")
              ? "fitted-held-out"
              : "a-priori",
          keyWasAvailable: false,
          answer: w.answer ?? "",
          key: item.key,
          trace: w.trace,
          itemStemPreview: item.stem.slice(0, 240),
          beatsChance: true,
        });
      } else {
        cells.push({
          itemId: item.id,
          operation: op,
          value: 1,
          searched,
          attempted,
          review: "machine",
        });
      }
    }
  }

  const comparisons: ComparisonRow[] = [];
  const claimKeys = new Set(items.map((it) => `${it.authority}::${it.claim}`));
  for (const ck of claimKeys) {
    const [authority, code] = ck.split("::") as [string, string];
    const subset = items.filter((it) => it.authority === authority && it.claim === code);
    const ids = new Set(subset.map((it) => it.id));
    const claimCells = cells.filter((c) => ids.has(c.itemId));
    const zeros = claimCells.filter((c) => c.value === 0 && c.attempted);
    const attemptedCells = claimCells.filter((c) => c.attempted);
    const bypass = attemptedCells.length ? zeros.length / attemptedCells.length : 0;
    const chanceVals = subset
      .map((it) => chanceRate(it))
      .filter((x): x is number => x !== null);
    const randTrials = trials.filter(
      (t) => t.programId === "random-choice" && ids.has(t.itemId) && t.correct !== null,
    );
    const flags = attemptedCells.map((c) => (c.value === 0 ? 1 : 0));
    const positive = subset.filter((it) => {
      const its = claimCells.filter((c) => c.itemId === it.id);
      return its.length > 0 && its.every((c) => c.value === 1) && its.some((c) => c.attempted);
    });
    const bypassable = subset.filter((it) =>
      claimCells.some((c) => c.itemId === it.id && c.value === 0),
    );
    const non = subset.filter((it) => !bypassable.includes(it));
    comparisons.push({
      claim: code,
      authority,
      nItems: subset.length,
      nAttempted: new Set(attemptedCells.map((c) => c.itemId)).size,
      bypassRate: bypass,
      chanceRate: chanceVals.length ? mean(chanceVals) : 0,
      randomBaseline: randTrials.length
        ? mean(randTrials.map((t) => (t.correct ? 1 : 0)))
        : chanceVals.length
          ? mean(chanceVals)
          : 0,
      complexity: {
        featureCount: mean(rules.map((r) => complexityFeatureCount(r.id))),
        description: "mean feature count of a priori rules scored on this claim's items",
      },
      ci95: bootstrapCi(flags, 1000, 7),
      nWitnesses: zeros.length,
      nPositiveControls: positive.length,
      discriminating: positive.length > 0,
      percentCorrectRelation: {
        bypassableMean: mean(bypassable.map((it) => it.percentCorrect ?? NaN).filter(Number.isFinite)),
        nonBypassableMean: mean(non.map((it) => it.percentCorrect ?? NaN).filter(Number.isFinite)),
      },
      minObservablePassRate: minObservablePassRate(subset.length, chanceVals.length ? mean(chanceVals) : 0.25),
      minDetectableTrueRate80: minDetectableTrueRate(subset.length, chanceVals.length ? mean(chanceVals) : 0.25),
      nullNote: powerNote({
        authority,
        claim: code,
        nItems: subset.length,
        nSelected: subset.filter((it) => it.responseType === "selected").length,
        chanceRate: chanceVals.length ? mean(chanceVals) : 0.25,
        minObservablePassRate: minObservablePassRate(subset.length, chanceVals.length ? mean(chanceVals) : 0.25),
        minDetectableTrueRate80: minDetectableTrueRate(subset.length, chanceVals.length ? mean(chanceVals) : 0.25),
        barNote: "",
      }),
    });
  }

  function heldOutRow(
    programId: string,
    trainSlice: string,
    evalSlice: string,
    nTrain: number,
    evalItems: Item[],
    randomProgramId?: string,
  ): FittedHeldOutRow {
    const ids = new Set(evalItems.map((it) => it.id));
    const attempted = trials.filter((t) => t.programId === programId && ids.has(t.itemId));
    const scored = attempted.filter((t) => !t.skipped && t.correct !== null);
    const flags = scored.map((t) => (t.correct ? 1 : 0));
    const chanceVals = scored
      .map((t) => chanceRate(itemById.get(t.itemId)!))
      .map((c) => (c === null ? 0 : c));
    const chance = chanceVals.length ? mean(chanceVals) : 0;
    const ci = bootstrapCi(flags, 1000, 13);
    const passRate = scored.length ? mean(flags) : 0;
    const beats = scored.length > 0 && ci[0] > chance;
    const randTrials = randomProgramId
      ? trials.filter(
          (t) => t.programId === randomProgramId && ids.has(t.itemId) && t.correct !== null,
        )
      : [];
    const randomBaseline = randTrials.length
      ? mean(randTrials.map((t) => (t.correct ? 1 : 0)))
      : chance;
    const nSkip = attempted.filter((t) => t.skipped).length;
    let note = "held-out does not beat chance";
    if (!attempted.length) note = "no held-out trials recorded";
    else if (!scored.length) {
      note = `abstained on all ${attempted.length} held-out items (${nSkip} skipped); not a witness`;
    } else if (beats && scored.length >= MIN_N_WITNESS) {
      note = "held-out CI excludes chance; n meets witness bar";
    } else if (beats) {
      note = "held-out CI excludes chance but n below witness bar; logged not claimed";
    }
    return {
      programId,
      trainSlice,
      evalSlice,
      nTrain,
      nScored: scored.length,
      nCorrect: flags.reduce<number>((a, b) => a + b, 0),
      passRate,
      chanceRate: chance,
      randomBaseline,
      ci95: ci,
      beatsChance: beats,
      witnessEligible: beats && scored.length >= MIN_N_WITNESS,
      note,
    };
  }

  const timssHeadlineSelected = timssSelected.filter(isTimssHeadline);
  const fittedHeldOut: FittedHeldOutRow[] = [
    heldOutRow(
      "fitted-stem-ngram/state-to-timss",
      `nysed+staar+mcas selected n=${ngramState.trainN}`,
      "timss applying+reasoning selected",
      ngramState.trainN,
      timssHeadlineSelected,
      "random-ngram-weights/state-to-timss",
    ),
    heldOutRow(
      "fitted-stem-ngram/state-to-timss",
      `nysed+staar+mcas selected n=${ngramState.trainN}`,
      "timss all selected",
      ngramState.trainN,
      timssSelected,
      "random-ngram-weights/state-to-timss",
    ),
    heldOutRow(
      "fitted-stem-overlap/state-to-timss",
      `nysed+staar+mcas selected n=${overlapState.trainN}`,
      "timss applying+reasoning selected",
      overlapState.trainN,
      timssHeadlineSelected,
      "random-ngram-weights/state-to-timss",
    ),
    heldOutRow(
      "random-ngram-weights/state-to-timss",
      "unfitted random weights; same features as n-gram",
      "timss applying+reasoning selected",
      0,
      timssHeadlineSelected,
    ),
    heldOutRow(
      "fitted-stem-ngram/timss-to-state",
      `timss selected n=${ngramTimss.trainN}`,
      "nysed+staar+mcas selected",
      ngramTimss.trainN,
      stateSelected,
      "random-ngram-weights/timss-to-state",
    ),
    heldOutRow(
      "fitted-stem-overlap/timss-to-state",
      `timss selected n=${overlapTimss.trainN}`,
      "nysed+staar+mcas selected",
      overlapTimss.trainN,
      stateSelected,
      "random-ngram-weights/timss-to-state",
    ),
    formulaState
      ? heldOutRow(
          "fitted-numeric-formula/state-to-timss",
          `state numeric n=${formulaState.trainN} best=${formulaState.formulaId}`,
          "timss numeric",
          formulaState.trainN,
          timssNumeric,
        )
      : null,
    formulaTimss
      ? heldOutRow(
          "fitted-numeric-formula/timss-to-other",
          `timss numeric n=${formulaTimss.trainN} best=${formulaTimss.formulaId}`,
          "non-TIMSS numeric (PISA+MCAS+NAPLAN)",
          formulaTimss.trainN,
          otherNumeric,
        )
      : null,
  ].filter((r): r is FittedHeldOutRow => r !== null);

  fs.writeFileSync(path.join(outDir, "matrix.json"), JSON.stringify(cells, null, 2));
  fs.writeFileSync(path.join(outDir, "witnesses.json"), JSON.stringify(witnesses, null, 2));
  fs.writeFileSync(path.join(outDir, "rule-chance.json"), JSON.stringify(ruleChance, null, 2));
  fs.writeFileSync(path.join(outDir, "fitted-heldout.json"), JSON.stringify(fittedHeldOut, null, 2));
  const marks = trials.map((t) => {
    const item = itemById.get(t.itemId);
    const key = item ? `${item.authority}::${item.claim}::${t.programId}` : "";
    const row = ruleChance.find(
      (r) => item && r.programId === t.programId && r.claim === item.claim && r.authority === item.authority,
    );
    return {
      trialId: t.trialId,
      itemId: t.itemId,
      programId: t.programId,
      correct: t.correct,
      skipped: t.skipped,
      beatsChance: row?.beatsChance ?? false,
      witnessEligible: Boolean(t.correct && !t.skipped && eligible.has(key)),
      mark:
        t.correct && !t.skipped && eligible.has(key)
          ? "witness-eligible"
          : t.correct && !t.skipped && row?.beatsChance
            ? "logged-singleton"
            : t.correct && !t.skipped
              ? "non-witness-chance"
              : "not-a-pass",
    };
  });
  fs.writeFileSync(
    path.join(outDir, "trial-marks.jsonl"),
    marks.map((m) => JSON.stringify(m)).join("\n") + "\n",
  );
  fs.writeFileSync(
    path.join(outDir, "comparisons.json"),
    JSON.stringify(
      {
        witnessDefinition: WITNESS_DEFINITION,
        oneSided:
          "Passing does not require X. A pass at chance is not a witness. Failing to find a witness does not certify the tag. We never say students do not learn X.",
        witnessBar: {
          minN: MIN_N_WITNESS,
          rule: "lower 95% bootstrap CI exceeds chance AND nScored >= minN. Search/fitted programs also need held-out pass above the 95th percentile of random programs of matched complexity. Singleton matches are logged, not claimed.",
        },
        programSpace: {
          stateToTimss: searchState.log,
          timssToState: searchTimss.log,
        },
        generatedAt: new Date().toISOString(),
        nItems: items.length,
        nTrials: trials.length,
        nWitnessesClaimed: witnesses.length,
        anyWitnessClearsBar: witnesses.length > 0,
        modelBackend: { name: backend.name, available: backend.available },
        fittedHeldOut,
        rows: comparisons,
        ruleChance,
      },
      null,
      2,
    ),
  );
  fs.writeFileSync(path.join(outDir, "grading.json"), JSON.stringify({ constructedResponse: [] }, null, 2));
  fs.writeFileSync(path.join(ROOT, "data/disputes.jsonl"), disputes.map((d) => JSON.stringify(d)).join("\n") + (disputes.length ? "\n" : ""));

  console.log(
    `census: items=${items.length} trials=${trials.length} cells=${cells.length} witnesses=${witnesses.length} disputes=${disputes.length} matrix=${path.join(outDir, "matrix.json")}`,
  );
  if (!backend.available) {
    console.log("model backend stubbed (no Bedrock credentials); local channels ran.");
  }
}
