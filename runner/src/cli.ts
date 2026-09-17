#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import { ClaimsFileSchema, ItemSchema, RulesFileSchema } from "./schema.ts";

type Kind = "items" | "claims" | "rules";

function fail(message: string, code = 1): never {
  console.error(message);
  process.exit(code);
}

function loadJsonOrJsonl(filePath: string): unknown[] {
  const raw = fs.readFileSync(filePath, "utf8");
  const trimmed = raw.trim();
  if (filePath.endsWith(".jsonl") || trimmed.includes("\n") && !trimmed.startsWith("[")) {
    const rows: unknown[] = [];
    for (const [i, line] of trimmed.split(/\r?\n/).entries()) {
      if (!line.trim()) continue;
      try {
        rows.push(JSON.parse(line));
      } catch (err) {
        fail(`${filePath}:${i + 1}: invalid JSON: ${(err as Error).message}`);
      }
    }
    return rows;
  }
  try {
    const parsed = JSON.parse(trimmed) as unknown;
    return Array.isArray(parsed) ? parsed : [parsed];
  } catch (err) {
    fail(`${filePath}: invalid JSON: ${(err as Error).message}`);
  }
}

function validateItems(filePath: string): void {
  const rows = loadJsonOrJsonl(filePath);
  const errors: string[] = [];
  const ids = new Set<string>();
  rows.forEach((row, i) => {
    const parsed = ItemSchema.safeParse(row);
    if (!parsed.success) {
      errors.push(`item[${i}]: ${parsed.error.message}`);
      return;
    }
    if (ids.has(parsed.data.id)) {
      errors.push(`item[${i}]: duplicate id ${parsed.data.id}`);
    }
    ids.add(parsed.data.id);
  });
  if (errors.length) fail(`${filePath}: ${errors.length} error(s)\n${errors.slice(0, 40).join("\n")}`);
  console.log(`ok items ${filePath}: ${rows.length} records`);
}

function validateClaims(filePath: string): void {
  const raw = JSON.parse(fs.readFileSync(filePath, "utf8")) as unknown;
  const parsed = ClaimsFileSchema.safeParse(raw);
  if (!parsed.success) fail(`${filePath}: ${parsed.error.message}`);
  const claims = Array.isArray(parsed.data) ? parsed.data : parsed.data.claims;
  const keys = new Set<string>();
  for (const c of claims) {
    const k = `${c.authority}::${c.code}`;
    if (keys.has(k)) fail(`${filePath}: duplicate claim ${k}`);
    keys.add(k);
  }
  console.log(`ok claims ${filePath}: ${claims.length} records`);
}

function validateRules(filePath: string): void {
  const raw = JSON.parse(fs.readFileSync(filePath, "utf8")) as unknown;
  const parsed = RulesFileSchema.safeParse(raw);
  if (!parsed.success) fail(`${filePath}: ${parsed.error.message}`);
  const rules = Array.isArray(parsed.data) ? parsed.data : parsed.data.rules;
  const ids = new Set<string>();
  for (const r of rules) {
    if (ids.has(r.id)) fail(`${filePath}: duplicate rule ${r.id}`);
    ids.add(r.id);
    if (!r.citation.trim()) fail(`${filePath}: ${r.id} missing citation`);
  }
  console.log(`ok rules ${filePath}: ${rules.length} records`);
}

export function validateFile(kind: Kind, filePath: string): void {
  const resolved = path.resolve(filePath);
  if (!fs.existsSync(resolved)) fail(`file not found: ${resolved}`);
  if (kind === "items") validateItems(resolved);
  else if (kind === "claims") validateClaims(resolved);
  else validateRules(resolved);
}

const USAGE = `usage:
  validate items|claims|rules <file>
  run [--items <file>] [--claims-dir <dir>] [--rules <file>] [--out <dir>] [--resume]
  controls

Contracts A/B/C. One-sided: a pass is a witness that the tag overstates what a pass shows.`;

export async function main(argv = process.argv.slice(2)): Promise<void> {
  const cmd = argv[0];
  if (cmd === "validate") {
    const kind = argv[1] as Kind | undefined;
    const file = argv[2];
    if (!kind || !file || !["items", "claims", "rules"].includes(kind)) {
      fail(USAGE);
    }
    validateFile(kind, file);
    return;
  }
  if (cmd === "run") {
    const { runCensus } = await import("./run.ts");
    await runCensus(argv.slice(1));
    return;
  }
  if (cmd === "controls") {
    const { runMethodControls } = await import("./run_controls.ts");
    runMethodControls();
    return;
  }
  if (cmd === "controls-real") {
    const { runRealControls } = await import("./run_real_controls.ts");
    runRealControls();
    return;
  }
  fail(USAGE);
}

main().catch((err: unknown) => {
  fail((err as Error).stack ?? String(err));
});
