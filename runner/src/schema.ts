import { z } from "zod";

const Operation = z.enum([
  "retrieve",
  "execute",
  "bind",
  "distinguish",
  "explain",
  "transfer",
]);

const ResponseType = z.enum([
  "selected",
  "numeric",
  "griddable",
  "matching",
  "constructed",
]);

const ChannelId = z.enum([
  "item-cues",
  "partial-input",
  "instruction-only",
  "unbound-exec",
]);

export const ItemSchema = z
  .object({
    id: z.string().min(1),
    corpus: z.string().min(1),
    authority: z.string().min(1),
    claim: z.string().min(1),
    stem: z.string().min(1),
    choices: z.record(z.string(), z.string()).optional(),
    key: z.string().min(1),
    responseType: ResponseType,
    figure: z
      .object({
        kind: z.enum(["table", "graph", "diagram"]),
        transcription: z.string().optional(),
      })
      .optional(),
    clusterId: z.string().optional(),
    percentCorrect: z.number().min(0).max(100).optional(),
    sourceUrl: z.string().min(1),
    licenseNote: z.string().min(1),
    contentDomain: z.string().optional(),
    grade: z.string().optional(),
    year: z.string().optional(),
    figureDependent: z.boolean().optional(),
    transcriptionMethod: z.string().optional(),
    pagePointer: z.string().optional(),
    officialTag: z.string().optional(),
    role: z.enum(["target", "retrieval-pool"]).optional(),
    stemRestored: z.boolean().optional(),
    restorationNote: z.string().optional(),
  })
  .superRefine((item, ctx) => {
    if (item.responseType === "selected") {
      if (!item.choices || Object.keys(item.choices).length < 2) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: "selected-response items need at least two choices",
        });
      }
    }
    if (item.role === "retrieval-pool") {
      return;
    }
  });

export const ClaimSchema = z.object({
  authority: z.string().min(1),
  code: z.string().min(1),
  text: z.string().min(1),
  operationalization: z.string().min(1),
  operations: z.array(Operation).min(1),
  sourceUrl: z.string().optional(),
});

export const AprioriRuleSchema = z.object({
  id: z.string().min(1),
  channel: ChannelId,
  lacks: z.array(Operation).min(1),
  description: z.string().min(1),
  citation: z.string().min(1),
  appliesTo: z.array(ResponseType).min(1),
});

export const ClaimsFileSchema = z.union([
  z.array(ClaimSchema),
  z.object({ claims: z.array(ClaimSchema) }),
]);

export const RulesFileSchema = z.union([
  z.array(AprioriRuleSchema),
  z.object({ rules: z.array(AprioriRuleSchema) }),
]);

export const RequirementCellSchema = z.object({
  itemId: z.string().min(1),
  operation: Operation,
  value: z.union([z.literal(0), z.literal(1)]),
  witness: z
    .object({
      programId: z.string(),
      trace: z.array(z.string()),
    })
    .optional(),
  searched: z.array(z.string()),
  attempted: z.boolean(),
  review: z.enum(["machine", "human-confirmed", "disputed"]),
});

export type ItemInput = z.infer<typeof ItemSchema>;
export type ClaimInput = z.infer<typeof ClaimSchema>;
export type RuleInput = z.infer<typeof AprioriRuleSchema>;
