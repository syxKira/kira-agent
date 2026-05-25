import type { KiraEvent } from "../lib/types";

export const stage10LongAssistantText =
  "Kira can keep long local workflow answers readable by wrapping dense paragraphs, paths, and identifiers without pushing controls out of the workbench shell. ".repeat(8);

export const stage10LongToolResult = {
  status: "ok",
  files: Array.from({ length: 16 }, (_, index) => ({
    path: `/tmp/project/packages/module-${index}/src/really-long-file-name-for-layout-smoke-${index}.ts`,
    lines: [index + 1, index + 48],
    summary: "Deterministic Stage 10 visual smoke data for bounded tool cards.",
  })),
};

export function stage10VisualEvents(): KiraEvent[] {
  return [
    event("thinking_delta", 1, { text: "Inspecting local context without exposing hidden thinking as answer text." }),
    event("tool_start", 2, { name: "project.search", message: "Searching cited project snippets" }),
    event("tool_result", 3, {
      name: "project.search",
      status: "ok",
      result: stage10LongToolResult,
      metadata: { content_type: "application/json", truncated: true },
    }),
    event("retry", 4, { message: "Retrying provider stream after transient local error", attempt: 2 }),
    event("side_effect_reused", 5, { name: "project.search", status: "reused", result: { idempotency_key: "stage10-smoke" } }),
    event("checkpoint", 6, { checkpoint_id: "stage10-checkpoint" }),
    event("text_delta", 7, { text: stage10LongAssistantText }),
    event("done", 8, { message: "Stage 10 fixture completed" }),
  ];
}

function event(type: KiraEvent["type"], seq: number, data: KiraEvent["data"]): KiraEvent {
  return {
    type,
    thread_id: "stage10-visual-smoke",
    seq,
    data,
  };
}
