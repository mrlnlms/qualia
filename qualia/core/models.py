# qualia/core/models.py
"""
Modelos de dados do Qualia Core — Document, ExecutionContext, Pipeline.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Document:
    """Documento efêmero — Qualia é stateless, sem acúmulo de estado."""
    id: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)


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
