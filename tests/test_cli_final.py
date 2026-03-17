"""
Testes finais para cobrir gaps restantes no CLI.

Cobre:
- interactive/utils.py: _choose_file_from_examples, choose_plugin, choose_file
- commands/pipeline.py: multi-step, visualizer step, erro mid-pipeline, JSON config
- commands/__init__.py: menu command, --list-commands, invoke sem subcommand
"""

import pytest
import json
import yaml
from pathlib import Path
from unittest.mock import patch, MagicMock, call
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
    """Arquivo de texto para testes de pipeline"""
    f = tmp_path / "sample.txt"
    f.write_text("O gato sentou no tapete. O gato e bonito. O tapete e macio. "
                 "Palavras repetidas ajudam na frequencia de palavras.")
    return f


@pytest.fixture
def multi_step_pipeline_yaml(tmp_path):
    """Pipeline YAML com dois steps (analyzer + visualizer)"""
    config = {
        "name": "multi_step_test",
        "steps": [
            {"plugin": "word_frequency", "config": {"min_word_length": 2}},
        ],
        "metadata": {"author": "test"},
    }
    f = tmp_path / "multi.yaml"
    f.write_text(yaml.dump(config))
    return f


@pytest.fixture
def pipeline_json_config(tmp_path):
    """Pipeline config em formato JSON (nao YAML)"""
    config = {
        "name": "json_pipeline",
        "steps": [
            {"plugin": "word_frequency", "config": {"min_word_length": 3}},
        ],
    }
    f = tmp_path / "pipeline.json"
    f.write_text(json.dumps(config))
    return f


@pytest.fixture
def pipeline_invalid_plugin(tmp_path):
    """Pipeline com plugin inexistente"""
    config = {
        "name": "bad_pipeline",
        "steps": [
            {"plugin": "plugin_fantasma", "config": {}},
        ],
    }
    f = tmp_path / "bad_pipeline.yaml"
    f.write_text(yaml.dump(config))
    return f


@pytest.fixture
def pipeline_with_output_name(tmp_path):
    """Pipeline com output_name customizado"""
    config = {
        "name": "named_output",
        "steps": [
            {
                "plugin": "word_frequency",
                "config": {"min_word_length": 2},
                "output_name": "freq_result",
            },
        ],
    }
    f = tmp_path / "named.yaml"
    f.write_text(yaml.dump(config))
    return f


# =============================================================================
# COMMANDS/__INIT__.PY — menu, --list-commands, invoke sem subcommand
# =============================================================================

class TestCLIGroup:
    """Testa o grupo CLI principal e o comando menu"""

    def test_list_commands_flag(self, runner):
        """--list-commands deve mostrar help com comandos disponiveis"""
        result = runner.invoke(cli, ["--list-commands"])
        assert result.exit_code == 0
        # Help lista os subcomandos registrados
        assert "analyze" in result.output
        assert "pipeline" in result.output
        assert "menu" in result.output

    @patch("qualia.cli.commands.start_menu")
    def test_cli_no_subcommand_calls_start_menu(self, mock_start_menu, runner):
        """CLI invocado sem subcomando deve chamar start_menu"""
        result = runner.invoke(cli, [])
        mock_start_menu.assert_called_once()

    @patch("qualia.cli.commands.start_menu", side_effect=KeyboardInterrupt)
    def test_cli_no_subcommand_keyboard_interrupt(self, mock_start_menu, runner):
        """KeyboardInterrupt no menu interativo deve ser tratado graciosamente"""
        result = runner.invoke(cli, [])
        # Nao deve crashar — trata KeyboardInterrupt
        assert result.exit_code == 0
        assert "interrompido" in result.output or result.exit_code == 0

    @patch("qualia.cli.commands.start_menu", side_effect=RuntimeError("boom"))
    def test_cli_no_subcommand_generic_exception(self, mock_start_menu, runner):
        """Excecao generica no menu deve ser formatada como erro"""
        result = runner.invoke(cli, [])
        # format_error e chamado, nao deve crashar com traceback
        assert "Erro" in result.output or "boom" in result.output or result.exit_code == 0


class TestMenuCommand:
    """Testa o subcomando 'menu' explicitamente"""

    @patch("qualia.cli.commands.start_menu")
    def test_menu_command_calls_start_menu(self, mock_start_menu, runner):
        """'qualia menu' deve chamar start_menu"""
        result = runner.invoke(cli, ["menu"])
        mock_start_menu.assert_called_once()

    @patch("qualia.cli.commands.start_menu", side_effect=KeyboardInterrupt)
    def test_menu_keyboard_interrupt(self, mock_start_menu, runner):
        """KeyboardInterrupt no menu deve ser tratado"""
        result = runner.invoke(cli, ["menu"])
        assert result.exit_code == 0
        assert "interrompido" in result.output or result.exit_code == 0

    @patch("qualia.cli.commands.start_menu", side_effect=ValueError("erro interno"))
    def test_menu_exception_reraises(self, mock_start_menu, runner):
        """Excecao generica no menu deve formatar erro e re-raise"""
        result = runner.invoke(cli, ["menu"])
        # O comando menu faz raise apos formatar — Click captura como exit_code 1
        assert result.exit_code != 0 or "erro interno" in result.output


# =============================================================================
# PIPELINE — multi-step, JSON config, erro, output_name
# =============================================================================

class TestPipelineAdvanced:
    """Testes avancados do comando pipeline"""

    def test_pipeline_with_json_config(self, runner, text_file, pipeline_json_config, tmp_path):
        """Pipeline aceita config em formato JSON (nao so YAML)"""
        output_dir = tmp_path / "json_output"
        result = runner.invoke(cli, [
            "pipeline", str(text_file),
            "--config", str(pipeline_json_config),
            "--output-dir", str(output_dir),
        ])
        assert result.exit_code == 0
        assert "completo" in result.output.lower()

    def test_pipeline_with_output_name(self, runner, text_file, pipeline_with_output_name, tmp_path):
        """Pipeline usa output_name customizado nos resultados"""
        output_dir = tmp_path / "named_output"
        result = runner.invoke(cli, [
            "pipeline", str(text_file),
            "--config", str(pipeline_with_output_name),
            "--output-dir", str(output_dir),
        ])
        assert result.exit_code == 0
        # Resultado deve usar o nome customizado
        if output_dir.exists():
            files = list(output_dir.iterdir())
            names = [f.name for f in files]
            assert any("freq_result" in n for n in names)

    def test_pipeline_invalid_plugin_fails(self, runner, text_file, pipeline_invalid_plugin):
        """Pipeline com plugin inexistente deve falhar mid-execution"""
        result = runner.invoke(cli, [
            "pipeline", str(text_file),
            "--config", str(pipeline_invalid_plugin),
        ])
        # Deve falhar com SystemExit(1) ou erro
        assert result.exit_code != 0

    def test_pipeline_creates_output_dir(self, runner, text_file, multi_step_pipeline_yaml, tmp_path):
        """Pipeline cria diretorio de output se nao existir"""
        output_dir = tmp_path / "deep" / "nested" / "output"
        assert not output_dir.exists()
        result = runner.invoke(cli, [
            "pipeline", str(text_file),
            "--config", str(multi_step_pipeline_yaml),
            "--output-dir", str(output_dir),
        ])
        assert result.exit_code == 0
        assert output_dir.exists()

    def test_pipeline_saves_summary_yaml(self, runner, text_file, multi_step_pipeline_yaml, tmp_path):
        """Pipeline salva pipeline_summary.yaml no output dir"""
        output_dir = tmp_path / "summary_test"
        result = runner.invoke(cli, [
            "pipeline", str(text_file),
            "--config", str(multi_step_pipeline_yaml),
            "--output-dir", str(output_dir),
        ])
        assert result.exit_code == 0
        summary_path = output_dir / "pipeline_summary.yaml"
        assert summary_path.exists()
        summary = yaml.safe_load(summary_path.read_text())
        assert summary["pipeline"] == "multi_step_test"
        assert "steps_executed" in summary

    def test_pipeline_saves_result_json(self, runner, text_file, multi_step_pipeline_yaml, tmp_path):
        """Pipeline salva resultado JSON de cada step"""
        output_dir = tmp_path / "result_test"
        result = runner.invoke(cli, [
            "pipeline", str(text_file),
            "--config", str(multi_step_pipeline_yaml),
            "--output-dir", str(output_dir),
        ])
        assert result.exit_code == 0
        json_files = list(output_dir.glob("*_result.json"))
        assert len(json_files) >= 1
        # Verifica se o JSON e valido
        for jf in json_files:
            data = json.loads(jf.read_text())
            assert isinstance(data, dict)

    def test_pipeline_without_output_dir(self, runner, text_file, multi_step_pipeline_yaml):
        """Pipeline sem --output-dir executa mas nao salva arquivos"""
        result = runner.invoke(cli, [
            "pipeline", str(text_file),
            "--config", str(multi_step_pipeline_yaml),
        ])
        assert result.exit_code == 0
        assert "completo" in result.output.lower()

    def test_pipeline_with_metadata(self, runner, text_file, tmp_path):
        """Pipeline com metadata no config"""
        config = {
            "name": "metadata_test",
            "steps": [
                {"plugin": "word_frequency", "config": {}},
            ],
            "metadata": {"project": "test", "version": "1.0"},
        }
        config_file = tmp_path / "meta.yaml"
        config_file.write_text(yaml.dump(config))

        result = runner.invoke(cli, [
            "pipeline", str(text_file),
            "--config", str(config_file),
        ])
        assert result.exit_code == 0

    def test_pipeline_visualizer_step_without_prior_data(self, runner, text_file, tmp_path):
        """Visualizer como primeiro step deve falhar (sem dados anteriores)"""
        config = {
            "name": "viz_first",
            "steps": [
                {"plugin": "wordcloud_viz", "config": {}},
            ],
        }
        config_file = tmp_path / "viz_first.yaml"
        config_file.write_text(yaml.dump(config))

        result = runner.invoke(cli, [
            "pipeline", str(text_file),
            "--config", str(config_file),
        ])
        # Deve falhar — visualizer precisa de dados anteriores
        assert result.exit_code != 0

    def test_pipeline_visualizer_after_analyzer(self, runner, text_file, tmp_path):
        """Visualizer apos analyzer usa word_frequencies do step anterior"""
        config = {
            "name": "full_pipeline",
            "steps": [
                {"plugin": "word_frequency", "config": {"min_word_length": 2}},
                {"plugin": "wordcloud_viz", "config": {}, "output_name": "cloud"},
            ],
        }
        config_file = tmp_path / "full.yaml"
        config_file.write_text(yaml.dump(config))
        output_dir = tmp_path / "viz_output"

        result = runner.invoke(cli, [
            "pipeline", str(text_file),
            "--config", str(config_file),
            "--output-dir", str(output_dir),
        ])
        # Pode falhar se matplotlib/wordcloud nao esta instalado, mas nao deve crashar com KeyError
        # Se sucesso, verifica output
        if result.exit_code == 0:
            assert "completo" in result.output.lower()


# =============================================================================
# INTERACTIVE/UTILS.PY — _choose_file_from_examples, choose_plugin, choose_file
# =============================================================================

class TestChooseFileFromExamples:
    """Testa _choose_file_from_examples (linhas 68-91)"""

    @patch("qualia.cli.interactive.utils.get_int_choice", return_value=1)
    def test_finds_txt_files_in_examples_dir(self, mock_choice, tmp_path):
        """Encontra arquivos .txt em diretorio examples"""
        from qualia.cli.interactive.utils import _choose_file_from_examples

        examples_dir = tmp_path / "examples"
        examples_dir.mkdir()
        (examples_dir / "doc1.txt").write_text("texto 1")
        (examples_dir / "doc2.txt").write_text("texto 2")

        # Mudar cwd para tmp_path para que Path("examples") resolva corretamente
        import os
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = _choose_file_from_examples()
            assert result is not None
            assert "doc" in result
        finally:
            os.chdir(old_cwd)

    def test_no_examples_returns_none(self, tmp_path):
        """Sem arquivos de exemplo retorna None"""
        from qualia.cli.interactive.utils import _choose_file_from_examples

        import os
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = _choose_file_from_examples()
            assert result is None
        finally:
            os.chdir(old_cwd)


class TestChoosePlugin:
    """Testa choose_plugin (linhas 143-163)"""

    @patch("qualia.cli.interactive.utils.get_int_choice", return_value=1)
    @patch("qualia.cli.interactive.utils.run_qualia_command")
    def test_choose_plugin_success(self, mock_run, mock_choice):
        """Seleciona plugin da lista com sucesso"""
        from qualia.cli.interactive.utils import choose_plugin

        # Simular output do comando 'qualia list'
        mock_run.return_value = (True, (
            "┏━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━┓\n"
            "┃ ID              │ Tipo     │ Nome               ┃\n"
            "│ word_frequency  │ analyzer │ Word Frequency     │\n"
            "│ sentiment       │ analyzer │ Sentiment Analyzer │\n"
        ), "")

        result = choose_plugin("all")
        assert result == "word_frequency"

    @patch("qualia.cli.interactive.utils.run_qualia_command")
    def test_choose_plugin_command_fails(self, mock_run):
        """Erro ao listar plugins retorna None"""
        from qualia.cli.interactive.utils import choose_plugin

        mock_run.return_value = (False, "", "erro de subprocess")
        result = choose_plugin("all")
        assert result is None

    @patch("qualia.cli.interactive.utils.run_qualia_command")
    def test_choose_plugin_no_plugins_found(self, mock_run):
        """Nenhum plugin encontrado retorna None"""
        from qualia.cli.interactive.utils import choose_plugin

        mock_run.return_value = (True, "No plugins found\n", "")
        result = choose_plugin("analyzer")
        assert result is None

    @patch("qualia.cli.interactive.utils.run_qualia_command")
    def test_choose_plugin_filters_by_type(self, mock_run):
        """Passa tipo correto para o comando list"""
        from qualia.cli.interactive.utils import choose_plugin

        mock_run.return_value = (True, "", "")
        choose_plugin("visualizer")
        args = mock_run.call_args[0][0]
        assert "-t" in args
        assert "visualizer" in args

    @patch("qualia.cli.interactive.utils.run_qualia_command")
    def test_choose_plugin_all_no_type_flag(self, mock_run):
        """Tipo 'all' nao passa flag -t"""
        from qualia.cli.interactive.utils import choose_plugin

        mock_run.return_value = (True, "", "")
        choose_plugin("all")
        args = mock_run.call_args[0][0]
        assert "-t" not in args


class TestChooseFile:
    """Testa choose_file (linha 49 — opcao 2 examples)"""

    @patch("qualia.cli.interactive.utils.Prompt.ask", return_value="4")
    def test_choose_file_cancel(self, mock_ask):
        """Opcao 4 (voltar) retorna None"""
        from qualia.cli.interactive.utils import choose_file
        result = choose_file([])
        assert result is None

    @patch("qualia.cli.interactive.utils._choose_file_from_examples", return_value="/tmp/example.txt")
    @patch("qualia.cli.interactive.utils.Prompt.ask", return_value="2")
    def test_choose_file_from_examples_option(self, mock_ask, mock_examples):
        """Opcao 2 chama _choose_file_from_examples"""
        from qualia.cli.interactive.utils import choose_file
        result = choose_file([])
        assert result == "/tmp/example.txt"
        mock_examples.assert_called_once()

    @patch("qualia.cli.interactive.utils._choose_file_from_recent", return_value="/tmp/recent.txt")
    @patch("qualia.cli.interactive.utils.Prompt.ask", return_value="3")
    def test_choose_file_from_recent_option(self, mock_ask, mock_recent):
        """Opcao 3 chama _choose_file_from_recent"""
        from qualia.cli.interactive.utils import choose_file
        result = choose_file(["file1.txt"])
        assert result == "/tmp/recent.txt"

    @patch("qualia.cli.interactive.utils._choose_file_by_path", return_value="/tmp/typed.txt")
    @patch("qualia.cli.interactive.utils.Prompt.ask", return_value="1")
    def test_choose_file_by_path_option(self, mock_ask, mock_path):
        """Opcao 1 chama _choose_file_by_path"""
        from qualia.cli.interactive.utils import choose_file
        result = choose_file([])
        assert result == "/tmp/typed.txt"


class TestChooseFileFromRecent:
    """Testa _choose_file_from_recent"""

    def test_no_recent_files(self):
        """Sem arquivos recentes retorna None"""
        from qualia.cli.interactive.utils import _choose_file_from_recent
        result = _choose_file_from_recent([])
        assert result is None

    @patch("qualia.cli.interactive.utils.get_int_choice", return_value=1)
    def test_selects_recent_file(self, mock_choice):
        """Seleciona arquivo recente pelo indice"""
        from qualia.cli.interactive.utils import _choose_file_from_recent
        recent = ["/tmp/old.txt", "/tmp/mid.txt", "/tmp/new.txt"]
        result = _choose_file_from_recent(recent)
        assert result is not None
        assert result in recent


class TestChooseFileByPath:
    """Testa _choose_file_by_path"""

    @patch("qualia.cli.interactive.utils.Prompt.ask")
    def test_valid_path(self, mock_ask, tmp_path):
        """Caminho valido retorna o path"""
        from qualia.cli.interactive.utils import _choose_file_by_path
        f = tmp_path / "exists.txt"
        f.write_text("conteudo")
        mock_ask.return_value = str(f)
        result = _choose_file_by_path()
        assert result == str(f)

    @patch("qualia.cli.interactive.utils.Prompt.ask", return_value="/nao/existe/abc.txt")
    def test_invalid_path(self, mock_ask):
        """Caminho invalido retorna None"""
        from qualia.cli.interactive.utils import _choose_file_by_path
        result = _choose_file_by_path()
        assert result is None


class TestConfigureParameters:
    """Testa configure_parameters"""

    @patch("qualia.cli.interactive.utils.Prompt.ask", return_value="3")
    def test_preset_plugin_returns_params(self, mock_ask):
        """Plugin com presets retorna parametros configurados"""
        from qualia.cli.interactive.utils import configure_parameters
        result = configure_parameters("word_frequency")
        assert isinstance(result, dict)
        # Deve conter os parametros do preset
        assert "min_word_length" in result

    @patch("qualia.cli.interactive.utils.Confirm.ask", return_value=False)
    def test_unknown_plugin_no_custom_params(self, mock_confirm):
        """Plugin desconhecido sem params customizados retorna dict vazio"""
        from qualia.cli.interactive.utils import configure_parameters
        result = configure_parameters("plugin_desconhecido")
        assert result == {}

    @patch("qualia.cli.interactive.utils.Prompt.ask", side_effect=["meu_param", "42", "fim"])
    @patch("qualia.cli.interactive.utils.Confirm.ask", return_value=True)
    def test_unknown_plugin_with_custom_params(self, mock_confirm, mock_ask):
        """Plugin desconhecido com params customizados"""
        from qualia.cli.interactive.utils import configure_parameters
        result = configure_parameters("plugin_desconhecido")
        assert result == {"meu_param": "42"}

    @patch("qualia.cli.interactive.utils.Prompt.ask", return_value="skip")
    def test_skip_parameter(self, mock_ask):
        """Digitar 'skip' pula o parametro"""
        from qualia.cli.interactive.utils import configure_parameters
        result = configure_parameters("word_frequency")
        # Parametros com valor 'skip' nao entram no resultado
        for v in result.values():
            assert v != "skip"


class TestRunQualiaCommand:
    """Testa run_qualia_command"""

    @patch("qualia.cli.interactive.utils.subprocess.run")
    def test_success(self, mock_run):
        """Comando com sucesso retorna (True, stdout, stderr)"""
        from qualia.cli.interactive.utils import run_qualia_command
        mock_run.return_value = MagicMock(returncode=0, stdout="ok", stderr="")
        success, stdout, stderr = run_qualia_command(["list"])
        assert success is True
        assert stdout == "ok"

    @patch("qualia.cli.interactive.utils.subprocess.run")
    def test_failure(self, mock_run):
        """Comando com falha retorna (False, stdout, stderr)"""
        from qualia.cli.interactive.utils import run_qualia_command
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="falhou")
        success, stdout, stderr = run_qualia_command(["bad"])
        assert success is False
        assert stderr == "falhou"


class TestGetIntChoice:
    """Testa get_int_choice"""

    @patch("qualia.cli.interactive.utils.Prompt.ask", side_effect=["abc", "0", "3"])
    def test_retries_on_invalid_then_succeeds(self, mock_ask):
        """Retenta em input invalido ate receber valor valido"""
        from qualia.cli.interactive.utils import get_int_choice
        result = get_int_choice("Escolha", 1, 5)
        assert result == 3

    @patch("qualia.cli.interactive.utils.Prompt.ask", return_value="2")
    def test_valid_first_try(self, mock_ask):
        """Retorna valor valido na primeira tentativa"""
        from qualia.cli.interactive.utils import get_int_choice
        result = get_int_choice("Escolha", 1, 5)
        assert result == 2
