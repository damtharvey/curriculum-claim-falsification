/**
 * Data loading — reads items.jsonl and rules from the bundled assets
 * (embedded at build time by esbuild) or from S3 at runtime.
 */

import { GetObjectCommand, S3Client } from "@aws-sdk/client-s3";
import type { AprioriRule, Item } from "./types.js";

const s3 = new S3Client({});
const BUCKET = process.env.DATA_BUCKET ?? "";

let itemsCache: Item[] | null = null;
let rulesCache: AprioriRule[] | null = null;
let witnessesCache: unknown[] | null = null;
let ruleChanceCache: unknown[] | null = null;
let cellTableCache: unknown | null = null;

async function fetchS3Json(key: string): Promise<string> {
  const cmd = new GetObjectCommand({ Bucket: BUCKET, Key: key });
  const resp = await s3.send(cmd);
  return resp.Body?.transformToString("utf-8") ?? "";
}

export async function loadItems(): Promise<Item[]> {
  if (itemsCache) return itemsCache;
  const text = await fetchS3Json("data/items.jsonl");
  itemsCache = text
    .split("\n")
    .filter((l) => l.trim())
    .map((l) => JSON.parse(l) as Item)
    .filter((it) => it.role !== "retrieval-pool");
  return itemsCache;
}

export async function loadRules(): Promise<AprioriRule[]> {
  if (rulesCache) return rulesCache;
  const text = await fetchS3Json("data/apriori.json");
  const raw = JSON.parse(text) as { rules?: AprioriRule[] } | AprioriRule[];
  rulesCache = Array.isArray(raw) ? raw : (raw.rules ?? []);
  return rulesCache;
}

export async function loadWitnesses(): Promise<unknown[]> {
  if (witnessesCache) return witnessesCache;
  const text = await fetchS3Json("data/witnesses.json");
  witnessesCache = JSON.parse(text) as unknown[];
  return witnessesCache;
}

export async function loadRuleChance(): Promise<unknown[]> {
  if (ruleChanceCache) return ruleChanceCache;
  const text = await fetchS3Json("data/rule-chance.json");
  ruleChanceCache = JSON.parse(text) as unknown[];
  return ruleChanceCache;
}

export async function loadCellTable(): Promise<unknown> {
  if (cellTableCache) return cellTableCache;
  const text = await fetchS3Json("data/apriori-cell-table.json");
  cellTableCache = JSON.parse(text);
  return cellTableCache;
}
