"""Endpoints de análise de texto."""

import json
import hashlib
import asyncio

from fastapi import APIRouter, HTTPException, UploadFile, File, Form

from qualia.api.deps import get_core, track
from qualia.api.schemas import AnalyzeRequest

router = APIRouter()


@router.post("/analyze/{plugin_id}")
async def analyze(plugin_id: str, request: AnalyzeRequest):
    """Execute an analyzer plugin on text"""
    core = get_core()
    try:
        registry = core.get_config_registry()
        if registry and request.config:
            valid, errors = registry.validate_config(plugin_id, request.config)
            if not valid:
                raise HTTPException(
                    status_code=422,
                    detail={"message": "Configuração inválida", "errors": errors}
                )

        doc = core.add_document(f"api_{plugin_id}_{hashlib.md5(request.text.encode()).hexdigest()[:8]}", request.text)
        result = await asyncio.to_thread(core.execute_plugin, plugin_id, doc, request.config, request.context)
        await track(f"/analyze/{plugin_id}", plugin_id)

        return {
            "status": "success",
            "plugin_id": plugin_id,
            "result": result
        }
    except HTTPException:
        raise
    except Exception as e:
        await track(f"/analyze/{plugin_id}", plugin_id, str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/analyze/{plugin_id}/file")
async def analyze_file(
    plugin_id: str,
    file: UploadFile = File(...),
    config: str = Form("{}"),
    context: str = Form("{}")
):
    """Execute an analyzer plugin on uploaded file"""
    core = get_core()
    try:
        config_dict = json.loads(config)
        context_dict = json.loads(context)

        content = await file.read()
        try:
            text = content.decode('utf-8')
        except UnicodeDecodeError:
            try:
                text = content.decode('latin-1')
            except UnicodeDecodeError:
                raise HTTPException(
                    status_code=422,
                    detail="Encoding não suportado. Envie arquivo em UTF-8 ou Latin-1."
                )

        doc = core.add_document(f"api_upload_{file.filename}_{hashlib.md5(text.encode()).hexdigest()[:8]}", text)
        result = await asyncio.to_thread(core.execute_plugin, plugin_id, doc, config_dict, context_dict)
        await track(f"/analyze/{plugin_id}/file", plugin_id)

        return {
            "status": "success",
            "plugin_id": plugin_id,
            "filename": file.filename,
            "result": result
        }
    except HTTPException:
        raise
    except Exception as e:
        await track(f"/analyze/{plugin_id}/file", plugin_id, str(e))
        raise HTTPException(status_code=400, detail=str(e))
