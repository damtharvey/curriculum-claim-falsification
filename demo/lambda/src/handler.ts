/**
 * Lambda handler — serves the interactive API for the CCF demo.
 *
 * Routes:
 *   GET  /api/items          — list items (paginated, filterable)
 *   GET  /api/items/{itemId} — single item detail
 *   GET  /api/rules          — list a priori rules
 *   GET  /api/stats          — summary stats
 *   POST /api/run-rules      — run all a priori rules on a single item
 */

import type { APIGatewayProxyEventV2, APIGatewayProxyResultV2 } from "aws-lambda";
import { loadCellTable, loadItems, loadRuleChance, loadRules, loadWitnesses } from "./data.js";
import { answersMatch, viewFor } from "./channels.js";
import { programs } from "./programs.js";
import type { Item, RunRulesResponse } from "./types.js";

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

async function handleGetItems(event: APIGatewayProxyEventV2) {
  const items = await loadItems();
  const params = event.queryStringParameters ?? {};

  let filtered = items;
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
    items: slice.map(sanitizeItem),
  });
}

async function handleGetItem(itemId: string) {
  const items = await loadItems();
  const item = items.find((i) => i.id === itemId);
  if (!item) return json({ error: "Item not found" }, 404);

  // Also load witnesses for this item
  const witnesses = (await loadWitnesses()) as { itemId: string }[];
  const itemWitnesses = witnesses.filter((w) => w.itemId === itemId);

  return json({
    ...sanitizeItem(item),
    witnesses: itemWitnesses,
  });
}

async function handleGetRules() {
  const rules = await loadRules();
  return json(rules);
}

async function handleGetStats() {
  const items = await loadItems();
  const witnesses = (await loadWitnesses()) as unknown[];
  const corpora = [...new Set(items.map((i) => i.corpus))].sort();
  const authorities = [...new Set(items.map((i) => i.authority))].sort();
  const responseTypes: Record<string, number> = {};
  for (const item of items) {
    responseTypes[item.responseType] = (responseTypes[item.responseType] ?? 0) + 1;
  }

  return json({
    totalItems: items.length,
    totalWitnesses: witnesses.length,
    corpora,
    authorities,
    responseTypes,
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
