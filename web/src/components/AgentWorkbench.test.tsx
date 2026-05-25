import { cleanup, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { AgentWorkbench } from "./AgentWorkbench";
import type { KiraEvent, ProviderMetadata } from "../lib/types";
import { stage13ChunkedAnswerEvents } from "../test/stage13Fixtures";

const apiMock = vi.hoisted(() => ({
  compactConversation: vi.fn(),
  createConversation: vi.fn(),
  createRun: vi.fn(),
  getConversationTrace: vi.fn(),
  getDoctor: vi.fn(),
  getMemoryTrace: vi.fn(),
  getConversationTranscript: vi.fn(),
  getProjectIndexStatus: vi.fn(),
  getProjectTrace: vi.fn(),
  getRunContext: vi.fn(),
  getRunTrace: vi.fn(),
  getSkill: vi.fn(),
  inspectReplacement: vi.fn(),
  listAudit: vi.fn(),
  listMemory: vi.fn(),
  listConversations: vi.fn(),
  listSkills: vi.fn(),
  createMemory: vi.fn(),
  updateMemory: vi.fn(),
  deleteMemory: vi.fn(),
  extractMemory: vi.fn(),
  forkConversation: vi.fn(),
  decideMemoryCandidate: vi.fn(),
  memoryAction: vi.fn(),
  refreshProjectIndex: vi.fn(),
  resumeRun: vi.fn(),
  rollbackConversation: vi.fn(),
  searchMemory: vi.fn(),
  searchProject: vi.fn(),
  streamRunEvents: vi.fn(),
  updateConversation: vi.fn(),
}));

vi.mock("../lib/api", () => apiMock);

describe("AgentWorkbench", () => {
  beforeEach(() => {
    for (const mock of Object.values(apiMock)) {
      mock.mockReset();
    }
    apiMock.listSkills.mockResolvedValue({ skills: [] });
    apiMock.listConversations.mockResolvedValue({ conversations: [] });
    apiMock.listMemory.mockResolvedValue({ memories: [] });
    apiMock.getProjectIndexStatus.mockResolvedValue({
      root_id: "root",
      root: "/tmp/project",
      status: "not_indexed",
      file_count: 0,
      chunk_count: 0,
      skipped_count: 0,
      omitted_count: 0,
      fts_available: true,
    });
    apiMock.getRunContext.mockRejectedValue(new Error("not found"));
    apiMock.createConversation.mockResolvedValue({ conversation: conversation("conv-created", "New conversation") });
    apiMock.getConversationTranscript.mockResolvedValue({ conversation_id: "conv-1", messages: [] });
    apiMock.updateConversation.mockResolvedValue({ conversation: { ...conversation("conv-1", "hello"), archived: true, status: "archived" } });
    window.localStorage.clear();
    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      value: { writeText: vi.fn().mockResolvedValue(undefined) },
    });
  });

  afterEach(() => {
    cleanup();
  });

  it("renders the Stage 14 Mira-like default without dashboard or inspector content", () => {
    render(<AgentWorkbench />);

    expect(screen.getByLabelText("Task rail")).toBeTruthy();
    expect(screen.getByLabelText("Kira workbench")).toBeTruthy();
    expect(screen.getByLabelText("Run timeline")).toBeTruthy();
    expect(screen.getByLabelText("Prompt")).toBeTruthy();
    expect(screen.getByText("一个专业的数据agent助手")).toBeTruthy();
    expect(screen.getAllByText("Kira").length).toBeGreaterThanOrEqual(1);
    expect(screen.queryByText("Auto provider")).toBeNull();

    expect(screen.queryByRole("button", { name: "Inspector" })).toBeNull();
    expect(screen.queryByRole("button", { name: "Run fixture" })).toBeNull();
    expect(screen.queryByRole("button", { name: "Run error fixture" })).toBeNull();
    expect(screen.queryByRole("button", { name: "Run HITL fixture" })).toBeNull();
    expect(screen.queryByRole("region", { name: "Conversations" })).toBeNull();
    expect(screen.queryByRole("region", { name: "Skills" })).toBeNull();
    expect(screen.queryByRole("region", { name: "Memory" })).toBeNull();
    expect(screen.queryByRole("region", { name: "Project knowledge" })).toBeNull();
    expect(screen.queryByRole("region", { name: "Run context" })).toBeNull();
    expect(screen.queryByRole("region", { name: "Safety and diagnostics" })).toBeNull();
    expect(screen.queryByText("Local workbench")).toBeNull();
    expect(screen.queryByText(/\d+ events/i)).toBeNull();
    expect(screen.queryByText("No active skill")).toBeNull();
    expect(screen.queryByText("No skill")).toBeNull();
    expect(screen.queryByText("No project query")).toBeNull();
    expect(screen.queryByText("Memory off")).toBeNull();

    expect((document.querySelector(".workbench-shell") as HTMLElement).className).toContain("workbench-shell");
    expect((document.querySelector(".agent-header") as HTMLElement).className).toContain("agent-header");
    expect((document.querySelector(".composer") as HTMLElement).className).toContain("composer");
    expect((document.querySelector(".timeline") as HTMLElement).className).toContain("timeline");
  });

  it("starts with an empty composer, clears after submit, keeps focus, and uses auto provider semantics", async () => {
    mockRun([event("text_delta", 1, { text: "Visible assistant text" }), event("done", 2, { message: "Done" })], {
      mode: "real",
      source: "config",
      provider: "openai",
      name: "default",
      model: "model-a",
    });

    render(<AgentWorkbench />);
    const input = screen.getByLabelText("Prompt") as HTMLInputElement;
    expect(input.value).toBe("");

    await userEvent.type(input, "Summarize the dataset");
    await userEvent.click(screen.getByRole("button", { name: "Run" }));

    expect(apiMock.createRun).toHaveBeenCalledWith(expect.objectContaining({
      prompt: "Summarize the dataset",
      provider_mode: "auto",
      skill_id: undefined,
      project_root: expect.stringContaining("kira-agent"),
    }));
    await waitFor(() => expect(input.value).toBe(""));
    await waitFor(() => expect(document.activeElement).toBe(input));

    await userEvent.type(input, "Next prompt");
    expect(input.value).toBe("Next prompt");
    expect((await screen.findByTestId("user-row")).textContent).toContain("Summarize the dataset");
    const answerRow = await screen.findByTestId("answer-row");
    expect(answerRow.textContent).toContain("Visible assistant text");
    expect(within(answerRow).queryByRole("button", { name: "Copy rendered answer" })).toBeNull();
    expect(within(answerRow).queryByRole("button", { name: "Copy" })).toBeNull();
  });

  it("shows available skills after slash input and uses the selected skill explicitly", async () => {
    apiMock.listSkills.mockResolvedValue({
      skills: [
        skill("analysis-skill", "Analysis Skill", "Analyze local datasets"),
        { ...skill("shadowed-skill", "Shadowed Skill", "Should not be shown"), active: false },
      ],
    });
    mockRun([event("text_delta", 1, { text: "Skill answer" }), event("done", 2, { message: "Done" })]);

    render(<AgentWorkbench />);
    const input = screen.getByLabelText("Prompt") as HTMLInputElement;
    await userEvent.type(input, "/");

    const menu = await screen.findByRole("listbox", { name: "Available skills" });
    expect(within(menu).getByText("Analysis Skill")).toBeTruthy();
    expect(within(menu).queryByText("Shadowed Skill")).toBeNull();

    await userEvent.click(within(menu).getByRole("option", { name: /Analysis Skill/ }));
    expect(screen.getByLabelText("Active skill").textContent).toContain("Using Analysis Skill");
    expect(input.value).toBe("");

    await userEvent.type(input, "Run analysis");
    await userEvent.click(screen.getByRole("button", { name: "Run" }));

    expect(apiMock.createRun).toHaveBeenCalledWith(expect.objectContaining({
      prompt: "Run analysis",
      provider_mode: "auto",
      skill_id: "analysis-skill",
      project_root: expect.stringContaining("kira-agent"),
    }));
  });

  it("groups thinking events into a collapsed 思考过程 block that toggles without merging into answers", async () => {
    mockRun([
      event("thinking_delta", 1, { text: "Hidden planning text" }),
      event("thinking_delta", 2, { text: "Hidden tool choice" }),
      event("text_delta", 3, { text: "Visible answer" }),
      event("done", 4, { message: "Done" }),
    ]);

    render(<AgentWorkbench />);
    await submitPrompt("Explain the data");

    const thinkingToggle = await screen.findByRole("button", { name: /思考过程/ });
    expect(thinkingToggle.getAttribute("aria-expanded")).toBe("false");
    expect(screen.queryByText("Hidden planning text")).toBeNull();

    const answer = await screen.findByTestId("answer-row");
    expect(answer.textContent).toContain("Visible answer");
    expect(answer.textContent).not.toContain("Hidden planning text");
    expect(within(await screen.findByTestId("chat-turn")).getByLabelText("Assistant turn")).toBeTruthy();

    await userEvent.click(thinkingToggle);
    expect(thinkingToggle.getAttribute("aria-expanded")).toBe("true");
    expect(screen.getByText(/Hidden planning text/)).toBeTruthy();
    expect(screen.getByText(/Hidden tool choice/)).toBeTruthy();

    await userEvent.click(thinkingToggle);
    expect(thinkingToggle.getAttribute("aria-expanded")).toBe("false");
    expect(screen.queryByText("Hidden planning text")).toBeNull();
  });

  it("aggregates chunked text into one assistant row and does not render done as a primary card", async () => {
    mockRun(stage13ChunkedAnswerEvents());

    render(<AgentWorkbench />);
    await submitPrompt("Aggregate this answer");

    const answers = await screen.findAllByTestId("answer-row");
    expect(answers).toHaveLength(1);
    expect(answers[0].textContent).toContain("Kira keeps one answer.");
    expect(document.querySelector(".done-row")).toBeNull();
  });

  it("keeps completed transcript visible when a follow-up run starts", async () => {
    const firstTranscript = [
      transcriptMessage("msg-first-user", "user", "First question", { conversationId: "conv-test", turnId: "turn-first", threadId: "thread-first" }),
      transcriptMessage("msg-first-assistant", "assistant", "First answer", { conversationId: "conv-test", turnId: "turn-first", threadId: "thread-first" }),
    ];
    const secondTranscript = [
      ...firstTranscript,
      transcriptMessage("msg-second-user", "user", "Second question", { conversationId: "conv-test", turnId: "turn-second", threadId: "thread-second" }),
      transcriptMessage("msg-second-assistant", "assistant", "Second answer", { conversationId: "conv-test", turnId: "turn-second", threadId: "thread-second" }),
    ];
    apiMock.getConversationTranscript
      .mockResolvedValueOnce({ conversation_id: "conv-test", messages: firstTranscript })
      .mockResolvedValueOnce({ conversation_id: "conv-test", messages: secondTranscript });

    mockRun(
      [event("text_delta", 1, { text: "First answer" }, "thread-first"), event("done", 2, { message: "Done" }, "thread-first")],
      undefined,
      "conv-test",
      "turn-first",
      "thread-first",
    );
    render(<AgentWorkbench />);
    await submitPrompt("First question");

    expect((await screen.findByTestId("transcript-answer-row")).textContent).toContain("First answer");

    mockRun(
      [event("text_delta", 1, { text: "Second answer" }, "thread-second"), event("done", 2, { message: "Done" }, "thread-second")],
      undefined,
      "conv-test",
      "turn-second",
      "thread-second",
    );
    await submitPrompt("Second question");

    expect((await screen.findByText("First answer")).textContent).toContain("First answer");
    expect((await screen.findByText("Second answer")).textContent).toContain("Second answer");
  });

  it("resets thinking groups for a new run", async () => {
    mockRun([event("thinking_delta", 1, { text: "First hidden thought" }), event("done", 2, { message: "Done" })]);
    render(<AgentWorkbench />);

    await submitPrompt("First prompt");
    await screen.findByRole("button", { name: /思考过程/ });

    mockRun([event("thinking_delta", 1, { text: "Second hidden thought" }), event("done", 2, { message: "Done" })]);
    await submitPrompt("Second prompt");

    await userEvent.click(await screen.findByRole("button", { name: /思考过程/ }));
    expect(screen.getByText("Second hidden thought")).toBeTruthy();
    expect(screen.queryByText("First hidden thought")).toBeNull();
  });

  it("groups tool start and result events with a collapsed long preview and keeps tool output out of answers", async () => {
    const longResult = {
      status: "ok",
      payload: `${"x".repeat(520)}TAIL_MARKER`,
    };
    mockRun([
      event("tool_start", 1, { name: "project.search", message: "Searching cited project snippets" }),
      event("tool_result", 2, {
        name: "project.search",
        status: "ok",
        result: longResult,
        metadata: { content_type: "application/json", truncated: true },
      }),
      event("text_delta", 3, { text: "Visible answer after tool" }),
      event("done", 4, { message: "Done" }),
    ]);

    render(<AgentWorkbench />);
    await submitPrompt("Use a tool");

    const tools = await screen.findAllByTestId("tool-activity-block");
    expect(tools).toHaveLength(1);
    expect(tools[0].textContent).toContain("调用工具");
    expect(tools[0].textContent).toContain("project.search");
    expect(tools[0].textContent).not.toContain("TAIL_MARKER");

    await userEvent.click(within(tools[0]).getByRole("button", { name: "Expand" }));
    expect(tools[0].textContent).toContain("TAIL_MARKER");
    expect(within(tools[0]).getByRole("button", { name: "Copy" })).toBeTruthy();

    const answer = await screen.findByTestId("answer-row");
    expect(answer.textContent).toContain("Visible answer after tool");
    expect(answer.textContent).not.toContain("TAIL_MARKER");
  });

  it("renders user and assistant text inside tight message bubble containers", async () => {
    mockRun([event("text_delta", 1, { text: "\n\nAssistant bubble text" }), event("done", 2, { message: "Done" })]);

    render(<AgentWorkbench />);
    await submitPrompt("User bubble text");

    const userRow = await screen.findByTestId("user-row");
    const answerRow = await screen.findByTestId("answer-row");
    expect(userRow.querySelector(".message-bubble")).toBeTruthy();
    expect(answerRow.querySelector(".message-bubble")).toBeTruthy();
    expect(userRow.className).toContain("user-message");
    expect(answerRow.className).toContain("assistant-message");
    const answerBubble = answerRow.querySelector(".message-bubble") as HTMLElement;
    expect(within(answerBubble).getByText("Kira")).toBeTruthy();
    expect(within(answerBubble).getByText("Assistant bubble text")).toBeTruthy();
    expect(answerBubble.querySelector("p")?.textContent).toBe("Assistant bubble text");
  });

  it("shows a lightweight run step between the prompt and the first answer", async () => {
    mockPendingRun();

    render(<AgentWorkbench />);
    await submitPrompt("什么是 trace");

    const progress = await screen.findByLabelText("Current run step");
    expect(progress.textContent).toContain("Kira");
    expect(progress.textContent).toContain("正在理解你的问题");
  });

  it("renders assistant markdown as formatted content instead of raw markdown text", async () => {
    mockRun([
      event("text_delta", 1, {
        text: "# Python 数据发送脚本\n\n当然可以，使用 `requests`：\n\n```python\nimport requests\n```\n\n- POST JSON\n- 设置 timeout\n\n| Data Agent 场景 | 对应设计 |\n| --- | --- |\n| 文档管理 | 双层保险 |\n| 评估 | eval 目录 |",
      }),
      event("done", 2, { message: "Done" }),
    ]);

    render(<AgentWorkbench />);
    await submitPrompt("生成脚本");

    const answerRow = await screen.findByTestId("answer-row");
    expect(within(answerRow).getByRole("heading", { name: "Python 数据发送脚本" })).toBeTruthy();
    expect(within(answerRow).getByText("requests")).toBeTruthy();
    expect(within(answerRow).getByText("import requests")).toBeTruthy();
    expect(within(answerRow).getByText("POST JSON")).toBeTruthy();
    expect(within(answerRow).getByText("Data Agent 场景")).toBeTruthy();
    expect(within(answerRow).getByText("双层保险")).toBeTruthy();
    await userEvent.click(within(answerRow).getByRole("button", { name: "Copy python code" }));
    expect(navigator.clipboard.writeText).toHaveBeenCalledWith("import requests");
    expect(within(answerRow).getByRole("button", { name: "Copy python code" }).textContent).toBe("Copied");
    expect(answerRow.textContent).not.toContain("```python");
    expect(answerRow.textContent).not.toContain("# Python");
  });

  it("renders transcript rows as chat bubbles from the task rail", async () => {
    apiMock.listConversations.mockResolvedValue({
      conversations: [conversation("conv-1", "hello")],
    });
    apiMock.getConversationTranscript.mockResolvedValue({
      conversation_id: "conv-1",
      messages: [
        transcriptMessage("msg-1", "user", "hello"),
        transcriptMessage("msg-2", "assistant", "visible answer"),
      ],
    });

    render(<AgentWorkbench />);
    await userEvent.click(await screen.findByRole("button", { name: "Select task hello" }));

    expect((await screen.findByTestId("transcript-user-row")).textContent).toContain("hello");
    expect((await screen.findByTestId("transcript-answer-row")).textContent).toContain("visible answer");
    expect((await screen.findByTestId("transcript-answer-row")).querySelector(".message-bubble")).toBeTruthy();
  });

  it("opens recent task actions, pins locally, and deletes a conversation", async () => {
    apiMock.listConversations
      .mockResolvedValueOnce({ conversations: [conversation("conv-1", "hello")] })
      .mockResolvedValueOnce({ conversations: [] });

    render(<AgentWorkbench />);
    await userEvent.click(await screen.findByRole("button", { name: "Open actions for hello" }));
    await userEvent.click(screen.getByRole("menuitem", { name: /Pin/ }));

    expect(window.localStorage.getItem("kira:pinned-conversations")).toContain("conv-1");
    expect(screen.getByRole("button", { name: "Select task hello" }).textContent).toContain("Pin · hello");

    await userEvent.click(screen.getByRole("button", { name: "Open actions for hello" }));
    expect(screen.queryByRole("menuitem", { name: /Share/ })).toBeNull();
    await userEvent.click(screen.getByRole("menuitem", { name: /Delete/ }));

    await waitFor(() => expect(apiMock.updateConversation).toHaveBeenCalledWith("conv-1", { archived: true }));
    expect(screen.queryByRole("button", { name: "Select task hello" })).toBeNull();
  });

  it("renames a recent task from the actions menu", async () => {
    apiMock.listConversations.mockResolvedValue({
      conversations: [conversation("conv-1", "hello")],
    });
    apiMock.updateConversation.mockResolvedValueOnce({
      conversation: conversation("conv-1", "renamed task"),
    });

    render(<AgentWorkbench />);
    await userEvent.click(await screen.findByRole("button", { name: "Open actions for hello" }));
    await userEvent.click(screen.getByRole("menuitem", { name: /Rename/ }));
    await userEvent.clear(screen.getByRole("textbox", { name: "Rename hello" }));
    await userEvent.type(screen.getByRole("textbox", { name: "Rename hello" }), "renamed task{Enter}");

    await waitFor(() => expect(apiMock.updateConversation).toHaveBeenCalledWith("conv-1", { title: "renamed task" }));
    expect(await screen.findByRole("button", { name: "Select task renamed task" })).toBeTruthy();
  });

  it("clears saved conversations by archiving active history", async () => {
    apiMock.listConversations.mockResolvedValue({
      conversations: [conversation("conv-1", "hello"), conversation("conv-2", "analysis")],
    });
    apiMock.getConversationTranscript.mockResolvedValue({
      conversation_id: "conv-1",
      messages: [transcriptMessage("msg-1", "user", "hello")],
    });

    render(<AgentWorkbench />);
    await userEvent.click(await screen.findByRole("button", { name: "Select task hello" }));
    expect(await screen.findByTestId("transcript-user-row")).toBeTruthy();

    await userEvent.click(screen.getByRole("button", { name: "Clear history" }));

    await waitFor(() => {
      expect(apiMock.updateConversation).toHaveBeenCalledWith("conv-1", { archived: true });
      expect(apiMock.updateConversation).toHaveBeenCalledWith("conv-2", { archived: true });
    });
    expect(screen.queryByTestId("transcript-user-row")).toBeNull();
    expect(await screen.findByText("Cleared 2 conversations")).toBeTruthy();
  });

  it("renders HITL interrupts from the chat timeline and appends resume results", async () => {
    apiMock.resumeRun.mockResolvedValue({
      status: "completed",
      thread_id: "local-test",
      interrupt_id: "interrupt-1",
      decision: "approve",
      events: [
        event("resume", 3, { interrupt_id: "interrupt-1", decision: "approve" }),
        event("text_delta", 4, { text: "Approval received." }),
        event("done", 5, { message: "Done" }),
      ],
    });
    mockRun([
      event("interrupt", 1, {
        interrupt_id: "interrupt-1",
        kind: "approval",
        title: "Approve workflow step",
        body: "Approve this deterministic fixture step.",
        data: {},
        allowed_responses: [
          { id: "approve", label: "Approve", kind: "approve" },
          { id: "reject", label: "Reject", kind: "reject" },
        ],
      }),
      event("checkpoint", 2, { checkpoint_id: "latest" }),
    ]);

    render(<AgentWorkbench />);
    await submitPrompt("Needs approval");

    expect(await screen.findByLabelText("Human input required")).toBeTruthy();
    await userEvent.click(screen.getByRole("button", { name: "Approve" }));

    expect(apiMock.resumeRun).toHaveBeenCalledWith(
      "local-test",
      expect.objectContaining({ interrupt_id: "interrupt-1", decision: "approve", data: {} }),
    );
    expect(await screen.findByText("Approval received.")).toBeTruthy();
    expect(await screen.findByText("Decision: approve")).toBeTruthy();
  });
});

async function submitPrompt(text: string) {
  const input = screen.getByLabelText("Prompt") as HTMLInputElement;
  await userEvent.clear(input);
  await userEvent.type(input, text);
  await userEvent.click(screen.getByRole("button", { name: "Run" }));
}

function mockRun(events: KiraEvent[], provider?: ProviderMetadata, conversationId = "conv-test", turnId = "turn-test", threadId = "local-test") {
  apiMock.createRun.mockResolvedValue({
    thread_id: threadId,
    conversation_id: conversationId,
    turn_id: turnId,
    status: "created",
    fixture: null,
    events_url: `/api/runs/${threadId}/events`,
    provider: provider ?? { mode: "fixture", source: "fixture", fixture: null },
  });
  apiMock.streamRunEvents.mockImplementation((_eventsUrl, handlers) => {
    const close = vi.fn();
    queueMicrotask(() => {
      for (const nextEvent of events) {
        handlers.onEvent(nextEvent);
      }
    });
    return close;
  });
}

function mockPendingRun(provider?: ProviderMetadata, conversationId = "conv-test", turnId = "turn-test", threadId = "local-test") {
  apiMock.createRun.mockResolvedValue({
    thread_id: threadId,
    conversation_id: conversationId,
    turn_id: turnId,
    status: "created",
    fixture: null,
    events_url: `/api/runs/${threadId}/events`,
    provider: provider ?? { mode: "fixture", source: "fixture", fixture: null },
  });
  apiMock.streamRunEvents.mockReturnValue(vi.fn());
}

function event(type: KiraEvent["type"], seq: number, data: KiraEvent["data"], threadId = "local-test"): KiraEvent {
  return {
    type,
    thread_id: threadId,
    seq,
    data,
  };
}

function conversation(id: string, title: string) {
  return {
    id,
    title,
    status: "active",
    archived: false,
    active_head_message_id: null,
    created_at: "2026-05-14T00:00:00Z",
    updated_at: "2026-05-14T00:00:00Z",
  };
}

function skill(skillId: string, name: string, description: string) {
  return {
    skill_id: skillId,
    name,
    description,
    valid: true,
    active: true,
    workflows: [],
    allowed_tools: [],
  };
}

function transcriptMessage(
  id: string,
  role: "user" | "assistant",
  text: string,
  options: { conversationId?: string; turnId?: string; threadId?: string } = {},
) {
  const conversationId = options.conversationId ?? "conv-1";
  const turnId = options.turnId ?? "turn-1";
  const threadId = options.threadId ?? "local-test";
  return {
    id,
    conversation_id: conversationId,
    turn_id: turnId,
    thread_id: threadId,
    parent_message_id: null,
    logical_parent_message_id: null,
    role,
    status: "completed",
    branch_status: "active",
    parts: [
      {
        id: `${id}-part`,
        message_id: id,
        conversation_id: conversationId,
        turn_id: turnId,
        thread_id: threadId,
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
