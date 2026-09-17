import fs from "node:fs";
import path from "node:path";
import type { TrialRecord } from "./types.ts";

/** Append-only JSONL trial log. Resume skips (itemId, programId) pairs already present. */

export function loadCompleted(logPath: string): Set<string> {
  const done = new Set<string>();
  if (!fs.existsSync(logPath)) return done;
  const raw = fs.readFileSync(logPath, "utf8");
  for (const line of raw.split(/\r?\n/)) {
    if (!line.trim()) continue;
    try {
      const rec = JSON.parse(line) as TrialRecord;
      done.add(`${rec.itemId}::${rec.programId}`);
    } catch {
      // leave corrupt lines; next writer appends; resume still skips parseable rows
    }
  }
  return done;
}

export function appendTrial(logPath: string, rec: TrialRecord): void {
  fs.mkdirSync(path.dirname(logPath), { recursive: true });
  fs.appendFileSync(logPath, JSON.stringify(rec) + "\n", "utf8");
}

export function trialKey(itemId: string, programId: string): string {
  return `${itemId}::${programId}`;
}
