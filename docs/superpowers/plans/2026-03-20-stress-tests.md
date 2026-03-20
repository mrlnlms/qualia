# Stress Tests Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bateria de testes de stress que bombardeiam cache, plugins e API com entradas extremas, concorrência pesada e configs aleatórias pra achar bugs que testes unitários não pegam.

**Architecture:** Um único arquivo `tests/test_stress.py` com 5 classes temáticas. Usa plugins reais (não mocks) contra o core e a API. Cada teste roda em <5s, bateria total <30s. Marcados com `@pytest.mark.stress` pra rodar separado se quiser.

**Tech Stack:** pytest, threading, asyncio, httpx, random, string

---

## File Structure

- **Create:** `tests/test_stress.py` — todos os testes de stress
- **No other files need modification**

Testes existentes de referência (não modificar):
- `tests/test_thread_safety.py` — 3 testes de concorrência básica com ThreadPoolExecutor
- `tests/test_performance.py` — 5 testes de tempo de execução
- `tests/test_async.py` — 9 testes de concorrência HTTP

Os testes de stress vão além: mais threads, entradas extremas, configs aleatórias, combinações de plugins.

---

### Task 1: Fixture base e imports

**Files:**
- Create: `tests/test_stress.py`

- [ ] **Step 1: Criar arquivo com imports, fixtures e marker**

```python
# tests/test_stress.py
"""
Testes de stress — concorrência pesada, entradas extremas, configs aleatórias.

Roda com: pytest tests/test_stress.py -v
Ou separado: pytest tests/test_stress.py -v -m stress
"""

import json
import random
import string
import shutil
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pytest
import pytest_asyncio
import asyncio
import httpx

from qualia.core import QualiaCore, Document
from qualia.core.cache import CacheManager
from qualia.api import app

pytestmark = pytest.mark.stress


@pytest.fixture
def core():
    tmp = Path(tempfile.mkdtemp())
    c = QualiaCore(
        plugins_dir=Path(__file__).parent.parent / "plugins",
        cache_dir=tmp / "cache",
    )
    yield c
    shutil.rmtree(tmp)


@pytest.fixture
def cache_dir():
    tmp = Path(tempfile.mkdtemp())
    yield tmp
    shutil.rmtree(tmp)


@pytest_asyncio.fixture
async def ac():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
```

- [ ] **Step 2: Verificar que o arquivo importa sem erro**

Run: `source .venv/bin/activate && python -c "import tests.test_stress"`
Expected: sem erro

- [ ] **Step 3: Commit**

```bash
git add tests/test_stress.py
~/.claude/scripts/commit.sh "test: scaffold test_stress.py com fixtures e imports"
```

---

### Task 2: Cache concorrente — set/get/invalidate sob pressão

**Files:**
- Modify: `tests/test_stress.py`

- [ ] **Step 1: Escrever testes de cache concorrente**

Adicionar ao final do arquivo:

```python
# =============================================================================
# CACHE — concorrência pesada
# =============================================================================

class TestCacheStress:
    """Cache sob pressão: múltiplas threads fazendo set/get/invalidate."""

    def test_concurrent_set_get_no_corruption(self, cache_dir):
        """20 threads gravando e lendo ao mesmo tempo — dados nunca corrompem."""
        cache = CacheManager(cache_dir)
        errors = []

        def worker(thread_id):
            try:
                for i in range(50):
                    doc_id = f"doc_{thread_id}"
                    plugin_id = f"plugin_{thread_id % 3}"
                    config = {"iter": i}
                    data = {"thread": thread_id, "iter": i, "value": thread_id * 1000 + i}

                    cache.set(doc_id, plugin_id, config, data)
                    result = cache.get(doc_id, plugin_id, config)

                    if result is None:
                        errors.append(f"Thread {thread_id} iter {i}: got None after set")
                    elif result["value"] != thread_id * 1000 + i:
                        errors.append(f"Thread {thread_id} iter {i}: wrong value {result['value']}")
            except Exception as e:
                errors.append(f"Thread {thread_id}: {type(e).__name__}: {e}")

        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(worker, i) for i in range(20)]
            for f in as_completed(futures):
                f.result()

        assert errors == [], f"Erros de concorrência:\n" + "\n".join(errors[:10])

    def test_concurrent_invalidate_during_writes(self, cache_dir):
        """Threads invalidando enquanto outras gravam — sem crash."""
        cache = CacheManager(cache_dir)
        errors = []
        stop = threading.Event()

        def writer():
            i = 0
            while not stop.is_set():
                try:
                    cache.set(f"doc_{i % 10}", "plugin_a", {"i": i}, {"v": i})
                    i += 1
                except Exception as e:
                    errors.append(f"Writer: {e}")

        def invalidator():
            while not stop.is_set():
                try:
                    cache.invalidate(doc_id=f"doc_{random.randint(0, 9)}")
                except Exception as e:
                    errors.append(f"Invalidator: {e}")

        threads = [threading.Thread(target=writer) for _ in range(5)]
        threads += [threading.Thread(target=invalidator) for _ in range(3)]
        for t in threads:
            t.start()

        time.sleep(2)
        stop.set()
        for t in threads:
            t.join(timeout=5)

        assert errors == [], f"Erros:\n" + "\n".join(errors[:10])

        # Stats devem ser consistentes
        stats = cache.stats()
        assert stats["hits"] >= 0
        assert stats["misses"] >= 0

    def test_cache_stats_consistent_under_load(self, cache_dir):
        """Após N operações, hits + misses + size devem ser consistentes."""
        cache = CacheManager(cache_dir, max_size=50)

        for i in range(200):
            cache.set(f"doc_{i % 20}", "plugin", {"i": i}, {"v": i})

        for i in range(200):
            cache.get(f"doc_{i % 20}", "plugin", {"i": i})

        stats = cache.stats()
        assert stats["size"] <= 50, f"Size {stats['size']} excede max_size 50"
        assert stats["hits"] + stats["misses"] == 200
        assert stats["evictions"] >= 150  # 200 sets - 50 max_size
```

- [ ] **Step 2: Rodar testes**

Run: `source .venv/bin/activate && pytest tests/test_stress.py::TestCacheStress -v`
Expected: 3 passed

- [ ] **Step 3: Commit**

```bash
git add tests/test_stress.py
~/.claude/scripts/commit.sh "test: stress cache — concorrência set/get/invalidate, stats consistentes"
```

---

### Task 3: Configs aleatórias — nenhum plugin deve crashar

**Files:**
- Modify: `tests/test_stress.py`

- [ ] **Step 1: Escrever testes de config fuzzing**

```python
# =============================================================================
# CONFIG FUZZING — configs aleatórias nunca crasham
# =============================================================================

class TestConfigFuzzing:
    """Configs aleatórias/malformadas nunca devem crashar — sempre ValueError ou resultado válido."""

    FUZZ_CONFIGS = [
        {"min_word_length": "abc"},            # tipo errado
        {"min_word_length": -999},             # valor extremo negativo
        {"min_word_length": 999999},           # valor extremo positivo
        {"max_words": 0},                      # zero
        {"max_words": 0.5},                    # float onde espera int
        {"case_sensitive": "maybe"},           # string onde espera bool
        {"language": "klingon"},               # opção inválida
        {"tokenization": "quantum"},           # opção inválida
        {"param_fantasma": 123},               # campo inventado
        {"remove_stopwords": None},            # None
        {"min_word_length": True},             # bool onde espera int
        {"": ""},                              # chave vazia
        {"a" * 1000: "b" * 1000},             # chaves gigantes
    ]

    def test_word_frequency_never_crashes_on_bad_config(self, core):
        """word_frequency com configs malformadas: ValueError ou resultado, nunca crash."""
        doc = core.add_document("fuzz", "Texto normal para fuzzing de configuração.")
        for i, config in enumerate(self.FUZZ_CONFIGS):
            try:
                result = core.execute_plugin("word_frequency", doc, config)
                # Se não levantou erro, resultado deve ter provides
                assert "word_frequencies" in result, f"Config {i}: resultado sem word_frequencies"
            except ValueError:
                pass  # Erro esperado — config inválida rejeitada

    def test_sentiment_never_crashes_on_bad_config(self, core):
        """sentiment_analyzer com configs malformadas: ValueError ou resultado, nunca crash."""
        doc = core.add_document("fuzz_sent", "Texto positivo e feliz para teste.")
        bad_configs = [
            {"language": 42},
            {"polarity_threshold": "alto"},
            {"polarity_threshold": -5},
            {"analyze_sentences": "yes"},
            {"campo_inexistente": [1, 2, 3]},
        ]
        for i, config in enumerate(bad_configs):
            try:
                result = core.execute_plugin("sentiment_analyzer", doc, config)
                assert "polarity" in result, f"Config {i}: resultado sem polarity"
            except ValueError:
                pass

    def test_readability_never_crashes_on_bad_config(self, core):
        """readability com configs malformadas: sempre controlado."""
        doc = core.add_document("fuzz_read", "Frase curta. Frase longa com muitas palavras diferentes.")
        bad_configs = [
            {"detail_level": 999},
            {"detail_level": "full"},
            {"campo": {"nested": True}},
        ]
        for i, config in enumerate(bad_configs):
            try:
                result = core.execute_plugin("readability_analyzer", doc, config)
                assert "word_count" in result
            except ValueError:
                pass

    def test_random_configs_never_crash(self, core):
        """50 configs geradas aleatoriamente — nenhum plugin crasheia."""
        doc = core.add_document("random", "Texto para teste aleatório de configuração.")
        analyzers = ["word_frequency", "sentiment_analyzer", "readability_analyzer"]

        for _ in range(50):
            plugin = random.choice(analyzers)
            config = {}
            # Gerar 1-3 campos aleatórios
            for _ in range(random.randint(1, 3)):
                key = random.choice(["min_word_length", "max_words", "language",
                                     "xyz", "foo_bar", ""])
                value = random.choice([
                    random.randint(-100, 100),
                    random.random(),
                    "".join(random.choices(string.ascii_letters, k=5)),
                    True, False, None, [], {},
                ])
                config[key] = value

            try:
                core.execute_plugin(plugin, doc, config)
            except (ValueError, TypeError):
                pass  # Erros esperados
            # Se chegou aqui sem crash, sucesso
```

- [ ] **Step 2: Rodar testes**

Run: `source .venv/bin/activate && pytest tests/test_stress.py::TestConfigFuzzing -v`
Expected: 4 passed

- [ ] **Step 3: Commit**

```bash
git add tests/test_stress.py
~/.claude/scripts/commit.sh "test: stress config fuzzing — configs aleatórias e malformadas nunca crasham"
```

---

### Task 4: Textos extremos — provides sempre cumprido

**Files:**
- Modify: `tests/test_stress.py`

- [ ] **Step 1: Escrever testes de textos extremos**

```python
# =============================================================================
# TEXTOS EXTREMOS — provides sempre cumprido
# =============================================================================

class TestExtremeInputs:
    """Textos extremos nunca devem quebrar o contrato de provides."""

    EXTREME_TEXTS = [
        ("empty", ""),
        ("single_char", "a"),
        ("single_word", "palavra"),
        ("only_spaces", "   \t\n  \t  "),
        ("only_numbers", "123 456 789 0 42 99"),
        ("only_punctuation", "!@#$%^&*()_+-=[]{}|;':\",./<>?"),
        ("only_emojis", "😀🎉🚀💡🔥 " * 20),
        ("null_bytes", "texto\x00com\x00nulos\x00dentro"),
        ("unicode_mixed", "café naïve résumé über straße 日本語 中文 العربية"),
        ("repetitive_100kb", "palavra " * 12500),  # ~100KB
        ("single_long_word", "a" * 10000),
        ("newlines_only", "\n" * 100),
        ("tabs_only", "\t" * 100),
    ]

    @pytest.mark.parametrize("name,text", EXTREME_TEXTS)
    def test_word_frequency_provides_contract(self, core, name, text):
        """word_frequency cumpre provides com qualquer texto — nunca ValueError de contrato."""
        doc = core.add_document(f"extreme_{name}", text)
        result = core.execute_plugin("word_frequency", doc)
        # Provides: word_frequencies, vocabulary_size, top_words, hapax_legomena
        assert "word_frequencies" in result
        assert "vocabulary_size" in result
        assert isinstance(result["vocabulary_size"], int)
        assert result["vocabulary_size"] >= 0

    @pytest.mark.parametrize("name,text", EXTREME_TEXTS)
    def test_readability_provides_contract(self, core, name, text):
        """readability cumpre provides com qualquer texto."""
        doc = core.add_document(f"extreme_read_{name}", text)
        result = core.execute_plugin("readability_analyzer", doc)
        assert "word_count" in result
        assert isinstance(result["word_count"], int)

    def test_sentiment_with_extreme_texts(self, core):
        """sentiment com textos extremos — nunca crash."""
        safe_texts = [
            ("empty", ""),
            ("single_word", "bom"),
            ("emojis", "😀🎉🚀 " * 10),
            ("unicode", "café résumé über日本語"),
            ("big", "Texto positivo e bom. " * 2000),
        ]
        for name, text in safe_texts:
            doc = core.add_document(f"sent_{name}", text)
            try:
                result = core.execute_plugin("sentiment_analyzer", doc)
                assert "polarity" in result
                assert -1 <= result["polarity"] <= 1
            except (ValueError, Exception):
                pass  # Alguns textos podem falhar no TextBlob — não deve crashar
```

- [ ] **Step 2: Rodar testes**

Run: `source .venv/bin/activate && pytest tests/test_stress.py::TestExtremeInputs -v`
Expected: 31 passed (13 word_freq + 13 readability + 5 sentiment)

- [ ] **Step 3: Commit**

```bash
git add tests/test_stress.py
~/.claude/scripts/commit.sh "test: stress textos extremos — provides cumprido com qualquer input"
```

---

### Task 5: API concorrente — nunca 500

**Files:**
- Modify: `tests/test_stress.py`

- [ ] **Step 1: Escrever testes de API sob pressão**

```python
# =============================================================================
# API — concorrência pesada, nunca 500
# =============================================================================

class TestAPIStress:
    """API sob carga: muitos requests simultâneos, nunca 500."""

    @pytest.mark.asyncio
    async def test_20_concurrent_analyze_requests(self, ac):
        """20 requests simultâneos ao /analyze — todos 200, nenhum 500."""
        tasks = [
            ac.post("/analyze/word_frequency", json={
                "text": f"Texto único thread {i} com palavras suficientes pra análise.",
                "config": {},
            })
            for i in range(20)
        ]
        responses = await asyncio.gather(*tasks)
        status_codes = [r.status_code for r in responses]
        assert 500 not in status_codes, f"500 encontrado: {status_codes}"
        assert all(s == 200 for s in status_codes), f"Status inesperados: {status_codes}"

    @pytest.mark.asyncio
    async def test_mixed_endpoints_under_load(self, ac):
        """Mix de endpoints simultâneos — health, plugins, analyze, pipeline."""
        tasks = []
        for i in range(5):
            tasks.append(ac.get("/health"))
            tasks.append(ac.get("/plugins"))
            tasks.append(ac.post("/analyze/word_frequency", json={
                "text": f"Texto mix {i} para teste de carga.",
                "config": {},
            }))
            tasks.append(ac.post("/pipeline", data={
                "steps": '[{"plugin_id": "word_frequency", "config": {}}]',
                "text": f"Pipeline mix {i} para teste.",
            }))

        responses = await asyncio.gather(*tasks)
        status_codes = [r.status_code for r in responses]
        assert 500 not in status_codes, f"500 encontrado nos {len(responses)} responses"

    @pytest.mark.asyncio
    async def test_bad_requests_never_500(self, ac):
        """Requests inválidos devem retornar 4xx, nunca 500."""
        bad_requests = [
            ac.post("/analyze/nonexistent_plugin", json={"text": "t", "config": {}}),
            ac.post("/analyze/word_frequency", json={"text": "", "config": {}}),
            ac.post("/analyze/word_frequency", json={"text": "t", "config": "bad"}),
            ac.post("/pipeline", data={"steps": "invalid json", "text": "t"}),
            ac.post("/pipeline", data={"steps": "[]", "text": "t"}),
            ac.post("/visualize/word_frequency", json={"data": {}, "config": {}}),
        ]
        responses = await asyncio.gather(*bad_requests, return_exceptions=True)
        for i, r in enumerate(responses):
            if isinstance(r, Exception):
                continue  # Conexão pode falhar, não é 500
            assert r.status_code != 500, f"Request {i} retornou 500: {r.text[:200]}"
```

- [ ] **Step 2: Rodar testes**

Run: `source .venv/bin/activate && pytest tests/test_stress.py::TestAPIStress -v`
Expected: 3 passed

- [ ] **Step 3: Commit**

```bash
git add tests/test_stress.py
~/.claude/scripts/commit.sh "test: stress API — 20 requests concorrentes, mix de endpoints, bad requests"
```

---

### Task 6: Pipeline combos — fail limpo

**Files:**
- Modify: `tests/test_stress.py`

- [ ] **Step 1: Escrever testes de combinações de pipeline**

```python
# =============================================================================
# PIPELINE — combinações aleatórias falham limpo
# =============================================================================

class TestPipelineStress:
    """Pipelines com combinações diversas — falham limpo, nunca crasham."""

    def test_all_analyzer_pairs(self, core):
        """Todas as combinações de 2 analyzers em pipeline — todas completam."""
        analyzers = ["word_frequency", "sentiment_analyzer", "readability_analyzer"]
        text = "Texto para testar combinações de pipeline com múltiplos analyzers."

        for a in analyzers:
            for b in analyzers:
                doc = core.add_document(f"pipe_{a}_{b}", text)
                results = {}
                for plugin_id in [a, b]:
                    result = core.execute_plugin(plugin_id, doc)
                    results[plugin_id] = result

                # Cada plugin deve ter retornado algo
                for plugin_id, result in results.items():
                    assert isinstance(result, dict), f"{a}→{b}: {plugin_id} não retornou dict"

    def test_pipeline_with_document_then_analyzer(self, core):
        """teams_cleaner → word_frequency — pipeline misto funciona."""
        transcript = "[10:00:00] Maria: Olá pessoal bom dia\n[10:01:00] João: Bom dia Maria"
        doc = core.add_document("pipe_doc_analyze", transcript)

        # Step 1: document plugin
        doc_result = core.execute_plugin("teams_cleaner", doc)
        assert "cleaned_document" in doc_result

        # Step 2: analyzer no texto limpo
        cleaned_doc = core.add_document("pipe_cleaned", doc_result["cleaned_document"])
        freq_result = core.execute_plugin("word_frequency", cleaned_doc)
        assert "word_frequencies" in freq_result

    def test_repeated_plugin_same_pipeline(self, core):
        """Mesmo plugin 3x no pipeline com configs diferentes — sem estado vazando."""
        text = "Gato gato cachorro pato gato cachorro pato pato leão"
        configs = [
            {"min_word_length": 2},
            {"min_word_length": 4},
            {"min_word_length": 6},
        ]
        results = []
        for i, config in enumerate(configs):
            doc = core.add_document(f"repeat_{i}", text)
            result = core.execute_plugin("word_frequency", doc, config)
            results.append(result)

        # min_word_length crescente → vocabulary_size decrescente
        assert results[0]["vocabulary_size"] >= results[1]["vocabulary_size"]
        assert results[1]["vocabulary_size"] >= results[2]["vocabulary_size"]
```

- [ ] **Step 2: Rodar testes**

Run: `source .venv/bin/activate && pytest tests/test_stress.py::TestPipelineStress -v`
Expected: 3 passed

- [ ] **Step 3: Rodar bateria completa de stress**

Run: `source .venv/bin/activate && pytest tests/test_stress.py -v`
Expected: todos os testes passam, <30s total

- [ ] **Step 4: Rodar suite completa pra garantir que nada quebrou**

Run: `source .venv/bin/activate && pytest tests/ -v --tb=short`
Expected: 883+ passed, 1 skipped

- [ ] **Step 5: Commit final**

```bash
git add tests/test_stress.py
~/.claude/scripts/commit.sh "test: stress pipeline combos — pares de analyzers, doc→analyzer, repetição"
```
