# tests/test_loader_errors.py
"""Testes para exposição de erros de discovery."""

import pytest
import tempfile
import shutil
from pathlib import Path
from qualia.core.loader import PluginLoader


class TestDiscoveryErrors:
    """Discovery deve acumular erros em vez de engolir silenciosamente."""

    @pytest.fixture
    def broken_plugins_dir(self):
        """Cria dir com plugin quebrado."""
        tmp = Path(tempfile.mkdtemp())
        plugin_dir = tmp / "broken_plugin"
        plugin_dir.mkdir()
        (plugin_dir / "__init__.py").write_text("raise ImportError('dependência faltando')\n")
        yield tmp
        shutil.rmtree(tmp)

    def test_discovery_errors_accumulated(self, broken_plugins_dir):
        """Plugins que falham devem aparecer em discovery_errors."""
        loader = PluginLoader(broken_plugins_dir)
        discovered = loader.discover()

        assert len(loader.discovery_errors) > 0
        error = loader.discovery_errors[0]
        assert "broken_plugin" in error["plugin"]
        assert "dependência faltando" in error["error"]

    def test_discovery_errors_empty_on_success(self):
        """Sem erros quando todos plugins carregam ok."""
        loader = PluginLoader(Path("plugins"))
        loader.discover()
        assert loader.discovery_errors == []

    def test_healthy_plugins_still_discovered_with_broken(self, broken_plugins_dir):
        """Plugin saudável deve ser descoberto mesmo com irmão quebrado."""
        good_dir = broken_plugins_dir / "good_plugin"
        good_dir.mkdir()
        (good_dir / "__init__.py").write_text(
            "from qualia.core import BaseAnalyzerPlugin, PluginMetadata, PluginType, Document\n"
            "class GoodPlugin(BaseAnalyzerPlugin):\n"
            "    def meta(self):\n"
            "        return PluginMetadata(id='good', name='Good', type=PluginType.ANALYZER,\n"
            "                             version='1.0', description='test')\n"
            "    def _analyze_impl(self, doc, config, ctx):\n"
            "        return {'ok': True}\n"
        )

        loader = PluginLoader(broken_plugins_dir)
        discovered = loader.discover()

        assert "good" in discovered
        assert len(loader.discovery_errors) > 0

    def test_rediscovery_clears_stale_plugins(self, broken_plugins_dir):
        """Após remover plugin do disco, rediscovery não deve manter fantasma."""
        # Criar plugin temporário
        plugin_dir = broken_plugins_dir / "ephemeral"
        plugin_dir.mkdir()
        (plugin_dir / "__init__.py").write_text(
            "from qualia.core import BaseAnalyzerPlugin, PluginMetadata, PluginType, Document\n"
            "class EphemeralPlugin(BaseAnalyzerPlugin):\n"
            "    def meta(self):\n"
            "        return PluginMetadata(id='ephemeral', name='Ephemeral', type=PluginType.ANALYZER,\n"
            "                             version='1.0', description='test')\n"
            "    def _analyze_impl(self, doc, config, ctx):\n"
            "        return {'ok': True}\n"
        )

        loader = PluginLoader(broken_plugins_dir)

        # Primeira discovery — plugin existe
        discovered1 = loader.discover()
        assert "ephemeral" in discovered1
        assert loader.get_plugin("ephemeral") is not None

        # Remover plugin do disco
        shutil.rmtree(plugin_dir)

        # Segunda discovery — plugin não deve mais existir
        discovered2 = loader.discover()
        assert "ephemeral" not in discovered2
        assert loader.get_plugin("ephemeral") is None
