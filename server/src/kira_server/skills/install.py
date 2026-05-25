from __future__ import annotations

import shutil
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from kira_server.skills.packages import PackageSource, parse_skill_package
from kira_server.tooling.policy import ProjectRootResolver, ResolvedRoot
from kira_server.tooling.results import tool_error


@dataclass(frozen=True)
class SkillInstallResult:
    ok: bool
    code: str
    message: str
    status: str
    project_root: str | None = None
    skill_id: str | None = None
    destination: str | None = None
    skipped_entries: list[str] | None = None
    diagnostics: list[dict[str, Any]] | None = None
    skill: dict[str, Any] | None = None

    def model_dump(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "code": self.code,
            "message": self.message,
            "status": self.status,
            "project_root": self.project_root,
            "skill_id": self.skill_id,
            "destination": self.destination,
            "skipped_entries": self.skipped_entries or [],
            "diagnostics": self.diagnostics or [],
            "skill": self.skill,
        }


def install_skill_zip(
    *,
    project_root: str,
    zip_path: str,
    resolver: ProjectRootResolver | None = None,
) -> SkillInstallResult:
    resolver = resolver or ProjectRootResolver()
    resolved_root, error = resolver.resolve_root(project_root)
    if error is not None or resolved_root is None:
        return _from_tool_error(error)

    archive = Path(zip_path).expanduser()
    if not archive.is_file() or archive.suffix.lower() != ".zip":
        return SkillInstallResult(
            ok=False,
            code="zip_not_found",
            message="Skill zip was not found or is not a .zip file",
            status="error",
            project_root=str(resolved_root.path),
            diagnostics=[{"code": "zip_not_found", "message": str(archive)}],
        )

    install_root = resolved_root.path / ".kira" / "skills"
    tmp_root = install_root / f".installing-{archive.stem}"
    skipped: list[str] = []

    try:
        with zipfile.ZipFile(archive) as zf:
            safe_entries = []
            top_levels: set[str] = set()
            for info in zf.infolist():
                name = info.filename
                safe, reason = _safe_zip_member(name)
                if not safe:
                    skipped.append(name)
                    if reason == "unsafe_path":
                        return SkillInstallResult(
                            ok=False,
                            code="unsafe_zip_path",
                            message="Skill zip contains an unsafe path",
                            status="error",
                            project_root=str(resolved_root.path),
                            skipped_entries=skipped,
                            diagnostics=[{"code": "unsafe_zip_path", "message": name}],
                        )
                    continue
                if info.is_dir():
                    continue
                parts = PurePosixPath(name).parts
                if parts:
                    top_levels.add(parts[0])
                safe_entries.append(info)

            if not safe_entries:
                return SkillInstallResult(
                    ok=False,
                    code="empty_skill_zip",
                    message="Skill zip does not contain installable files",
                    status="error",
                    project_root=str(resolved_root.path),
                    skipped_entries=skipped,
                )
            if len(top_levels) == 1:
                source_subdir = next(iter(top_levels))
            elif "SKILL.md" in {PurePosixPath(info.filename).name for info in safe_entries}:
                source_subdir = ""
            else:
                return SkillInstallResult(
                    ok=False,
                    code="ambiguous_skill_zip",
                    message="Skill zip must contain one top-level skill package",
                    status="error",
                    project_root=str(resolved_root.path),
                    skipped_entries=skipped,
                    diagnostics=[{"code": "top_level_count", "message": str(sorted(top_levels))}],
                )

            install_root.mkdir(parents=True, exist_ok=True)
            if tmp_root.exists():
                shutil.rmtree(tmp_root)
            tmp_root.mkdir(parents=True)
            for info in safe_entries:
                target = (tmp_root / PurePosixPath(info.filename).as_posix()).resolve()
                target.relative_to(tmp_root.resolve())
                target.parent.mkdir(parents=True, exist_ok=True)
                with zf.open(info) as src, target.open("wb") as dst:
                    shutil.copyfileobj(src, dst)
    except zipfile.BadZipFile:
        return SkillInstallResult(
            ok=False,
            code="invalid_zip",
            message="Skill zip could not be read",
            status="error",
            project_root=str(resolved_root.path),
        )

    source_dir = tmp_root / source_subdir if source_subdir else tmp_root
    source = PackageSource(key="project", priority=20, path=str(install_root))
    parsed = parse_skill_package(source_dir, source, include_body=False)
    diagnostics = [item.model_dump() for item in parsed.diagnostics]
    if not parsed.valid:
        shutil.rmtree(tmp_root, ignore_errors=True)
        return SkillInstallResult(
            ok=False,
            code="invalid_skill_package",
            message="Installed zip did not contain a valid skill package",
            status="error",
            project_root=str(resolved_root.path),
            skipped_entries=skipped,
            diagnostics=diagnostics,
        )

    destination = install_root / parsed.skill_id
    status = "updated" if destination.exists() else "installed"
    if destination.exists():
        shutil.rmtree(destination)
    source_dir.rename(destination)
    shutil.rmtree(tmp_root, ignore_errors=True)

    final = parse_skill_package(destination, source, include_body=False)
    return SkillInstallResult(
        ok=True,
        code="skill_installed",
        message=f"Skill '{final.skill_id}' {status}",
        status=status,
        project_root=str(resolved_root.path),
        skill_id=final.skill_id,
        destination=str(destination),
        skipped_entries=skipped,
        diagnostics=[item.model_dump() for item in final.diagnostics],
        skill=final.public_metadata(include_body=False),
    )


def _safe_zip_member(name: str) -> tuple[bool, str | None]:
    path = PurePosixPath(name)
    parts = path.parts
    if not parts or path.is_absolute() or any(part == ".." for part in parts):
        return False, "unsafe_path"
    if any(part == "__MACOSX" for part in parts):
        return False, "metadata"
    if any(part == "__pycache__" for part in parts) or path.suffix == ".pyc":
        return False, "metadata"
    if any(part.startswith("._") for part in parts):
        return False, "metadata"
    return True, None


def _from_tool_error(error: dict | None) -> SkillInstallResult:
    error = error or {}
    return SkillInstallResult(
        ok=False,
        code=str(error.get("code") or "project_root_error"),
        message=str(error.get("message") or "Project root could not be resolved"),
        status="error",
        diagnostics=[error],
    )
