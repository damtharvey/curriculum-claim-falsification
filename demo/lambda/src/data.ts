/**
 * Data loading — reads the frozen exports from S3 at runtime, or from the
 * repo checkout when LOCAL_DATA_ROOT is set (local dev server).
 */

import { GetObjectCommand, ListObjectsV2Command, S3Client } from "@aws-sdk/client-s3";
import { readdir, readFile, stat } from "node:fs/promises";
import { join } from "node:path";
import type { AprioriRule, ClaimFile, Item } from "./types.js";

const s3 = new S3Client({});
const BUCKET = process.env.DATA_BUCKET ?? "";
const LOCAL_ROOT = process.env.LOCAL_DATA_ROOT ?? "";

/** S3 key → path in the repo checkout (mirrors scripts/upload-data.mjs). */
const LOCAL_PATHS: Record<string, string> = {
  "data/items.jsonl": "data/items.jsonl",
  "data/apriori.json": "rules/apriori.json",
  "data/witnesses.json": "exports/witnesses.json",
  "data/rule-chance.json": "exports/rule-chance.json",
  "data/apriori-cell-table.json": "exports/apriori-cell-table.json",
};

let itemsCache: Item[] | null = null;
let rulesCache: AprioriRule[] | null = null;
let witnessesCache: unknown[] | null = null;
let ruleChanceCache: unknown[] | null = null;
let cellTableCache: unknown | null = null;
let claimsCache: ClaimFile[] | null = null;

function localPath(key: string): string {
  const rel = LOCAL_PATHS[key] ?? key.replace(/^data\/claims\//, "claims/");
  return join(LOCAL_ROOT, rel);
}

async function fetchText(key: string): Promise<string> {
  if (LOCAL_ROOT) return readFile(localPath(key), "utf-8");
  const cmd = new GetObjectCommand({ Bucket: BUCKET, Key: key });
  const resp = await s3.send(cmd);
  return resp.Body?.transformToString("utf-8") ?? "";
}

export interface DataFile {
  key: string;
  size: number;
  lastModified?: string;
}

/** Every object under data/ in the bucket (or the same files locally). */
export async function listDataFiles(): Promise<DataFile[]> {
  if (LOCAL_ROOT) {
    const out: DataFile[] = [];
    const keys = [...Object.keys(LOCAL_PATHS)];
    for (const f of await readdir(join(LOCAL_ROOT, "claims"))) {
      if (f.endsWith(".json")) keys.push(`data/claims/${f}`);
    }
    for (const key of keys) {
      const s = await stat(localPath(key)).catch(() => null);
      if (s) out.push({ key, size: s.size, lastModified: s.mtime.toISOString() });
    }
    return out;
  }
  const out: DataFile[] = [];
  let token: string | undefined;
  do {
    const resp = await s3.send(
      new ListObjectsV2Command({ Bucket: BUCKET, Prefix: "data/", ContinuationToken: token }),
    );
    for (const o of resp.Contents ?? []) {
      if (o.Key) out.push({ key: o.Key, size: o.Size ?? 0, lastModified: o.LastModified?.toISOString() });
    }
    token = resp.IsTruncated ? resp.NextContinuationToken : undefined;
  } while (token);
  return out;
}

export async function loadItems(): Promise<Item[]> {
  if (itemsCache) return itemsCache;
  const text = await fetchText("data/items.jsonl");
  itemsCache = text
    .split("\n")
    .filter((l) => l.trim())
    .map((l) => JSON.parse(l) as Item)
    .filter((it) => it.role !== "retrieval-pool");
  return itemsCache;
}

export async function loadRules(): Promise<AprioriRule[]> {
  if (rulesCache) return rulesCache;
  const text = await fetchText("data/apriori.json");
  const raw = JSON.parse(text) as { rules?: AprioriRule[] } | AprioriRule[];
  rulesCache = Array.isArray(raw) ? raw : (raw.rules ?? []);
  return rulesCache;
}

export async function loadWitnesses(): Promise<unknown[]> {
  if (witnessesCache) return witnessesCache;
  const text = await fetchText("data/witnesses.json");
  witnessesCache = JSON.parse(text) as unknown[];
  return witnessesCache;
}

export async function loadRuleChance(): Promise<unknown[]> {
  if (ruleChanceCache) return ruleChanceCache;
  const text = await fetchText("data/rule-chance.json");
  ruleChanceCache = JSON.parse(text) as unknown[];
  return ruleChanceCache;
}

export async function loadCellTable(): Promise<unknown> {
  if (cellTableCache) return cellTableCache;
  const text = await fetchText("data/apriori-cell-table.json");
  cellTableCache = JSON.parse(text);
  return cellTableCache;
}

/** One entry per claims/<authority>.json. */
export async function loadClaims(): Promise<ClaimFile[]> {
  if (claimsCache) return claimsCache;
  const files = (await listDataFiles()).filter((f) => f.key.startsWith("data/claims/"));
  const out: ClaimFile[] = [];
  for (const f of files) {
    const parsed = JSON.parse(await fetchText(f.key)) as ClaimFile;
    out.push({ ...parsed, file: f.key.replace(/^data\/claims\//, "claims/") });
  }
  claimsCache = out.sort((a, b) => a.file.localeCompare(b.file));
  return claimsCache;
}
