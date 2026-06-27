import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from kira_server.api.routes import router
from kira_server.core.runs import InMemoryRunStore
from kira_server.graph_runtime.runtime import GraphRuntime
from kira_server.memory import MemoryService
from kira_server.safety import PermissionService
from kira_server.providers.config import ProviderConfigStore, load_provider_config
from kira_server.providers.fixture import FixtureProvider
from kira_server.providers.openai_compatible import OpenAICompatibleProvider
from kira_server.project_knowledge import ProjectKnowledgeService
from kira_server.skills.builtin import create_builtin_skill_registry
from kira_server.skills.registry import SkillRegistry
from kira_server.storage.database import RuntimeStorage
from kira_server.transcript import TranscriptService
from kira_server.tooling.registry import create_tool_registry


def create_app(
    fixture_delay_seconds: float = 0.05,
    provider_config: ProviderConfigStore | None = None,
    openai_provider: OpenAICompatibleProvider | None = None,
    skill_registry: SkillRegistry | None = None,
    runtime_storage: RuntimeStorage | None = None,
    frontend_dist: str | Path | None = None,
) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        yield
        app.state.runtime_storage.mark_active_cancelled_for_shutdown()

    app = FastAPI(title="Kira Agent Server", version="0.1.0", lifespan=lifespan)
    app.state.run_store = InMemoryRunStore()
    app.state.fixture_provider = FixtureProvider(delay_seconds=fixture_delay_seconds)
    app.state.openai_provider = openai_provider or OpenAICompatibleProvider()
    app.state.provider_config = provider_config or load_provider_config()
    app.state.tool_registry = create_tool_registry()
    app.state.skill_registry = skill_registry or create_builtin_skill_registry()
    app.state.runtime_storage = runtime_storage or RuntimeStorage.from_env()
    app.state.graph_runtime = GraphRuntime(app.state.tool_registry, runtime_storage=app.state.runtime_storage)
    app.state.project_knowledge = ProjectKnowledgeService(app.state.runtime_storage)
    app.state.memory_service = MemoryService(app.state.runtime_storage)
    app.state.transcript_service = TranscriptService(app.state.runtime_storage)
    app.state.permission_service = PermissionService()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router, prefix="/api")
    configure_frontend_serving(app, frontend_dist)
    return app


def resolve_frontend_dist(frontend_dist: str | Path | None = None) -> Path | None:
    if frontend_dist is not None:
        candidate = Path(frontend_dist).expanduser()
        return candidate.resolve() if (candidate / "index.html").is_file() else None

    configured = os.getenv("KIRA_WEB_DIST")
    if configured:
        candidate = Path(configured).expanduser()
        return candidate.resolve() if (candidate / "index.html").is_file() else None

    repo_dist = Path(__file__).resolve().parents[3] / "web" / "dist"
    return repo_dist.resolve() if (repo_dist / "index.html").is_file() else None


def configure_frontend_serving(app: FastAPI, frontend_dist: str | Path | None = None) -> None:
    dist = resolve_frontend_dist(frontend_dist)
    app.state.frontend_dist = str(dist) if dist else None
    if dist is None:
        return

    index_html = dist / "index.html"
    assets_dir = dist / "assets"
    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="frontend-assets")

    @app.get("/", include_in_schema=False)
    async def frontend_index() -> FileResponse:
        return FileResponse(index_html)

    @app.get("/{full_path:path}", include_in_schema=False)
    async def frontend_fallback(full_path: str) -> FileResponse:
        if full_path == "api" or full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not Found")

        requested = (dist / full_path).resolve()
        try:
            requested.relative_to(dist)
        except ValueError:
            raise HTTPException(status_code=404, detail="Not Found") from None

        if requested.is_file():
            return FileResponse(requested)
        if Path(full_path).suffix:
            raise HTTPException(status_code=404, detail="Not Found")
        return FileResponse(index_html)


app = create_app()
