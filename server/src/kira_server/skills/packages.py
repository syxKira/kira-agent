from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from kira_server.context import ContextItem, estimate_budget_cost, make_context_id
from kira_server.graph_runtime.specs import END_NODE, NodeMetadata, WorkflowEdgeSpec, WorkflowNodeSpec, WorkflowSpec
from kira_server.providers.config import redact_text
from kira_server.tooling.policy import ProjectRootResolver, repo_root


SKILL_PATHS_ENV = "KIRA_SKILL_PATHS"
SECRET_FIELD_RE = re.compile(r"(api[_-]?key|authorization|bearer|secret|base[_-]?url|baseURL)", re.IGNORECASE)
SECTION_HEADING_RE = re.compile(r"(?m)^(#{2,4})\s+(.+)$")
ALWAYS_INCLUDE_SECTION_HEADINGS = (
    "快速开始",
    "核心概念",
    "精准匹配字段",
    "构造约束",
    "输出格式",
    "输出前自检",
    "数据发送顺序",
    "失败处理",
)
MAX_SELECTED_SKILL_SECTIONS = 10


class SkillFrontmatter(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str | None = None
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    when_to_use: str | None = None
    argument_hint: str | None = Field(default=None, alias="argument-hint")
    disable_model_invocation: bool = Field(default=False, alias="disable-model-invocation")
    user_invocable: bool = Field(default=True, alias="user-invocable")
    model_invocable: bool = Field(default=True, alias="model-invocable")


class SkillModelHint(BaseModel):
    profile: str | None = None
    model: str | None = None


class SkillWorkflowManifest(BaseModel):
    name: str = Field(min_length=1)
    description: str = ""
    entrypoint: str = "model_step"
    tools: list[str] = Field(default_factory=list)


class SkillManifest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    workflows: list[SkillWorkflowManifest] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)
    permissions: dict[str, Any] = Field(default_factory=dict)
    context: list[str] = Field(default_factory=list)
    references: list[str] = Field(default_factory=list)
    fixtures: list[dict[str, Any]] = Field(default_factory=list)
    ui: dict[str, Any] = Field(default_factory=dict)
    model_hint: SkillModelHint | str | None = None


class SkillDiagnostic(BaseModel):
    code: str
    message: str
    severity: str = "error"
    metadata: dict[str, Any] = Field(default_factory=dict)


class PackageSource(BaseModel):
    key: str
    priority: int
    path: str


@dataclass(frozen=True)
class ParsedSkillPackage:
    skill_id: str
    path: Path
    source: PackageSource
    frontmatter: SkillFrontmatter | None
    body_loaded: bool
    body: str | None
    manifest: SkillManifest | None
    workflows: list[WorkflowSpec]
    diagnostics: list[SkillDiagnostic]
    active: bool = True
    shadowed_by: str | None = None

    @property
    def valid(self) -> bool:
        return self.frontmatter is not None and not any(item.severity == "error" for item in self.diagnostics)

    @property
    def name(self) -> str:
        return self.frontmatter.name if self.frontmatter else self.path.name

    @property
    def description(self) -> str:
        return self.frontmatter.description if self.frontmatter else ""

    @property
    def model_hint_profile(self) -> str | None:
        hint = self.manifest.model_hint if self.manifest else None
        if isinstance(hint, SkillModelHint):
            return hint.profile
        if isinstance(hint, str):
            return hint
        return None

    @property
    def model_hint_model(self) -> str | None:
        hint = self.manifest.model_hint if self.manifest else None
        return hint.model if isinstance(hint, SkillModelHint) else None

    def public_metadata(self, *, include_body: bool = False) -> dict[str, Any]:
        manifest = self.manifest
        invocation = {
            "argument_hint": self.frontmatter.argument_hint if self.frontmatter else None,
            "disable_model_invocation": self.frontmatter.disable_model_invocation if self.frontmatter else False,
            "user_invocable": self.frontmatter.user_invocable if self.frontmatter else True,
            "model_invocable": (
                False
                if self.frontmatter and self.frontmatter.disable_model_invocation
                else (self.frontmatter.model_invocable if self.frontmatter else True)
            ),
        }
        payload: dict[str, Any] = {
            "skill_id": self.skill_id,
            "name": self.name,
            "description": self.description,
            "when_to_use": self.frontmatter.when_to_use if self.frontmatter else None,
            "invocation": invocation,
            "source": self.source.model_dump(),
            "valid": self.valid,
            "active": self.active,
            "shadowed_by": self.shadowed_by,
            "body_loaded": include_body and self.body is not None,
            "workflows": [workflow.public_metadata() for workflow in self.workflows],
            "allowed_tools": sorted({tool for workflow in self.workflows for tool in workflow.tools}),
            "permissions": manifest.permissions if manifest else {},
            "fixtures": manifest.fixtures if manifest else [],
            "references": manifest.references if manifest else [],
            "context": manifest.context if manifest else [],
            "ui": manifest.ui if manifest else {},
            "model_hint": {"profile": self.model_hint_profile, "model": self.model_hint_model} if (self.model_hint_profile or self.model_hint_model) else None,
            "diagnostics": [diagnostic.model_dump() for diagnostic in self.diagnostics],
        }
        if include_body:
            payload["body"] = self.body
        return _redact(payload)


def default_skill_roots(project_root: str | None = None) -> list[PackageSource]:
    roots = [
        PackageSource(key="bundled", priority=10, path=str(repo_root() / "skills")),
        PackageSource(key="user", priority=30, path=str(Path.home() / ".kira-agent" / "skills")),
    ]
    if project_root:
        resolved, error = ProjectRootResolver().resolve_root(project_root)
        if error is None and resolved is not None:
            roots.append(PackageSource(key="project", priority=20, path=str(resolved.path / ".kira" / "skills")))
    for index, raw in enumerate(os.environ.get(SKILL_PATHS_ENV, "").split(os.pathsep)):
        if raw.strip():
            roots.append(PackageSource(key=f"env-{index}", priority=40 + index, path=str(Path(raw).expanduser())))
    return roots


class SkillPackageLoader:
    def __init__(self, roots: list[PackageSource] | None = None) -> None:
        self.roots = roots or default_skill_roots()

    def discover(self, *, include_body: bool = False) -> list[ParsedSkillPackage]:
        packages: list[ParsedSkillPackage] = []
        for source in self.roots:
            root = Path(source.path).expanduser()
            if not root.is_dir():
                continue
            for candidate in sorted(path for path in root.iterdir() if path.is_dir()):
                packages.append(parse_skill_package(candidate, source, include_body=include_body))
        return resolve_duplicates(packages)

    def get(self, skill_id: str, *, include_body: bool = False) -> ParsedSkillPackage | None:
        for package in self.discover(include_body=include_body):
            if package.skill_id == skill_id and package.active:
                return package
        return None


def parse_skill_package(path: Path, source: PackageSource, *, include_body: bool = False) -> ParsedSkillPackage:
    diagnostics: list[SkillDiagnostic] = []
    skill_md = path / "SKILL.md"
    frontmatter: SkillFrontmatter | None = None
    body: str | None = None
    if not skill_md.is_file():
        diagnostics.append(SkillDiagnostic(code="missing_skill_md", message="Skill package is missing SKILL.md"))
        skill_id = path.name
    else:
        try:
            frontmatter_raw, body_raw = parse_skill_markdown(skill_md.read_text(encoding="utf-8", errors="replace"))
            frontmatter = SkillFrontmatter.model_validate(frontmatter_raw)
            skill_id = frontmatter.id or _slug(frontmatter.name)
            if include_body:
                body = body_raw
        except (ValueError, ValidationError, yaml.YAMLError) as exc:
            diagnostics.append(SkillDiagnostic(code="invalid_skill_frontmatter", message=redact_text(str(exc))))
            skill_id = path.name

    manifest = None
    manifest_path = path / "skill.yaml"
    if manifest_path.is_file():
        try:
            loaded = yaml.safe_load(manifest_path.read_text(encoding="utf-8", errors="replace")) or {}
            _reject_secret_like_keys(loaded)
            manifest = SkillManifest.model_validate(loaded)
            diagnostics.extend(_validate_manifest(manifest, path))
        except (ValueError, ValidationError, yaml.YAMLError) as exc:
            diagnostics.append(SkillDiagnostic(code="invalid_skill_manifest", message=redact_text(str(exc))))
    workflows = [_workflow_from_manifest(item) for item in (manifest.workflows if manifest else [])]
    return ParsedSkillPackage(skill_id, path, source, frontmatter, include_body, body, manifest, workflows, diagnostics)


def parse_skill_markdown(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---\n"):
        raise ValueError("SKILL.md frontmatter is required")
    parts = text.split("---\n", 2)
    if len(parts) < 3:
        raise ValueError("SKILL.md frontmatter is not closed")
    frontmatter = yaml.safe_load(parts[1]) or {}
    _reject_secret_like_keys(frontmatter)
    return frontmatter, parts[2].lstrip()


def resolve_duplicates(packages: list[ParsedSkillPackage]) -> list[ParsedSkillPackage]:
    by_id: dict[str, list[ParsedSkillPackage]] = {}
    for package in packages:
        by_id.setdefault(package.skill_id, []).append(package)

    resolved: list[ParsedSkillPackage] = []
    for skill_id, group in by_id.items():
        valid = [package for package in group if package.valid]
        winner = max(valid, key=lambda package: (package.source.priority, str(package.path))) if valid else None
        for package in group:
            if winner is not None and package is not winner:
                diagnostics = [
                    *package.diagnostics,
                    SkillDiagnostic(code="skill_shadowed", message=f"Skill '{skill_id}' is shadowed by {winner.source.key}", severity="warning"),
                ]
                resolved.append(_replace_package(package, active=False, shadowed_by=str(winner.path), diagnostics=diagnostics))
            elif winner is None:
                resolved.append(_replace_package(package, active=False))
            else:
                resolved.append(package)
    return sorted(resolved, key=lambda package: (package.skill_id, -package.source.priority, str(package.path)))


def skill_context_items(package: ParsedSkillPackage, *, query: str | None = None) -> list[ContextItem]:
    items: list[ContextItem] = []
    body = _rewrite_installed_skill_paths(package.body or "", package)
    body, selection_metadata = _select_skill_sections(body, query)
    if body:
        relative_path = package.path.as_posix()
        header = (
            f"Skill id: {package.skill_id}\n"
            f"Installed path: {relative_path}\n"
            "When invoking bundled scripts from the project root, use the actual installed path above.\n\n"
        )
        for index, chunk in enumerate(_chunk_text(header + body, max_chars=6_000)):
            items.append(
                ContextItem(
                    id=make_context_id("skill_doc", package.skill_id, index, chunk),
                    kind="skill_doc",
                    text=chunk,
                    metadata={
                        "source": str(package.path / "SKILL.md"),
                        "skill_id": package.skill_id,
                        "chunk_index": index,
                        **selection_metadata,
                    },
                    trust="trusted_skill",
                    budget_cost=estimate_budget_cost(chunk),
                )
            )
    if package.manifest and package.manifest.permissions:
        text = yaml.safe_dump(package.manifest.permissions, sort_keys=True)
        items.append(
            ContextItem(
                id=make_context_id("skill_perm", package.skill_id, text),
                kind="permission",
                text=text,
                metadata={"source": str(package.path / "skill.yaml"), "skill_id": package.skill_id},
                trust="trusted_skill",
                budget_cost=estimate_budget_cost(text),
            )
        )
    return items


def _rewrite_installed_skill_paths(body: str, package: ParsedSkillPackage) -> str:
    """Normalize imported skill script examples to this package's actual path."""

    installed_path = package.path.as_posix()
    pattern = re.compile(rf"(?:\.cursor|\.codex|\.kira)/skills/{re.escape(package.skill_id)}")
    return pattern.sub(installed_path, body)


def _select_skill_sections(body: str, query: str | None) -> tuple[str, dict[str, Any]]:
    query = (query or "").strip()
    if not body or not query:
        return body, {"selection": {"mode": "full"}}

    sections = _markdown_sections(body)
    if len(sections) <= 1:
        return body, {"selection": {"mode": "full"}}

    always_indexes: set[int] = set()
    scored: list[tuple[float, int]] = []
    for index, section in enumerate(sections):
        heading = section["heading"]
        if index == 0 or any(token in heading for token in ALWAYS_INCLUDE_SECTION_HEADINGS):
            always_indexes.add(index)
            continue
        score = _section_score(section["text"], query)
        if score > 0:
            scored.append((score, index))

    if not scored:
        return body, {"selection": {"mode": "full", "reason": "no_section_match"}}

    max_score = max(score for score, _ in scored)
    threshold = max(3.0, max_score * 0.6)
    selected_indexes = set(always_indexes)
    for score, index in sorted(scored, key=lambda item: (-item[0], item[1]))[:MAX_SELECTED_SKILL_SECTIONS]:
        if score >= threshold:
            selected_indexes.add(index)

    if len(selected_indexes) == len(sections):
        return body, {"selection": {"mode": "full", "reason": "all_sections_selected"}}

    selected = [sections[index]["text"].strip() for index in sorted(selected_indexes) if sections[index]["text"].strip()]
    headings = [sections[index]["heading"] for index in sorted(selected_indexes)]
    return "\n\n".join(selected), {
        "selection": {
            "mode": "section",
            "query": query[:200],
            "selected_headings": headings,
            "omitted_section_count": len(sections) - len(selected_indexes),
        }
    }


def _markdown_sections(body: str) -> list[dict[str, str]]:
    matches = list(SECTION_HEADING_RE.finditer(body))
    if not matches:
        return [{"heading": "", "text": body}]

    sections: list[dict[str, str]] = []
    if matches[0].start() > 0:
        sections.append({"heading": "", "text": body[: matches[0].start()].strip()})
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
        sections.append({"heading": match.group(2).strip(), "text": body[match.start() : end].strip()})
    return sections


def _section_score(text: str, query: str) -> float:
    normalized_text = _normalize_for_match(text)
    query_terms = _query_terms(query)
    if not query_terms:
        return 0.0
    score = 0.0
    for term in query_terms:
        normalized_term = _normalize_for_match(term)
        if not normalized_term:
            continue
        if normalized_term in normalized_text:
            score += 4.0 if any(char.isascii() and char.isalnum() for char in term) else 2.0
    return score


def _query_terms(query: str) -> list[str]:
    terms: list[str] = []
    for match in re.findall(r"[A-Za-z0-9_][A-Za-z0-9_.:/-]{1,}|[\u4e00-\u9fff]{2,}", query):
        lowered = match.lower()
        if lowered not in terms:
            terms.append(lowered)
        if all("\u4e00" <= char <= "\u9fff" for char in match) and len(match) > 4:
            for width in (4, 3, 2):
                for index in range(0, len(match) - width + 1):
                    part = match[index : index + width].lower()
                    if part not in terms:
                        terms.append(part)
    return terms


def _normalize_for_match(value: str) -> str:
    return re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "", value.lower())


def _chunk_text(text: str, *, max_chars: int) -> list[str]:
    if len(text) <= max_chars:
        return [text]
    chunks: list[str] = []
    remaining = text
    while remaining:
        if len(remaining) <= max_chars:
            chunks.append(remaining)
            break
        split_at = remaining.rfind("\n## ", 0, max_chars)
        if split_at < max_chars // 3:
            split_at = remaining.rfind("\n\n", 0, max_chars)
        if split_at < max_chars // 3:
            split_at = max_chars
        chunks.append(remaining[:split_at].rstrip())
        remaining = remaining[split_at:].lstrip()
    return chunks


def _workflow_from_manifest(item: SkillWorkflowManifest) -> WorkflowSpec:
    tools = item.tools
    nodes = [
        WorkflowNodeSpec(
            id="model_step",
            node_type="model",
            metadata=NodeMetadata(node_type="model", timeout_hint=30, retry_hint=0, side_effect_hint="none", uses_model=True),
        )
    ]
    edges = [WorkflowEdgeSpec(source="model_step", target=END_NODE)]
    return WorkflowSpec(name=item.name, description=item.description, entrypoint="model_step", tools=tools, nodes=nodes, edges=edges)


def _validate_manifest(manifest: SkillManifest, path: Path) -> list[SkillDiagnostic]:
    diagnostics: list[SkillDiagnostic] = []
    for reference in [*manifest.context, *manifest.references]:
        candidate = (path / reference).resolve()
        try:
            candidate.relative_to(path.resolve())
        except ValueError:
            diagnostics.append(SkillDiagnostic(code="path_outside_skill", message=f"Reference '{reference}' escapes the skill package"))
    if manifest.model_hint:
        hint = manifest.model_hint
        if isinstance(hint, SkillModelHint):
            fields = hint.model_dump(exclude_none=True)
        else:
            fields = {"profile": hint}
        if any(SECRET_FIELD_RE.search(key) for key in fields):
            diagnostics.append(SkillDiagnostic(code="invalid_model_hint", message="Model hint contains unsupported secret-like fields"))
    return diagnostics


def _reject_secret_like_keys(value: Any, prefix: str = "") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            text_key = str(key)
            full_key = f"{prefix}.{text_key}" if prefix else text_key
            if SECRET_FIELD_RE.search(text_key):
                raise ValueError(f"Secret-like manifest field is not allowed: {full_key}")
            _reject_secret_like_keys(child, full_key)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_secret_like_keys(child, f"{prefix}[{index}]")


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "skill"


def _replace_package(package: ParsedSkillPackage, **updates: Any) -> ParsedSkillPackage:
    values = {
        "skill_id": package.skill_id,
        "path": package.path,
        "source": package.source,
        "frontmatter": package.frontmatter,
        "body_loaded": package.body_loaded,
        "body": package.body,
        "manifest": package.manifest,
        "workflows": package.workflows,
        "diagnostics": package.diagnostics,
        "active": package.active,
        "shadowed_by": package.shadowed_by,
    }
    values.update(updates)
    return ParsedSkillPackage(**values)


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _redact(child) for key, child in value.items() if not SECRET_FIELD_RE.search(str(key))}
    if isinstance(value, list):
        return [_redact(child) for child in value]
    if isinstance(value, str):
        return redact_text(value)
    return value
