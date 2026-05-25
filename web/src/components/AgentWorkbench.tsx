import { FormEvent, useEffect, useRef, useState, type ReactNode, type RefObject } from "react";

import {
  compactConversation,
  createConversation,
  createMemory,
  createRun,
  decideMemoryCandidate,
  deleteMemory,
  extractMemory,
  forkConversation,
  getConversationTranscript,
  getConversationTrace,
  getDoctor,
  getMemoryTrace,
  getProjectIndexStatus,
  getProjectTrace,
  getRunContext,
  getRunTrace,
  getSkill,
  inspectReplacement,
  listAudit,
  listMemory,
  listConversations,
  listSkills,
  memoryAction,
  refreshProjectIndex,
  resumeRun,
  rollbackConversation,
  searchMemory,
  searchProject,
  streamRunEvents,
  updateConversation,
  updateMemory,
} from "../lib/api";
import { buildChatTurns, type ChatMessageViewModel, type ChatTurnItem, type ChatTurnViewModel, type RunStatusViewModel } from "../lib/chatTurns";
import { copyTextToClipboard } from "../lib/clipboard";
import type {
  Conversation,
  AuditRecord,
  DoctorDiagnostics,
  InterruptPayload,
  KiraEvent,
  MemoryCandidate,
  MemoryAction,
  MemoryRecord,
  MemoryScope,
  MemorySearchResponse,
  MemoryStatus,
  MemoryType,
  ProjectIndexStatus,
  ProjectSearchResponse,
  ProviderMetadata,
  ReplacementInspection,
  ResumeRequest,
  RunContextTrace,
  RunCreateRequest,
  RunCreateResponse,
  SkillMetadata,
  TraceExport,
  TranscriptMessage,
} from "../lib/types";
import { ThinkingBlock } from "./ThinkingBlock";
import { ToolActivityBlock } from "./ToolActivityBlock";

type MemoryFormInput = {
  text: string;
  scope: MemoryScope;
  type: MemoryType;
  confidence: number;
  tags: string[];
  sourceSummary: string;
};

type MarkdownBlock =
  | { kind: "code"; language: string; text: string }
  | { kind: "heading"; level: 1 | 2 | 3; text: string }
  | { kind: "list"; ordered: boolean; items: string[] }
  | { kind: "table"; headers: string[]; rows: string[][] }
  | { kind: "paragraph"; text: string };

const PINNED_CONVERSATIONS_KEY = "kira:pinned-conversations";
const DEFAULT_PROJECT_ROOT = import.meta.env.VITE_KIRA_PROJECT_ROOT ?? "";

export function AgentWorkbench() {
  const [events, setEvents] = useState<KiraEvent[]>([]);
  const [running, setRunning] = useState(false);
  const [prompt, setPrompt] = useState("");
  const [activePrompt, setActivePrompt] = useState<string | null>(null);
  const [threadId, setThreadId] = useState<string | null>(null);
  const [turnId, setTurnId] = useState<string | null>(null);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [selectedConversationId, setSelectedConversationId] = useState<string | null>(null);
  const [transcriptMessages, setTranscriptMessages] = useState<TranscriptMessage[]>([]);
  const [provider, setProvider] = useState<ProviderMetadata | null>(null);
  const [pendingInterrupt, setPendingInterrupt] = useState<InterruptPayload | null>(null);
  const [resumeError, setResumeError] = useState<string | null>(null);
  const [skills, setSkills] = useState<SkillMetadata[]>([]);
  const [selectedSkillId, setSelectedSkillId] = useState("");
  const [skillDetail, setSkillDetail] = useState<SkillMetadata | null>(null);
  const [projectRoot, setProjectRoot] = useState(DEFAULT_PROJECT_ROOT);
  const [projectQuery, setProjectQuery] = useState("");
  const [projectStatus, setProjectStatus] = useState<ProjectIndexStatus | null>(null);
  const [projectSearch, setProjectSearch] = useState<ProjectSearchResponse | null>(null);
  const [contextTrace, setContextTrace] = useState<RunContextTrace | null>(null);
  const [compactStatus, setCompactStatus] = useState<string | null>(null);
  const [branchStatus, setBranchStatus] = useState<string | null>(null);
  const [clearStatus, setClearStatus] = useState<string | null>(null);
  const [includeMemory, setIncludeMemory] = useState(false);
  const [memoryQuery, setMemoryQuery] = useState("");
  const [memoryScope, setMemoryScope] = useState<MemoryScope | "">("");
  const [memoryType, setMemoryType] = useState<MemoryType | "">("");
  const [memoryStatus, setMemoryStatus] = useState<MemoryStatus | "">("active");
  const [memoryTag, setMemoryTag] = useState("");
  const [memories, setMemories] = useState<MemoryRecord[]>([]);
  const [memorySearchResult, setMemorySearchResult] = useState<MemorySearchResponse | null>(null);
  const [memoryCandidates, setMemoryCandidates] = useState<MemoryCandidate[]>([]);
  const [memoryError, setMemoryError] = useState<string | null>(null);
  const [doctor, setDoctor] = useState<DoctorDiagnostics | null>(null);
  const [audit, setAudit] = useState<AuditRecord[]>([]);
  const [traceExport, setTraceExport] = useState<TraceExport | null>(null);
  const [replacementInspection, setReplacementInspection] = useState<ReplacementInspection | null>(null);
  const [safetyError, setSafetyError] = useState<string | null>(null);
  const [replacementId, setReplacementId] = useState("");
  const [streamNotice, setStreamNotice] = useState<string | null>(null);
  const stopStreamRef = useRef<(() => void) | null>(null);
  const currentRunRef = useRef<{ threadId: string } | null>(null);
  const selectedConversationIdRef = useRef<string | null>(null);
  const promptInputRef = useRef<HTMLInputElement | null>(null);

  function refreshMemory(query = memoryQuery) {
    void listMemory({
      query,
      scope: memoryScope || undefined,
      type: memoryType || undefined,
      status: memoryStatus || undefined,
      tag: memoryTag.trim() || undefined,
      include_non_injectable: memoryStatus !== "active",
    })
      .then((result) => {
        setMemories(result.memories);
        setMemoryError(null);
      })
      .catch((error) => setMemoryError(error instanceof Error ? error.message : "Failed to load memory"));
  }

  function refreshSkills(root = projectRoot) {
    void listSkills(root.trim() || undefined)
      .then((result) => {
        setSkills(result.skills);
        setSelectedSkillId((current) => (current && result.skills.some((skill) => skill.skill_id === current) ? current : ""));
      })
      .catch(() => setSkills([]));
  }

  function refreshConversations() {
    void listConversations()
      .then((result) => setConversations(result.conversations))
      .catch(() => setConversations([]));
  }

  function loadTranscript(conversationId: string): Promise<TranscriptMessage[]> {
    return getConversationTranscript(conversationId)
      .then((result) => {
        setTranscriptMessages(result.messages);
        return result.messages;
      })
      .catch(() => {
        setTranscriptMessages([]);
        return [];
      });
  }

  function replaceCompletedRunWithTranscript(run: RunCreateResponse) {
    const conversationId = run.conversation_id;
    if (!conversationId) {
      return;
    }
    void getConversationTranscript(conversationId)
      .then((result) => {
        const stillShowingCompletedRun = currentRunRef.current?.threadId === run.thread_id;
        const stillOnConversation = selectedConversationIdRef.current === null || selectedConversationIdRef.current === conversationId;
        const transcriptContainsCompletedRun = result.messages.some(
          (message) => message.thread_id === run.thread_id || (run.turn_id && message.turn_id === run.turn_id),
        );
        if (!stillShowingCompletedRun || !stillOnConversation || !transcriptContainsCompletedRun) {
          return;
        }
        setTranscriptMessages(result.messages);
        setEvents([]);
        setActivePrompt(null);
      })
      .catch(() => {
        // Keep the live event buffer visible if transcript refresh fails.
      });
  }

  function compactSelectedConversation() {
    if (!selectedConversationId || running) {
      return;
    }
    setCompactStatus("Compacting");
    void compactConversation(selectedConversationId, { summarizer_mode: "fixture", tail_messages: 4 })
      .then((result) => {
        setCompactStatus(`Compacted ${result.replaced_raw_messages} messages`);
        loadTranscript(selectedConversationId);
        refreshConversations();
        setContextTrace({
          thread_id: "conversation-preview",
          budget: { max_items: 20, max_chars: 24_000, max_item_chars: 8_000 },
          included: [result.context_item],
          truncated: [],
          omitted: result.omitted,
          provider: {},
          selected_skills: [],
          transcript: {
            conversation_id: result.conversation_id,
            compacted: true,
            summary_id: result.summary.id,
            tail_start_message_id: result.tail_start_message_id,
          },
        });
      })
      .catch((error) => setCompactStatus(error instanceof Error ? "Compaction failed" : "Compaction failed"));
  }

  function forkFromMessage(messageId: string) {
    if (!selectedConversationId || running) {
      return;
    }
    setBranchStatus("Forking");
    void forkConversation(selectedConversationId, messageId)
      .then((result) => {
        const conversationId = result.conversation.id;
        setSelectedConversationId(conversationId);
        currentRunRef.current = null;
        setEvents([]);
        setActivePrompt(null);
        setContextTrace(null);
        setBranchStatus("Forked");
        refreshConversations();
        loadTranscript(conversationId);
      })
      .catch(() => setBranchStatus("Fork failed"));
  }

  function rollbackToMessage(messageId: string) {
    if (!selectedConversationId || running) {
      return;
    }
    setBranchStatus("Rolling back");
    void rollbackConversation(selectedConversationId, messageId)
      .then((result) => {
        const conversationId = result.conversation.id;
        currentRunRef.current = null;
        setEvents([]);
        setActivePrompt(null);
        setContextTrace(null);
        setBranchStatus(`Rolled back; ${result.inactive_message_ids.length} inactive`);
        refreshConversations();
        loadTranscript(conversationId);
      })
      .catch(() => setBranchStatus("Rollback failed"));
  }

  function createNewConversation() {
    void createConversation()
      .then((result) => {
        const conversationId = result.conversation.id;
        setSelectedConversationId(conversationId);
        currentRunRef.current = null;
        setTranscriptMessages([]);
        setEvents([]);
        setActivePrompt(null);
        setContextTrace(null);
        setBranchStatus(null);
        refreshConversations();
      })
      .catch(() => refreshConversations());
  }

  async function clearConversationHistory() {
    if (running || conversations.length === 0) {
      return;
    }

    setClearStatus("Clearing history");
    const conversationIds = conversations.map((conversation) => conversation.id);
    try {
      await Promise.all(conversationIds.map((conversationId) => updateConversation(conversationId, { archived: true })));
      currentRunRef.current = null;
      setSelectedConversationId(null);
      setTranscriptMessages([]);
      setEvents([]);
      setActivePrompt(null);
      setContextTrace(null);
      setBranchStatus(null);
      setCompactStatus(null);
      setConversations([]);
      setClearStatus(`Cleared ${conversationIds.length} conversation${conversationIds.length === 1 ? "" : "s"}`);
      refreshConversations();
    } catch {
      setClearStatus("Clear failed. Please try again.");
    }
  }

  async function deleteConversation(conversationId: string) {
    if (running) {
      return;
    }

    try {
      await updateConversation(conversationId, { archived: true });
      setConversations((current) => current.filter((conversation) => conversation.id !== conversationId));
      if (selectedConversationId === conversationId) {
        currentRunRef.current = null;
        setSelectedConversationId(null);
        setTranscriptMessages([]);
        setEvents([]);
        setActivePrompt(null);
        setContextTrace(null);
      }
      setClearStatus("Conversation deleted");
      refreshConversations();
    } catch {
      setClearStatus("Delete failed. Please try again.");
    }
  }

  async function renameConversation(conversationId: string, title: string) {
    const nextTitle = title.trim();
    if (nextTitle.length === 0 || running) {
      return;
    }

    try {
      const result = await updateConversation(conversationId, { title: nextTitle });
      setConversations((current) => current.map((conversation) => (conversation.id === conversationId ? result.conversation : conversation)));
      setClearStatus(null);
    } catch {
      setClearStatus("Rename failed. Please try again.");
    }
  }

  useEffect(() => {
    refreshSkills(DEFAULT_PROJECT_ROOT);
    void getProjectIndexStatus()
      .then(setProjectStatus)
      .catch(() => setProjectStatus(null));
    refreshConversations();
    refreshMemory("");
  }, []);

  useEffect(() => {
    selectedConversationIdRef.current = selectedConversationId;
  }, [selectedConversationId]);

  async function startRun(options: { fixture?: string; skillId?: string; promptOverride?: string } = {}) {
    const nextPrompt = (options.promptOverride ?? prompt).trim();
    if (nextPrompt.length === 0 || running) {
      return;
    }

    setEvents([]);
    setRunning(true);
    setPendingInterrupt(null);
    setResumeError(null);
    setSafetyError(null);
    setContextTrace(null);
    setStreamNotice(null);
    setActivePrompt(nextPrompt);
    // Optimistically clear the composer so users do not see the same prompt twice while awaiting createRun.
    // If the request fails we restore the original input so nothing is lost.
    const previousPrompt = prompt;
    const shouldClearComposer = options.promptOverride === undefined;
    if (shouldClearComposer) {
      setPrompt("");
    }
    const runRequest: RunCreateRequest = {
      prompt: options.promptOverride ?? nextPrompt,
      provider_mode: options.fixture ? "fixture" : "auto",
      ...(selectedConversationId ? { conversation_id: selectedConversationId } : {}),
      skill_id: options.skillId ?? (selectedSkillId || undefined),
      ...(options.fixture ? { fixture: options.fixture } : {}),
      ...(projectRoot.trim() ? { project_root: projectRoot.trim() } : {}),
      ...(projectQuery.trim() ? { project_context_query: projectQuery.trim(), project_context_limit: 5 } : {}),
      ...(includeMemory || memoryQuery.trim() ? { include_memory: true, memory_query: memoryQuery.trim() || nextPrompt, memory_top_k: 5 } : {}),
    };
    let run;
    try {
      run = await createRun(runRequest);
    } catch (error) {
      setSafetyError(error instanceof Error ? error.message : "Failed to create run");
      setRunning(false);
      // Keep activePrompt so the user bubble remains visible even when run creation fails.
      // Restore composer on failure so the user can retry without retyping.
      if (shouldClearComposer) {
        setPrompt(previousPrompt);
      }
      return;
    }
    requestAnimationFrame(() => promptInputRef.current?.focus());
    setThreadId(run.thread_id);
    setTurnId(run.turn_id ?? null);
    currentRunRef.current = { threadId: run.thread_id };
    if (run.conversation_id) {
      setSelectedConversationId(run.conversation_id);
      refreshConversations();
    }
    setProvider(run.provider);
    const stop = streamRunEvents(run.events_url, {
      onEvent(event) {
        setEvents((current) => [...current, event]);
        if (event.type === "interrupt") {
          const interrupt = toInterrupt(event.data);
          setPendingInterrupt(interrupt);
          setRunning(false);
          stopStreamRef.current = null;
          stop();
        }
        if (event.type === "done" || event.type === "error") {
          setRunning(false);
          setPendingInterrupt(null);
          stopStreamRef.current = null;
          void getRunContext(run.thread_id)
            .then(setContextTrace)
            .catch(() => setContextTrace(null));
          if (run.conversation_id) {
            refreshConversations();
            replaceCompletedRunWithTranscript(run);
          }
          stop();
        }
      },
      onError() {
        setStreamNotice("Stream disconnected; inspect replay or trace if the run does not complete.");
        setRunning(false);
        stopStreamRef.current = null;
        stop();
      },
    });
    stopStreamRef.current = stop;
  }

  async function submitResume(request: ResumeRequest) {
    if (!threadId || !pendingInterrupt) {
      return;
    }
    setResumeError(null);
    setRunning(true);
    try {
      const result = await resumeRun(threadId, request);
      setEvents((current) => [...current, ...result.events]);
      setPendingInterrupt(null);
      setRunning(false);
      requestAnimationFrame(() => promptInputRef.current?.focus());
    } catch (error) {
      setResumeError(error instanceof Error ? error.message : "Failed to resume run");
      setRunning(false);
    }
  }

  function stopRun() {
    stopStreamRef.current?.();
    stopStreamRef.current = null;
    setRunning(false);
  }

  function submitPrompt(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void startRun();
  }

  function selectPromptSkill(skillId: string) {
    setSelectedSkillId(skillId);
    setPrompt(stripSlashSkillQuery(prompt));
    requestAnimationFrame(() => promptInputRef.current?.focus());
  }

  function loadDoctor() {
    void getDoctor()
      .then((result) => {
        setDoctor(result);
        setSafetyError(null);
      })
      .catch((error) => setSafetyError(error instanceof Error ? error.message : "Failed to load doctor diagnostics"));
  }

  function loadAudit() {
    void listAudit({ thread_id: threadId ?? undefined, conversation_id: selectedConversationId ?? undefined, limit: 25 })
      .then((result) => {
        setAudit(result.records);
        setSafetyError(null);
      })
      .catch((error) => setSafetyError(error instanceof Error ? error.message : "Failed to load audit records"));
  }

  function loadTrace(scope: "run" | "conversation" | "project" | "memory") {
    const request =
      scope === "run" && threadId
        ? getRunTrace(threadId)
        : scope === "conversation" && selectedConversationId
          ? getConversationTrace(selectedConversationId)
          : scope === "project"
            ? getProjectTrace(projectRoot.trim() || undefined)
            : getMemoryTrace(threadId ? { thread_id: threadId } : {});
    void request
      .then((result) => {
        setTraceExport(result);
        setSafetyError(null);
      })
      .catch((error) => setSafetyError(error instanceof Error ? error.message : "Failed to load trace export"));
  }

  function inspectReplacementById() {
    if (!replacementId.trim()) {
      return;
    }
    void inspectReplacement(replacementId.trim())
      .then((result) => {
        setReplacementInspection(result);
        setSafetyError(null);
      })
      .catch((error) => setSafetyError(error instanceof Error ? error.message : "Replacement inspection denied or unavailable"));
  }

  function selectConversation(conversationId: string) {
    setSelectedConversationId(conversationId || null);
    currentRunRef.current = null;
    setEvents([]);
    setActivePrompt(null);
    setContextTrace(null);
    setCompactStatus(null);
    setBranchStatus(null);
    setClearStatus(null);
    if (conversationId) {
      loadTranscript(conversationId);
    } else {
      setTranscriptMessages([]);
    }
  }

  const runStatus = getWorkbenchStatus({ running, pendingInterrupt, events, streamNotice });
  const selectedConversation = conversations.find((conversation) => conversation.id === selectedConversationId) ?? null;
  const activeSkill = skills.find((skill) => skill.skill_id === selectedSkillId) ?? null;
  const chatTurns = buildChatTurns({ transcriptMessages, activePrompt, events, threadId, turnId });

  return (
    <main className="workbench-shell">
      <TaskRail
        conversations={conversations}
        selectedConversationId={selectedConversationId}
        runStatus={runStatus}
        clearStatus={clearStatus}
        onCreate={createNewConversation}
        onClear={clearConversationHistory}
        onDelete={deleteConversation}
        onRename={renameConversation}
        onSelect={selectConversation}
        clearDisabled={running || conversations.length === 0}
      />

      <section className="workbench-main" aria-label="Kira workbench">
        <AgentHeader
          runStatus={runStatus}
          provider={provider}
          selectedConversation={selectedConversation}
          activeSkill={activeSkill}
        />
        <section className="timeline" aria-label="Run timeline">
          {streamNotice ? <StreamNotice message={streamNotice} /> : null}
          {chatTurns.length === 0 ? <EmptyTimeline /> : null}
          {chatTurns.map((turn) => (
            <ChatTurn
              key={turn.id}
              turn={turn}
              disabled={running || !selectedConversationId}
            />
          ))}
        </section>
        <footer className="composer">
          {pendingInterrupt ? (
            <HitlPanel interrupt={pendingInterrupt} error={resumeError} onSubmit={(request) => void submitResume(request)} />
          ) : (
            <PromptComposer
              prompt={prompt}
              setPrompt={setPrompt}
              running={running}
              inputRef={promptInputRef}
              skills={skills}
              selectedSkillId={selectedSkillId}
              onSkillSelect={selectPromptSkill}
              onSkillClear={() => setSelectedSkillId("")}
              onSubmit={submitPrompt}
              onStop={stopRun}
            />
          )}
        </footer>
      </section>
    </main>
  );
}

function TaskRail({
  conversations,
  selectedConversationId,
  runStatus,
  clearStatus,
  onCreate,
  onClear,
  onDelete,
  onRename,
  onSelect,
  clearDisabled,
}: {
  conversations: Conversation[];
  selectedConversationId: string | null;
  runStatus: string;
  clearStatus: string | null;
  onCreate: () => void;
  onClear: () => void;
  onDelete: (conversationId: string) => void;
  onRename: (conversationId: string, title: string) => void;
  onSelect: (conversationId: string) => void;
  clearDisabled: boolean;
}) {
  const [menuConversationId, setMenuConversationId] = useState<string | null>(null);
  const [renameConversationId, setRenameConversationId] = useState<string | null>(null);
  const [renameDraft, setRenameDraft] = useState("");
  const [pinnedConversationIds, setPinnedConversationIds] = useState<string[]>(() => readPinnedConversationIds());
  const visibleConversations = [...conversations]
    .sort((left, right) => {
      const leftPinned = pinnedConversationIds.includes(left.id);
      const rightPinned = pinnedConversationIds.includes(right.id);
      if (leftPinned === rightPinned) {
        return 0;
      }
      return leftPinned ? -1 : 1;
    })
    .slice(0, 8);

  useEffect(() => {
    writePinnedConversationIds(pinnedConversationIds);
  }, [pinnedConversationIds]);

  function togglePinned(conversationId: string) {
    setPinnedConversationIds((current) =>
      current.includes(conversationId) ? current.filter((pinnedId) => pinnedId !== conversationId) : [...current, conversationId],
    );
    setMenuConversationId(null);
  }

  function startRename(conversation: Conversation) {
    setRenameConversationId(conversation.id);
    setRenameDraft(conversation.title || "");
    setMenuConversationId(null);
  }

  function submitRename(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!renameConversationId) {
      return;
    }
    onRename(renameConversationId, renameDraft);
    setRenameConversationId(null);
    setRenameDraft("");
  }

  function deleteFromMenu(conversationId: string) {
    setPinnedConversationIds((current) => current.filter((pinnedId) => pinnedId !== conversationId));
    onDelete(conversationId);
    setMenuConversationId(null);
  }

  return (
    <aside className="task-rail" aria-label="Task rail">
      <div className="rail-brand">
        <span className="agent-avatar rail-avatar" aria-hidden="true">
          K
        </span>
        <div>
          <strong>Kira</strong>
          <span>一个专业的数据agent助手</span>
        </div>
      </div>
      <button className="primary-button rail-new-task" type="button" onClick={onCreate}>
        New task
      </button>
      <button className="secondary-button rail-clear-history" type="button" onClick={onClear} disabled={clearDisabled}>
        Clear history
      </button>
      <div className="rail-status" aria-label="Current conversation status">
        <span>Current state</span>
        <strong>{runStatus}</strong>
      </div>
      {clearStatus ? <p className="rail-clear-status" role="status">{clearStatus}</p> : null}
      <div className="rail-list" aria-label="Recent tasks">
        {conversations.length === 0 ? (
          <p>No saved tasks yet</p>
        ) : (
          visibleConversations.map((conversation) => {
            const selected = conversation.id === selectedConversationId;
            const pinned = pinnedConversationIds.includes(conversation.id);
            const menuOpen = menuConversationId === conversation.id;
            const renaming = renameConversationId === conversation.id;
            return (
              <div key={conversation.id} className="rail-task-row">
                {renaming ? (
                  <form className="rail-rename-form" onSubmit={submitRename}>
                    <input
                      aria-label={`Rename ${conversation.title || conversation.id}`}
                      autoFocus
                      value={renameDraft}
                      onChange={(event) => setRenameDraft(event.target.value)}
                      onBlur={() => {
                        setRenameConversationId(null);
                        setRenameDraft("");
                      }}
                    />
                  </form>
                ) : (
                  <button
                    type="button"
                    className={`rail-task ${selected ? "is-selected" : ""}`}
                    onClick={() => onSelect(conversation.id)}
                    aria-pressed={selected}
                    aria-label={`Select task ${conversation.title || conversation.id}`}
                  >
                    <strong>{pinned ? "Pin · " : ""}{conversation.title || "Untitled task"}</strong>
                    <span>{conversation.status} · {conversation.id}</span>
                  </button>
                )}
                <button
                  type="button"
                  className="rail-task-menu-button"
                  aria-haspopup="menu"
                  aria-expanded={menuOpen}
                  aria-label={`Open actions for ${conversation.title || conversation.id}`}
                  onClick={() => setMenuConversationId(menuOpen ? null : conversation.id)}
                >
                  ⋯
                </button>
                {menuOpen ? (
                  <div className="rail-task-menu" role="menu">
                    <button type="button" role="menuitem" onClick={() => togglePinned(conversation.id)}>
                      <span aria-hidden="true">☆</span>
                      {pinned ? "Unpin" : "Pin"}
                    </button>
                    <button type="button" role="menuitem" onClick={() => startRename(conversation)}>
                      <span aria-hidden="true">✎</span>
                      Rename
                    </button>
                    <button type="button" role="menuitem" className="is-danger" onClick={() => deleteFromMenu(conversation.id)}>
                      <span aria-hidden="true">⌫</span>
                      Delete
                    </button>
                  </div>
                ) : null}
              </div>
            );
          })
        )}
      </div>
    </aside>
  );
}

function AgentHeader({
  runStatus,
  provider,
  selectedConversation,
  activeSkill,
}: {
  runStatus: string;
  provider: ProviderMetadata | null;
  selectedConversation: Conversation | null;
  activeSkill: SkillMetadata | null;
}) {
  return (
    <header className="agent-header">
      <div className="agent-identity">
        <span className="agent-avatar" aria-hidden="true">
          K
        </span>
        <div>
          <p className="eyebrow">Kira Agent</p>
          <h2>{selectedConversation?.title || "New conversation"}</h2>
        </div>
      </div>
      <div className="agent-meta" aria-label="Conversation metadata">
        <span>{runStatus}</span>
        <span>{formatProvider(provider)}</span>
        {activeSkill ? <span>{activeSkill.name}</span> : null}
      </div>
    </header>
  );
}

function ConversationPanel({
  conversations,
  selectedConversationId,
  compactStatus,
  branchStatus,
  onCreate,
  onRefresh,
  onCompact,
  onSelect,
}: {
  conversations: Conversation[];
  selectedConversationId: string | null;
  compactStatus: string | null;
  branchStatus: string | null;
  onCreate: () => void;
  onRefresh: () => void;
  onCompact: () => void;
  onSelect: (conversationId: string) => void;
}) {
  return (
    <section className="side-panel" aria-label="Conversations">
      <h3>Conversations</h3>
      <select aria-label="Active conversation" value={selectedConversationId ?? ""} onChange={(event) => onSelect(event.target.value)}>
        <option value="">New conversation</option>
        {conversations.map((conversation) => (
          <option key={conversation.id} value={conversation.id}>
            {conversation.title || conversation.id}
          </option>
        ))}
      </select>
      <div className="panel-actions">
        <button className="secondary-button compact-button" type="button" onClick={onCreate}>
          Create
        </button>
        <button className="secondary-button compact-button" type="button" onClick={onRefresh}>
          Refresh
        </button>
        <button className="secondary-button compact-button" type="button" onClick={onCompact} disabled={!selectedConversationId}>
          Compact
        </button>
      </div>
      {compactStatus ? <p className="muted-text" role="status">{compactStatus}</p> : null}
      {branchStatus ? <p className="muted-text" role="status">{branchStatus}</p> : null}
      <div className="side-list">
        {conversations.slice(0, 5).map((conversation) => (
          <div key={conversation.id}>
            <strong>{conversation.title || conversation.id}</strong>
            <span>{conversation.status} · {conversation.id}</span>
          </div>
        ))}
      </div>
    </section>
  );
}

function SkillPanel({
  skills,
  selectedSkillId,
  skillDetail,
  onSelect,
  onLoadDetail,
}: {
  skills: SkillMetadata[];
  selectedSkillId: string;
  skillDetail: SkillMetadata | null;
  onSelect: (skillId: string) => void;
  onLoadDetail: (skillId: string) => void;
}) {
  return (
    <section className="side-panel" aria-label="Skills">
      <h3>Skills</h3>
      <select aria-label="Active skill" value={selectedSkillId} onChange={(event) => onSelect(event.target.value)}>
        <option value="">None</option>
        {skills.map((skill) => (
          <option key={skill.skill_id} value={skill.skill_id} disabled={skill.valid === false || skill.active === false}>
            {skill.name}
          </option>
        ))}
      </select>
      {selectedSkillId ? (
        <button className="secondary-button compact-button" type="button" onClick={() => onLoadDetail(selectedSkillId)}>
          Details
        </button>
      ) : null}
      <div className="side-list">
        {skills.slice(0, 6).map((skill) => (
          <div key={skill.skill_id}>
            <strong>{skill.name}</strong>
            <span>{skill.source?.key ?? "built-in"} · {skill.valid === false ? "invalid" : skill.active === false ? "shadowed" : "active"}</span>
          </div>
        ))}
      </div>
      {skillDetail ? (
        <pre className="detail-box">
{JSON.stringify(
  {
    workflows: skillDetail.workflows?.map((workflow) => String(workflow.name ?? "workflow")),
    tools: skillDetail.allowed_tools,
    permissions: skillDetail.permissions ?? {},
    fixtures: skillDetail.fixtures ?? [],
    diagnostics: skillDetail.diagnostics ?? [],
    body_loaded: skillDetail.body_loaded,
  },
  null,
  2,
)}
        </pre>
      ) : null}
    </section>
  );
}

const MEMORY_SCOPES: MemoryScope[] = ["session", "projectLocal", "project", "user"];
const MEMORY_TYPES: MemoryType[] = ["preference", "feedback", "decision", "project", "reference", "fact", "workflow"];
const MEMORY_STATUSES: MemoryStatus[] = ["active", "stale", "archived"];

function MemoryPanel({
  includeMemory,
  memoryQuery,
  memoryScope,
  memoryType,
  memoryStatus,
  memoryTag,
  memories,
  searchResult,
  candidates,
  error,
  onIncludeChange,
  onQueryChange,
  onScopeChange,
  onTypeChange,
  onStatusChange,
  onTagChange,
  onRefresh,
  onSearch,
  onAdd,
  onEdit,
  onAction,
  onDelete,
  onExtract,
  onCandidate,
}: {
  includeMemory: boolean;
  memoryQuery: string;
  memoryScope: MemoryScope | "";
  memoryType: MemoryType | "";
  memoryStatus: MemoryStatus | "";
  memoryTag: string;
  memories: MemoryRecord[];
  searchResult: MemorySearchResponse | null;
  candidates: MemoryCandidate[];
  error: string | null;
  onIncludeChange: (value: boolean) => void;
  onQueryChange: (value: string) => void;
  onScopeChange: (value: MemoryScope | "") => void;
  onTypeChange: (value: MemoryType | "") => void;
  onStatusChange: (value: MemoryStatus | "") => void;
  onTagChange: (value: string) => void;
  onRefresh: () => void;
  onSearch: () => void;
  onAdd: (input: MemoryFormInput) => void;
  onEdit: (memoryId: string, input: MemoryFormInput) => void;
  onAction: (memoryId: string, action: MemoryAction, extra?: Record<string, unknown>) => void;
  onDelete: (memoryId: string) => void;
  onExtract: () => void;
  onCandidate: (candidateId: string, decision: string, text?: string) => void;
}) {
  const [text, setText] = useState("");
  const [scope, setScope] = useState<MemoryScope>("projectLocal");
  const [type, setType] = useState<MemoryType>("fact");
  const [confidence, setConfidence] = useState(0.7);
  const [tags, setTags] = useState("");
  const [sourceSummary, setSourceSummary] = useState("");
  const [editingId, setEditingId] = useState<string | null>(null);
  const formValid = text.trim().length > 0 && confidence >= 0 && confidence <= 1;

  function input(): MemoryFormInput {
    return {
      text: text.trim(),
      scope,
      type,
      confidence,
      tags: tags.split(",").map((tag) => tag.trim()).filter(Boolean),
      sourceSummary: sourceSummary.trim(),
    };
  }

  function resetForm() {
    setText("");
    setScope("projectLocal");
    setType("fact");
    setConfidence(0.7);
    setTags("");
    setSourceSummary("");
    setEditingId(null);
  }

  function loadForEdit(memory: MemoryRecord) {
    setEditingId(memory.id);
    setText(memory.text);
    setScope(memory.scope);
    setType(memory.type);
    setConfidence(memory.confidence);
    setTags(memory.tags.join(", "));
    setSourceSummary(memory.source.summary ?? "");
  }

  return (
    <section className="side-panel" aria-label="Memory">
      <h3>Memory</h3>
      <label className="inline-control">
        <input type="checkbox" checked={includeMemory} onChange={(event) => onIncludeChange(event.target.checked)} />
        Use memory
      </label>
      <input aria-label="Memory query" value={memoryQuery} onChange={(event) => onQueryChange(event.target.value)} placeholder="Search or run memory query" />
      <div className="panel-actions">
        <button className="secondary-button compact-button" type="button" onClick={onRefresh}>
          Refresh
        </button>
        <button className="secondary-button compact-button" type="button" onClick={onSearch} disabled={!memoryQuery.trim()}>
          Search
        </button>
      </div>
      <select aria-label="Memory scope filter" value={memoryScope} onChange={(event) => onScopeChange(event.target.value as MemoryScope | "")}>
        <option value="">All scopes</option>
        {MEMORY_SCOPES.map((nextScope) => (
          <option key={nextScope} value={nextScope}>{nextScope}</option>
        ))}
      </select>
      <select aria-label="Memory type filter" value={memoryType} onChange={(event) => onTypeChange(event.target.value as MemoryType | "")}>
        <option value="">All types</option>
        {MEMORY_TYPES.map((nextType) => (
          <option key={nextType} value={nextType}>{nextType}</option>
        ))}
      </select>
      <select aria-label="Memory status filter" value={memoryStatus} onChange={(event) => onStatusChange(event.target.value as MemoryStatus | "")}>
        <option value="">All statuses</option>
        {MEMORY_STATUSES.map((nextStatus) => (
          <option key={nextStatus} value={nextStatus}>{nextStatus}</option>
        ))}
      </select>
      <input aria-label="Memory tag filter" value={memoryTag} onChange={(event) => onTagChange(event.target.value)} placeholder="Tag filter" />

      <div className="memory-form">
        <textarea aria-label="Memory text" value={text} onChange={(event) => setText(event.target.value)} placeholder="Add a memory" />
        <select aria-label="Memory scope" value={scope} onChange={(event) => setScope(event.target.value as MemoryScope)}>
          {MEMORY_SCOPES.map((nextScope) => (
            <option key={nextScope} value={nextScope}>{nextScope}</option>
          ))}
        </select>
        <select aria-label="Memory type" value={type} onChange={(event) => setType(event.target.value as MemoryType)}>
          {MEMORY_TYPES.map((nextType) => (
            <option key={nextType} value={nextType}>{nextType}</option>
          ))}
        </select>
        <input aria-label="Memory confidence" type="number" min="0" max="1" step="0.05" value={confidence} onChange={(event) => setConfidence(Number(event.target.value))} />
        <input aria-label="Memory tags" value={tags} onChange={(event) => setTags(event.target.value)} placeholder="tags, comma separated" />
        <input aria-label="Memory source summary" value={sourceSummary} onChange={(event) => setSourceSummary(event.target.value)} placeholder="Source summary" />
        <div className="panel-actions">
          <button
            className="secondary-button compact-button"
            type="button"
            onClick={() => {
              if (editingId) {
                onEdit(editingId, input());
              } else {
                onAdd(input());
              }
              resetForm();
            }}
            disabled={!formValid}
          >
            {editingId ? "Save memory" : "Add memory"}
          </button>
          {editingId ? (
            <button className="secondary-button compact-button" type="button" onClick={resetForm}>
              Cancel
            </button>
          ) : null}
        </div>
      </div>

      {error ? <p className="hitl-error" role="alert">{error}</p> : null}
      <div className="side-list">
        {memories.length === 0 ? <p className="muted-text">No memories match the current filters</p> : null}
        {memories.slice(0, 6).map((memory) => (
          <div key={memory.id}>
            <strong>{memory.text}</strong>
            <span>{memory.scope} · {memory.type} · {memory.status} · confidence {memory.confidence}</span>
            <span>{memory.tags.length ? memory.tags.join(", ") : "untagged"}</span>
            <div className="panel-actions">
              <button className="secondary-button compact-button" type="button" onClick={() => loadForEdit(memory)}>
                Edit
              </button>
              <button className="secondary-button compact-button" type="button" onClick={() => onAction(memory.id, "archive")}>
                Archive
              </button>
              <button className="secondary-button compact-button" type="button" onClick={() => onAction(memory.id, "stale")}>
                Stale
              </button>
              <button className="secondary-button compact-button" type="button" onClick={() => onAction(memory.id, "refresh", { evidence: "Reviewed in workbench" })}>
                Refresh
              </button>
            </div>
            <div className="panel-actions">
              <button className="secondary-button compact-button" type="button" onClick={() => onAction(memory.id, "promote", { target_scope: "user", approved: true })}>
                Promote
              </button>
              <button className="secondary-button compact-button" type="button" onClick={() => onDelete(memory.id)}>
                Delete
              </button>
            </div>
          </div>
        ))}
      </div>

      {searchResult ? (
        <div className="search-results" aria-label="Memory search results">
          {searchResult.results.length === 0 ? <p className="muted-text">No matching memory results</p> : null}
          {searchResult.results.slice(0, 4).map((result) => (
            <article key={result.memory.id}>
              <strong>{result.memory.text}</strong>
              <p>{formatScoreReasons(result.score_reasons)}</p>
              <span>score {result.score} · duplicate omissions {result.duplicate_ids.length}</span>
            </article>
          ))}
        </div>
      ) : null}

      <button className="secondary-button compact-button" type="button" onClick={onExtract}>
        Extract candidates
      </button>
      <div className="side-list">
        {candidates.map((candidate) => (
          <div key={candidate.id}>
            <strong>{candidate.text}</strong>
            <span>{candidate.suggested_scope} · {candidate.suggested_type} · {candidate.status} · {candidate.risk}</span>
            <span>{candidate.guard.allowed ? "guard ok" : `blocked: ${candidate.guard.reasons.join(", ")}`}</span>
            <div className="panel-actions">
              <button className="secondary-button compact-button" type="button" onClick={() => onCandidate(candidate.id, "approve")} disabled={!candidate.guard.allowed}>
                Approve
              </button>
              <button className="secondary-button compact-button" type="button" onClick={() => onCandidate(candidate.id, "reject")}>
                Reject
              </button>
              <button className="secondary-button compact-button" type="button" onClick={() => onCandidate(candidate.id, "defer")}>
                Defer
              </button>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

function ProjectPanel({
  root,
  query,
  status,
  search,
  onRootChange,
  onQueryChange,
  onRefresh,
  onSearch,
}: {
  root: string;
  query: string;
  status: ProjectIndexStatus | null;
  search: ProjectSearchResponse | null;
  onRootChange: (value: string) => void;
  onQueryChange: (value: string) => void;
  onRefresh: () => void;
  onSearch: () => void;
}) {
  return (
    <section className="side-panel" aria-label="Project knowledge">
      <h3>Project</h3>
      <input aria-label="Project root" value={root} onChange={(event) => onRootChange(event.target.value)} placeholder="Project root" />
      <div className="panel-actions">
        <button className="secondary-button compact-button" type="button" onClick={onRefresh}>
          Refresh
        </button>
      </div>
      <dl className="compact-dl">
        <dt>Status</dt>
        <dd>{status?.status ?? "unknown"}</dd>
        <dt>Files</dt>
        <dd>{status ? `${status.file_count} files · ${status.chunk_count} chunks` : "Not loaded"}</dd>
      </dl>
      <input aria-label="Project search" value={query} onChange={(event) => onQueryChange(event.target.value)} placeholder="Search project context" />
      <button className="secondary-button compact-button" type="button" onClick={onSearch} disabled={!query.trim()}>
        Search
      </button>
      <div className="search-results">
        {search?.results.slice(0, 4).map((result) => (
          <article key={`${result.path}-${result.start_line}-${result.chunk_id ?? "live"}`}>
            <strong>{result.path}{result.start_line ? `:${result.start_line}` : ""}</strong>
            <p>{result.snippet}</p>
            <span>{result.stale ? "stale" : "fresh"} · score {result.score}</span>
          </article>
        ))}
      </div>
    </section>
  );
}

function SafetyPanel({
  doctor,
  audit,
  traceExport,
  replacementInspection,
  error,
  replacementId,
  onReplacementIdChange,
  onDoctor,
  onAudit,
  onRunTrace,
  onConversationTrace,
  onProjectTrace,
  onMemoryTrace,
  onInspectReplacement,
  runDisabled,
  conversationDisabled,
}: {
  doctor: DoctorDiagnostics | null;
  audit: AuditRecord[];
  traceExport: TraceExport | null;
  replacementInspection: ReplacementInspection | null;
  error: string | null;
  replacementId: string;
  onReplacementIdChange: (value: string) => void;
  onDoctor: () => void;
  onAudit: () => void;
  onRunTrace: () => void;
  onConversationTrace: () => void;
  onProjectTrace: () => void;
  onMemoryTrace: () => void;
  onInspectReplacement: () => void;
  runDisabled: boolean;
  conversationDisabled: boolean;
}) {
  return (
    <section className="side-panel" aria-label="Safety and diagnostics">
      <h3>Safety</h3>
      {error ? <p className="hitl-error" role="alert">{redactForDisplay(error)}</p> : null}
      <div className="panel-actions">
        <button className="secondary-button compact-button" type="button" onClick={onDoctor}>
          Doctor
        </button>
        <button className="secondary-button compact-button" type="button" onClick={onAudit}>
          Audit
        </button>
      </div>
      <div className="panel-actions">
        <button className="secondary-button compact-button" type="button" onClick={onRunTrace} disabled={runDisabled}>
          Run trace
        </button>
        <button className="secondary-button compact-button" type="button" onClick={onConversationTrace} disabled={conversationDisabled}>
          Conversation trace
        </button>
      </div>
      <div className="panel-actions">
        <button className="secondary-button compact-button" type="button" onClick={onProjectTrace}>
          Project trace
        </button>
        <button className="secondary-button compact-button" type="button" onClick={onMemoryTrace}>
          Memory trace
        </button>
      </div>
      <input aria-label="Replacement ID" value={replacementId} onChange={(event) => onReplacementIdChange(event.target.value)} placeholder="Replacement ID" />
      <button className="secondary-button compact-button" type="button" onClick={onInspectReplacement} disabled={!replacementId.trim()}>
        Inspect replacement
      </button>
      {doctor ? (
        <div className="side-list" aria-label="Doctor diagnostics">
          <div>
            <strong>Doctor {doctor.status}</strong>
            <span>{doctor.checks.length} checks · backend {String(doctor.versions?.backend ?? "unknown")}</span>
          </div>
          {doctor.checks.slice(0, 6).map((check) => (
            <div key={`${check.component}-${check.message}`}>
              <strong>{check.component}</strong>
              <span>{check.status} · {check.severity}</span>
              <span>{check.message}</span>
              {check.remediation ? <span>{check.remediation}</span> : null}
            </div>
          ))}
        </div>
      ) : null}
      {audit.length ? (
        <div className="side-list" aria-label="Audit records">
          {audit.slice(0, 8).map((record) => (
            <div key={record.id}>
              <strong>{record.action}</strong>
              <span>{record.status} · {record.decision ?? "n/a"}</span>
              <span>{record.summary ?? record.id}</span>
            </div>
          ))}
        </div>
      ) : null}
      {traceExport ? <pre className="detail-box">{safeJson(traceExport)}</pre> : null}
      {replacementInspection ? <pre className="detail-box">{safeJson(replacementInspection)}</pre> : null}
    </section>
  );
}

function ContextInspector({ trace }: { trace: RunContextTrace | null }) {
  return (
    <section className="side-panel" aria-label="Run context">
      <h3>Context</h3>
      {trace ? (
        <>
          <dl className="compact-dl">
            <dt>Included</dt>
            <dd>{trace.included.length}</dd>
            <dt>Omitted</dt>
            <dd>{trace.omitted.length}</dd>
          </dl>
          <div className="side-list">
            {trace.included.slice(0, 5).map((item) => (
              <div key={item.id}>
                <strong>{item.kind}</strong>
                <span>{item.trust} · {item.budget_cost}</span>
                {item.kind === "conversation_history" || item.kind === "tool_summary" ? (
                  <span>{String(item.metadata.role ?? item.metadata.message_id ?? "transcript")} · {String(item.metadata.turn_id ?? "turn")}</span>
                ) : null}
                {item.kind === "conversation_summary" || item.kind === "compaction_summary" ? (
                  <span>
                    {String(item.metadata.summary_id ?? "summary")} · {String(item.metadata.status ?? "active")} · tail {String(item.metadata.tail_start_message_id ?? "none")}
                  </span>
                ) : null}
                {item.metadata.source === "tool_output_replacement" ? (
                  <span>
                    {String(item.metadata.replacement_id ?? "replacement")} · {String(item.metadata.reason ?? "replaced")} · omitted {String(item.metadata.omitted_char_count ?? 0)}
                  </span>
                ) : null}
                {item.citations.slice(0, 2).map((citation) => (
                  <span key={`${item.id}-${citation.citation_id ?? citation.path}`}>
                    {citation.citation_type === "memory" || item.kind === "memory"
                      ? `memory ${citation.memory_id ?? citation.citation_id ?? citation.path}`
                      : `${citation.path}${citation.start_line ? `:${citation.start_line}` : ""}`}
                  </span>
                ))}
              </div>
            ))}
          </div>
          {trace.omitted.length ? (
            <div className="side-list" aria-label="Context omissions">
              {trace.omitted.slice(0, 4).map((item, index) => (
                <div key={`${String(item.summary_id ?? item.replacement_id ?? item.message_id ?? index)}-${index}`}>
                  <strong>{String(item.kind ?? item.reason ?? "omitted")}</strong>
                  <span>{String(item.summary_id ?? item.replacement_id ?? item.message_id ?? "context")} · {String(item.reason ?? "omitted")}</span>
                </div>
              ))}
            </div>
          ) : null}
        </>
      ) : (
        <p className="muted-text">No run context yet</p>
      )}
    </section>
  );
}

function StreamNotice({ message }: { message: string }) {
  return (
    <article className="timeline-row status-row reconnect-row" role="status">
      <span className="event-type">Reconnecting</span>
      <p>{message}</p>
    </article>
  );
}

function ChatTurn({
  turn,
  disabled,
}: {
  turn: ChatTurnViewModel;
  disabled: boolean;
}) {
  const progressMessage = getTurnProgressMessage(turn);
  const hasAssistantProcess = turn.items.length > 0 || turn.assistant;
  return (
    <article className="chat-turn" data-testid="chat-turn">
      {turn.user ? <ChatMessageBubble message={turn.user} disabled={disabled} /> : null}
      {progressMessage ? <InlineRunProgress message={progressMessage} /> : null}
      {hasAssistantProcess ? (
        <section className="assistant-turn" aria-label="Assistant turn">
          {turn.items.map((item) => (
            <ChatTurnProcessItem key={item.key} item={item} />
          ))}
          {turn.assistant ? <ChatMessageBubble message={turn.assistant} disabled={disabled} /> : null}
        </section>
      ) : null}
    </article>
  );
}

function InlineRunProgress({ message }: { message: string }) {
  return (
    <div className="inline-run-progress" role="status" aria-label="Current run step">
      <span className="inline-run-progress-icon" aria-hidden="true">
        <span />
        <span />
        <span />
      </span>
      <strong>Kira</strong>
      <span>{message}</span>
    </div>
  );
}

function getTurnProgressMessage(turn: ChatTurnViewModel): string | null {
  if (turn.assistant || turn.runState === "idle" || turn.runState === "completed" || turn.runState === "error" || turn.runState === "cancelled") {
    return null;
  }
  if (turn.runState === "waiting") {
    return "等待你的确认或补充信息...";
  }

  const latestItem = turn.items[turn.items.length - 1];
  if (latestItem?.kind === "tool") {
    const toolName = formatToolName(latestItem.tool.start ?? latestItem.tool.result);
    return latestItem.tool.result ? "正在整理工具结果..." : `正在调用工具${toolName ? ` ${toolName}` : ""}...`;
  }
  if (latestItem?.kind === "reasoning") {
    return "正在梳理思路和约束...";
  }
  if (latestItem?.kind === "status") {
    if (latestItem.status.kind === "retry") {
      return "正在重试上一步...";
    }
    if (latestItem.status.kind === "resume") {
      return "已收到回复，继续处理...";
    }
    if (latestItem.status.kind === "checkpoint") {
      return "正在保存进度...";
    }
  }

  return "正在理解你的问题...";
}

function formatToolName(event?: KiraEvent): string {
  if (!event) {
    return "";
  }
  const metadata = isPlainObject(event.data.metadata) ? event.data.metadata : {};
  return formatEventValue(event.data.name ?? event.data.tool_name ?? metadata.name ?? metadata.tool_name, "");
}

function isPlainObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function ChatTurnProcessItem({ item }: { item: ChatTurnItem }) {
  if (item.kind === "reasoning") {
    return <ThinkingBlock events={item.reasoning.events} />;
  }
  if (item.kind === "tool") {
    return <ToolActivityBlock start={item.tool.start} result={item.tool.result} />;
  }
  return <ProcessStatus status={item.status} />;
}

function ChatMessageBubble({
  message,
  disabled: _disabled,
}: {
  message: ChatMessageViewModel;
  disabled: boolean;
}) {
  const source = message.sourceMessage;
  const branchLabel = source?.branch_status === "inactive" ? "Inactive" : source?.branch_status === "inherited" ? "Inherited" : null;
  const label = `${message.role === "user" ? "You" : "Kira"}${branchLabel ? ` · ${branchLabel}` : ""}`;
  const className = source?.branch_status === "inactive" ? "inactive-row" : "";
  const testId = source ? (message.role === "user" ? "transcript-user-row" : "transcript-answer-row") : message.role === "user" ? "user-row" : "answer-row";

  // Stage 11: Fork / Rollback controls intentionally omitted from default chat bubbles.
  // forkConversation / rollbackConversation API client functions remain available for future stages.
  return (
    <MessageBubble role={message.role} label={label} text={message.text} timestamp={message.timestamp} className={className} testId={testId} />
  );
}

function ProcessStatus({ status }: { status: RunStatusViewModel }) {
  const cancelled = status.kind === "error" && status.runState === "cancelled";
  return (
    <article
      className={`timeline-row status-row ${status.kind}-row ${cancelled ? "cancelled-row" : ""}`}
      data-testid={`${status.kind}-row`}
      role={status.kind === "error" ? "alert" : undefined}
    >
      <span className="event-type">{status.label}</span>
      <p>{status.message}</p>
      {status.timestamp ? <time>{status.timestamp}</time> : null}
    </article>
  );
}

function MessageBubble({
  role,
  label,
  text,
  timestamp,
  className = "",
  testId,
  children,
}: {
  role: "assistant" | "user";
  label: string;
  text: string;
  timestamp?: string;
  className?: string;
  testId?: string;
  children?: ReactNode;
}) {
  const assistant = role === "assistant";
  const visibleText = assistant ? trimLeadingBlankLines(text) : text;
  return (
    <article className={`message-row ${role}-message ${className}`} data-testid={testId}>
      <div className="message-bubble">
        {assistant ? (
          <div className="assistant-identity-line">
            <span className="agent-avatar message-avatar" aria-hidden="true">
              K
            </span>
            <span>{label}</span>
          </div>
        ) : (
          <div className="message-caption">
            <span>{label}</span>
            {timestamp ? <time>{timestamp}</time> : null}
          </div>
        )}
        {assistant ? <MarkdownContent text={visibleText} /> : <p>{visibleText}</p>}
        {assistant && timestamp ? (
          <div className="assistant-actions" aria-label="Assistant actions">
            <time>{timestamp}</time>
          </div>
        ) : null}
        {children}
      </div>
    </article>
  );
}

function trimLeadingBlankLines(text: string): string {
  return text.replace(/^(?:[ \t]*\r?\n)+/, "");
}

function MarkdownContent({ text }: { text: string }) {
  const blocks = parseMarkdownBlocks(text);
  return (
    <div className="markdown-content">
      {blocks.map((block, index) => {
        if (block.kind === "code") {
          return (
            <div key={`code-${index}`} className="markdown-code-card">
              <div className="markdown-code-header">
                <span>{block.language || "plaintext"}</span>
                <CopyButton value={block.text} ariaLabel={`Copy ${block.language || "plaintext"} code`} />
              </div>
              <pre className="markdown-code-block">
                <code>{block.text}</code>
              </pre>
            </div>
          );
        }
        if (block.kind === "heading") {
          const Heading = block.level === 1 ? "h3" : block.level === 2 ? "h4" : "h5";
          return <Heading key={`heading-${index}`}>{renderInlineMarkdown(block.text)}</Heading>;
        }
        if (block.kind === "list") {
          const List = block.ordered ? "ol" : "ul";
          return (
            <List key={`list-${index}`}>
              {block.items.map((item, itemIndex) => (
                <li key={`${item}-${itemIndex}`}>{renderInlineMarkdown(item)}</li>
              ))}
            </List>
          );
        }
        if (block.kind === "table") {
          return (
            <div key={`table-${index}`} className="markdown-table-wrap">
              <table>
                <thead>
                  <tr>
                    {block.headers.map((header, headerIndex) => (
                      <th key={`${header}-${headerIndex}`}>{renderInlineMarkdown(header)}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {block.rows.map((row, rowIndex) => (
                    <tr key={rowIndex}>
                      {block.headers.map((_, cellIndex) => (
                        <td key={cellIndex}>{renderInlineMarkdown(row[cellIndex] ?? "")}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          );
        }
        return <p key={`paragraph-${index}`}>{renderInlineMarkdown(block.text)}</p>;
      })}
    </div>
  );
}

function CopyButton({
  value,
  ariaLabel,
  className = "",
}: {
  value: string;
  ariaLabel: string;
  className?: string;
}) {
  const [status, setStatus] = useState<"idle" | "copied" | "failed">("idle");

  async function handleCopy() {
    const ok = await copyText(value);
    setStatus(ok ? "copied" : "failed");
    window.setTimeout(() => setStatus("idle"), 1600);
  }

  const label = status === "copied" ? "Copied" : status === "failed" ? "Copy failed" : "Copy";
  return (
    <button
      className={`copy-feedback-button ${status === "copied" ? "is-copied" : ""} ${status === "failed" ? "is-failed" : ""} ${className}`}
      type="button"
      onClick={() => void handleCopy()}
      aria-label={ariaLabel}
      aria-live="polite"
    >
      {label}
    </button>
  );
}

function parseMarkdownBlocks(text: string): MarkdownBlock[] {
  const lines = text.replace(/\r\n/g, "\n").split("\n");
  const blocks: MarkdownBlock[] = [];
  let index = 0;

  while (index < lines.length) {
    const line = lines[index];
    if (line.trim().length === 0) {
      index += 1;
      continue;
    }

    const fence = line.match(/^```(\w[\w-]*)?\s*$/);
    if (fence) {
      const language = fence[1] ?? "";
      const codeLines: string[] = [];
      index += 1;
      while (index < lines.length && !/^```\s*$/.test(lines[index])) {
        codeLines.push(lines[index]);
        index += 1;
      }
      blocks.push({ kind: "code", language, text: codeLines.join("\n") });
      index += index < lines.length ? 1 : 0;
      continue;
    }

    const heading = line.match(/^(#{1,3})\s+(.+)$/);
    if (heading) {
      blocks.push({ kind: "heading", level: heading[1].length as 1 | 2 | 3, text: heading[2].trim() });
      index += 1;
      continue;
    }

    if (isMarkdownTableStart(lines, index)) {
      const headers = parseMarkdownTableRow(lines[index]);
      const rows: string[][] = [];
      index += 2;
      while (index < lines.length && isMarkdownTableRow(lines[index])) {
        rows.push(parseMarkdownTableRow(lines[index]));
        index += 1;
      }
      blocks.push({ kind: "table", headers, rows });
      continue;
    }

    const unordered = line.match(/^\s*[-*]\s+(.+)$/);
    const ordered = line.match(/^\s*\d+\.\s+(.+)$/);
    if (unordered || ordered) {
      const orderedList = Boolean(ordered);
      const items: string[] = [];
      while (index < lines.length) {
        const item = orderedList ? lines[index].match(/^\s*\d+\.\s+(.+)$/) : lines[index].match(/^\s*[-*]\s+(.+)$/);
        if (!item) {
          break;
        }
        items.push(item[1].trim());
        index += 1;
      }
      blocks.push({ kind: "list", ordered: orderedList, items });
      continue;
    }

    const paragraphLines: string[] = [];
    while (index < lines.length && lines[index].trim().length > 0 && !isMarkdownBoundary(lines[index])) {
      paragraphLines.push(lines[index]);
      index += 1;
    }
    if (paragraphLines.length > 0) {
      blocks.push({ kind: "paragraph", text: paragraphLines.join("\n") });
    }
  }

  return blocks.length > 0 ? blocks : [{ kind: "paragraph", text }];
}

function isMarkdownBoundary(line: string): boolean {
  return /^```/.test(line) || /^(#{1,3})\s+/.test(line) || /^\s*[-*]\s+/.test(line) || /^\s*\d+\.\s+/.test(line) || isMarkdownTableRow(line);
}

function isMarkdownTableStart(lines: string[], index: number): boolean {
  return isMarkdownTableRow(lines[index]) && Boolean(lines[index + 1]?.match(/^\s*\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)+\|?\s*$/));
}

function isMarkdownTableRow(line: string): boolean {
  return /^\s*\|.+\|\s*$/.test(line);
}

function parseMarkdownTableRow(line: string): string[] {
  return line
    .trim()
    .replace(/^\|/, "")
    .replace(/\|$/, "")
    .split("|")
    .map((cell) => cell.trim());
}

function renderInlineMarkdown(text: string): ReactNode[] {
  const segments = text.split(/(`[^`]+`|\*\*[^*]+\*\*)/g);
  return segments.map((segment, index) => {
    if (segment.startsWith("`") && segment.endsWith("`")) {
      return <code key={index}>{segment.slice(1, -1)}</code>;
    }
    if (segment.startsWith("**") && segment.endsWith("**")) {
      return <strong key={index}>{segment.slice(2, -2)}</strong>;
    }
    return segment.split("\n").flatMap((part, partIndex) => (partIndex === 0 ? [part] : [<br key={`${index}-${partIndex}`} />, part]));
  });
}

function readPinnedConversationIds(): string[] {
  try {
    const raw = window.localStorage.getItem(PINNED_CONVERSATIONS_KEY);
    const parsed = raw ? JSON.parse(raw) : [];
    return Array.isArray(parsed) ? parsed.filter((value): value is string => typeof value === "string") : [];
  } catch {
    return [];
  }
}

function writePinnedConversationIds(conversationIds: string[]) {
  try {
    window.localStorage.setItem(PINNED_CONVERSATIONS_KEY, JSON.stringify(conversationIds));
  } catch {
    // Pinning is a local preference; ignore storage failures.
  }
}

function BranchActions({
  message,
  disabled,
  onFork,
  onRollback,
}: {
  message: TranscriptMessage;
  disabled: boolean;
  onFork: (messageId: string) => void;
  onRollback: (messageId: string) => void;
}) {
  if (message.branch_status === "inactive") {
    return null;
  }
  return (
    <div className="message-actions">
      <button className="secondary-button compact-button" type="button" onClick={() => onFork(message.id)} disabled={disabled}>
        Fork
      </button>
      <button className="secondary-button compact-button" type="button" onClick={() => onRollback(message.id)} disabled={disabled}>
        Rollback
      </button>
    </div>
  );
}

function HitlPanel({
  interrupt,
  error,
  onSubmit,
}: {
  interrupt: InterruptPayload;
  error: string | null;
  onSubmit: (request: ResumeRequest) => void;
}) {
  const [value, setValue] = useState(formatEventValue(interrupt.data.suggested_value, ""));
  const [reason, setReason] = useState("");
  const requiresText = interrupt.kind === "edit" || interrupt.kind === "question";
  const title = interrupt.kind === "python_approval" ? "Python approval" : interrupt.title;

  function submit(decision: ResumeRequest["decision"]) {
    onSubmit({
      interrupt_id: interrupt.interrupt_id,
      decision,
      value: requiresText ? value : undefined,
      reason: decision === "reject" ? reason || "Rejected by user" : undefined,
      data: requiresText ? { answer: value } : {},
    });
  }

  return (
    <section className="hitl-panel" aria-label="Human input required">
      <div>
        <span className="event-type">{title}</span>
        <p>{interrupt.body}</p>
      </div>
      {requiresText ? (
        <input aria-label="HITL response" value={value} onChange={(event) => setValue(event.target.value)} />
      ) : null}
      {interrupt.kind === "approval" || interrupt.kind === "python_approval" ? (
        <input aria-label="Rejection reason" value={reason} onChange={(event) => setReason(event.target.value)} placeholder="Optional rejection reason" />
      ) : null}
      {error ? <p className="hitl-error" role="alert">{error}</p> : null}
      <div className="hitl-actions">
        {interrupt.allowed_responses.map((response) => (
          <button
            key={response.id}
            type="button"
            className={response.kind === "reject" ? "secondary-button" : undefined}
            onClick={() => submit(response.kind)}
            disabled={requiresText && value.trim().length === 0}
          >
            {response.label}
          </button>
        ))}
      </div>
    </section>
  );
}

function EmptyTimeline() {
  return (
    <div className="empty-timeline">
      <p>Ask Kira to work with the local project.</p>
    </div>
  );
}

function PromptComposer({
  prompt,
  setPrompt,
  running,
  inputRef,
  skills,
  selectedSkillId,
  onSkillSelect,
  onSkillClear,
  onSubmit,
  onStop,
}: {
  prompt: string;
  setPrompt: (prompt: string) => void;
  running: boolean;
  inputRef: RefObject<HTMLInputElement>;
  skills: SkillMetadata[];
  selectedSkillId: string;
  onSkillSelect: (skillId: string) => void;
  onSkillClear: () => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
  onStop: () => void;
}) {
  const activeSkill = skills.find((skill) => skill.skill_id === selectedSkillId) ?? null;
  const slashQuery = slashSkillQuery(prompt);
  const visibleSkills = filterInvocableSkills(skills, slashQuery).slice(0, 8);
  const showSkillMenu = slashQuery !== null && visibleSkills.length > 0 && !running;

  return (
    <form className="prompt-form" onSubmit={onSubmit}>
      {activeSkill ? (
        <div className="composer-skill-chip" aria-label="Active skill">
          <span>Using {activeSkill.name}</span>
          <button type="button" onClick={onSkillClear} aria-label={`Clear skill ${activeSkill.name}`}>
            Clear
          </button>
        </div>
      ) : null}
      {showSkillMenu ? (
        <div className="skill-command-menu" role="listbox" aria-label="Available skills">
          <div className="skill-command-menu-title">可用 Skills</div>
          {visibleSkills.map((skill) => (
            <button
              key={skill.skill_id}
              type="button"
              role="option"
              aria-selected={skill.skill_id === selectedSkillId}
              onClick={() => onSkillSelect(skill.skill_id)}
            >
              <strong>{skill.name}</strong>
              <span>{skill.description || skill.when_to_use || skill.skill_id}</span>
            </button>
          ))}
        </div>
      ) : null}
      <input
        ref={inputRef}
        aria-label="Prompt"
        value={prompt}
        placeholder="Message Kira, or type / to use a skill"
        onChange={(event) => setPrompt(event.target.value)}
      />
      {running ? (
        <button className="secondary-button" type="button" onClick={onStop}>
          Stop
        </button>
      ) : null}
      <button type="submit" disabled={prompt.trim().length === 0 || running}>
        Run
      </button>
    </form>
  );
}

function slashSkillQuery(prompt: string): string | null {
  const match = prompt.match(/^\s*\/([^\s]*)?/);
  if (!match) {
    return null;
  }
  return (match[1] || "").toLowerCase();
}

function stripSlashSkillQuery(prompt: string): string {
  return prompt.replace(/^\s*\/[^\s]*\s*/, "");
}

function filterInvocableSkills(skills: SkillMetadata[], query: string | null): SkillMetadata[] {
  const activeSkills = skills.filter((skill) => skill.valid !== false && skill.active !== false && skill.invocation?.user_invocable !== false);
  if (query === null || query.length === 0) {
    return activeSkills;
  }
  return activeSkills.filter((skill) => {
    const haystack = `${skill.skill_id} ${skill.name} ${skill.description ?? ""} ${skill.when_to_use ?? ""}`.toLowerCase();
    return haystack.includes(query);
  });
}

function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState(() => {
    if (typeof window === "undefined" || typeof window.matchMedia !== "function") {
      return false;
    }
    return window.matchMedia(query).matches;
  });

  useEffect(() => {
    if (typeof window === "undefined" || typeof window.matchMedia !== "function") {
      return;
    }

    const mediaQuery = window.matchMedia(query);
    const updateMatches = () => setMatches(mediaQuery.matches);
    updateMatches();
    if (typeof mediaQuery.addEventListener === "function") {
      mediaQuery.addEventListener("change", updateMatches);
      return () => mediaQuery.removeEventListener("change", updateMatches);
    }
    mediaQuery.addListener(updateMatches);
    return () => mediaQuery.removeListener(updateMatches);
  }, [query]);

  return matches;
}

function getWorkbenchStatus({
  running,
  pendingInterrupt,
  events,
  streamNotice,
}: {
  running: boolean;
  pendingInterrupt: InterruptPayload | null;
  events: KiraEvent[];
  streamNotice: string | null;
}): string {
  if (pendingInterrupt) {
    return "Waiting for input";
  }
  if (running) {
    return "Running";
  }
  if (streamNotice) {
    return "Reconnecting";
  }
  const lastEvent = events.length > 0 ? events[events.length - 1] : null;
  if (lastEvent?.type === "error") {
    return isCancelledEvent(lastEvent) ? "Cancelled" : "Error";
  }
  if (lastEvent?.type === "done") {
    return "Completed";
  }
  return "Idle";
}

function isCancelledEvent(event: KiraEvent): boolean {
  return event.type === "error" && (event.data.failure_class === "cancelled" || event.data.status === "cancelled");
}

async function copyText(value: string): Promise<boolean> {
  return copyTextToClipboard(value);
}

function formatEventValue(value: unknown, fallback: string): string {
  if (typeof value === "string" && value.length > 0) {
    return value;
  }

  return fallback;
}

function formatProvider(provider: ProviderMetadata | null): string {
  if (!provider) {
    return "Not selected";
  }
  if (provider.mode === "fixture") {
    const reason = provider.fallback_reason ? ` (${provider.fallback_reason})` : "";
    return `Fixture${reason}`;
  }
  const label = provider.preset || provider.name || provider.provider || "OpenAI-compatible";
  return provider.model ? `${label} · ${provider.model}` : label;
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

function formatScoreReasons(reasons: MemorySearchResponse["results"][number]["score_reasons"]): string {
  if (reasons.length === 0) {
    return "No score factors";
  }
  return reasons.map((reason) => `${reason.factor} +${reason.score}${reason.matched.length ? ` (${reason.matched.join(", ")})` : ""}`).join("; ");
}

function toInterrupt(data: Record<string, unknown>): InterruptPayload {
  return {
    interrupt_id: formatEventValue(data.interrupt_id, "interrupt"),
    kind: isInterruptKind(data.kind) ? data.kind : "approval",
    title: formatEventValue(data.title, "Human input required"),
    body: formatEventValue(data.body, "Review the pending workflow step."),
    data: isRecord(data.data) ? data.data : {},
    allowed_responses: Array.isArray(data.allowed_responses)
      ? data.allowed_responses.filter(isAllowedResponse)
      : [{ id: "approve", label: "Approve", kind: "approve" }, { id: "reject", label: "Reject", kind: "reject" }],
    metadata: isRecord(data.metadata) ? data.metadata : {},
  };
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isInterruptKind(value: unknown): value is InterruptPayload["kind"] {
  return value === "approval" || value === "edit" || value === "question" || value === "python_approval";
}

function isAllowedResponse(value: unknown): value is InterruptPayload["allowed_responses"][number] {
  if (!isRecord(value)) {
    return false;
  }
  return typeof value.id === "string" && typeof value.label === "string" && (value.kind === "approve" || value.kind === "reject" || value.kind === "submit");
}
