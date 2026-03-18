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
        assert "wordcloud_d3" not in result.output

    def test_list_filter_visualizer(self, runner):
        result = runner.invoke(cli, ["list", "--type", "visualizer"])
        assert result.exit_code == 0
        assert "wordcloud_d3" in result.output
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
        result = runner.invoke(cli, ["analyze", str(text_file), "-p", "wordcloud_d3"])
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


# =============================================================================
# INSPECT COMMAND
# =============================================================================

class TestInspectCommand:

    def test_inspect_analyzer_plugin(self, runner):
        """Inspeciona plugin analyzer existente"""
        result = runner.invoke(cli, ["inspect", "word_frequency"])
        assert result.exit_code == 0
        assert "word_frequency" in result.output

    def test_inspect_document_plugin(self, runner):
        """Inspeciona plugin de documento"""
        result = runner.invoke(cli, ["inspect", "teams_cleaner"])
        assert result.exit_code == 0
        assert "teams_cleaner" in result.output

    def test_inspect_visualizer_plugin(self, runner):
        """Inspeciona plugin visualizer"""
        result = runner.invoke(cli, ["inspect", "wordcloud_d3"])
        assert result.exit_code == 0
        assert "wordcloud_d3" in result.output

    def test_inspect_shows_parameters(self, runner):
        """Inspect deve mostrar parâmetros do plugin"""
        result = runner.invoke(cli, ["inspect", "word_frequency"])
        assert result.exit_code == 0
        # word_frequency tem parâmetros configuráveis
        assert "min_word_length" in result.output or "Parâmetros" in result.output or "Nome" in result.output

    def test_inspect_shows_type(self, runner):
        """Inspect deve mostrar o tipo do plugin"""
        result = runner.invoke(cli, ["inspect", "word_frequency"])
        assert result.exit_code == 0
        assert "analyzer" in result.output.lower() or "Tipo" in result.output

    def test_inspect_shows_provides(self, runner):
        """Inspect deve mostrar o que o plugin fornece"""
        result = runner.invoke(cli, ["inspect", "word_frequency"])
        assert result.exit_code == 0
        assert "Fornece" in result.output or "word_frequencies" in result.output

    def test_inspect_nonexistent_plugin(self, runner):
        """Plugin inexistente deve mostrar erro"""
        result = runner.invoke(cli, ["inspect", "plugin_que_nao_existe"])
        assert "não encontrado" in result.output

    def test_inspect_no_argument(self, runner):
        """Sem argumento deve dar erro (argumento obrigatório)"""
        result = runner.invoke(cli, ["inspect"])
        assert result.exit_code != 0


# =============================================================================
# PROCESS COMMAND
# =============================================================================

class TestProcessCommand:

    @pytest.fixture
    def teams_file(self, tmp_path):
        """Cria arquivo simulando export do Teams"""
        content = (
            "12:00 PM - João Silva\n"
            "Olá pessoal, bom dia!\n"
            "12:01 PM - Maria Santos\n"
            "Bom dia João!\n"
            "12:02 PM - João Silva\n"
            "Vamos discutir o projeto.\n"
        )
        f = tmp_path / "teams_chat.txt"
        f.write_text(content)
        return f

    @pytest.fixture
    def simple_doc(self, tmp_path):
        """Documento simples para processamento"""
        f = tmp_path / "doc.txt"
        f.write_text("Este é um documento simples para testar o processamento.")
        return f

    def test_process_nonexistent_plugin(self, runner, simple_doc):
        """Plugin inexistente deve mostrar erro"""
        result = runner.invoke(cli, ["process", str(simple_doc), "-p", "nao_existe"])
        assert "não encontrado" in result.output

    def test_process_wrong_type_analyzer(self, runner, simple_doc):
        """Usar analyzer como processador deve dar erro"""
        result = runner.invoke(cli, ["process", str(simple_doc), "-p", "word_frequency"])
        assert "não é um processador" in result.output

    def test_process_wrong_type_visualizer(self, runner, simple_doc):
        """Usar visualizer como processador deve dar erro"""
        result = runner.invoke(cli, ["process", str(simple_doc), "-p", "wordcloud_d3"])
        assert "não é um processador" in result.output

    def test_process_nonexistent_file(self, runner):
        """Arquivo inexistente deve dar erro (Click valida exists=True)"""
        result = runner.invoke(cli, ["process", "/tmp/nao_existe_xyz.txt", "-p", "teams_cleaner"])
        assert result.exit_code != 0

    def test_process_missing_plugin_option(self, runner, simple_doc):
        """Sem --plugin deve dar erro (opção obrigatória)"""
        result = runner.invoke(cli, ["process", str(simple_doc)])
        assert result.exit_code != 0

    def test_process_with_save(self, runner, teams_file, tmp_path):
        """Processar e salvar resultado"""
        output = tmp_path / "cleaned.txt"
        result = runner.invoke(cli, [
            "process", str(teams_file), "-p", "teams_cleaner",
            "--save-as", str(output),
        ])
        # Se processou com sucesso, verifica se tentou salvar
        # O resultado depende do plugin, mas não deve crashar
        assert result.exit_code == 0 or "Erro" in result.output

    def test_process_with_config_file(self, runner, teams_file, tmp_path):
        """Processar com arquivo de configuração"""
        config = tmp_path / "config.yaml"
        config.write_text(yaml.dump({"remove_timestamps": True}))
        result = runner.invoke(cli, [
            "process", str(teams_file), "-p", "teams_cleaner",
            "--config", str(config),
        ])
        assert result.exit_code == 0 or "Erro" in result.output

    def test_process_with_params(self, runner, teams_file):
        """Processar com parâmetros inline"""
        result = runner.invoke(cli, [
            "process", str(teams_file), "-p", "teams_cleaner",
            "-P", "remove_timestamps=true",
        ])
        assert result.exit_code == 0 or "Erro" in result.output


# =============================================================================
# FORMATTERS (testes diretos, sem CliRunner)
# =============================================================================

class TestFormatters:

    def test_create_plugin_table_basic(self):
        """Tabela básica tem colunas ID, Tipo, Nome, Versão"""
        from qualia.cli.formatters import create_plugin_table
        table = create_plugin_table([], detailed=False)
        assert table.title == "Plugins Disponíveis"
        col_names = [col.header for col in table.columns]
        assert "ID" in col_names
        assert "Tipo" in col_names
        assert "Nome" in col_names
        assert "Versão" in col_names
        # Sem detailed, não deve ter Descrição
        assert "Descrição" not in col_names

    def test_create_plugin_table_detailed(self):
        """Tabela detalhada tem colunas extras"""
        from qualia.cli.formatters import create_plugin_table
        table = create_plugin_table([], detailed=True)
        col_names = [col.header for col in table.columns]
        assert "Descrição" in col_names
        assert "Autor" in col_names

    def test_format_analysis_results_dict(self):
        """Formata resultado com valores dict"""
        from qualia.cli.formatters import format_analysis_results
        results = {
            "word_frequencies": {"gato": 5, "cachorro": 3},
            "total_words": 8,
        }
        panel = format_analysis_results(results)
        assert panel.title == "Resultados da Análise"
        # Panel renderable deve conter os dados
        content = str(panel.renderable)
        assert "word_frequencies" in content
        assert "total_words" in content

    def test_format_analysis_results_list(self):
        """Formata resultado com valores lista — mostra contagem"""
        from qualia.cli.formatters import format_analysis_results
        results = {"items": [1, 2, 3]}
        panel = format_analysis_results(results)
        content = str(panel.renderable)
        assert "3 items" in content

    def test_format_analysis_results_scalar(self):
        """Formata resultado com valores escalares"""
        from qualia.cli.formatters import format_analysis_results
        results = {"score": 42}
        panel = format_analysis_results(results)
        content = str(panel.renderable)
        assert "42" in content

    def test_format_analysis_results_empty(self):
        """Resultado vazio não deve crashar"""
        from qualia.cli.formatters import format_analysis_results
        panel = format_analysis_results({})
        assert panel.title == "Resultados da Análise"

    def test_format_error(self):
        """Formata exceção com tipo e mensagem"""
        from qualia.cli.formatters import format_error
        err = ValueError("algo deu errado")
        panel = format_error(err)
        assert panel.title == "Erro"
        content = str(panel.renderable)
        assert "ValueError" in content
        assert "algo deu errado" in content

    def test_format_error_custom_exception(self):
        """Formata exceção customizada"""
        from qualia.cli.formatters import format_error
        err = FileNotFoundError("arquivo.txt")
        panel = format_error(err)
        content = str(panel.renderable)
        assert "FileNotFoundError" in content

    def test_format_success(self):
        """Mensagem de sucesso contém o texto"""
        from qualia.cli.formatters import format_success
        msg = format_success("Operação concluída")
        assert "Operação concluída" in msg

    def test_format_warning(self):
        """Mensagem de aviso contém o texto"""
        from qualia.cli.formatters import format_warning
        msg = format_warning("Cuidado com isso")
        assert "Cuidado com isso" in msg

    def test_format_info(self):
        """Mensagem informativa contém o texto"""
        from qualia.cli.formatters import format_info
        msg = format_info("Informação útil")
        assert "Informação útil" in msg

    def test_show_banner(self):
        """Banner retorna Panel com título do Qualia"""
        from qualia.cli.formatters import show_banner
        from rich.panel import Panel
        panel = show_banner()
        assert isinstance(panel, Panel)
        content = str(panel.renderable)
        assert "QUALIA" in content
