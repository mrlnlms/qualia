"""Testes do discovery recursivo de plugins."""

import pytest
from pathlib import Path
from qualia.core.loader import PluginLoader


@pytest.fixture
def plugin_tree(tmp_path):
    """Cria árvore de plugins em múltiplos níveis."""
    # Plugin flat (nível 1) — como hoje
    flat = tmp_path / "flat_plugin"
    flat.mkdir()
    (flat / "__init__.py").write_text('''
from qualia.core import BaseAnalyzerPlugin, PluginMetadata, PluginType, Document

class FlatAnalyzer(BaseAnalyzerPlugin):
    def meta(self):
        return PluginMetadata(
            id="flat_plugin", name="Flat", type=PluginType.ANALYZER,
            version="0.1.0", description="flat", provides=["flat_result"],
        )
    def _analyze_impl(self, doc, config, ctx):
        return {"flat_result": True}
''')

    # Plugin nested (nível 2) — plugins/analyzers/nested_plugin/
    analyzers = tmp_path / "analyzers"
    analyzers.mkdir()
    nested = analyzers / "nested_plugin"
    nested.mkdir()
    (nested / "__init__.py").write_text('''
from qualia.core import BaseAnalyzerPlugin, PluginMetadata, PluginType, Document

class NestedAnalyzer(BaseAnalyzerPlugin):
    def meta(self):
        return PluginMetadata(
            id="nested_plugin", name="Nested", type=PluginType.ANALYZER,
            version="0.1.0", description="nested", provides=["nested_result"],
        )
    def _analyze_impl(self, doc, config, ctx):
        return {"nested_result": True}
''')

    # Plugin deep (nível 3) — plugins/documents/cleaners/deep_plugin/
    cleaners = tmp_path / "documents" / "cleaners"
    cleaners.mkdir(parents=True)
    deep = cleaners / "deep_plugin"
    deep.mkdir()
    (deep / "__init__.py").write_text('''
from qualia.core import BaseDocumentPlugin, PluginMetadata, PluginType, Document

class DeepProcessor(BaseDocumentPlugin):
    def meta(self):
        return PluginMetadata(
            id="deep_plugin", name="Deep", type=PluginType.DOCUMENT,
            version="0.1.0", description="deep",
            provides=["cleaned_document", "quality_report"],
        )
    def _process_impl(self, doc, config, ctx):
        return {"cleaned_document": doc.content, "quality_report": {}}
''')

    # Pasta _templates (deve ser ignorada)
    templates = tmp_path / "_templates"
    templates.mkdir()
    (templates / "analyzer.py").write_text("# template, not a plugin")

    return tmp_path


class TestRecursiveDiscovery:

    def test_discovers_flat_plugin(self, plugin_tree):
        """Plugins no nível 1 continuam funcionando"""
        loader = PluginLoader(plugin_tree)
        discovered = loader.discover()
        assert "flat_plugin" in discovered

    def test_discovers_nested_plugin(self, plugin_tree):
        """Plugins no nível 2 são descobertos"""
        loader = PluginLoader(plugin_tree)
        discovered = loader.discover()
        assert "nested_plugin" in discovered

    def test_discovers_deep_plugin(self, plugin_tree):
        """Plugins no nível 3 são descobertos"""
        loader = PluginLoader(plugin_tree)
        discovered = loader.discover()
        assert "deep_plugin" in discovered

    def test_ignores_underscore_dirs(self, plugin_tree):
        """Pastas com _ no início são ignoradas"""
        loader = PluginLoader(plugin_tree)
        discovered = loader.discover()
        for pid in discovered:
            assert not pid.startswith("_")

    def test_discovers_all_plugins(self, plugin_tree):
        """Descobre todos os 3 plugins em todos os níveis"""
        loader = PluginLoader(plugin_tree)
        discovered = loader.discover()
        assert len(discovered) == 3
        assert set(discovered.keys()) == {"flat_plugin", "nested_plugin", "deep_plugin"}

    def test_empty_dir_no_error(self, tmp_path):
        """Diretório vazio não causa erro"""
        loader = PluginLoader(tmp_path)
        discovered = loader.discover()
        assert discovered == {}

    def test_nonexistent_dir_no_error(self, tmp_path):
        """Diretório inexistente não causa erro"""
        loader = PluginLoader(tmp_path / "nonexistent")
        discovered = loader.discover()
        assert discovered == {}

    def test_duplicate_id_raises(self, plugin_tree):
        """Plugin com ID duplicado em subpasta diferente levanta ValueError"""
        dup = plugin_tree / "visualizers" / "flat_plugin"
        dup.mkdir(parents=True)
        (dup / "__init__.py").write_text('''
from qualia.core import BaseAnalyzerPlugin, PluginMetadata, PluginType, Document

class DupAnalyzer(BaseAnalyzerPlugin):
    def meta(self):
        return PluginMetadata(
            id="flat_plugin", name="Dup", type=PluginType.ANALYZER,
            version="0.1.0", description="dup", provides=["dup_result"],
        )
    def _analyze_impl(self, doc, config, ctx):
        return {"dup_result": True}
''')
        loader = PluginLoader(plugin_tree)
        with pytest.raises(ValueError, match="duplicado"):
            loader.discover()
