import logging
from typing import Literal

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.agent.llm import LLM, build_llm
from app.api import chat, clusterings, datasets
from app.config import Settings, get_settings
from app.services import Services
from app.store import Store

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
for noisy in ("httpx", "google_genai"):
    logging.getLogger(noisy).setLevel(logging.WARNING)


def create_app(settings: Settings | None = None, llm: LLM | None | Literal["auto"] = "auto") -> FastAPI:
    settings = settings or get_settings()
    services = Services(
        settings=settings,
        store=Store(settings.workspace_dir),
        llm=build_llm(settings) if llm == "auto" else llm,
    )

    app = FastAPI(
        title="ClusterChat API",
        version="0.1.0",
        description="Sube tu base de clientes, segmenta con clustering y conversa con los clusters.",
    )
    app.state.services = services
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(datasets.router)
    app.include_router(clusterings.router)
    app.include_router(chat.router)

    @app.get("/health", tags=["meta"])
    def health() -> dict:
        return {"status": "ok", "llm": services.llm is not None, "model": settings.gemini_model}

    return app


app = create_app()
