from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any, Literal

from pydantic import BaseModel, Field


ContextKind = Literal[
    "system",
    "skill_summary",
    "skill_doc",
    "skill_reference",
    "workflow_hint",
    "permission",
    "project_file",
    "project_search",
    "memory",
    "conversation_history",
    "conversation_summary",
    "compaction_summary",
    "tool_summary",
    "run",
    "omission",
    "debug",
]
TrustLabel = Literal["trusted_system", "trusted_skill", "untrusted_project", "user_supplied", "runtime_generated"]


class Citation(BaseModel):
    root_id: str
    path: str
    citation_type: str = "project"
    citation_id: str | None = None
    memory_id: str | None = None
    start_line: int | None = None
    end_line: int | None = None
    chunk_id: str | None = None
    content_hash: str | None = None
    indexed_at: str | None = None
    stale: bool = False
    query: str | None = None


class ContextItem(BaseModel):
    id: str = Field(min_length=1)
    kind: ContextKind
    text: str = ""
    payload: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    trust: TrustLabel
    budget_cost: int = Field(default=0, ge=0)
    citations: list[Citation] = Field(default_factory=list)


class ContextBudget(BaseModel):
    max_items: int = Field(default=20, ge=1, le=200)
    max_chars: int = Field(default=24_000, ge=500, le=200_000)
    max_item_chars: int = Field(default=8_000, ge=100, le=100_000)


class ContextTrace(BaseModel):
    thread_id: str
    budget: ContextBudget
    included: list[ContextItem] = Field(default_factory=list)
    truncated: list[dict[str, Any]] = Field(default_factory=list)
    omitted: list[dict[str, Any]] = Field(default_factory=list)
    provider: dict[str, Any] = Field(default_factory=dict)
    selected_skills: list[dict[str, Any]] = Field(default_factory=list)
    project: dict[str, Any] | None = None
    memory: dict[str, Any] | None = None
    transcript: dict[str, Any] | None = None


@dataclass(frozen=True)
class PackedContext:
    items: list[ContextItem]
    trace: ContextTrace


PRIORITY: dict[str, int] = {
    "system": 0,
    "skill_summary": 10,
    "workflow_hint": 15,
    "permission": 20,
    "skill_doc": 30,
    "project_file": 40,
    "project_search": 45,
    "memory": 35,
    "conversation_history": 25,
    "conversation_summary": 24,
    "compaction_summary": 24,
    "tool_summary": 38,
    "run": 50,
    "debug": 60,
    "omission": 90,
}


def make_context_id(prefix: str, *parts: Any) -> str:
    digest = hashlib.sha256("|".join(str(part) for part in parts).encode("utf-8")).hexdigest()[:16]
    return f"{prefix}:{digest}"


def estimate_budget_cost(text: str, payload: dict[str, Any] | None = None) -> int:
    payload_cost = len(str(payload or {}))
    return max(1, (len(text) + payload_cost + 3) // 4)


def pack_context(
    *,
    thread_id: str,
    items: list[ContextItem],
    budget: ContextBudget | None = None,
    provider: dict[str, Any] | None = None,
    selected_skills: list[dict[str, Any]] | None = None,
    project: dict[str, Any] | None = None,
    memory: dict[str, Any] | None = None,
    transcript: dict[str, Any] | None = None,
) -> PackedContext:
    resolved_budget = budget or ContextBudget()
    included: list[ContextItem] = []
    truncated: list[dict[str, Any]] = []
    omitted: list[dict[str, Any]] = []
    used_chars = 0

    for item in sorted(items, key=_context_sort_key):
        if len(included) >= resolved_budget.max_items:
            omitted.append({"id": item.id, "kind": item.kind, "reason": "max_items"})
            continue
        text = item.text
        was_truncated = False
        if len(text) > resolved_budget.max_item_chars:
            text = text[: resolved_budget.max_item_chars]
            was_truncated = True
        if used_chars + len(text) > resolved_budget.max_chars:
            remaining = resolved_budget.max_chars - used_chars
            if remaining >= 100:
                text = text[:remaining]
                was_truncated = True
            else:
                omitted.append({"id": item.id, "kind": item.kind, "reason": "max_chars"})
                continue
        packed = item.model_copy(update={"text": text, "budget_cost": estimate_budget_cost(text, item.payload)})
        included.append(packed)
        used_chars += len(text)
        if was_truncated:
            truncated.append({"id": item.id, "kind": item.kind, "reason": "budget", "original_chars": len(item.text), "included_chars": len(text)})

    trace = ContextTrace(
        thread_id=thread_id,
        budget=resolved_budget,
        included=included,
        truncated=truncated,
        omitted=omitted,
        provider=provider or {},
        selected_skills=selected_skills or [],
        project=project,
        memory=memory,
        transcript=transcript,
    )
    return PackedContext(items=included, trace=trace)


def _context_sort_key(item: ContextItem) -> tuple[Any, ...]:
    priority = PRIORITY.get(item.kind, 100)
    if item.kind == "skill_doc":
        skill_id = str(item.metadata.get("skill_id") or "")
        chunk_index = item.metadata.get("chunk_index")
        if not isinstance(chunk_index, int):
            chunk_index = 1_000_000
        return (priority, skill_id, chunk_index, item.id)
    return (priority, item.id)


def context_prompt(items: list[ContextItem]) -> str:
    if not items:
        return ""
    blocks = []
    for item in items:
        source = item.metadata.get("source") or item.kind
        trust = item.trust
        citation_text = ""
        if item.citations:
            citation = item.citations[0]
            line_text = ""
            if citation.start_line is not None:
                line_text = f":{citation.start_line}"
                if citation.end_line and citation.end_line != citation.start_line:
                    line_text += f"-{citation.end_line}"
            citation_text = f" [{citation.path}{line_text}]"
        blocks.append(f"[{item.kind} | {trust} | {source}{citation_text}]\n{item.text}")
    return "\n\n".join(blocks)
