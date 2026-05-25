#!/usr/bin/env python3
"""Send one behavior Kafka message through DolphinScheduler."""

from __future__ import annotations

import argparse
import json
import os
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request


DEFAULT_ENDPOINT = "https://dolphinscheduler.hypergryph.net/dolphinscheduler"
DEFAULT_PROJECT_CODE = "152149824329120"
DEFAULT_WORKFLOW_CODE = "172773151769857"
DEFAULT_WORKFLOW_VERSION = "4"
DEFAULT_POST_SEND_WAIT_SECONDS = 60
BEHAVIOR_TOPIC = "data-lake_ods_staging_17IYH6HNGZwwbD2mE1ag6Rqm"
ALLOWED_EVENT_NAMES = {
    "#app_start",
    "#user_login",
    "#charge",
    "#character_login",
    "#downloader_start",
    "#installer_start",
    "#launcher_expose",
}


def load_token() -> str | None:
    token = os.getenv("DS_TOKEN")
    if token:
        return token

    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, "../../../.."))
    candidates = [
        os.path.join(os.getcwd(), ".env.local"),
        os.path.join(project_root, ".env.local"),
    ]

    seen = set()
    for path in candidates:
        if path in seen or not os.path.exists(path):
            continue
        seen.add(path)
        with open(path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                if key.strip() == "DS_TOKEN":
                    return value.strip().strip('"').strip("'")
    return None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Send one behavior JSON message by starting the DolphinScheduler workflow."
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--file", help="Path to one behavior Kafka JSON message, or '-' for stdin.")
    source.add_argument("--json", help="One behavior Kafka JSON message.")
    parser.add_argument(
        "--token",
        default=load_token(),
        help="DolphinScheduler token. Defaults to DS_TOKEN, then project .env.local.",
    )
    parser.add_argument("--endpoint", default=os.getenv("DS_ENDPOINT", DEFAULT_ENDPOINT))
    parser.add_argument("--project-code", default=os.getenv("DS_PROJECT_CODE", DEFAULT_PROJECT_CODE))
    parser.add_argument(
        "--workflow-code",
        default=os.getenv("DS_BEHAVIOR_WORKFLOW_CODE", DEFAULT_WORKFLOW_CODE),
        help="DolphinScheduler workflowDefinitionCode for behavior sending.",
    )
    parser.add_argument(
        "--workflow-version",
        default=os.getenv("DS_BEHAVIOR_WORKFLOW_VERSION", DEFAULT_WORKFLOW_VERSION),
        help="DolphinScheduler workflow definition version for behavior sending.",
    )
    parser.add_argument("--schedule-date", default=os.getenv("DS_SCHEDULE_DATE", time.strftime("%Y-%m-%d")))
    parser.add_argument("--dry-run", action="store_true", help="Print request payload without sending.")
    parser.add_argument("--wait", action="store_true", help="Poll the task instance state after starting workflow.")
    parser.add_argument("--wait-timeout", type=int, default=60)
    parser.add_argument(
        "--post-send-wait-seconds",
        type=int,
        default=int(os.getenv("DS_POST_SEND_WAIT_SECONDS", DEFAULT_POST_SEND_WAIT_SECONDS)),
        help="Extra wait time in seconds after sending completes. Defaults to 60.",
    )
    return parser.parse_args()


def load_message(args: argparse.Namespace) -> dict:
    if args.json is not None:
        raw = args.json
    elif args.file == "-":
        raw = sys.stdin.read()
    else:
        with open(args.file, "r", encoding="utf-8") as fh:
            raw = fh.read()

    message = json.loads(raw)
    topic = message.get("topic")
    event_name = message.get("data", {}).get("#name")
    if topic != BEHAVIOR_TOPIC:
        raise SystemExit(f"Expected topic to be {BEHAVIOR_TOPIC}, got {topic!r}.")
    if event_name not in ALLOWED_EVENT_NAMES:
        expected = ", ".join(sorted(ALLOWED_EVENT_NAMES))
        raise SystemExit(f"Expected data.#name to be one of {expected}, got {event_name!r}.")
    return message


def build_start_params(message: dict) -> str:
    compact_message = json.dumps(message, ensure_ascii=False, separators=(",", ":"))
    params = [
        {
            "direct": "IN",
            "type": "VARCHAR",
            "value": f"[{json.dumps(compact_message, ensure_ascii=False)}]",
            "prop": "data",
        }
    ]
    return json.dumps(params, ensure_ascii=False, separators=(",", ":"))


def request_json(url: str, token: str, data: dict | None = None) -> dict:
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
        raise SystemExit("Missing workflow code. Set DS_BEHAVIOR_WORKFLOW_CODE or pass --workflow-code.")

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
    message = load_message(args)
    start_params = build_start_params(message)
    result = start_workflow(args, start_params)
    print(json.dumps(result, ensure_ascii=False))

    workflow_ids = result.get("data") if isinstance(result, dict) else None
    if args.wait and workflow_ids:
        task = wait_for_task(args, int(workflow_ids[0]))
        print(json.dumps({"task": task}, ensure_ascii=False))
        if task and task.get("state") != "SUCCESS":
            raise SystemExit(1)

    if not args.dry_run and args.post_send_wait_seconds > 0:
        time.sleep(args.post_send_wait_seconds)


if __name__ == "__main__":
    main()
