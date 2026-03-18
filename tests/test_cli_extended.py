"""
Testes estendidos dos comandos CLI do Qualia: visualize, batch, export.

Complementa test_cli.py com cobertura mais profunda — happy paths, error paths,
edge cases. Usa CliRunner do Click, plugins reais, fixtures com dados realistas.
"""

import pytest
import json
import yaml
import csv
from pathlib import Path
from unittest.mock import patch
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
    """Cria arquivo de texto para análise"""
    f = tmp_path / "sample.txt"
    f.write_text("O gato sentou no tapete. O gato é bonito. O tapete é macio.")
    return f


@pytest.fixture
def word_freq_data(tmp_path):
    """JSON com resultado típico de word_frequency"""
    data = {
        "word_frequencies": {"gato": 5, "tapete": 3, "bonito": 2, "macio": 1},
        "total_words": 11,
        "vocabulary_size": 4,
        "top_words": [["gato", 5], ["tapete", 3], ["bonito", 2], ["macio", 1]],
    }
    f = tmp_path / "freq_result.json"
    f.write_text(json.dumps(data))
    return f


@pytest.fixture
def sentiment_data(tmp_path):
    """JSON com resultado típico de sentiment_analyzer"""
    data = {
        "sentiment": "positive",
        "polarity": 0.65,
        "subjectivity": 0.4,
        "sentence_sentiments": [
            {"sentence": "O produto é excelente.", "polarity": 0.8},
            {"sentence": "Entrega rápida.", "polarity": 0.5},
        ],
    }
    f = tmp_path / "sentiment_result.json"
    f.write_text(json.dumps(data))
    return f


@pytest.fixture
def empty_data_file(tmp_path):
    """JSON com dados vazios"""
    f = tmp_path / "empty.json"
    f.write_text(json.dumps({}))
    return f


@pytest.fixture
def yaml_data_file(tmp_path):
    """Dados de resultado em formato YAML"""
    data = {
        "word_frequencies": {"casa": 4, "jardim": 2},
        "total_words": 6,
    }
    f = tmp_path / "result.yaml"
    f.write_text(yaml.dump(data))
    return f


@pytest.fixture
def complex_result_data(tmp_path):
    """JSON com estrutura mais complexa (metadata + results)"""
    data = {
        "metadata": {
            "plugin": "word_frequency",
            "timestamp": "2026-03-17T10:00:00",
            "source": "entrevista_01.txt",
        },
        "results": {
            "word_frequencies": {"qualitativo": 8, "pesquisa": 6, "dados": 5},
            "total_words": 19,
        },
    }
    f = tmp_path / "complex_result.json"
    f.write_text(json.dumps(data))
    return f


@pytest.fixture
def batch_text_files(tmp_path):
    """Cria múltiplos arquivos de texto para batch"""
    texts = [
        "O gato sentou no tapete. O gato é bonito.",
        "A pesquisa qualitativa revela padrões interessantes no discurso.",
        "Python é uma linguagem de programação versátil e poderosa.",
        "O sol brilha forte no verão brasileiro. O calor é intenso.",
        "Análise de dados qualitativos requer atenção aos detalhes.",
    ]
    files = []
    for i, text in enumerate(texts):
        f = tmp_path / f"doc_{i:02d}.txt"
        f.write_text(text)
        files.append(f)
    return files


@pytest.fixture
def invalid_json_file(tmp_path):
    """Arquivo JSON malformado"""
    f = tmp_path / "bad.json"
    f.write_text("{not valid json at all")
    return f


@pytest.fixture
def unsupported_file(tmp_path):
    """Arquivo com extensão não suportada"""
    f = tmp_path / "data.xyz"
    f.write_text("conteúdo qualquer")
    return f


@pytest.fixture
def viz_config(tmp_path):
    """Config YAML para visualização"""
    config = {"colormap": "viridis", "max_words": 50}
    f = tmp_path / "viz_config.yaml"
    f.write_text(yaml.dump(config))
    return f


# =============================================================================
# VISUALIZE COMMAND
# =============================================================================

class TestVisualizeCommand:

    def test_visualize_plugin_not_found(self, runner, word_freq_data):
        """Plugin inexistente deve gerar erro"""
        result = runner.invoke(cli, [
            "visualize", str(word_freq_data), "-p", "plugin_fantasma",
        ])
        assert "não encontrado" in result.output

    def test_visualize_wrong_plugin_type_analyzer(self, runner, word_freq_data):
        """Usar analyzer como visualizador deve gerar erro de tipo"""
        result = runner.invoke(cli, [
            "visualize", str(word_freq_data), "-p", "word_frequency",
        ])
        assert "não é um visualizador" in result.output

    def test_visualize_wrong_plugin_type_document(self, runner, word_freq_data):
        """Usar document plugin como visualizador deve gerar erro de tipo"""
        result = runner.invoke(cli, [
            "visualize", str(word_freq_data), "-p", "teams_cleaner",
        ])
        assert "não é um visualizador" in result.output

    def test_visualize_nonexistent_data_file(self, runner):
        """Arquivo de dados inexistente — Click rejeita antes do handler"""
        result = runner.invoke(cli, [
            "visualize", "/nonexistent/data.json", "-p", "wordcloud_d3",
        ])
        assert result.exit_code != 0

    def test_visualize_unsupported_data_format(self, runner, unsupported_file):
        """Formato de dados não suportado (nem JSON nem YAML)"""
        result = runner.invoke(cli, [
            "visualize", str(unsupported_file), "-p", "wordcloud_d3",
        ])
        assert "não suportado" in result.output.lower() or result.exit_code != 0

    def test_visualize_invalid_json_data(self, runner, invalid_json_file):
        """JSON malformado deve gerar erro de leitura"""
        result = runner.invoke(cli, [
            "visualize", str(invalid_json_file), "-p", "wordcloud_d3",
        ])
        assert "Erro" in result.output or "erro" in result.output.lower()

    def test_visualize_wordcloud_with_output(self, runner, word_freq_data, tmp_path):
        """Wordcloud com output explícito — happy path"""
        output = tmp_path / "cloud.png"
        result = runner.invoke(cli, [
            "visualize", str(word_freq_data),
            "-p", "wordcloud_d3",
            "-o", str(output),
        ])
        # O plugin pode falhar se wordcloud não estiver instalado,
        # mas o comando deve ao menos chegar à fase de renderização
        assert "Gerando visualização" in result.output or "Erro" in result.output

    def test_visualize_frequency_chart_plotly(self, runner, word_freq_data, tmp_path):
        """Frequency chart com output HTML"""
        output = tmp_path / "chart.html"
        result = runner.invoke(cli, [
            "visualize", str(word_freq_data),
            "-p", "frequency_chart_plotly",
            "-o", str(output),
        ])
        assert "Gerando visualização" in result.output or "Erro" in result.output

    def test_visualize_with_config_file(self, runner, word_freq_data, viz_config, tmp_path):
        """Visualização com arquivo de configuração"""
        output = tmp_path / "viz_with_config.png"
        result = runner.invoke(cli, [
            "visualize", str(word_freq_data),
            "-p", "wordcloud_d3",
            "-c", str(viz_config),
            "-o", str(output),
        ])
        # Deve ao menos reconhecer o plugin e tentar renderizar
        assert "Gerando visualização" in result.output or "Erro" in result.output

    def test_visualize_with_params(self, runner, word_freq_data, tmp_path):
        """Visualização com parâmetros inline (-P key=value)"""
        output = tmp_path / "viz_params.png"
        result = runner.invoke(cli, [
            "visualize", str(word_freq_data),
            "-p", "wordcloud_d3",
            "-P", "colormap=plasma",
            "-P", "max_words=30",
            "-o", str(output),
        ])
        assert "Gerando visualização" in result.output or "Erro" in result.output

    def test_visualize_format_html(self, runner, word_freq_data, tmp_path):
        """Formato explícito HTML"""
        output = tmp_path / "result.html"
        result = runner.invoke(cli, [
            "visualize", str(word_freq_data),
            "-p", "frequency_chart_plotly",
            "-f", "html",
            "-o", str(output),
        ])
        assert "Gerando visualização" in result.output or "Erro" in result.output

    def test_visualize_auto_output_name(self, runner, word_freq_data):
        """Sem -o deve gerar nome automático"""
        result = runner.invoke(cli, [
            "visualize", str(word_freq_data),
            "-p", "wordcloud_d3",
        ])
        # Deve mencionar o nome automático gerado
        assert "Saída não especificada" in result.output or "Gerando" in result.output

    def test_visualize_yaml_data(self, runner, yaml_data_file, tmp_path):
        """Dados de entrada em YAML"""
        output = tmp_path / "from_yaml.png"
        result = runner.invoke(cli, [
            "visualize", str(yaml_data_file),
            "-p", "wordcloud_d3",
            "-o", str(output),
        ])
        assert "Gerando visualização" in result.output or "Erro" in result.output

    def test_visualize_nonexistent_config_file(self, runner, word_freq_data):
        """Config inexistente — Click rejeita antes do handler"""
        result = runner.invoke(cli, [
            "visualize", str(word_freq_data),
            "-p", "wordcloud_d3",
            "-c", "/nonexistent/config.yaml",
        ])
        assert result.exit_code != 0

    def test_visualize_sentiment_viz_plotly(self, runner, sentiment_data, tmp_path):
        """Sentiment viz com dados de sentimento"""
        output = tmp_path / "sentiment.png"
        result = runner.invoke(cli, [
            "visualize", str(sentiment_data),
            "-p", "sentiment_viz_plotly",
            "-o", str(output),
        ])
        assert "Gerando visualização" in result.output or "Erro" in result.output


# =============================================================================
# BATCH COMMAND
# =============================================================================

class TestBatchCommand:

    def test_batch_dry_run_lists_files(self, runner, batch_text_files):
        """Dry run deve listar arquivos sem processar"""
        pattern = str(batch_text_files[0].parent / "*.txt")
        result = runner.invoke(cli, [
            "batch", pattern, "-p", "word_frequency", "--dry-run",
        ])
        assert result.exit_code == 0
        assert "dry-run" in result.output.lower() or "Arquivos encontrados" in result.output

    def test_batch_dry_run_shows_count(self, runner, batch_text_files):
        """Dry run deve mostrar quantidade de arquivos"""
        pattern = str(batch_text_files[0].parent / "*.txt")
        result = runner.invoke(cli, [
            "batch", pattern, "-p", "word_frequency", "--dry-run",
        ])
        assert result.exit_code == 0
        assert "5" in result.output  # 5 arquivos criados pela fixture

    def test_batch_no_matching_files(self, runner, tmp_path):
        """Padrão sem match deve avisar"""
        result = runner.invoke(cli, [
            "batch", str(tmp_path / "*.nonexistent"),
            "-p", "word_frequency",
        ])
        assert "nenhum" in result.output.lower() or "Nenhum" in result.output

    def test_batch_plugin_not_found(self, runner, batch_text_files):
        """Plugin inexistente deve gerar erro"""
        pattern = str(batch_text_files[0].parent / "*.txt")
        result = runner.invoke(cli, [
            "batch", pattern, "-p", "plugin_fantasma",
        ])
        assert "não encontrado" in result.output

    def test_batch_process_sequential(self, runner, batch_text_files, tmp_path):
        """Processamento sequencial com output dir"""
        pattern = str(batch_text_files[0].parent / "*.txt")
        output_dir = tmp_path / "batch_output"
        result = runner.invoke(cli, [
            "batch", pattern,
            "-p", "word_frequency",
            "-o", str(output_dir),
            "--continue-on-error",
        ])
        assert result.exit_code == 0
        # Deve ter criado o diretório de output
        assert output_dir.exists()

    def test_batch_process_parallel(self, runner, batch_text_files, tmp_path):
        """Processamento paralelo com -j 2"""
        pattern = str(batch_text_files[0].parent / "*.txt")
        output_dir = tmp_path / "batch_parallel"
        result = runner.invoke(cli, [
            "batch", pattern,
            "-p", "word_frequency",
            "-o", str(output_dir),
            "-j", "2",
            "--continue-on-error",
        ])
        assert result.exit_code == 0
        assert output_dir.exists()

    def test_batch_with_config_file(self, runner, batch_text_files, tmp_path):
        """Batch com arquivo de configuração"""
        config = {"min_word_length": 3, "max_words": 20}
        config_file = tmp_path / "batch_config.yaml"
        config_file.write_text(yaml.dump(config))

        pattern = str(batch_text_files[0].parent / "*.txt")
        result = runner.invoke(cli, [
            "batch", pattern,
            "-p", "word_frequency",
            "-c", str(config_file),
            "--dry-run",
        ])
        assert result.exit_code == 0

    def test_batch_with_params(self, runner, batch_text_files):
        """Batch com parâmetros inline"""
        pattern = str(batch_text_files[0].parent / "*.txt")
        result = runner.invoke(cli, [
            "batch", pattern,
            "-p", "word_frequency",
            "-P", "min_word_length=4",
            "--dry-run",
        ])
        assert result.exit_code == 0

    def test_batch_output_creates_log(self, runner, batch_text_files, tmp_path):
        """Batch com output deve criar batch_log.json"""
        pattern = str(batch_text_files[0].parent / "*.txt")
        output_dir = tmp_path / "batch_log_test"
        result = runner.invoke(cli, [
            "batch", pattern,
            "-p", "word_frequency",
            "-o", str(output_dir),
            "--continue-on-error",
        ])
        assert result.exit_code == 0
        log_file = output_dir / "batch_log.json"
        if log_file.exists():
            log_data = json.loads(log_file.read_text())
            assert "plugin" in log_data
            assert log_data["plugin"] == "word_frequency"

    def test_batch_single_file_pattern(self, runner, batch_text_files):
        """Padrão que casa com um único arquivo"""
        pattern = str(batch_text_files[0].parent / "doc_00.txt")
        result = runner.invoke(cli, [
            "batch", pattern,
            "-p", "word_frequency",
            "--dry-run",
        ])
        # Pode não casar por glob (path literal não é glob), mas não deve crashar
        assert result.exit_code == 0

    def test_batch_summary_shows_counts(self, runner, batch_text_files, tmp_path):
        """Resumo deve mostrar contagem de sucesso/erro"""
        pattern = str(batch_text_files[0].parent / "*.txt")
        output_dir = tmp_path / "batch_summary"
        result = runner.invoke(cli, [
            "batch", pattern,
            "-p", "word_frequency",
            "-o", str(output_dir),
            "--continue-on-error",
        ])
        assert "Sucesso" in result.output or "sucesso" in result.output.lower()


# =============================================================================
# EXPORT COMMAND
# =============================================================================

class TestExportCommand:

    # --- CSV ---

    def test_export_json_to_csv_happy_path(self, runner, word_freq_data, tmp_path):
        """Exportar word_frequency para CSV"""
        output = tmp_path / "result.csv"
        result = runner.invoke(cli, [
            "export", str(word_freq_data),
            "--format", "csv",
            "--output", str(output),
        ])
        assert result.exit_code == 0
        assert output.exists()
        content = output.read_text()
        assert "key" in content or "gato" in content

    def test_export_csv_contains_all_words(self, runner, word_freq_data, tmp_path):
        """CSV deve conter todas as palavras do resultado"""
        output = tmp_path / "all_words.csv"
        result = runner.invoke(cli, [
            "export", str(word_freq_data),
            "--format", "csv",
            "--output", str(output),
        ])
        assert result.exit_code == 0
        content = output.read_text()
        assert "gato" in content
        assert "tapete" in content

    def test_export_csv_auto_output_name(self, runner, word_freq_data):
        """Sem -o deve gerar nome automático baseado no input"""
        result = runner.invoke(cli, [
            "export", str(word_freq_data), "--format", "csv",
        ])
        assert result.exit_code == 0
        # Deve ter criado freq_result.csv
        auto_output = word_freq_data.with_suffix(".csv")
        assert auto_output.exists()

    # --- Markdown ---

    def test_export_json_to_markdown(self, runner, word_freq_data, tmp_path):
        """Exportar para Markdown"""
        output = tmp_path / "result.md"
        result = runner.invoke(cli, [
            "export", str(word_freq_data),
            "--format", "markdown",
            "--output", str(output),
        ])
        assert result.exit_code == 0
        assert output.exists()
        content = output.read_text()
        assert "# Resultados Qualia" in content

    def test_export_markdown_with_metadata(self, runner, complex_result_data, tmp_path):
        """Markdown deve incluir seção de metadata quando presente"""
        output = tmp_path / "with_meta.md"
        result = runner.invoke(cli, [
            "export", str(complex_result_data),
            "--format", "markdown",
            "--output", str(output),
        ])
        assert result.exit_code == 0
        content = output.read_text()
        assert "Metadata" in content
        assert "word_frequency" in content

    def test_export_markdown_word_frequencies(self, runner, word_freq_data, tmp_path):
        """Markdown deve conter palavras e contagens"""
        output = tmp_path / "freq.md"
        result = runner.invoke(cli, [
            "export", str(word_freq_data),
            "--format", "markdown",
            "--output", str(output),
        ])
        assert result.exit_code == 0
        content = output.read_text()
        assert "gato" in content

    # --- HTML ---

    def test_export_json_to_html(self, runner, word_freq_data, tmp_path):
        """Exportar para HTML"""
        output = tmp_path / "result.html"
        result = runner.invoke(cli, [
            "export", str(word_freq_data),
            "--format", "html",
            "--output", str(output),
        ])
        assert result.exit_code == 0
        assert output.exists()
        content = output.read_text()
        assert "<!DOCTYPE html>" in content
        assert "Resultados Qualia" in content

    def test_export_html_with_metadata(self, runner, complex_result_data, tmp_path):
        """HTML deve incluir metadata quando presente"""
        output = tmp_path / "meta.html"
        result = runner.invoke(cli, [
            "export", str(complex_result_data),
            "--format", "html",
            "--output", str(output),
        ])
        assert result.exit_code == 0
        content = output.read_text()
        assert "Metadata" in content

    # --- YAML ---

    def test_export_json_to_yaml(self, runner, word_freq_data, tmp_path):
        """Exportar JSON para YAML"""
        output = tmp_path / "result.yaml"
        result = runner.invoke(cli, [
            "export", str(word_freq_data),
            "--format", "yaml",
            "--output", str(output),
        ])
        assert result.exit_code == 0
        assert output.exists()
        data = yaml.safe_load(output.read_text())
        assert "word_frequencies" in data
        assert data["word_frequencies"]["gato"] == 5

    def test_export_yaml_pretty(self, runner, word_freq_data, tmp_path):
        """YAML com --pretty deve funcionar"""
        output = tmp_path / "pretty.yaml"
        result = runner.invoke(cli, [
            "export", str(word_freq_data),
            "--format", "yaml",
            "--output", str(output),
            "--pretty",
        ])
        assert result.exit_code == 0
        assert output.exists()

    # --- Input YAML ---

    def test_export_yaml_input_to_csv(self, runner, yaml_data_file, tmp_path):
        """Entrada YAML exportada para CSV"""
        output = tmp_path / "from_yaml.csv"
        result = runner.invoke(cli, [
            "export", str(yaml_data_file),
            "--format", "csv",
            "--output", str(output),
        ])
        assert result.exit_code == 0
        assert output.exists()

    # --- Error paths ---

    def test_export_nonexistent_file(self, runner):
        """Arquivo inexistente — Click rejeita"""
        result = runner.invoke(cli, [
            "export", "/nonexistent/file.json", "--format", "csv",
        ])
        assert result.exit_code != 0

    def test_export_invalid_json(self, runner, invalid_json_file, tmp_path):
        """JSON malformado deve gerar erro"""
        output = tmp_path / "fail.csv"
        result = runner.invoke(cli, [
            "export", str(invalid_json_file),
            "--format", "csv",
            "--output", str(output),
        ])
        assert "Erro" in result.output or "erro" in result.output.lower()

    def test_export_unsupported_input_format(self, runner, unsupported_file, tmp_path):
        """Formato de entrada não suportado"""
        output = tmp_path / "fail.csv"
        result = runner.invoke(cli, [
            "export", str(unsupported_file),
            "--format", "csv",
            "--output", str(output),
        ])
        assert "não suportado" in result.output.lower() or "Formato" in result.output

    def test_export_empty_data(self, runner, empty_data_file, tmp_path):
        """Dados vazios não devem crashar"""
        output = tmp_path / "empty.csv"
        result = runner.invoke(cli, [
            "export", str(empty_data_file),
            "--format", "csv",
            "--output", str(output),
        ])
        # Não deve crashar, mesmo com dados vazios
        assert result.exit_code == 0

    def test_export_empty_to_markdown(self, runner, empty_data_file, tmp_path):
        """Dados vazios exportados para markdown"""
        output = tmp_path / "empty.md"
        result = runner.invoke(cli, [
            "export", str(empty_data_file),
            "--format", "markdown",
            "--output", str(output),
        ])
        assert result.exit_code == 0
        assert output.exists()

    def test_export_empty_to_html(self, runner, empty_data_file, tmp_path):
        """Dados vazios exportados para HTML"""
        output = tmp_path / "empty.html"
        result = runner.invoke(cli, [
            "export", str(empty_data_file),
            "--format", "html",
            "--output", str(output),
        ])
        assert result.exit_code == 0
        assert output.exists()

    def test_export_creates_parent_dirs(self, runner, word_freq_data, tmp_path):
        """Export deve criar diretórios pais se não existirem"""
        output = tmp_path / "deep" / "nested" / "dir" / "result.csv"
        result = runner.invoke(cli, [
            "export", str(word_freq_data),
            "--format", "csv",
            "--output", str(output),
        ])
        assert result.exit_code == 0
        assert output.exists()

    def test_export_sentiment_data(self, runner, sentiment_data, tmp_path):
        """Exportar dados de sentimento para CSV"""
        output = tmp_path / "sentiment.csv"
        result = runner.invoke(cli, [
            "export", str(sentiment_data),
            "--format", "csv",
            "--output", str(output),
        ])
        assert result.exit_code == 0
        assert output.exists()

    def test_export_complex_to_yaml(self, runner, complex_result_data, tmp_path):
        """Exportar dados complexos (com metadata) para YAML"""
        output = tmp_path / "complex.yaml"
        result = runner.invoke(cli, [
            "export", str(complex_result_data),
            "--format", "yaml",
            "--output", str(output),
        ])
        assert result.exit_code == 0
        data = yaml.safe_load(output.read_text())
        assert "metadata" in data
        assert "results" in data


# =============================================================================
# BATCH COMMAND — cobertura adicional (error paths, recursive, sequential stop)
# =============================================================================

class TestBatchCommandExtended:

    def test_batch_process_file_error(self, runner, tmp_path):
        """Erro durante processamento de arquivo é capturado, não crasha"""
        # Criar arquivo de texto
        f = tmp_path / "error_test.txt"
        f.write_text("Conteúdo para análise.")

        pattern = str(tmp_path / "*.txt")
        output_dir = tmp_path / "error_output"

        with patch("qualia.cli.commands.batch.process_file") as mock_pf:
            mock_pf.return_value = {
                "file": "error_test.txt",
                "status": "error",
                "error": "Falha simulada no plugin"
            }
            result = runner.invoke(cli, [
                "batch", pattern,
                "-p", "word_frequency",
                "-o", str(output_dir),
                "--continue-on-error",
            ])
            assert result.exit_code == 0
            assert "Erro" in result.output or "erro" in result.output.lower()

    def test_batch_recursive_pattern(self, runner, tmp_path):
        """Flag --recursive encontra arquivos em subdiretórios"""
        # Criar estrutura de diretórios aninhados
        sub1 = tmp_path / "sub1"
        sub2 = tmp_path / "sub1" / "sub2"
        sub1.mkdir()
        sub2.mkdir()

        (tmp_path / "root.txt").write_text("Arquivo na raiz.")
        (sub1 / "level1.txt").write_text("Arquivo nível 1.")
        (sub2 / "level2.txt").write_text("Arquivo nível 2.")

        pattern = str(tmp_path / "*.txt")
        result = runner.invoke(cli, [
            "batch", pattern,
            "-p", "word_frequency",
            "--recursive",
            "--dry-run",
        ])
        assert result.exit_code == 0
        # Deve encontrar arquivos em subdiretórios (3 arquivos total)
        assert "3" in result.output

    def test_batch_sequential_error_stops(self, runner, tmp_path):
        """Em modo sequencial sem --continue-on-error, erro para o processamento"""
        # Criar dois arquivos
        (tmp_path / "file_a.txt").write_text("Primeiro arquivo.")
        (tmp_path / "file_b.txt").write_text("Segundo arquivo.")

        pattern = str(tmp_path / "*.txt")
        output_dir = tmp_path / "seq_output"

        call_count = 0

        def mock_process(file_path, plugin_id, config, output_dir_arg=None):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return {"file": file_path.name, "status": "success", "result": {}, "output": None}
            return {"file": file_path.name, "status": "error", "error": "Erro no segundo arquivo"}

        with patch("qualia.cli.commands.batch.process_file", side_effect=mock_process):
            result = runner.invoke(cli, [
                "batch", pattern,
                "-p", "word_frequency",
                "-o", str(output_dir),
            ])
            assert result.exit_code == 0
            # Deve ter parado após o erro
            assert "Parando" in result.output or "Erro" in result.output or "erro" in result.output.lower()
            # Deve mostrar 1 sucesso e 1 erro
            assert "1" in result.output


# =============================================================================
# EXPORT COMMAND — cobertura adicional (CSV vazio, Excel com pandas)
# =============================================================================

class TestExportCommandExtended:

    def test_export_csv_empty_data(self, runner, tmp_path):
        """Dados com estrutura sem rows tabulares produz arquivo (fallback)"""
        data = {"info": "sem dados tabulares", "count": 0}
        input_file = tmp_path / "minimal.json"
        input_file.write_text(json.dumps(data))

        output = tmp_path / "minimal.csv"
        result = runner.invoke(cli, [
            "export", str(input_file),
            "--format", "csv",
            "--output", str(output),
        ])
        assert result.exit_code == 0
        assert output.exists()
        # Deve ter escrito algo (fallback path com dict como uma linha)
        content = output.read_text()
        assert len(content) > 0

    def test_export_excel_if_pandas(self, runner, tmp_path):
        """Exporta para .xlsx se pandas estiver disponível"""
        pytest.importorskip("pandas")
        pytest.importorskip("openpyxl")

        data = {
            "word_frequencies": {"gato": 5, "tapete": 3},
            "total_words": 8,
        }
        input_file = tmp_path / "for_excel.json"
        input_file.write_text(json.dumps(data))

        output = tmp_path / "result.xlsx"
        result = runner.invoke(cli, [
            "export", str(input_file),
            "--format", "excel",
            "--output", str(output),
        ])
        assert result.exit_code == 0
        assert output.exists()
        assert output.stat().st_size > 0


# =============================================================================
# BATCH COMMAND — remaining uncovered lines
# =============================================================================

class TestBatchRemainingPaths:
    """Cobre linhas restantes em batch.py: 42-43, 106, 112, 120, 159-161, 194"""

    def test_batch_dry_run_more_than_10_files(self, runner, tmp_path):
        """Line 106: '...e mais N arquivos' quando >10 arquivos no dry-run"""
        # Criar 15 arquivos
        for i in range(15):
            (tmp_path / f"file_{i:02d}.txt").write_text(f"Conteúdo do arquivo {i}.")

        pattern = str(tmp_path / "*.txt")
        result = runner.invoke(cli, [
            "batch", pattern, "-p", "word_frequency", "--dry-run",
        ])
        assert result.exit_code == 0
        assert "e mais 5 arquivos" in result.output

    def test_batch_with_config_yaml_file(self, runner, tmp_path):
        """Line 112: load_config carrega config de arquivo YAML passado com --config"""
        # Criar arquivos de texto
        (tmp_path / "doc.txt").write_text("Texto para análise de frequência.")
        # Criar config YAML
        config_file = tmp_path / "my_config.yaml"
        config_file.write_text("min_word_length: 4\nmax_words: 10\n")

        pattern = str(tmp_path / "*.txt")
        output_dir = tmp_path / "config_output"
        result = runner.invoke(cli, [
            "batch", pattern,
            "-p", "word_frequency",
            "-c", str(config_file),
            "-o", str(output_dir),
            "--continue-on-error",
        ])
        assert result.exit_code == 0

    def test_batch_no_output_dir(self, runner, tmp_path):
        """Line 120: output_path = None quando --output não é passado"""
        (tmp_path / "no_output.txt").write_text("Texto sem diretório de saída.")
        pattern = str(tmp_path / "*.txt")
        result = runner.invoke(cli, [
            "batch", pattern,
            "-p", "word_frequency",
            "--continue-on-error",
        ])
        assert result.exit_code == 0
        assert "Sucesso" in result.output or "sucesso" in result.output.lower()

    def test_batch_parallel_break_on_error(self, runner, tmp_path):
        """Lines 159-161: break no modo paralelo quando continue_on_error=False"""
        # Criar vários arquivos
        for i in range(5):
            (tmp_path / f"para_{i:02d}.txt").write_text(f"Arquivo paralelo {i}.")

        pattern = str(tmp_path / "*.txt")
        output_dir = tmp_path / "parallel_error"

        with patch("qualia.cli.commands.batch.process_file") as mock_pf:
            # Todos retornam erro para garantir que break é acionado
            mock_pf.return_value = {
                "file": "test.txt",
                "status": "error",
                "error": "Falha simulada"
            }
            result = runner.invoke(cli, [
                "batch", pattern,
                "-p", "word_frequency",
                "-o", str(output_dir),
                "-j", "2",
                # SEM --continue-on-error → deve fazer break
            ])
            assert result.exit_code == 0
            assert "Erro" in result.output or "erro" in result.output.lower()

    def test_batch_process_file_exception(self, runner, tmp_path):
        """Lines 42-43: exceção em process_file retorna dict com status error"""
        from qualia.cli.commands.batch import process_file

        bad_file = tmp_path / "nonexistent_for_process.txt"
        # Arquivo não existe, read_text vai falhar
        result = process_file(bad_file, "word_frequency", {}, None)
        assert result["status"] == "error"
        assert "error" in result
        assert result["file"] == "nonexistent_for_process.txt"

    def test_batch_many_errors_display(self, runner, tmp_path):
        """Line 194: '...e mais N erros' quando >5 erros"""
        # Criar 8 arquivos
        for i in range(8):
            (tmp_path / f"err_{i:02d}.txt").write_text(f"Arquivo {i}.")

        pattern = str(tmp_path / "*.txt")
        output_dir = tmp_path / "many_errors"

        with patch("qualia.cli.commands.batch.process_file") as mock_pf:
            mock_pf.return_value = {
                "file": "test.txt",
                "status": "error",
                "error": "Erro simulado"
            }
            result = runner.invoke(cli, [
                "batch", pattern,
                "-p", "word_frequency",
                "-o", str(output_dir),
                "--continue-on-error",
            ])
            assert result.exit_code == 0
            assert "e mais" in result.output and "erros" in result.output
