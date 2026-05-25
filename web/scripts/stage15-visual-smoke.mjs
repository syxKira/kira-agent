import { spawn } from "node:child_process";
import { mkdtemp, writeFile } from "node:fs/promises";
import { createServer } from "node:http";
import { tmpdir } from "node:os";
import { join } from "node:path";

const chromeBin = process.env.CHROME_BIN ?? "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const chromePort = 9800 + Math.floor(Math.random() * 300);
const userDataDir = await mkdtemp(join(tmpdir(), "kira-stage15-chrome-"));
const outDir = await mkdtemp(join(tmpdir(), "kira-stage15-visual-"));
const apiServer = createApiServer();
const apiPort = await listen(apiServer);
const appPort = await getFreePort();
const apiBase = `http://127.0.0.1:${apiPort}`;
const appUrl = `http://127.0.0.1:${appPort}/`;
const viteBin = process.platform === "win32" ? join(process.cwd(), "node_modules", ".bin", "vite.cmd") : join(process.cwd(), "node_modules", ".bin", "vite");

const vite = spawn(viteBin, ["--host", "127.0.0.1", "--port", String(appPort)], {
  env: { ...process.env, VITE_KIRA_API_BASE: apiBase },
  stdio: ["ignore", "pipe", "pipe"],
});

const chrome = spawn(chromeBin, [
  "--headless=new",
  "--disable-gpu",
  "--no-first-run",
  "--no-default-browser-check",
  `--remote-debugging-port=${chromePort}`,
  `--user-data-dir=${userDataDir}`,
  "about:blank",
], { stdio: ["ignore", "pipe", "pipe"] });

try {
  await waitForHttp(appUrl, "Vite dev server");
  await waitForDebugger(chromePort);
  const tabs = await getJson(`http://127.0.0.1:${chromePort}/json/list`);
  const page = tabs.find((tab) => tab.type === "page" && tab.webSocketDebuggerUrl);
  if (!page) {
    throw new Error("No Chrome page target available");
  }

  const cdp = await connectCdp(page.webSocketDebuggerUrl);
  await cdp.send("Page.enable");
  await cdp.send("Runtime.enable");

  await captureWelcome(cdp);
  await captureRunScenario(cdp, {
    id: "normal-chat",
    prompt: "stage15 normal answer",
    waitFor: "document.body.innerText.includes('Stage 15 keeps one continuous answer.')",
    assertKind: "normal",
  });
  await captureRunScenario(cdp, {
    id: "streaming-status",
    prompt: "stage15 streaming status",
    waitFor: "document.body.innerText.includes('Retrying deterministic stream') && document.body.innerText.includes('Stop')",
    assertKind: "streaming",
  });
  await captureRunScenario(cdp, {
    id: "reasoning-collapsed",
    prompt: "stage15 reasoning state",
    waitFor: "Boolean(document.querySelector('[data-testid=\"thinking-block\"]')) && document.body.innerText.includes('Reasoning answer remains visible.')",
    assertKind: "reasoning-collapsed",
    afterDesktop: async () => {
      await screenshot(cdp, join(outDir, "reasoning-collapsed-desktop.png"));
      await clickByText(cdp, "思考过程");
      await waitForCondition(cdp, "document.body.innerText.includes('Hidden stage15 planning detail')");
      await assertStage15State(cdp, "reasoning-expanded");
      await screenshot(cdp, join(outDir, "reasoning-expanded-desktop.png"));
    },
    afterNarrow: async () => {
      await screenshot(cdp, join(outDir, "reasoning-collapsed-narrow.png"));
      await clickByText(cdp, "思考过程");
      await waitForCondition(cdp, "document.body.innerText.includes('Hidden stage15 planning detail')");
      await assertStage15State(cdp, "reasoning-expanded");
      await screenshot(cdp, join(outDir, "reasoning-expanded-narrow.png"));
    },
    skipDefaultScreenshot: true,
  });
  await captureRunScenario(cdp, {
    id: "tool-activity",
    prompt: "stage15 tool activity",
    waitFor: "Boolean(document.querySelector('[data-testid=\"tool-activity-block\"]')) && document.body.innerText.includes('Tool evidence is summarized without leaking raw output.')",
    assertKind: "tool",
  });
  await captureRunScenario(cdp, {
    id: "hitl",
    prompt: "stage15 hitl approval",
    waitFor: "Boolean(document.querySelector('[aria-label=\"Human input required\"]'))",
    assertKind: "hitl",
    afterDesktop: async () => {
      await screenshot(cdp, join(outDir, "hitl-desktop.png"));
      await clickByText(cdp, "Approve");
      await waitForCondition(cdp, "document.body.innerText.includes('Approval received for visual smoke.') && document.body.innerText.includes('Decision: approve')");
      await assertStage15State(cdp, "hitl-resumed");
      await screenshot(cdp, join(outDir, "hitl-resumed-desktop.png"));
    },
    afterNarrow: async () => {
      await screenshot(cdp, join(outDir, "hitl-narrow.png"));
      await clickByText(cdp, "Approve");
      await waitForCondition(cdp, "document.body.innerText.includes('Approval received for visual smoke.') && document.body.innerText.includes('Decision: approve')");
      await assertStage15State(cdp, "hitl-resumed");
      await screenshot(cdp, join(outDir, "hitl-resumed-narrow.png"));
    },
    skipDefaultScreenshot: true,
  });
  await captureRunScenario(cdp, {
    id: "error",
    prompt: "stage15 error state",
    waitFor: "Boolean(document.querySelector('[role=\"alert\"]')) && document.body.innerText.includes('Provider stream failed for visual smoke')",
    assertKind: "error",
  });
  await captureLongTranscript(cdp);

  await cdp.close();
  console.log(JSON.stringify({
    status: "ok",
    appUrl,
    apiBase,
    screenshots: outDir,
    viewports: ["1280x900", "390x780"],
    states: [
      "welcome",
      "normal-chat",
      "streaming-status",
      "reasoning-collapsed",
      "reasoning-expanded",
      "tool-activity",
      "hitl",
      "hitl-resumed",
      "error",
      "long-transcript",
    ],
  }, null, 2));
} finally {
  chrome.kill("SIGTERM");
  vite.kill("SIGTERM");
  apiServer.close();
}

async function captureWelcome(cdp) {
  await setViewport(cdp, 1280, 900);
  await navigate(cdp, appUrl);
  await waitForCondition(cdp, "Boolean(document.querySelector('.welcome-shell'))");
  await assertWelcome(cdp);
  await screenshot(cdp, join(outDir, "welcome-desktop.png"));

  await setViewport(cdp, 390, 780);
  await waitForCondition(cdp, "Boolean(document.querySelector('.welcome-shell'))");
  await assertWelcome(cdp);
  await screenshot(cdp, join(outDir, "welcome-narrow.png"));
}

async function captureRunScenario(cdp, scenario) {
  await setViewport(cdp, 1280, 900);
  await navigateToWorkbench(cdp);
  await submitPrompt(cdp, scenario.prompt);
  await waitForCondition(cdp, scenario.waitFor);
  await assertStage15State(cdp, scenario.assertKind);
  if (scenario.afterDesktop) {
    await scenario.afterDesktop();
  }
  if (!scenario.skipDefaultScreenshot) {
    await screenshot(cdp, join(outDir, `${scenario.id}-desktop.png`));
  }

  await setViewport(cdp, 390, 780);
  await navigateToWorkbench(cdp);
  await submitPrompt(cdp, scenario.prompt);
  await waitForCondition(cdp, scenario.waitFor);
  await assertStage15State(cdp, scenario.assertKind);
  if (scenario.afterNarrow) {
    await scenario.afterNarrow();
  }
  if (!scenario.skipDefaultScreenshot) {
    await screenshot(cdp, join(outDir, `${scenario.id}-narrow.png`));
  }
}

async function captureLongTranscript(cdp) {
  await setViewport(cdp, 1280, 900);
  await navigateToWorkbench(cdp);
  await clickByText(cdp, "Long transcript");
  await waitForCondition(cdp, "document.querySelectorAll('[data-testid=\"transcript-answer-row\"]').length >= 6");
  await assertStage15State(cdp, "long-transcript");
  await screenshot(cdp, join(outDir, "long-transcript-desktop.png"));

  await setViewport(cdp, 390, 780);
  await waitForCondition(cdp, "document.querySelectorAll('[data-testid=\"transcript-answer-row\"]').length >= 6");
  await assertStage15State(cdp, "long-transcript");
  await screenshot(cdp, join(outDir, "long-transcript-narrow.png"));
}

async function navigateToWorkbench(cdp) {
  await navigate(cdp, appUrl);
  await waitForCondition(cdp, "Boolean(document.querySelector('.welcome-shell'))");
  await clickByText(cdp, "立刻开始");
  await waitForCondition(cdp, "Boolean(document.querySelector('.workbench-shell')) && Boolean(document.querySelector('input[aria-label=\"Prompt\"]'))");
}

async function assertWelcome(cdp) {
  const result = await evaluate(cdp, `(() => {
    const shell = document.querySelector('.welcome-shell');
    const panel = document.querySelector('.welcome-panel');
    const shellRect = shell.getBoundingClientRect();
    const panelRect = panel.getBoundingClientRect();
    const text = document.body.innerText;
    return {
      hasProductCopy: text.includes('一个专业的数据agent助手'),
      hasStartAction: text.includes('立刻开始'),
      hasSingleAgent: document.querySelectorAll('.agent-card').length === 1,
      removedScaffold: ['FastAPI local', 'Read-only context', 'Auto or fixture', 'Local Web Agent', 'Local agent'].some((value) => text.includes(value)),
      horizontalOverflow: document.documentElement.scrollWidth > window.innerWidth + 1,
      centerDeltaX: Math.abs((panelRect.left + panelRect.width / 2) - (shellRect.left + shellRect.width / 2)),
      centerDeltaY: Math.abs((panelRect.top + panelRect.height / 2) - (shellRect.top + shellRect.height / 2)),
    };
  })()`);
  assertSmoke(result.hasProductCopy, "welcome product copy is visible");
  assertSmoke(result.hasStartAction, "welcome start action is visible");
  assertSmoke(result.hasSingleAgent, "welcome has exactly one agent card");
  assertSmoke(!result.removedScaffold, "welcome scaffold copy is absent");
  assertSmoke(!result.horizontalOverflow, "welcome has no horizontal overflow");
  assertSmoke(result.centerDeltaX < 4, `welcome is horizontally centered (${result.centerDeltaX}px)`);
  assertSmoke(result.centerDeltaY < 4, `welcome is vertically centered (${result.centerDeltaY}px)`);
}

async function assertStage15State(cdp, kind) {
  const result = await evaluate(cdp, `(() => {
    const text = document.body.innerText;
    const timeline = document.querySelector('.timeline');
    const composer = document.querySelector('.composer');
    const answerRows = [...document.querySelectorAll('[data-testid="answer-row"]')];
    const transcriptAnswerRows = [...document.querySelectorAll('[data-testid="transcript-answer-row"]')];
    const thinkingToggle = document.querySelector('.thinking-toggle');
    const answerText = answerRows.map((row) => row.innerText).join('\\n');
    const composerRect = composer?.getBoundingClientRect();
    const timelineRect = timeline?.getBoundingClientRect();
    const boundedSelectors = '.workbench-main,.agent-header,.timeline,.composer,.message-bubble,.thinking-block,.tool-activity-card,.timeline-row,.hitl-panel';
    const viewportEscapes = [...document.querySelectorAll(boundedSelectors)]
      .filter((node) => {
        const style = getComputedStyle(node);
        if (style.display === 'none' || style.visibility === 'hidden') {
          return false;
        }
        const rect = node.getBoundingClientRect();
        return rect.width > 0 && rect.height > 0 && (rect.left < -1 || rect.right > window.innerWidth + 1);
      })
      .map((node) => node.className || node.getAttribute('data-testid') || node.tagName);
    return {
      text,
      answerCount: answerRows.length,
      transcriptAnswerCount: transcriptAnswerRows.length,
      answerText,
      promptValue: document.querySelector('input[aria-label="Prompt"]')?.value ?? '',
      hasInspector: text.includes('Inspector') || Boolean(document.querySelector('.inspector')),
      hasDefaultDebug: ['Run fixture', 'Run error fixture', 'Run HITL fixture', 'Safety and diagnostics', 'Project knowledge', 'Run context'].some((value) => text.includes(value)),
      hasEventCount: /\\b\\d+ events\\b/i.test(text),
      hasDoneRow: Boolean(document.querySelector('.done-row')),
      timelineHasCompletedCard: [...document.querySelectorAll('.timeline .timeline-row, .timeline .message-row')]
        .some((node) => node.innerText.trim() === 'Completed'),
      thinkingExpanded: thinkingToggle?.getAttribute('aria-expanded') === 'true',
      hiddenThinkingVisible: text.includes('Hidden stage15 planning detail'),
      toolMarkerInAnswer: answerText.includes('TAIL_MARKER_STAGE15'),
      horizontalOverflow: document.documentElement.scrollWidth > window.innerWidth + 1,
      viewportEscapes,
      composerOverlapsTimeline: Boolean(composerRect && timelineRect && composerRect.top < timelineRect.bottom - 1),
      controlsReachable: [...document.querySelectorAll('.composer input, .composer button, .hitl-panel button')]
        .every((node) => {
          const rect = node.getBoundingClientRect();
          return rect.width > 0 && rect.height > 0 && rect.left >= -1 && rect.right <= window.innerWidth + 1 && rect.bottom <= window.innerHeight + 1;
        }),
      hasHitl: Boolean(document.querySelector('[aria-label="Human input required"]')),
      hasError: Boolean(document.querySelector('[role="alert"]')),
      hasTool: Boolean(document.querySelector('[data-testid="tool-activity-block"]')),
      hasThinking: Boolean(document.querySelector('[data-testid="thinking-block"]')),
      hasStop: [...document.querySelectorAll('button')].some((button) => button.textContent.trim() === 'Stop'),
    };
  })()`);

  assertSmoke(!result.hasInspector, `${kind}: default inspector is absent`);
  assertSmoke(!result.hasDefaultDebug, `${kind}: default debug and fixture controls are absent`);
  assertSmoke(!result.hasEventCount, `${kind}: event-count dashboard content is absent`);
  assertSmoke(!result.hasDoneRow && !result.timelineHasCompletedCard, `${kind}: Completed is not a prominent timeline card`);
  assertSmoke(!result.toolMarkerInAnswer, `${kind}: tool output marker is not answer text`);
  assertSmoke(!result.horizontalOverflow, `${kind}: document has no horizontal overflow`);
  assertSmoke(result.viewportEscapes.length === 0, `${kind}: content stays inside viewport (${result.viewportEscapes.join(', ')})`);
  assertSmoke(!result.composerOverlapsTimeline, `${kind}: composer does not overlap timeline`);
  assertSmoke(result.controlsReachable, `${kind}: composer and HITL controls are reachable`);

  if (kind === "normal") {
    assertSmoke(result.answerCount === 1, "normal: one assistant answer row");
    assertSmoke(result.answerText.includes("Stage 15 keeps one continuous answer."), "normal: continuous answer text is visible");
    assertSmoke(result.promptValue === "", "normal: composer clears after submit");
  }
  if (kind === "streaming") {
    assertSmoke(result.hasStop, "streaming: stop control is visible");
    assertSmoke(result.promptValue === "", "streaming: composer clears while run is active");
  }
  if (kind === "reasoning-collapsed") {
    assertSmoke(result.hasThinking, "reasoning: thinking block is visible");
    assertSmoke(!result.thinkingExpanded, "reasoning: thinking is collapsed by default");
    assertSmoke(!result.hiddenThinkingVisible, "reasoning: hidden thinking is not open by default");
  }
  if (kind === "reasoning-expanded") {
    assertSmoke(result.hasThinking && result.thinkingExpanded, "reasoning expanded: thinking disclosure opens intentionally");
    assertSmoke(result.hiddenThinkingVisible, "reasoning expanded: hidden thinking is visible after explicit expand");
  }
  if (kind === "tool") {
    assertSmoke(result.hasTool, "tool: tool activity block is visible");
    assertSmoke(result.answerCount === 1, "tool: answer stays one row");
    assertSmoke(result.text.includes("调用工具"), "tool: tool activity is labeled inline");
  }
  if (kind === "tool-expanded") {
    assertSmoke(result.hasTool, "tool expanded: tool activity block is visible");
    assertSmoke(result.text.includes("Collapse"), "tool expanded: long tool output can be collapsed again");
  }
  if (kind === "hitl") {
    assertSmoke(result.hasHitl, "HITL: human input panel is visible");
  }
  if (kind === "hitl-resumed") {
    assertSmoke(result.answerText.includes("Approval received for visual smoke."), "HITL resumed: assistant resume text is visible");
    assertSmoke(result.text.includes("Decision: approve"), "HITL resumed: resume decision is visible");
  }
  if (kind === "error") {
    assertSmoke(result.hasError, "error: alert row is visible");
    assertSmoke(result.answerCount === 1, "error: partial answer remains one row");
  }
  if (kind === "long-transcript") {
    assertSmoke(result.transcriptAnswerCount >= 6, "long transcript: multiple transcript answer rows render");
  }
}

async function submitPrompt(cdp, prompt) {
  await evaluate(cdp, `(() => {
    const input = document.querySelector('input[aria-label="Prompt"]');
    const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
    setter.call(input, ${JSON.stringify(prompt)});
    input.dispatchEvent(new Event('input', { bubbles: true }));
    return true;
  })()`);
  await waitForCondition(cdp, `document.querySelector('input[aria-label="Prompt"]').value === ${JSON.stringify(prompt)}`);
  await clickByText(cdp, "Run");
}

async function clickByText(cdp, label) {
  await evaluate(cdp, `(() => {
    const target = [...document.querySelectorAll('button')]
      .find((button) => button.textContent.trim().includes(${JSON.stringify(label)}) && !button.disabled);
    if (!target) {
      throw new Error('No enabled button found for ${label}');
    }
    target.click();
    return true;
  })()`);
}

function createApiServer() {
  const runs = new Map();
  return createServer(async (request, response) => {
    setCors(response);
    if (request.method === "OPTIONS") {
      response.writeHead(204);
      response.end();
      return;
    }

    const url = new URL(request.url ?? "/", "http://127.0.0.1");
    const path = url.pathname;
    try {
      if (request.method === "GET" && path === "/api/skills") {
        return json(response, { skills: [] });
      }
      if (request.method === "GET" && path === "/api/memory") {
        return json(response, { memories: [] });
      }
      if (request.method === "GET" && path === "/api/project/index/status") {
        return json(response, projectStatus());
      }
      if (request.method === "GET" && path === "/api/conversations") {
        return json(response, { conversations: [conversation("long-transcript", "Long transcript")] });
      }
      if (request.method === "POST" && path === "/api/conversations") {
        return json(response, { conversation: conversation("stage15-new", "New conversation") });
      }

      const transcriptMatch = path.match(/^\/api\/conversations\/([^/]+)\/transcript$/);
      if (request.method === "GET" && transcriptMatch) {
        const conversationId = decodeURIComponent(transcriptMatch[1]);
        return json(response, {
          conversation_id: conversationId,
          messages: conversationId === "long-transcript" ? longTranscriptMessages(conversationId) : [],
        });
      }

      if (request.method === "POST" && path === "/api/runs") {
        const body = await readJson(request);
        const run = createRunForPrompt(String(body.prompt ?? ""), runs);
        return json(response, run);
      }

      const eventsMatch = path.match(/^\/api\/runs\/([^/]+)\/events$/);
      if (request.method === "GET" && eventsMatch) {
        return streamEvents(response, runs.get(decodeURIComponent(eventsMatch[1])));
      }

      const resumeMatch = path.match(/^\/api\/runs\/([^/]+)\/resume$/);
      if (request.method === "POST" && resumeMatch) {
        return json(response, {
          status: "completed",
          thread_id: decodeURIComponent(resumeMatch[1]),
          interrupt_id: "stage15-interrupt",
          decision: "approve",
          events: [
            event(decodeURIComponent(resumeMatch[1]), "resume", 3, { interrupt_id: "stage15-interrupt", decision: "approve" }),
            event(decodeURIComponent(resumeMatch[1]), "text_delta", 4, { text: "Approval received for visual smoke." }),
            event(decodeURIComponent(resumeMatch[1]), "done", 5, { message: "Completed" }),
          ],
        });
      }

      const contextMatch = path.match(/^\/api\/runs\/([^/]+)\/context$/);
      if (request.method === "GET" && contextMatch) {
        return json(response, runContext(decodeURIComponent(contextMatch[1])));
      }

      response.writeHead(404, { "Content-Type": "application/json" });
      response.end(JSON.stringify({ detail: `Unhandled ${request.method} ${path}` }));
    } catch (error) {
      response.writeHead(500, { "Content-Type": "application/json" });
      response.end(JSON.stringify({ detail: error instanceof Error ? error.message : "Smoke API failed" }));
    }
  });
}

function createRunForPrompt(prompt, runs) {
  const normalized = prompt.toLowerCase();
  const scenario = normalized.includes("streaming")
    ? "streaming"
    : normalized.includes("reasoning")
      ? "reasoning"
      : normalized.includes("tool")
        ? "tool"
        : normalized.includes("hitl")
          ? "hitl"
          : normalized.includes("error")
            ? "error"
            : "normal";
  const threadId = `stage15-${scenario}`;
  runs.set(threadId, scenarioEvents(threadId, scenario));
  return {
    thread_id: threadId,
    conversation_id: `conversation-${scenario}`,
    turn_id: `turn-${scenario}`,
    status: "created",
    fixture: null,
    events_url: `/api/runs/${threadId}/events`,
    provider: { mode: "fixture", source: "fixture", fixture: "stage15-visual-smoke", fallback_reason: "no_api_key" },
  };
}

function scenarioEvents(threadId, scenario) {
  if (scenario === "streaming") {
    return {
      keepOpen: true,
      events: [
        event(threadId, "retry", 1, { attempt: 2, message: "Retrying deterministic stream" }),
        event(threadId, "checkpoint", 2, { checkpoint_id: "stage15-streaming", message: "Checkpoint saved while streaming" }),
      ],
    };
  }
  if (scenario === "reasoning") {
    return {
      events: [
        event(threadId, "thinking_delta", 1, { text: "Hidden stage15 planning detail" }),
        event(threadId, "thinking_delta", 2, { text: "Second hidden stage15 decision" }),
        event(threadId, "text_delta", 3, { text: "Reasoning answer remains visible." }),
        event(threadId, "done", 4, { message: "Completed" }),
      ],
    };
  }
  if (scenario === "tool") {
    return {
      events: [
        event(threadId, "tool_start", 1, { name: "project.search", call_id: "stage15-tool", message: "Searching deterministic project evidence" }),
        event(threadId, "tool_result", 2, {
          name: "project.search",
          call_id: "stage15-tool",
          status: "ok",
          metadata: { content_type: "application/json", truncated: true },
          result: `Long deterministic tool output for the visual smoke.\n${Array.from({ length: 18 }, (_, index) => (
            `/tmp/project/packages/stage15-module-${index}/src/really-long-file-name-that-must-wrap-without-horizontal-overflow-${index}.ts :: bounded fixture excerpt ${index} ${"x".repeat(42)}`
          )).join("\n")}\nTAIL_MARKER_STAGE15`,
        }),
        event(threadId, "text_delta", 3, { text: "Tool evidence is summarized without leaking raw output." }),
        event(threadId, "done", 4, { message: "Completed" }),
      ],
    };
  }
  if (scenario === "hitl") {
    return {
      events: [
        event(threadId, "interrupt", 1, {
          interrupt_id: "stage15-interrupt",
          kind: "approval",
          title: "Approve visual smoke step",
          body: "Approve this deterministic Stage 15 browser smoke step.",
          data: {},
          allowed_responses: [
            { id: "approve", label: "Approve", kind: "approve" },
            { id: "reject", label: "Reject", kind: "reject" },
          ],
        }),
        event(threadId, "checkpoint", 2, { checkpoint_id: "stage15-hitl", message: "HITL checkpoint saved" }),
      ],
    };
  }
  if (scenario === "error") {
    return {
      events: [
        event(threadId, "text_delta", 1, { text: "Partial answer before visual smoke error." }),
        event(threadId, "error", 2, { message: "Provider stream failed for visual smoke", failure_class: "provider_stream_error" }),
      ],
    };
  }
  return {
    events: [
      event(threadId, "text_delta", 1, { text: "Stage 15 " }),
      event(threadId, "text_delta", 2, { text: "keeps one continuous answer." }),
      event(threadId, "done", 3, { message: "Completed" }),
    ],
  };
}

function streamEvents(response, run) {
  if (!run) {
    response.writeHead(404, { "Content-Type": "application/json" });
    response.end(JSON.stringify({ detail: "Unknown run" }));
    return;
  }
  response.writeHead(200, {
    "Content-Type": "text/event-stream",
    "Cache-Control": "no-cache",
    Connection: "keep-alive",
    "Access-Control-Allow-Origin": "*",
  });
  let index = 0;
  let closed = false;
  response.on("close", () => {
    closed = true;
  });
  const sendNext = () => {
    if (closed) {
      return;
    }
    if (index >= run.events.length) {
      if (!run.keepOpen) {
        response.end();
      }
      return;
    }
    const next = run.events[index++];
    response.write(`event: ${next.type}\n`);
    response.write(`data: ${JSON.stringify(next)}\n\n`);
    setTimeout(sendNext, 60);
  };
  sendNext();
}

function longTranscriptMessages(conversationId) {
  const messages = [];
  for (let index = 0; index < 7; index += 1) {
    const turnId = `long-turn-${index}`;
    messages.push(transcriptMessage(conversationId, `long-user-${index}`, turnId, "user", `Long transcript prompt ${index}: compare this local project path /tmp/project/packages/very-long-package-name-${index}/src/index.ts with current Stage 15 requirements.`));
    messages.push(transcriptMessage(conversationId, `long-assistant-${index}`, turnId, "assistant", `Long transcript answer ${index}: Kira keeps this as a normal assistant bubble with wrapping text, no dashboard panel, no default inspector, and no horizontal overflow even when the response includes a long token ${"stage15wrap".repeat(12)}.`));
  }
  return messages;
}

function transcriptMessage(conversationId, id, turnId, role, text) {
  return {
    id,
    conversation_id: conversationId,
    turn_id: turnId,
    thread_id: "stage15-transcript",
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
        thread_id: "stage15-transcript",
        kind: "text",
        seq: 1,
        text,
        payload: {},
        visible: true,
        token_estimate: 1,
        created_at: "2026-05-15T10:00:00Z",
      },
    ],
    created_at: "2026-05-15T10:00:00Z",
    updated_at: "2026-05-15T10:00:00Z",
  };
}

function conversation(id, title) {
  return {
    id,
    title,
    status: "active",
    archived: false,
    active_head_message_id: null,
    created_at: "2026-05-15T10:00:00Z",
    updated_at: "2026-05-15T10:00:00Z",
  };
}

function projectStatus() {
  return {
    root_id: "stage15-root",
    root: "/tmp/project",
    status: "not_indexed",
    file_count: 0,
    chunk_count: 0,
    skipped_count: 0,
    omitted_count: 0,
    fts_available: true,
  };
}

function runContext(threadId) {
  return {
    thread_id: threadId,
    budget: { max_items: 20, max_chars: 24000, max_item_chars: 8000 },
    included: [],
    truncated: [],
    omitted: [],
    provider: { mode: "fixture", source: "fixture" },
    selected_skills: [],
  };
}

function event(threadId, type, seq, data) {
  return { type, thread_id: threadId, seq, data };
}

async function readJson(request) {
  const chunks = [];
  for await (const chunk of request) {
    chunks.push(chunk);
  }
  const text = Buffer.concat(chunks).toString("utf8");
  return text ? JSON.parse(text) : {};
}

function setCors(response) {
  response.setHeader("Access-Control-Allow-Origin", "*");
  response.setHeader("Access-Control-Allow-Headers", "Content-Type");
  response.setHeader("Access-Control-Allow-Methods", "GET,POST,PUT,PATCH,DELETE,OPTIONS");
}

function json(response, payload) {
  response.writeHead(200, { "Content-Type": "application/json" });
  response.end(JSON.stringify(payload));
}

async function listen(server) {
  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
  return server.address().port;
}

async function getFreePort() {
  const server = createServer();
  const port = await listen(server);
  await new Promise((resolve) => server.close(resolve));
  return port;
}

async function waitForHttp(nextUrl, label) {
  const deadline = Date.now() + 15_000;
  while (Date.now() < deadline) {
    try {
      const response = await fetch(nextUrl);
      if (response.ok) {
        return;
      }
    } catch {
      await delay(100);
    }
  }
  throw new Error(`${label} did not start at ${nextUrl}`);
}

async function waitForDebugger(debugPort) {
  const deadline = Date.now() + 10_000;
  while (Date.now() < deadline) {
    try {
      await getJson(`http://127.0.0.1:${debugPort}/json/version`);
      return;
    } catch {
      await delay(100);
    }
  }
  throw new Error("Chrome remote debugger did not start");
}

async function getJson(nextUrl) {
  const response = await fetch(nextUrl);
  if (!response.ok) {
    throw new Error(`HTTP ${response.status} for ${nextUrl}`);
  }
  return response.json();
}

async function connectCdp(wsUrl) {
  const ws = new WebSocket(wsUrl);
  const pending = new Map();
  const eventWaiters = new Map();
  let nextId = 1;

  await new Promise((resolve, reject) => {
    ws.addEventListener("open", resolve, { once: true });
    ws.addEventListener("error", reject, { once: true });
  });

  ws.addEventListener("message", (message) => {
    const data = JSON.parse(message.data);
    if (data.id && pending.has(data.id)) {
      const { resolve, reject } = pending.get(data.id);
      pending.delete(data.id);
      if (data.error) {
        reject(new Error(data.error.message));
      } else {
        resolve(data.result);
      }
      return;
    }
    if (data.method && eventWaiters.has(data.method)) {
      const waiters = eventWaiters.get(data.method);
      eventWaiters.delete(data.method);
      for (const resolve of waiters) {
        resolve(data.params ?? {});
      }
    }
  });

  return {
    send(method, params = {}) {
      const id = nextId++;
      ws.send(JSON.stringify({ id, method, params }));
      return new Promise((resolve, reject) => pending.set(id, { resolve, reject }));
    },
    waitForEvent(method) {
      return new Promise((resolve) => {
        const waiters = eventWaiters.get(method) ?? [];
        waiters.push(resolve);
        eventWaiters.set(method, waiters);
      });
    },
    close() {
      ws.close();
    },
  };
}

async function navigate(cdp, nextUrl) {
  const loaded = cdp.waitForEvent("Page.loadEventFired");
  await cdp.send("Page.navigate", { url: nextUrl });
  await loaded;
}

async function setViewport(cdp, width, height) {
  await cdp.send("Emulation.setDeviceMetricsOverride", {
    width,
    height,
    deviceScaleFactor: 1,
    mobile: width < 600,
  });
}

async function evaluate(cdp, expression) {
  const result = await cdp.send("Runtime.evaluate", {
    expression,
    awaitPromise: true,
    returnByValue: true,
  });
  if (result.exceptionDetails) {
    throw new Error(result.exceptionDetails.exception?.description ?? result.exceptionDetails.text ?? "Runtime evaluation failed");
  }
  return result.result.value;
}

async function waitForCondition(cdp, expression) {
  const deadline = Date.now() + 8_000;
  while (Date.now() < deadline) {
    if (await evaluate(cdp, expression)) {
      return;
    }
    await delay(100);
  }
  throw new Error(`Condition did not become true: ${expression}`);
}

async function screenshot(cdp, filePath) {
  const result = await cdp.send("Page.captureScreenshot", { format: "png", fromSurface: true });
  const buffer = Buffer.from(result.data, "base64");
  assertSmoke(buffer.length > 1000, `screenshot is non-empty: ${filePath}`);
  await writeFile(filePath, buffer);
}

function assertSmoke(condition, message) {
  if (!condition) {
    throw new Error(`Stage 15 visual smoke failed: ${message}`);
  }
}

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
