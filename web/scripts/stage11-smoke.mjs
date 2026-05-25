import { spawn } from "node:child_process";
import { mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

const url = process.argv[2] ?? "http://localhost:5174/";
const chromeBin =
  process.env.CHROME_BIN ?? "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const port = 9400 + Math.floor(Math.random() * 400);
const userDataDir = await mkdtemp(join(tmpdir(), "kira-stage11-chrome-"));
const outDir = await mkdtemp(join(tmpdir(), "kira-stage11-smoke-"));

const welcomeCheckExpression = `(() => {
  const shell = document.querySelector('.welcome-shell');
  const panel = document.querySelector('.welcome-panel');
  const shellRect = shell.getBoundingClientRect();
  const panelRect = panel.getBoundingClientRect();
  const text = document.body.innerText;
  return {
    hasProductCopy: text.includes('一个专业的数据agent助手'),
    hasStartAction: text.includes('立刻开始'),
    hasRemovedScaffoldCopy: ['FastAPI local', 'Read-only context', 'Auto or fixture', 'Local Web Agent', 'Local agent'].some((value) => text.includes(value)),
    centerDeltaX: Math.abs((panelRect.left + panelRect.width / 2) - (shellRect.left + shellRect.width / 2)),
    centerDeltaY: Math.abs((panelRect.top + panelRect.height / 2) - (shellRect.top + shellRect.height / 2)),
  };
})()`;

const workbenchCheckExpression = `(() => {
  const text = document.body.innerText;
  const header = document.querySelector('.agent-header');
  const composer = document.querySelector('.composer');
  return {
    hasRail: Boolean(document.querySelector('.task-rail')) && getComputedStyle(document.querySelector('.task-rail')).display !== 'none',
    hasTimeline: Boolean(document.querySelector('.timeline')),
    hasComposer: Boolean(composer),
    headerSticky: getComputedStyle(header).position === 'sticky',
    composerSticky: getComputedStyle(composer).position === 'sticky',
    noInspector: !text.includes('Inspector') && !document.querySelector('.inspector'),
    noFixtureButtons: !['Run fixture', 'Run error fixture', 'Run HITL fixture'].some((value) => text.includes(value)),
    horizontalOverflow: document.documentElement.scrollWidth > window.innerWidth + 1,
  };
})()`;

const chrome = spawn(chromeBin, [
  "--headless=new",
  "--disable-gpu",
  "--no-first-run",
  "--no-default-browser-check",
  `--remote-debugging-port=${port}`,
  `--user-data-dir=${userDataDir}`,
  "about:blank",
], { stdio: ["ignore", "pipe", "pipe"] });

try {
  await waitForDebugger(port);
  const tabs = await getJson(`http://127.0.0.1:${port}/json/list`);
  const page = tabs.find((tab) => tab.type === "page" && tab.webSocketDebuggerUrl);
  if (!page) {
    throw new Error("No Chrome page target available");
  }

  const cdp = await connectCdp(page.webSocketDebuggerUrl);
  await cdp.send("Page.enable");
  await cdp.send("Runtime.enable");

  await setViewport(cdp, 1280, 900);
  await navigate(cdp, url);
  const welcome = await evaluate(cdp, welcomeCheckExpression);
  assertSmoke(welcome.hasProductCopy, "welcome product copy is visible");
  assertSmoke(welcome.hasStartAction, "welcome start action is visible");
  assertSmoke(!welcome.hasRemovedScaffoldCopy, "welcome removed scaffold copy is absent");
  assertSmoke(welcome.centerDeltaX < 4, `welcome is horizontally centered (${welcome.centerDeltaX}px)`);
  assertSmoke(welcome.centerDeltaY < 4, `welcome is vertically centered (${welcome.centerDeltaY}px)`);
  await screenshot(cdp, join(outDir, "welcome-desktop.png"));

  await cdp.send("Runtime.evaluate", { expression: "document.querySelector('.primary-button')?.click()" });
  await waitForCondition(cdp, "Boolean(document.querySelector('.workbench-shell'))");
  const desktop = await evaluate(cdp, workbenchCheckExpression);
  assertWorkbench(desktop, "desktop");
  await screenshot(cdp, join(outDir, "workbench-desktop.png"));

  await setViewport(cdp, 390, 780);
  await waitForCondition(cdp, "Boolean(document.querySelector('.workbench-shell'))");
  const narrow = await evaluate(cdp, workbenchCheckExpression);
  assertWorkbench(narrow, "narrow");
  await screenshot(cdp, join(outDir, "workbench-narrow.png"));

  await cdp.close();
  console.log(JSON.stringify({ status: "ok", url, screenshots: outDir }, null, 2));
} finally {
  chrome.kill("SIGTERM");
  await new Promise((resolve) => {
    chrome.once("exit", resolve);
    setTimeout(resolve, 1_000);
  });
  await rm(userDataDir, { recursive: true, force: true, maxRetries: 3, retryDelay: 100 }).catch(() => {});
}

function assertWorkbench(result, label) {
  assertSmoke(result.hasRail || label === "narrow", `${label} rail is present or collapsed as expected`);
  assertSmoke(result.hasTimeline, `${label} timeline is present`);
  assertSmoke(result.hasComposer, `${label} composer is present`);
  assertSmoke(result.headerSticky, `${label} header is sticky`);
  assertSmoke(result.composerSticky, `${label} composer is sticky`);
  assertSmoke(result.noInspector, `${label} default inspector is absent`);
  assertSmoke(result.noFixtureButtons, `${label} fixture buttons are absent`);
  assertSmoke(!result.horizontalOverflow, `${label} has no horizontal overflow`);
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
    throw new Error(result.exceptionDetails.text ?? "Runtime evaluation failed");
  }
  return result.result.value;
}

async function waitForCondition(cdp, expression) {
  const deadline = Date.now() + 5_000;
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
  await writeFile(filePath, Buffer.from(result.data, "base64"));
}

function assertSmoke(condition, message) {
  if (!condition) {
    throw new Error(`Stage 11 smoke failed: ${message}`);
  }
}

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
