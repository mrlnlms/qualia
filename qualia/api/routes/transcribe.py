"""Endpoint de transcrição de áudio/vídeo."""

import json
import hashlib
import asyncio
import tempfile
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File, Form

from qualia.api.deps import get_core, track

router = APIRouter()


@router.post("/transcribe/{plugin_id}")
async def transcribe(
    plugin_id: str,
    file: UploadFile = File(...),
    config: str = Form("{}"),
):
    """Transcribe an audio/video file using a document plugin.

    Receives file via multipart/form-data, saves to temp,
    passes path via document metadata to the plugin.
    """
    core = get_core()

    try:
        config_dict = json.loads(config)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=422, detail=f"Config JSON inválido: {e}")

    plugin = core.loader.get_plugin(plugin_id)
    if not plugin:
        raise HTTPException(status_code=404, detail=f"Plugin '{plugin_id}' not found")

    registry = core.get_config_registry()
    if registry and config_dict:
        valid, errors = registry.validate_config(plugin_id, config_dict)
        if not valid:
            raise HTTPException(
                status_code=422,
                detail={"message": "Configuração inválida", "errors": errors}
            )

    suffix = Path(file.filename).suffix if file.filename else ""
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        doc = core.add_document(
            f"api_transcribe_{file.filename}_{hashlib.md5(content).hexdigest()[:8]}",
            "",
        )
        doc.metadata["file_path"] = tmp_path
        doc.metadata["original_filename"] = file.filename
        doc.metadata["file_size"] = len(content)

        result = await asyncio.to_thread(core.execute_plugin, plugin_id, doc, config_dict)
        await track(f"/transcribe/{plugin_id}", plugin_id)

        return {
            "status": "success",
            "plugin_id": plugin_id,
            "filename": file.filename,
            "result": result,
        }
    except HTTPException:
        raise
    except Exception as e:
        await track(f"/transcribe/{plugin_id}", plugin_id, str(e))
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        Path(tmp_path).unlink(missing_ok=True)
