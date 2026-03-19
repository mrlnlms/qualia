# tests/test_cache_pipeline.py
"""Testes de cache em pipelines repetidos.

Verifica que executar o mesmo pipeline duas vezes com o mesmo
documento usa cache na segunda execução.
"""

import pytest
from qualia.core import QualiaCore, Document, PipelineConfig, PipelineStep
from pathlib import Path
import tempfile
import shutil


@pytest.fixture
def core():
    tmp = Path(tempfile.mkdtemp())
    c = QualiaCore(plugins_dir=Path(__file__).parent.parent / "plugins", cache_dir=tmp / "cache")
    yield c
    shutil.rmtree(tmp)


class TestPipelineCacheHit:
    """Pipeline repetido deve usar cache na segunda execução."""

    def test_second_pipeline_uses_cache(self, core):
        """Segunda execução do mesmo pipeline com mesmo doc deve vir do cache."""
        doc = core.add_document("cache_test", "texto de teste para pipeline " * 20)
        pipeline = PipelineConfig(
            name="cache_pipe",
            steps=[
                PipelineStep("word_frequency"),
                PipelineStep("sentiment_analyzer", {"language": "pt"}),
            ],
        )

        # Primeira execução — popula cache
        result1 = core.execute_pipeline(pipeline, doc)
        assert "word_frequency" in result1
        assert "sentiment_analyzer" in result1

        # Capturar stats do cache
        stats_before = core.cache.stats()

        # Segunda execução — deve vir do cache
        result2 = core.execute_pipeline(pipeline, doc)

        stats_after = core.cache.stats()

        # Resultados devem ser idênticos
        assert result1 == result2

        # Cache hits devem ter aumentado
        assert stats_after["hits"] > stats_before["hits"]

    def test_different_config_misses_cache(self, core):
        """Mesmo pipeline com config diferente não deve usar cache."""
        doc = core.add_document("cache_miss", "texto para testar cache miss " * 20)

        # Primeira execução com min_word_length=3
        pipeline1 = PipelineConfig(
            name="pipe1",
            steps=[PipelineStep("word_frequency", {"min_word_length": 3})],
        )
        result1 = core.execute_pipeline(pipeline1, doc)

        # Segunda execução com min_word_length=5 — config diferente, cache miss
        pipeline2 = PipelineConfig(
            name="pipe2",
            steps=[PipelineStep("word_frequency", {"min_word_length": 5})],
        )
        result2 = core.execute_pipeline(pipeline2, doc)

        # Resultados devem ser diferentes (filtros diferentes)
        assert result1["word_frequency"] != result2["word_frequency"]

    def test_different_document_misses_cache(self, core):
        """Mesmo pipeline com documento diferente não deve usar cache."""
        doc1 = core.add_document("doc_a", "primeiro documento com conteúdo único " * 20)
        doc2 = core.add_document("doc_b", "segundo documento completamente diferente " * 20)

        pipeline = PipelineConfig(
            name="same_pipe",
            steps=[PipelineStep("word_frequency")],
        )

        result1 = core.execute_pipeline(pipeline, doc1)
        result2 = core.execute_pipeline(pipeline, doc2)

        # Resultados devem ser diferentes (documentos diferentes)
        assert result1["word_frequency"]["word_frequencies"] != result2["word_frequency"]["word_frequencies"]
