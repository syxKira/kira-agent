import { useState } from "react";

import { copyTextToClipboard } from "../lib/clipboard";
import { getEventText, getTimestampLabel } from "../lib/timeline";
import type { KiraEvent } from "../lib/types";

type ToolActivityBlockProps = {
  start?: KiraEvent;
  result?: KiraEvent;
};

const COLLAPSED_PREVIEW_CHARS = 420;

export function ToolActivityBlock({ start, result }: ToolActivityBlockProps) {
  const source = result ?? start;
  const preview = result ? safeJson(result.data.result ?? result.data) : getEventText(start!, "Tool call started");
  const isLong = preview.length > COLLAPSED_PREVIEW_CHARS;
  const [expanded, setExpanded] = useState(!isLong);
  const visiblePreview = expanded || !isLong ? preview : `${preview.slice(0, COLLAPSED_PREVIEW_CHARS)}...`;
  const status = formatEventValue(result?.data.status ?? start?.data.status, result ? "completed" : "running");
  const timestamp = getTimestampLabel((result ?? start)?.data.timestamp);
  const metadata = result?.data.metadata ?? start?.data.metadata;

  return (
    <article className="tool-activity-card" data-testid="tool-activity-block">
      <header className="tool-activity-header">
        <span className="event-type">调用工具</span>
        <code>{formatToolName(source)}</code>
        <small>{status}</small>
        {timestamp ? <time>{timestamp}</time> : null}
      </header>
      {metadata && typeof metadata === "object" ? (
        <div className="tool-card-meta">
          {Object.entries(metadata as Record<string, unknown>).slice(0, 4).map(([key, value]) => (
            <span key={key}>
              {key}: {String(value)}
            </span>
          ))}
        </div>
      ) : null}
      <div className="tool-preview-actions">
        <ToolCopyButton value={preview} />
        {isLong ? (
          <button className="secondary-button" type="button" aria-expanded={expanded} onClick={() => setExpanded((value) => !value)}>
            {expanded ? "Collapse" : "Expand"}
          </button>
        ) : null}
      </div>
      <pre className={expanded ? "is-expanded" : ""}>{visiblePreview}</pre>
    </article>
  );
}

function ToolCopyButton({ value }: { value: string }) {
  const [status, setStatus] = useState<"idle" | "copied" | "failed">("idle");

  async function handleCopy() {
    const ok = await copyTextToClipboard(value);
    setStatus(ok ? "copied" : "failed");
    window.setTimeout(() => setStatus("idle"), 1600);
  }

  const label = status === "copied" ? "Copied" : status === "failed" ? "Copy failed" : "Copy";
  return (
    <button
      className={`secondary-button copy-button copy-feedback-button ${status === "copied" ? "is-copied" : ""} ${status === "failed" ? "is-failed" : ""}`}
      type="button"
      onClick={() => void handleCopy()}
      aria-live="polite"
    >
      {label}
    </button>
  );
}

function formatToolName(event?: KiraEvent): string {
  return formatEventValue(event?.data.name ?? event?.data.tool_name, event?.type === "side_effect_reused" ? "side effect" : "tool");
}

function formatEventValue(value: unknown, fallback: string): string {
  if (typeof value === "string" && value.length > 0) {
    return value;
  }
  return fallback;
}

function safeJson(value: unknown): string {
  return redactForDisplay(JSON.stringify(value, null, 2));
}

function redactForDisplay(value: string): string {
  return value
    .replace(/sk-[A-Za-z0-9._-]+/g, "[redacted]")
    .replace(/Bearer\s+[A-Za-z0-9._~+/=-]+/gi, "Bearer [redacted]")
    .replace(/(api[_-]?key|token|password|secret)["']?\s*[:=]\s*["']?[^"',\s}]+/gi, "$1: [redacted]");
}
