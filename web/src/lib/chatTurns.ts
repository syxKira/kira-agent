import { getEventText, getTimestampLabel, isAnswerTextEvent, isFixtureToolPreview } from "./timeline";
import type { KiraEvent, TranscriptMessage } from "./types";

export type ChatMessageViewModel = {
  id: string;
  role: "user" | "assistant";
  text: string;
  timestamp: string;
  sourceMessage?: TranscriptMessage;
};

export type ReasoningGroupViewModel = {
  id: string;
  events: KiraEvent[];
};

export type ToolActivityViewModel = {
  id: string;
  start?: KiraEvent;
  result?: KiraEvent;
};

export type RunStatusViewModel = {
  id: string;
  kind: "retry" | "checkpoint" | "interrupt" | "resume" | "error";
  label: string;
  message: string;
  timestamp: string;
  event: KiraEvent;
  runState?: ChatRunState;
};

export type ChatTurnItem =
  | { kind: "reasoning"; key: string; reasoning: ReasoningGroupViewModel }
  | { kind: "tool"; key: string; tool: ToolActivityViewModel }
  | { kind: "status"; key: string; status: RunStatusViewModel };

export type ChatRunState = "idle" | "streaming" | "waiting" | "completed" | "error" | "cancelled";

export type ChatTurnViewModel = {
  id: string;
  user?: ChatMessageViewModel;
  assistant?: ChatMessageViewModel;
  reasoning: ReasoningGroupViewModel[];
  tools: ToolActivityViewModel[];
  statuses: RunStatusViewModel[];
  items: ChatTurnItem[];
  runState: ChatRunState;
};

export type BuildChatTurnsInput = {
  transcriptMessages: TranscriptMessage[];
  activePrompt: string | null;
  events: KiraEvent[];
  threadId?: string | null;
  turnId?: string | null;
};

export function buildChatTurns({
  transcriptMessages,
  activePrompt,
  events,
  threadId,
  turnId,
}: BuildChatTurnsInput): ChatTurnViewModel[] {
  const turns: ChatTurnViewModel[] = [];
  const byId = new Map<string, ChatTurnViewModel>();
  const currentTurnId = turnId || threadId || events[0]?.thread_id || "active";

  function ensureTurn(id: string): ChatTurnViewModel {
    const existing = byId.get(id);
    if (existing) {
      return existing;
    }
    const turn: ChatTurnViewModel = {
      id,
      reasoning: [],
      tools: [],
      statuses: [],
      items: [],
      runState: "idle",
    };
    byId.set(id, turn);
    turns.push(turn);
    return turn;
  }

  transcriptMessages.forEach((message, index) => {
    const text = transcriptVisibleText(message);
    if (!text) {
      return;
    }

    const turn = ensureTurn(transcriptTurnId(message, index));
    if (message.role === "user") {
      mergeChatMessage(turn, "user", {
        id: message.id,
        role: "user",
        text,
        timestamp: getTimestampLabel(message.created_at),
        sourceMessage: message,
      });
      return;
    }

    if (message.role === "assistant") {
      mergeChatMessage(turn, "assistant", {
        id: message.id,
        role: "assistant",
        text,
        timestamp: getTimestampLabel(message.created_at),
        sourceMessage: message,
      });
      return;
    }

    const status = transcriptStatus(message, text);
    turn.statuses.push(status);
    turn.items.push({ kind: "status", key: status.id, status });
  });

  const trimmedPrompt = activePrompt?.trim();
  if (trimmedPrompt) {
    const turn = ensureTurn(currentTurnId);
    if (!turn.user || turn.user.sourceMessage || turn.user.text !== trimmedPrompt) {
      turn.user = {
        id: `${currentTurnId}-active-user`,
        role: "user",
        text: trimmedPrompt,
        timestamp: "",
      };
    }
    if (turn.runState === "idle") {
      turn.runState = "streaming";
    }
  }

  for (const event of events) {
    const turn = ensureTurn(eventTurnId(event, currentTurnId));
    applyEventToTurn(turn, event);
  }

  return turns.filter((turn) => turn.user || turn.assistant || turn.items.length > 0);
}

function applyEventToTurn(turn: ChatTurnViewModel, event: KiraEvent) {
  if (event.type === "text_delta") {
    if (isAnswerTextEvent(event)) {
      appendAssistantText(turn, event);
    } else if (isFixtureToolPreview(event)) {
      addToolResult(turn, event);
    }
    return;
  }

  if (event.type === "thinking_delta") {
    addReasoningEvent(turn, event);
    return;
  }

  if (event.type === "tool_start") {
    addToolStart(turn, event);
    return;
  }

  if (event.type === "tool_result" || event.type === "side_effect_reused") {
    addToolResult(turn, event);
    return;
  }

  if (event.type === "done") {
    turn.runState = "completed";
    return;
  }

  if (event.type === "error") {
    const cancelled = isCancelledEvent(event);
    turn.runState = cancelled ? "cancelled" : "error";
    addStatus(turn, {
      event,
      kind: "error",
      label: cancelled ? "Cancelled" : "Error",
      fallback: cancelled ? "Run cancelled" : "Run failed",
      runState: turn.runState,
    });
    return;
  }

  if (event.type === "interrupt") {
    turn.runState = "waiting";
    addStatus(turn, { event, kind: "interrupt", label: "Waiting", fallback: formatEventValue(event.data.title, "Human input required") });
    return;
  }

  if (event.type === "resume") {
    turn.runState = "streaming";
    addStatus(turn, { event, kind: "resume", label: "Resumed", fallback: `Decision: ${formatEventValue(event.data.decision, "submitted")}` });
    return;
  }

  if (event.type === "retry") {
    addStatus(turn, { event, kind: "retry", label: "Retry", fallback: "Retrying step" });
    return;
  }

  if (event.type === "checkpoint") {
    addStatus(turn, { event, kind: "checkpoint", label: "Checkpoint", fallback: "Checkpoint saved" });
  }
}

function appendAssistantText(turn: ChatTurnViewModel, event: KiraEvent) {
  const text = getEventText(event, "");
  if (!text) {
    return;
  }
  const timestamp = getTimestampLabel(event.data.timestamp);
  if (!turn.assistant) {
    turn.assistant = {
      id: `${event.thread_id}-assistant`,
      role: "assistant",
      text,
      timestamp,
    };
    return;
  }
  turn.assistant = {
    ...turn.assistant,
    text: `${turn.assistant.text}${text}`,
    timestamp: timestamp || turn.assistant.timestamp,
  };
}

function addReasoningEvent(turn: ChatTurnViewModel, event: KiraEvent) {
  const previousItem = turn.items[turn.items.length - 1];
  if (previousItem?.kind === "reasoning") {
    previousItem.reasoning.events.push(event);
    return;
  }

  const reasoning = {
    id: `${event.thread_id}-reasoning-${event.seq}`,
    events: [event],
  };
  turn.reasoning.push(reasoning);
  turn.items.push({ kind: "reasoning", key: reasoning.id, reasoning });
}

function addToolStart(turn: ChatTurnViewModel, event: KiraEvent) {
  const tool = {
    id: `${event.thread_id}-tool-${event.seq}`,
    start: event,
  };
  turn.tools.push(tool);
  turn.items.push({ kind: "tool", key: tool.id, tool });
}

function addToolResult(turn: ChatTurnViewModel, event: KiraEvent) {
  const existing = [...turn.tools].reverse().find((tool) => tool.start && !tool.result && toolEventsMatch(tool.start, event));
  if (existing) {
    existing.result = event;
    return;
  }

  const tool = {
    id: `${event.thread_id}-tool-result-${event.seq}`,
    result: event,
  };
  turn.tools.push(tool);
  turn.items.push({ kind: "tool", key: tool.id, tool });
}

function addStatus(
  turn: ChatTurnViewModel,
  {
    event,
    kind,
    label,
    fallback,
    runState,
  }: {
    event: KiraEvent;
    kind: RunStatusViewModel["kind"];
    label: string;
    fallback: string;
    runState?: ChatRunState;
  },
) {
  const status = {
    id: `${event.thread_id}-${kind}-${event.seq}`,
    kind,
    label,
    message: getEventText(event, fallback),
    timestamp: getTimestampLabel(event.data.timestamp),
    event,
    runState,
  };
  turn.statuses.push(status);
  turn.items.push({ kind: "status", key: status.id, status });
}

function mergeChatMessage(turn: ChatTurnViewModel, role: ChatMessageViewModel["role"], message: ChatMessageViewModel) {
  const existing = turn[role];
  if (!existing) {
    turn[role] = message;
    return;
  }
  turn[role] = {
    ...existing,
    text: existing.text === message.text ? existing.text : `${existing.text}\n${message.text}`,
    timestamp: message.timestamp || existing.timestamp,
  };
}

function transcriptStatus(message: TranscriptMessage, text: string): RunStatusViewModel {
  const syntheticEvent: KiraEvent = {
    type: "checkpoint",
    thread_id: message.thread_id || message.turn_id || message.id,
    seq: 0,
    data: { text, timestamp: message.created_at },
  };
  return {
    id: `${message.id}-status`,
    kind: "checkpoint",
    label: message.role === "tool" ? "Tool" : "Transcript",
    message: text,
    timestamp: getTimestampLabel(message.created_at),
    event: syntheticEvent,
  };
}

function transcriptVisibleText(message: TranscriptMessage): string {
  return message.parts
    .filter((part) => part.visible && part.kind === "text")
    .map((part) => part.text)
    .join("");
}

function transcriptTurnId(message: TranscriptMessage, index: number): string {
  return message.turn_id || message.thread_id || `transcript-${index}`;
}

function eventTurnId(event: KiraEvent, currentTurnId: string): string {
  const explicitTurnId = event.data.turn_id ?? event.data.turnId;
  if (typeof explicitTurnId === "string" && explicitTurnId.length > 0) {
    return explicitTurnId;
  }
  return currentTurnId || event.thread_id;
}

function toolEventsMatch(start: KiraEvent, result: KiraEvent): boolean {
  const startValues = toolCorrelationValues(start);
  const resultValues = toolCorrelationValues(result);
  if (startValues.ids.some((id) => resultValues.ids.includes(id))) {
    return true;
  }
  return Boolean(startValues.name && resultValues.name && startValues.name === resultValues.name);
}

function toolCorrelationValues(event: KiraEvent): { ids: string[]; name: string } {
  const metadata = isRecord(event.data.metadata) ? event.data.metadata : {};
  const ids = [
    event.data.call_id,
    event.data.tool_call_id,
    event.data.tool_use_id,
    event.data.id,
    metadata.call_id,
    metadata.tool_call_id,
    metadata.tool_use_id,
    metadata.id,
  ].filter((value): value is string => typeof value === "string" && value.length > 0);
  const name = formatEventValue(event.data.name ?? event.data.tool_name ?? metadata.name ?? metadata.tool_name, "");
  return { ids, name };
}

function isCancelledEvent(event: KiraEvent): boolean {
  return event.type === "error" && (event.data.failure_class === "cancelled" || event.data.status === "cancelled");
}

function formatEventValue(value: unknown, fallback: string): string {
  if (typeof value === "string" && value.length > 0) {
    return value;
  }
  return fallback;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
