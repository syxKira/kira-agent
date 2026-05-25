#!/usr/bin/env python3
"""Start the attribution validation DolphinScheduler workflow."""

from __future__ import annotations

import argparse
import json
import os
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


DEFAULT_ENDPOINT = "https://dolphinscheduler.hypergryph.net/dolphinscheduler"
DEFAULT_PROJECT_CODE = "152149824329120"
DEFAULT_WORKFLOW_CODE = "173307975548163"
DEFAULT_WORKFLOW_VERSION = "12"


def load_token() -> str | None:
    token = os.getenv("DS_TOKEN")
    if token:
        return token

    project_root = Path(__file__).resolve().parents[4]
    candidates = [
        Path.cwd() / ".env.local",
        project_root / ".env.local",
    ]

    seen: set[Path] = set()
    for path in candidates:
        if path in seen or not path.exists():
            continue
        seen.add(path)
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            if key.strip() == "DS_TOKEN":
                return value.strip().strip('"').strip("'")
    return None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Start the attribution validation workflow in DolphinScheduler."
    )
    parser.add_argument("--scene-type", required=True, help="Validation scene, e.g. device_activation.")
    parser.add_argument(
        "--query-target",
        required=True,
        choices=["attribution", "landing"],
        help="Which table type to query first.",
    )
    parser.add_argument(
        "--event-timestamp-ms",
        required=True,
        help="Business event timestamp in milliseconds, e.g. 1778688000000.",
    )
    parser.add_argument("--biz-env", required=True, help="Business env, e.g. staging.")
    parser.add_argument("--app-id", required=True, help="App id for the target project.")
    parser.add_argument("--device-id", help="Device id for device/launcher scenes.")
    parser.add_argument("--user-id", help="User id for user scenes.")
    parser.add_argument("--token", default=load_token(), help="DolphinScheduler token.")
    parser.add_argument("--endpoint", default=os.getenv("DS_ENDPOINT", DEFAULT_ENDPOINT))
    parser.add_argument("--project-code", default=os.getenv("DS_PROJECT_CODE", DEFAULT_PROJECT_CODE))
    parser.add_argument(
        "--workflow-code",
        default=os.getenv("DS_VALIDATION_WORKFLOW_CODE", DEFAULT_WORKFLOW_CODE),
        help="Workflow definition code for attribution validation.",
    )
    parser.add_argument(
        "--workflow-version",
        default=os.getenv("DS_VALIDATION_WORKFLOW_VERSION", DEFAULT_WORKFLOW_VERSION),
        help="Workflow definition version for attribution validation.",
    )
    parser.add_argument("--schedule-date", default=time.strftime("%Y-%m-%d"))
    parser.add_argument("--wait", action="store_true", help="Poll the task state after starting workflow.")
    parser.add_argument("--wait-timeout", type=int, default=60)
    parser.add_argument("--dry-run", action="store_true", help="Print request payload without sending.")
    return parser.parse_args()


def build_start_params(args: argparse.Namespace) -> str:
    params: list[dict[str, str]] = [
        {"direct": "IN", "type": "VARCHAR", "value": args.scene_type, "prop": "scene_type"},
        {"direct": "IN", "type": "VARCHAR", "value": args.query_target, "prop": "query_target"},
        {
            "direct": "IN",
            "type": "VARCHAR",
            "value": args.event_timestamp_ms,
            "prop": "event_timestamp_ms",
        },
        {"direct": "IN", "type": "VARCHAR", "value": args.biz_env, "prop": "biz_env"},
        {"direct": "IN", "type": "VARCHAR", "value": args.app_id, "prop": "app_id"},
    ]

    if args.device_id:
        params.append(
            {"direct": "IN", "type": "VARCHAR", "value": args.device_id, "prop": "device_id"}
        )
    if args.user_id:
        params.append({"direct": "IN", "type": "VARCHAR", "value": args.user_id, "prop": "user_id"})

    return json.dumps(params, ensure_ascii=False, separators=(",", ":"))


def request_json(url: str, token: str, data: dict[str, str] | None = None) -> dict:
    ssl_context = None
    try:
        import certifi

        ssl_context = ssl.create_default_context(cafile=certifi.where())
    except Exception:
        pass

    if data is None:
        request = urllib.request.Request(url, headers={"accept": "application/json", "token": token})
    else:
        body = urllib.parse.urlencode(data).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=body,
            headers={
                "accept": "application/json, text/plain, */*",
                "accept-language": "zh-CN,zh;q=0.9",
                "content-type": "application/x-www-form-urlencoded",
                "token": token,
                "language": "zh_CN",
                "origin": "https://dolphinscheduler.hypergryph.net",
            },
        )

    try:
        with urllib.request.urlopen(request, timeout=30, context=ssl_context) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"HTTP {exc.code}: {detail}") from exc


def start_workflow(args: argparse.Namespace, start_params: str) -> dict:
    schedule_time = json.dumps(
        {
            "complementStartDate": f"{args.schedule_date} 00:00:00",
            "complementEndDate": f"{args.schedule_date} 00:00:00",
        },
        separators=(",", ":"),
    )
    url = f"{args.endpoint}/projects/{args.project_code}/executors/start-workflow-instance"
    form = {
        "workflowDefinitionCode": args.workflow_code,
        "failureStrategy": "CONTINUE",
        "warningType": "NONE",
        "warningGroupId": "",
        "execType": "START_PROCESS",
        "startNodeList": "",
        "taskDependType": "TASK_POST",
        "complementDependentMode": "OFF_MODE",
        "runMode": "RUN_MODE_SERIAL",
        "workflowInstancePriority": "MEDIUM",
        "workerGroup": "default",
        "tenantCode": "default",
        "environmentCode": "",
        "startParams": start_params,
        "expectedParallelismNumber": "2",
        "dryRun": "0",
        "testFlag": "0",
        "version": args.workflow_version,
        "allLevelDependent": "false",
        "executionOrder": "DESC_ORDER",
        "scheduleTime": schedule_time,
    }

    if args.dry_run:
        return {"dryRun": True, "url": url, "form": form}

    if not args.token:
        raise SystemExit("Missing token. Set DS_TOKEN or pass --token.")

    return request_json(url, args.token, form)


def wait_for_task(args: argparse.Namespace, workflow_instance_id: int) -> dict | None:
    if not args.token:
        raise SystemExit("Missing token. Set DS_TOKEN or pass --token.")

    deadline = time.time() + args.wait_timeout
    base_url = f"{args.endpoint}/projects/{args.project_code}/task-instances"
    query = urllib.parse.urlencode(
        {"workflowInstanceId": workflow_instance_id, "pageNo": 1, "pageSize": 20}
    )
    url = f"{base_url}?{query}"

    while time.time() < deadline:
        result = request_json(url, args.token)
        tasks = result.get("data", {}).get("totalList", [])
        if tasks:
            task = tasks[0]
            state = task.get("state")
            if state in {"SUCCESS", "FAILURE", "KILL", "STOP"}:
                return task
        time.sleep(2)
    return None


def main() -> None:
    args = parse_args()
    start_params = build_start_params(args)
    result = start_workflow(args, start_params)
    print(json.dumps(result, ensure_ascii=False))

    workflow_ids = result.get("data") if isinstance(result, dict) else None
    if args.wait and workflow_ids:
        task = wait_for_task(args, int(workflow_ids[0]))
        print(json.dumps({"task": task}, ensure_ascii=False))
        if task and task.get("state") != "SUCCESS":
            raise SystemExit(1)


if __name__ == "__main__":
    main()
