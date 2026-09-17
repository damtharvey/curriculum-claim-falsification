/**
 * Lambda handler — serves the interactive API for the CCF demo.
 *
 * Routes:
 *   GET  /api/items          — list items (paginated, filterable)
 *   GET  /api/items/{itemId} — single item detail
 *   GET  /api/rules          — list a priori rules
 *   GET  /api/claims         — one entry per claims/<authority>.json
 *   GET  /api/stats          — summary stats
 *   GET  /api/config         — data files in the bucket, routes, runtime
 *   POST /api/run-rules      — run all a priori rules on a single item
 */

import type { APIGatewayProxyEventV2, APIGatewayProxyResultV2 } from "aws-lambda";
import { listDataFiles, loadClaims, loadItems, loadRules, loadWitnesses } from "./data.js";
import { answersMatch, viewFor } from "./channels.js";
import { programs } from "./programs.js";
import type { DemoStats, Item, RunRulesResponse } from "./types.js";

function json(body: unknown, statusCode = 200): APIGatewayProxyResultV2 {
  return {
    statusCode,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  };
}

function sanitizeItem(item: Item) {
  return {
    id: item.id,
    corpus: item.corpus,
    authority: item.authority,
    claim: item.claim,
    stem: item.stem,
    choices: item.choices,
    key: item.key,
    responseType: item.responseType,
    figure: item.figure,
    percentCorrect: item.percentCorrect,
    contentDomain: item.contentDomain,
    grade: item.grade,
    year: item.year,
  };
}

interface WitnessRow {
  itemId: string;
  channel: string;
  programId: string;
}

/** itemId → witness rows, so the list can show counts without a second call. */
async function witnessIndex(): Promise<Map<string, WitnessRow[]>> {
  const rows = (await loadWitnesses()) as WitnessRow[];
  const index = new Map<string, WitnessRow[]>();
  for (const w of rows) {
    const list = index.get(w.itemId);
    if (list) list.push(w);
    else index.set(w.itemId, [w]);
  }
  return index;
}

function witnessSummary(rows: WitnessRow[] | undefined) {
  const list = rows ?? [];
  return {
    witnessCount: list.length,
    witnessPrograms: [...new Set(list.map((w) => w.programId))].length,
    channels: [...new Set(list.map((w) => w.channel))].sort(),
  };
}

async function handleGetItems(event: APIGatewayProxyEventV2) {
  const items = await loadItems();
  const index = await witnessIndex();
  const params = event.queryStringParameters ?? {};

  let filtered = items;
  if (params.witnessed === "1") filtered = filtered.filter((i) => index.has(i.id));
  if (params.channel) {
    const ch = params.channel;
    filtered = filtered.filter((i) => (index.get(i.id) ?? []).some((w) => w.channel === ch));
  }
  if (params.corpus) filtered = filtered.filter((i) => i.corpus === params.corpus);
  if (params.authority) filtered = filtered.filter((i) => i.authority === params.authority);
  if (params.claim) filtered = filtered.filter((i) => i.claim === params.claim);
  if (params.responseType) filtered = filtered.filter((i) => i.responseType === params.responseType);
  if (params.search) {
    const q = params.search.toLowerCase();
    filtered = filtered.filter(
      (i) =>
        i.id.toLowerCase().includes(q) ||
        i.stem.toLowerCase().includes(q) ||
        i.claim.toLowerCase().includes(q),
    );
  }

  const page = Math.max(1, Number(params.page) || 1);
  const pageSize = Math.min(100, Math.max(1, Number(params.pageSize) || 25));
  const start = (page - 1) * pageSize;
  const slice = filtered.slice(start, start + pageSize);

  return json({
    total: filtered.length,
    page,
    pageSize,
    items: slice.map((i) => ({ ...sanitizeItem(i), ...witnessSummary(index.get(i.id)) })),
  });
}

async function handleGetItem(itemId: string) {
  const items = await loadItems();
  const item = items.find((i) => i.id === itemId);
  if (!item) return json({ error: "Item not found" }, 404);

  const itemWitnesses = (await witnessIndex()).get(itemId) ?? [];

  return json({
    ...sanitizeItem(item),
    ...witnessSummary(itemWitnesses),
    sourceUrl: item.sourceUrl,
    figureDependent: item.figureDependent,
    witnesses: itemWitnesses,
  });
}

async function handleGetRules() {
  const rules = await loadRules();
  return json(rules);
}

async function handleGetClaims() {
  const claims = await loadClaims();
  const items = await loadItems();
  const counts = new Map<string, number>();
  for (const i of items) {
    const k = `${i.authority}/${i.claim}`;
    counts.set(k, (counts.get(k) ?? 0) + 1);
  }
  return json(
    claims.map((f) => ({
      ...f,
      claims: f.claims.map((c) => ({ ...c, items: counts.get(`${c.authority}/${c.code}`) ?? 0 })),
    })),
  );
}

async function handleGetStats() {
  const items = await loadItems();
  const witnesses = (await loadWitnesses()) as WitnessRow[];
  const rules = await loadRules();
  const corpora = [...new Set(items.map((i) => i.corpus))].sort();
  const authorities = [...new Set(items.map((i) => i.authority))].sort();
  const responseTypes: Record<string, number> = {};
  const claimCounts = new Map<string, number>();
  for (const item of items) {
    responseTypes[item.responseType] = (responseTypes[item.responseType] ?? 0) + 1;
    const k = `${item.authority}\u0000${item.claim}`;
    claimCounts.set(k, (claimCounts.get(k) ?? 0) + 1);
  }

  const stats: DemoStats = {
    totalItems: items.length,
    totalWitnesses: witnesses.length,
    witnessedItems: new Set(witnesses.map((w) => w.itemId)).size,
    ruleCount: rules.length,
    corpora,
    authorities,
    claims: [...claimCounts.entries()]
      .map(([k, n]) => {
        const [authority, claim] = k.split("\u0000") as [string, string];
        return { authority, claim, items: n };
      })
      .sort((a, b) => a.authority.localeCompare(b.authority) || a.claim.localeCompare(b.claim)),
    channels: [...new Set(rules.map((r) => r.channel))].sort(),
    responseTypes,
  };
  return json(stats);
}

async function handleGetConfig() {
  const files = await listDataFiles();
  return json({
    dataBucket: process.env.DATA_BUCKET ?? null,
    localDataRoot: process.env.LOCAL_DATA_ROOT ?? null,
    region: process.env.AWS_REGION ?? null,
    functionName: process.env.AWS_LAMBDA_FUNCTION_NAME ?? null,
    memoryMb: Number(process.env.AWS_LAMBDA_FUNCTION_MEMORY_SIZE) || null,
    nodeVersion: process.version,
    routes: [
      { method: "GET", path: "/api/stats", note: "counts for the header strip" },
      { method: "GET", path: "/api/items", note: "paged; filter by authority, claim, channel, witnessed, search" },
      { method: "GET", path: "/api/items/{itemId}", note: "item plus witness rows" },
      { method: "GET", path: "/api/rules", note: "a priori rules" },
      { method: "GET", path: "/api/claims", note: "claims per authority with item counts" },
      { method: "GET", path: "/api/config", note: "this response" },
      { method: "POST", path: "/api/run-rules", note: "score one item against every rule" },
    ],
    dataFiles: files,
  });
}

async function handleRunRules(event: APIGatewayProxyEventV2) {
  if (!event.body) return json({ error: "Missing body" }, 400);
  const body = JSON.parse(event.body) as { itemId?: string };
  if (!body.itemId) return json({ error: "Missing itemId" }, 400);

  const items = await loadItems();
  const item = items.find((i) => i.id === body.itemId);
  if (!item) return json({ error: "Item not found" }, 404);

  const rules = await loadRules();
  const results: RunRulesResponse["results"] = [];

  for (const rule of rules) {
    if (!rule.appliesTo.includes(item.responseType)) {
      results.push({
        ruleId: rule.id,
        ruleName: rule.description.split(".")[0] ?? rule.id,
        channel: rule.channel,
        lacks: rule.lacks,
        answer: null,
        correct: null,
        skipped: true,
        skipReason: `responseType ${item.responseType} not in ${rule.appliesTo.join(",")}`,
        trace: ["not applicable"],
      });
      continue;
    }

    const view = viewFor(rule, item);
    const fn = programs[rule.id];
    if (!fn) {
      results.push({
        ruleId: rule.id,
        ruleName: rule.description.split(".")[0] ?? rule.id,
        channel: rule.channel,
        lacks: rule.lacks,
        answer: null,
        correct: null,
        skipped: true,
        skipReason: "program not implemented",
        trace: [],
      });
      continue;
    }

    const result = fn(view, item, rule);
    const correct =
      result.skipped || result.answer === null
        ? null
        : answersMatch(item.key, result.answer);

    results.push({
      ruleId: rule.id,
      ruleName: rule.description.split(".")[0] ?? rule.id,
      channel: rule.channel,
      lacks: rule.lacks,
      answer: result.answer,
      correct,
      skipped: result.skipped,
      skipReason: result.skipReason,
      trace: result.trace,
    });
  }

  const response: RunRulesResponse = {
    itemId: item.id,
    stem: item.stem,
    key: item.key,
    results,
  };

  return json(response);
}

export async function handler(
  event: APIGatewayProxyEventV2,
): Promise<APIGatewayProxyResultV2> {
  try {
    const path = event.rawPath;
    const method = event.requestContext.http.method;

    if (method === "GET" && path === "/api/stats") {
      return await handleGetStats();
    }
    if (method === "GET" && path === "/api/rules") {
      return await handleGetRules();
    }
    if (method === "GET" && path === "/api/claims") {
      return await handleGetClaims();
    }
    if (method === "GET" && path === "/api/config") {
      return await handleGetConfig();
    }
    if (method === "GET" && path.startsWith("/api/items/")) {
      const itemId = decodeURIComponent(path.replace("/api/items/", ""));
      return await handleGetItem(itemId);
    }
    if (method === "GET" && path === "/api/items") {
      return await handleGetItems(event);
    }
    if (method === "POST" && path === "/api/run-rules") {
      return await handleRunRules(event);
    }

    return json({ error: "Not found", path }, 404);
  } catch (err) {
    console.error("Handler error:", err);
    return json({ error: "Internal server error" }, 500);
  }
}
