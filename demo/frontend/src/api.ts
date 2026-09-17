/**
 * API client — talks to the Lambda via CloudFront or local proxy.
 */

const BASE = "";

export interface ItemSummary {
  id: string;
  corpus: string;
  authority: string;
  claim: string;
  stem: string;
  choices?: Record<string, string>;
  key: string;
  responseType: string;
  percentCorrect?: number;
  contentDomain?: string;
  grade?: string;
  year?: string;
}

export interface ItemDetail extends ItemSummary {
  witnesses: WitnessRecord[];
}

export interface WitnessRecord {
  itemId: string;
  claim: string;
  authority: string;
  operation: string;
  programId: string;
  channel: string;
  howObtained: string;
  answer: string;
  key: string;
  trace: string[];
  itemStemPreview: string;
  beatsChance: boolean;
}

export interface RuleDefinition {
  id: string;
  channel: string;
  lacks: string[];
  description: string;
  citation: string;
  appliesTo: string[];
}

export interface RuleResult {
  ruleId: string;
  ruleName: string;
  channel: string;
  lacks: string[];
  answer: string | null;
  correct: boolean | null;
  skipped: boolean;
  skipReason?: string;
  trace: string[];
}

export interface RunRulesResponse {
  itemId: string;
  stem: string;
  key: string;
  results: RuleResult[];
}

export interface DemoStats {
  totalItems: number;
  totalWitnesses: number;
  corpora: string[];
  authorities: string[];
  responseTypes: Record<string, number>;
}

export interface PagedItems {
  total: number;
  page: number;
  pageSize: number;
  items: ItemSummary[];
}

async function fetchJson<T>(url: string, init?: RequestInit): Promise<T> {
  const resp = await fetch(`${BASE}${url}`, init);
  if (!resp.ok) {
    const text = await resp.text().catch(() => "");
    throw new Error(`${resp.status}: ${text}`);
  }
  return resp.json() as Promise<T>;
}

export function getStats(): Promise<DemoStats> {
  return fetchJson("/api/stats");
}

export function getItems(params: Record<string, string> = {}): Promise<PagedItems> {
  const qs = new URLSearchParams(params).toString();
  return fetchJson(`/api/items${qs ? `?${qs}` : ""}`);
}

export function getItem(itemId: string): Promise<ItemDetail> {
  return fetchJson(`/api/items/${encodeURIComponent(itemId)}`);
}

export function getRules(): Promise<RuleDefinition[]> {
  return fetchJson("/api/rules");
}

export function runRules(itemId: string): Promise<RunRulesResponse> {
  return fetchJson("/api/run-rules", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ itemId }),
  });
}
