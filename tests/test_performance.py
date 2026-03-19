"""
Testes de performance baseline do Qualia

Valida que startup, execução e cache estão dentro de limites aceitáveis.
"""

import pytest
import time
import tempfile
import shutil
from pathlib import Path

from qualia.core import QualiaCore, Document


@pytest.fixture
def temp_dir():
    temp = tempfile.mkdtemp()
    yield Path(temp)
    shutil.rmtree(temp)


# =============================================================================
# STARTUP
# =============================================================================

@pytest.mark.performance
class TestStartupPerformance:

    def test_core_startup_time(self, temp_dir):
        """QualiaCore init + plugin discovery deve ser < 2s (inclui warm-up NLTK/spaCy)"""
        start = time.perf_counter()
        core = QualiaCore(
            plugins_dir=Path("plugins"),
            cache_dir=temp_dir / "cache"
        )
        elapsed = time.perf_counter() - start
        assert elapsed < 2.0, f"Startup levou {elapsed:.3f}s (limite: 2.0s)"
        assert len(core.registry) > 0, "Nenhum plugin descoberto"


# =============================================================================
# EXECUÇÃO DE PLUGINS
# =============================================================================

@pytest.mark.performance
class TestExecutionPerformance:

    @pytest.fixture
    def core(self, temp_dir):
        return QualiaCore(
            plugins_dir=Path("plugins"),
            cache_dir=temp_dir / "cache"
        )

    def test_word_frequency_small_text(self, core):
        """word_frequency em texto curto deve ser < 100ms"""
        doc = core.add_document("small", "Este é um texto de teste. " * 10)
        start = time.perf_counter()
        result = core.execute_plugin("word_frequency", doc, {})
        elapsed = time.perf_counter() - start
        assert elapsed < 0.1, f"Levou {elapsed:.3f}s"
        assert result["total_words"] > 0

    def test_word_frequency_10kb_text(self, core):
        """word_frequency em texto 10KB deve ser < 500ms"""
        # ~10KB de texto
        text = "A análise qualitativa de dados é fundamental para pesquisa. " * 200
        doc = core.add_document("10kb", text)
        start = time.perf_counter()
        result = core.execute_plugin("word_frequency", doc, {})
        elapsed = time.perf_counter() - start
        assert elapsed < 0.5, f"Levou {elapsed:.3f}s"
        assert result["total_words"] > 100

    def test_readability_10kb_text(self, core):
        """readability em texto 10KB deve ser < 500ms"""
        text = "O sol nasceu cedo. O dia está bonito. As pessoas caminham. " * 200
        doc = core.add_document("read_10kb", text)
        start = time.perf_counter()
        result = core.execute_plugin("readability_analyzer", doc, {})
        elapsed = time.perf_counter() - start
        assert elapsed < 0.5, f"Levou {elapsed:.3f}s"
        assert result["word_count"] > 100


# =============================================================================
# CACHE
# =============================================================================

@pytest.mark.performance
class TestCachePerformance:

    @pytest.fixture
    def core(self, temp_dir):
        return QualiaCore(
            plugins_dir=Path("plugins"),
            cache_dir=temp_dir / "cache"
        )

    def test_cache_hit_faster_than_miss(self, core):
        """Cache hit deve ser significativamente mais rápido que miss"""
        text = "Texto para teste de cache com várias palavras diferentes. " * 50
        doc = core.add_document("cache_test", text)

        # Primeira execução (cache miss)
        start = time.perf_counter()
        result1 = core.execute_plugin("word_frequency", doc, {"min_word_length": 3})
        time_miss = time.perf_counter() - start

        # Segunda execução (cache hit)
        start = time.perf_counter()
        result2 = core.execute_plugin("word_frequency", doc, {"min_word_length": 3})
        time_hit = time.perf_counter() - start

        assert result1 == result2, "Resultados devem ser iguais"
        # Cache hit deve ser pelo menos 2x mais rápido
        assert time_hit < time_miss, f"Hit ({time_hit:.4f}s) não foi mais rápido que miss ({time_miss:.4f}s)"
