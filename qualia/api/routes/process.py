"""Endpoint de processamento de documentos."""

import hashlib
import asyncio

from fastapi import APIRouter, HTTPException

from qualia.core import Document
from qualia.api.deps import get_core, track, validate_plugin_config, require_plugin_type
from qualia.api.schemas import ProcessRequest

router = APIRouter()


@router.post("/process/{plugin_id}")
async def process(plugin_id: str, request: ProcessRequest):
    """Execute a document processor plugin"""
    core = get_core()
    require_plugin_type(core, plugin_id, "document")
    try:
        validate_plugin_config(core, plugin_id, request.config)

        doc = core.add_document(f"api_process_{plugin_id}_{hashlib.md5(request.text.encode()).hexdigest()[:8]}", request.text)
        try:
            result = await asyncio.wait_for(
                asyncio.to_thread(core.execute_plugin, plugin_id, doc, request.config, request.context),
                timeout=60.0
            )
        except asyncio.TimeoutError:
            await track(f"/process/{plugin_id}", plugin_id, "timeout")
            raise HTTPException(status_code=504, detail="Plugin execution timed out (60s)")

        if isinstance(result, Document):
            result = result.content

        await track(f"/process/{plugin_id}", plugin_id)

        return {
            "status": "success",
            "plugin_id": plugin_id,
            "processed_text": result
        }
    except HTTPException:
        raise
    except Exception as e:
        await track(f"/process/{plugin_id}", plugin_id, str(e))
        raise HTTPException(status_code=400, detail=str(e))
