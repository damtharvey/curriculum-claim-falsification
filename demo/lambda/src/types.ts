/**
 * Shared types extracted from runner/src/types.ts for the Lambda.
 * Kept minimal — only what the API needs.
 */

export type Operation =
  | "retrieve"
  | "execute"
  | "bind"
  | "distinguish"
  | "explain"
  | "transfer";

export type ResponseType =
  | "selected"
  | "numeric"
  | "griddable"
  | "matching"
  | "constructed";

export type ChannelId =
  | "item-cues"
  | "partial-input"
  | "instruction-only"
  | "unbound-exec";

export interface Item {
  id: string;
  corpus: string;
  authority: string;
  claim: string;
  stem: string;
  choices?: Record<string, string>;
  key: string;
  responseType: ResponseType;
  figure?: { kind: "table" | "graph" | "diagram"; transcription?: string };
  clusterId?: string;
  percentCorrect?: number;
  sourceUrl: string;
  licenseNote: string;
  contentDomain?: string;
  grade?: string;
  year?: string;
  figureDependent?: boolean;
  role?: "target" | "retrieval-pool";
}

export interface AprioriRule {
  id: string;
  channel: ChannelId;
  lacks: Operation[];
  description: string;
  citation: string;
  appliesTo: ResponseType[];
}

export interface SurfaceFeatures {
  optionLengths: Record<string, number>;
  longest: string[];
  absoluteTerms: Record<string, boolean>;
  stemOverlap: Record<string, number>;
  stemNumbersRepeated: Record<string, boolean>;
  numericValues: Record<string, number | null>;
  middleValueKeys: string[];
  positions: string[];
}

export interface ItemView {
  itemId: string;
  channel: ChannelId;
  programId: string;
  stem?: string;
  choices?: Record<string, string>;
  numbers?: number[];
  numberTokens?: string[];
  surface?: SurfaceFeatures;
}

export interface ProgramResult {
  answer: string | null;
  skipped: boolean;
  skipReason?: string;
  trace: string[];
}

export type ProgramFn = (
  view: ItemView,
  item: Item,
  rule: AprioriRule,
) => ProgramResult;

/** API response for POST /api/run-rules */
export interface RunRulesResponse {
  itemId: string;
  stem: string;
  key: string;
  results: {
    ruleId: string;
    ruleName: string;
    channel: ChannelId;
    lacks: Operation[];
    answer: string | null;
    correct: boolean | null;
    skipped: boolean;
    skipReason?: string;
    trace: string[];
  }[];
}

/** Summary stats for GET /api/stats */
export interface DemoStats {
  totalItems: number;
  totalWitnesses: number;
  corpora: string[];
  authorities: string[];
  responseTypes: Record<string, number>;
}
