from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, ValidationError

from kira_server.tooling.hitl import AskUserQuestionInput, ask_user_question_tool
from kira_server.tooling.policy import ProjectRootResolver
from kira_server.tooling.project_files import (
    ListProjectFilesInput,
    ReadProjectFileInput,
    SearchProjectFilesInput,
    list_project_files_tool,
    read_project_file_tool,
    search_project_files_tool,
)
from kira_server.tooling.python_exec import RunPythonScriptInput, run_python_script_tool
from kira_server.tooling.results import RESULT_SCHEMA, tool_error
from kira_server.tooling.shell_exec import RunShellCommandInput, run_shell_command_tool


class ToolRegistry:
    def __init__(self, default_root: Path | None = None, prefer_rg: bool = True) -> None:
        self.resolver = ProjectRootResolver(default_root)
        self.prefer_rg = prefer_rg
        self._tools: dict[str, StructuredTool] = {}
        self._risk: dict[str, str] = {}
        self._register_defaults()

    @property
    def tool_names(self) -> list[str]:
        return sorted(self._tools)

    def tools_for_graph(self, names: list[str]) -> list[StructuredTool]:
        return [self._tools[name] for name in names if name in self._tools]

    def metadata(self) -> dict[str, Any]:
        return {
            "tools": [
                {
                    "name": name,
                    "description": tool.description,
                    "args_schema": _schema_for(tool.args_schema),
                    "result_schema": RESULT_SCHEMA,
                    "risk": self._risk[name],
                }
                for name, tool in sorted(self._tools.items())
            ]
        }

    def invoke(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        tool = self._tools.get(name)
        if tool is None:
            return tool_error(code="tool_not_found", message=f"Tool '{name}' is not registered")
        try:
            return tool.invoke(arguments)
        except ValidationError as exc:
            return tool_error(
                code="validation_error",
                message="Tool arguments failed validation",
                metadata={"errors": exc.errors()},
            )
        except Exception as exc:
            return tool_error(
                code="execution_error",
                message="Tool execution failed",
                metadata={"error_type": type(exc).__name__, "error": str(exc)},
            )

    def _register_defaults(self) -> None:
        self._register(
            name="list_project_files",
            description="List bounded read-only project files under an allowed root.",
            args_schema=ListProjectFilesInput,
            risk="read_only_project_files",
            func=lambda root=None, glob=None, limit=100: list_project_files_tool(
                root=root,
                glob=glob,
                limit=limit,
                resolver=self.resolver,
                prefer_rg=self.prefer_rg,
            ),
        )
        self._register(
            name="search_project_files",
            description="Search bounded read-only project text under an allowed root.",
            args_schema=SearchProjectFilesInput,
            risk="read_only_project_files",
            func=lambda query, root=None, glob=None, limit=50: search_project_files_tool(
                query=query,
                root=root,
                glob=glob,
                limit=limit,
                resolver=self.resolver,
                prefer_rg=self.prefer_rg,
            ),
        )
        self._register(
            name="read_project_file",
            description="Read a bounded slice of a project-local text file.",
            args_schema=ReadProjectFileInput,
            risk="read_only_project_files",
            func=lambda path, root=None, offset=0, limit=20_000: read_project_file_tool(
                path=path,
                root=root,
                offset=offset,
                limit=limit,
                resolver=self.resolver,
            ),
        )
        self._register(
            name="run_python_script",
            description="Run a project-local Python script with cwd, env, timeout, and output controls.",
            args_schema=RunPythonScriptInput,
            risk="controlled_python_execution",
            func=lambda path, root=None, cwd=None, args=None, env=None, timeout_seconds=5.0, stdout_limit=4_000, stderr_limit=4_000: run_python_script_tool(
                path=path,
                root=root,
                cwd=cwd,
                args=args or [],
                env=env or {},
                timeout_seconds=timeout_seconds,
                stdout_limit=stdout_limit,
                stderr_limit=stderr_limit,
                resolver=self.resolver,
            ),
        )
        self._register(
            name="run_shell_command",
            description=(
                "Run a bounded shell command from a project-local working directory with timeout and output limits. "
                "Use it for the actual target command, for example an installed skill send script. "
                "Do not call it just to synthesize, compact, or print JSON before a later command; write that JSON directly and pass it to the target script."
                " When the user asks for compressed JSON, pass minified one-line JSON with no spaces outside string values."
            ),
            args_schema=RunShellCommandInput,
            risk="controlled_shell_execution",
            func=lambda command, root=None, cwd=None, env=None, timeout_seconds=30.0, stdout_limit=8_000, stderr_limit=8_000: run_shell_command_tool(
                command=command,
                root=root,
                cwd=cwd,
                env=env or {},
                timeout_seconds=timeout_seconds,
                stdout_limit=stdout_limit,
                stderr_limit=stderr_limit,
                resolver=self.resolver,
            ),
        )
        self._register(
            name="ask_user_question",
            description="Return a pending human question payload for later HITL integration.",
            args_schema=AskUserQuestionInput,
            risk="hitl_placeholder",
            func=lambda question, fields=None: ask_user_question_tool(question=question, fields=fields or []),
        )

    def _register(
        self,
        *,
        name: str,
        description: str,
        args_schema: type[BaseModel],
        risk: str,
        func: Callable[..., dict[str, Any]],
    ) -> None:
        self._tools[name] = StructuredTool.from_function(
            name=name,
            description=description,
            func=func,
            args_schema=args_schema,
        )
        self._risk[name] = risk


def create_tool_registry(default_root: Path | None = None, prefer_rg: bool = True) -> ToolRegistry:
    return ToolRegistry(default_root=default_root, prefer_rg=prefer_rg)


def _schema_for(args_schema: Any) -> dict[str, Any]:
    if hasattr(args_schema, "model_json_schema"):
        return args_schema.model_json_schema()
    return {}
