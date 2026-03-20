"""
Testes do CacheManager com LRU e TTL.

Valida eviction, expiração, stats e backward compatibility.
"""

import pytest
import time
from pathlib import Path
import tempfile
import shutil
from unittest.mock import patch

from qualia.core import CacheManager


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def cache_dir():
    temp = tempfile.mkdtemp()
    yield Path(temp)
    shutil.rmtree(temp)


@pytest.fixture
def cache(cache_dir):
    """Cache padrão (sem limites — backward compatible)"""
    return CacheManager(cache_dir)


@pytest.fixture
def lru_cache(cache_dir):
    """Cache com max_size=3"""
    return CacheManager(cache_dir, max_size=3)


@pytest.fixture
def ttl_cache(cache_dir):
    """Cache com TTL de 1 segundo"""
    return CacheManager(cache_dir, ttl=1)


# =============================================================================
# LRU EVICTION
# =============================================================================

class TestLRUEviction:

    def test_evicts_oldest_when_full(self, lru_cache):
        """max_size=3, add 4 → mais antigo evictado"""
        lru_cache.set("d1", "p", {}, {"v": 1})
        lru_cache.set("d2", "p", {}, {"v": 2})
        lru_cache.set("d3", "p", {}, {"v": 3})
        lru_cache.set("d4", "p", {}, {"v": 4})  # d1 deve ser evictado

        assert lru_cache.get("d1", "p", {}) is None
        assert lru_cache.get("d2", "p", {})["v"] == 2
        assert lru_cache.get("d3", "p", {})["v"] == 3
        assert lru_cache.get("d4", "p", {})["v"] == 4

    def test_get_updates_lru_order(self, lru_cache):
        """get() move item pro mais recente, evitando eviction"""
        lru_cache.set("d1", "p", {}, {"v": 1})
        lru_cache.set("d2", "p", {}, {"v": 2})
        lru_cache.set("d3", "p", {}, {"v": 3})

        # Acessar d1 (move pro fim)
        lru_cache.get("d1", "p", {})

        # Adicionar d4 — d2 deve ser evictado (era o mais antigo agora)
        lru_cache.set("d4", "p", {}, {"v": 4})

        assert lru_cache.get("d1", "p", {})["v"] == 1  # Sobreviveu
        assert lru_cache.get("d2", "p", {}) is None     # Evictado
        assert lru_cache.get("d3", "p", {})["v"] == 3
        assert lru_cache.get("d4", "p", {})["v"] == 4

    def test_eviction_counted_in_stats(self, lru_cache):
        for i in range(5):
            lru_cache.set(f"d{i}", "p", {}, {"v": i})
        stats = lru_cache.stats()
        assert stats["evictions"] == 2  # 5 - 3 = 2 evictions

    def test_overwrite_does_not_evict(self, lru_cache):
        """Sobrescrever mesma chave não conta como nova entrada"""
        lru_cache.set("d1", "p", {}, {"v": 1})
        lru_cache.set("d2", "p", {}, {"v": 2})
        lru_cache.set("d3", "p", {}, {"v": 3})
        # Sobrescrever d1 — não deve evictar ninguém
        lru_cache.set("d1", "p", {}, {"v": 10})

        assert lru_cache.get("d1", "p", {})["v"] == 10
        assert lru_cache.get("d2", "p", {})["v"] == 2
        assert lru_cache.get("d3", "p", {})["v"] == 3
        assert lru_cache.stats()["evictions"] == 0

    def test_max_size_zero_means_unlimited(self, cache):
        """max_size=0 (default) → sem limite de entradas"""
        for i in range(100):
            cache.set(f"d{i}", "p", {}, {"v": i})
        # Todos devem estar lá
        assert cache.get("d0", "p", {})["v"] == 0
        assert cache.get("d99", "p", {})["v"] == 99
        assert cache.stats()["evictions"] == 0


# =============================================================================
# TTL EXPIRATION
# =============================================================================

class TestTTLExpiration:

    def test_expired_item_returns_none(self, ttl_cache):
        """Item expira após TTL"""
        ttl_cache.set("d1", "p", {}, {"v": 1})

        # Mock time pra simular que passou o TTL
        original_time = ttl_cache._timestamps["d1".join("") or list(ttl_cache._timestamps.keys())[0]]
        # Forçar timestamp antigo
        for key in ttl_cache._timestamps:
            ttl_cache._timestamps[key] = time.time() - 2  # 2s atrás, TTL é 1s

        assert ttl_cache.get("d1", "p", {}) is None

    def test_item_within_ttl_returns_ok(self, ttl_cache):
        """Item dentro do TTL retorna normalmente"""
        ttl_cache.set("d1", "p", {}, {"v": 1})
        # Sem delay — está dentro do TTL
        assert ttl_cache.get("d1", "p", {})["v"] == 1

    def test_expired_file_is_cleaned(self, ttl_cache, cache_dir):
        """Arquivo de item expirado é removido do disco"""
        ttl_cache.set("d1", "p", {}, {"v": 1})
        pkl_files_before = list(cache_dir.glob("*.pkl"))
        assert len(pkl_files_before) == 1

        # Forçar expiração
        for key in ttl_cache._timestamps:
            ttl_cache._timestamps[key] = time.time() - 2

        ttl_cache.get("d1", "p", {})  # Trigger cleanup
        pkl_files_after = list(cache_dir.glob("*.pkl"))
        assert len(pkl_files_after) == 0

    def test_expired_item_cleans_reverse_index(self, ttl_cache):
        """TTL expiration limpa índices reversos (sem chaves zumbis)"""
        ttl_cache.set("d1", "p", {}, {"v": 1})
        assert "d1" in ttl_cache._doc_index
        assert "p" in ttl_cache._plugin_index

        for key in ttl_cache._timestamps:
            ttl_cache._timestamps[key] = time.time() - 2

        ttl_cache.get("d1", "p", {})  # trigger cleanup
        assert "d1" not in ttl_cache._doc_index
        assert "p" not in ttl_cache._plugin_index

    def test_ttl_zero_means_no_expiration(self, cache):
        """ttl=0 (default) → sem expiração"""
        cache.set("d1", "p", {}, {"v": 1})

        # Mesmo com timestamp antigo, sem TTL não expira
        for key in cache._timestamps:
            cache._timestamps[key] = time.time() - 99999

        assert cache.get("d1", "p", {})["v"] == 1


# =============================================================================
# PERSISTÊNCIA ENTRE INSTÂNCIAS (simulação de restart)
# =============================================================================

class TestCachePersistence:
    """Cache em disco deve sobreviver a restart do processo."""

    def test_cache_survives_new_instance(self, cache_dir):
        """Dado gravado por instância A deve ser lido por instância B."""
        cache_a = CacheManager(cache_dir)
        cache_a.set("doc1", "word_frequency", {"lang": "pt"}, {"total": 42})

        # Verificar que .pkl existe
        pkl_files = list(cache_dir.glob("*.pkl"))
        assert len(pkl_files) == 1

        # Nova instância (simula restart) — índice reconstruído do disco
        cache_b = CacheManager(cache_dir)
        assert len(cache_b._access_order) == 1  # reconstruído via _rebuild_index

        # Deve recuperar o dado do disco
        result = cache_b.get("doc1", "word_frequency", {"lang": "pt"})
        assert result is not None
        assert result["total"] == 42
        assert cache_b._hits == 1
        assert len(cache_b._access_order) == 1

    def test_cache_miss_on_different_config(self, cache_dir):
        """Config diferente não acha o dado mesmo com .pkl no disco."""
        cache_a = CacheManager(cache_dir)
        cache_a.set("doc1", "p", {"a": 1}, {"v": 1})

        cache_b = CacheManager(cache_dir)
        result = cache_b.get("doc1", "p", {"a": 2})
        assert result is None

    def test_lru_works_after_reload(self, cache_dir):
        """LRU eviction funciona corretamente com dados recarregados do disco."""
        cache_a = CacheManager(cache_dir, max_size=2)
        cache_a.set("d1", "p", {}, {"v": 1})
        cache_a.set("d2", "p", {}, {"v": 2})

        # Nova instância com max_size=2
        cache_b = CacheManager(cache_dir, max_size=2)

        # Recarregar ambos
        cache_b.get("d1", "p", {})
        cache_b.get("d2", "p", {})

        # Adicionar terceiro — deve evictar d1 (LRU)
        cache_b.set("d3", "p", {}, {"v": 3})
        assert cache_b.get("d3", "p", {})["v"] == 3
        assert len(cache_b._access_order) == 2


# =============================================================================
# STATS
# =============================================================================

class TestCacheStats:

    def test_stats_structure(self, cache):
        stats = cache.stats()
        assert "size" in stats
        assert "max_size" in stats
        assert "ttl" in stats
        assert "hits" in stats
        assert "misses" in stats
        assert "evictions" in stats

    def test_hits_and_misses(self, cache):
        cache.set("d1", "p", {}, {"v": 1})
        cache.get("d1", "p", {})       # hit
        cache.get("d1", "p", {})       # hit
        cache.get("d2", "p", {})       # miss
        cache.get("nonexist", "x", {}) # miss

        stats = cache.stats()
        assert stats["hits"] == 2
        assert stats["misses"] == 2

    def test_cache_stats_api_endpoint(self, client):
        """GET /cache/stats retorna JSON"""
        response = client.get("/cache/stats")
        assert response.status_code == 200
        data = response.json()
        assert "size" in data
        assert "hits" in data
        assert "misses" in data


# =============================================================================
# BACKWARD COMPATIBILITY
# =============================================================================

class TestBackwardCompat:

    def test_default_constructor_works(self, cache_dir):
        """Constructor sem max_size/ttl se comporta como antes"""
        cm = CacheManager(cache_dir)
        cm.set("d1", "p", {}, {"v": 1})
        assert cm.get("d1", "p", {})["v"] == 1

    def test_clear_empties_everything(self, cache):
        for i in range(5):
            cache.set(f"d{i}", "p", {}, {"v": i})
        cache.get("d0", "p", {})  # gerar hit

        cache.clear()
        stats = cache.stats()
        assert stats["size"] == 0
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["evictions"] == 0

        # Todos devem retornar None
        for i in range(5):
            assert cache.get(f"d{i}", "p", {}) is None

    def test_corrupt_cache_cleans_reverse_index(self, cache, cache_dir):
        """Arquivo corrompido limpa índices reversos (sem chaves zumbis)"""
        cache.set("d1", "p", {}, {"v": 1})
        assert "d1" in cache._doc_index

        # Corromper o arquivo
        for pkl in cache_dir.glob("*.pkl"):
            pkl.write_bytes(b"corrupted")

        cache.get("d1", "p", {})  # trigger cleanup
        assert "d1" not in cache._doc_index
        assert "p" not in cache._plugin_index

    def test_existing_cache_tests_still_pass(self, cache):
        """Reproduz cenários do test_cache_deps.py pra garantir regressão"""
        # set and get
        result = {"word_frequencies": {"gato": 3}}
        cache.set("doc1", "word_frequency", {"min_length": 3}, result)
        cached = cache.get("doc1", "word_frequency", {"min_length": 3})
        assert cached == result

        # different config is miss
        assert cache.get("doc1", "word_frequency", {"min_length": 5}) is None

        # same config different key order is hit
        cache.set("doc2", "p", {"x": 1, "y": 2}, {"ok": True})
        assert cache.get("doc2", "p", {"y": 2, "x": 1})["ok"] is True


# =============================================================================
# INVALIDATE
# =============================================================================

class TestCacheInvalidate:
    """Testes de invalidação seletiva por doc_id e/ou plugin_id."""

    def test_invalidate_by_doc_id(self, cache, cache_dir):
        """invalidate(doc_id=X) remove apenas entradas daquele documento"""
        cache.set("doc1", "plugin_a", {}, {"v": 1})
        cache.set("doc1", "plugin_b", {}, {"v": 2})
        cache.set("doc2", "plugin_a", {}, {"v": 3})

        cache.invalidate(doc_id="doc1")

        assert cache.get("doc1", "plugin_a", {}) is None
        assert cache.get("doc1", "plugin_b", {}) is None
        assert cache.get("doc2", "plugin_a", {})["v"] == 3

    def test_invalidate_by_plugin_id(self, cache, cache_dir):
        """invalidate(plugin_id=X) remove apenas entradas daquele plugin"""
        cache.set("doc1", "plugin_a", {}, {"v": 1})
        cache.set("doc2", "plugin_a", {}, {"v": 2})
        cache.set("doc1", "plugin_b", {}, {"v": 3})

        cache.invalidate(plugin_id="plugin_a")

        assert cache.get("doc1", "plugin_a", {}) is None
        assert cache.get("doc2", "plugin_a", {}) is None
        assert cache.get("doc1", "plugin_b", {})["v"] == 3

    def test_invalidate_by_doc_and_plugin(self, cache, cache_dir):
        """invalidate(doc_id=X, plugin_id=Y) remove apenas a intersecção"""
        cache.set("doc1", "plugin_a", {}, {"v": 1})
        cache.set("doc1", "plugin_a", {"x": 1}, {"v": 2})
        cache.set("doc1", "plugin_b", {}, {"v": 3})
        cache.set("doc2", "plugin_a", {}, {"v": 4})

        cache.invalidate(doc_id="doc1", plugin_id="plugin_a")

        assert cache.get("doc1", "plugin_a", {}) is None
        assert cache.get("doc1", "plugin_a", {"x": 1}) is None
        assert cache.get("doc1", "plugin_b", {})["v"] == 3
        assert cache.get("doc2", "plugin_a", {})["v"] == 4

    def test_invalidate_without_args_does_nothing(self, cache, cache_dir):
        """invalidate() sem argumentos não remove nada"""
        cache.set("d1", "p", {}, {"v": 1})
        cache.invalidate()
        assert cache.get("d1", "p", {})["v"] == 1

    def test_invalidate_updates_stats_and_tracking(self, cache):
        """invalidate() limpa access_order e timestamps das chaves removidas"""
        cache.set("doc1", "p", {}, {"v": 1})
        cache.set("doc2", "p", {}, {"v": 2})
        assert cache.stats()["size"] == 2

        cache.invalidate(doc_id="doc1")
        assert cache.stats()["size"] == 1

    def test_invalidate_removes_files_from_disk(self, cache, cache_dir):
        """invalidate() remove os .pkl correspondentes do disco"""
        cache.set("doc1", "p", {}, {"v": 1})
        cache.set("doc2", "p", {}, {"v": 2})
        assert len(list(cache_dir.glob("*.pkl"))) == 2

        cache.invalidate(doc_id="doc1")
        assert len(list(cache_dir.glob("*.pkl"))) == 1

    def test_invalidate_cleans_empty_buckets(self, cache):
        """Buckets vazios são removidos dos índices após invalidação"""
        cache.set("doc1", "plugin_a", {}, {"v": 1})
        assert "doc1" in cache._doc_index
        assert "plugin_a" in cache._plugin_index

        cache.invalidate(doc_id="doc1")
        assert "doc1" not in cache._doc_index
        # plugin_a bucket também vazio → removido
        assert "plugin_a" not in cache._plugin_index

    def test_evict_lru_cleans_empty_buckets(self, cache_dir):
        """LRU eviction remove buckets vazios dos índices"""
        lru = CacheManager(cache_dir, max_size=1)
        lru.set("d1", "p1", {}, {"v": 1})
        lru.set("d2", "p2", {}, {"v": 2})  # evicta d1

        assert "d1" not in lru._doc_index
        assert "p1" not in lru._plugin_index
        assert "d2" in lru._doc_index
        assert "p2" in lru._plugin_index

    def test_evict_lru_empty_access_order(self, cache_dir):
        """_evict_lru() com _access_order vazio retorna sem fazer nada"""
        cm = CacheManager(cache_dir, max_size=3)
        assert len(cm._access_order) == 0
        cm._evict_lru()
        assert cm.stats()["evictions"] == 0


# =============================================================================
# INVALIDATE AFTER RESTART (index persistence)
# =============================================================================

class TestInvalidateAfterRestart:
    """Testes de invalidação após restart — depende de .cache_index.json."""

    def test_invalidate_after_restart(self, cache_dir):
        """invalidate(doc_id=...) funciona após criar nova instância (restart)"""
        cache_a = CacheManager(cache_dir)
        cache_a.set("doc1", "plugin_a", {}, {"v": 1})
        cache_a.set("doc2", "plugin_a", {}, {"v": 2})

        # Nova instância simula restart — índice reconstruído do disco
        cache_b = CacheManager(cache_dir)
        cache_b.invalidate(doc_id="doc1")

        assert cache_b.get("doc1", "plugin_a", {}) is None
        assert cache_b.get("doc2", "plugin_a", {})["v"] == 2

    def test_invalidate_by_plugin_after_restart(self, cache_dir):
        """invalidate(plugin_id=...) funciona após restart"""
        cache_a = CacheManager(cache_dir)
        cache_a.set("doc1", "plugin_a", {}, {"v": 1})
        cache_a.set("doc1", "plugin_b", {}, {"v": 2})
        cache_a.set("doc2", "plugin_a", {}, {"v": 3})

        cache_b = CacheManager(cache_dir)
        cache_b.invalidate(plugin_id="plugin_a")

        assert cache_b.get("doc1", "plugin_a", {}) is None
        assert cache_b.get("doc2", "plugin_a", {}) is None
        assert cache_b.get("doc1", "plugin_b", {})["v"] == 2

    def test_clear_removes_index_file(self, cache_dir):
        """clear() deve remover .cache_index.json do disco"""
        cache = CacheManager(cache_dir)
        cache.set("doc1", "plugin_a", {}, {"v": 1})

        index_file = cache_dir / ".cache_index.json"
        assert index_file.exists()

        cache.clear()
        assert not index_file.exists()
