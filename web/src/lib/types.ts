export type KiraEventType =
  | "text_delta"
  | "thinking_delta"
  | "tool_start"
  | "tool_result"
  | "retry"
  | "side_effect_reused"
  | "checkpoint"
  | "interrupt"
  | "resume"
  | "done"
  | "error";

export type KiraEvent = {
  type: KiraEventType;
  thread_id: string;
  seq: number;
  data: Record<string, unknown>;
};

export type RunCreateRequest = {
  prompt: string;
  project_root?: string;
  skill_id?: string;
  skill_ids?: string[];
  disabled_skill_ids?: string[];
  auto_route_skills?: boolean;
  project_context_query?: string;
  project_context_limit?: number;
  auto_project_context?: boolean;
  include_memory?: boolean;
  memory_query?: string;
  memory_top_k?: number;
  memory_scopes?: MemoryScope[];
  memory_types?: MemoryType[];
  context_budget?: ContextBudget;
  fixture?: string | null;
  provider_mode?: "auto" | "fixture" | "real";
  provider?: string;
  model?: string;
  conversation_id?: string;
  overflow_compaction_enabled?: boolean;
  transcript_overflow_thresholds?: TranscriptOverflowThresholds;
};

export type SkillInstallResponse = {
  ok: boolean;
  code: string;
  message: string;
  status: string;
  project_root?: string | null;
  skill_id?: string | null;
  destination?: string | null;
  skipped_entries: string[];
  diagnostics: Array<Record<string, unknown>>;
  skill?: SkillMetadata | null;
};

export type RunStatus = "created" | "running" | "completed" | "error" | "stopped";

export type ProviderMetadata = {
  mode: "fixture" | "real";
  source?: string;
  fixture?: string;
  provider?: string;
  name?: string;
  preset?: string;
  model?: string;
  base_url?: string;
  api_key?: string;
  has_api_key?: boolean;
  fallback_reason?: string;
  attempted_provider?: Record<string, unknown>;
  permission?: PermissionDecision;
  audit_id?: string | null;
  doctor_status?: string | null;
};

export type PermissionDecision = {
  action: string;
  decision: "allow" | "ask" | "deny";
  reasons: string[];
  subject: Record<string, unknown>;
  redacted: boolean;
  audit?: Record<string, unknown>;
  created_at?: string;
};

export type SafetyError = {
  code: string;
  message: string;
  reasons?: string[];
  subject?: Record<string, unknown>;
  permission?: PermissionDecision;
};

export type AuditRecord = {
  id: string;
  action: string;
  status: string;
  decision?: "allow" | "ask" | "deny" | null;
  thread_id?: string | null;
  conversation_id?: string | null;
  turn_id?: string | null;
  provider?: string | null;
  model?: string | null;
  tool?: string | null;
  skill_id?: string | null;
  memory_id?: string | null;
  project_root?: string | null;
  metadata: Record<string, unknown>;
  summary?: string | null;
  redacted: boolean;
  created_at: string;
};

export type DoctorCheck = {
  component: string;
  status: "ok" | "warning" | "error" | "skipped";
  severity: "info" | "warning" | "error";
  message: string;
  remediation?: string | null;
  evidence?: Record<string, unknown>;
};

export type DoctorDiagnostics = {
  status: "ok" | "warning" | "error";
  generated_at: string;
  checks: DoctorCheck[];
  versions?: Record<string, unknown>;
  deep_checks?: Record<string, unknown>;
};

export type WorkflowNodeMetadata = {
  node_type: "model" | "tool" | "passthrough";
  allowed_tools?: string[];
  timeout_hint?: number;
  retry_hint?: number;
  side_effect_hint?: "none" | "read_only" | "external";
  uses_model?: boolean;
};

export type SkillMetadata = {
  skill_id: string;
  name: string;
  description?: string;
  when_to_use?: string | null;
  invocation?: {
    argument_hint?: string | null;
    disable_model_invocation?: boolean;
    user_invocable?: boolean;
    model_invocable?: boolean;
  };
  source?: { key: string; priority: number; path: string };
  valid?: boolean;
  active?: boolean;
  shadowed_by?: string | null;
  body_loaded?: boolean;
  body?: string;
  workflows: Array<Record<string, unknown>>;
  allowed_tools: string[];
  permissions?: Record<string, unknown>;
  fixtures?: Array<Record<string, unknown>>;
  references?: string[];
  context?: string[];
  ui?: Record<string, unknown>;
  diagnostics?: Array<{ code: string; message: string; severity: string; metadata?: Record<string, unknown> }>;
  model_hint?: string | { profile?: string | null; model?: string | null } | null;
};

export type RunCreateResponse = {
  thread_id: string;
  conversation_id?: string | null;
  turn_id?: string | null;
  status: RunStatus;
  fixture?: string | null;
  events_url: string;
  resume_url?: string | null;
  provider: ProviderMetadata;
  skill?: SkillMetadata | null;
  context?: { included_count: number; omitted_count: number; truncated_count: number } | null;
};

export type ContextBudget = {
  max_items: number;
  max_chars: number;
  max_item_chars: number;
};

export type Citation = {
  root_id: string;
  path: string;
  citation_type?: string;
  citation_id?: string | null;
  memory_id?: string | null;
  start_line?: number | null;
  end_line?: number | null;
  chunk_id?: string | null;
  content_hash?: string | null;
  indexed_at?: string | null;
  stale: boolean;
  query?: string | null;
};

export type ContextItem = {
  id: string;
  kind: string;
  text: string;
  payload: Record<string, unknown>;
  metadata: Record<string, unknown>;
  trust: string;
  budget_cost: number;
  citations: Citation[];
};

export type TranscriptOverflowThresholds = {
  max_raw_messages: number;
  max_estimated_tokens: number;
  max_estimated_chars: number;
  budget_pressure_ratio: number;
};

export type CompactionSummary = {
  id: string;
  conversation_id: string;
  source_first_message_id?: string | null;
  source_last_message_id?: string | null;
  source_message_ids: string[];
  source_turn_ids: string[];
  replacement_ids: string[];
  source_hash: string;
  tail_start_message_id?: string | null;
  summary: string;
  source_token_estimate: number;
  summary_token_estimate: number;
  summarizer: Record<string, unknown>;
  status: "active" | "stale" | "error";
  stale: boolean;
  stale_reason?: string | null;
  previous_summary_id?: string | null;
  trigger: string;
  created_at: string;
  updated_at: string;
};

export type ToolOutputReplacement = {
  id: string;
  conversation_id: string;
  turn_id?: string | null;
  thread_id?: string | null;
  message_id: string;
  part_id?: string | null;
  tool_name: string;
  output_hash: string;
  summary: string;
  omitted_char_count: number;
  reason: string;
  retention_policy: string;
  status: string;
  redacted_reference: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type CompactConversationRequest = {
  summarizer_mode?: "fixture" | "real" | "auto";
  provider?: string;
  model?: string;
  tail_messages?: number;
  max_source_messages?: number;
  refresh?: boolean;
  trigger?: "manual" | "overflow" | "refresh";
  thresholds?: TranscriptOverflowThresholds;
};

export type CompactConversationResponse = {
  conversation_id: string;
  summary: CompactionSummary;
  context_item: ContextItem;
  replaced_raw_messages: number;
  tail_start_message_id?: string | null;
  status: string;
  omitted: Array<Record<string, unknown>>;
};

export type RunContextTrace = {
  thread_id: string;
  budget: ContextBudget;
  included: ContextItem[];
  truncated: Array<Record<string, unknown>>;
  omitted: Array<Record<string, unknown>>;
  provider: ProviderMetadata | Record<string, unknown>;
  selected_skills: Array<Record<string, unknown>>;
  project?: Record<string, unknown> | null;
  memory?: Record<string, unknown> | null;
  transcript?: Record<string, unknown> | null;
  audit_ids?: string[];
  permission_decisions?: PermissionDecision[];
  trace_export_refs?: Array<Record<string, unknown>>;
};

export type Conversation = {
  id: string;
  title?: string | null;
  status: "active" | "archived";
  archived: boolean;
  active_head_message_id?: string | null;
  forked_from_conversation_id?: string | null;
  forked_from_message_id?: string | null;
  forked_from_turn_id?: string | null;
  created_at: string;
  updated_at: string;
};

export type ConversationTurn = {
  turn_id: string;
  conversation_id: string;
  thread_id?: string | null;
  user_message_id?: string | null;
  assistant_message_id?: string | null;
  status: string;
  prompt: string;
  created_at: string;
  updated_at: string;
};

export type TranscriptPart = {
  id: string;
  message_id: string;
  conversation_id: string;
  turn_id?: string | null;
  thread_id?: string | null;
  kind: string;
  seq: number;
  text: string;
  payload: Record<string, unknown>;
  visible: boolean;
  token_estimate: number;
  created_at: string;
};

export type TranscriptMessage = {
  id: string;
  conversation_id: string;
  turn_id?: string | null;
  thread_id?: string | null;
  parent_message_id?: string | null;
  logical_parent_message_id?: string | null;
  role: "user" | "assistant" | "tool" | "system";
  status: "draft" | "streaming" | "completed" | "error" | "cancelled";
  branch_status: string;
  parts: TranscriptPart[];
  created_at: string;
  updated_at: string;
};

export type ConversationBranchRecord = {
  id: string;
  operation: "fork" | "rollback";
  source_conversation_id: string;
  target_conversation_id: string;
  source_message_id?: string | null;
  source_turn_id?: string | null;
  previous_active_head_id?: string | null;
  new_active_head_id?: string | null;
  reason: Record<string, unknown>;
  status: string;
  created_at: string;
  updated_at: string;
};

export type ActiveHeadTransition = {
  id: string;
  conversation_id: string;
  operation: "fork" | "rollback";
  previous_active_head_id?: string | null;
  new_active_head_id?: string | null;
  branch_record_id?: string | null;
  reason: Record<string, unknown>;
  created_at: string;
};

export type BranchOperationResponse = {
  conversation: Conversation;
  branch_record: ConversationBranchRecord;
  active_head_transition: ActiveHeadTransition;
  active_head_message_id?: string | null;
  inactive_message_ids: string[];
};

export type TranscriptContextTrace = {
  conversation_id: string;
  turn_id?: string | null;
  active_head_message_id?: string | null;
  branch?: Record<string, unknown>;
  included: Array<Record<string, unknown>>;
  omitted: Array<Record<string, unknown>>;
  summaries?: CompactionSummary[];
};

export type ProjectIndexStatus = {
  root_id: string;
  root: string;
  status: string;
  file_count: number;
  chunk_count: number;
  skipped_count: number;
  omitted_count: number;
  last_refresh_at?: string | null;
  fts_available?: boolean;
  metadata?: Record<string, unknown>;
  error?: Record<string, unknown>;
  audit_ids?: string[];
  permission?: PermissionDecision;
  doctor_status?: string | null;
};

export type ProjectSearchResult = {
  path: string;
  snippet: string;
  start_line?: number | null;
  end_line?: number | null;
  chunk_id?: string | null;
  score: number;
  stale: boolean;
  citation: Citation;
};

export type ProjectSearchResponse = {
  root_id: string;
  root: string;
  query: string;
  results: ProjectSearchResult[];
  omitted_count: number;
  truncated: boolean;
  used_index: boolean;
  used_live: boolean;
  audit_ids?: string[];
  permission?: PermissionDecision;
  trace_export_refs?: Array<Record<string, unknown>>;
};

export type MemoryScope = "session" | "projectLocal" | "project" | "user";
export type MemoryType = "preference" | "feedback" | "decision" | "project" | "reference" | "fact" | "workflow";
export type MemoryStatus = "active" | "stale" | "archived";
export type MemoryAction = "archive" | "delete" | "merge" | "refresh" | "stale" | "promote" | "explain";

export type MemorySource = {
  kind: string;
  summary?: string;
  thread_id?: string | null;
  project_root_id?: string | null;
  metadata?: Record<string, unknown>;
};

export type MemoryRecord = {
  id: string;
  scope: MemoryScope;
  type: MemoryType;
  status: MemoryStatus;
  text: string;
  tags: string[];
  confidence: number;
  source: MemorySource;
  created_at: string;
  updated_at: string;
  last_used_at?: string | null;
  expires_at?: string | null;
  project_root_id?: string | null;
  thread_id?: string | null;
  merged_ids?: string[];
  audit_ids?: string[];
  permission?: PermissionDecision;
};

export type ScoreReason = {
  factor: string;
  score: number;
  matched: string[];
};

export type MemoryRetrievalResult = {
  memory: MemoryRecord;
  score: number;
  score_reasons: ScoreReason[];
  duplicate_ids: string[];
  citation_id?: string | null;
};

export type MemorySearchResponse = {
  query: string;
  results: MemoryRetrievalResult[];
  omitted_count: number;
  filters: Record<string, unknown>;
};

export type GuardResult = {
  allowed: boolean;
  reasons: string[];
  redacted_text: string;
};

export type MemoryCandidate = {
  id: string;
  thread_id?: string | null;
  status: "pending" | "approved" | "rejected" | "deferred" | "blocked";
  suggested_scope: MemoryScope;
  suggested_type: MemoryType;
  text: string;
  confidence: number;
  reason: string;
  risk: string;
  guard: GuardResult;
  duplicate_ids: string[];
  source: MemorySource;
  created_memory_id?: string | null;
  created_at: string;
  updated_at: string;
  audit_ids?: string[];
  permission?: PermissionDecision;
};

export type InterruptKind = "approval" | "edit" | "question" | "python_approval";
export type ResumeDecision = "approve" | "reject" | "submit";

export type AllowedResponse = {
  id: string;
  label: string;
  kind: ResumeDecision;
};

export type InterruptPayload = {
  interrupt_id: string;
  kind: InterruptKind;
  title: string;
  body: string;
  data: Record<string, unknown>;
  allowed_responses: AllowedResponse[];
  metadata?: Record<string, unknown>;
};

export type ResumeRequest = {
  interrupt_id: string;
  decision: ResumeDecision;
  value?: string;
  reason?: string;
  data?: Record<string, unknown>;
};

export type ResumeResult = {
  status: string;
  thread_id: string;
  interrupt_id: string;
  decision: ResumeDecision;
  events: KiraEvent[];
};

export type FailureClass =
  | "validation_error"
  | "permission_error"
  | "timeout_error"
  | "transient_external_error"
  | "provider_config_error"
  | "provider_stream_error"
  | "tool_error"
  | "side_effect_conflict"
  | "cancelled"
  | "invariant_error";

export type RunStateProjection = {
  thread_id: string;
  status: string;
  prompt?: string;
  fixture?: string | null;
  skill?: SkillMetadata | null;
  workflow?: Record<string, unknown> | null;
  provider: ProviderMetadata;
  model?: string | null;
  fixture_fallback: boolean;
  latest_seq: number;
  failure_class?: FailureClass | null;
  repair_required: boolean;
  pending_interrupt?: InterruptPayload | null;
  attempts: Array<Record<string, unknown>>;
  provider_attempts: Array<Record<string, unknown>>;
  side_effects: Array<Record<string, unknown>>;
  repair_notes?: Array<Record<string, unknown>>;
  lock?: Record<string, unknown> | null;
  checkpoints?: Array<Record<string, unknown>>;
  conversation_id?: string | null;
  turn_id?: string | null;
  user_message_id?: string | null;
  assistant_message_id?: string | null;
  transcript_status?: string | null;
  active_head_message_id?: string | null;
  branch_metadata?: Record<string, unknown> | null;
  transcript_parts?: Array<Record<string, unknown>>;
  compaction_summaries?: CompactionSummary[];
  tool_output_replacements?: ToolOutputReplacement[];
  context_trace?: RunContextTrace | null;
  audit_ids?: string[];
  permission_decisions?: PermissionDecision[];
  doctor_status?: string | null;
  trace_export_refs?: Array<Record<string, unknown>>;
};

export type RunReplayExport = {
  thread_id: string;
  state: RunStateProjection;
  events: KiraEvent[];
  audit?: AuditRecord[];
  trace_export?: TraceExport;
  redacted?: boolean;
};

export type TraceExport = {
  scope: string;
  thread_id?: string | null;
  conversation_id?: string | null;
  root_id?: string | null;
  memory_id?: string | null;
  generated_at: string;
  redacted: boolean;
  truncated: boolean;
  limit: number;
  state?: RunStateProjection | null;
  events?: KiraEvent[];
  audit?: AuditRecord[];
  context?: Record<string, unknown> | null;
  provider_attempts?: Array<Record<string, unknown>>;
  side_effects?: Array<Record<string, unknown>>;
  transcript?: Record<string, unknown> | null;
  project?: Record<string, unknown> | null;
  memory?: Record<string, unknown> | null;
};

export type ReplacementInspection = {
  replacement_id: string;
  status: "allowed" | "denied" | "missing";
  content?: string | null;
  reason?: string | null;
  redacted: boolean;
  audit_id?: string | null;
  metadata: Record<string, unknown>;
  permission?: PermissionDecision;
};
