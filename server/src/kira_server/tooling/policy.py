from __future__ import annotations

import fnmatch
import hashlib
import os
from dataclasses import dataclass
from pathlib import Path

from kira_server.tooling.results import tool_error

DEFAULT_IGNORED_NAMES = {
    ".cache",
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    ".vite",
    ".idea",
    ".vscode",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
}
MAX_FILE_BYTES = 1_000_000
MAX_READ_CHARS = 50_000
MAX_PREVIEW_CHARS = 300


@dataclass(frozen=True)
class ResolvedRoot:
    path: Path
    root_id: str

    def metadata(self) -> dict[str, str]:
        return {"root_id": self.root_id, "root": str(self.path)}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


class ProjectRootResolver:
    def __init__(self, default_root: Path | None = None) -> None:
        self.default_root = (default_root or repo_root()).resolve()

    def resolve_root(self, root: str | None = None) -> tuple[ResolvedRoot | None, dict | None]:
        raw = Path(root).expanduser() if root else self.default_root
        try:
            resolved = raw.resolve(strict=True)
        except FileNotFoundError:
            return None, tool_error(
                code="root_not_found",
                message="Project root was not found",
                metadata={"root": str(raw)},
            )

        if not resolved.is_dir():
            return None, tool_error(
                code="root_not_directory",
                message="Project root is not a directory",
                metadata={"root": str(resolved)},
            )

        root_id = hashlib.sha256(str(resolved).encode("utf-8")).hexdigest()[:16]
        return ResolvedRoot(path=resolved, root_id=root_id), None

    def resolve_child(
        self,
        path: str,
        root: str | None = None,
    ) -> tuple[ResolvedRoot | None, Path | None, Path | None, dict | None]:
        resolved_root, error = self.resolve_root(root)
        if error is not None or resolved_root is None:
            return None, None, None, error

        raw_path = Path(path).expanduser()
        candidate = raw_path if raw_path.is_absolute() else resolved_root.path / raw_path
        try:
            resolved = candidate.resolve(strict=True)
            relative = resolved.relative_to(resolved_root.path)
        except (FileNotFoundError, ValueError):
            return resolved_root, None, None, tool_error(
                code="path_outside_root",
                message="Path resolves outside the project root or does not exist",
                metadata={"root": str(resolved_root.path), "path": path},
            )

        return resolved_root, resolved, relative, None


def load_gitignore_patterns(root: Path) -> list[str]:
    gitignore = root / ".gitignore"
    if not gitignore.is_file():
        return []

    patterns: list[str] = []
    for line in gitignore.read_text(encoding="utf-8", errors="ignore").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("!"):
            continue
        patterns.append(stripped.rstrip("/"))
    return patterns


def is_ignored_path(relative: Path, patterns: list[str] | None = None) -> bool:
    parts = relative.parts
    for index, part in enumerate(parts):
        if part in DEFAULT_IGNORED_NAMES:
            return True
        if index < len(parts) - 1 and part.startswith("."):
            return True

    name = relative.name
    if name.startswith(".") and name not in {".gitignore"}:
        return True

    rel = relative.as_posix()
    for pattern in patterns or []:
        if fnmatch.fnmatch(rel, pattern) or fnmatch.fnmatch(name, pattern):
            return True
        if rel.startswith(pattern.rstrip("/") + "/"):
            return True
    return False


def matches_glob(relative: Path, pattern: str | None) -> bool:
    if not pattern:
        return True
    rel = relative.as_posix()
    return fnmatch.fnmatch(rel, pattern) or fnmatch.fnmatch(relative.name, pattern)


def is_binary_file(path: Path) -> bool:
    sample = path.read_bytes()[:4096]
    if b"\x00" in sample:
        return True
    try:
        sample.decode("utf-8")
    except UnicodeDecodeError:
        return True
    return False


def content_hash(path: Path, max_bytes: int = MAX_FILE_BYTES) -> str | None:
    if path.stat().st_size > max_bytes:
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def file_metadata(root: ResolvedRoot, path: Path, relative: Path) -> dict:
    stat = path.stat()
    return {
        **root.metadata(),
        "path": relative.as_posix(),
        "size": stat.st_size,
        "mtime": stat.st_mtime,
        "content_hash": content_hash(path),
    }


def iter_project_files(root: ResolvedRoot, glob: str | None = None):
    patterns = load_gitignore_patterns(root.path)
    for current_root, dirs, files in os.walk(root.path):
        current = Path(current_root)
        kept_dirs = []
        for dirname in dirs:
            rel_dir = (current / dirname).relative_to(root.path)
            if not is_ignored_path(rel_dir, patterns):
                kept_dirs.append(dirname)
        dirs[:] = kept_dirs

        for filename in files:
            path = current / filename
            relative = path.relative_to(root.path)
            if is_ignored_path(relative, patterns) or not matches_glob(relative, glob):
                continue
            yield path, relative
