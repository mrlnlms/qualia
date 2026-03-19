"""Endpoint de pipeline multi-step."""

import json
import hashlib
import tempfile
import asyncio
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File, Form

from qualia.api.deps import get_core, track, validate_plugin_config, check_upload_size

router = APIRouter()


def _extract_text_result(result):
    """Extrai texto encadeável de resultados de analyzer/document.

    Prioridade (primeiro encontrado vence):
      1. transcription — plugins de transcrição (e.g. transcription)
      2. cleaned_document — plugins de limpeza (e.g. teams_cleaner)
      3. processed_text — plugins de processamento genérico

    Se um plugin retornar múltiplos desses campos, apenas o de maior
    prioridade será usado para encadear ao próximo step.
    """
    if isinstance(result, str):
        return result
    if isinstance(result, dict):
        for key in ("transcription", "cleaned_document", "processed_text"):
            if key in result and isinstance(result[key], str):
                return result[key]
    return None


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

    tmp_path = None
    all_results = []

    try:
        current_text = text or ""
        step_offset = 0

        first_plugin_id = steps_list[0].get("plugin_id", "")
        first_meta = core.registry.get(first_plugin_id)
        first_is_document = first_meta and first_meta.type.value == "document"

        if file and first_is_document:
            step0 = steps_list[0]
            plugin_id = step0["plugin_id"]
            config_dict = step0.get("config", {})
            validate_plugin_config(core, plugin_id, config_dict)

            content = await check_upload_size(file)
            suffix = Path(file.filename).suffix if file.filename else ""
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(content)
                tmp_path = tmp.name

            doc = core.add_document(
                f"api_pipeline_file_{file.filename}_{hashlib.md5(content).hexdigest()[:8]}",
                "",
            )
            doc.metadata["file_path"] = tmp_path
            doc.metadata["original_filename"] = file.filename
            doc.metadata["file_size"] = len(content)

            try:
                result = await asyncio.wait_for(
                    asyncio.to_thread(core.execute_plugin, plugin_id, doc, config_dict),
                    timeout=60.0,
                )
            except asyncio.TimeoutError:
                raise HTTPException(status_code=504, detail=f"Plugin '{plugin_id}' timed out (60s)")
            all_results.append({"plugin_id": plugin_id, "result": result})

            next_text = _extract_text_result(result)
            if next_text is not None:
                current_text = next_text

            step_offset = 1
        elif file and not first_is_document:
            plugin_type = first_meta.type.value if first_meta else "desconhecido"
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
            if plugin_type == "visualizer" and "format" in config_dict:
                config_dict = {**config_dict}
                output_format = config_dict.pop("format", "html")

            validate_plugin_config(core, plugin_id, config_dict)

            if plugin_type == "visualizer":
                if last_result is None:
                    raise HTTPException(
                        status_code=422,
                        detail=f"Visualizer '{plugin_id}' requires a previous step's result as data",
                    )
                viz_config = {**config_dict, "output_format": output_format}
                try:
                    result = await asyncio.wait_for(
                        asyncio.to_thread(plugin.render, last_result, viz_config),
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
            last_result = result

        await track("/pipeline")

        return {
            "status": "success",
            "pipeline": "API Pipeline",
            "steps_executed": len(all_results),
            "results": all_results,
        }
    except HTTPException:
        raise
    except Exception as e:
        await track("/pipeline", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        if tmp_path:
            Path(tmp_path).unlink(missing_ok=True)
