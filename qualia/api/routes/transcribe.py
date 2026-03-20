"""Endpoint de transcrição de áudio/vídeo."""

import json
import asyncio
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File, Form

from qualia.api.deps import get_core, track, validate_plugin_config, require_plugin_type, check_upload_size

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
    if not isinstance(config_dict, dict):
        raise HTTPException(status_code=422, detail="Config deve ser um objeto JSON, não array/string/número")

    require_plugin_type(core, plugin_id, "document")

    # Validar que o plugin é de transcrição (não qualquer document plugin)
    meta = core.registry.get(plugin_id)
    if meta and "transcription" not in meta.provides and "transcription" not in plugin_id:
        raise HTTPException(
            status_code=422,
            detail=f"Plugin '{plugin_id}' é document mas não é de transcrição. "
                   f"Use POST /process/{plugin_id} para processamento de documentos.",
        )

    validate_plugin_config(core, plugin_id, config_dict)

    suffix = Path(file.filename).suffix if file.filename else ""
    upload = await check_upload_size(file, suffix=suffix)
    tmp_path = upload.tmp_path

    try:
        doc = core.add_document(
            f"api_transcribe_{file.filename}_{upload.content_hash}",
            "",
        )
        doc.metadata["file_path"] = tmp_path
        doc.metadata["original_filename"] = file.filename
        doc.metadata["file_size"] = upload.size

        result = await asyncio.wait_for(
            asyncio.to_thread(core.execute_plugin, plugin_id, doc, config_dict),
            timeout=60.0,
        )

        # Plugin retorna status: "error" para falhas de domínio (sem API key, arquivo inválido, etc)
        if isinstance(result, dict) and result.get("status") == "error":
            error_msg = result.get("error", "Erro na transcrição")
            await track(f"/transcribe/{plugin_id}", plugin_id, error_msg)
            raise HTTPException(status_code=400, detail=error_msg)

        await track(f"/transcribe/{plugin_id}", plugin_id)

        Path(tmp_path).unlink(missing_ok=True)

        return {
            "status": "success",
            "plugin_id": plugin_id,
            "filename": file.filename,
            "result": result,
        }
    except HTTPException as he:
        if he.status_code != 504:
            # Cleanup seguro — não deu timeout, thread não está mais lendo
            Path(tmp_path).unlink(missing_ok=True)
        raise
    except asyncio.TimeoutError:
        # Não deleta tempfile no timeout — thread órfã pode ainda estar lendo
        await track(f"/transcribe/{plugin_id}", plugin_id, "Timeout")
        raise HTTPException(status_code=504, detail="Transcrição excedeu timeout de 60s")
    except Exception as e:
        Path(tmp_path).unlink(missing_ok=True)
        await track(f"/transcribe/{plugin_id}", plugin_id, str(e))
        raise HTTPException(status_code=400, detail=str(e))
