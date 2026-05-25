from __future__ import annotations

import json
from collections.abc import AsyncIterator
from pathlib import Path

from fastapi.testclient import TestClient

from kira_server.core.events import ProviderEvent
from kira_server.main import create_app
from kira_server.project_knowledge import ProjectIndexRefreshRequest, ProjectKnowledgeService, ProjectSearchRequest
from kira_server.providers.base import ProviderRequest
from kira_server.providers.config import ProviderConfig, ProviderConfigStore
from kira_server.skills.packages import PackageSource, SkillPackageLoader
from kira_server.skills.registry import SkillRegistry
from kira_server.storage.database import RuntimeDatabase, RuntimeStorage


class FakeOpenAIProvider:
    def __init__(self) -> None:
        self.requests: list[ProviderRequest] = []

    async def stream(self, request: ProviderRequest) -> AsyncIterator[ProviderEvent]:
        self.requests.append(request)
        yield ProviderEvent(type="text_delta", data={"text": "remote"})
        yield ProviderEvent(type="done", data={"message": "done"})


def config_store() -> ProviderConfigStore:
    return ProviderConfigStore(
        default_provider="default",
        config_path="/tmp/config.yaml",
        loaded=True,
        providers={
            "default": ProviderConfig(name="default", provider="openai", base_url="https://example.test/v1", model="model-a", api_key="sk-secret"),
            "other": ProviderConfig(name="other", provider="openai", base_url="https://other.example/v1", model="model-b", api_key="sk-secret"),
        },
    )


def test_skill_package_summary_detail_duplicate_and_secret_validation(tmp_path: Path) -> None:
    root = tmp_path / "skills"
    low = root / "low"
    high = root / "high"
    secret = root / "secret"
    _write_skill(low, name="Duplicate Skill", description="low priority")
    _write_manifest(low, "model_hint:\n  profile: default\n")
    _write_skill(high, name="Duplicate Skill", description="high priority")
    _write_manifest(high, "workflows:\n  - name: package-flow\n    description: package workflow\nmodel_hint:\n  profile: other\n")
    _write_skill(secret, name="Secret Skill", description="bad secret")
    _write_manifest(secret, "model_hint:\n  profile: default\nbaseURL: https://should-not-pass.test/v1\n")
    loader = SkillPackageLoader(
        [
            PackageSource(key="low", priority=10, path=str(root)),
            PackageSource(key="high", priority=20, path=str(root)),
        ]
    )

    packages = loader.discover()
    duplicate_entries = [package for package in packages if package.skill_id == "duplicate-skill"]
    secret_entry = next(package for package in packages if package.skill_id == "secret-skill")

    assert any(package.active for package in duplicate_entries)
    assert any(not package.active for package in duplicate_entries)
    assert duplicate_entries[0].body is None
    assert secret_entry.valid is False
    assert "should-not-pass" not in json.dumps(secret_entry.public_metadata())

    detail = loader.get("duplicate-skill", include_body=True)
    assert detail is not None
    assert detail.body_loaded is True
    assert "Detailed instructions" in (detail.body or "")


def test_skill_model_hint_context_trace_and_provider_redaction(tmp_path: Path) -> None:
    skill_root = tmp_path / "skills"
    package_dir = skill_root / "package"
    _write_skill(package_dir, name="Package Skill", description="uses other profile")
    _write_manifest(package_dir, "workflows:\n  - name: package-flow\nmodel_hint:\n  profile: other\n")
    packages = SkillPackageLoader([PackageSource(key="fixture", priority=10, path=str(skill_root))]).discover()
    fake = FakeOpenAIProvider()
    storage = _storage(tmp_path)
    client = TestClient(
        create_app(
            fixture_delay_seconds=0,
            provider_config=config_store(),
            openai_provider=fake,
            skill_registry=SkillRegistry(packages=packages),
            runtime_storage=storage,
        )
    )

    run = client.post("/api/runs", json={"prompt": "hello", "skill_id": "package-skill"}).json()
    with client.stream("GET", run["events_url"]) as response:
        payloads = _read_sse_payloads(response.iter_lines())
    trace = client.get(f"/api/runs/{run['thread_id']}/context").json()

    assert run["provider"]["source"] == "skill_model_hint"
    assert run["provider"]["name"] == "other"
    assert "body" not in run["skill"]
    assert fake.requests[0].config is not None
    assert fake.requests[0].config.name == "other"
    assert fake.requests[0].context_items
    assert any(item["kind"] == "skill_doc" for item in trace["included"])
    assert "sk-secret" not in json.dumps(run)
    assert "sk-secret" not in json.dumps(trace)
    assert payloads[-1]["type"] == "done"


def test_skill_catalog_summary_is_injected_for_model_routing(tmp_path: Path) -> None:
    skill_root = tmp_path / "skills"
    package_dir = skill_root / "analysis"
    _write_skill(package_dir, name="Analysis Skill", description="Analyze local datasets")
    packages = SkillPackageLoader([PackageSource(key="fixture", priority=10, path=str(skill_root))]).discover()
    fake = FakeOpenAIProvider()
    client = TestClient(
        create_app(
            fixture_delay_seconds=0,
            provider_config=config_store(),
            openai_provider=fake,
            skill_registry=SkillRegistry(packages=packages),
            runtime_storage=_storage(tmp_path),
        )
    )

    run = client.post("/api/runs", json={"prompt": "which skill should I use?", "auto_route_skills": True}).json()
    with client.stream("GET", run["events_url"]) as response:
        _read_sse_payloads(response.iter_lines())
    trace = client.get(f"/api/runs/{run['thread_id']}/context").json()

    assert fake.requests[0].context_items
    assert fake.requests[0].context_items[0]["kind"] == "skill_summary"
    assert "Analysis Skill" in fake.requests[0].context_items[0]["text"]
    assert trace["included"][0]["kind"] == "skill_summary"
    # The default agent loop also folds context_items into the seeded
    # messages so the provider receives them as a system role.
    messages = fake.requests[0].messages or []
    assert any(
        message.get("role") == "system" and "Analysis Skill" in (message.get("content") or "")
        for message in messages
    )


def test_skill_catalog_summary_is_injected_for_plain_chat_by_default(tmp_path: Path) -> None:
    skill_root = tmp_path / "skills"
    package_dir = skill_root / "analysis"
    _write_skill(package_dir, name="Analysis Skill", description="Analyze local datasets")
    packages = SkillPackageLoader([PackageSource(key="fixture", priority=10, path=str(skill_root))]).discover()
    fake = FakeOpenAIProvider()
    client = TestClient(
        create_app(
            fixture_delay_seconds=0,
            provider_config=config_store(),
            openai_provider=fake,
            skill_registry=SkillRegistry(packages=packages),
            runtime_storage=_storage(tmp_path),
        )
    )

    run = client.post("/api/runs", json={"prompt": "你好"}).json()
    with client.stream("GET", run["events_url"]) as response:
        _read_sse_payloads(response.iter_lines())
    trace = client.get(f"/api/runs/{run['thread_id']}/context").json()

    # Default agent behavior surfaces the skill catalog so the model can
    # suggest activation even without an explicit ``auto_route_skills`` opt-in.
    assert any(item["kind"] == "skill_summary" for item in trace["included"])


def test_project_root_skill_catalog_lists_project_skills(tmp_path: Path) -> None:
    project = tmp_path / "project"
    package_dir = project / ".kira" / "skills" / "project-analysis"
    _write_skill(package_dir, name="Project Analysis", description="Use for this project")
    client = TestClient(
        create_app(
            fixture_delay_seconds=0,
            provider_config=config_store(),
            skill_registry=SkillRegistry(),
            runtime_storage=_storage(tmp_path),
        )
    )

    response = client.get("/api/skills", params={"project_root": str(project)})

    assert response.status_code == 200
    body = response.json()
    assert any(skill["skill_id"] == "project-analysis" for skill in body["skills"])
    assert any(skill["source"]["key"] == "project" for skill in body["skills"] if skill["skill_id"] == "project-analysis")


def test_project_index_search_context_and_stale_flags(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "README.md").write_text("Kira retrieves local project context.\nUse citations for Kira results.\n", encoding="utf-8")
    (project / "large.txt").write_text("x" * 1_100_000, encoding="utf-8")
    (project / "bin.dat").write_bytes(b"\x00\x01binary")
    storage = _storage(tmp_path)
    service = ProjectKnowledgeService(storage)

    refresh = service.refresh(ProjectIndexRefreshRequest(root=str(project), max_files=20))
    search = service.search(ProjectSearchRequest(root=str(project), query="Kira citations", limit=5))
    items, project_trace = service.context_items_for_query("Kira citations", str(project), limit=3, thread_id="thread-1")
    (project / "README.md").write_text("changed after index\n", encoding="utf-8")
    stale_search = service.search(ProjectSearchRequest(root=str(project), query="Kira", limit=5))

    assert refresh["file_count"] == 1
    assert refresh["skipped_count"] == 2
    assert search["results"][0]["citation"]["path"] == "README.md"
    assert search["results"][0]["citation"]["start_line"] >= 1
    assert items[0].trust == "untrusted_project"
    assert project_trace["omitted_count"] >= 0
    assert stale_search["results"][0]["citation"]["stale"] is True


def test_project_apis_and_run_context_are_frontend_safe(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "app.py").write_text("print('project knowledge')\n", encoding="utf-8")
    fake = FakeOpenAIProvider()
    client = TestClient(
        create_app(
            fixture_delay_seconds=0,
            provider_config=config_store(),
            openai_provider=fake,
            skill_registry=SkillRegistry(),
            runtime_storage=_storage(tmp_path),
        )
    )

    refresh = client.post("/api/project/index/refresh", json={"root": str(project)}).json()
    search = client.post("/api/project/search", json={"root": str(project), "query": "project knowledge"}).json()
    run = client.post(
        "/api/runs",
        json={"prompt": "use project context", "project_root": str(project), "project_context_query": "project knowledge"},
    ).json()
    with client.stream("GET", run["events_url"]) as response:
        _read_sse_payloads(response.iter_lines())
    trace = client.get(f"/api/runs/{run['thread_id']}/context").json()

    assert refresh["status"] == "ready"
    assert search["results"][0]["citation"]["path"] == "app.py"
    assert any(item["trust"] == "untrusted_project" for item in trace["included"])
    assert "sk-secret" not in json.dumps(trace)
    # Project context is folded into the agent loop's seeded messages.
    seeded_messages = fake.requests[0].messages or []
    seeded_blob = json.dumps(seeded_messages)
    assert "project knowledge" in fake.requests[0].prompt or "project knowledge" in seeded_blob


def test_run_does_not_inject_project_context_by_default(tmp_path: Path) -> None:
    project = tmp_path / "project"
    docs = project / "docs"
    docs.mkdir(parents=True)
    (docs / "adtracker.md").write_text("adtracker 业务背景：归因窗口是七天。\n", encoding="utf-8")
    fake = FakeOpenAIProvider()
    client = TestClient(
        create_app(
            fixture_delay_seconds=0,
            provider_config=config_store(),
            openai_provider=fake,
            skill_registry=SkillRegistry(),
            runtime_storage=_storage(tmp_path),
        )
    )

    run = client.post(
        "/api/runs",
        json={"prompt": "帮我根据adtracker业务背景生成一条数据", "project_root": str(project)},
    ).json()
    with client.stream("GET", run["events_url"]) as response:
        _read_sse_payloads(response.iter_lines())
    trace = client.get(f"/api/runs/{run['thread_id']}/context").json()

    assert trace["project"] is None
    assert not any(item["trust"] == "untrusted_project" for item in trace["included"])


def test_run_can_opt_into_prompt_project_context(tmp_path: Path) -> None:
    project = tmp_path / "project"
    docs = project / "docs"
    docs.mkdir(parents=True)
    (docs / "adtracker.md").write_text("adtracker 业务背景：归因窗口是七天。\n", encoding="utf-8")
    fake = FakeOpenAIProvider()
    client = TestClient(
        create_app(
            fixture_delay_seconds=0,
            provider_config=config_store(),
            openai_provider=fake,
            skill_registry=SkillRegistry(),
            runtime_storage=_storage(tmp_path),
        )
    )

    run = client.post(
        "/api/runs",
        json={"prompt": "帮我根据adtracker业务背景生成一条数据", "project_root": str(project), "auto_project_context": True},
    ).json()
    with client.stream("GET", run["events_url"]) as response:
        _read_sse_payloads(response.iter_lines())
    trace = client.get(f"/api/runs/{run['thread_id']}/context").json()

    assert trace["project"]["auto_project_context"] is True
    assert trace["project"]["query_source"] == "prompt"
    assert trace["project"]["used_live"] is True
    assert any(item["kind"] == "project_search" and item["trust"] == "untrusted_project" for item in trace["included"])
    seeded_messages = fake.requests[0].messages or []
    seeded_blob = json.dumps(seeded_messages, ensure_ascii=False)
    assert "归因窗口是七天" in seeded_blob


def test_run_can_disable_auto_project_context(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "adtracker.md").write_text("adtracker 业务背景：归因窗口是七天。\n", encoding="utf-8")
    fake = FakeOpenAIProvider()
    client = TestClient(
        create_app(
            fixture_delay_seconds=0,
            provider_config=config_store(),
            openai_provider=fake,
            skill_registry=SkillRegistry(),
            runtime_storage=_storage(tmp_path),
        )
    )

    run = client.post(
        "/api/runs",
        json={"prompt": "帮我根据adtracker业务背景生成一条数据", "project_root": str(project), "auto_project_context": False},
    ).json()
    with client.stream("GET", run["events_url"]) as response:
        _read_sse_payloads(response.iter_lines())
    trace = client.get(f"/api/runs/{run['thread_id']}/context").json()

    assert trace["project"] is None
    assert not any(item["trust"] == "untrusted_project" for item in trace["included"])


def _write_skill(path: Path, *, name: str, description: str) -> None:
    path.mkdir(parents=True, exist_ok=True)
    (path / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: {description}\n---\nDetailed instructions for {name}.\n",
        encoding="utf-8",
    )


def _write_manifest(path: Path, text: str) -> None:
    path.mkdir(parents=True, exist_ok=True)
    (path / "skill.yaml").write_text(text, encoding="utf-8")


def _storage(tmp_path: Path) -> RuntimeStorage:
    return RuntimeStorage(RuntimeDatabase(tmp_path / "kira.db"))


def _read_sse_payloads(lines) -> list[dict]:
    payloads = []
    for line in lines:
        if line.startswith("data: "):
            payloads.append(json.loads(line.removeprefix("data: ")))
    return payloads
