# qualia/core/loader.py
"""
Auto-descoberta e carregamento de plugins com instanciação eager/lazy.
"""

import importlib.util
import inspect
import logging
import threading
import time
from pathlib import Path
from typing import Dict, Optional

from qualia.core.interfaces import (
    IAnalyzerPlugin,
    IComposerPlugin,
    IDocumentPlugin,
    IFilterPlugin,
    IPlugin,
    IVisualizerPlugin,
    PluginMetadata,
)


class PluginLoader:
    """Carrega plugins com instanciação lazy ou eager automática.

    Plugins com EAGER_LOAD = True ou __init__ próprio (warm-up, modelos, corpora)
    são instanciados na main thread durante discover() (eager).
    Os demais são instanciados sob demanda no primeiro get_plugin() (lazy).

    A detecção prioriza EAGER_LOAD (explícito) sobre '__init__' in cls.__dict__ (implícito).

    Discovery é recursivo — plugins podem estar em qualquer profundidade.
    Pastas cujo nome começa com _ são ignoradas (ex: _templates).
    """

    def __init__(self, plugins_dir: Path):
        self.plugins_dir = plugins_dir
        self.loaded_plugins: Dict[str, IPlugin] = {}
        self._plugin_classes: Dict[str, type] = {}
        self._lock = threading.Lock()
        self.discovery_errors: list = []

    def _find_plugin_dirs(self) -> list:
        """Encontra todas as pastas com __init__.py recursivamente.

        Ignora pastas cujo nome começa com _ (ex: _templates).
        """
        plugin_dirs = []
        for init_file in self.plugins_dir.rglob("__init__.py"):
            plugin_dir = init_file.parent
            rel = plugin_dir.relative_to(self.plugins_dir)
            if any(part.startswith('_') for part in rel.parts):
                continue
            plugin_dirs.append(plugin_dir)
        return plugin_dirs

    def discover(self) -> Dict[str, PluginMetadata]:
        """Descobre plugins em qualquer profundidade e instancia os que precisam de warm-up.

        Plugins com __init__ próprio → instanciados agora (main thread, thread-safe).
        Plugins sem __init__ próprio → classe guardada, instanciação deferida.
        Metadata extraída de todos (via instância temporária pra lazy plugins).
        """
        logger = logging.getLogger(__name__)
        discovered = {}
        self.discovery_errors = []
        self.loaded_plugins.clear()
        self._plugin_classes.clear()

        if not self.plugins_dir.exists():
            return discovered

        t_total = time.perf_counter()

        for plugin_dir in self._find_plugin_dirs():
                try:
                    t0 = time.perf_counter()
                    spec = importlib.util.spec_from_file_location(
                        plugin_dir.name,
                        plugin_dir / "__init__.py"
                    )
                    if spec and spec.loader:
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)

                        found_plugin = False
                        for name, obj in inspect.getmembers(module):
                            if name.startswith('Base'):
                                continue
                            if (inspect.isclass(obj) and
                                issubclass(obj, IPlugin) and
                                obj not in [IPlugin, IAnalyzerPlugin, IFilterPlugin,
                                           IVisualizerPlugin, IDocumentPlugin, IComposerPlugin]):

                                found_plugin = True
                                needs_eager = getattr(obj, 'EAGER_LOAD', None) is True or '__init__' in obj.__dict__

                                instance = obj()
                                meta = instance.meta()

                                if meta.id in discovered:
                                    raise ValueError(
                                        f"Plugin ID duplicado: '{meta.id}' em '{plugin_dir.name}' "
                                        f"(já registrado)"
                                    )

                                # Só mutamos estado após validação
                                if needs_eager:
                                    self.loaded_plugins[meta.id] = instance
                                    logger.debug(f"Plugin {meta.id}: eager (has __init__)")
                                else:
                                    logger.debug(f"Plugin {meta.id}: lazy")

                                self._plugin_classes[meta.id] = obj
                                discovered[meta.id] = meta

                        if not found_plugin:
                            logger.warning(f"Plugin dir '{plugin_dir.name}' não exporta nenhuma classe IPlugin")

                    elapsed = time.perf_counter() - t0
                    logger.debug(f"  {plugin_dir.name}: {elapsed:.3f}s")

                except Exception as e:
                    logger.error(f"Erro ao carregar plugin {plugin_dir.name}: {e}")
                    error_type, severity = self._classify_error(e)
                    self.discovery_errors.append({
                        "plugin": plugin_dir.name,
                        "error": str(e),
                        "path": str(plugin_dir),
                        "type": error_type,
                        "severity": severity,
                    })

        eager_count = len(self.loaded_plugins)
        lazy_count = len(discovered) - eager_count
        total = time.perf_counter() - t_total
        logger.info(f"Discovery: {len(discovered)} plugins ({eager_count} eager, {lazy_count} lazy) em {total:.3f}s")

        return discovered

    def get_plugin(self, plugin_id: str) -> Optional[IPlugin]:
        """Retorna instância do plugin (lazy — instancia no primeiro acesso)."""
        if plugin_id in self.loaded_plugins:
            return self.loaded_plugins[plugin_id]

        with self._lock:
            # Double-check após adquirir lock
            if plugin_id in self.loaded_plugins:
                return self.loaded_plugins[plugin_id]

            if plugin_id in self._plugin_classes:
                instance = self._plugin_classes[plugin_id]()
                self.loaded_plugins[plugin_id] = instance
                return instance

        return None

    @staticmethod
    def _classify_error(exc: Exception) -> tuple:
        """Classifica exceção por tipo e severidade.

        Returns:
            (type_str, severity_str) — severity é 'critical' ou 'warning'
        """
        if isinstance(exc, ImportError):
            return "import_error", "critical"
        elif isinstance(exc, SyntaxError):
            return "syntax_error", "critical"
        elif isinstance(exc, (OSError, FileNotFoundError)):
            return "os_error", "critical"
        elif isinstance(exc, ValueError):
            return "value_error", "critical"
        else:
            return "unknown_error", "warning"
