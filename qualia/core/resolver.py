# qualia/core/resolver.py
"""
Resolução de dependências entre plugins via ordenação topológica.

Suporta dois tipos de dependência em `requires`:
- Plugin IDs diretos (ex: "word_frequency")
- Field names (ex: "word_frequencies") — resolvidos via provides_map
"""

import logging
from typing import Dict, List, Optional, Set

from qualia.core.interfaces import PluginMetadata

logger = logging.getLogger(__name__)


class DependencyResolver:
    """Resolve ordem de execução baseado em dependências.

    Uso em duas fases:
    1. add_plugin() para cada plugin descoberto
    2. build_graph() após todos registrados (resolve field names → plugin IDs)
    """

    def __init__(self):
        self.graph: Dict[str, Set[str]] = {}
        self.metadata: Dict[str, PluginMetadata] = {}
        self._provides_map: Dict[str, str] = {}  # field_name -> plugin_id

    def add_plugin(self, plugin_id: str, metadata: PluginMetadata) -> None:
        """Registra plugin e seus provides. Grafo construído em build_graph()."""
        self.metadata[plugin_id] = metadata

        for field_name in metadata.provides:
            if field_name in self._provides_map:
                existing = self._provides_map[field_name]
                raise ValueError(
                    f"Colisão de provides: campo '{field_name}' fornecido por "
                    f"'{existing}' e '{plugin_id}'. Renomeie um deles."
                )
            self._provides_map[field_name] = plugin_id

    def build_graph(self) -> None:
        """Resolve field-name requires para plugin-ID edges.

        Deve ser chamado após todos os add_plugin(). Cada requires é resolvido:
        - Se é um plugin ID conhecido → edge direta
        - Se é um field name no provides_map → resolve pro provider
        - Se desconhecido → warning no log
        """
        for plugin_id, metadata in self.metadata.items():
            resolved_deps: Set[str] = set()
            for req in metadata.requires:
                if req in self.metadata:
                    resolved_deps.add(req)
                elif req in self._provides_map:
                    resolved_deps.add(self._provides_map[req])
                else:
                    logger.warning(
                        "Plugin '%s' requires '%s' mas nenhum plugin fornece este campo",
                        plugin_id, req,
                    )
            self.graph[plugin_id] = resolved_deps

    def resolve_provider(self, field_name: str) -> Optional[str]:
        """Retorna o plugin_id que provê um campo, ou None."""
        return self._provides_map.get(field_name)

    def resolve(self, target_plugins: List[str]) -> List[str]:
        """
        Resolve ordem de execução incluindo todas as dependências.
        Detecta ciclos e retorna ordem topológica.
        """
        # Coleta todas as dependências transitivas
        all_plugins = set()
        to_process = set(target_plugins)

        while to_process:
            plugin = to_process.pop()
            if plugin not in all_plugins:
                all_plugins.add(plugin)
                if plugin in self.graph:
                    to_process.update(self.graph[plugin])

        # Ordena topologicamente
        visited = set()
        stack = []

        def visit(plugin: str, path: Set[str]) -> None:
            if plugin in path:
                raise ValueError(f"Dependência circular detectada: {' -> '.join(path)} -> {plugin}")

            if plugin not in visited:
                path.add(plugin)
                for dep in self.graph.get(plugin, []):
                    if dep in all_plugins:
                        visit(dep, path.copy())
                visited.add(plugin)
                stack.append(plugin)

        for plugin in all_plugins:
            if plugin not in visited:
                visit(plugin, set())

        return stack
