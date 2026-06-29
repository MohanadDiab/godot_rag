"""FastAPI application for the Godot RAG web UI."""

from __future__ import annotations

from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from web.api.routes.chat import router as chat_router
from web.api.schemas import HealthResponse, ModelInfo, ModelsResponse

ROOT = Path(__file__).resolve().parent.parent.parent
UI_DIST = ROOT / "web" / "ui" / "dist"

PRESET_MODELS = [
    ModelInfo(id="gpt-5-nano", label="gpt-5-nano"),
    ModelInfo(id="gpt-4o-mini", label="gpt-4o-mini"),
    ModelInfo(id="gpt-4o", label="gpt-4o"),
    ModelInfo(id="custom", label="Custom (enter below)"),
]

app = FastAPI(title="Godot RAG", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
        "http://127.0.0.1:8000",
        "http://localhost:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)


@app.get("/api/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse()


@app.get("/api/models", response_model=ModelsResponse)
async def models() -> ModelsResponse:
    return ModelsResponse(models=PRESET_MODELS)


if UI_DIST.is_dir():
    assets_dir = UI_DIST / "assets"
    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str) -> FileResponse:
        if full_path.startswith("api/"):
            from fastapi import HTTPException

            raise HTTPException(status_code=404)
        file_path = UI_DIST / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(UI_DIST / "index.html")


def run() -> None:
    """CLI entry point for godot-web."""
    uvicorn.run(
        "web.api.main:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
    )


if __name__ == "__main__":
    run()
