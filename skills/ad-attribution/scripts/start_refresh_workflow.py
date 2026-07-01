#!/usr/bin/env python3
"""Start the attribution refresh DolphinScheduler workflow."""

from __future__ import annotations

import argparse
import json
import os
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, timedelta
from pathlib import Path


DEFAULT_ENDPOINT = "https://dolphinscheduler.hypergryph.net/dolphinscheduler"
DEFAULT_PROJECT_CODE = "152149824329120"
DEFAULT_WORKFLOW_CODE = "162039914621184"
DEFAULT_WORKFLOW_VERSION = "5"
DEFAULT_DS_DRY_RUN = "1"


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


def parse_date(value: str, arg_name: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise SystemExit(f"{arg_name} must be YYYY-MM-DD, got {value!r}.") from exc


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Start the attribution refresh workflow. The DS start_dt/end_dt params are "
            "derived by adding one day to the data period start/end dates."
        )
    )
    parser.add_argument(
        "--data-start-date",
        required=True,
        help="Start date of the generated data period, YYYY-MM-DD.",
    )
    parser.add_argument(
        "--data-end-date",
        required=True,
        help="End date of the generated data period, YYYY-MM-DD.",
    )
    parser.add_argument(
        "--token",
        default=load_token(),
        help="DolphinScheduler token. Defaults to DS_TOKEN, then project .env.local.",
    )
    parser.add_argument("--endpoint", default=os.getenv("DS_ENDPOINT", DEFAULT_ENDPOINT))
    parser.add_argument("--project-code", default=os.getenv("DS_PROJECT_CODE", DEFAULT_PROJECT_CODE))
    parser.add_argument(
        "--workflow-code",
        default=os.getenv("DS_REFRESH_WORKFLOW_CODE", DEFAULT_WORKFLOW_CODE),
        help="DolphinScheduler workflowDefinitionCode for attribution refresh.",
    )
    parser.add_argument(
        "--workflow-version",
        default=os.getenv("DS_REFRESH_WORKFLOW_VERSION", DEFAULT_WORKFLOW_VERSION),
        help="DolphinScheduler workflow definition version for attribution refresh.",
    )
    parser.add_argument(
        "--ds-dry-run",
        choices=["0", "1"],
        default=os.getenv("DS_REFRESH_DRY_RUN", DEFAULT_DS_DRY_RUN),
        help="Value sent to DolphinScheduler dryRun. Defaults to the captured curl value, 1.",
    )
    parser.add_argument("--schedule-date", default=os.getenv("DS_SCHEDULE_DATE", time.strftime("%Y-%m-%d")))
    parser.add_argument("--dry-run", action="store_true", help="Print request payload without sending.")
    parser.add_argument("--wait", action="store_true", help="Poll the task instance state after starting workflow.")
    parser.add_argument("--wait-timeout", type=int, default=60)
    return parser.parse_args()


def derive_refresh_dates(args: argparse.Namespace) -> tuple[str, str]:
    data_start_date = parse_date(args.data_start_date, "--data-start-date")
    data_end_date = parse_date(args.data_end_date, "--data-end-date")
    if data_start_date > data_end_date:
        raise SystemExit("--data-start-date must be earlier than or equal to --data-end-date.")

    start_dt = data_start_date + timedelta(days=1)
    end_dt = data_end_date + timedelta(days=1)
    return start_dt.isoformat(), end_dt.isoformat()


def build_start_params(start_dt: str, end_dt: str) -> str:
    params = [
        {"prop": "start_dt", "direct": "IN", "type": "VARCHAR", "value": start_dt},
        {"prop": "end_dt", "direct": "IN", "type": "VARCHAR", "value": end_dt},
    ]
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
                "language": "zh_CN",
                "origin": "https://dolphinscheduler.hypergryph.net",
                "token": token,
            },
        )

    try:
        with urllib.request.urlopen(request, timeout=30, context=ssl_context) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"HTTP {exc.code}: {detail}") from exc


def start_workflow(args: argparse.Namespace, start_params: str) -> dict:
    if not args.workflow_code:
        raise SystemExit("Missing workflow code. Set DS_REFRESH_WORKFLOW_CODE or pass --workflow-code.")

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
        "dryRun": args.ds_dry_run,
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
    start_dt, end_dt = derive_refresh_dates(args)
    start_params = build_start_params(start_dt, end_dt)
    result = start_workflow(args, start_params)
    print(json.dumps({"start_dt": start_dt, "end_dt": end_dt, "result": result}, ensure_ascii=False))

    workflow_ids = result.get("data") if isinstance(result, dict) else None
    if args.wait and workflow_ids:
        task = wait_for_task(args, int(workflow_ids[0]))
        print(json.dumps({"task": task}, ensure_ascii=False))
        if task and task.get("state") != "SUCCESS":
            raise SystemExit(1)


if __name__ == "__main__":
    main()
