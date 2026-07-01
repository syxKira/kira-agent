from __future__ import annotations

import json
import zipfile
from pathlib import Path

from fastapi.testclient import TestClient

from kira_server.main import create_app
from kira_server.providers.config import ProviderConfigStore
from kira_server.skills.builtin import HITL_FIXTURE_SKILL_ID, TEST_SKILL_ID, create_builtin_skill_registry, create_stage03_test_skill
from kira_server.context import pack_context
from kira_server.skills.packages import PackageSource, parse_skill_package, skill_context_items
from kira_server.skills.registry import SkillDefinition, SkillRegistry, create_package_skill_registry


def test_builtin_test_skill_is_discoverable_and_redacted() -> None:
    registry = create_builtin_skill_registry()

    body = registry.metadata()

    assert registry.skill_ids == [TEST_SKILL_ID, HITL_FIXTURE_SKILL_ID]
    skills = {skill["skill_id"]: skill for skill in body["skills"]}
    assert "ad-attribution" in skills
    assert skills[TEST_SKILL_ID]["workflows"][0]["name"] == "generic-stage-03-workflow"
    assert skills[TEST_SKILL_ID]["allowed_tools"] == ["list_project_files"]
    assert skills[HITL_FIXTURE_SKILL_ID]["skill_id"] == HITL_FIXTURE_SKILL_ID
    assert "api_key" not in json.dumps(body)
    assert "sk-secret" not in json.dumps(body)


def test_non_workflow_skill_is_ignored() -> None:
    registry = SkillRegistry([SkillDefinition(skill_id="notes", name="Notes", workflows=[])])

    assert registry.skill_ids == []
    assert registry.metadata() == {"skills": []}


def test_skills_endpoint_returns_empty_registry() -> None:
    client = TestClient(
        create_app(
            fixture_delay_seconds=0,
            provider_config=ProviderConfigStore(config_path="/missing", loaded=False),
            skill_registry=SkillRegistry(),
        )
    )

    response = client.get("/api/skills")

    assert response.status_code == 200
    assert response.json() == {"skills": []}


def test_default_skills_endpoint_hides_internal_builtin_fixture_skills() -> None:
    client = TestClient(
        create_app(
            fixture_delay_seconds=0,
            provider_config=ProviderConfigStore(config_path="/missing", loaded=False),
            skill_registry=create_builtin_skill_registry(),
        )
    )

    default_response = client.get("/api/skills")
    internal_response = client.get("/api/skills", params={"include_internal": "true"})

    assert default_response.status_code == 200
    assert {skill["skill_id"] for skill in default_response.json()["skills"]} == {"ad-attribution"}
    assert internal_response.status_code == 200
    assert {skill["skill_id"] for skill in internal_response.json()["skills"]} == {
        "ad-attribution",
        TEST_SKILL_ID,
        HITL_FIXTURE_SKILL_ID,
    }


def test_app_starts_with_new_runtime_packages_without_workflow_skills() -> None:
    client = TestClient(
        create_app(
            fixture_delay_seconds=0,
            provider_config=ProviderConfigStore(config_path="/missing", loaded=False),
            skill_registry=SkillRegistry(),
        )
    )

    assert client.get("/api/health").json() == {"status": "ok"}


def test_unknown_skill_id_is_rejected() -> None:
    client = TestClient(
        create_app(
            fixture_delay_seconds=0,
            provider_config=ProviderConfigStore(config_path="/missing", loaded=False),
            skill_registry=create_builtin_skill_registry(),
        )
    )

    response = client.post("/api/runs", json={"prompt": "hello", "skill_id": "missing"})

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "skill_not_found"


def test_known_skill_run_creation_stores_safe_skill_metadata() -> None:
    client = TestClient(
        create_app(
            fixture_delay_seconds=0,
            provider_config=ProviderConfigStore(config_path="/missing", loaded=False),
            skill_registry=SkillRegistry([create_stage03_test_skill()]),
        )
    )

    response = client.post("/api/runs", json={"prompt": "hello", "skill_id": TEST_SKILL_ID})

    assert response.status_code == 200
    body = response.json()
    assert body["skill"]["skill_id"] == TEST_SKILL_ID
    assert body["provider"]["mode"] == "fixture"
    assert body["provider"]["fallback_reason"] == "missing_provider_config"
    assert "api_key" not in json.dumps(body["skill"])


def test_project_skill_zip_install_filters_metadata_and_discovers_skill(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    archive = tmp_path / "ad.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("__MACOSX/._ad-skill", "ignored")
        zf.writestr("ad-skill/SKILL.md", "---\nname: ad-skill\ndescription: 构造 adtracker 广告数据\n---\n# Body\n")
        zf.writestr("ad-skill/scripts/send.py", "print('ok')\n")
        zf.writestr("ad-skill/scripts/__pycache__/send.pyc", "ignored")

    client = TestClient(create_app(fixture_delay_seconds=0, provider_config=ProviderConfigStore(config_path="/missing", loaded=False)))
    response = client.post("/api/skills/install", json={"project_root": str(project), "zip_path": str(archive)})

    assert response.status_code == 200
    body = response.json()
    assert body["skill_id"] == "ad-skill"
    assert (project / ".kira" / "skills" / "ad-skill" / "SKILL.md").is_file()
    assert not (project / ".kira" / "skills" / "__MACOSX").exists()
    skills = client.get("/api/skills", params={"project_root": str(project)}).json()["skills"]
    assert {"ad-attribution", "ad-skill"}.issubset({skill["skill_id"] for skill in skills})


def test_project_skill_zip_install_rejects_unsafe_path(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    archive = tmp_path / "bad.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("../escape/SKILL.md", "---\nname: bad\ndescription: bad\n---\n")

    client = TestClient(create_app(fixture_delay_seconds=0, provider_config=ProviderConfigStore(config_path="/missing", loaded=False)))
    response = client.post("/api/skills/install", json={"project_root": str(project), "zip_path": str(archive)})

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "unsafe_zip_path"


def test_skill_frontmatter_invocation_and_chunked_context(tmp_path: Path) -> None:
    skill_dir = tmp_path / "long-skill"
    skill_dir.mkdir()
    long_body = "# Start\n" + ("alpha\n" * 3000) + "\n## Send\npython scripts/send.py\n"
    skill_dir.joinpath("SKILL.md").write_text(
        "---\n"
        "name: long-skill\n"
        "description: 构造 adtracker 广告数据\n"
        "disable-model-invocation: true\n"
        "user-invocable: false\n"
        "---\n"
        + long_body,
        encoding="utf-8",
    )

    package = parse_skill_package(skill_dir, PackageSource(key="project", priority=20, path=str(tmp_path)), include_body=True)
    metadata = package.public_metadata()
    items = skill_context_items(package)

    assert metadata["invocation"]["disable_model_invocation"] is True
    assert metadata["invocation"]["model_invocable"] is False
    assert metadata["invocation"]["user_invocable"] is False
    assert len(items) > 1
    assert "python scripts/send.py" in items[-1].text
    packed = pack_context(thread_id="thread-1", items=list(reversed(items)))
    packed_indexes = [item.metadata.get("chunk_index") for item in packed.items if item.kind == "skill_doc"]
    assert packed_indexes == sorted(packed_indexes)


def test_skill_context_rewrites_imported_script_paths_to_installed_path(tmp_path: Path) -> None:
    skill_dir = tmp_path / ".kira" / "skills" / "ad-attribution-test-data"
    skill_dir.mkdir(parents=True)
    skill_dir.joinpath("SKILL.md").write_text(
        "---\n"
        "name: ad-attribution-test-data\n"
        "description: 构造 adtracker 广告数据\n"
        "---\n"
        "Run `python .cursor/skills/ad-attribution-test-data/scripts/send_adtracker.py --json ...`.\n"
        "Do not use `python .codex/skills/ad-attribution-test-data/scripts/send_adtracker.py` here.\n",
        encoding="utf-8",
    )
    package = parse_skill_package(skill_dir, PackageSource(key="project", priority=20, path=str(tmp_path / ".kira" / "skills")), include_body=True)

    text = "\n".join(item.text for item in skill_context_items(package))

    assert ".cursor/skills/ad-attribution-test-data" not in text
    assert ".codex/skills/ad-attribution-test-data" not in text
    assert f"{skill_dir.as_posix()}/scripts/send_adtracker.py" in text


def test_skill_context_selects_relevant_sections_for_prompt(tmp_path: Path) -> None:
    skill_dir = tmp_path / ".kira" / "skills" / "ad-attribution-test-data"
    skill_dir.mkdir(parents=True)
    skill_dir.joinpath("SKILL.md").write_text(
        "---\n"
        "name: ad-attribution-test-data\n"
        "description: 构造 adtracker 广告数据\n"
        "---\n"
        "# 通用广告归因测试数据\n\n"
        "## 快速开始\n按用户场景造数。\n\n"
        "## 核心概念\n选择精准匹配字段。\n\n"
        "### 精准匹配字段\n"
        "iOS 使用 idfa / #idfa_c，Android 使用 anid / #anid_c。\n\n"
        "## 数据模板\n选择匹配的模板。\n\n"
        "### 广告数据（`ad_tracker`）\n"
        "topic: data-lake_ods_staging_x48mn2zq83dx1flj7bds6xgk\n"
        "字段：idfa source media touch_ts。\n\n"
        "### Windows `tracking_code` 归因数据\n"
        "使用 #ad_landing 和 #tracking_code。\n\n"
        "### 设备数据（`#app_start`）\n"
        "字段：#sdid_s #idfa_c。\n\n"
        "## 输出格式\n每条 JSON 独立输出。\n\n"
        "## 发送 `ad_tracker` 广告数据\n"
        "python .cursor/skills/ad-attribution-test-data/scripts/send_adtracker.py --json '<单条ad_tracker JSON>' --wait\n\n"
        "## 发送 `#ad_landing` 广告落地数据\n"
        "python .cursor/skills/ad-attribution-test-data/scripts/send_ad_landing.py --json '<单条#ad_landing JSON>' --wait\n\n"
        "## 发送行为数据\n"
        "python .cursor/skills/ad-attribution-test-data/scripts/send_behavior.py --json '<单条行为JSON>' --wait\n",
        encoding="utf-8",
    )
    package = parse_skill_package(skill_dir, PackageSource(key="project", priority=20, path=str(tmp_path / ".kira" / "skills")), include_body=True)

    items = skill_context_items(package, query="帮我造一条adtracker广告数据，数据压缩成一行在单独的一个代码块里输出，然后发送一下")
    text = "\n".join(item.text for item in items)
    selection = items[0].metadata["selection"]

    assert selection["mode"] == "section"
    assert "精准匹配字段" in selection["selected_headings"]
    assert "广告数据（`ad_tracker`）" in selection["selected_headings"]
    assert "发送 `ad_tracker` 广告数据" in selection["selected_headings"]
    assert "send_adtracker.py" in text
    assert f"{skill_dir.as_posix()}/scripts/send_adtracker.py" in text
    assert "Windows `tracking_code`" not in text
    assert "send_ad_landing.py" not in text
    assert "send_behavior.py" not in text


def test_skill_context_selects_relevant_references_for_prompt(tmp_path: Path) -> None:
    skill_dir = tmp_path / ".kira" / "skills" / "ad-attribution"
    skill_dir.mkdir(parents=True)
    skill_dir.joinpath("SKILL.md").write_text(
        "---\n"
        "name: ad-attribution\n"
        "description: 构造广告归因测试数据并校验结果\n"
        "---\n"
        "# Body\n按需读取参考资料。\n",
        encoding="utf-8",
    )
    skill_dir.joinpath("skill.yaml").write_text(
        "references:\n"
        "  - references/test-data.md\n"
        "  - references/validation.md\n",
        encoding="utf-8",
    )
    references = skill_dir / "references"
    references.mkdir()
    references.joinpath("test-data.md").write_text(
        "# Test Data\n构造 adtracker 广告数据和 #app_start 行为数据。\n",
        encoding="utf-8",
    )
    references.joinpath("validation.md").write_text(
        "# Validation\n查询归因结果表，判断 match_type 和离线 device 表。\n",
        encoding="utf-8",
    )
    package = parse_skill_package(skill_dir, PackageSource(key="project", priority=20, path=str(tmp_path / ".kira" / "skills")), include_body=True)

    items = skill_context_items(package, query="帮我查询归因结果表并判断 match_type")
    text = "\n".join(item.text for item in items)
    references_loaded = [item for item in items if item.kind == "skill_reference"]

    assert len(references_loaded) == 1
    assert references_loaded[0].metadata["reference"] == "references/validation.md"
    assert "查询归因结果表" in text
    assert "构造 adtracker 广告数据" not in text


def test_prompt_auto_routes_to_model_invocable_skill(tmp_path: Path) -> None:
    skills_root = tmp_path / ".kira" / "skills"
    skills_root.mkdir(parents=True)
    data_skill = skills_root / "ad-data"
    data_skill.mkdir()
    data_skill.joinpath("SKILL.md").write_text(
        "---\nname: ad-data\ndescription: 构造 adtracker 广告数据并发送\n---\n# Body\n",
        encoding="utf-8",
    )
    validation_skill = skills_root / "ad-validation"
    validation_skill.mkdir()
    validation_skill.joinpath("SKILL.md").write_text(
        "---\nname: ad-validation\ndescription: 查询归因结果\ndisable-model-invocation: true\n---\n# Body\n",
        encoding="utf-8",
    )
    skill_registry = create_package_skill_registry(project_root=str(tmp_path))

    routed = skill_registry.route_for_prompt("帮我造一条 adtracker 广告数据，然后发送一下")
    disabled = skill_registry.route_for_prompt("查询归因结果")

    assert routed is not None
    assert routed.skill_id == "ad-data"
    assert disabled is not None
    assert disabled.skill_id == "ad-attribution"
