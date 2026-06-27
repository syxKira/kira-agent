import type {
  CompactConversationRequest,
  CompactConversationResponse,
  ActiveHeadTransition,
  AuditRecord,
  BranchOperationResponse,
  CompactionSummary,
  Conversation,
  ConversationBranchRecord,
  DoctorDiagnostics,
  KiraEvent,
  MemoryCandidate,
  MemoryAction,
  MemoryRecord,
  MemorySearchResponse,
  MemoryScope,
  MemoryStatus,
  MemoryType,
  PermissionDecision,
  ProjectIndexStatus,
  ProjectSearchResponse,
  ReplacementInspection,
  ResumeRequest,
  ResumeResult,
  RunCreateRequest,
  RunCreateResponse,
  RunContextTrace,
  RunReplayExport,
  RunStateProjection,
  TraceExport,
  SkillMetadata,
  SkillInstallResponse,
  TranscriptMessage,
  ToolOutputReplacement,
} from "./types";

const API_BASE = normalizeApiBase(import.meta.env.VITE_KIRA_API_BASE);
const API_PREFIX = "/api";

export function toApiUrl(pathOrUrl: string, base = API_BASE): string {
  if (pathOrUrl.startsWith("http://") || pathOrUrl.startsWith("https://")) {
    return pathOrUrl;
  }

  const path = pathOrUrl.startsWith("/") ? pathOrUrl : `/${pathOrUrl}`;
  const normalizedBase = normalizeApiBase(base);
  if (!normalizedBase) {
    return path;
  }

  if (normalizedBase.endsWith(API_PREFIX) && (path === API_PREFIX || path.startsWith(`${API_PREFIX}/`) || path.startsWith(`${API_PREFIX}?`))) {
    return `${normalizedBase}${path.slice(API_PREFIX.length)}`;
  }

  return `${normalizedBase}${path}`;
}

function normalizeApiBase(value?: string): string {
  return value?.replace(/\/+$/, "") ?? "";
}

export async function createRun(request: RunCreateRequest): Promise<RunCreateResponse> {
  const response = await fetch(toApiUrl("/api/runs"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw new Error(await errorMessage(response, "Failed to create run"));
  }

  return response.json() as Promise<RunCreateResponse>;
}

export async function getDoctor(): Promise<DoctorDiagnostics> {
  const response = await fetch(toApiUrl("/api/doctor"));
  if (!response.ok) {
    throw new Error(`Failed to get doctor diagnostics: ${response.status}`);
  }
  return response.json() as Promise<DoctorDiagnostics>;
}

export async function listAudit(params: Record<string, string | number | undefined> = {}): Promise<{ records: AuditRecord[]; limit: number; truncated: boolean; redacted: boolean }> {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && String(value).length > 0) {
      search.set(key, String(value));
    }
  });
  const query = search.toString();
  const response = await fetch(toApiUrl(`/api/audit${query ? `?${query}` : ""}`));
  if (!response.ok) {
    throw new Error(`Failed to list audit records: ${response.status}`);
  }
  return response.json() as Promise<{ records: AuditRecord[]; limit: number; truncated: boolean; redacted: boolean }>;
}

export async function previewPermission(action: string, subject: Record<string, unknown> = {}): Promise<PermissionDecision> {
  const response = await fetch(toApiUrl("/api/permissions/preview"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action, subject }),
  });
  if (!response.ok) {
    throw new Error(await errorMessage(response, "Failed to preview permission"));
  }
  return response.json() as Promise<PermissionDecision>;
}

export function streamRunEvents(
  eventsUrl: string,
  handlers: {
    onEvent: (event: KiraEvent) => void;
    onError: () => void;
  },
) {
  const source = new EventSource(toApiUrl(eventsUrl));

  const eventTypes: KiraEvent["type"][] = [
    "text_delta",
    "thinking_delta",
    "tool_start",
    "tool_result",
    "retry",
    "side_effect_reused",
    "checkpoint",
    "interrupt",
    "resume",
    "done",
    "error",
  ];

  for (const type of eventTypes) {
    source.addEventListener(type, (message) => {
      handlers.onEvent(JSON.parse(message.data) as KiraEvent);
    });
  }

  source.onerror = handlers.onError;

  return () => source.close();
}

export async function resumeRun(threadId: string, request: ResumeRequest): Promise<ResumeResult> {
  const response = await fetch(toApiUrl(`/api/runs/${threadId}/resume`), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });
  if (!response.ok) {
    throw new Error(await errorMessage(response, "Failed to resume run"));
  }
  return response.json() as Promise<ResumeResult>;
}

export async function listSkills(projectRoot?: string): Promise<{ skills: SkillMetadata[] }> {
  const params = new URLSearchParams();
  if (projectRoot?.trim()) {
    params.set("project_root", projectRoot.trim());
  }
  const query = params.toString();
  const response = await fetch(toApiUrl(`/api/skills${query ? `?${query}` : ""}`));
  if (!response.ok) {
    throw new Error(`Failed to list skills: ${response.status}`);
  }
  return response.json() as Promise<{ skills: SkillMetadata[] }>;
}

export async function getSkill(skillId: string, includeBody = false, projectRoot?: string): Promise<{ skill: SkillMetadata }> {
  const params = new URLSearchParams({ include_body: includeBody ? "true" : "false" });
  if (projectRoot?.trim()) {
    params.set("project_root", projectRoot.trim());
  }
  const response = await fetch(toApiUrl(`/api/skills/${encodeURIComponent(skillId)}?${params.toString()}`));
  if (!response.ok) {
    throw new Error(`Failed to get skill: ${response.status}`);
  }
  return response.json() as Promise<{ skill: SkillMetadata }>;
}

export async function installSkill(projectRoot: string, zipPath: string): Promise<SkillInstallResponse> {
  const response = await fetch(toApiUrl("/api/skills/install"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ project_root: projectRoot, zip_path: zipPath }),
  });
  if (!response.ok) {
    throw new Error(await errorMessage(response, "Failed to install skill"));
  }
  return response.json() as Promise<SkillInstallResponse>;
}

export async function getRunState(threadId: string): Promise<RunStateProjection> {
  const response = await fetch(toApiUrl(`/api/runs/${threadId}/state`));
  if (!response.ok) {
    throw new Error(`Failed to get run state: ${response.status}`);
  }
  return response.json() as Promise<RunStateProjection>;
}

export async function replayRun(threadId: string): Promise<RunReplayExport> {
  const response = await fetch(toApiUrl(`/api/runs/${threadId}/replay`));
  if (!response.ok) {
    throw new Error(`Failed to replay run: ${response.status}`);
  }
  return response.json() as Promise<RunReplayExport>;
}

export async function getRunContext(threadId: string): Promise<RunContextTrace> {
  const response = await fetch(toApiUrl(`/api/runs/${threadId}/context`));
  if (!response.ok) {
    throw new Error(`Failed to get run context: ${response.status}`);
  }
  return response.json() as Promise<RunContextTrace>;
}

export async function getRunTrace(threadId: string): Promise<TraceExport> {
  const response = await fetch(toApiUrl(`/api/runs/${encodeURIComponent(threadId)}/trace`));
  if (!response.ok) {
    throw new Error(`Failed to get run trace: ${response.status}`);
  }
  return response.json() as Promise<TraceExport>;
}

export async function createConversation(title?: string): Promise<{ conversation: Conversation }> {
  const response = await fetch(toApiUrl("/api/conversations"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title }),
  });
  if (!response.ok) {
    throw new Error(`Failed to create conversation: ${response.status}`);
  }
  return response.json() as Promise<{ conversation: Conversation }>;
}

export async function listConversations(includeArchived = false): Promise<{ conversations: Conversation[] }> {
  const response = await fetch(toApiUrl(`/api/conversations${includeArchived ? "?include_archived=true" : ""}`));
  if (!response.ok) {
    throw new Error(`Failed to list conversations: ${response.status}`);
  }
  return response.json() as Promise<{ conversations: Conversation[] }>;
}

export async function updateConversation(conversationId: string, request: Partial<{ title: string; archived: boolean }>): Promise<{ conversation: Conversation }> {
  const response = await fetch(toApiUrl(`/api/conversations/${encodeURIComponent(conversationId)}`), {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });
  if (!response.ok) {
    throw new Error(`Failed to update conversation: ${response.status}`);
  }
  return response.json() as Promise<{ conversation: Conversation }>;
}

export async function getConversationTranscript(conversationId: string): Promise<{
  conversation_id: string;
  messages: TranscriptMessage[];
  compaction_summaries?: CompactionSummary[];
  tool_output_replacements?: ToolOutputReplacement[];
  branch_records?: ConversationBranchRecord[];
  active_head_transitions?: ActiveHeadTransition[];
}> {
  const response = await fetch(toApiUrl(`/api/conversations/${encodeURIComponent(conversationId)}/transcript`));
  if (!response.ok) {
    throw new Error(`Failed to get conversation transcript: ${response.status}`);
  }
  return response.json() as Promise<{
    conversation_id: string;
    messages: TranscriptMessage[];
    compaction_summaries?: CompactionSummary[];
    tool_output_replacements?: ToolOutputReplacement[];
    branch_records?: ConversationBranchRecord[];
    active_head_transitions?: ActiveHeadTransition[];
  }>;
}

export async function forkConversation(conversationId: string, sourceMessageId: string): Promise<BranchOperationResponse> {
  const response = await fetch(toApiUrl(`/api/conversations/${encodeURIComponent(conversationId)}/fork`), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ source_message_id: sourceMessageId }),
  });
  if (!response.ok) {
    throw new Error(`Failed to fork conversation: ${response.status}`);
  }
  return response.json() as Promise<BranchOperationResponse>;
}

export async function rollbackConversation(conversationId: string, targetMessageId: string): Promise<BranchOperationResponse> {
  const response = await fetch(toApiUrl(`/api/conversations/${encodeURIComponent(conversationId)}/rollback`), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ target_message_id: targetMessageId }),
  });
  if (!response.ok) {
    throw new Error(`Failed to rollback conversation: ${response.status}`);
  }
  return response.json() as Promise<BranchOperationResponse>;
}

export async function getConversationContext(conversationId: string): Promise<{ conversation_id: string; items: RunContextTrace["included"]; trace: Record<string, unknown> }> {
  const response = await fetch(toApiUrl(`/api/conversations/${encodeURIComponent(conversationId)}/context`));
  if (!response.ok) {
    throw new Error(`Failed to get conversation context: ${response.status}`);
  }
  return response.json() as Promise<{ conversation_id: string; items: RunContextTrace["included"]; trace: Record<string, unknown> }>;
}

export async function getConversationTrace(conversationId: string): Promise<TraceExport> {
  const response = await fetch(toApiUrl(`/api/conversations/${encodeURIComponent(conversationId)}/trace`));
  if (!response.ok) {
    throw new Error(`Failed to get conversation trace: ${response.status}`);
  }
  return response.json() as Promise<TraceExport>;
}

export async function compactConversation(conversationId: string, request: CompactConversationRequest = {}): Promise<CompactConversationResponse> {
  const response = await fetch(toApiUrl(`/api/conversations/${encodeURIComponent(conversationId)}/compact`), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });
  if (!response.ok) {
    throw new Error(`Failed to compact conversation: ${response.status}`);
  }
  return response.json() as Promise<CompactConversationResponse>;
}

export async function getProjectIndexStatus(root?: string): Promise<ProjectIndexStatus> {
  const params = root ? `?root=${encodeURIComponent(root)}` : "";
  const response = await fetch(toApiUrl(`/api/project/index/status${params}`));
  if (!response.ok) {
    throw new Error(`Failed to get project index status: ${response.status}`);
  }
  return response.json() as Promise<ProjectIndexStatus>;
}

export async function refreshProjectIndex(root?: string): Promise<ProjectIndexStatus> {
  const response = await fetch(toApiUrl("/api/project/index/refresh"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ root }),
  });
  if (!response.ok) {
    throw new Error(`Failed to refresh project index: ${response.status}`);
  }
  return response.json() as Promise<ProjectIndexStatus>;
}

export async function searchProject(query: string, root?: string): Promise<ProjectSearchResponse> {
  const response = await fetch(toApiUrl("/api/project/search"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, root, limit: 8 }),
  });
  if (!response.ok) {
    throw new Error(`Failed to search project: ${response.status}`);
  }
  return response.json() as Promise<ProjectSearchResponse>;
}

export async function getProjectTrace(root?: string): Promise<TraceExport> {
  const params = root ? `?root=${encodeURIComponent(root)}` : "";
  const response = await fetch(toApiUrl(`/api/project/trace${params}`));
  if (!response.ok) {
    throw new Error(`Failed to get project trace: ${response.status}`);
  }
  return response.json() as Promise<TraceExport>;
}

export type MemoryListOptions = {
  query?: string;
  scope?: MemoryScope;
  type?: MemoryType;
  status?: MemoryStatus;
  tag?: string;
  include_non_injectable?: boolean;
};

export async function listMemory(options: string | MemoryListOptions = ""): Promise<{ memories: MemoryRecord[] }> {
  const normalized = typeof options === "string" ? { query: options } : options;
  const params = new URLSearchParams();
  if (normalized.query) {
    params.set("query", normalized.query);
  }
  if (normalized.scope) {
    params.append("scope", normalized.scope);
  }
  if (normalized.type) {
    params.append("type", normalized.type);
  }
  if (normalized.status) {
    params.append("status", normalized.status);
  }
  if (normalized.tag) {
    params.append("tag", normalized.tag);
  }
  if (normalized.include_non_injectable) {
    params.set("include_non_injectable", "true");
  }
  const query = params.toString();
  const response = await fetch(toApiUrl(`/api/memory${query ? `?${query}` : ""}`));
  if (!response.ok) {
    throw new Error(`Failed to list memory: ${response.status}`);
  }
  return response.json() as Promise<{ memories: MemoryRecord[] }>;
}

export async function searchMemory(query: string): Promise<MemorySearchResponse> {
  const response = await fetch(toApiUrl("/api/memory/search"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, top_k: 8 }),
  });
  if (!response.ok) {
    throw new Error(`Failed to search memory: ${response.status}`);
  }
  return response.json() as Promise<MemorySearchResponse>;
}

export async function getMemoryTrace(params: Record<string, string | undefined> = {}): Promise<TraceExport> {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value) {
      search.set(key, value);
    }
  });
  const query = search.toString();
  const response = await fetch(toApiUrl(`/api/memory/trace${query ? `?${query}` : ""}`));
  if (!response.ok) {
    throw new Error(`Failed to get memory trace: ${response.status}`);
  }
  return response.json() as Promise<TraceExport>;
}

export async function inspectReplacement(replacementId: string): Promise<ReplacementInspection> {
  const response = await fetch(toApiUrl(`/api/replacements/${encodeURIComponent(replacementId)}/inspect`));
  if (!response.ok) {
    throw new Error(await errorMessage(response, "Failed to inspect replacement"));
  }
  return response.json() as Promise<ReplacementInspection>;
}

export async function getMemory(memoryId: string): Promise<{ memory: MemoryRecord }> {
  const response = await fetch(toApiUrl(`/api/memory/${encodeURIComponent(memoryId)}`));
  if (!response.ok) {
    throw new Error(`Failed to get memory: ${response.status}`);
  }
  return response.json() as Promise<{ memory: MemoryRecord }>;
}

export async function createMemory(request: { text: string; scope: MemoryScope; type: MemoryType; tags?: string[]; confidence?: number; source?: Record<string, unknown> }): Promise<{ memory: MemoryRecord }> {
  const response = await fetch(toApiUrl("/api/memory"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });
  if (!response.ok) {
    throw new Error(`Failed to create memory: ${response.status}`);
  }
  return response.json() as Promise<{ memory: MemoryRecord }>;
}

export async function updateMemory(memoryId: string, request: Partial<{ text: string; scope: MemoryScope; type: MemoryType; status: MemoryStatus; tags: string[]; confidence: number; source: Record<string, unknown> }>): Promise<{ memory: MemoryRecord }> {
  const response = await fetch(toApiUrl(`/api/memory/${encodeURIComponent(memoryId)}`), {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });
  if (!response.ok) {
    throw new Error(`Failed to update memory: ${response.status}`);
  }
  return response.json() as Promise<{ memory: MemoryRecord }>;
}

export async function memoryAction(memoryId: string, action: MemoryAction, extra: Record<string, unknown> = {}): Promise<Record<string, unknown>> {
  const response = await fetch(toApiUrl(`/api/memory/${encodeURIComponent(memoryId)}/actions`), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action, ...extra }),
  });
  if (!response.ok) {
    throw new Error(`Failed to apply memory action: ${response.status}`);
  }
  return response.json() as Promise<Record<string, unknown>>;
}

export async function deleteMemory(memoryId: string): Promise<{ deleted: boolean; memory_id: string }> {
  const response = await fetch(toApiUrl(`/api/memory/${encodeURIComponent(memoryId)}`), { method: "DELETE" });
  if (!response.ok) {
    throw new Error(`Failed to delete memory: ${response.status}`);
  }
  return response.json() as Promise<{ deleted: boolean; memory_id: string }>;
}

export async function extractMemory(prompt: string, threadId?: string | null): Promise<{ status: string; candidates: MemoryCandidate[] }> {
  const response = await fetch(toApiUrl("/api/memory/extract"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt, thread_id: threadId, dry_run: true }),
  });
  if (!response.ok) {
    throw new Error(`Failed to extract memory: ${response.status}`);
  }
  return response.json() as Promise<{ status: string; candidates: MemoryCandidate[] }>;
}

export async function decideMemoryCandidate(candidateId: string, decision: string, text?: string): Promise<Record<string, unknown>> {
  const response = await fetch(toApiUrl(`/api/memory/candidates/${encodeURIComponent(candidateId)}/decisions`), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ decision, text }),
  });
  if (!response.ok) {
    throw new Error(`Failed to decide memory candidate: ${response.status}`);
  }
  return response.json() as Promise<Record<string, unknown>>;
}

export async function cancelRun(threadId: string): Promise<{ status: string; event?: KiraEvent }> {
  const response = await fetch(toApiUrl(`/api/runs/${threadId}/cancel`), { method: "POST" });
  if (!response.ok) {
    throw new Error(`Failed to cancel run: ${response.status}`);
  }
  return response.json() as Promise<{ status: string; event?: KiraEvent }>;
}

async function errorMessage(response: Response, fallback: string): Promise<string> {
  try {
    const payload = await response.json();
    const detail = payload?.detail;
    if (detail?.code) {
      return `${detail.code}: ${detail.message ?? fallback}`;
    }
  } catch {
    return `${fallback}: ${response.status}`;
  }
  return `${fallback}: ${response.status}`;
}
