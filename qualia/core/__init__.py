# qualia/core/__init__.py
"""
Qualia Core - Bare Metal Framework for Qualitative Data Analysis

Este é o núcleo COMPLETAMENTE AGNÓSTICO que:
- NÃO sabe o que é "sentiment", "LDA", "topic modeling", etc
- NÃO implementa NENHUMA feature específica
- APENAS orquestra plugins que se auto-descrevem
- Resolve dependências automaticamente
- Gerencia cache e estado
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import json
import hashlib
import pickle
import importlib.util
import inspect
from datetime import datetime
from enum import Enum
from typing import Dict, Any, List, Optional, Union, Set, Tuple
from qualia.core.config import ConfigurationRegistry

# ============================================================================
# CONTRATOS (O Core só conhece estas interfaces)
# ============================================================================

class PluginType(Enum):
    """Tipos de plugins que o Core pode orquestrar"""
    ANALYZER = "analyzer"
    FILTER = "filter"
    VISUALIZER = "visualizer"
    DOCUMENT = "document"
    COMPOSER = "composer"


@dataclass
class PluginMetadata:
    """Metadados que todo plugin deve fornecer"""
    id: str
    type: PluginType
    name: str
    description: str
    version: str
    provides: List[str] = field(default_factory=list)
    requires: List[str] = field(default_factory=list)
    can_use: List[str] = field(default_factory=list)
    accepts: List[str] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    def get_dependencies(self) -> Set[str]:
        """Retorna todas as dependências (obrigatórias e opcionais)"""
        return set(self.requires + self.can_use)


class IPlugin(ABC):
    """Interface base que todo plugin deve implementar"""
    
    @abstractmethod
    def meta(self) -> PluginMetadata:
        """Plugin se descreve completamente"""
        pass
    
    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Valida configuração contra schema do plugin"""
        pass


class IAnalyzerPlugin(IPlugin):
    """Cria dados novos a partir de documentos"""
    
    @abstractmethod
    def analyze(self, document: Any, config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analisa documento com configuração e contexto de dependências
        context contém resultados de plugins que este depende
        """
        pass


class IFilterPlugin(IPlugin):
    """Transforma ou filtra dados existentes"""
    
    @abstractmethod
    def filter(self, data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Aplica transformação aos dados"""
        pass


class IVisualizerPlugin(IPlugin):
    """Renderiza dados em visualizações"""
    
    @abstractmethod
    def render(self, data: Dict[str, Any], config: Dict[str, Any], output_path: Path) -> str:
        """Renderiza visualização e retorna caminho do arquivo gerado"""
        pass


class IDocumentPlugin(IPlugin):
    """Processa e prepara documentos"""
    
    @abstractmethod
    def process(self, raw_content: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Processa conteúdo bruto e retorna documento estruturado"""
        pass


class IComposerPlugin(IPlugin):
    """Combina múltiplas análises"""
    
    @abstractmethod
    def compose(self, analyses: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Combina resultados de múltiplas análises"""
        pass


# ============================================================================
# DOCUMENT OBJECT (Inspirado no spaCy)
# ============================================================================

@dataclass
class Document:
    """Single source of truth para todas as análises"""
    id: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    _analyses: Dict[str, Any] = field(default_factory=dict)
    _variants: Dict[str, 'Document'] = field(default_factory=dict)
    _cache: Dict[str, Any] = field(default_factory=dict)
    
    def add_analysis(self, plugin_id: str, result: Dict[str, Any]) -> None:
        """Adiciona resultado de análise ao documento"""
        self._analyses[plugin_id] = {
            'result': result,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_analysis(self, plugin_id: str) -> Optional[Dict[str, Any]]:
        """Recupera resultado de análise específica"""
        return self._analyses.get(plugin_id, {}).get('result')
    
    def add_variant(self, name: str, variant_doc: 'Document') -> None:
        """Adiciona variante do documento (ex: participants_only)"""
        self._variants[name] = variant_doc
    
    def get_variant(self, name: str) -> Optional['Document']:
        """Recupera variante específica"""
        return self._variants.get(name)


# ============================================================================
# # BASE CLASSES
# ============================================================================

# Adicionar estas classes em qualia/core/__init__.py após as interfaces
# IMPORTANTE: Adicionar no topo do arquivo, junto com os outros imports:
# from typing import Dict, Any, List, Optional, Union, Set, Tuple

class BaseAnalyzerPlugin(IAnalyzerPlugin):
    """Base class com funcionalidades comuns para analyzers"""
    
    # meta() NÃO é abstrato aqui - será implementado pelas subclasses
    # Removemos @abstractmethod para não conflitar
    
    def analyze(self, document: Document, config: Dict[str, Any], 
                context: Dict[str, Any]) -> Dict[str, Any]:
        """Wrapper que valida e prepara antes de chamar _analyze_impl"""
        validated_config = self._validate_config(config)
        return self._analyze_impl(document, validated_config, context)
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Implementação concreta do validate_config"""
        # Por enquanto sempre retorna True
        # TODO: implementar validação baseada em meta().parameters
        return True, None
    
    def _validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Valida e aplica defaults aos parâmetros"""
        meta = self.meta()
        validated = {}
        
        for param_name, param_spec in meta.parameters.items():
            if param_name in config:
                validated[param_name] = config[param_name]
            else:
                validated[param_name] = param_spec.get('default')
        
        return validated
    
    def _analyze_impl(self, document: Document, config: Dict[str, Any], 
                      context: Dict[str, Any]) -> Dict[str, Any]:
        """Implementação real do analyzer - override este método"""
        raise NotImplementedError("Subclasse deve implementar _analyze_impl()")


class BaseVisualizerPlugin(IVisualizerPlugin):
    """Base class com funcionalidades comuns para visualizers"""
    
    def render(self, data: Dict[str, Any], config: Dict[str, Any], 
               output_path: Union[str, Path]) -> Union[str, Path]:
        """Wrapper que valida e prepara antes de chamar _render_impl"""
        # Garantir que output_path é Path
        output_path = self._ensure_path(output_path)
        
        # Criar diretório se necessário
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Validar config
        validated_config = self._validate_config(config)
        
        # Validar que temos os dados necessários
        self._validate_data(data)
        
        # Chamar implementação real
        return self._render_impl(data, validated_config, output_path)
    
    def validate_config(self, config: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Implementação concreta do validate_config"""
        try:
            # Tentar validar usando _validate_config
            self._validate_config(config)
            return True, None
        except Exception as e:
            return False, str(e)
    
    def _validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Valida e aplica defaults aos parâmetros"""
        meta = self.meta()
        validated = {}
        
        # IMPORTANTE: Aplicar defaults de TODOS os parâmetros definidos no metadata!
        for param_name, param_spec in meta.parameters.items():
            if param_name in config:
                # Valor foi fornecido, usar ele
                value = config[param_name]
                
                # Converter tipos se necessário
                if param_spec.get('type') == 'integer':
                    validated[param_name] = int(value)
                elif param_spec.get('type') == 'float':
                    validated[param_name] = float(value)
                elif param_spec.get('type') == 'bool':
                    if isinstance(value, str):
                        validated[param_name] = value.lower() == 'true'
                    else:
                        validated[param_name] = bool(value)
                else:
                    validated[param_name] = value
            else:
                # CRUCIAL: Aplicar valor default se não fornecido!
                if 'default' in param_spec:
                    validated[param_name] = param_spec['default']
        
        return validated
    
    def _ensure_path(self, path: Union[str, Path]) -> Path:
        """Converte para Path se necessário"""
        return Path(path) if not isinstance(path, Path) else path
    
    
    def _validate_data(self, data: Dict[str, Any]):
        """Valida que os dados têm os campos necessários"""
        meta = self.meta()
        if meta.requires:
            for required_field in meta.requires:
                if required_field not in data:
                    raise ValueError(
                        f"Visualizador '{meta.id}' requer campo '{required_field}' nos dados"
                    )
    
    def _render_impl(self, data: Dict[str, Any], config: Dict[str, Any], 
                     output_path: Path) -> Path:
        """Implementação real do visualizer - override este método"""
        raise NotImplementedError("Subclasse deve implementar _render_impl()")


class BaseDocumentPlugin(IDocumentPlugin):
    """Base class para document processors"""
    
    def process(self, document: Document, config: Dict[str, Any], 
                context: Dict[str, Any]) -> Dict[str, Any]:
        """Wrapper que valida antes de processar"""
        validated_config = self._validate_config(config)
        return self._process_impl(document, validated_config, context)
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Implementação concreta do validate_config"""
        return True, None
    
    def _validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Reutiliza lógica de validação"""
        meta = self.meta()
        validated = {}
        
        for param_name, param_spec in meta.parameters.items():
            if param_name in config:
                validated[param_name] = config[param_name]
            else:
                validated[param_name] = param_spec.get('default')
        
        return validated
    
    def _process_impl(self, document: Document, config: Dict[str, Any], 
                      context: Dict[str, Any]) -> Dict[str, Any]:
        """Implementação real - override este método"""
        raise NotImplementedError("Subclasse deve implementar _process_impl()")



# Exportar as novas classes
__all__ = [
    'QualiaCore',
    'PluginType', 
    'PluginMetadata',
    'IPlugin',
    'IAnalyzerPlugin',
    'IFilterPlugin', 
    'IVisualizerPlugin',
    'IDocumentPlugin',
    'IComposerPlugin',
    'BaseAnalyzerPlugin',      # novo
    'BaseVisualizerPlugin',    # novo
    'BaseDocumentPlugin',      # novo
    'ConfigurationRegistry',
    'Document',
    'DependencyResolver',
    'CacheManager',
    'PluginLoader',
    'ExecutionContext',
    'PipelineStep',
    'PipelineConfig'
]

# ============================================================================
# DEPENDENCY RESOLVER
# ============================================================================

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


# ============================================================================
# CACHE MANAGER
# ============================================================================

class CacheManager:
    """Gerencia cache de resultados de análises"""
    
    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_cache_key(self, doc_id: str, plugin_id: str, config: Dict[str, Any]) -> str:
        """Gera chave única para cache"""
        config_str = json.dumps(config, sort_keys=True)
        content = f"{doc_id}:{plugin_id}:{config_str}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    def get(self, doc_id: str, plugin_id: str, config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Recupera resultado do cache se existir"""
        cache_key = self._get_cache_key(doc_id, plugin_id, config)
        cache_file = self.cache_dir / f"{cache_key}.pkl"
        
        if cache_file.exists():
            try:
                with open(cache_file, 'rb') as f:
                    return pickle.load(f)
            except Exception:
                # Cache corrompido, ignora
                cache_file.unlink()
        
        return None
    
    def set(self, doc_id: str, plugin_id: str, config: Dict[str, Any], result: Dict[str, Any]) -> None:
        """Armazena resultado no cache"""
        cache_key = self._get_cache_key(doc_id, plugin_id, config)
        cache_file = self.cache_dir / f"{cache_key}.pkl"
        
        with open(cache_file, 'wb') as f:
            pickle.dump(result, f)
    
    def invalidate(self, doc_id: Optional[str] = None, plugin_id: Optional[str] = None) -> None:
        """Invalida cache baseado em documento ou plugin"""
        pattern = ""
        if doc_id:
            pattern = f"{doc_id}:"
        # Implementação simplificada - em produção, indexar melhor
        for cache_file in self.cache_dir.glob("*.pkl"):
            if pattern and pattern in cache_file.stem:
                cache_file.unlink()


# ============================================================================
# PLUGIN LOADER
# ============================================================================

class PluginLoader:
    """Carrega plugins dinamicamente"""
    
    def __init__(self, plugins_dir: Path):
        self.plugins_dir = plugins_dir
        self.loaded_plugins: Dict[str, IPlugin] = {}
    
    def discover(self) -> Dict[str, PluginMetadata]:
        """Descobre todos os plugins disponíveis"""
        discovered = {}
        
        if not self.plugins_dir.exists():
            return discovered
        
        # Procura por arquivos Python em subdiretórios
        for plugin_dir in self.plugins_dir.iterdir():
            if plugin_dir.is_dir() and (plugin_dir / "__init__.py").exists():
                try:
                    # Carrega o módulo
                    spec = importlib.util.spec_from_file_location(
                        plugin_dir.name,
                        plugin_dir / "__init__.py"
                    )
                    if spec and spec.loader:
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                        
                        # Procura por classes que implementam IPlugin
                        for name, obj in inspect.getmembers(module):
                            if name.startswith('Base'):
                                continue
                            if (inspect.isclass(obj) and 
                                issubclass(obj, IPlugin) and 
                                obj not in [IPlugin, IAnalyzerPlugin, IFilterPlugin, 
                                           IVisualizerPlugin, IDocumentPlugin, IComposerPlugin]):
                                
                                instance = obj()
                                meta = instance.meta()
                                discovered[meta.id] = meta
                                self.loaded_plugins[meta.id] = instance
                
                except Exception as e:
                    print(f"Erro ao carregar plugin {plugin_dir.name}: {e}")
        
        return discovered
    
    def get_plugin(self, plugin_id: str) -> Optional[IPlugin]:
        """Retorna instância de plugin carregado"""
        return self.loaded_plugins.get(plugin_id)


# ============================================================================
# EXECUTION CONTEXT
# ============================================================================

@dataclass
class ExecutionContext:
    """Contexto passado entre plugins durante execução"""
    document: Document
    results: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_result(self, plugin_id: str, result: Any) -> None:
        """Adiciona resultado de plugin ao contexto"""
        self.results[plugin_id] = result
    
    def get_dependency_results(self, dependencies: List[str]) -> Dict[str, Any]:
        """Retorna resultados das dependências solicitadas"""
        return {dep: self.results.get(dep) for dep in dependencies if dep in self.results}


# ============================================================================
# PIPELINE CONFIGURATION
# ============================================================================

@dataclass
class PipelineStep:
    """Configuração de um passo no pipeline"""
    plugin_id: str
    config: Dict[str, Any] = field(default_factory=dict)
    output_name: Optional[str] = None  # Nome customizado para o resultado

@dataclass
class PipelineConfig:
    """Configuração completa de um pipeline"""
    name: str
    steps: List[PipelineStep]
    metadata: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# QUALIA CORE - O ORQUESTRADOR PURO
# ============================================================================

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

        # ADICIONE ESTA LINHA! Descobrir plugins na inicialização
        self.discover_plugins()
    
    def discover_plugins(self) -> Dict[str, PluginMetadata]:
        """
        Descobre plugins disponíveis
        Core não sabe o que vai encontrar!
        """
        self.registry = self.loader.discover()
        self.plugins = self.loader.loaded_plugins

        # Atualiza resolver
        for plugin_id, metadata in self.registry.items():
            self.resolver.add_plugin(plugin_id, metadata)

        # Criar ConfigurationRegistry com os plugins descobertos
        if self.plugins:
            self.config_registry = ConfigurationRegistry(self.plugins)

        return self.registry
    
    def execute_plugin(self, 
                  plugin_id: str, 
                  document: Document,
                  config: Dict[str, Any] = None,
                  context: Dict[str, Any] = None) -> Dict[str, Any]:  # ADICIONAR context aqui
                    """
                    Executa um plugin sem saber o que ele faz
                    Resolve dependências automaticamente
                    """
                    config = config or {}
                    # REMOVER a linha: context = context or {}  # Essa linha está causando erro
                    
                    if plugin_id not in self.plugins:
                        raise ValueError(f"Plugin '{plugin_id}' não encontrado")
                    
                    # REMOVER config = config or {} duplicado
                    plugin = self.plugins[plugin_id]
                    metadata = self.registry[plugin_id]
                    
                    # Valida configuração
                    valid, error = plugin.validate_config(config)
                    if not valid:
                        raise ValueError(f"Configuração inválida: {error}")
                    
                    # Verifica cache
                    cached = self.cache.get(document.id, plugin_id, config)
                    if cached is not None:
                        return cached
                    
                    # Cria contexto de execução (RENOMEAR para exec_context para não conflitar)
                    exec_context = ExecutionContext(document=document)
                    
                    # Resolve e executa dependências
                    dependencies = self.resolver.resolve([plugin_id])
                    dependencies.remove(plugin_id)  # Remove o próprio plugin
                    
                    for dep_id in dependencies:
                        if dep_id in self.plugins:
                            dep_result = self.execute_plugin(dep_id, document, {})
                            exec_context.add_result(dep_id, dep_result)
                    
                    # Executa o plugin baseado em seu tipo
                    result = None
                    dep_results = exec_context.get_dependency_results(metadata.requires)
                    
                    if metadata.type == PluginType.ANALYZER:
                        result = plugin.analyze(document, config, dep_results)
                    elif metadata.type == PluginType.FILTER:
                        # Precisa de dados para filtrar
                        data = dep_results.get(metadata.requires[0]) if metadata.requires else {}
                        result = plugin.filter(data, config)
                    elif metadata.type == PluginType.DOCUMENT:
                        # CORRIGIR: passar document (não document.content) e context simples
                        result = plugin.process(document, config, context or {})
                    elif metadata.type == PluginType.VISUALIZER:
                        # Precisa de dados para visualizar
                        data = dep_results.get(metadata.requires[0]) if metadata.requires else {}
                        output_path = Path(f"./output/{document.id}_{plugin_id}.png")
                        result = plugin.render(data, config, output_path)
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
                print(f"Erro ao executar {step.plugin_id}: {e}")
                # Continua com próximo passo ou para?
                # Decisão de design...
        
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


# ============================================================================
# EXEMPLO DE USO (Teste do Core Vazio)
# ============================================================================

if __name__ == "__main__":
    # Core inicia COMPLETAMENTE VAZIO
    core = QualiaCore()
    
    # Confirma que está vazio
    print(f"Plugins no início: {len(core.plugins)}")  # 0
    print(f"Registry no início: {len(core.registry)}")  # 0
    
    # Descobre o que existe (se houver plugins instalados)
    discovered = core.discover_plugins()
    print(f"\nPlugins descobertos: {len(discovered)}")
    
    # Lista o que encontrou (Core não sabe o que são!)
    for plugin_id, meta in discovered.items():
        print(f"  - {plugin_id}: {meta.type.value}")
        print(f"    Fornece: {meta.provides}")
        print(f"    Requer: {meta.requires}")
    
    # Core funciona mesmo vazio!
    print("\nCore está operacional, aguardando plugins...")