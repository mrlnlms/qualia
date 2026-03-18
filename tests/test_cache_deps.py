"""
Testes do CacheManager e DependencyResolver

Cobre cache hit/miss, corrupção, e resolução de dependências
com detecção de ciclos e resolução de field names.
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

def make_meta(plugin_id, requires=None, provides=None):
    return PluginMetadata(
        id=plugin_id,
        name=plugin_id,
        type=PluginType.ANALYZER,
        version="1.0",
        description="test",
        provides=provides or [],
        requires=requires or [],
        parameters={}
    )


class TestDependencyResolver:

    def test_no_dependencies(self, resolver):
        resolver.add_plugin("a", make_meta("a"))
        resolver.add_plugin("b", make_meta("b"))
        resolver.build_graph()
        result = resolver.resolve(["a", "b"])
        assert set(result) == {"a", "b"}

    def test_linear_order(self, resolver):
        resolver.add_plugin("a", make_meta("a"))
        resolver.add_plugin("b", make_meta("b", requires=["a"]))
        resolver.add_plugin("c", make_meta("c", requires=["b"]))
        resolver.build_graph()
        result = resolver.resolve(["c"])
        # a deve vir antes de b, b antes de c
        assert result.index("a") < result.index("b")
        assert result.index("b") < result.index("c")

    def test_cycle_detection(self, resolver):
        resolver.add_plugin("a", make_meta("a", requires=["b"]))
        resolver.add_plugin("b", make_meta("b", requires=["a"]))
        resolver.build_graph()
        with pytest.raises(ValueError, match="circular"):
            resolver.resolve(["a"])

    def test_transitive_dependencies(self, resolver):
        resolver.add_plugin("a", make_meta("a"))
        resolver.add_plugin("b", make_meta("b", requires=["a"]))
        resolver.add_plugin("c", make_meta("c", requires=["b"]))
        resolver.build_graph()
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
        resolver.build_graph()
        result = resolver.resolve(["a"])
        # d deve vir antes de b e c, ambos antes de a
        assert result.index("d") < result.index("b")
        assert result.index("d") < result.index("c")
        assert result.index("b") < result.index("a")
        assert result.index("c") < result.index("a")

    def test_single_plugin_no_deps(self, resolver):
        resolver.add_plugin("solo", make_meta("solo"))
        resolver.build_graph()
        result = resolver.resolve(["solo"])
        assert result == ["solo"]

    def test_empty_resolve(self, resolver):
        result = resolver.resolve([])
        assert result == []


class TestDependencyResolverFieldNames:
    """Testes de resolução field-name → plugin-ID"""

    def test_field_name_resolution(self, resolver):
        """requires por field name resolve pro provider"""
        resolver.add_plugin("provider", make_meta("provider", provides=["data_field"]))
        resolver.add_plugin("consumer", make_meta("consumer", requires=["data_field"]))
        resolver.build_graph()
        result = resolver.resolve(["consumer"])
        assert result == ["provider", "consumer"]

    def test_multiple_fields_same_provider(self, resolver):
        """Dois fields do mesmo provider = 1 dependência (sentiment_viz_plotly case)"""
        resolver.add_plugin("sentiment", make_meta(
            "sentiment", provides=["polarity", "subjectivity"]
        ))
        resolver.add_plugin("viz", make_meta(
            "viz", requires=["polarity", "subjectivity"]
        ))
        resolver.build_graph()
        result = resolver.resolve(["viz"])
        assert result == ["sentiment", "viz"]
        assert len(result) == 2  # sem duplicatas

    def test_missing_field_skipped(self, resolver):
        """Field sem provider é ignorado silenciosamente"""
        resolver.add_plugin("p", make_meta("p", requires=["nonexistent_field"]))
        resolver.build_graph()
        result = resolver.resolve(["p"])
        assert result == ["p"]

    def test_resolve_provider(self, resolver):
        """resolve_provider retorna plugin_id correto"""
        resolver.add_plugin("wf", make_meta("wf", provides=["word_frequencies"]))
        assert resolver.resolve_provider("word_frequencies") == "wf"
        assert resolver.resolve_provider("nonexistent") is None

    def test_real_plugin_graph(self, resolver):
        """Simula grafo real do Qualia"""
        resolver.add_plugin("word_frequency", make_meta(
            "word_frequency", provides=["word_frequencies"]
        ))
        resolver.add_plugin("wordcloud_d3", make_meta(
            "wordcloud_d3", requires=["word_frequencies"]
        ))
        resolver.add_plugin("sentiment_analyzer", make_meta(
            "sentiment_analyzer", provides=["polarity", "subjectivity"]
        ))
        resolver.add_plugin("sentiment_viz_plotly", make_meta(
            "sentiment_viz_plotly", requires=["polarity", "subjectivity"]
        ))
        resolver.build_graph()

        result = resolver.resolve(["wordcloud_d3"])
        assert result.index("word_frequency") < result.index("wordcloud_d3")

        result = resolver.resolve(["sentiment_viz_plotly"])
        assert result.index("sentiment_analyzer") < result.index("sentiment_viz_plotly")

    def test_cycle_through_field_names(self, resolver):
        """Ciclo detectado mesmo quando deps são field names"""
        resolver.add_plugin("a", make_meta("a", provides=["field_a"], requires=["field_b"]))
        resolver.add_plugin("b", make_meta("b", provides=["field_b"], requires=["field_a"]))
        resolver.build_graph()
        with pytest.raises(ValueError, match="circular"):
            resolver.resolve(["a"])

    def test_plugin_id_takes_precedence_over_field_name(self, resolver):
        """Se req é plugin ID conhecido, usa direto (não busca no provides_map)"""
        resolver.add_plugin("analyzer", make_meta(
            "analyzer", provides=["analyzer_data"]
        ))
        # "analyzer" é tanto plugin ID quanto potencialmente um field name
        resolver.add_plugin("consumer", make_meta("consumer", requires=["analyzer"]))
        resolver.build_graph()
        result = resolver.resolve(["consumer"])
        assert result == ["analyzer", "consumer"]


class TestMultipleProviders:
    """Testes de múltiplos providers — plugins podem declarar o mesmo campo"""

    def test_two_plugins_same_provides_coexist(self, resolver):
        """Dois plugins com mesmo provides registram sem erro"""
        resolver.add_plugin("plugin_a", make_meta("plugin_a", provides=["shared_field"]))
        resolver.add_plugin("plugin_b", make_meta("plugin_b", provides=["shared_field"]))
        assert resolver.list_providers("shared_field") == ["plugin_a", "plugin_b"]

    def test_three_plugins_same_provides(self, resolver):
        """Três plugins com mesmo provides registram todos"""
        resolver.add_plugin("a", make_meta("a", provides=["score"]))
        resolver.add_plugin("b", make_meta("b", provides=["score"]))
        resolver.add_plugin("c", make_meta("c", provides=["score"]))
        assert resolver.list_providers("score") == ["a", "b", "c"]

    def test_no_collision_different_fields(self, resolver):
        """Campos distintos — cada um com provider único"""
        resolver.add_plugin("plugin_a", make_meta("plugin_a", provides=["field_a"]))
        resolver.add_plugin("plugin_b", make_meta("plugin_b", provides=["field_b"]))
        assert resolver.resolve_provider("field_a") == "plugin_a"
        assert resolver.resolve_provider("field_b") == "plugin_b"

    def test_resolve_provider_ambiguous_returns_none(self, resolver):
        """resolve_provider retorna None quando campo tem múltiplos providers"""
        resolver.add_plugin("first", make_meta("first", provides=["language"]))
        resolver.add_plugin("second", make_meta("second", provides=["language"]))
        assert resolver.resolve_provider("language") is None

    def test_resolve_provider_unique_returns_id(self, resolver):
        """resolve_provider retorna plugin_id quando campo tem provider único"""
        resolver.add_plugin("only", make_meta("only", provides=["unique_field"]))
        assert resolver.resolve_provider("unique_field") == "only"

    def test_list_providers_empty(self, resolver):
        """list_providers retorna lista vazia pra campo inexistente"""
        assert resolver.list_providers("nonexistent") == []

    def test_build_graph_ambiguous_skips_dep(self, resolver):
        """build_graph não resolve dependência quando provider é ambíguo"""
        resolver.add_plugin("provider_a", make_meta("provider_a", provides=["data"]))
        resolver.add_plugin("provider_b", make_meta("provider_b", provides=["data"]))
        resolver.add_plugin("consumer", make_meta("consumer", requires=["data"]))
        resolver.build_graph()
        # consumer não tem deps resolvidas (ambíguo)
        assert resolver.graph["consumer"] == set()

    def test_empty_provides_no_collision(self, resolver):
        """Plugins sem provides nunca colidem"""
        resolver.add_plugin("viz_a", make_meta("viz_a", provides=[]))
        resolver.add_plugin("viz_b", make_meta("viz_b", provides=[]))
        # Sem erro
