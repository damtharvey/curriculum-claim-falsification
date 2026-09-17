export interface ModelBackend {
  name: string;
  available: boolean;
  complete(prompt: string): Promise<string>;
}

/**
 * Bedrock/LLM is allowed only for choices-only, reference solver critique,
 * labeler, and constructed-response grading. Stem-only LM is forbidden.
 * No fake CPU path. If credentials are missing, the backend is unavailable.
 */
export function bedrockBackend(): ModelBackend {
  const key =
    process.env.AWS_ACCESS_KEY_ID ||
    process.env.BEDROCK_API_KEY ||
    process.env.ANTHROPIC_API_KEY;
  if (!key) {
    return {
      name: "bedrock-stub",
      available: false,
      async complete(): Promise<string> {
        throw new Error("Bedrock unavailable: no AWS_ACCESS_KEY_ID / BEDROCK_API_KEY / ANTHROPIC_API_KEY");
      },
    };
  }
  return {
    name: "bedrock-env",
    available: true,
    async complete(prompt: string): Promise<string> {
      throw new Error(
        `Bedrock credentials present but the live client is not wired in v1 (${prompt.slice(0, 40)}…). Census local channels do not need it.`,
      );
    },
  };
}

export async function choicesOnlyModel(
  backend: ModelBackend,
  choices: Record<string, string>,
): Promise<string | null> {
  if (!backend.available) return null;
  const prompt = `You see only these multiple-choice options, not the question. Pick the letter of the option that looks most likely to be correct. Reply with a single letter.\n${Object.entries(choices)
    .map(([k, v]) => `${k}. ${v}`)
    .join("\n")}`;
  const out = await backend.complete(prompt);
  const m = out.trim().match(/[A-Da-d]/);
  return m ? m[0]!.toUpperCase() : null;
}
