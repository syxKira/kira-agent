import type { KiraEvent } from "./types";

export function isFixtureToolPreview(event: KiraEvent): boolean {
  return (
    event.type === "tool_result" ||
    event.type === "side_effect_reused" ||
    (event.type === "text_delta" &&
      (event.data.kind === "fixture_tool_result" ||
        event.data.kind === "graph_tool_result" ||
        event.data.kind === "side_effect_reused"))
  );
}

export function isAnswerTextEvent(event: KiraEvent): boolean {
  return event.type === "text_delta" && !isFixtureToolPreview(event);
}

export function getEventText(event: KiraEvent, fallback = ""): string {
  const text = event.data.text;
  if (typeof text === "string") {
    return text;
  }

  const message = event.data.message;
  if (typeof message === "string") {
    return message;
  }

  return fallback;
}

export function getTimestampLabel(value: unknown): string {
  if (typeof value !== "string") {
    return "";
  }

  const timestamp = new Date(value);
  if (Number.isNaN(timestamp.getTime())) {
    return "";
  }

  return timestamp.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

export function getVisibleAssistantText(events: KiraEvent[]): string {
  return events
    .filter(isAnswerTextEvent)
    .map((event) => getEventText(event))
    .join("");
}
