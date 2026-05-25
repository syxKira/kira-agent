from __future__ import annotations

from dataclasses import dataclass

from kira_server.storage.failure import FailureClass, is_retryable


@dataclass(frozen=True)
class RetryDecision:
    retry: bool
    attempts_remaining: int
    reason: str


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 2

    def decide(self, *, failure_class: FailureClass, attempt_number: int, idempotent: bool) -> RetryDecision:
        remaining = max(self.max_attempts - attempt_number, 0)
        retry = is_retryable(failure_class, idempotent=idempotent, attempts_remaining=remaining)
        if retry:
            return RetryDecision(retry=True, attempts_remaining=remaining, reason="retryable")
        if not idempotent:
            return RetryDecision(retry=False, attempts_remaining=remaining, reason="not_idempotent")
        if remaining <= 0:
            return RetryDecision(retry=False, attempts_remaining=0, reason="retry_exhausted")
        return RetryDecision(retry=False, attempts_remaining=remaining, reason="non_retryable_failure")
