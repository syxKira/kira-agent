from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from kira_server.context import ContextItem, estimate_budget_cost, make_context_id
from kira_server.graph_runtime.specs import WorkflowSpec
from kira_server.skills.packages import ParsedSkillPackage, SkillPackageLoader, default_skill_roots


class WorkflowSkillMetadata(BaseModel):
    skill_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: str = ""
    when_to_use: str | None = None
    workflows: list[dict[str, Any]] = Field(default_factory=list)
    allowed_tools: list[str] = Field(default_factory=list)
    model_hint: Any | None = None
    internal: bool = False


class SkillDefinition(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    skill_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: str = ""
    workflows: list[WorkflowSpec] = Field(default_factory=list)
    model_hint: str | None = None
    internal: bool = False
    package: ParsedSkillPackage | None = Field(default=None, exclude=True)

    @property
    def workflow_capable(self) -> bool:
        return bool(self.workflows)

    def public_metadata(self) -> dict[str, Any]:
        if self.package is not None:
            return self.package.public_metadata(include_body=self.package.body_loaded)
        tools = sorted({tool for workflow in self.workflows for tool in workflow.tools})
        return WorkflowSkillMetadata(
            skill_id=self.skill_id,
            name=self.name,
            description=self.description,
            workflows=[workflow.public_metadata() for workflow in self.workflows],
            allowed_tools=tools,
            model_hint=self.model_hint,
            internal=self.internal,
        ).model_dump(exclude_none=True)


class SkillRegistry:
    def __init__(self, skills: list[SkillDefinition] | None = None, packages: list[ParsedSkillPackage] | None = None) -> None:
        self._skills: dict[str, SkillDefinition] = {}
        self._catalog: dict[str, SkillDefinition] = {}
        self._all_packages: list[ParsedSkillPackage] = []
        for skill in skills or []:
            self.register(skill)
        for package in packages or []:
            self.register_package(package)

    def register(self, skill: SkillDefinition) -> None:
        if skill.workflow_capable:
            self._skills[skill.skill_id] = skill
            self._catalog[skill.skill_id] = skill

    def register_package(self, package: ParsedSkillPackage) -> None:
        self._all_packages.append(package)
        definition = SkillDefinition(
            skill_id=package.skill_id,
            name=package.name,
            description=package.description,
            workflows=package.workflows,
            model_hint=package.model_hint_model,
            package=package,
        )
        catalog_key = f"{package.skill_id}:{package.source.key}:{package.path}"
        self._catalog[catalog_key] = definition
        if package.active and package.valid:
            self._catalog[package.skill_id] = definition
            if package.workflows:
                self._skills[package.skill_id] = definition

    def get(self, skill_id: str | None) -> SkillDefinition | None:
        if not skill_id:
            return None
        return self._skills.get(skill_id)

    def get_catalog(self, skill_id: str | None, *, include_body: bool = False) -> SkillDefinition | None:
        if not skill_id:
            return None
        current = self._catalog.get(skill_id)
        if current is None:
            return None
        if include_body and current.package is not None:
            loader = SkillPackageLoader([current.package.source])
            package = loader.get(current.package.skill_id, include_body=True)
            if package is not None:
                return SkillDefinition(
                    skill_id=package.skill_id,
                    name=package.name,
                    description=package.description,
                    workflows=package.workflows,
                    model_hint=package.model_hint_model,
                    package=package,
                )
        return current

    def route_for_prompt(self, prompt: str) -> SkillDefinition | None:
        candidates = [
            skill
            for skill in _dedupe_catalog(self._catalog.values())
            if _is_active_valid_catalog_skill(skill) and _is_model_invocable(skill)
        ]
        scored = [
            (score, skill)
            for skill in candidates
            if (score := _route_score(prompt, skill)) > 0
        ]
        if not scored:
            return None
        scored.sort(key=lambda item: (-item[0], item[1].skill_id))
        best_score, best = scored[0]
        if best_score < 3:
            return None
        if len(scored) > 1 and scored[1][0] == best_score:
            return None
        return best

    def metadata(self, *, include_internal: bool = True) -> dict[str, Any]:
        values = _dedupe_catalog(self._catalog.values())
        return {
            "skills": [
                skill.public_metadata()
                for skill in sorted(values, key=lambda item: item.skill_id)
                if include_internal or not skill.internal
            ]
        }

    @property
    def skill_ids(self) -> list[str]:
        return sorted(self._skills)

    def catalog_context_items(self, *, include_internal: bool = False) -> list[ContextItem]:
        skills = [
            skill
            for skill in _dedupe_catalog(self._catalog.values())
            if _is_active_valid_catalog_skill(skill) and (include_internal or not skill.internal)
        ]
        if not skills:
            return []
        text = "\n".join(_catalog_line(skill) for skill in sorted(skills, key=lambda item: item.skill_id))
        header = (
            "Available Kira skills. Use these summaries to decide whether a user request matches a skill. "
            "If a skill is relevant but not explicitly activated, mention the skill id and ask the user to activate it with slash selection."
        )
        summary = f"{header}\n{text}"
        return [
            ContextItem(
                id=make_context_id("skill_summary", summary),
                kind="skill_summary",
                text=summary,
                metadata={"source": "skill_catalog"},
                trust="trusted_skill",
                budget_cost=estimate_budget_cost(summary),
            )
        ]


def create_package_skill_registry(*, include_builtins: bool = True, project_root: str | None = None) -> SkillRegistry:
    from kira_server.skills.builtin import create_builtin_skill_registry

    registry = create_builtin_skill_registry(include_test_skill=include_builtins, discover_packages=False)
    for package in SkillPackageLoader(default_skill_roots(project_root)).discover(include_body=False):
        registry.register_package(package)
    return registry


def _dedupe_catalog(values) -> list[SkillDefinition]:
    seen: set[int] = set()
    result: list[SkillDefinition] = []
    for value in values:
        marker = id(value)
        if marker not in seen:
            seen.add(marker)
            result.append(value)
    return result


def _is_active_valid_catalog_skill(skill: SkillDefinition) -> bool:
    package = skill.package
    if package is not None:
        return package.active and package.valid
    return skill.workflow_capable


def _is_model_invocable(skill: SkillDefinition) -> bool:
    package = skill.package
    if package is None or package.frontmatter is None:
        return True
    if package.frontmatter.disable_model_invocation:
        return False
    return package.frontmatter.model_invocable


def _catalog_line(skill: SkillDefinition) -> str:
    package = skill.package
    when_to_use = package.frontmatter.when_to_use if package and package.frontmatter else None
    tools = sorted({tool for workflow in skill.workflows for tool in workflow.tools})
    details = [
        f"id={skill.skill_id}",
        f"name={skill.name}",
        f"description={skill.description or 'No description'}",
    ]
    if when_to_use:
        details.append(f"when_to_use={when_to_use}")
    if tools:
        details.append(f"tools={', '.join(tools)}")
    return "- " + "; ".join(details)


def _route_score(prompt: str, skill: SkillDefinition) -> int:
    prompt_norm = _normalize(prompt)
    if not prompt_norm:
        return 0
    package = skill.package
    fields = [
        skill.skill_id,
        skill.name,
        skill.description,
        package.frontmatter.when_to_use if package and package.frontmatter else "",
    ]
    haystack = " ".join(field or "" for field in fields)
    haystack_norm = _normalize(haystack)
    score = 0
    skill_id_norm = _normalize(skill.skill_id)
    if skill_id_norm and skill_id_norm in prompt_norm:
        score += 5
    for token in _tokens(haystack):
        if token in prompt_norm:
            score += 1
    prompt_bigrams = _cjk_bigrams(prompt)
    if prompt_bigrams:
        score += min(4, len(prompt_bigrams & _cjk_bigrams(haystack)))
    if ("造" in prompt or "构造" in prompt or "生成" in prompt) and "构造" in haystack:
        score += 3
    if ("发送" in prompt or "发" in prompt) and ("发送" in haystack or "send" in haystack_norm):
        score += 2
    return score


def _normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9#\u4e00-\u9fff]+", "", value.lower())


def _tokens(value: str) -> set[str]:
    tokens: set[str] = set()
    for raw in re.findall(r"[A-Za-z0-9_#-]{3,}", value.lower()):
        normalized = _normalize(raw)
        if normalized:
            tokens.add(normalized)
    return tokens


def _cjk_bigrams(value: str) -> set[str]:
    chars = re.findall(r"[\u4e00-\u9fff]", value)
    return {"".join(chars[index : index + 2]) for index in range(max(0, len(chars) - 1))}
