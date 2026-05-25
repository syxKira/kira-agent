from __future__ import annotations

import os
import subprocess
import sys
import time
from typing import Any

from pydantic import BaseModel, Field

from kira_server.tooling.policy import ProjectRootResolver
from kira_server.tooling.results import tool_error, tool_success

ALLOWED_ENV = {"PATH", "PYTHONPATH", "PYTHONIOENCODING", "KIRA_TEST_ENV"}


class RunPythonScriptInput(BaseModel):
    path: str = Field(min_length=1)
    root: str | None = None
    cwd: str | None = None
    args: list[str] = Field(default_factory=list)
    env: dict[str, str] = Field(default_factory=dict)
    timeout_seconds: float = Field(default=5.0, gt=0, le=30)
    stdout_limit: int = Field(default=4_000, ge=1, le=50_000)
    stderr_limit: int = Field(default=4_000, ge=1, le=50_000)


def run_python_script_tool(
    path: str,
    root: str | None = None,
    cwd: str | None = None,
    args: list[str] | None = None,
    env: dict[str, str] | None = None,
    timeout_seconds: float = 5.0,
    stdout_limit: int = 4_000,
    stderr_limit: int = 4_000,
    *,
    resolver: ProjectRootResolver | None = None,
) -> dict[str, Any]:
    resolver = resolver or ProjectRootResolver()
    resolved_root, script, relative_script, error = resolver.resolve_child(path, root)
    if error is not None or resolved_root is None or script is None or relative_script is None:
        return error
    if not script.is_file() or script.suffix != ".py":
        return tool_error(
            code="invalid_script",
            message="Python execution requires a project-local .py file",
            metadata={"path": path, **resolved_root.metadata()},
        )

    cwd_path = resolved_root.path
    relative_cwd = "."
    if cwd:
        _, resolved_cwd, rel_cwd, cwd_error = resolver.resolve_child(cwd, str(resolved_root.path))
        if cwd_error is not None or resolved_cwd is None or rel_cwd is None:
            return cwd_error
        if not resolved_cwd.is_dir():
            return tool_error(
                code="invalid_cwd",
                message="Python cwd must be a project-local directory",
                metadata={"cwd": cwd, **resolved_root.metadata()},
            )
        cwd_path = resolved_cwd
        relative_cwd = rel_cwd.as_posix()

    child_env = _filtered_env(env or {})
    start = time.monotonic()
    command = [sys.executable, str(script), *(args or [])]
    try:
        completed = subprocess.run(
            command,
            cwd=cwd_path,
            env=child_env,
            shell=False,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        duration = time.monotonic() - start
        stdout, stdout_truncated = _cap_output(_coerce_output(exc.stdout), stdout_limit)
        stderr, stderr_truncated = _cap_output(_coerce_output(exc.stderr), stderr_limit)
        return tool_error(
            code="timeout",
            message="Python script timed out",
            data={"stdout": stdout, "stderr": stderr},
            metadata={
                **resolved_root.metadata(),
                "path": relative_script.as_posix(),
                "cwd": relative_cwd,
                "duration_seconds": duration,
                "timeout_seconds": timeout_seconds,
                "stdout_truncated": stdout_truncated,
                "stderr_truncated": stderr_truncated,
            },
            truncated=stdout_truncated or stderr_truncated,
        )
    except OSError as exc:
        return tool_error(
            code="execution_error",
            message="Python script could not be started",
            metadata={"error": str(exc), "path": relative_script.as_posix(), **resolved_root.metadata()},
        )

    duration = time.monotonic() - start
    stdout, stdout_truncated = _cap_output(completed.stdout, stdout_limit)
    stderr, stderr_truncated = _cap_output(completed.stderr, stderr_limit)
    ok = completed.returncode == 0
    result = tool_success if ok else tool_error
    return result(
        code="python_completed" if ok else "python_failed",
        message="Python script completed" if ok else "Python script exited with a non-zero status",
        data={"exit_code": completed.returncode, "stdout": stdout, "stderr": stderr},
        metadata={
            **resolved_root.metadata(),
            "path": relative_script.as_posix(),
            "cwd": relative_cwd,
            "duration_seconds": duration,
            "stdout_truncated": stdout_truncated,
            "stderr_truncated": stderr_truncated,
            "env_keys": sorted(child_env.keys()),
        },
        truncated=stdout_truncated or stderr_truncated,
    )


def _filtered_env(extra_env: dict[str, str]) -> dict[str, str]:
    env = {key: value for key, value in os.environ.items() if key in ALLOWED_ENV}
    for key, value in extra_env.items():
        if key in ALLOWED_ENV:
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
