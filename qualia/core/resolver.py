# qualia/core/resolver.py
"""
Resolução de dependências entre plugins via ordenação topológica.
"""

from typing import Dict, List, Set

from qualia.core.interfaces import PluginMetadata


class DependencyResolver:
    """Resolve ordem de execução baseado em dependências"""

    def __init__(self):
        self.graph: Dict[str, Set[str]] = {}
        self.metadata: Dict[str, PluginMetadata] = {}

    def add_plugin(self, plugin_id: str, metadata: PluginMetadata) -> None:
        """Adiciona plugin ao grafo de dependências"""
        self.metadata[plugin_id] = metadata
        self.graph[plugin_id] = set(metadata.requires)

    def resolve(self, target_plugins: List[str]) -> List[str]:
        """
        Resolve ordem de execução incluindo todas as dependências
        Detecta ciclos e retorna ordem topológica
        """
        # Coleta todas as dependências transitivas
        all_plugins = set()
        to_process = set(target_plugins)

        while to_process:
            plugin = to_process.pop()
            if plugin not in all_plugins:
                all_plugins.add(plugin)
                if plugin in self.metadata:
                    deps = self.metadata[plugin].requires
                    to_process.update(deps)

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
