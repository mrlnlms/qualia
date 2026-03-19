"""Endpoints de saúde, info e cache."""

from fastapi import APIRouter
from fastapi.responses import FileResponse
from pathlib import Path

from qualia.api.deps import get_core, HAS_EXTENSIONS

router = APIRouter()

_frontend_dist_check = Path(__file__).parent.parent.parent / "frontend" / "dist"
_has_frontend = _frontend_dist_check.exists() and (_frontend_dist_check / "index.html").exists()


def _api_info():
    endpoints = {
        "plugins": "/plugins",
        "analyze": "/analyze/{plugin_id}",
        "process": "/process/{plugin_id}",
        "visualize": "/visualize/{plugin_id}",
        "pipeline": "/pipeline",
        "transcribe": "/transcribe/{plugin_id}",
        "health": "/health"
    }
    from qualia.api.deps import HAS_EXTENSIONS
    if HAS_EXTENSIONS:
        endpoints.update({
            "webhooks": "/webhook/{provider}",
            "webhook_stats": "/webhook/stats",
            "monitor": "/monitor/",
            "monitor_stream": "/monitor/stream"
        })
    return {
        "name": "Qualia Core API",
        "version": "0.1.0",
        "description": "REST API for qualitative analysis",
        "endpoints": endpoints,
        "documentation": "/docs"
    }


@router.get("/")
def root():
    """Serve frontend if available, otherwise API info"""
    if _has_frontend:
        return FileResponse(_frontend_dist_check / "index.html")
    return _api_info()


@router.get("/api")
def api_info():
    """API information and available endpoints"""
    return _api_info()


@router.get("/cache/stats")
def cache_stats():
    """Retorna estatísticas do cache (tamanho, hits, misses, evictions)"""
    core = get_core()
    return core.cache.stats()


@router.get("/health")
def health_check():
    """Health check endpoint"""
    core = get_core()
    from qualia.api.deps import HAS_EXTENSIONS
    response = {
        "status": "healthy",
        "plugins_loaded": len(core.registry),
        "plugin_types": {
            "analyzers": len([m for m in core.registry.values() if m.type.value == "analyzer"]),
            "visualizers": len([m for m in core.registry.values() if m.type.value == "visualizer"]),
            "document_processors": len([m for m in core.registry.values() if m.type.value == "document"])
        },
        "extensions": {
            "webhooks": HAS_EXTENSIONS,
            "monitoring": HAS_EXTENSIONS
        }
    }
    if core.discovery_errors:
        response["discovery_errors"] = core.discovery_errors
    return response
