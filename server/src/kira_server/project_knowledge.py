from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from kira_server.context import Citation, ContextItem, estimate_budget_cost, make_context_id
from kira_server.storage.database import RuntimeStorage, utc_now
from kira_server.tooling.policy import (
    MAX_FILE_BYTES,
    MAX_PREVIEW_CHARS,
    ProjectRootResolver,
    file_metadata,
    is_binary_file,
    is_ignored_path,
    iter_project_files,
    load_gitignore_patterns,
)
from kira_server.tooling.project_files import read_project_file_tool, search_project_files_tool


INDEX_VERSION = "stage06-v1"
DEFAULT_MAX_FILES = 1_000
DEFAULT_MAX_BYTES = 8_000_000
CHUNK_LINES = 80
MAX_LIVE_QUERY_TERMS = 8
TERM_RE = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_.:/-]{1,}|[\u4e00-\u9fff]{2,}")
CJK_STOP_TERMS = {
    "一个",
    "一条",
    "一下",
    "帮我",
    "请帮",
    "根据",
    "当前",
    "项目",
    "文档",
    "信息",
    "查看",
    "支持",
    "能力",
    "生成",
    "输出",
    "发送",
}


class ProjectIndexRefreshRequest(BaseModel):
    root: str | None = None
    max_files: int = Field(default=DEFAULT_MAX_FILES, ge=1, le=20_000)
    max_bytes: int = Field(default=DEFAULT_MAX_BYTES, ge=1_000, le=100_000_000)


class ProjectSearchRequest(BaseModel):
    query: str = Field(min_length=1)
    root: str | None = None
    limit: int = Field(default=10, ge=1, le=50)
    glob: str | None = None


@dataclass(frozen=True)
class RefreshStats:
    root_id: str
    root: str
    files_indexed: int
    chunks_indexed: int
    skipped_count: int
    omitted_count: int
    last_refresh_at: str
    fts_available: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "root_id": self.root_id,
            "root": self.root,
            "status": "ready",
            "file_count": self.files_indexed,
            "chunk_count": self.chunks_indexed,
            "skipped_count": self.skipped_count,
            "omitted_count": self.omitted_count,
            "last_refresh_at": self.last_refresh_at,
            "fts_available": self.fts_available,
        }


class ProjectKnowledgeService:
    def __init__(self, storage: RuntimeStorage, resolver: ProjectRootResolver | None = None) -> None:
        self.storage = storage
        self.resolver = resolver or ProjectRootResolver()

    def status(self, root: str | None = None) -> dict[str, Any]:
        resolved, error = self.resolver.resolve_root(root)
        if error is not None or resolved is None:
            return {"status": "error", "error": error}
        with self.storage.database.connect() as conn:
            row = conn.execute("SELECT * FROM project_roots WHERE root_id = ?", (resolved.root_id,)).fetchone()
        if row is None:
            return {
                "root_id": resolved.root_id,
                "root": str(resolved.path),
                "status": "not_indexed",
                "file_count": 0,
                "chunk_count": 0,
                "skipped_count": 0,
                "omitted_count": 0,
                "last_refresh_at": None,
                "fts_available": self._fts_available(),
            }
        return {
            "root_id": row["root_id"],
            "root": row["root_path"],
            "status": row["status"],
            "file_count": row["file_count"],
            "chunk_count": row["chunk_count"],
            "skipped_count": row["skipped_count"],
            "omitted_count": row["omitted_count"],
            "last_refresh_at": row["last_refresh_at"],
            "fts_available": self._fts_available(),
            "metadata": _loads(row["metadata_json"]) or {},
        }

    def refresh(self, request: ProjectIndexRefreshRequest) -> dict[str, Any]:
        resolved, error = self.resolver.resolve_root(request.root)
        if error is not None or resolved is None:
            return {"status": "error", "error": error}

        indexed_files = 0
        indexed_chunks = 0
        skipped = 0
        omitted = 0
        consumed_bytes = 0
        now = utc_now()
        fts_available = self._fts_available()
        patterns = load_gitignore_patterns(resolved.path)
        rows: list[dict[str, Any]] = []
        chunks: list[dict[str, Any]] = []

        for path, relative in iter_project_files(resolved):
            if indexed_files >= request.max_files or consumed_bytes >= request.max_bytes:
                omitted += 1
                continue
            try:
                path.resolve(strict=True).relative_to(resolved.path)
            except (FileNotFoundError, ValueError):
                rows.append(
                    {
                        "root_id": resolved.root_id,
                        "path": relative.as_posix(),
                        "size": 0,
                        "mtime": 0,
                        "content_hash": None,
                        "skipped_reason": "path_outside_root",
                        "indexed_at": now,
                    }
                )
                skipped += 1
                continue
            if is_ignored_path(relative, patterns):
                skipped += 1
                continue
            try:
                stat = path.stat()
            except OSError:
                skipped += 1
                continue
            if stat.st_size > MAX_FILE_BYTES:
                rows.append(_file_row(resolved.root_id, path, relative, "file_too_large", now))
                skipped += 1
                continue
            if is_binary_file(path):
                rows.append(_file_row(resolved.root_id, path, relative, "binary_file", now))
                skipped += 1
                continue
            content = path.read_text(encoding="utf-8", errors="replace")
            metadata = file_metadata(resolved, path, relative)
            rows.append(_file_row(resolved.root_id, path, relative, None, now, metadata))
            for chunk in _chunk_file(resolved.root_id, relative, content, metadata.get("content_hash"), now):
                chunks.append(chunk)
            indexed_files += 1
            indexed_chunks = len(chunks)
            consumed_bytes += stat.st_size

        with self.storage.database.connect() as conn:
            conn.execute("DELETE FROM project_files WHERE root_id = ?", (resolved.root_id,))
            conn.execute("DELETE FROM project_chunks WHERE root_id = ?", (resolved.root_id,))
            for row in rows:
                conn.execute(
                    """
                    INSERT INTO project_files(root_id, path, size, mtime, content_hash, skipped_reason, indexed_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (row["root_id"], row["path"], row["size"], row["mtime"], row["content_hash"], row["skipped_reason"], row["indexed_at"]),
                )
            for chunk in chunks:
                conn.execute(
                    """
                    INSERT INTO project_chunks(chunk_id, root_id, path, start_line, end_line, start_byte, end_byte, content_hash, language, content, indexed_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        chunk["chunk_id"],
                        chunk["root_id"],
                        chunk["path"],
                        chunk["start_line"],
                        chunk["end_line"],
                        chunk["start_byte"],
                        chunk["end_byte"],
                        chunk["content_hash"],
                        chunk["language"],
                        chunk["content"],
                        chunk["indexed_at"],
                    ),
                )
            if fts_available:
                conn.execute(
                    "CREATE VIRTUAL TABLE IF NOT EXISTS project_chunks_fts USING fts5(chunk_id UNINDEXED, root_id UNINDEXED, path UNINDEXED, content)"
                )
                conn.execute("DELETE FROM project_chunks_fts WHERE root_id = ?", (resolved.root_id,))
                for chunk in chunks:
                    conn.execute(
                        "INSERT INTO project_chunks_fts(chunk_id, root_id, path, content) VALUES (?, ?, ?, ?)",
                        (chunk["chunk_id"], chunk["root_id"], chunk["path"], chunk["content"]),
                    )
            conn.execute(
                """
                INSERT INTO project_roots(root_id, root_path, status, file_count, chunk_count, skipped_count, omitted_count, last_refresh_at, metadata_json)
                VALUES (?, ?, 'ready', ?, ?, ?, ?, ?, ?)
                ON CONFLICT(root_id) DO UPDATE SET
                  root_path=excluded.root_path,
                  status='ready',
                  file_count=excluded.file_count,
                  chunk_count=excluded.chunk_count,
                  skipped_count=excluded.skipped_count,
                  omitted_count=excluded.omitted_count,
                  last_refresh_at=excluded.last_refresh_at,
                  metadata_json=excluded.metadata_json
                """,
                (resolved.root_id, str(resolved.path), indexed_files, indexed_chunks, skipped, omitted, now, json.dumps({"index_version": INDEX_VERSION}, sort_keys=True)),
            )

        return RefreshStats(resolved.root_id, str(resolved.path), indexed_files, indexed_chunks, skipped, omitted, now, fts_available).as_dict()

    def search(self, request: ProjectSearchRequest, *, thread_id: str | None = None, skill_hints: list[str] | None = None) -> dict[str, Any]:
        resolved, error = self.resolver.resolve_root(request.root)
        if error is not None or resolved is None:
            return {"status": "error", "error": error, "results": []}
        indexed = self._indexed_candidates(resolved.root_id, request.query, request.limit * 4, skill_hints or [])
        live = self._live_candidates(request, resolved.root_id)
        merged = _rank_candidates([*indexed, *live], request.query, request.limit)
        results = [self._with_stale(candidate, resolved.path) for candidate in merged[: request.limit]]
        omitted = max(len(indexed) + len(live) - len(results), 0)
        response = {
            "root_id": resolved.root_id,
            "root": str(resolved.path),
            "query": request.query,
            "results": results,
            "omitted_count": omitted,
            "truncated": omitted > 0,
            "used_index": bool(indexed),
            "used_live": bool(live),
        }
        with self.storage.database.connect() as conn:
            conn.execute(
                "INSERT INTO retrieval_traces(thread_id, root_id, query, results_json, created_at) VALUES (?, ?, ?, ?, ?)",
                (thread_id, resolved.root_id, request.query, json.dumps(results, ensure_ascii=False, sort_keys=True), utc_now()),
            )
        return response

    def read_file(self, path: str, root: str | None = None, *, limit: int = 20_000) -> dict[str, Any]:
        result = read_project_file_tool(path=path, root=root, limit=limit, resolver=self.resolver)
        if not result.get("ok"):
            return result
        metadata = result.get("metadata") or {}
        citation = {
            "root_id": metadata.get("root_id"),
            "path": metadata.get("path"),
            "start_line": metadata.get("start_line"),
            "end_line": metadata.get("end_line"),
            "content_hash": metadata.get("content_hash"),
            "stale": False,
        }
        result["citation"] = citation
        return result

    def context_items_for_query(self, query: str, root: str | None, *, limit: int = 5, thread_id: str | None = None) -> tuple[list[ContextItem], dict[str, Any]]:
        response = self.search(ProjectSearchRequest(query=query, root=root, limit=limit), thread_id=thread_id)
        items = [context_item_from_result(result, query) for result in response.get("results", [])]
        return items, {key: response.get(key) for key in ("root_id", "root", "query", "omitted_count", "truncated", "used_index", "used_live")}

    def _indexed_candidates(self, root_id: str, query: str, limit: int, skill_hints: list[str]) -> list[dict[str, Any]]:
        terms = _terms(query)
        if not terms:
            return []
        fts_rows = self._fts_candidates(root_id, query, limit)
        if fts_rows:
            return [self._candidate_from_row(row, query, skill_hints, source="fts") for row in fts_rows]
        like = f"%{terms[0]}%"
        with self.storage.database.connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM project_chunks
                WHERE root_id = ? AND lower(content) LIKE ?
                ORDER BY path, start_line
                LIMIT ?
                """,
                (root_id, like.lower(), limit),
            ).fetchall()
        return [self._candidate_from_row(row, query, skill_hints, source="index") for row in rows]

    def _fts_candidates(self, root_id: str, query: str, limit: int):
        if not self._fts_available():
            return []
        try:
            with self.storage.database.connect() as conn:
                return conn.execute(
                    """
                    SELECT c.*
                    FROM project_chunks_fts f
                    JOIN project_chunks c ON c.chunk_id = f.chunk_id
                    WHERE f.root_id = ? AND project_chunks_fts MATCH ?
                    ORDER BY rank
                    LIMIT ?
                    """,
                    (root_id, _fts_query(query), limit),
                ).fetchall()
        except Exception:
            return []

    def _candidate_from_row(self, row, query: str, skill_hints: list[str], *, source: str) -> dict[str, Any]:
        content = row["content"]
        return {
            "source": source,
            "path": row["path"],
            "snippet": _snippet(content, query),
            "start_line": row["start_line"],
            "end_line": row["end_line"],
            "chunk_id": row["chunk_id"],
            "content_hash": row["content_hash"],
            "indexed_at": row["indexed_at"],
            "score": _score(row["path"], content, query, skill_hints) + (1 if source == "fts" else 0),
            "stale": False,
        }

    def _live_candidates(self, request: ProjectSearchRequest, root_id: str) -> list[dict[str, Any]]:
        candidates = []
        for live_query in _candidate_queries(request.query):
            live = search_project_files_tool(query=live_query, root=request.root, glob=request.glob, limit=request.limit, resolver=self.resolver)
            if not live.get("ok"):
                continue
            for match in (live.get("data") or {}).get("matches", []):
                candidates.append(
                    {
                        "source": "live",
                        "path": match["path"],
                        "snippet": match["preview"][:MAX_PREVIEW_CHARS],
                        "start_line": match["line"],
                        "end_line": match["line"],
                        "chunk_id": None,
                        "content_hash": None,
                        "indexed_at": None,
                        "matched_query": live_query,
                        "score": _score(match["path"], match["preview"], request.query, []) + _match_bonus(match["preview"], live_query),
                        "stale": False,
                        "root_id": root_id,
                    }
                )
        return candidates

    def _with_stale(self, candidate: dict[str, Any], root_path: Path) -> dict[str, Any]:
        if candidate.get("source") in {"index", "fts"}:
            path = root_path / candidate["path"]
            current_hash = None
            if path.is_file() and path.stat().st_size <= MAX_FILE_BYTES and not is_binary_file(path):
                current_hash = hashlib.sha256(path.read_bytes()).hexdigest()
            candidate["stale"] = bool(current_hash and candidate.get("content_hash") and current_hash != candidate["content_hash"])
        candidate["citation"] = {
            "root_id": candidate.get("root_id") or hashlib.sha256(str(root_path).encode("utf-8")).hexdigest()[:16],
            "path": candidate["path"],
            "start_line": candidate.get("start_line"),
            "end_line": candidate.get("end_line"),
            "chunk_id": candidate.get("chunk_id"),
            "content_hash": candidate.get("content_hash"),
            "indexed_at": candidate.get("indexed_at"),
            "stale": candidate.get("stale", False),
        }
        return candidate

    def _fts_available(self) -> bool:
        with self.storage.database.connect() as conn:
            try:
                conn.execute("CREATE VIRTUAL TABLE IF NOT EXISTS project_chunks_fts_probe USING fts5(content)")
                conn.execute("DROP TABLE IF EXISTS project_chunks_fts_probe")
                return True
            except Exception:
                return False


def context_item_from_result(result: dict[str, Any], query: str) -> ContextItem:
    citation = Citation(**{**result["citation"], "query": query})
    text = result.get("snippet") or ""
    item = ContextItem(
        id=make_context_id("project", result.get("path"), result.get("chunk_id"), text),
        kind="project_search",
        text=text,
        metadata={"source": "project_retrieval", "path": result.get("path"), "query": query},
        trust="untrusted_project",
        budget_cost=estimate_budget_cost(text),
        citations=[citation],
    )
    return item


def _file_row(root_id: str, path: Path, relative: Path, skipped_reason: str | None, indexed_at: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    stat = path.stat()
    return {
        "root_id": root_id,
        "path": relative.as_posix(),
        "size": stat.st_size,
        "mtime": stat.st_mtime,
        "content_hash": (metadata or {}).get("content_hash"),
        "skipped_reason": skipped_reason,
        "indexed_at": indexed_at,
    }


def _chunk_file(root_id: str, relative: Path, content: str, content_hash: str | None, indexed_at: str) -> list[dict[str, Any]]:
    lines = content.splitlines()
    chunks = []
    cursor = 0
    for start_index in range(0, len(lines) or 1, CHUNK_LINES):
        selected = lines[start_index : start_index + CHUNK_LINES]
        text = "\n".join(selected)
        start_line = start_index + 1
        end_line = start_index + max(len(selected), 1)
        start_byte = len("\n".join(lines[:start_index]).encode("utf-8"))
        end_byte = start_byte + len(text.encode("utf-8"))
        chunk_id = stable_chunk_id(root_id, relative.as_posix(), start_line, end_line, content_hash or "", INDEX_VERSION)
        chunks.append(
            {
                "chunk_id": chunk_id,
                "root_id": root_id,
                "path": relative.as_posix(),
                "start_line": start_line,
                "end_line": end_line,
                "start_byte": start_byte,
                "end_byte": end_byte,
                "content_hash": content_hash,
                "language": relative.suffix.lstrip(".") or None,
                "content": text,
                "indexed_at": indexed_at,
            }
        )
        cursor = end_byte
    return chunks


def stable_chunk_id(root_id: str, path: str, start_line: int, end_line: int, content_hash: str, version: str = INDEX_VERSION) -> str:
    digest = hashlib.sha256(f"{version}|{root_id}|{path}|{start_line}|{end_line}|{content_hash}".encode("utf-8")).hexdigest()[:24]
    return f"chk_{digest}"


def _candidate_queries(query: str) -> list[str]:
    stripped = query.strip()
    queries = [stripped] if stripped else []
    terms = sorted(_terms(query), key=lambda term: (0 if _has_code_character(term) else 1, -len(term), term))
    for term in terms:
        if term not in queries:
            queries.append(term)
        if len(queries) >= MAX_LIVE_QUERY_TERMS + 1:
            break
    return queries


def _terms(query: str) -> list[str]:
    terms: list[str] = []
    for part in query.split():
        _append_term(terms, part)
    for match in TERM_RE.findall(query):
        _append_term(terms, match)
        if _is_cjk(match) and len(match) > 4:
            for width in (4, 3, 2):
                for index in range(0, len(match) - width + 1):
                    _append_term(terms, match[index : index + width])
    return terms


def _append_term(terms: list[str], raw: str) -> None:
    term = raw.strip().strip(".,;:!?，。；：！？、()[]{}<>\"'`").lower()
    if len(term) < 2 or term in CJK_STOP_TERMS or term in terms:
        return
    terms.append(term)


def _is_cjk(term: str) -> bool:
    return bool(term) and all("\u4e00" <= char <= "\u9fff" for char in term)


def _has_code_character(term: str) -> bool:
    return any(char.isascii() and (char.isalnum() or char in "_./:-") for char in term)


def _match_bonus(text: str, query: str) -> float:
    return 2.0 if query.lower() in text.lower() else 0.0


def _fts_query(query: str) -> str:
    terms = [term.replace('"', "") for term in _terms(query)]
    return " OR ".join(f'"{term}"' for term in terms) or '""'


def _score(path: str, text: str, query: str, skill_hints: list[str]) -> float:
    lowered = text.lower()
    path_lower = path.lower()
    terms = _terms(query)
    score = sum(lowered.count(term) * 2 + path_lower.count(term) for term in terms)
    score += sum(3 for hint in skill_hints if hint and hint.lower() in path_lower)
    return float(score)


def _rank_candidates(candidates: list[dict[str, Any]], query: str, limit: int) -> list[dict[str, Any]]:
    deduped: dict[tuple[str, int | None, str], dict[str, Any]] = {}
    for candidate in candidates:
        key = (candidate["path"], candidate.get("start_line"), candidate.get("snippet", ""))
        previous = deduped.get(key)
        if previous is None or candidate.get("score", 0) > previous.get("score", 0):
            deduped[key] = candidate
    return sorted(deduped.values(), key=lambda item: (-float(item.get("score", 0)), item["path"], item.get("start_line") or 0))[:limit]


def _snippet(content: str, query: str) -> str:
    lowered = content.lower()
    index = min((lowered.find(term) for term in _terms(query) if term in lowered), default=0)
    start = max(index - 120, 0)
    end = min(index + MAX_PREVIEW_CHARS, len(content))
    return content[start:end].strip()


def _loads(value: str | None) -> Any:
    return json.loads(value) if value else None
