# Kira Agent Web

Vite React frontend for local Kira Agent development.

## Local Run

Recommended from the repository root:

```bash
scripts/kira dev
```

This starts FastAPI and Vite together, then prints the frontend URL. The Vite dev server proxies same-origin `/api` browser requests to the backend.

For focused frontend development:

```bash
cd web
pnpm install
pnpm dev
```

By default, frontend code calls same-origin `/api` paths. Configure the Vite proxy target when the backend is not on `http://127.0.0.1:8000`:

```bash
VITE_KIRA_DEV_API_TARGET=http://127.0.0.1:9000 pnpm dev
```

Use `VITE_KIRA_API_BASE` only for explicit split-host deployments where browser requests should go to a different API origin instead of the serving origin.

For a complete single-service run from the repository root:

```bash
scripts/kira serve --build
```

FastAPI serves the built Vite app and `/api/*` from the same origin, usually `http://127.0.0.1:8000/`.

## Local Demo Flow

1. Start the backend.
2. Start the frontend.
3. Open `http://localhost:5173`.
4. Click `立刻开始`.
5. Use `Run` for provider auto selection.

The default workbench is a light Mira-like conversation surface. It renders
right-aligned user prompts, Kira assistant identity rows, one continuous answer
body per turn, a subdued answer action bar, collapsed `思考过程`, inline tool
activity, and a quiet sticky bottom composer. The Stop control remains available
while a stream is active.

Stage 14 supersedes the historical Stage 10/11 dark cockpit as the default
product surface. `web/DESIGN.md` defines the current visual contract: one
centered Kira launch view with `一个专业的数据agent助手` and `立刻开始`, followed by
a light chat-first workbench. Fixture controls, event counts, and operator
inspector panels are not default primary content.

The conversation panel lists local conversations, can create an empty conversation, can trigger deterministic manual compaction, and lets follow-up runs reuse the selected `conversation_id`. When you select a conversation, prior visible transcript messages are restored before the current live stream. Transcript rows expose basic Fork and Rollback controls: Fork selects the new forked conversation, while Rollback refreshes the current transcript and shows inactive branch status. The `thread_id` shown in the run inspector is still the execution/replay/resume cursor for the current run, not the chat continuity key.

Hidden thinking arrives as `thinking_delta` and is rendered only inside the
collapsed `思考过程` disclosure. It is not merged into normal assistant answer
text or copied final-answer content.

The inspector includes panels for conversations, skill catalog/details, project knowledge indexing/search, local memory, and run context traces. Project search results show citations and stale markers; memory search shows score reasons and duplicate omissions; run context shows included, truncated, and omitted ContextItems, including transcript history, compaction summaries, stale summary omissions, inactive branch omissions, and replacement stub metadata, without exposing provider secrets or raw replaced output.

These inspector and diagnostic surfaces are non-default developer affordances.
The Stage 14 default route keeps them out of the primary chat surface while
preserving their frontend semantics for a future explicit debug entry point.

The Safety panel loads `GET /api/doctor`, filtered audit records, run/conversation/project/memory trace exports, and replacement inspection responses. It uses bounded JSON display and a frontend redaction fallback for API keys, bearer tokens, passwords, and secret-like text. Run trace and conversation trace buttons are disabled until a run or conversation is selected.

Memory controls can list and filter local records by query, scope, type, status, and tag; add or edit records with scope/type/confidence/tags/source metadata; run lifecycle actions; dry-run extraction; and approve, reject, or defer candidates. Use memory for a run by enabling `Use memory` or entering a memory query.

## Smoke

```bash
scripts/kira smoke-dev
scripts/kira smoke-serve
cd web
pnpm test
pnpm build
pnpm smoke:stage10
pnpm smoke:stage11 http://localhost:5173/
pnpm smoke:stage15
```

`pnpm smoke:stage10` runs DOM-level visual and accessibility smoke checks with
the existing Vitest/jsdom toolchain. For local browser review, start `pnpm dev`
and run `pnpm smoke:stage11 <dev-server-url>`; the browser smoke captures
desktop and narrow screenshots and checks welcome centering, sticky header and
composer, absence of default inspector/fixture controls, and horizontal overflow.

`pnpm smoke:stage15` is the no-provider-key browser visual gate. It starts a
mock local API and a Vite dev server, then captures desktop and narrow
screenshots for welcome, normal chat, streaming/status, collapsed and expanded
`思考过程`, tool activity, HITL, error, and long transcript states. The command
prints a temporary screenshot directory such as `/tmp/kira-stage15-visual-*`.

Stage 15 does not commit binary screenshot baselines. Treat the generated
screenshots plus DOM assertions as the local baseline evidence; intentional
visual changes should update `web/DESIGN.md`, the smoke assertions, and this
README wording in the same change.
