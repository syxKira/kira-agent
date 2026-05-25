from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field

from kira_server.providers.config import REDACTED, redact_text

PermissionDecisionValue = Literal["allow", "ask", "deny"]

SENSITIVE_KEYS = {
    "api_key",
    "apikey",
    "apiKey",
    "authorization",
    "bearer",
    "cookie",
    "set-cookie",
    "private_key",
    "privateKey",
    "secret",
    "token",
    "password",
    "hidden_thinking",
    "thinking",
    "reasoning_content",
}


class PermissionDecision(BaseModel):
    action: str
    decision: PermissionDecisionValue
    reasons: list[str] = Field(default_factory=list)
    subject: dict[str, Any] = Field(default_factory=dict)
    redacted: bool = True
    audit: dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class PermissionErrorDetail(BaseModel):
    code: str
    message: str
    reasons: list[str] = Field(default_factory=list)
    subject: dict[str, Any] = Field(default_factory=dict)
    permission: PermissionDecision | None = None


class PermissionService:
    def evaluate(self, action: str, subject: dict[str, Any] | None = None) -> PermissionDecision:
        safe_subject = redact_value(subject or {})
        decision, reasons = _default_decision(action, safe_subject)
        return PermissionDecision(
            action=action,
            decision=decision,
            reasons=reasons,
            subject=safe_subject if isinstance(safe_subject, dict) else {"value": safe_subject},
            audit={"action": action, "decision": decision},
        )

    def error_detail(self, decision: PermissionDecision) -> PermissionErrorDetail:
        code = "permission_required" if decision.decision == "ask" else "permission_denied"
        return PermissionErrorDetail(
            code=code,
            message=f"Permission decision for '{decision.action}' is {decision.decision}",
            reasons=decision.reasons,
            subject=decision.subject,
            permission=decision,
        )


def redact_value(value: Any) -> Any:
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for key, item in value.items():
            if _is_sensitive_key(str(key)):
                result[key] = REDACTED
            else:
                result[key] = redact_value(item)
        return result
    if isinstance(value, list):
        return [redact_value(item) for item in value]
    if isinstance(value, tuple):
        return [redact_value(item) for item in value]
    if isinstance(value, str):
        return _redact_string(value)
    return value


def _redact_string(value: str) -> str:
    text = redact_text(value) or ""
    text = re.sub(r"Bearer\s+[A-Za-z0-9._~+/=-]+", f"Bearer {REDACTED}", text, flags=re.IGNORECASE)
    text = re.sub(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----", REDACTED, text, flags=re.DOTALL)
    text = re.sub(r"(?i)(api[_-]?key|token|password|secret)\s*[:=]\s*[^,\s]+", lambda m: f"{m.group(1)}={REDACTED}", text)
    return text


def _is_sensitive_key(key: str) -> bool:
    normalized = key.lower().replace("-", "_")
    return normalized in {item.lower().replace("-", "_") for item in SENSITIVE_KEYS}


def _default_decision(action: str, subject: dict[str, Any]) -> tuple[PermissionDecisionValue, list[str]]:
    if action == "provider.override" and subject.get("known") is False:
        return "deny", ["unknown provider profiles are not allowed by the local default policy"]
    if action == "python.run" and (subject.get("temp_script") or subject.get("risky")):
        return "ask", ["risky or temporary Python execution requires explicit approval"]
    if action == "skill.invoke" and subject.get("trusted") is False:
        return "ask", ["untrusted or imported skill invocation requires explicit approval"]
    if action == "workflow.external_action":
        return "ask", ["workflow external actions require explicit approval"]
    if action == "shell.run":
        return "allow", ["controlled shell execution is allowed by local project policy with bounded cwd, timeout, output, and audit metadata"]
    if action == "memory.write" and subject.get("scope") in {"project", "user"}:
        return "ask", ["project and user memory writes require explicit approval"]
    if action == "transcript.delete":
        return "ask", ["transcript deletion is explicit and audited"]
    if action == "replacement.inspect":
        if subject.get("retention_policy") != "debug_only":
            return "deny", ["replacement inspection is only available for retained debug output"]
        return "ask", ["replacement inspection requires explicit approval by default"]
    return "allow", ["allowed by local default policy"]
