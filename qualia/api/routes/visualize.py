"""Rota de visualização — plugin renderiza, BaseClass serializa."""

import asyncio

from fastapi import APIRouter, HTTPException

from qualia.api.deps import get_core, track, validate_plugin_config, require_plugin_type
from qualia.api.schemas import VisualizeRequest

router = APIRouter()


@router.post("/visualize/{plugin_id}")
async def visualize(plugin_id: str, request: VisualizeRequest):
    """Gera visualização usando plugin especificado.

    Retorna dict com "html" (string HTML) ou "data"+"encoding"+"format" (base64 imagem).
    """
    core = get_core()
    require_plugin_type(core, plugin_id, "visualizer")
    validate_plugin_config(core, plugin_id, request.config)

    config = {**request.config, "output_format": request.output_format or "html"}
    plugin = core.loader.get_plugin(plugin_id)

    try:
        result = await asyncio.wait_for(
            asyncio.to_thread(plugin.render, request.data, config),
            timeout=60.0,
        )
    except asyncio.TimeoutError:
        await track(f"/visualize/{plugin_id}", plugin_id, "timeout")
        raise HTTPException(status_code=504, detail=f"Plugin '{plugin_id}' timed out (60s)")
    except HTTPException:
        raise
    except Exception as e:
        await track(f"/visualize/{plugin_id}", plugin_id, str(e))
        raise HTTPException(status_code=400, detail=str(e))

    await track(f"/visualize/{plugin_id}", plugin_id)

    return {"status": "success", "plugin_id": plugin_id, **result}
