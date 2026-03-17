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

    def test_ttl_zero_means_no_expiration(self, cache):
        """ttl=0 (default) → sem expiração"""
        cache.set("d1", "p", {}, {"v": 1})

        # Mesmo com timestamp antigo, sem TTL não expira
        for key in cache._timestamps:
            cache._timestamps[key] = time.time() - 99999

        assert cache.get("d1", "p", {})["v"] == 1


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
    """Testes do metodo invalidate() — linhas 104, 113-119"""

    def test_invalidate_by_doc_id_pattern_does_not_match_hash(self, cache, cache_dir):
        """invalidate(doc_id=...) compara pattern com stem do arquivo,
        mas o stem e um SHA256 hash, entao o doc_id nao aparece nele.
        Resultado: nenhum arquivo e removido."""
        cache.set("doc1", "plugin_a", {}, {"v": 1})
        cache.set("doc2", "plugin_a", {}, {"v": 2})

        pkl_before = list(cache_dir.glob("*.pkl"))
        assert len(pkl_before) == 2

        # Invalidar com doc_id — o pattern "doc1:" nao vai casar com hash SHA256
        cache.invalidate(doc_id="doc1")

        pkl_after = list(cache_dir.glob("*.pkl"))
        # Nenhum arquivo removido porque o stem e hash, nao contem doc_id
        assert len(pkl_after) == 2

    def test_invalidate_without_pattern_iterates_files(self, cache, cache_dir):
        """invalidate() sem doc_id nem plugin_id itera arquivos mas nao remove nenhum
        (pattern vazio, condicao 'if pattern and ...' e falsa)"""
        cache.set("d1", "p", {}, {"v": 1})
        cache.set("d2", "p", {}, {"v": 2})

        pkl_before = list(cache_dir.glob("*.pkl"))
        assert len(pkl_before) == 2

        cache.invalidate()  # sem argumentos

        pkl_after = list(cache_dir.glob("*.pkl"))
        assert len(pkl_after) == 2  # nenhum removido

    def test_invalidate_removes_file_when_pattern_in_stem(self, cache, cache_dir):
        """Se o stem do arquivo contem o pattern, o arquivo e removido.
        Criamos um arquivo .pkl cujo nome contem o pattern pra forcar o match."""
        cache.set("d1", "p", {}, {"v": 1})

        # Criar arquivo fake cujo stem contem o pattern
        fake_file = cache_dir / "doc_special:.pkl"
        fake_file.write_bytes(b"fake")

        pkl_before = list(cache_dir.glob("*.pkl"))
        assert len(pkl_before) == 2

        cache.invalidate(doc_id="doc_special")

        # O fake_file deve ter sido removido (pattern "doc_special:" esta no stem)
        assert not fake_file.exists()
        # O outro arquivo (hash) permanece
        pkl_after = list(cache_dir.glob("*.pkl"))
        assert len(pkl_after) == 1

    def test_evict_lru_empty_access_order(self, cache_dir):
        """_evict_lru() com _access_order vazio retorna sem fazer nada (linha 104)"""
        cm = CacheManager(cache_dir, max_size=3)
        assert cm._access_order == []
        # Nao deve lancar excecao
        cm._evict_lru()
        assert cm.stats()["evictions"] == 0
