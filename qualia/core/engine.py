# qualia/core/engine.py
"""
QualiaCore — orquestrador principal, completamente agnóstico.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

from qualia.core.cache import CacheManager
from qualia.core.config import ConfigurationRegistry
from qualia.core.interfaces import IPlugin, PluginMetadata, PluginType
from qualia.core.loader import PluginLoader
from qualia.core.models import Document, ExecutionContext, PipelineConfig
from qualia.core.resolver import DependencyResolver


class QualiaCore:
    """
    Core completamente agnóstico que:
    - Não conhece NENHUM tipo de análise
    - Apenas orquestra baseado em metadados
    - Resolve dependências automaticamente
    """

    def __init__(self,
                 plugins_dir: Path = Path("./plugins"),
                 cache_dir: Path = Path("./cache")):
        # Core inicia COMPLETAMENTE VAZIO
        self.registry: Dict[str, PluginMetadata] = {}  # Vazio!
        self.plugins: Dict[str, IPlugin] = {}          # Vazio!

        # Sistemas auxiliares
        self.loader = PluginLoader(plugins_dir)
        self.resolver = DependencyResolver()
        self.cache = CacheManager(cache_dir)

        # Estado
        self.documents: Dict[str, Document] = {}
        self.pipelines: Dict[str, PipelineConfig] = {}
        self.config_registry: Optional[ConfigurationRegistry] = None

        self.discover_plugins()

    def discover_plugins(self) -> Dict[str, PluginMetadata]:
        """Descobre plugins disponíveis. Core não sabe o que vai encontrar."""
        self.registry = self.loader.discover()
        # plugins aponta pro mesmo dict do loader — lazy plugins aparecem quando instanciados
        self.plugins = self.loader.loaded_plugins

        for plugin_id, metadata in self.registry.items():
            self.resolver.add_plugin(plugin_id, metadata)

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

        # Valida configuração
        valid, error = plugin.validate_config(config)
        if not valid:
            raise ValueError(f"Configuração inválida: {error}")

        # Verifica cache
        cached = self.cache.get(document.id, plugin_id, config)
        if cached is not None:
            return cached

        # Cria contexto de execução
        exec_context = ExecutionContext(document=document)

        # Resolve dependências: requires pode ser plugin IDs ou field names
        if metadata.requires:
            for req in metadata.requires:
                if req in self.plugins:
                    dep_result = self.execute_plugin(req, document, {})
                    exec_context.add_result(req, dep_result)
                else:
                    # É um field name — encontrar o plugin que o fornece
                    for pid, pmeta in self.registry.items():
                        if req in getattr(pmeta, 'provides', []) and pid in self.plugins:
                            dep_result = self.execute_plugin(pid, document, {})
                            exec_context.add_result(pid, dep_result)
                            break

        # Executa o plugin baseado em seu tipo
        result = None
        dep_results = dict(exec_context.results)

        if metadata.type == PluginType.ANALYZER:
            result = plugin.analyze(document, config, dep_results)
        elif metadata.type == PluginType.FILTER:
            data = dep_results.get(metadata.requires[0]) if metadata.requires else {}
            result = plugin.filter(data, config)
        elif metadata.type == PluginType.DOCUMENT:
            result = plugin.process(document, config, context or {})
        elif metadata.type == PluginType.VISUALIZER:
            # Monta dados combinados de todas as dependências
            data = {}
            for dep_result in dep_results.values():
                if isinstance(dep_result, dict):
                    data.update(dep_result)
            output_path = Path(f"./output/{document.id}_{plugin_id}.png")
            render_result = plugin.render(data, config, output_path)
            # render retorna Path — envolver em dict para consistência
            if isinstance(render_result, Path):
                result = {"output_path": str(render_result), "plugin_id": plugin_id}
            else:
                result = render_result
        elif metadata.type == PluginType.COMPOSER:
            result = plugin.compose(dep_results, config)

        # Armazena no cache e no documento
        if result is not None:
            self.cache.set(document.id, plugin_id, config, result)
            document.add_analysis(plugin_id, result)

        return result or {}

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
        """Adiciona documento ao sistema"""
        doc = Document(id=doc_id, content=content, metadata=metadata or {})
        self.documents[doc_id] = doc
        return doc

    def get_document(self, doc_id: str) -> Optional[Document]:
        """Recupera documento"""
        return self.documents.get(doc_id)

    def save_pipeline(self, pipeline: PipelineConfig) -> None:
        """Salva configuração de pipeline"""
        self.pipelines[pipeline.name] = pipeline

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
