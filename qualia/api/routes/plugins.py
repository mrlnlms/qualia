"""Endpoints de descoberta de plugins."""

from typing import List, Optional
from fastapi import APIRouter

from qualia.api.deps import get_core
from qualia.api.schemas import PluginInfo, plugin_to_info

router = APIRouter()


@router.get("/plugins", response_model=List[PluginInfo])
def list_plugins(plugin_type: Optional[str] = None):
    """List all available plugins"""
    core = get_core()
    plugins = []
    for plugin_id, meta in core.registry.items():
        if plugin_type and meta.type.value != plugin_type:
            continue
        plugins.append(plugin_to_info(plugin_id))
    return plugins


@router.get("/plugins/{plugin_id}", response_model=PluginInfo)
def get_plugin(plugin_id: str):
    """Get detailed information about a specific plugin"""
    return plugin_to_info(plugin_id)
