"""Dependências compartilhadas entre módulos de rota."""

from typing import Dict, Optional

from fastapi import HTTPException

from qualia.core import QualiaCore

_core: Optional[QualiaCore] = None
HAS_EXTENSIONS: bool = False


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


async def track(endpoint: str, plugin_id: str = None, error: str = None):
    """Wrapper de track_request — no-op quando extensions não estão disponíveis."""
    if HAS_EXTENSIONS:
        from qualia.api.monitor import track_request
        await track_request(endpoint, plugin_id, error)
