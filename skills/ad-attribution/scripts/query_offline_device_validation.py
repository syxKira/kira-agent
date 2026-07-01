#!/usr/bin/env python3
"""Query Trino for offline device attribution validation."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any


DEFAULT_HOST = "trino-gateway-data-platform-data-lake-prod.hypergryph.net"
DEFAULT_PORT = 443
DEFAULT_USER = "suyuxuan@hypergryph.com"
DEFAULT_DATABASE = "hive.hgbi_staging_17iyh6hngzwwbd2me1ag6rqm"

SCENE_LABELS = {
    "device_activation": "设备新增",
    "device_backflow": "设备回流",
    "device_activation_attribution": "设备新增归因",
    "device_backflow_attribution": "设备回流归因",
}


def load_env_file() -> None:
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
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Query offline device validation data from Trino."
    )
    parser.add_argument(
        "--scene-type",
        required=True,
        choices=sorted(SCENE_LABELS),
        help="Offline device validation scene.",
    )
    parser.add_argument("--device-id", required=True, help="Device id to query.")
    parser.add_argument("--dt", required=True, help="Device table partition date, YYYY-MM-DD.")
    parser.add_argument(
        "--event-timestamp-ms",
        type=int,
        help="Sent event timestamp in milliseconds, required for activation/backflow checks.",
    )
    parser.add_argument(
        "--database",
        default=DEFAULT_DATABASE,
        help=f"Full Trino database name. Defaults to {DEFAULT_DATABASE}.",
    )
    parser.add_argument(
        "--region",
        default="cn",
        choices=["cn", "overseas"],
        help="Credential set to use.",
    )
    parser.add_argument("--limit", type=int, default=20)
    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> None:
    try:
        date.fromisoformat(args.dt)
    except ValueError as exc:
        raise SystemExit("--dt must be YYYY-MM-DD.") from exc

    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)+", args.database):
        raise SystemExit("--database must be a dot-separated identifier like hive.schema.")

    if args.limit < 1 or args.limit > 100:
        raise SystemExit("--limit must be between 1 and 100.")

    if args.scene_type in {"device_activation", "device_backflow"} and args.event_timestamp_ms is None:
        raise SystemExit("--event-timestamp-ms is required for device activation/backflow checks.")


def trino_password_key(region: str) -> str:
    return "TRINO_OVERSEAS_PASSWORD" if region == "overseas" else "TRINO_CN_PASSWORD"


def connect_trino(region: str):
    try:
        import trino
        from trino.auth import BasicAuthentication
    except ImportError as exc:
        raise SystemExit("Missing dependency: install with `python -m pip install trino`.") from exc

    password_key = trino_password_key(region)
    password = os.getenv(password_key)
    if not password:
        raise SystemExit(f"Missing {password_key}. Set it in environment or .env.local.")

    user = os.getenv("TRINO_USER", DEFAULT_USER)
    return trino.dbapi.connect(
        host=os.getenv("TRINO_HOST", DEFAULT_HOST),
        port=int(os.getenv("TRINO_PORT", str(DEFAULT_PORT))),
        user=user,
        http_scheme="https",
        auth=BasicAuthentication(username=user, password=password),
        catalog="hive",
        schema="default",
    )


def sql_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def build_sql(args: argparse.Namespace) -> str:
    return f"""
SELECT
  "#device_id",
  "#activation_ts",
  "#backflow_ts",
  "#activation_match_type",
  "#ad_conversion_ts",
  dt
FROM {args.database}.device
WHERE "#device_id" = {sql_quote(args.device_id)}
  AND dt = DATE {sql_quote(args.dt)}
LIMIT {args.limit}
""".strip()


def normalize_row(columns: list[str], row: tuple[Any, ...]) -> dict[str, Any]:
    return {column: value for column, value in zip(columns, row, strict=False)}


def judge_row(args: argparse.Namespace, row: dict[str, Any]) -> dict[str, Any]:
    if args.scene_type == "device_activation":
        actual = row.get("#activation_ts")
        return {
            "field": "#activation_ts",
            "expected": args.event_timestamp_ms,
            "actual": actual,
            "passed": actual == args.event_timestamp_ms,
        }

    if args.scene_type == "device_backflow":
        actual = row.get("#backflow_ts")
        return {
            "field": "#backflow_ts",
            "expected": args.event_timestamp_ms,
            "actual": actual,
            "passed": actual == args.event_timestamp_ms,
        }

    if args.scene_type == "device_activation_attribution":
        actual = row.get("#activation_match_type")
        return {
            "field": "#activation_match_type",
            "actual": actual,
            "passed": actual is not None and actual != "",
        }

    actual_backflow_ts = row.get("#backflow_ts")
    actual_ad_conversion_ts = row.get("#ad_conversion_ts")
    return {
        "field": "#backflow_ts == #ad_conversion_ts",
        "backflow_ts": actual_backflow_ts,
        "ad_conversion_ts": actual_ad_conversion_ts,
        "passed": actual_backflow_ts is not None and actual_backflow_ts == actual_ad_conversion_ts,
    }


def main() -> None:
    load_env_file()
    args = parse_args()
    validate_args(args)

    database_was_default = "--database" not in sys.argv
    sql = build_sql(args)

    conn = connect_trino(args.region)
    cursor = conn.cursor()
    cursor.execute(sql)
    columns = [description[0] for description in cursor.description]
    rows = [normalize_row(columns, row) for row in cursor.fetchall()]

    result = {
        "scene_type": args.scene_type,
        "scene": SCENE_LABELS[args.scene_type],
        "database": args.database,
        "database_was_default": database_was_default,
        "default_database_notice": (
            f"未提供库名，已默认使用 {DEFAULT_DATABASE}" if database_was_default else None
        ),
        "table": f"{args.database}.device",
        "device_id": args.device_id,
        "dt": args.dt,
        "sql": sql,
        "row_count": len(rows),
        "rows": rows,
        "judgements": [judge_row(args, row) for row in rows],
    }
    print(json.dumps(result, ensure_ascii=False, default=str, indent=2))


if __name__ == "__main__":
    main()
