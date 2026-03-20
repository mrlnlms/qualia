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


def extract_chained_text(result) -> Optional[str]:
    """Extrai texto encadeável de resultado de plugin.

    Prioridade canônica (primeiro encontrado vence):
      1. transcription — plugins de transcrição
      2. cleaned_document — plugins de limpeza
      3. processed_text — processamento genérico

    Usada por API e CLI para manter a mesma regra de encadeamento.
    """
    if isinstance(result, str):
        return result
    if isinstance(result, dict):
        for key in ("transcription", "cleaned_document", "processed_text"):
            if key in result and isinstance(result[key], str):
                return result[key]
    return None


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
