"""Endpoints de descoberta de plugins."""

from typing import List, Optional
from fastapi import APIRouter

from qualia.api.deps import get_core, track
from qualia.api.schemas import PluginInfo, plugin_to_info

router = APIRouter()


@router.get("/plugins", response_model=List[PluginInfo])
async def list_plugins(plugin_type: Optional[str] = None):
    """List all available plugins"""
    core = get_core()
    plugins = []
    for plugin_id, meta in core.registry.items():
        if plugin_type and meta.type.value != plugin_type:
            continue
        plugins.append(plugin_to_info(plugin_id))
    await track("/plugins", "list")
    return plugins


@router.get("/plugins/health")
def plugins_health():
    """Status individual por plugin — loaded/pending, eager/lazy."""
    core = get_core()
    plugins_status = []
    for plugin_id, meta in core.registry.items():
        is_loaded = plugin_id in core.loader.loaded_plugins
        cls = core.loader._plugin_classes.get(plugin_id)
        needs_eager = (
            getattr(cls, 'EAGER_LOAD', None) is True
            or (cls is not None and '__init__' in cls.__dict__)
        )
        plugins_status.append({
            "id": plugin_id,
            "name": meta.name,
            "type": meta.type.value,
            "status": "loaded" if is_loaded else "pending",
            "loading": "eager" if needs_eager else "lazy",
        })

    response = {
        "status": "healthy",
        "total": len(core.registry),
        "plugins": plugins_status,
    }
    if core.discovery_errors:
        response["errors"] = core.discovery_errors
        response["status"] = "degraded"
    return response


@router.get("/plugins/{plugin_id}", response_model=PluginInfo)
async def get_plugin(plugin_id: str):
    """Get detailed information about a specific plugin"""
    result = plugin_to_info(plugin_id)
    await track(f"/plugins/{plugin_id}", plugin_id)
    return result
