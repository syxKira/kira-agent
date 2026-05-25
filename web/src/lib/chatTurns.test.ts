import { describe, expect, it } from "vitest";

import { buildChatTurns } from "./chatTurns";
import type { TranscriptMessage } from "./types";
import {
  stage13ChunkedAnswerEvents,
  stage13ErrorEvents,
  stage13HitlEvents,
  stage13InterleavedProcessEvents,
} from "../test/stage13Fixtures";

describe("buildChatTurns", () => {
  it("aggregates many text deltas into one assistant answer and treats done as terminal state", () => {
    const turns = buildChatTurns({
      transcriptMessages: [],
      activePrompt: "Explain the data",
      events: stage13ChunkedAnswerEvents(),
      threadId: "stage13-turn",
      turnId: "turn-live",
    });

    expect(turns).toHaveLength(1);
    expect(turns[0].user?.text).toBe("Explain the data");
    expect(turns[0].assistant?.text).toBe("Kira keeps one answer.");
    expect(turns[0].runState).toBe("completed");
    expect(turns[0].items.some((item) => item.kind === "status" && item.status.label === "Completed")).toBe(false);
  });

  it("keeps thinking and tool output out of assistant answer text", () => {
    const turns = buildChatTurns({
      transcriptMessages: [],
      activePrompt: "Use process data",
      events: stage13InterleavedProcessEvents(),
      threadId: "stage13-turn",
      turnId: "turn-live",
    });

    const turn = turns[0];
    expect(turn.assistant?.text).toBe("Visible answer only.");
    expect(turn.assistant?.text).not.toContain("Plan without exposing hidden thinking");
    expect(turn.assistant?.text).not.toContain("Tool output belongs to process");
    expect(turn.reasoning).toHaveLength(1);
    expect(turn.tools).toHaveLength(1);
    expect(turn.statuses.map((status) => status.kind)).toEqual(["checkpoint", "retry"]);
  });

  it("normalizes transcript history and live events into ordered turns", () => {
    const turns = buildChatTurns({
      transcriptMessages: [
        transcriptMessage("msg-1", "turn-1", "user", "historical prompt"),
        transcriptMessage("msg-2", "turn-1", "assistant", "historical answer"),
      ],
      activePrompt: "live prompt",
      events: stage13ChunkedAnswerEvents(),
      threadId: "stage13-turn",
      turnId: "turn-live",
    });

    expect(turns).toHaveLength(2);
    expect(turns[0].user?.text).toBe("historical prompt");
    expect(turns[0].assistant?.text).toBe("historical answer");
    expect(turns[0].user?.sourceMessage?.id).toBe("msg-1");
    expect(turns[1].user?.text).toBe("live prompt");
    expect(turns[1].assistant?.text).toBe("Kira keeps one answer.");
  });

  it("keeps HITL and error states as process/status content on the active turn", () => {
    const hitlTurn = buildChatTurns({
      transcriptMessages: [],
      activePrompt: "Needs approval",
      events: stage13HitlEvents(),
      threadId: "stage13-turn",
      turnId: "turn-live",
    })[0];

    expect(hitlTurn.statuses.map((status) => status.kind)).toEqual(["interrupt", "resume"]);
    expect(hitlTurn.runState).toBe("completed");

    const errorTurn = buildChatTurns({
      transcriptMessages: [],
      activePrompt: "May fail",
      events: stage13ErrorEvents(),
      threadId: "stage13-turn",
      turnId: "turn-live",
    })[0];

    expect(errorTurn.runState).toBe("error");
    expect(errorTurn.statuses[errorTurn.statuses.length - 1]?.message).toBe("Provider stream failed");
  });
});

function transcriptMessage(id: string, turnId: string, role: "user" | "assistant", text: string): TranscriptMessage {
  return {
    id,
    conversation_id: "conv-1",
    turn_id: turnId,
    thread_id: "thread-1",
    parent_message_id: null,
    logical_parent_message_id: null,
    role,
    status: "completed",
    branch_status: "active",
    parts: [
      {
        id: `${id}-part`,
        message_id: id,
        conversation_id: "conv-1",
        turn_id: turnId,
        thread_id: "thread-1",
        kind: "text",
        seq: 1,
        text,
        payload: {},
        visible: true,
        token_estimate: 1,
        created_at: "2026-05-14T00:00:00Z",
      },
    ],
    created_at: "2026-05-14T00:00:00Z",
    updated_at: "2026-05-14T00:00:00Z",
  };
}
