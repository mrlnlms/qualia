# qualia/core/models.py
"""
Modelos de dados do Qualia Core — Document, ExecutionContext, Pipeline.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


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
