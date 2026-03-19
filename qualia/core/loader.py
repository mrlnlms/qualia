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

    Plugins que definem __init__ próprio (warm-up, modelos, corpora)
    são instanciados na main thread durante discover() (eager).
    Os demais são instanciados sob demanda no primeiro get_plugin() (lazy).

    A detecção é automática via '__init__' in cls.__dict__.

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
                                self._plugin_classes[obj.__name__] = obj
                                needs_eager = '__init__' in obj.__dict__

                                if needs_eager:
                                    # Warm-up na main thread (thread-safe)
                                    instance = obj()
                                    meta = instance.meta()
                                    self.loaded_plugins[meta.id] = instance
                                    self._plugin_classes[meta.id] = obj
                                    logger.debug(f"Plugin {meta.id}: eager (has __init__)")
                                else:
                                    # Instância temporária só pra extrair metadata
                                    instance = obj()
                                    meta = instance.meta()
                                    self._plugin_classes[meta.id] = obj
                                    # NÃO guarda em loaded_plugins — lazy
                                    logger.debug(f"Plugin {meta.id}: lazy")

                                if meta.id in discovered:
                                    raise ValueError(
                                        f"Plugin ID duplicado: '{meta.id}' em '{plugin_dir.name}' "
                                        f"(já registrado)"
                                    )
                                discovered[meta.id] = meta

                        if not found_plugin:
                            logger.warning(f"Plugin dir '{plugin_dir.name}' não exporta nenhuma classe IPlugin")

                    elapsed = time.perf_counter() - t0
                    logger.debug(f"  {plugin_dir.name}: {elapsed:.3f}s")

                except Exception as e:
                    logger.error(f"Erro ao carregar plugin {plugin_dir.name}: {e}")
                    self.discovery_errors.append({
                        "plugin": plugin_dir.name,
                        "error": str(e),
                        "path": str(plugin_dir),
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
