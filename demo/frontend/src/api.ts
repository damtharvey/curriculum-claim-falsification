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
  witnessCount: number;
  witnessPrograms: number;
  channels: string[];
}

export interface ItemDetail extends ItemSummary {
  sourceUrl?: string;
  figureDependent?: boolean;
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
  witnessedItems: number;
  ruleCount: number;
  corpora: string[];
  authorities: string[];
  claims: { authority: string; claim: string; items: number }[];
  channels: string[];
  responseTypes: Record<string, number>;
}

export interface Claim {
  authority: string;
  code: string;
  text: string;
  operationalization: string;
  operations: string[];
  sourceUrl?: string;
  items: number;
}

export interface ClaimFile {
  authority: string;
  note?: string;
  file: string;
  claims: Claim[];
}

export interface DataFile {
  key: string;
  size: number;
  lastModified?: string;
}

export interface DemoConfig {
  dataBucket: string | null;
  localDataRoot: string | null;
  region: string | null;
  functionName: string | null;
  memoryMb: number | null;
  nodeVersion: string;
  routes: { method: string; path: string; note: string }[];
  dataFiles: DataFile[];
}

export const OPERATIONS = ["retrieve", "execute", "bind", "distinguish", "explain", "transfer"] as const;

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

export function getClaims(): Promise<ClaimFile[]> {
  return fetchJson("/api/claims");
}

export function getConfig(): Promise<DemoConfig> {
  return fetchJson("/api/config");
}

export function runRules(itemId: string): Promise<RunRulesResponse> {
  return fetchJson("/api/run-rules", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ itemId }),
  });
}
