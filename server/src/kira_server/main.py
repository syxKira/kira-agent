from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
    return app


app = create_app()
