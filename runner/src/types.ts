/**
 * Frozen contracts A, B, C from temp/CHAT-hackathon-plan.md Section 5.
 * Extra optional fields are allowed on items so ingestion can keep content
 * domain, grade, and restoration notes without changing the join keys.
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

export type ReviewStatus = "machine" | "human-confirmed" | "disputed";

/** Contract A */
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
  /** Non-contract extras kept for QA. */
  contentDomain?: string;
  grade?: string;
  year?: string;
  figureDependent?: boolean;
  transcriptionMethod?: string;
  pagePointer?: string;
  officialTag?: string;
  role?: "target" | "retrieval-pool";
  stemRestored?: boolean;
  restorationNote?: string;
}

/** Contract B */
export interface Claim {
  authority: string;
  code: string;
  text: string;
  operationalization: string;
  operations: Operation[];
  sourceUrl?: string;
}

export interface AprioriRule {
  id: string;
  channel: ChannelId;
  lacks: Operation[];
  description: string;
  citation: string;
  appliesTo: ResponseType[];
}

/** Contract C */
export interface RequirementCell {
  itemId: string;
  operation: Operation;
  value: 0 | 1;
  witness?: { programId: string; trace: string[] };
  searched: string[];
  attempted: boolean;
  review: ReviewStatus;
}

export interface WitnessRecord {
  itemId: string;
  claim: string;
  authority: string;
  operation: Operation;
  programId: string;
  channel: ChannelId;
  howObtained: "a-priori" | "fitted-held-out";
  keyWasAvailable: false;
  answer: string;
  key: string;
  trace: string[];
  itemStemPreview: string;
  beatsChance: boolean;
}

export interface ComparisonRow {
  claim: string;
  authority: string;
  nItems: number;
  nAttempted: number;
  bypassRate: number;
  chanceRate: number;
  randomBaseline: number;
  complexity: { featureCount: number; description: string };
  ci95: [number, number];
  nWitnesses: number;
  nPositiveControls: number;
  discriminating: boolean;
  percentCorrectRelation?: {
    bypassableMean?: number;
    nonBypassableMean?: number;
  };
  minObservablePassRate?: number | null;
  minDetectableTrueRate80?: number | null;
  nullNote?: string;
}

export interface RuleChanceRow {
  programId: string;
  claim: string;
  authority: string;
  nScored: number;
  nCorrect: number;
  passRate: number;
  chanceRate: number;
  ci95: [number, number];
  beatsChance: boolean;
  witnessEligible: boolean;
  heldOut?: boolean;
  trainSlice?: string;
  evalSlice?: string;
  note: string;
}

export interface FittedHeldOutRow {
  programId: string;
  trainSlice: string;
  evalSlice: string;
  nTrain: number;
  nScored: number;
  nCorrect: number;
  passRate: number;
  chanceRate: number;
  randomBaseline: number;
  ci95: [number, number];
  beatsChance: boolean;
  witnessEligible: boolean;
  note: string;
}

/** Channel view: the published key is unreachable. */
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

export interface TrialRecord {
  trialId: string;
  itemId: string;
  programId: string;
  channel: ChannelId;
  answer: string | null;
  correct: boolean | null;
  skipped: boolean;
  skipReason?: string;
  trace: string[];
  timestamp: string;
}

export interface DisputeRecord {
  itemId: string;
  publishedKey: string;
  solverAnswer: string;
  solverTrace: string[];
  status: "open" | "resolved-published" | "resolved-solver";
}

export const OPERATIONS: Operation[] = [
  "retrieve",
  "execute",
  "bind",
  "distinguish",
  "explain",
  "transfer",
];

export const RESPONSE_TYPES: ResponseType[] = [
  "selected",
  "numeric",
  "griddable",
  "matching",
  "constructed",
];

export const CHANNEL_IDS: ChannelId[] = [
  "item-cues",
  "partial-input",
  "instruction-only",
  "unbound-exec",
];

export const WITNESS_DEFINITION =
  "A witness is a program that is admitted under the a priori or held-out fitted rules, that never receives the published key, that lacks at least one operation the item's tag names as necessary, and that nevertheless scores as correct under the published scoring rule. A witness refutes the claim that a pass on that item requires the tagged operation. Failure of searched programs does not certify the tag.";
