# qualia/core/engine.py
"""
QualiaCore — orquestrador principal, completamente agnóstico.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from qualia.core.cache import CacheManager
from qualia.core.config import ConfigurationRegistry
from qualia.core.interfaces import IPlugin, PluginMetadata, PluginType
from qualia.core.loader import PluginLoader
from qualia.core.models import Document, ExecutionContext, PipelineConfig
from qualia.core.resolver import DependencyResolver

logger = logging.getLogger(__name__)


class QualiaCore:
    """
    Core completamente agnóstico que:
    - Não conhece NENHUM tipo de análise
    - Apenas orquestra baseado em metadados
    - Resolve dependências automaticamente
    """

    def __init__(self,
                 plugins_dir: Path = None,
                 cache_dir: Path = None):
        # Resolve paths relativos ao pacote, não ao cwd
        _project_root = Path(__file__).resolve().parent.parent.parent
        if plugins_dir is None:
            plugins_dir = _project_root / "plugins"
        if cache_dir is None:
            cache_dir = _project_root / "cache"

        # Core inicia COMPLETAMENTE VAZIO
        self.registry: Dict[str, PluginMetadata] = {}  # Vazio!
        self.plugins: Dict[str, IPlugin] = {}          # Vazio!

        # Sistemas auxiliares
        self.loader = PluginLoader(plugins_dir)
        self.resolver = DependencyResolver()
        self.cache = CacheManager(cache_dir)

        self.config_registry: Optional[ConfigurationRegistry] = None

        self.discover_plugins()

    def discover_plugins(self) -> Dict[str, PluginMetadata]:
        """Descobre plugins disponíveis. Core não sabe o que vai encontrar."""
        self.registry = self.loader.discover()
        # plugins aponta pro mesmo dict do loader — lazy plugins aparecem quando instanciados
        self.plugins = self.loader.loaded_plugins

        # Resolver fresco a cada discovery (evita estado stale)
        self.resolver = DependencyResolver()
        for plugin_id, metadata in self.registry.items():
            self.resolver.add_plugin(plugin_id, metadata)
        self.resolver.build_graph()

        # ConfigurationRegistry usa metadata (não precisa de instâncias)
        if self.registry:
            self.config_registry = ConfigurationRegistry(self.registry)

        return self.registry

    def get_plugin(self, plugin_id: str) -> IPlugin:
        """Retorna instância do plugin (lazy — instancia no primeiro acesso)."""
        plugin = self.loader.get_plugin(plugin_id)
        if plugin is None:
            raise ValueError(f"Plugin '{plugin_id}' não encontrado")
        return plugin

    def execute_plugin(self,
                       plugin_id: str,
                       document: Document,
                       config: Dict[str, Any] = None,
                       context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Executa um plugin sem saber o que ele faz. Resolve dependências automaticamente."""
        config = config or {}

        if plugin_id not in self.registry:
            raise ValueError(f"Plugin '{plugin_id}' não encontrado")

        plugin = self.get_plugin(plugin_id)
        metadata = self.registry[plugin_id]

        # Valida configuração — ConfigRegistry (range, options) + plugin (chaves desconhecidas)
        if self.config_registry and plugin_id in self.config_registry._schemas:
            valid, errors = self.config_registry.validate_config(plugin_id, config)
            if not valid:
                raise ValueError(f"Configuração inválida: {'; '.join(errors)}")
        valid, error = plugin.validate_config(config)
        if not valid:
            raise ValueError(f"Configuração inválida: {error}")

        # Verifica cache — context entra na chave quando não vazio
        cache_config = {**config, "__context__": context} if context else config
        cached = self.cache.get(document.id, plugin_id, cache_config)
        if cached is not None:
            return cached

        # Cria contexto de execução
        exec_context = ExecutionContext(document=document)

        # Resolve dependências via ordenação topológica
        if metadata.requires:
            try:
                execution_order = self.resolver.resolve([plugin_id])
            except ValueError as e:
                raise ValueError(f"Erro de dependência para '{plugin_id}': {e}")
            for dep_id in execution_order:
                if dep_id == plugin_id:
                    continue
                dep_result = self.execute_plugin(dep_id, document, {}, context)
                exec_context.add_result(dep_id, dep_result)

        # Executa o plugin baseado em seu tipo
        result = None
        dep_results = dict(exec_context.results)

        if metadata.type == PluginType.ANALYZER:
            analyzer_context = {**(context or {}), **dep_results}
            result = plugin.analyze(document, config, analyzer_context)
        elif metadata.type == PluginType.DOCUMENT:
            result = plugin.process(document, config, context or {})
        elif metadata.type == PluginType.VISUALIZER:
            # Monta dados combinados de todas as dependências
            data = {}
            for dep_result in dep_results.values():
                if isinstance(dep_result, dict):
                    data.update(dep_result)
            result = plugin.render(data, config)
        else:
            raise ValueError(f"Tipo de plugin não suportado: {metadata.type.value}")

        # Valida contrato de provides (analyzers e documents)
        if (result is not None and isinstance(result, dict) and metadata.provides
                and metadata.type in (PluginType.ANALYZER, PluginType.DOCUMENT)):
            missing = [f for f in metadata.provides if f not in result]
            if missing:
                raise ValueError(
                    f"Plugin '{plugin_id}' declara provides={metadata.provides} "
                    f"mas resultado não contém: {missing}"
                )

        # Armazena no cache (mesma chave com context)
        if result is not None:
            self.cache.set(document.id, plugin_id, cache_config, result)

        if result is None:
            logger.warning("Plugin '%s' retornou None", plugin_id)
        return result if result is not None else {}

    def execute_pipeline(self,
                        pipeline_config: PipelineConfig,
                        document: Document) -> Dict[str, Any]:
        """
        Executa pipeline completo
        Core apenas orquestra, não sabe o que está executando
        """
        results = {}

        for step in pipeline_config.steps:
            try:
                result = self.execute_plugin(
                    step.plugin_id,
                    document,
                    step.config
                )

                output_name = step.output_name or step.plugin_id
                results[output_name] = result

            except Exception as e:
                raise RuntimeError(
                    f"Pipeline falhou no step '{step.plugin_id}': {e}"
                ) from e

        return results

    def add_document(self, doc_id: str, content: str, metadata: Dict[str, Any] = None) -> Document:
        """Cria documento efêmero para processamento stateless."""
        return Document(id=doc_id, content=content, metadata=metadata or {})

    def list_plugins(self, plugin_type: Optional[PluginType] = None) -> List[PluginMetadata]:
        """Lista plugins disponíveis, opcionalmente filtrados por tipo"""
        plugins = list(self.registry.values())

        if plugin_type:
            plugins = [p for p in plugins if p.type == plugin_type]

        return plugins

    def get_plugin_info(self, plugin_id: str) -> Optional[PluginMetadata]:
        """Retorna informações sobre um plugin específico"""
        return self.registry.get(plugin_id)

    def get_config_registry(self) -> Optional[ConfigurationRegistry]:
        """Retorna a instância do ConfigurationRegistry"""
        return self.config_registry

    @property
    def discovery_errors(self) -> list:
        """Erros encontrados durante discovery de plugins."""
        return self.loader.discovery_errors
