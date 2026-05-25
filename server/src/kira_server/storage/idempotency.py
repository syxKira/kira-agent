from __future__ import annotations

import hashlib
import json
from typing import Any


def args_hash(arguments: dict[str, Any]) -> str:
    encoded = json.dumps(arguments, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def idempotency_key(
    *,
    thread_id: str,
    checkpoint_id: str,
    node_name: str,
    call_index: int,
    tool_name: str,
    arguments: dict[str, Any],
) -> str:
    raw = "|".join(
        [
            thread_id,
            checkpoint_id,
            node_name,
            str(call_index),
            tool_name,
            args_hash(arguments),
        ]
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
