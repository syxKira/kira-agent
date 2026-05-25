from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from kira_server.tooling.policy import (
    MAX_FILE_BYTES,
    MAX_PREVIEW_CHARS,
    MAX_READ_CHARS,
    ProjectRootResolver,
    file_metadata,
    is_binary_file,
    is_ignored_path,
    iter_project_files,
    load_gitignore_patterns,
    matches_glob,
)
from kira_server.tooling.results import tool_error, tool_success


class ListProjectFilesInput(BaseModel):
    root: str | None = None
    glob: str | None = None
    limit: int = Field(default=100, ge=1, le=1000)


class SearchProjectFilesInput(BaseModel):
    query: str = Field(min_length=1)
    root: str | None = None
    glob: str | None = None
    limit: int = Field(default=50, ge=1, le=500)


class ReadProjectFileInput(BaseModel):
    path: str = Field(min_length=1)
    root: str | None = None
    offset: int = Field(default=0, ge=0)
    limit: int = Field(default=20_000, ge=1, le=MAX_READ_CHARS)


def list_project_files_tool(
    root: str | None = None,
    glob: str | None = None,
    limit: int = 100,
    *,
    resolver: ProjectRootResolver | None = None,
    prefer_rg: bool = True,
) -> dict[str, Any]:
    resolved_root, error = (resolver or ProjectRootResolver()).resolve_root(root)
    if error is not None or resolved_root is None:
        return error

    files, used_rg = _list_with_rg(resolved_root.path, glob, limit) if prefer_rg else (None, False)
    if files is None:
        used_rg = False
        files = [relative.as_posix() for _, relative in iter_project_files(resolved_root, glob)]

    files = sorted(files)
    truncated = len(files) > limit
    selected = files[:limit]
    return tool_success(
        code="files_listed",
        message="Project files listed",
        data={"files": selected},
        metadata={
            **resolved_root.metadata(),
            "count": len(selected),
            "omitted_count": max(len(files) - len(selected), 0),
            "used_rg": used_rg,
            "glob": glob,
        },
        truncated=truncated,
    )


def search_project_files_tool(
    query: str,
    root: str | None = None,
    glob: str | None = None,
    limit: int = 50,
    *,
    resolver: ProjectRootResolver | None = None,
    prefer_rg: bool = True,
) -> dict[str, Any]:
    if not query.strip():
        return tool_error(code="validation_error", message="query must not be empty")

    resolved_root, error = (resolver or ProjectRootResolver()).resolve_root(root)
    if error is not None or resolved_root is None:
        return error

    matches, used_rg = _search_with_rg(resolved_root.path, query, glob, limit) if prefer_rg else (None, False)
    if matches is None:
        used_rg = False
        matches = _search_with_python(resolved_root, query, glob)

    truncated = len(matches) > limit
    selected = matches[:limit]
    return tool_success(
        code="files_searched",
        message="Project files searched",
        data={"matches": selected},
        metadata={
            **resolved_root.metadata(),
            "count": len(selected),
            "omitted_count": max(len(matches) - len(selected), 0),
            "used_rg": used_rg,
            "glob": glob,
            "query": query,
        },
        truncated=truncated,
    )


def read_project_file_tool(
    path: str,
    root: str | None = None,
    offset: int = 0,
    limit: int = 20_000,
    *,
    resolver: ProjectRootResolver | None = None,
) -> dict[str, Any]:
    resolved_root, resolved, relative, error = (resolver or ProjectRootResolver()).resolve_child(path, root)
    if error is not None or resolved_root is None or resolved is None or relative is None:
        return error

    patterns = load_gitignore_patterns(resolved_root.path)
    if is_ignored_path(relative, patterns):
        return tool_error(
            code="path_ignored",
            message="Path is ignored by local file policy",
            metadata={"path": relative.as_posix(), **resolved_root.metadata()},
        )
    if not resolved.is_file():
        return tool_error(
            code="not_file",
            message="Path is not a file",
            metadata={"path": relative.as_posix(), **resolved_root.metadata()},
        )
    if resolved.stat().st_size > MAX_FILE_BYTES:
        return tool_error(
            code="file_too_large",
            message="File is too large to read in Stage 02",
            metadata=file_metadata(resolved_root, resolved, relative),
        )
    if is_binary_file(resolved):
        return tool_error(
            code="binary_file",
            message="Binary files are not returned as project context",
            metadata=file_metadata(resolved_root, resolved, relative),
        )

    text = resolved.read_text(encoding="utf-8", errors="replace")
    start = min(offset, len(text))
    end = min(start + limit, len(text))
    content = text[start:end]
    truncated = end < len(text)
    start_line = text.count("\n", 0, start) + 1
    end_line = text.count("\n", 0, end) + 1
    return tool_success(
        code="file_read",
        message="Project file read",
        data={"content": content},
        metadata={
            **file_metadata(resolved_root, resolved, relative),
            "start_byte": start,
            "end_byte": end,
            "start_line": start_line,
            "end_line": end_line,
        },
        truncated=truncated,
    )


def _list_with_rg(root: Path, glob: str | None, limit: int) -> tuple[list[str] | None, bool]:
    if shutil.which("rg") is None:
        return None, False
    command = ["rg", "--files"]
    if glob:
        command.extend(["-g", glob])
    try:
        result = subprocess.run(
            command,
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None, False
    if result.returncode not in {0, 1}:
        return None, False
    patterns = load_gitignore_patterns(root)
    files = []
    for line in result.stdout.splitlines():
        relative = Path(line)
        if is_ignored_path(relative, patterns) or not matches_glob(relative, glob):
            continue
        files.append(relative.as_posix())
        if len(files) > limit:
            break
    return files, True


def _search_with_rg(root: Path, query: str, glob: str | None, limit: int) -> tuple[list[dict] | None, bool]:
    if shutil.which("rg") is None:
        return None, False
    command = ["rg", "--line-number", "--no-heading", "--color", "never"]
    if glob:
        command.extend(["-g", glob])
    command.append(query)
    try:
        result = subprocess.run(
            command,
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None, False
    if result.returncode not in {0, 1}:
        return None, False

    patterns = load_gitignore_patterns(root)
    matches = []
    for line in result.stdout.splitlines():
        path_text, line_text, preview = _split_rg_line(line)
        if path_text is None or line_text is None:
            continue
        relative = Path(path_text)
        if is_ignored_path(relative, patterns) or not matches_glob(relative, glob):
            continue
        matches.append(
            {
                "path": relative.as_posix(),
                "line": int(line_text),
                "preview": preview[:MAX_PREVIEW_CHARS],
            }
        )
        if len(matches) > limit:
            break
    return matches, True


def _split_rg_line(line: str) -> tuple[str | None, str | None, str]:
    first = line.split(":", 2)
    if len(first) != 3:
        return None, None, line
    return first[0], first[1], first[2]


def _search_with_python(resolved_root, query: str, glob: str | None) -> list[dict]:
    matches = []
    needle = query.lower()
    for path, relative in iter_project_files(resolved_root, glob):
        if path.stat().st_size > MAX_FILE_BYTES or is_binary_file(path):
            continue
        for line_number, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
            if needle in line.lower():
                matches.append(
                    {
                        "path": relative.as_posix(),
                        "line": line_number,
                        "preview": line[:MAX_PREVIEW_CHARS],
                    }
                )
    return matches
