from __future__ import annotations

from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator

from kira_server.providers.config import redact_text

InterruptKind = Literal["approval", "edit", "question", "python_approval"]
ResumeDecision = Literal["approve", "reject", "submit"]


class AllowedResponse(BaseModel):
    id: str = Field(min_length=1, max_length=64)
    label: str = Field(min_length=1, max_length=80)
    kind: ResumeDecision


class InterruptPayload(BaseModel):
    interrupt_id: str = Field(default_factory=lambda: f"interrupt-{uuid4().hex}", min_length=1, max_length=96)
    kind: InterruptKind
    title: str = Field(min_length=1, max_length=160)
    body: str = Field(min_length=1, max_length=2_000)
    data: dict[str, Any] = Field(default_factory=dict)
    allowed_responses: list[AllowedResponse] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_payload(self) -> "InterruptPayload":
        if not self.allowed_responses:
            self.allowed_responses = default_allowed_responses(self.kind)
        self.title = redact_text(self.title).strip()
        self.body = redact_text(self.body).strip()
        self.data = redact_public_dict(self.data)
        self.metadata = redact_public_dict(self.metadata)
        return self

    def public_dict(self) -> dict[str, Any]:
        return self.model_dump()


class ResumeRequest(BaseModel):
    interrupt_id: str = Field(min_length=1, max_length=96)
    decision: ResumeDecision
    value: str | None = Field(default=None, max_length=8_000)
    reason: str | None = Field(default=None, max_length=1_000)
    data: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def redact_payload(self) -> "ResumeRequest":
        if self.value is not None:
            self.value = redact_text(self.value).strip()
        if self.reason is not None:
            self.reason = redact_text(self.reason).strip()
        self.data = redact_public_dict(self.data)
        return self


class ResumeResult(BaseModel):
    status: str
    thread_id: str
    interrupt_id: str
    decision: ResumeDecision
    events: list[dict[str, Any]] = Field(default_factory=list)


def default_allowed_responses(kind: InterruptKind) -> list[AllowedResponse]:
    if kind in {"approval", "python_approval"}:
        return [
            AllowedResponse(id="approve", label="Approve", kind="approve"),
            AllowedResponse(id="reject", label="Reject", kind="reject"),
        ]
    return [AllowedResponse(id="submit", label="Submit", kind="submit")]


def validate_interrupt_payload(payload: dict[str, Any]) -> InterruptPayload:
    return InterruptPayload.model_validate(payload)


def validate_resume_for_interrupt(pending: dict[str, Any], resume: ResumeRequest) -> ResumeRequest:
    interrupt = InterruptPayload.model_validate(pending)
    if resume.interrupt_id != interrupt.interrupt_id:
        raise ValueError("resume interrupt_id does not match pending interrupt")
    allowed = {item.kind for item in interrupt.allowed_responses}
    if resume.decision not in allowed:
        raise ValueError("resume decision is not allowed for pending interrupt")
    if interrupt.kind in {"approval", "python_approval"} and resume.decision == "reject" and not (resume.reason or resume.value):
        raise ValueError("rejection requires a reason")
    if interrupt.kind == "edit" and resume.decision == "submit" and not resume.value:
        raise ValueError("edit resume requires replacement text")
    if interrupt.kind == "question" and resume.decision == "submit" and not (resume.value or resume.data):
        raise ValueError("question resume requires an answer")
    return resume


def redact_public_dict(value: dict[str, Any]) -> dict[str, Any]:
    return {key: _redact_value(item) for key, item in value.items() if key.lower() not in {"api_key", "apikey", "authorization"}}


def _redact_value(value: Any) -> Any:
    if isinstance(value, str):
        return redact_text(value)
    if isinstance(value, dict):
        return redact_public_dict(value)
    if isinstance(value, list):
        return [_redact_value(item) for item in value]
    return value


def make_interrupt(
    *,
    kind: InterruptKind,
    title: str,
    body: str,
    data: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
) -> InterruptPayload:
    return InterruptPayload(kind=kind, title=title, body=body, data=data or {}, metadata=metadata or {})
