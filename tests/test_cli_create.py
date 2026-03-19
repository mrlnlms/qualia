"""Testes do comando qualia create"""

import shutil
import pytest
from pathlib import Path
from click.testing import CliRunner

from qualia.cli.commands import cli


_REAL_TEMPLATES = Path(__file__).parent.parent / "plugins" / "_templates"


@pytest.fixture
def runner():
    return CliRunner()


def _setup_templates(tmp_path):
    """Copia templates reais pra dentro do filesystem isolado."""
    templates_dir = tmp_path / "plugins" / "_templates"
    templates_dir.mkdir(parents=True)
    for f in _REAL_TEMPLATES.glob("*.py"):
        shutil.copy(f, templates_dir / f.name)


class TestCreateCommand:
    """Testes do comando create"""

    def test_create_analyzer(self, runner, tmp_path):
        """Cria analyzer com sucesso"""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            _setup_templates(tmp_path)
            result = runner.invoke(cli, ["create", "test_analyzer", "analyzer"])
            assert result.exit_code == 0
            init_file = Path("plugins/test_analyzer/__init__.py")
            assert init_file.exists()
            content = init_file.read_text()
            assert "class TestAnalyzerAnalyzer" in content
            assert '"test_analyzer"' in content
            assert "__PLUGIN_ID__" not in content
            assert "__CLASS_NAME__" not in content

    def test_create_visualizer(self, runner, tmp_path):
        """Cria visualizer com sucesso"""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            _setup_templates(tmp_path)
            result = runner.invoke(cli, ["create", "test_viz", "visualizer"])
            assert result.exit_code == 0
            content = Path("plugins/test_viz/__init__.py").read_text()
            assert "class TestVizVisualizer" in content
            assert "__PLUGIN_ID__" not in content

    def test_create_document(self, runner, tmp_path):
        """Cria document processor com sucesso"""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            _setup_templates(tmp_path)
            result = runner.invoke(cli, ["create", "test_cleaner", "document"])
            assert result.exit_code == 0
            content = Path("plugins/test_cleaner/__init__.py").read_text()
            assert "class TestCleanerProcessor" in content
            assert "__PLUGIN_ID__" not in content

    def test_create_invalid_type(self, runner, tmp_path):
        """Tipo inválido mostra erro"""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ["create", "test_plugin", "invalid"])
            assert result.exit_code != 0

    def test_create_existing_plugin(self, runner, tmp_path):
        """Plugin que já existe mostra erro"""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            _setup_templates(tmp_path)
            Path("plugins/existing").mkdir(parents=True)
            result = runner.invoke(cli, ["create", "existing", "analyzer"])
            assert result.exit_code == 1
            assert "existe" in result.output.lower()

    def test_create_lists_templates(self, runner, tmp_path):
        """Sem argumentos lista templates disponíveis"""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ["create"])
            assert result.exit_code == 0
            assert "analyzer" in result.output
            assert "visualizer" in result.output
            assert "document" in result.output

    def test_create_no_type_shows_error(self, runner, tmp_path):
        """Com nome mas sem tipo mostra erro"""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ["create", "test_plugin"])
            assert result.exit_code == 1
            assert "tipo" in result.output.lower() or "type" in result.output.lower()
