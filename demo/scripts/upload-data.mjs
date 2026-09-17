#!/usr/bin/env node
/**
 * Upload pre-computed export data to the S3 data bucket.
 * Usage: node scripts/upload-data.mjs <bucket-name>
 *
 * If no bucket name is provided, reads from CDK outputs.
 */

import { execSync } from "node:child_process";
import { existsSync, readFileSync } from "node:fs";
import { resolve, join } from "node:path";

const ROOT = resolve(import.meta.dirname, "../..");

// Files to upload to s3://<bucket>/data/
const DATA_FILES = [
  { local: "data/items.jsonl", s3Key: "data/items.jsonl" },
  { local: "rules/apriori.json", s3Key: "data/apriori.json" },
  { local: "exports/witnesses.json", s3Key: "data/witnesses.json" },
  { local: "exports/rule-chance.json", s3Key: "data/rule-chance.json" },
  { local: "exports/apriori-cell-table.json", s3Key: "data/apriori-cell-table.json" },
  { local: "exports/comparisons.json", s3Key: "data/comparisons.json" },
  { local: "exports/cell-power.json", s3Key: "data/cell-power.json" },
  { local: "exports/fitted-heldout.json", s3Key: "data/fitted-heldout.json" },
  { local: "exports/method-controls.json", s3Key: "data/method-controls.json" },
  { local: "exports/channel-audit.json", s3Key: "data/channel-audit.json" },
];

// Addendum GPU files
const GPU_FILES = [
  "masked-stem-7b.json",
  "masked-stem-14b.json",
  "masked-stem-phi4.json",
  "masked-stem-mistral-7b.json",
  "masked-stem-populations.json",
  "choices-only-local-lm.json",
  "choices-only-local-lm-14b.json",
  "information-ladder.json",
];

for (const f of GPU_FILES) {
  const localPath = `exports/addendum-gpu/${f}`;
  if (existsSync(join(ROOT, localPath))) {
    DATA_FILES.push({ local: localPath, s3Key: `data/gpu/${f}` });
  }
}

// Addendum files
const ADDENDUM_FILES = [
  "e1-witness-dependence.json",
  "apriori-cues-extended.json",
  "power-by-cell.json",
];

for (const f of ADDENDUM_FILES) {
  const localPath = `exports/addendum/${f}`;
  if (existsSync(join(ROOT, localPath))) {
    DATA_FILES.push({ local: localPath, s3Key: `data/addendum/${f}` });
  }
}

const bucket = process.argv[2];

if (!bucket) {
  console.error("Usage: node scripts/upload-data.mjs <s3-bucket-name>");
  console.error("");
  console.error("Get the bucket name from CDK output: DataBucketName");
  process.exit(1);
}

console.log(`Uploading ${DATA_FILES.length} files to s3://${bucket}/`);

let uploaded = 0;
let skipped = 0;

for (const { local, s3Key } of DATA_FILES) {
  const localPath = join(ROOT, local);
  if (!existsSync(localPath)) {
    console.log(`  SKIP ${local} (not found)`);
    skipped++;
    continue;
  }
  console.log(`  ${local} → s3://${bucket}/${s3Key}`);
  execSync(`aws s3 cp "${localPath}" "s3://${bucket}/${s3Key}" --content-type application/json`, {
    stdio: "inherit",
  });
  uploaded++;
}

console.log(`\nDone: ${uploaded} uploaded, ${skipped} skipped.`);
