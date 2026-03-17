"""Dependências compartilhadas entre módulos de rota."""

from typing import Optional
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


async def track(endpoint: str, plugin_id: str = None, error: str = None):
    """Wrapper de track_request — no-op quando extensions não estão disponíveis."""
    if HAS_EXTENSIONS:
        from qualia.api.monitor import track_request
        await track_request(endpoint, plugin_id, error)
