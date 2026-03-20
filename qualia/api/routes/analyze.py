"""Endpoints de análise de texto."""

import json
import hashlib
import asyncio
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File, Form

from qualia.api.deps import get_core, track, validate_plugin_config, require_plugin_type, check_upload_size
from qualia.api.schemas import AnalyzeRequest

router = APIRouter()


@router.post("/analyze/{plugin_id}")
async def analyze(plugin_id: str, request: AnalyzeRequest):
    """Execute an analyzer plugin on text"""
    core = get_core()
    require_plugin_type(core, plugin_id, "analyzer")
    try:
        validate_plugin_config(core, plugin_id, request.config)

        doc = core.add_document(f"api_{plugin_id}_{hashlib.md5(request.text.encode()).hexdigest()[:8]}", request.text)
        try:
            result = await asyncio.wait_for(
                asyncio.to_thread(core.execute_plugin, plugin_id, doc, request.config, request.context),
                timeout=60.0
            )
        except asyncio.TimeoutError:
            await track(f"/analyze/{plugin_id}", plugin_id, "timeout")
            raise HTTPException(status_code=504, detail="Plugin execution timed out (60s)")
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
    require_plugin_type(core, plugin_id, "analyzer")

    try:
        config_dict = json.loads(config)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=422, detail=f"Config JSON inválido: {e}")
    if not isinstance(config_dict, dict):
        raise HTTPException(status_code=422, detail="Config deve ser um objeto JSON, não array/string/número")
    try:
        context_dict = json.loads(context)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=422, detail=f"Context JSON inválido: {e}")
    if not isinstance(context_dict, dict):
        raise HTTPException(status_code=422, detail="Context deve ser um objeto JSON, não array/string/número")

    try:
        validate_plugin_config(core, plugin_id, config_dict)

        suffix = Path(file.filename).suffix if file.filename else ""
        upload = await check_upload_size(file, suffix=suffix)
        encoding_used = "utf-8"
        try:
            text = Path(upload.tmp_path).read_text(encoding='utf-8')
        except UnicodeDecodeError:
            text = Path(upload.tmp_path).read_text(encoding='latin-1')
            encoding_used = "latin-1"
        finally:
            Path(upload.tmp_path).unlink(missing_ok=True)

        doc = core.add_document(f"api_upload_{file.filename}_{upload.content_hash}", text)
        try:
            result = await asyncio.wait_for(
                asyncio.to_thread(core.execute_plugin, plugin_id, doc, config_dict, context_dict),
                timeout=60.0
            )
        except asyncio.TimeoutError:
            await track(f"/analyze/{plugin_id}/file", plugin_id, "timeout")
            raise HTTPException(status_code=504, detail="Plugin execution timed out (60s)")
        await track(f"/analyze/{plugin_id}/file", plugin_id)

        response = {
            "status": "success",
            "plugin_id": plugin_id,
            "filename": file.filename,
            "result": result
        }
        if encoding_used != "utf-8":
            response["encoding_warning"] = (
                f"Arquivo decodificado como {encoding_used} (UTF-8 falhou). "
                "Caracteres podem estar incorretos. Reenvie em UTF-8 para garantir fidelidade."
            )
        return response
    except HTTPException:
        raise
    except Exception as e:
        await track(f"/analyze/{plugin_id}/file", plugin_id, str(e))
        raise HTTPException(status_code=400, detail=str(e))
