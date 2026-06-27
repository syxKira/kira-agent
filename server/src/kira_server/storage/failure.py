from __future__ import annotations

from enum import Enum


class FailureClass(str, Enum):
    VALIDATION = "validation_error"
    PERMISSION = "permission_error"
    TIMEOUT = "timeout_error"
    TRANSIENT_EXTERNAL = "transient_external_error"
    PROVIDER_CONFIG = "provider_config_error"
    PROVIDER_STREAM = "provider_stream_error"
    TOOL = "tool_error"
    SIDE_EFFECT_CONFLICT = "side_effect_conflict"
    CANCELLED = "cancelled"
    INVARIANT = "invariant_error"


RETRYABLE_FAILURES = {
    FailureClass.TIMEOUT,
    FailureClass.TRANSIENT_EXTERNAL,
    FailureClass.PROVIDER_STREAM,
}


def classify_error_code(code: str | None) -> FailureClass:
    value = (code or "").lower()
    if "validation" in value:
        return FailureClass.VALIDATION
    if "permission" in value or "path_outside_root" in value or "forbidden" in value:
        return FailureClass.PERMISSION
    if "timeout" in value:
        return FailureClass.TIMEOUT
    if "provider_config" in value or "missing_api_key" in value or "invalid_provider" in value:
        return FailureClass.PROVIDER_CONFIG
    if "provider" in value:
        return FailureClass.PROVIDER_STREAM
    if "side_effect" in value or "ledger" in value:
        return FailureClass.SIDE_EFFECT_CONFLICT
    if "cancel" in value:
        return FailureClass.CANCELLED
    if "invariant" in value or "checkpoint" in value:
        return FailureClass.INVARIANT
    if "tool" in value:
        return FailureClass.TOOL
    return FailureClass.TRANSIENT_EXTERNAL


def is_retryable(failure_class: FailureClass, *, idempotent: bool, attempts_remaining: int) -> bool:
    return idempotent and attempts_remaining > 0 and failure_class in RETRYABLE_FAILURES
