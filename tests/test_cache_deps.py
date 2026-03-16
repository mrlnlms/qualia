"""
Testes do CacheManager e DependencyResolver

Cobre cache hit/miss, corrupção, e resolução de dependências
com detecção de ciclos.
"""

import pytest
import pickle
from pathlib import Path
import tempfile
import shutil

from qualia.core import CacheManager, DependencyResolver, PluginMetadata, PluginType


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
    return CacheManager(cache_dir)


@pytest.fixture
def resolver():
    return DependencyResolver()


# =============================================================================
# CACHE MANAGER
# =============================================================================

class TestCacheManager:

    def test_set_and_get(self, cache):
        result = {"word_frequencies": {"gato": 3}}
        cache.set("doc1", "word_frequency", {"min_length": 3}, result)
        cached = cache.get("doc1", "word_frequency", {"min_length": 3})
        assert cached == result

    def test_cache_miss(self, cache):
        cached = cache.get("nonexistent", "plugin", {})
        assert cached is None

    def test_different_config_is_miss(self, cache):
        result = {"count": 1}
        cache.set("doc1", "plugin", {"param": "a"}, result)
        cached = cache.get("doc1", "plugin", {"param": "b"})
        assert cached is None

    def test_same_config_is_hit(self, cache):
        result = {"count": 1}
        cache.set("doc1", "plugin", {"x": 1, "y": 2}, result)
        # Mesma config, ordem diferente das chaves — deve ser hit
        # (json.dumps com sort_keys=True garante isso)
        cached = cache.get("doc1", "plugin", {"y": 2, "x": 1})
        assert cached == result

    def test_different_doc_is_miss(self, cache):
        result = {"count": 1}
        cache.set("doc1", "plugin", {}, result)
        cached = cache.get("doc2", "plugin", {})
        assert cached is None

    def test_corrupt_cache_returns_none(self, cache, cache_dir):
        """Cache corrompido retorna None e limpa o arquivo"""
        cache.set("doc1", "plugin", {}, {"data": 1})

        # Corromper o arquivo de cache
        cache_files = list(cache_dir.glob("*.pkl"))
        assert len(cache_files) == 1
        cache_files[0].write_bytes(b"corrupted data")

        cached = cache.get("doc1", "plugin", {})
        assert cached is None
        # Arquivo corrompido deve ter sido removido
        assert not cache_files[0].exists()

    def test_overwrite_cache(self, cache):
        cache.set("doc1", "plugin", {}, {"v": 1})
        cache.set("doc1", "plugin", {}, {"v": 2})
        cached = cache.get("doc1", "plugin", {})
        assert cached["v"] == 2

    def test_cache_dir_created(self, cache_dir):
        new_dir = cache_dir / "sub" / "cache"
        cm = CacheManager(new_dir)
        assert new_dir.exists()


# =============================================================================
# DEPENDENCY RESOLVER
# =============================================================================

def make_meta(plugin_id, requires=None):
    return PluginMetadata(
        id=plugin_id,
        name=plugin_id,
        type=PluginType.ANALYZER,
        version="1.0",
        description="test",
        provides=[],
        requires=requires or [],
        parameters={}
    )


class TestDependencyResolver:

    def test_no_dependencies(self, resolver):
        resolver.add_plugin("a", make_meta("a"))
        resolver.add_plugin("b", make_meta("b"))
        result = resolver.resolve(["a", "b"])
        assert set(result) == {"a", "b"}

    def test_linear_order(self, resolver):
        resolver.add_plugin("a", make_meta("a"))
        resolver.add_plugin("b", make_meta("b", requires=["a"]))
        resolver.add_plugin("c", make_meta("c", requires=["b"]))
        result = resolver.resolve(["c"])
        # a deve vir antes de b, b antes de c
        assert result.index("a") < result.index("b")
        assert result.index("b") < result.index("c")

    def test_cycle_detection(self, resolver):
        resolver.add_plugin("a", make_meta("a", requires=["b"]))
        resolver.add_plugin("b", make_meta("b", requires=["a"]))
        with pytest.raises(ValueError, match="circular"):
            resolver.resolve(["a"])

    def test_transitive_dependencies(self, resolver):
        resolver.add_plugin("a", make_meta("a"))
        resolver.add_plugin("b", make_meta("b", requires=["a"]))
        resolver.add_plugin("c", make_meta("c", requires=["b"]))
        # Pedir só c, mas a e b devem ser incluídos
        result = resolver.resolve(["c"])
        assert "a" in result
        assert "b" in result
        assert "c" in result

    def test_diamond_dependency(self, resolver):
        """A depende de B e C, ambos dependem de D"""
        resolver.add_plugin("d", make_meta("d"))
        resolver.add_plugin("b", make_meta("b", requires=["d"]))
        resolver.add_plugin("c", make_meta("c", requires=["d"]))
        resolver.add_plugin("a", make_meta("a", requires=["b", "c"]))
        result = resolver.resolve(["a"])
        # d deve vir antes de b e c, ambos antes de a
        assert result.index("d") < result.index("b")
        assert result.index("d") < result.index("c")
        assert result.index("b") < result.index("a")
        assert result.index("c") < result.index("a")

    def test_single_plugin_no_deps(self, resolver):
        resolver.add_plugin("solo", make_meta("solo"))
        result = resolver.resolve(["solo"])
        assert result == ["solo"]

    def test_empty_resolve(self, resolver):
        result = resolver.resolve([])
        assert result == []
