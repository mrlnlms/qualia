"""Dependências compartilhadas entre módulos de rota."""

from typing import Dict, Optional

from fastapi import HTTPException, UploadFile

from qualia.core import QualiaCore

_core: Optional[QualiaCore] = None
HAS_EXTENSIONS: bool = False

# Limite de upload do engine (500MB — plugins com limites menores tratam internamente)
MAX_UPLOAD_SIZE = 500 * 1024 * 1024


def set_core(core: QualiaCore):
    global _core
    _core = core


def get_core() -> QualiaCore:
    assert _core is not None, "Core não inicializado — set_core() não foi chamado"
    return _core


def set_extensions(available: bool):
    global HAS_EXTENSIONS
    HAS_EXTENSIONS = available


def validate_plugin_config(core: QualiaCore, plugin_id: str, config: Dict) -> None:
    """Valida config via registry. Levanta HTTPException 422 se inválida."""
    registry = core.get_config_registry()
    if registry is not None:
        valid, errors = registry.validate_config(plugin_id, config or {})
        if not valid:
            raise HTTPException(
                status_code=422,
                detail={"message": "Configuração inválida", "errors": errors},
            )


def require_plugin_type(core: QualiaCore, plugin_id: str, *expected_types: str) -> None:
    """Verifica se o plugin é do tipo esperado. Levanta HTTPException 422 se incompatível."""
    meta = core.registry.get(plugin_id)
    if not meta:
        raise HTTPException(status_code=404, detail=f"Plugin '{plugin_id}' não encontrado")
    if meta.type.value not in expected_types:
        raise HTTPException(
            status_code=422,
            detail=f"Plugin '{plugin_id}' é do tipo '{meta.type.value}', "
                   f"esperado: {', '.join(expected_types)}",
        )


UPLOAD_CHUNK_SIZE = 64 * 1024  # 64KB por chunk


async def check_upload_size(file: UploadFile, max_size: int = None) -> bytes:
    """Lê upload em streaming e aborta com 413 se exceder limite.

    Lê em chunks de 64KB — nunca carrega mais que max_size + 1 chunk na RAM.
    """
    if max_size is None:
        max_size = MAX_UPLOAD_SIZE
    chunks = []
    total = 0
    while True:
        chunk = await file.read(UPLOAD_CHUNK_SIZE)
        if not chunk:
            break
        total += len(chunk)
        if total > max_size:
            size_mb = total / (1024 * 1024)
            limit_mb = max_size / (1024 * 1024)
            raise HTTPException(
                status_code=413,
                detail=f"Arquivo muito grande: >{size_mb:.0f}MB. Limite: {limit_mb:.0f}MB."
            )
        chunks.append(chunk)
    return b"".join(chunks)


async def track(endpoint: str, plugin_id: str = None, error: str = None):
    """Wrapper de track_request — no-op quando extensions não estão disponíveis."""
    if HAS_EXTENSIONS:
        from qualia.api.monitor import track_request
        await track_request(endpoint, plugin_id, error)
