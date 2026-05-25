import type { KiraEvent } from "../lib/types";

export function stage13ChunkedAnswerEvents(): KiraEvent[] {
  return [
    event("text_delta", 1, { text: "Kira " }),
    event("text_delta", 2, { text: "keeps " }),
    event("text_delta", 3, { text: "one answer." }),
    event("done", 4, { message: "Completed" }),
  ];
}

export function stage13InterleavedProcessEvents(): KiraEvent[] {
  return [
    event("thinking_delta", 1, { text: "Plan without exposing hidden thinking." }),
    event("tool_start", 2, { name: "project.search", call_id: "call-1", message: "Searching cited snippets" }),
    event("tool_result", 3, {
      name: "project.search",
      call_id: "call-1",
      status: "ok",
      result: { snippet: "Tool output belongs to process, not the answer." },
    }),
    event("checkpoint", 4, { checkpoint_id: "cp-1", message: "Checkpoint saved" }),
    event("retry", 5, { attempt: 2, message: "Retrying transient provider stream" }),
    event("text_delta", 6, { text: "Visible answer only." }),
    event("done", 7, { message: "Completed" }),
  ];
}

export function stage13HitlEvents(): KiraEvent[] {
  return [
    event("interrupt", 1, {
      interrupt_id: "interrupt-1",
      kind: "approval",
      title: "Approve workflow step",
      body: "Approve this deterministic fixture step.",
    }),
    event("resume", 2, { interrupt_id: "interrupt-1", decision: "approve" }),
    event("text_delta", 3, { text: "Approval received." }),
    event("done", 4, { message: "Completed" }),
  ];
}

export function stage13ErrorEvents(): KiraEvent[] {
  return [
    event("text_delta", 1, { text: "Partial answer before failure." }),
    event("error", 2, { message: "Provider stream failed", failure_class: "provider_stream_error" }),
  ];
}

function event(type: KiraEvent["type"], seq: number, data: KiraEvent["data"]): KiraEvent {
  return {
    type,
    thread_id: "stage13-turn",
    seq,
    data,
  };
}
