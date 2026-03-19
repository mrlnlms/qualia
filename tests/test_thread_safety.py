# tests/test_thread_safety.py
"""Testes de thread-safety para plugin singletons.

Plugins são singletons: __init__ roda na main thread,
_analyze_impl roda em worker threads via asyncio.to_thread.
Estes testes simulam esse padrão com ThreadPoolExecutor.
"""

import pytest
from concurrent.futures import ThreadPoolExecutor, as_completed
from qualia.core import QualiaCore, Document
from pathlib import Path
import tempfile
import shutil


@pytest.fixture
def core():
    tmp = Path(tempfile.mkdtemp())
    c = QualiaCore(plugins_dir=Path("plugins"), cache_dir=tmp / "cache")
    yield c
    shutil.rmtree(tmp)


class TestWordFrequencyConcurrent:
    """word_frequency singleton chamado por múltiplas threads."""

    def test_concurrent_analyze_returns_correct_results(self, core):
        """10 threads analisando textos diferentes devem retornar resultados corretos."""
        unique_words = [
            "abacaxi", "beterraba", "cenoura", "damasco", "ervilha",
            "framboesa", "goiaba", "hortela", "inhame", "jabuticaba",
        ]
        texts = [
            f"{unique_words[i]} " * (10 + i) + "comum " * 5
            for i in range(10)
        ]
        docs = [
            core.add_document(f"thread_{i}", text)
            for i, text in enumerate(texts)
        ]

        results = {}

        def analyze(idx):
            return idx, core.execute_plugin("word_frequency", docs[idx])

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(analyze, i) for i in range(10)]
            for future in as_completed(futures):
                idx, result = future.result()
                results[idx] = result

        # Todos devem ter retornado
        assert len(results) == 10

        # Cada resultado deve ter total_words > 0
        for idx, result in results.items():
            assert result["total_words"] > 0, f"Thread {idx} retornou total_words=0"

        # Cada resultado deve conter a palavra única daquela thread
        for idx in range(10):
            freq = results[idx].get("word_frequencies", {})
            word = unique_words[idx]
            assert word in freq, f"Thread {idx} não tem '{word}' no resultado"

    def test_concurrent_no_shared_state_corruption(self, core):
        """Resultados de uma thread não devem vazar pra outra."""
        doc_a = core.add_document("a", "alpha " * 50)
        doc_b = core.add_document("b", "beta " * 50)

        results = {}

        def analyze(name, doc):
            return name, core.execute_plugin("word_frequency", doc)

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [
                executor.submit(analyze, "a", doc_a),
                executor.submit(analyze, "b", doc_b),
            ]
            for future in as_completed(futures):
                name, result = future.result()
                results[name] = result

        freq_a = results["a"].get("word_frequencies", {})
        freq_b = results["b"].get("word_frequencies", {})

        # alpha só deve aparecer no resultado de a
        assert "alpha" in freq_a
        assert "alpha" not in freq_b

        # beta só deve aparecer no resultado de b
        assert "beta" in freq_b
        assert "beta" not in freq_a


class TestSentimentConcurrent:
    """sentiment_analyzer singleton chamado por múltiplas threads."""

    def test_concurrent_sentiment_returns_results(self, core):
        """5 threads analisando sentimento devem todas retornar."""
        texts = [
            "Excelente produto, muito bom!",
            "Péssimo atendimento, horrível.",
            "Normal, nada de especial.",
            "Adorei a experiência, fantástico!",
            "Muito ruim, decepcionante.",
        ]
        docs = [core.add_document(f"sent_{i}", t) for i, t in enumerate(texts)]

        results = {}

        def analyze(idx):
            return idx, core.execute_plugin(
                "sentiment_analyzer", docs[idx], {"language": "pt"}
            )

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(analyze, i) for i in range(5)]
            for future in as_completed(futures):
                idx, result = future.result()
                results[idx] = result

        assert len(results) == 5
        for idx, result in results.items():
            assert "polarity" in result
            assert "subjectivity" in result
            assert -1 <= result["polarity"] <= 1
            assert 0 <= result["subjectivity"] <= 1
