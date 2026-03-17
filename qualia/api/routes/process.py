"""Endpoint de processamento de documentos."""

import hashlib
import asyncio

from fastapi import APIRouter, HTTPException

from qualia.core import Document
from qualia.api.deps import get_core, track
from qualia.api.schemas import ProcessRequest

router = APIRouter()


@router.post("/process/{plugin_id}")
async def process(plugin_id: str, request: ProcessRequest):
    """Execute a document processor plugin"""
    core = get_core()
    try:
        doc = core.add_document(f"api_process_{plugin_id}_{hashlib.md5(request.text.encode()).hexdigest()[:8]}", request.text)
        result = await asyncio.to_thread(core.execute_plugin, plugin_id, doc, request.config)

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
