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


@router.get("/plugins/{plugin_id}", response_model=PluginInfo)
async def get_plugin(plugin_id: str):
    """Get detailed information about a specific plugin"""
    result = plugin_to_info(plugin_id)
    await track(f"/plugins/{plugin_id}", plugin_id)
    return result
