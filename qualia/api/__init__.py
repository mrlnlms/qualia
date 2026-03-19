"""
Qualia Core REST API

Fachada mínima: cria app, monta routers, serve SPA.
Lógica de endpoints em qualia/api/routes/.
"""

from dotenv import load_dotenv
load_dotenv()

import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pathlib import Path

from qualia.core import QualiaCore
from qualia.api.deps import set_core, set_extensions

# App
app = FastAPI(
    title="Qualia Core API",
    description="REST API for Qualia Core - Análise Qualitativa Framework",
    version="0.2.0-beta"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Core singleton
core = QualiaCore()
set_core(core)

# Extensions (opcionais)
try:
    from qualia.api.webhooks import router as webhook_router, init_webhooks, set_tracking_callback
    from qualia.api.monitor import router as monitor_router, track_webhook
    set_extensions(True)
    init_webhooks(core)
    set_tracking_callback(track_webhook)
    app.include_router(webhook_router)
    app.include_router(monitor_router)
except ImportError:
    logging.getLogger("qualia.api").info(
        "Extensions (webhooks, monitor) não disponíveis — dependências opcionais não instaladas"
    )

# Rotas
from qualia.api.routes.health import router as health_router
from qualia.api.routes.plugins import router as plugins_router
from qualia.api.routes.analyze import router as analyze_router
from qualia.api.routes.process import router as process_router
from qualia.api.routes.visualize import router as visualize_router
from qualia.api.routes.pipeline import router as pipeline_router
from qualia.api.routes.config import router as config_router
from qualia.api.routes.transcribe import router as transcribe_router

app.include_router(health_router)
app.include_router(plugins_router)
app.include_router(analyze_router)
app.include_router(process_router)
app.include_router(visualize_router)
app.include_router(pipeline_router)
app.include_router(config_router)
app.include_router(transcribe_router)


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    if isinstance(exc.detail, dict):
        content = {"status": "error", **exc.detail}
    else:
        content = {"status": "error", "message": exc.detail}
    return JSONResponse(status_code=exc.status_code, content=content)

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logging.getLogger("qualia.api").error("Unhandled exception: %s", exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"status": "error", "message": "Internal server error"}
    )


# SPA catch-all (DEVE ser último — após todas as rotas)
from fastapi.staticfiles import StaticFiles

_frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
if _frontend_dist.exists():
    from fastapi.responses import FileResponse
    _assets_dir = _frontend_dist / "assets"
    if _assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=_assets_dir), name="frontend-assets")

    @app.get("/{path:path}")
    async def serve_spa(path: str):
        index = _frontend_dist / "index.html"
        if index.exists():
            return FileResponse(index)
        raise HTTPException(status_code=404)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
