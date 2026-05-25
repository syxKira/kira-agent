from __future__ import annotations

import os
import re
import subprocess
import time
from typing import Any

from pydantic import BaseModel, Field

from kira_server.providers.config import redact_text
from kira_server.tooling.policy import ProjectRootResolver
from kira_server.tooling.results import tool_error, tool_success

BASE_ENV_KEYS = {
    "HOME",
    "PATH",
    "PYTHONPATH",
    "PYTHONIOENCODING",
    "SSL_CERT_FILE",
    "REQUESTS_CA_BUNDLE",
}
ALLOWED_ENV_PREFIXES = ("KIRA_", "DS_", "TRINO_")
ENV_FILE_READ_RE = re.compile(r"\b(cat|head|tail|grep|egrep|fgrep|sed|awk|less|more)\b[^;&|]*\.env(?:\.[\w.-]+)?", re.IGNORECASE)
ENV_DUMP_RE = re.compile(r"(^|[;&|]\s*)(env|printenv)(\s|$)", re.IGNORECASE)
SECRET_VAR_ECHO_RE = re.compile(r"\b(echo|printf)\b[^;&|]*\$[A-Za-z_]*(?:TOKEN|PASSWORD|SECRET|API_KEY|AUTHORIZATION|BEARER)[A-Za-z_]*", re.IGNORECASE)


class RunShellCommandInput(BaseModel):
    command: str = Field(
        min_length=1,
        description=(
            "Non-interactive shell command to run. Use this for the actual target command, such as an installed skill send script. "
            "Do not use shell commands such as python -c, node -e, date, echo, printf, or jq merely to synthesize, compact, or print JSON that can be written directly in the assistant response."
            " If passing compressed JSON to a script, pass minified one-line JSON with no spaces outside string values."
        ),
    )
    root: str | None = None
    cwd: str | None = None
    env: dict[str, str] = Field(default_factory=dict)
    timeout_seconds: float = Field(default=30.0, gt=0, le=300)
    stdout_limit: int = Field(default=8_000, ge=1, le=100_000)
    stderr_limit: int = Field(default=8_000, ge=1, le=100_000)


def run_shell_command_tool(
    command: str,
    root: str | None = None,
    cwd: str | None = None,
    env: dict[str, str] | None = None,
    timeout_seconds: float = 30.0,
    stdout_limit: int = 8_000,
    stderr_limit: int = 8_000,
    *,
    resolver: ProjectRootResolver | None = None,
) -> dict[str, Any]:
    resolver = resolver or ProjectRootResolver()
    resolved_root, error = resolver.resolve_root(root)
    if error is not None or resolved_root is None:
        return error

    cwd_path = resolved_root.path
    relative_cwd = "."
    if cwd:
        _, resolved_cwd, rel_cwd, cwd_error = resolver.resolve_child(cwd, str(resolved_root.path))
        if cwd_error is not None or resolved_cwd is None or rel_cwd is None:
            return cwd_error
        if not resolved_cwd.is_dir():
            return tool_error(
                code="invalid_cwd",
                message="Shell cwd must be a project-local directory",
                metadata={"cwd": cwd, **resolved_root.metadata()},
            )
        cwd_path = resolved_cwd
        relative_cwd = rel_cwd.as_posix()

    secret_error = _secret_inspection_error(command, resolved_root.metadata(), relative_cwd)
    if secret_error is not None:
        return secret_error

    child_env = _filtered_env(env or {})
    start = time.monotonic()
    try:
        completed = subprocess.run(
            command,
            cwd=cwd_path,
            env=child_env,
            shell=True,
            executable="/bin/bash",
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        duration = time.monotonic() - start
        stdout, stdout_truncated = _cap_output(_redact(_coerce_output(exc.stdout), child_env), stdout_limit)
        stderr, stderr_truncated = _cap_output(_redact(_coerce_output(exc.stderr), child_env), stderr_limit)
        return tool_error(
            code="timeout",
            message="Shell command timed out",
            data={"exit_code": None, "stdout": stdout, "stderr": stderr},
            metadata={
                **resolved_root.metadata(),
                "cwd": relative_cwd,
                "duration_seconds": duration,
                "timeout_seconds": timeout_seconds,
                "stdout_truncated": stdout_truncated,
                "stderr_truncated": stderr_truncated,
                "env_keys": sorted(child_env.keys()),
            },
            truncated=stdout_truncated or stderr_truncated,
        )
    except OSError as exc:
        return tool_error(
            code="execution_error",
            message="Shell command could not be started",
            metadata={"error": _redact(str(exc), child_env), **resolved_root.metadata(), "cwd": relative_cwd},
        )

    duration = time.monotonic() - start
    stdout, stdout_truncated = _cap_output(_redact(completed.stdout, child_env), stdout_limit)
    stderr, stderr_truncated = _cap_output(_redact(completed.stderr, child_env), stderr_limit)
    result = tool_success if completed.returncode == 0 else tool_error
    return result(
        code="shell_completed" if completed.returncode == 0 else "shell_failed",
        message="Shell command completed" if completed.returncode == 0 else "Shell command exited with a non-zero status",
        data={"exit_code": completed.returncode, "stdout": stdout, "stderr": stderr},
        metadata={
            **resolved_root.metadata(),
            "cwd": relative_cwd,
            "duration_seconds": duration,
            "timeout_seconds": timeout_seconds,
            "stdout_truncated": stdout_truncated,
            "stderr_truncated": stderr_truncated,
            "env_keys": sorted(child_env.keys()),
            "command_preview": _redact(command[:300], child_env),
        },
        truncated=stdout_truncated or stderr_truncated,
    )


def _filtered_env(extra_env: dict[str, str]) -> dict[str, str]:
    env = {
        key: value
        for key, value in os.environ.items()
        if key in BASE_ENV_KEYS or key.startswith(ALLOWED_ENV_PREFIXES)
    }
    for key, value in extra_env.items():
        if key in BASE_ENV_KEYS or key.startswith(ALLOWED_ENV_PREFIXES):
            env[key] = value
    return env


def _cap_output(output: str, limit: int) -> tuple[str, bool]:
    if len(output) <= limit:
        return output, False
    return output[:limit], True


def _coerce_output(output: str | bytes | None) -> str:
    if output is None:
        return ""
    if isinstance(output, bytes):
        return output.decode("utf-8", errors="replace")
    return output


def _redact(value: str, env: dict[str, str] | None = None) -> str:
    text = redact_text(value) or ""
    for key, secret in (env or {}).items():
        if _is_secret_key(key) and secret:
            text = text.replace(secret, "[redacted]")
    return text


def _is_secret_key(key: str) -> bool:
    upper = key.upper()
    return any(token in upper for token in ("TOKEN", "PASSWORD", "SECRET", "KEY"))


def _secret_inspection_error(command: str, root_metadata: dict[str, Any], relative_cwd: str) -> dict[str, Any] | None:
    if ENV_FILE_READ_RE.search(command) or ENV_DUMP_RE.search(command) or SECRET_VAR_ECHO_RE.search(command):
        return tool_error(
            code="secret_inspection_denied",
            message="Shell commands may not print .env files or secret environment variables. Run the target script and report missing credentials instead.",
            metadata={**root_metadata, "cwd": relative_cwd, "command_preview": command[:300]},
        )
    return None
