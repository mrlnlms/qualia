# tests/test_cli_plugins_check.py
"""Testes do comando qualia list --check (diagnóstico de plugins)."""

import pytest
from click.testing import CliRunner
from qualia.cli.commands import cli


@pytest.fixture
def runner():
    return CliRunner()


class TestPluginsCheck:
    """qualia list --check diagnostica saúde dos plugins."""

    def test_check_all_healthy(self, runner):
        """Quando todos plugins carregam ok, mostra status saudável."""
        result = runner.invoke(cli, ["list", "--check"])
        assert result.exit_code == 0
        assert "ERRO" not in result.output
        assert "FALHA" not in result.output

    def test_check_shows_plugin_status(self, runner):
        """--check mostra status de cada plugin."""
        result = runner.invoke(cli, ["list", "--check"])
        assert result.exit_code == 0
        assert "word_frequency" in result.output
        assert "sentiment_analyzer" in result.output

    def test_check_shows_loading_type(self, runner):
        """--check mostra se plugin é eager ou lazy."""
        result = runner.invoke(cli, ["list", "--check"])
        assert result.exit_code == 0
        assert "eager" in result.output.lower() or "lazy" in result.output.lower()

    def test_check_incompatible_with_type_filter(self, runner):
        """--check funciona junto com --type filter."""
        result = runner.invoke(cli, ["list", "--check", "--type", "analyzer"])
        assert result.exit_code == 0
        assert "word_frequency" in result.output
        assert "wordcloud_d3" not in result.output
