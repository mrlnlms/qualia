"""Endpoint de pipeline multi-step."""

import json
import hashlib
import asyncio
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File, Form

from qualia.api.deps import get_core, track, validate_plugin_config, check_upload_size
from qualia.core.models import extract_chained_text

router = APIRouter()


def _extract_text_result(result):
    """Wrapper local — delega pra helper canônico em core.models."""
    return extract_chained_text(result)


@router.post("/pipeline")
async def execute_pipeline(
    steps: str = Form(...),
    text: str = Form(None),
    file: UploadFile = File(None),
):
    """Execute a pipeline of plugins.

    Accepts multipart/form-data with:
    - steps: JSON array of {plugin_id, config}
    - text: input text (optional if file provided)
    - file: uploaded file for document plugins (optional if text provided)

    When file is provided and step[0] is a document plugin, the file is
    transcribed first and the resulting text feeds into subsequent steps.
    Each analyzer step receives the text produced by the chain so far.
    """
    core = get_core()

    try:
        steps_list = json.loads(steps)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=422, detail=f"Invalid steps JSON: {e}")

    if not steps_list:
        raise HTTPException(status_code=422, detail="Pipeline must have at least one step")

    # Validar estrutura de todos os steps antes de executar
    for i, step in enumerate(steps_list):
        if not isinstance(step, dict):
            raise HTTPException(status_code=422, detail=f"Step {i} deve ser um objeto JSON")
        if "plugin_id" not in step or not step["plugin_id"]:
            raise HTTPException(status_code=422, detail=f"Step {i} requer 'plugin_id'")
        step_config = step.get("config", {})
        if not isinstance(step_config, dict):
            raise HTTPException(status_code=422, detail=f"Step {i}: config deve ser um objeto JSON")

    tmp_path = None
    all_results = []
    accumulated_data = {}  # Acumula resultados de todos os steps pra visualizers

    try:
        current_text = text or ""
        step_offset = 0

        first_plugin_id = steps_list[0]["plugin_id"]
        first_meta = core.registry.get(first_plugin_id)

        # 404 antes de qualquer lógica de tipo
        if not first_meta:
            raise HTTPException(status_code=404, detail=f"Plugin '{first_plugin_id}' not found")

        first_is_document = first_meta.type.value == "document"

        if file and first_is_document:
            step0 = steps_list[0]
            plugin_id = step0["plugin_id"]
            config_dict = step0.get("config", {})
            validate_plugin_config(core, plugin_id, config_dict)

            suffix = Path(file.filename).suffix if file.filename else ""
            is_transcription = "transcription" in (first_meta.provides or [])
            # Transcrição: limite 25MB da Groq na borda; outros: limite global
            max_size = 25 * 1024 * 1024 if is_transcription else None
            upload = await check_upload_size(file, max_size=max_size, suffix=suffix)
            tmp_path = upload.tmp_path
            if is_transcription:
                doc_content = ""
            else:
                try:
                    doc_content = Path(tmp_path).read_text(encoding="utf-8")
                except UnicodeDecodeError:
                    doc_content = Path(tmp_path).read_text(encoding="latin-1")

            doc = core.add_document(
                f"api_pipeline_file_{file.filename}_{upload.content_hash}",
                doc_content,
            )
            doc.metadata["file_path"] = tmp_path
            doc.metadata["original_filename"] = file.filename
            doc.metadata["file_size"] = upload.size

            try:
                result = await asyncio.wait_for(
                    asyncio.to_thread(core.execute_plugin, plugin_id, doc, config_dict),
                    timeout=60.0,
                )
            except asyncio.TimeoutError:
                raise HTTPException(status_code=504, detail=f"Plugin '{plugin_id}' timed out (60s)")
            all_results.append({"plugin_id": plugin_id, "result": result})
            if isinstance(result, dict):
                accumulated_data.update(result)

            next_text = _extract_text_result(result)
            if next_text is not None:
                current_text = next_text

            step_offset = 1
        elif file and not first_is_document:
            plugin_type = first_meta.type.value
            raise HTTPException(
                status_code=422,
                detail=f"Arquivo enviado mas primeiro step '{first_plugin_id}' é '{plugin_type}', "
                       f"não 'document'. Para processar arquivos, o primeiro step deve ser um plugin document.",
            )
        elif not current_text:
            raise HTTPException(status_code=422, detail="Pipeline requires text or file input")

        last_result = all_results[-1]["result"] if all_results else None

        for step_def in steps_list[step_offset:]:
            plugin_id = step_def["plugin_id"]
            config_dict = step_def.get("config", {})

            if plugin_id not in core.registry:
                raise HTTPException(status_code=404, detail=f"Plugin '{plugin_id}' not found")
            plugin = core.loader.get_plugin(plugin_id)

            plugin_type = core.registry[plugin_id].type.value
            if plugin_type not in ("analyzer", "document", "visualizer"):
                raise HTTPException(
                    status_code=422,
                    detail=f"Plugin '{plugin_id}' é tipo '{plugin_type}', não suportado em pipelines"
                )

            output_format = "html"
            if plugin_type == "visualizer":
                config_dict = {**config_dict}
                # output_format é canônico; format é alias backward-compatible
                if "output_format" in config_dict:
                    output_format = config_dict.pop("output_format")
                elif "format" in config_dict:
                    output_format = config_dict.pop("format")

                # Validar formato aceito — alinhado com /visualize (Literal["html","png","svg"])
                valid_formats = {"html", "png", "svg"}
                if output_format not in valid_formats:
                    raise HTTPException(
                        status_code=422,
                        detail=f"output_format '{output_format}' inválido para visualizer. "
                               f"Aceitos: {', '.join(sorted(valid_formats))}",
                    )

            validate_plugin_config(core, plugin_id, config_dict)

            if plugin_type == "visualizer":
                if last_result is None:
                    raise HTTPException(
                        status_code=422,
                        detail=f"Visualizer '{plugin_id}' requires a previous step's result as data",
                    )
                # Usar dados acumulados de todos os steps anteriores (não só o último)
                viz_data = {**accumulated_data}
                if isinstance(last_result, dict):
                    viz_data.update(last_result)
                viz_config = {**config_dict, "output_format": output_format}
                try:
                    result = await asyncio.wait_for(
                        asyncio.to_thread(plugin.render, viz_data, viz_config),
                        timeout=60.0,
                    )
                except asyncio.TimeoutError:
                    raise HTTPException(status_code=504, detail=f"Plugin '{plugin_id}' timed out (60s)")
            else:
                doc = core.add_document(
                    f"api_pipeline_{plugin_id}_{hashlib.md5(current_text.encode()).hexdigest()[:8]}",
                    current_text,
                )
                try:
                    result = await asyncio.wait_for(
                        asyncio.to_thread(core.execute_plugin, plugin_id, doc, config_dict),
                        timeout=60.0,
                    )
                except asyncio.TimeoutError:
                    raise HTTPException(status_code=504, detail=f"Plugin '{plugin_id}' timed out (60s)")

                next_text = _extract_text_result(result)
                if next_text is not None:
                    current_text = next_text

            all_results.append({"plugin_id": plugin_id, "result": result})
            if isinstance(result, dict):
                accumulated_data.update(result)
            last_result = result

        await track("/pipeline")

        if tmp_path:
            Path(tmp_path).unlink(missing_ok=True)

        return {
            "status": "success",
            "pipeline": "API Pipeline",
            "steps_executed": len(all_results),
            "results": all_results,
        }
    except HTTPException as he:
        if he.status_code != 504 and tmp_path:
            # Cleanup seguro — não deu timeout, thread não está mais lendo
            Path(tmp_path).unlink(missing_ok=True)
        raise
    except Exception as e:
        if tmp_path:
            Path(tmp_path).unlink(missing_ok=True)
        await track("/pipeline", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))
