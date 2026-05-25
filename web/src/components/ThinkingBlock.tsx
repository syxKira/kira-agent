import { useState } from "react";

import { getEventText, getTimestampLabel } from "../lib/timeline";
import type { KiraEvent } from "../lib/types";

type ThinkingBlockProps = {
  events: KiraEvent[];
};

export function ThinkingBlock({ events }: ThinkingBlockProps) {
  const [open, setOpen] = useState(false);
  const text = events.map((event) => getEventText(event, "")).filter(Boolean).join("\n");
  const timestamp = getTimestampLabel(events[events.length - 1]?.data.timestamp);

  return (
    <article className="thinking-block" data-testid="thinking-block">
      <button
        type="button"
        className="thinking-toggle"
        aria-expanded={open}
        onClick={() => setOpen((value) => !value)}
      >
        <span className={`thinking-chevron ${open ? "is-open" : ""}`} aria-hidden="true">
          &gt;
        </span>
        <span>思考过程</span>
        <small>{events.length > 1 ? `${events.length} updates` : "collapsed"}</small>
        {timestamp ? <time>{timestamp}</time> : null}
      </button>
      {open ? <pre className="thinking-content">{text || "Preparing run"}</pre> : null}
    </article>
  );
}
