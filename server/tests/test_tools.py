from __future__ import annotations

import os
from pathlib import Path

from fastapi.testclient import TestClient

from kira_server.main import create_app
from kira_server.tooling.policy import MAX_FILE_BYTES
from kira_server.tooling.registry import create_tool_registry


def test_get_tools_returns_builtin_schemas() -> None:
    client = TestClient(create_app(fixture_delay_seconds=0))

    response = client.get("/api/tools")

    assert response.status_code == 200
    body = response.json()
    tools = {tool["name"]: tool for tool in body["tools"]}
    assert set(tools) == {
        "list_project_files",
        "search_project_files",
        "read_project_file",
        "run_python_script",
        "run_shell_command",
        "ask_user_question",
    }
    for tool in tools.values():
        assert tool["description"]
        assert tool["args_schema"]["type"] == "object"
        assert tool["result_schema"]["title"] == "ToolResult"
        assert tool["risk"] in {
            "read_only_project_files",
            "controlled_python_execution",
            "controlled_shell_execution",
            "hitl_placeholder",
        }
    assert "Do not call it just to synthesize" in tools["run_shell_command"]["description"]
    assert "python -c" in tools["run_shell_command"]["args_schema"]["properties"]["command"]["description"]
    assert "minified one-line JSON" in tools["run_shell_command"]["args_schema"]["properties"]["command"]["description"]


def test_validation_errors_are_normalized(tmp_path: Path) -> None:
    registry = create_tool_registry(default_root=tmp_path, prefer_rg=False)

    result = registry.invoke("list_project_files", {"limit": 0})

    assert result["ok"] is False
    assert result["code"] == "validation_error"
    assert "errors" in result["metadata"]


def test_path_traversal_and_symlink_escape_are_rejected(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("outside", encoding="utf-8")
    (project / "link.txt").symlink_to(outside)
    registry = create_tool_registry(default_root=project, prefer_rg=False)

    traversal = registry.invoke("read_project_file", {"path": "../outside.txt"})
    symlink = registry.invoke("read_project_file", {"path": "link.txt"})

    assert traversal["ok"] is False
    assert traversal["code"] == "path_outside_root"
    assert symlink["ok"] is False
    assert symlink["code"] == "path_outside_root"


def test_file_policy_handles_ignored_binary_large_and_truncated_reads(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "README.md").write_text("hello\nneedle\nmore text\n", encoding="utf-8")
    (project / "node_modules").mkdir()
    (project / "node_modules" / "ignored.txt").write_text("needle", encoding="utf-8")
    (project / "binary.bin").write_bytes(b"\x00\x01binary")
    (project / "large.txt").write_text("x" * (MAX_FILE_BYTES + 1), encoding="utf-8")
    registry = create_tool_registry(default_root=project, prefer_rg=False)

    listed = registry.invoke("list_project_files", {"limit": 10})
    binary = registry.invoke("read_project_file", {"path": "binary.bin"})
    large = registry.invoke("read_project_file", {"path": "large.txt"})
    truncated = registry.invoke("read_project_file", {"path": "README.md", "limit": 5})

    assert listed["ok"] is True
    assert "README.md" in listed["data"]["files"]
    assert "node_modules/ignored.txt" not in listed["data"]["files"]
    assert binary["ok"] is False
    assert binary["code"] == "binary_file"
    assert large["ok"] is False
    assert large["code"] == "file_too_large"
    assert truncated["ok"] is True
    assert truncated["data"]["content"] == "hello"
    assert truncated["truncated"] is True
    assert truncated["metadata"]["path"] == "README.md"
    assert truncated["metadata"]["content_hash"]


def test_file_listing_and_search_work_without_rg(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "a.txt").write_text("needle one\n", encoding="utf-8")
    (project / "b.txt").write_text("needle two\n", encoding="utf-8")
    registry = create_tool_registry(default_root=project, prefer_rg=False)

    listed = registry.invoke("list_project_files", {"limit": 1})
    searched = registry.invoke("search_project_files", {"query": "needle", "limit": 5})

    assert listed["ok"] is True
    assert listed["metadata"]["used_rg"] is False
    assert listed["truncated"] is True
    assert listed["metadata"]["omitted_count"] == 1
    assert searched["ok"] is True
    assert searched["metadata"]["used_rg"] is False
    assert {match["path"] for match in searched["data"]["matches"]} == {"a.txt", "b.txt"}


def test_read_only_registry_exposes_no_mutation_tools(tmp_path: Path) -> None:
    registry = create_tool_registry(default_root=tmp_path, prefer_rg=False)

    forbidden_terms = ["write", "delete", "patch", "stage", "git"]

    assert all(not any(term in name for term in forbidden_terms) for name in registry.tool_names)


def test_run_python_script_controls_execution(tmp_path: Path, monkeypatch) -> None:
    project = tmp_path / "project"
    project.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    script = project / "inspect.py"
    script.write_text(
        "\n".join(
            [
                "import os, sys",
                "print('secret=' + str(os.environ.get('SECRET_TOKEN')))",
                "print('allowed=' + str(os.environ.get('KIRA_TEST_ENV')))",
                "print(sys.argv[1])",
            ]
        ),
        encoding="utf-8",
    )
    timeout_script = project / "sleep.py"
    timeout_script.write_text("import time; time.sleep(2)", encoding="utf-8")
    output_script = project / "output.py"
    output_script.write_text("print('x' * 100)", encoding="utf-8")
    outside_script = outside / "outside.py"
    outside_script.write_text("print('outside')", encoding="utf-8")
    monkeypatch.setenv("SECRET_TOKEN", "parent-secret")
    registry = create_tool_registry(default_root=project, prefer_rg=False)

    completed = registry.invoke(
        "run_python_script",
        {
            "path": "inspect.py",
            "args": ["literal&&value"],
            "env": {"SECRET_TOKEN": "child-secret", "KIRA_TEST_ENV": "allowed"},
        },
    )
    cwd_error = registry.invoke("run_python_script", {"path": "inspect.py", "cwd": str(outside)})
    script_error = registry.invoke("run_python_script", {"path": str(outside_script)})
    timeout = registry.invoke("run_python_script", {"path": "sleep.py", "timeout_seconds": 0.1})
    capped = registry.invoke("run_python_script", {"path": "output.py", "stdout_limit": 10})

    assert completed["ok"] is True
    assert "literal&&value" in completed["data"]["stdout"]
    assert "secret=None" in completed["data"]["stdout"]
    assert "allowed=allowed" in completed["data"]["stdout"]
    assert "SECRET_TOKEN" not in completed["metadata"]["env_keys"]
    assert cwd_error["ok"] is False
    assert cwd_error["code"] == "path_outside_root"
    assert script_error["ok"] is False
    assert script_error["code"] == "path_outside_root"
    assert timeout["ok"] is False
    assert timeout["code"] == "timeout"
    assert capped["ok"] is True
    assert capped["truncated"] is True
    assert capped["metadata"]["stdout_truncated"] is True
    assert len(capped["data"]["stdout"]) == 10


def test_run_shell_command_controls_execution(tmp_path: Path, monkeypatch) -> None:
    project = tmp_path / "project"
    project.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    monkeypatch.setenv("DS_TOKEN", "token-secret-value")
    monkeypatch.setenv("KIRA_TEST_ENV", "allowed-value")
    registry = create_tool_registry(default_root=project, prefer_rg=False)

    completed = registry.invoke(
        "run_shell_command",
        {
            "command": "printf 'hello'; printf 'err' >&2",
            "timeout_seconds": 2,
        },
    )
    env_result = registry.invoke(
        "run_shell_command",
        {
            "command": "printf 'allowed=%s' \"$KIRA_TEST_ENV\"",
            "stdout_limit": 200,
        },
    )
    secret_echo = registry.invoke(
        "run_shell_command",
        {
            "command": "printf 'token=%s' \"$DS_TOKEN\"",
            "stdout_limit": 200,
        },
    )
    secret_file = registry.invoke("run_shell_command", {"command": "cat .env.local 2>/dev/null | head -20"})
    cwd_error = registry.invoke("run_shell_command", {"command": "pwd", "cwd": str(outside)})
    timeout = registry.invoke("run_shell_command", {"command": "sleep 2", "timeout_seconds": 0.1})
    capped = registry.invoke("run_shell_command", {"command": "printf 'xxxxxxxxxx'", "stdout_limit": 4})

    assert completed["ok"] is True
    assert completed["data"]["stdout"] == "hello"
    assert completed["data"]["stderr"] == "err"
    assert env_result["ok"] is True
    assert env_result["data"]["stdout"] == "allowed=allowed-value"
    assert secret_echo["ok"] is False
    assert secret_echo["code"] == "secret_inspection_denied"
    assert secret_file["ok"] is False
    assert secret_file["code"] == "secret_inspection_denied"
    assert "DS_TOKEN" in env_result["metadata"]["env_keys"]
    assert cwd_error["ok"] is False
    assert cwd_error["code"] == "path_outside_root"
    assert timeout["ok"] is False
    assert timeout["code"] == "timeout"
    assert capped["ok"] is True
    assert capped["truncated"] is True
    assert capped["data"]["stdout"] == "xxxx"


def test_ask_user_question_placeholder_and_validation(tmp_path: Path) -> None:
    registry = create_tool_registry(default_root=tmp_path, prefer_rg=False)

    pending = registry.invoke(
        "ask_user_question",
        {"question": "Pick an option", "fields": [{"id": "choice", "label": "Choice"}]},
    )
    invalid = registry.invoke("ask_user_question", {"question": "   "})

    assert pending["ok"] is True
    assert pending["code"] == "question_pending"
    assert pending["data"]["status"] == "pending"
    assert pending["data"]["question_id"].startswith("question-")
    assert pending["metadata"]["stage"] == "stage-02-placeholder"
    assert invalid["ok"] is False
    assert invalid["code"] == "validation_error"


def test_unknown_tool_returns_structured_error(tmp_path: Path) -> None:
    registry = create_tool_registry(default_root=tmp_path, prefer_rg=False)

    result = registry.invoke("missing_tool", {})

    assert result["ok"] is False
    assert result["code"] == "tool_not_found"
