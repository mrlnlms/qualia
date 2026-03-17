"""Endpoint de visualização."""

import tempfile
import base64
import asyncio
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from qualia.api.deps import get_core, track
from qualia.api.schemas import VisualizeRequest

router = APIRouter()


@router.post("/visualize/{plugin_id}")
async def visualize(plugin_id: str, request: VisualizeRequest):
    """Execute a visualizer plugin"""
    core = get_core()
    try:
        suffix = f".{request.output_format}"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            output_path = Path(tmp.name)

        plugin = core.loader.get_plugin(plugin_id)
        if not plugin:
            raise HTTPException(status_code=404, detail=f"Plugin '{plugin_id}' not found")

        try:
            await asyncio.wait_for(
                asyncio.to_thread(plugin.render, request.data, request.config, output_path),
                timeout=60.0
            )
        except asyncio.TimeoutError:
            output_path.unlink(missing_ok=True)
            raise HTTPException(status_code=504, detail="Visualization timed out after 60s")

        await track(f"/visualize/{plugin_id}", plugin_id)

        if request.output_format in ["png", "svg"]:
            with open(output_path, "rb") as f:
                content = base64.b64encode(f.read()).decode()
            output_path.unlink()
            return {
                "status": "success",
                "plugin_id": plugin_id,
                "format": request.output_format,
                "data": content,
                "encoding": "base64"
            }
        elif request.output_format == "html":
            with open(output_path, "r", encoding="utf-8") as f:
                content = f.read()
            output_path.unlink()
            return {
                "status": "success",
                "plugin_id": plugin_id,
                "format": "html",
                "data": content,
                "encoding": "utf-8"
            }
        else:
            return FileResponse(
                output_path,
                media_type=f"application/{request.output_format}",
                filename=f"visualization.{request.output_format}"
            )

    except HTTPException:
        raise
    except Exception as e:
        await track(f"/visualize/{plugin_id}", plugin_id, str(e))
        raise HTTPException(status_code=400, detail=str(e))
