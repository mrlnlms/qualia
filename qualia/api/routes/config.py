"""Endpoints de configuração e schema."""

from fastapi import APIRouter, HTTPException

from qualia.api.deps import get_core
from qualia.api.schemas import ConfigResolveRequest

router = APIRouter()


@router.get("/plugins/{plugin_id}/schema")
def get_plugin_schema(plugin_id: str):
    """Get normalized schema for a plugin"""
    core = get_core()
    registry = core.get_config_registry()
    if not registry:
        raise HTTPException(status_code=503, detail="ConfigurationRegistry not initialized")

    schema = registry.get_plugin_schema(plugin_id)
    if not schema:
        raise HTTPException(status_code=404, detail=f"Plugin '{plugin_id}' not found")

    return schema


@router.get("/config/consolidated")
def get_consolidated_config():
    """Get consolidated view of all schemas and text_size rules"""
    core = get_core()
    registry = core.get_config_registry()
    if not registry:
        raise HTTPException(status_code=503, detail="ConfigurationRegistry not initialized")

    return registry.get_consolidated_view()


@router.post("/config/resolve")
def resolve_config(request: ConfigResolveRequest):
    """Resolve final config for a plugin with text_size cascade"""
    core = get_core()
    registry = core.get_config_registry()
    if not registry:
        raise HTTPException(status_code=503, detail="ConfigurationRegistry not initialized")

    if not registry.get_plugin_schema(request.plugin_id):
        raise HTTPException(status_code=404, detail=f"Plugin '{request.plugin_id}' not found")

    config = registry.get_config_for_plugin(
        request.plugin_id,
        text_size=request.text_size,
    )

    return {
        "plugin_id": request.plugin_id,
        "text_size": request.text_size,
        "resolved_config": config,
    }
