"""FastAPI application for the Godot RAG web UI."""

from __future__ import annotations

import argparse
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from web.api.routes.chat import router as chat_router
from web.api.schemas import HealthResponse, ModelInfo, ModelsResponse

ROOT = Path(__file__).resolve().parent.parent.parent
UI_DIR = ROOT / "web" / "ui"
UI_DIST = UI_DIR / "dist"

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


def run_prod(host: str = "127.0.0.1", port: int = 8000) -> None:
    """Serve the built UI and API from a single server."""
    if not UI_DIST.is_dir():
        print(
            "Web UI not built. Run once:\n"
            "  cd web/ui && npm install && npm run build\n"
            "Or use dev mode with hot reload:\n"
            "  godot-web --dev",
            file=sys.stderr,
        )
        sys.exit(1)
    uvicorn.run("web.api.main:app", host=host, port=port, reload=False)


def run_dev(host: str = "127.0.0.1", port: int = 8000) -> None:
    """Start API + Vite dev server in one terminal (UI hot reload)."""
    if not (UI_DIR / "node_modules").is_dir():
        print(
            "Frontend dependencies missing. Run once:\n"
            "  cd web/ui && npm install",
            file=sys.stderr,
        )
        sys.exit(1)

    npm = shutil.which("npm")
    if not npm:
        print("npm not found. Install Node.js to use --dev mode.", file=sys.stderr)
        sys.exit(1)

    procs: list[subprocess.Popen[bytes]] = []

    def shutdown(*_args: object) -> None:
        for proc in procs:
            if proc.poll() is None:
                proc.terminate()
        for proc in procs:
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, shutdown)

    api = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "web.api.main:app",
            "--host",
            host,
            "--port",
            str(port),
            "--reload",
        ],
        cwd=ROOT,
    )
    procs.append(api)
    time.sleep(0.5)

    vite = subprocess.Popen([npm, "run", "dev"], cwd=UI_DIR)
    procs.append(vite)

    print("Godot RAG web UI (dev)")
    print("  UI:  http://localhost:5173")
    print(f"  API: http://{host}:{port}")
    print("Press Ctrl+C to stop.\n")

    try:
        while True:
            for proc in procs:
                if proc.poll() is not None:
                    shutdown()
            time.sleep(0.5)
    except KeyboardInterrupt:
        shutdown()


def run(argv: list[str] | None = None) -> None:
    """CLI entry point for godot-web."""
    parser = argparse.ArgumentParser(
        prog="godot-web",
        description="Run the Godot RAG web chat UI.",
    )
    parser.add_argument(
        "--dev",
        action="store_true",
        help="Dev mode: start API + Vite with hot reload (single terminal)",
    )
    parser.add_argument("--host", default="127.0.0.1", help="API bind host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="API port (default: 8000)")
    args = parser.parse_args(argv)

    if args.dev:
        run_dev(host=args.host, port=args.port)
    else:
        run_prod(host=args.host, port=args.port)


if __name__ == "__main__":
    run()
