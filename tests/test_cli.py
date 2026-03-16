"""
Testes dos comandos CLI do Qualia.

Usa CliRunner do Click para testar sem processos reais.
Os comandos dependem de get_core() que é mockado para velocidade.
"""

import pytest
import json
import yaml
from pathlib import Path
from click.testing import CliRunner

from qualia.cli.commands import cli


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def text_file(tmp_path):
    """Cria arquivo de texto temporário"""
    f = tmp_path / "sample.txt"
    f.write_text("O gato sentou no tapete. O gato é bonito. O tapete é macio.")
    return f


@pytest.fixture
def pipeline_config(tmp_path):
    """Cria arquivo de config de pipeline"""
    config = {
        "name": "test_pipeline",
        "steps": [
            {"plugin": "word_frequency", "config": {"min_word_length": 2}},
        ],
    }
    f = tmp_path / "pipeline.yaml"
    f.write_text(yaml.dump(config))
    return f


@pytest.fixture
def invalid_yaml(tmp_path):
    f = tmp_path / "bad.yaml"
    f.write_text(": : : not valid yaml [[[")
    return f


@pytest.fixture
def valid_plugin_config(tmp_path):
    config = {"min_word_length": 3, "max_words": 50}
    f = tmp_path / "config.yaml"
    f.write_text(yaml.dump(config))
    return f


# =============================================================================
# LIST COMMAND
# =============================================================================

class TestListCommand:

    def test_list_all_plugins(self, runner):
        result = runner.invoke(cli, ["list"])
        assert result.exit_code == 0
        assert "word_frequency" in result.output

    def test_list_filter_analyzer(self, runner):
        result = runner.invoke(cli, ["list", "--type", "analyzer"])
        assert result.exit_code == 0
        assert "word_frequency" in result.output
        # Visualizers não devem aparecer
        assert "wordcloud_viz" not in result.output

    def test_list_filter_visualizer(self, runner):
        result = runner.invoke(cli, ["list", "--type", "visualizer"])
        assert result.exit_code == 0
        assert "wordcloud_viz" in result.output
        assert "word_frequency" not in result.output

    def test_list_detailed(self, runner):
        result = runner.invoke(cli, ["list", "--detailed"])
        assert result.exit_code == 0
        # Modo detailed mostra colunas extras
        assert "Fornece" in result.output or "fornece" in result.output.lower()


# =============================================================================
# ANALYZE COMMAND
# =============================================================================

class TestAnalyzeCommand:

    def test_analyze_happy_path(self, runner, text_file):
        result = runner.invoke(cli, ["analyze", str(text_file), "-p", "word_frequency"])
        assert result.exit_code == 0
        assert "gato" in result.output.lower() or "Resultado" in result.output

    def test_analyze_invalid_plugin(self, runner, text_file):
        result = runner.invoke(cli, ["analyze", str(text_file), "-p", "nonexistent"])
        assert "não encontrado" in result.output or "not found" in result.output.lower()

    def test_analyze_wrong_type(self, runner, text_file):
        result = runner.invoke(cli, ["analyze", str(text_file), "-p", "wordcloud_viz"])
        assert "não é um analyzer" in result.output or "Tipo" in result.output

    def test_analyze_json_format(self, runner, text_file):
        result = runner.invoke(cli, [
            "analyze", str(text_file), "-p", "word_frequency", "--format", "json"
        ])
        assert result.exit_code == 0
        # Output deve conter JSON válido
        assert "word_frequencies" in result.output

    def test_analyze_with_output_file(self, runner, text_file, tmp_path):
        output = tmp_path / "result.json"
        result = runner.invoke(cli, [
            "analyze", str(text_file), "-p", "word_frequency",
            "--format", "json", "--output", str(output),
        ])
        assert result.exit_code == 0
        assert output.exists()
        data = json.loads(output.read_text())
        assert "word_frequencies" in data


# =============================================================================
# PIPELINE COMMAND
# =============================================================================

class TestPipelineCommand:

    def test_pipeline_happy_path(self, runner, text_file, pipeline_config, tmp_path):
        output_dir = tmp_path / "output"
        result = runner.invoke(cli, [
            "pipeline", str(text_file),
            "--config", str(pipeline_config),
            "--output-dir", str(output_dir),
        ])
        assert result.exit_code == 0
        assert "Pipeline completo" in result.output or "completo" in result.output.lower()

    def test_pipeline_missing_config(self, runner, text_file):
        result = runner.invoke(cli, [
            "pipeline", str(text_file), "--config", "/nonexistent/path.yaml"
        ])
        # Click valida exists=True antes de chamar o handler
        assert result.exit_code != 0

    def test_pipeline_invalid_document(self, runner, pipeline_config):
        result = runner.invoke(cli, [
            "pipeline", "/nonexistent/doc.txt", "--config", str(pipeline_config)
        ])
        assert result.exit_code != 0


# =============================================================================
# BATCH COMMAND
# =============================================================================

class TestBatchCommand:

    def test_batch_dry_run(self, runner, tmp_path):
        # Criar alguns arquivos
        for i in range(3):
            (tmp_path / f"doc{i}.txt").write_text(f"Documento número {i} com texto.")
        result = runner.invoke(cli, [
            "batch", str(tmp_path / "*.txt"),
            "-p", "word_frequency", "--dry-run",
        ])
        assert result.exit_code == 0

    def test_batch_no_matching_files(self, runner, tmp_path):
        result = runner.invoke(cli, [
            "batch", str(tmp_path / "*.xyz"),
            "-p", "word_frequency",
        ])
        # Deve avisar que não encontrou arquivos
        assert "nenhum" in result.output.lower() or result.exit_code == 0


# =============================================================================
# EXPORT COMMAND
# =============================================================================

class TestExportCommand:

    def test_export_json_to_csv(self, runner, tmp_path):
        # Criar JSON de input
        data = {
            "word_frequencies": {"gato": 5, "cachorro": 3, "pato": 1},
            "total_words": 9,
        }
        input_file = tmp_path / "result.json"
        input_file.write_text(json.dumps(data))

        output_file = tmp_path / "result.csv"
        result = runner.invoke(cli, [
            "export", str(input_file), "--format", "csv", "--output", str(output_file),
        ])
        assert result.exit_code == 0
        assert output_file.exists()

    def test_export_json_to_markdown(self, runner, tmp_path):
        data = {
            "word_frequencies": {"gato": 5, "cachorro": 3},
            "total_words": 8,
        }
        input_file = tmp_path / "result.json"
        input_file.write_text(json.dumps(data))

        output_file = tmp_path / "result.md"
        result = runner.invoke(cli, [
            "export", str(input_file), "--format", "markdown", "--output", str(output_file),
        ])
        assert result.exit_code == 0
        assert output_file.exists()

    def test_export_nonexistent_file(self, runner):
        result = runner.invoke(cli, [
            "export", "/nonexistent/file.json", "--format", "csv",
        ])
        assert result.exit_code != 0


# =============================================================================
# CONFIG COMMAND
# =============================================================================

class TestConfigCommand:

    def test_config_validate_valid_yaml(self, runner, valid_plugin_config):
        result = runner.invoke(cli, ["config", "validate", str(valid_plugin_config)])
        assert result.exit_code == 0
        assert "válido" in result.output.lower() or "valid" in result.output.lower()

    def test_config_validate_invalid_file(self, runner, invalid_yaml):
        result = runner.invoke(cli, ["config", "validate", str(invalid_yaml)])
        # Deve reportar erro de parsing
        assert "inválido" in result.output.lower() or "invalid" in result.output.lower() or "erro" in result.output.lower() or result.exit_code != 0


# =============================================================================
# VERSION & HELP
# =============================================================================

class TestCLIBasics:

    def test_version(self, runner):
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.output

    def test_help(self, runner):
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "Qualia Core" in result.output
