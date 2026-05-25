from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ToolResult(BaseModel):
    ok: bool
    code: str
    message: str
    data: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    truncated: bool = False


def tool_success(
    *,
    code: str = "ok",
    message: str = "Tool completed",
    data: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
    truncated: bool = False,
) -> dict[str, Any]:
    return ToolResult(
        ok=True,
        code=code,
        message=message,
        data=data or {},
        metadata=metadata or {},
        truncated=truncated,
    ).model_dump()


def tool_error(
    *,
    code: str,
    message: str,
    data: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
    truncated: bool = False,
) -> dict[str, Any]:
    return ToolResult(
        ok=False,
        code=code,
        message=message,
        data=data or {},
        metadata=metadata or {},
        truncated=truncated,
    ).model_dump()


RESULT_SCHEMA = ToolResult.model_json_schema()
