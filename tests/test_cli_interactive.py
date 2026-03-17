"""
Testes do menu interativo do Qualia (handlers, menu, utils, wizards).

Foco principal: handlers.py (cobertura anterior: 9%).
Estratégia: mock de Rich Prompt/Confirm, run_qualia_command e filesystem.
"""

import pytest
import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, call


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def mock_menu():
    """Menu mock com atributos básicos"""
    menu = MagicMock()
    menu.recent_files = []
    menu.current_analysis = None
    menu.show_banner = MagicMock()
    menu.add_recent_file = MagicMock()
    return menu


@pytest.fixture
def handlers(mock_menu):
    """MenuHandlers com menu mockado"""
    from qualia.cli.interactive.handlers import MenuHandlers
    return MenuHandlers(mock_menu)


@pytest.fixture
def tmp_json(tmp_path):
    """Cria arquivo JSON temporário"""
    data = {"word_frequencies": {"gato": 5, "cachorro": 3}, "total_words": 8}
    f = tmp_path / "result.json"
    f.write_text(json.dumps(data))
    return f


@pytest.fixture
def tmp_text(tmp_path):
    """Cria arquivo de texto temporário"""
    f = tmp_path / "sample.txt"
    f.write_text("O gato sentou no tapete.")
    return f


# =============================================================================
# IMPORTS (__init__.py)
# =============================================================================

class TestImports:

    def test_start_menu_importable(self):
        from qualia.cli.interactive import start_menu
        assert callable(start_menu)

    def test_menu_class_importable(self):
        from qualia.cli.interactive import QualiaInteractiveMenu
        assert QualiaInteractiveMenu is not None

    def test_all_exports(self):
        from qualia.cli.interactive import __all__
        assert 'start_menu' in __all__
        assert 'QualiaInteractiveMenu' in __all__


# =============================================================================
# UTILS — funções puras e utilitárias
# =============================================================================

class TestParsePluginList:
    """Testa parse_plugin_list que não depende de I/O"""

    def test_parse_table_output(self):
        from qualia.cli.interactive.utils import parse_plugin_list
        output = (
            "┏━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┓\n"
            "┃ ID              ┃ Tipo     ┃ Nome                ┃\n"
            "┡━━━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━┩\n"
            "│ word_frequency  │ analyzer │ Word Frequency      │\n"
            "│ wordcloud_viz   │ visualizer│ Word Cloud          │\n"
            "└─────────────────┴──────────┴─────────────────────┘\n"
        )
        plugins = parse_plugin_list(output)
        assert len(plugins) == 2
        ids = [p[0] for p in plugins]
        assert "word_frequency" in ids
        assert "wordcloud_viz" in ids

    def test_parse_filter_by_type(self):
        from qualia.cli.interactive.utils import parse_plugin_list
        output = (
            "│ word_frequency  │ analyzer │ Word Frequency      │\n"
            "│ wordcloud_viz   │ visualizer│ Word Cloud          │\n"
        )
        plugins = parse_plugin_list(output, "analyzer")
        assert len(plugins) == 1
        assert plugins[0][0] == "word_frequency"

    def test_parse_empty_output(self):
        from qualia.cli.interactive.utils import parse_plugin_list
        assert parse_plugin_list("") == []
        assert parse_plugin_list("No plugins found") == []

    def test_parse_header_only(self):
        from qualia.cli.interactive.utils import parse_plugin_list
        output = "┃ ID ┃ Tipo ┃ Nome ┃\n"
        assert parse_plugin_list(output) == []


class TestShowFilePreview:
    """Testa show_file_preview com arquivos reais"""

    def test_preview_json_file(self, tmp_json):
        from qualia.cli.interactive.utils import show_file_preview
        # Não deve levantar exceção
        show_file_preview(str(tmp_json))

    def test_preview_text_file(self, tmp_text):
        from qualia.cli.interactive.utils import show_file_preview
        show_file_preview(str(tmp_text))

    def test_preview_nonexistent_file(self):
        from qualia.cli.interactive.utils import show_file_preview
        # Não deve crashar — trata exceção internamente
        show_file_preview("/nonexistent/file.json")

    def test_preview_text_file_with_many_lines(self, tmp_path):
        from qualia.cli.interactive.utils import show_file_preview
        f = tmp_path / "long.txt"
        f.write_text("\n".join(f"Linha {i}" for i in range(20)))
        show_file_preview(str(f), max_lines=3)


class TestRunQualiaCommand:

    @patch("qualia.cli.interactive.utils.subprocess.run")
    def test_success(self, mock_run):
        from qualia.cli.interactive.utils import run_qualia_command
        mock_run.return_value = MagicMock(returncode=0, stdout="ok", stderr="")
        success, stdout, stderr = run_qualia_command(["list"])
        assert success is True
        assert stdout == "ok"
        mock_run.assert_called_once_with(
            ["python", "-m", "qualia", "list"],
            capture_output=True, text=True
        )

    @patch("qualia.cli.interactive.utils.subprocess.run")
    def test_failure(self, mock_run):
        from qualia.cli.interactive.utils import run_qualia_command
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="erro")
        success, stdout, stderr = run_qualia_command(["analyze"])
        assert success is False
        assert stderr == "erro"


class TestChooseFile:

    @patch("qualia.cli.interactive.utils.Prompt.ask", return_value="4")
    def test_choose_back(self, mock_ask):
        from qualia.cli.interactive.utils import choose_file
        result = choose_file([])
        assert result is None

    @patch("qualia.cli.interactive.utils.Prompt.ask")
    def test_choose_by_path_exists(self, mock_ask, tmp_text):
        from qualia.cli.interactive.utils import choose_file
        mock_ask.side_effect = ["1", str(tmp_text)]
        result = choose_file([])
        assert result == str(tmp_text)

    @patch("qualia.cli.interactive.utils.Prompt.ask")
    def test_choose_by_path_not_exists(self, mock_ask):
        from qualia.cli.interactive.utils import choose_file
        mock_ask.side_effect = ["1", "/nonexistent/file.txt"]
        result = choose_file([])
        assert result is None

    @patch("qualia.cli.interactive.utils.Prompt.ask")
    @patch("qualia.cli.interactive.utils.get_int_choice", return_value=1)
    def test_choose_from_recent(self, mock_int, mock_ask):
        from qualia.cli.interactive.utils import choose_file
        mock_ask.return_value = "3"
        result = choose_file(["/some/file.txt", "/other/file.txt"])
        assert result is not None

    @patch("qualia.cli.interactive.utils.Prompt.ask", return_value="3")
    def test_choose_from_recent_empty(self, mock_ask):
        from qualia.cli.interactive.utils import choose_file
        result = choose_file([])
        assert result is None


class TestConfigureParameters:

    @patch("qualia.cli.interactive.utils.Prompt.ask")
    def test_known_plugin_defaults(self, mock_ask):
        """Plugin conhecido (word_frequency) usa presets"""
        from qualia.cli.interactive.utils import configure_parameters
        # Aceitar todos os defaults
        mock_ask.side_effect = ["3", "true", "portuguese"]
        params = configure_parameters("word_frequency")
        assert "min_word_length" in params
        assert "remove_stopwords" in params
        assert "language" in params

    @patch("qualia.cli.interactive.utils.Confirm.ask", return_value=False)
    def test_unknown_plugin_no_custom(self, mock_confirm):
        """Plugin desconhecido sem parâmetros custom"""
        from qualia.cli.interactive.utils import configure_parameters
        params = configure_parameters("some_plugin")
        assert params == {}

    @patch("qualia.cli.interactive.utils.Prompt.ask")
    @patch("qualia.cli.interactive.utils.Confirm.ask", return_value=True)
    def test_unknown_plugin_with_custom(self, mock_confirm, mock_ask):
        """Plugin desconhecido com parâmetros custom"""
        from qualia.cli.interactive.utils import configure_parameters
        mock_ask.side_effect = ["my_param", "my_value", "fim"]
        params = configure_parameters("unknown_plugin")
        assert params == {"my_param": "my_value"}

    @patch("qualia.cli.interactive.utils.Prompt.ask")
    def test_skip_parameter(self, mock_ask):
        """Digitar 'skip' em um parâmetro preset o exclui"""
        from qualia.cli.interactive.utils import configure_parameters
        mock_ask.side_effect = ["skip", "true", "portuguese"]
        params = configure_parameters("word_frequency")
        assert "min_word_length" not in params
        assert "remove_stopwords" in params


class TestGetIntChoice:

    @patch("qualia.cli.interactive.utils.Prompt.ask", return_value="2")
    def test_valid_choice(self, mock_ask):
        from qualia.cli.interactive.utils import get_int_choice
        assert get_int_choice("Escolha", 1, 5) == 2

    @patch("qualia.cli.interactive.utils.Prompt.ask", side_effect=["abc", "0", "3"])
    def test_retries_on_invalid(self, mock_ask):
        """Repete até receber valor válido"""
        from qualia.cli.interactive.utils import get_int_choice
        result = get_int_choice("Escolha", 1, 5)
        assert result == 3
        assert mock_ask.call_count == 3


# =============================================================================
# HANDLERS — testes com mock de I/O
# =============================================================================

class TestAnalyzeDocument:

    @patch("qualia.cli.interactive.handlers.Prompt.ask")
    @patch("qualia.cli.interactive.handlers.Confirm.ask", return_value=False)
    @patch("qualia.cli.interactive.handlers.configure_parameters", return_value={})
    @patch("qualia.cli.interactive.handlers.choose_plugin", return_value="word_frequency")
    @patch("qualia.cli.interactive.handlers.choose_file", return_value="/tmp/test.txt")
    @patch("qualia.cli.interactive.handlers.run_qualia_command", return_value=(True, "ok", ""))
    def test_happy_path(self, mock_cmd, mock_file, mock_plugin, mock_params,
                        mock_confirm, mock_prompt, handlers):
        mock_prompt.return_value = "output.json"
        handlers.analyze_document()
        handlers.menu.add_recent_file.assert_called_with("/tmp/test.txt")
        mock_cmd.assert_called_once()

    @patch("qualia.cli.interactive.handlers.choose_file", return_value=None)
    def test_no_file_selected(self, mock_file, handlers):
        """Retorna cedo se nenhum arquivo selecionado"""
        handlers.analyze_document()
        handlers.menu.add_recent_file.assert_not_called()

    @patch("qualia.cli.interactive.handlers.choose_file", return_value="/tmp/test.txt")
    @patch("qualia.cli.interactive.handlers.choose_plugin", return_value=None)
    def test_no_plugin_selected(self, mock_plugin, mock_file, handlers):
        """Retorna cedo se nenhum plugin selecionado"""
        handlers.analyze_document()
        # add_recent_file é chamado antes de choose_plugin
        handlers.menu.add_recent_file.assert_called_once()

    @patch("qualia.cli.interactive.handlers.Prompt.ask")
    @patch("qualia.cli.interactive.handlers.Confirm.ask", return_value=False)
    @patch("qualia.cli.interactive.handlers.configure_parameters", return_value={"min_word_length": "3"})
    @patch("qualia.cli.interactive.handlers.choose_plugin", return_value="word_frequency")
    @patch("qualia.cli.interactive.handlers.choose_file", return_value="/tmp/test.txt")
    @patch("qualia.cli.interactive.handlers.run_qualia_command", return_value=(False, "", "falhou"))
    def test_analysis_failure(self, mock_cmd, mock_file, mock_plugin, mock_params,
                              mock_confirm, mock_prompt, handlers):
        """Análise que falha mostra erro sem crashar"""
        mock_prompt.return_value = "output.json"
        handlers.analyze_document()
        # Não deve levantar exceção


class TestVisualizeResults:

    @patch("qualia.cli.interactive.handlers.Prompt.ask")
    @patch("qualia.cli.interactive.handlers.Confirm.ask", return_value=False)
    @patch("qualia.cli.interactive.handlers.configure_parameters", return_value={})
    @patch("qualia.cli.interactive.handlers.choose_plugin", return_value="wordcloud_viz")
    @patch("qualia.cli.interactive.handlers.show_file_preview")
    @patch("qualia.cli.interactive.handlers.run_qualia_command", return_value=(True, "ok", ""))
    def test_with_data_file(self, mock_cmd, mock_preview, mock_plugin,
                            mock_params, mock_confirm, mock_prompt, handlers):
        mock_prompt.side_effect = ["1", "output.png", ""]
        handlers.visualize_results(data_file="/tmp/data.json")
        mock_preview.assert_called_with("/tmp/data.json")
        mock_cmd.assert_called_once()

    @patch("qualia.cli.interactive.handlers.choose_plugin", return_value=None)
    @patch("qualia.cli.interactive.handlers.show_file_preview")
    def test_no_visualizer_selected(self, mock_preview, mock_plugin, handlers):
        """Retorna cedo se nenhum visualizer selecionado"""
        handlers.visualize_results(data_file="/tmp/data.json")

    @patch("qualia.cli.interactive.handlers.Prompt.ask")
    @patch("qualia.cli.interactive.handlers.Confirm.ask", return_value=False)
    @patch("qualia.cli.interactive.handlers.configure_parameters", return_value={})
    @patch("qualia.cli.interactive.handlers.choose_plugin", return_value="wordcloud_viz")
    @patch("qualia.cli.interactive.handlers.show_file_preview")
    @patch("qualia.cli.interactive.handlers.run_qualia_command", return_value=(False, "", "erro viz"))
    def test_visualization_failure(self, mock_cmd, mock_preview, mock_plugin,
                                   mock_params, mock_confirm, mock_prompt, handlers):
        """Falha na visualização não crasha"""
        mock_prompt.side_effect = ["1", "out.png", ""]
        handlers.visualize_results(data_file="/tmp/data.json")


class TestRunPipeline:

    @patch("qualia.cli.interactive.handlers.Prompt.ask")
    @patch("qualia.cli.interactive.handlers.Confirm.ask", return_value=False)
    def test_no_pipeline_dir_decline_create(self, mock_confirm, mock_prompt, handlers, tmp_path, monkeypatch):
        """Recusa criar diretório de pipelines"""
        monkeypatch.chdir(tmp_path)
        handlers.run_pipeline()
        # Não deve crashar

    @patch("qualia.cli.interactive.handlers.Prompt.ask")
    @patch("qualia.cli.interactive.handlers.Confirm.ask", return_value=True)
    def test_no_pipeline_dir_accept_create(self, mock_confirm, mock_prompt, handlers, tmp_path, monkeypatch):
        """Aceita criar diretório de pipelines"""
        monkeypatch.chdir(tmp_path)
        mock_prompt.return_value = ""
        # Confirm.ask retorna True pra criar dir e True pra criar pipeline
        mock_confirm.side_effect = [True, False]
        handlers.run_pipeline()
        assert (tmp_path / "configs" / "pipelines").exists()

    @patch("qualia.cli.interactive.handlers.Prompt.ask", return_value="")
    @patch("qualia.cli.interactive.handlers.get_int_choice", return_value=1)
    @patch("qualia.cli.interactive.handlers.choose_file", return_value="/tmp/test.txt")
    @patch("qualia.cli.interactive.handlers.run_qualia_command", return_value=(True, "ok", ""))
    def test_execute_existing_pipeline(self, mock_cmd, mock_file, mock_choice,
                                       mock_prompt, handlers, tmp_path, monkeypatch):
        """Executa pipeline existente"""
        monkeypatch.chdir(tmp_path)
        pipeline_dir = tmp_path / "configs" / "pipelines"
        pipeline_dir.mkdir(parents=True)
        (pipeline_dir / "test.yaml").write_text("name: test\nsteps: []")

        handlers.run_pipeline()
        mock_cmd.assert_called_once()

    @patch("qualia.cli.interactive.handlers.Prompt.ask", return_value="")
    @patch("qualia.cli.interactive.handlers.get_int_choice", return_value=1)
    @patch("qualia.cli.interactive.handlers.choose_file", return_value=None)
    def test_execute_pipeline_no_file(self, mock_file, mock_choice, mock_prompt,
                                      handlers, tmp_path, monkeypatch):
        """Pipeline sem arquivo selecionado retorna cedo"""
        monkeypatch.chdir(tmp_path)
        pipeline_dir = tmp_path / "configs" / "pipelines"
        pipeline_dir.mkdir(parents=True)
        (pipeline_dir / "test.yaml").write_text("name: test")
        handlers.run_pipeline()


class TestExplorePlugins:

    @patch("qualia.cli.interactive.handlers.Prompt.ask", return_value="")
    @patch("qualia.cli.interactive.handlers.run_qualia_command", return_value=(True, "plugin list", ""))
    def test_list_success_no_inspect(self, mock_cmd, mock_prompt, handlers):
        """Lista plugins com sucesso, não inspeciona nenhum"""
        handlers.explore_plugins()
        mock_cmd.assert_called_once_with(["list", "-d"])

    @patch("qualia.cli.interactive.handlers.Prompt.ask")
    @patch("qualia.cli.interactive.handlers.run_qualia_command")
    def test_list_and_inspect(self, mock_cmd, mock_prompt, handlers):
        """Lista e depois inspeciona um plugin"""
        mock_cmd.side_effect = [
            (True, "lista", ""),
            (True, "detalhes do plugin", "")
        ]
        mock_prompt.side_effect = ["word_frequency", ""]
        handlers.explore_plugins()
        assert mock_cmd.call_count == 2
        mock_cmd.assert_any_call(["inspect", "word_frequency"])

    @patch("qualia.cli.interactive.handlers.Prompt.ask")
    @patch("qualia.cli.interactive.handlers.run_qualia_command")
    def test_list_failure(self, mock_cmd, mock_prompt, handlers):
        """Falha ao listar plugins"""
        mock_cmd.return_value = (False, "", "erro")
        mock_prompt.side_effect = ["", ""]
        handlers.explore_plugins()

    @patch("qualia.cli.interactive.handlers.Prompt.ask")
    @patch("qualia.cli.interactive.handlers.run_qualia_command")
    def test_inspect_not_found(self, mock_cmd, mock_prompt, handlers):
        """Inspeciona plugin inexistente"""
        mock_cmd.side_effect = [
            (True, "lista", ""),
            (False, "", "not found")
        ]
        mock_prompt.side_effect = ["nao_existe", ""]
        handlers.explore_plugins()


class TestSettingsMenu:

    @patch("qualia.cli.interactive.handlers.Prompt.ask", return_value="5")
    def test_back(self, mock_prompt, handlers):
        """Opção 'Voltar' não executa nada"""
        handlers.settings_menu()

    @patch("qualia.cli.interactive.handlers.Prompt.ask")
    @patch("qualia.cli.interactive.handlers.Confirm.ask", return_value=True)
    def test_clear_cache(self, mock_confirm, mock_prompt, handlers, tmp_path, monkeypatch):
        """Limpa cache com sucesso"""
        monkeypatch.chdir(tmp_path)
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        (cache_dir / "item.dat").write_text("data")

        mock_prompt.side_effect = ["1", ""]
        handlers.settings_menu()
        # Cache dir deve existir mas vazio
        assert cache_dir.exists()
        assert list(cache_dir.iterdir()) == []

    @patch("qualia.cli.interactive.handlers.Prompt.ask")
    @patch("qualia.cli.interactive.handlers.Confirm.ask", return_value=False)
    def test_clear_cache_decline(self, mock_confirm, mock_prompt, handlers, tmp_path, monkeypatch):
        """Recusa limpar cache"""
        monkeypatch.chdir(tmp_path)
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        (cache_dir / "item.dat").write_text("data")

        mock_prompt.side_effect = ["1", ""]
        handlers.settings_menu()
        # Arquivo deve continuar lá
        assert (cache_dir / "item.dat").exists()

    @patch("qualia.cli.interactive.handlers.Prompt.ask")
    def test_show_config(self, mock_prompt, handlers, tmp_path, monkeypatch):
        """Mostra configuração sem crashar"""
        monkeypatch.chdir(tmp_path)
        # Criar diretório plugins pra contagem
        plugins_dir = tmp_path / "plugins"
        plugins_dir.mkdir()
        plugin = plugins_dir / "test_plugin"
        plugin.mkdir()
        (plugin / "__init__.py").write_text("")

        mock_prompt.side_effect = ["2", ""]
        handlers.settings_menu()

    @patch("qualia.cli.interactive.handlers.Prompt.ask")
    @patch("qualia.cli.interactive.handlers.run_qualia_command", return_value=(True, "qualia 0.1.0", ""))
    def test_verify_installation(self, mock_cmd, mock_prompt, handlers, tmp_path, monkeypatch):
        """Verifica instalação"""
        monkeypatch.chdir(tmp_path)
        mock_prompt.side_effect = ["4", ""]
        handlers.settings_menu()
        mock_cmd.assert_called_with(["--version"])

    @patch("qualia.cli.interactive.handlers.Prompt.ask")
    @patch("qualia.cli.interactive.handlers.run_qualia_command", return_value=(False, "", "erro"))
    def test_verify_installation_failure(self, mock_cmd, mock_prompt, handlers, tmp_path, monkeypatch):
        """Verifica instalação com falha"""
        monkeypatch.chdir(tmp_path)
        mock_prompt.side_effect = ["4", ""]
        handlers.settings_menu()

    @patch("qualia.cli.interactive.handlers.Prompt.ask")
    @patch("qualia.cli.interactive.handlers.choose_plugin", return_value="word_frequency")
    def test_install_deps_no_requirements(self, mock_plugin, mock_prompt, handlers, tmp_path, monkeypatch):
        """Instalar deps de plugin sem requirements.txt"""
        monkeypatch.chdir(tmp_path)
        mock_prompt.side_effect = ["3", ""]
        handlers.settings_menu()

    @patch("qualia.cli.interactive.handlers.Prompt.ask")
    @patch("qualia.cli.interactive.handlers.choose_plugin", return_value=None)
    def test_install_deps_no_plugin(self, mock_plugin, mock_prompt, handlers):
        """Instalar deps sem selecionar plugin"""
        mock_prompt.side_effect = ["3", ""]
        handlers.settings_menu()


class TestProcessDocument:

    @patch("qualia.cli.interactive.handlers.Prompt.ask", return_value="")
    @patch("qualia.cli.interactive.handlers.configure_parameters", return_value={})
    @patch("qualia.cli.interactive.handlers.choose_plugin", return_value="teams_cleaner")
    @patch("qualia.cli.interactive.handlers.choose_file", return_value="/tmp/chat.txt")
    @patch("qualia.cli.interactive.handlers.run_qualia_command", return_value=(True, "processado", ""))
    def test_happy_path(self, mock_cmd, mock_file, mock_plugin, mock_params,
                        mock_prompt, handlers):
        handlers.process_document()
        handlers.menu.add_recent_file.assert_called_with("/tmp/chat.txt")
        args = mock_cmd.call_args[0][0]
        assert "process" in args
        assert "teams_cleaner" in args

    @patch("qualia.cli.interactive.handlers.choose_file", return_value=None)
    def test_no_file(self, mock_file, handlers):
        handlers.process_document()
        handlers.menu.add_recent_file.assert_not_called()

    @patch("qualia.cli.interactive.handlers.choose_file", return_value="/tmp/chat.txt")
    @patch("qualia.cli.interactive.handlers.choose_plugin", return_value=None)
    def test_no_plugin(self, mock_plugin, mock_file, handlers):
        handlers.process_document()

    @patch("qualia.cli.interactive.handlers.Prompt.ask", return_value="")
    @patch("qualia.cli.interactive.handlers.configure_parameters", return_value={"k": "v"})
    @patch("qualia.cli.interactive.handlers.choose_plugin", return_value="teams_cleaner")
    @patch("qualia.cli.interactive.handlers.choose_file", return_value="/tmp/chat.txt")
    @patch("qualia.cli.interactive.handlers.run_qualia_command", return_value=(False, "", "erro"))
    def test_failure(self, mock_cmd, mock_file, mock_plugin, mock_params,
                     mock_prompt, handlers):
        """Processamento que falha não crasha"""
        handlers.process_document()


class TestBatchProcess:

    @patch("qualia.cli.interactive.handlers.Prompt.ask")
    @patch("qualia.cli.interactive.handlers.Confirm.ask", return_value=True)
    @patch("qualia.cli.interactive.handlers.configure_parameters", return_value={})
    @patch("qualia.cli.interactive.handlers.choose_plugin", return_value="word_frequency")
    @patch("qualia.cli.interactive.handlers.run_qualia_command", return_value=(True, "batch ok", ""))
    def test_happy_path(self, mock_cmd, mock_plugin, mock_params,
                        mock_confirm, mock_prompt, handlers, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        mock_prompt.side_effect = ["*.txt", str(tmp_path / "results"), ""]
        handlers.batch_process()
        args = mock_cmd.call_args[0][0]
        assert "batch" in args
        assert "--continue-on-error" in args

    @patch("qualia.cli.interactive.handlers.Prompt.ask")
    @patch("qualia.cli.interactive.handlers.choose_plugin", return_value=None)
    def test_no_plugin(self, mock_plugin, mock_prompt, handlers):
        mock_prompt.return_value = "*.txt"
        handlers.batch_process()

    @patch("qualia.cli.interactive.handlers.Prompt.ask")
    @patch("qualia.cli.interactive.handlers.Confirm.ask", return_value=False)
    @patch("qualia.cli.interactive.handlers.configure_parameters", return_value={})
    @patch("qualia.cli.interactive.handlers.choose_plugin", return_value="word_frequency")
    @patch("qualia.cli.interactive.handlers.run_qualia_command", return_value=(True, "ok", ""))
    def test_no_continue_on_error(self, mock_cmd, mock_plugin, mock_params,
                                  mock_confirm, mock_prompt, handlers, tmp_path, monkeypatch):
        """Sem --continue-on-error quando recusa"""
        monkeypatch.chdir(tmp_path)
        mock_prompt.side_effect = ["*.txt", str(tmp_path / "out"), ""]
        handlers.batch_process()
        args = mock_cmd.call_args[0][0]
        assert "--continue-on-error" not in args

    @patch("qualia.cli.interactive.handlers.Prompt.ask")
    @patch("qualia.cli.interactive.handlers.Confirm.ask", return_value=True)
    @patch("qualia.cli.interactive.handlers.configure_parameters", return_value={})
    @patch("qualia.cli.interactive.handlers.choose_plugin", return_value="word_frequency")
    @patch("qualia.cli.interactive.handlers.run_qualia_command", return_value=(False, "", "batch falhou"))
    def test_batch_failure(self, mock_cmd, mock_plugin, mock_params,
                           mock_confirm, mock_prompt, handlers, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        mock_prompt.side_effect = ["*.txt", str(tmp_path / "out"), ""]
        handlers.batch_process()


class TestWatchFolder:

    @patch("qualia.cli.interactive.handlers.Prompt.ask")
    def test_folder_not_found(self, mock_prompt, handlers):
        mock_prompt.side_effect = ["/nonexistent/folder", ""]
        handlers.watch_folder()

    @patch("qualia.cli.interactive.handlers.Prompt.ask")
    @patch("qualia.cli.interactive.handlers.choose_plugin", return_value=None)
    def test_no_plugin(self, mock_plugin, mock_prompt, handlers, tmp_path):
        mock_prompt.return_value = str(tmp_path)
        handlers.watch_folder()

    @patch("qualia.cli.interactive.handlers.Prompt.ask")
    @patch("qualia.cli.interactive.handlers.choose_plugin", return_value="word_frequency")
    @patch("qualia.cli.interactive.handlers.run_qualia_command", return_value=(True, "watching", ""))
    def test_happy_path(self, mock_cmd, mock_plugin, mock_prompt, handlers, tmp_path):
        mock_prompt.side_effect = [str(tmp_path), "*.txt", "results/watch", ""]
        handlers.watch_folder()
        args = mock_cmd.call_args[0][0]
        assert "watch" in args
        assert str(tmp_path) in args

    @patch("qualia.cli.interactive.handlers.Prompt.ask")
    @patch("qualia.cli.interactive.handlers.choose_plugin", return_value="word_frequency")
    @patch("qualia.cli.interactive.handlers.run_qualia_command", return_value=(False, "", "erro watch"))
    def test_watch_failure(self, mock_cmd, mock_plugin, mock_prompt, handlers, tmp_path):
        mock_prompt.side_effect = [str(tmp_path), "*.txt", "results/watch", ""]
        handlers.watch_folder()


class TestExportResults:

    @patch("qualia.cli.interactive.handlers.Prompt.ask")
    @patch("qualia.cli.interactive.handlers.run_qualia_command", return_value=(True, "exportado", ""))
    def test_happy_path(self, mock_cmd, mock_prompt, handlers):
        # Mock _choose_data_file
        handlers._choose_data_file = MagicMock(return_value="/tmp/data.json")
        mock_prompt.side_effect = ["1", "output.csv", ""]
        handlers.export_results()
        args = mock_cmd.call_args[0][0]
        assert "export" in args
        assert "-f" in args
        assert "csv" in args

    def test_no_data_file(self, handlers):
        handlers._choose_data_file = MagicMock(return_value=None)
        handlers.export_results()

    @patch("qualia.cli.interactive.handlers.Prompt.ask")
    @patch("qualia.cli.interactive.handlers.run_qualia_command", return_value=(False, "", "erro"))
    def test_export_failure(self, mock_cmd, mock_prompt, handlers):
        handlers._choose_data_file = MagicMock(return_value="/tmp/data.json")
        mock_prompt.side_effect = ["3", "output.md", ""]
        handlers.export_results()

    @patch("qualia.cli.interactive.handlers.Prompt.ask")
    @patch("qualia.cli.interactive.handlers.run_qualia_command", return_value=(True, "ok", ""))
    def test_all_formats(self, mock_cmd, mock_prompt, handlers):
        """Testa todos os formatos de exportação"""
        format_map = {"1": "csv", "2": "excel", "3": "markdown", "4": "html", "5": "yaml"}
        for choice, fmt in format_map.items():
            handlers._choose_data_file = MagicMock(return_value="/tmp/data.json")
            mock_prompt.side_effect = [choice, f"output.{fmt}", ""]
            handlers.export_results()
            args = mock_cmd.call_args[0][0]
            assert fmt in args


class TestChooseDataFile:

    @patch("qualia.cli.interactive.handlers.Confirm.ask", return_value=True)
    def test_use_current_analysis(self, mock_confirm, handlers):
        handlers.menu.current_analysis = "/tmp/analysis.json"
        result = handlers._choose_data_file()
        assert result == "/tmp/analysis.json"

    @patch("qualia.cli.interactive.handlers.Confirm.ask", return_value=False)
    @patch("qualia.cli.interactive.handlers.Prompt.ask", return_value="/nonexistent.json")
    @patch("qualia.cli.interactive.handlers.get_int_choice")
    def test_current_analysis_declined_no_files(self, mock_int, mock_prompt,
                                                 mock_confirm, handlers, tmp_path, monkeypatch):
        """Recusa análise atual, sem JSON encontrado, caminho inexistente"""
        monkeypatch.chdir(tmp_path)
        handlers.menu.current_analysis = "/tmp/old.json"
        result = handlers._choose_data_file()
        assert result is None

    @patch("qualia.cli.interactive.handlers.get_int_choice", return_value=1)
    def test_choose_from_list(self, mock_choice, handlers, tmp_path, monkeypatch):
        """Escolhe JSON da lista de arquivos"""
        monkeypatch.chdir(tmp_path)
        handlers.menu.current_analysis = None
        # Criar JSON no diretório atual
        json_file = tmp_path / "data.json"
        json_file.write_text('{"key": "value"}')

        result = handlers._choose_data_file()
        assert result is not None
        assert result.endswith(".json")


class TestExecuteAnalysis:

    @patch("qualia.cli.interactive.handlers.run_qualia_command", return_value=(True, "resultado", ""))
    @patch("qualia.cli.interactive.handlers.show_file_preview")
    def test_success(self, mock_preview, mock_cmd, handlers, tmp_path):
        output = str(tmp_path / "out.json")
        handlers._execute_analysis("/tmp/test.txt", "word_frequency",
                                   {"min_word_length": "3"}, output)
        args = mock_cmd.call_args[0][0]
        assert "-P" in args
        assert "min_word_length=3" in args
        assert handlers.menu.current_analysis == output

    @patch("qualia.cli.interactive.handlers.run_qualia_command", return_value=(False, "", "falhou"))
    def test_failure(self, mock_cmd, handlers, tmp_path):
        output = str(tmp_path / "out.json")
        handlers._execute_analysis("/tmp/test.txt", "word_frequency", {}, output)
        # current_analysis não deve ser setado
        assert handlers.menu.current_analysis != output


class TestExecuteVisualization:

    @patch("qualia.cli.interactive.handlers.Confirm.ask", return_value=False)
    @patch("qualia.cli.interactive.handlers.run_qualia_command", return_value=(True, "viz ok", ""))
    def test_success(self, mock_cmd, mock_confirm, handlers, tmp_path):
        output = str(tmp_path / "chart.png")
        handlers._execute_visualization("/tmp/data.json", "wordcloud_viz",
                                        output, {"colormap": "viridis"})
        args = mock_cmd.call_args[0][0]
        assert "visualize" in args
        assert "-P" in args
        assert "colormap=viridis" in args

    @patch("qualia.cli.interactive.handlers.run_qualia_command", return_value=(False, "", "erro"))
    def test_failure(self, mock_cmd, handlers, tmp_path):
        output = str(tmp_path / "chart.png")
        handlers._execute_visualization("/tmp/data.json", "wordcloud_viz", output, {})


class TestExecutePipeline:

    @patch("qualia.cli.interactive.handlers.Prompt.ask", return_value="results/out")
    @patch("qualia.cli.interactive.handlers.choose_file", return_value="/tmp/test.txt")
    @patch("qualia.cli.interactive.handlers.run_qualia_command", return_value=(True, "pipeline ok", ""))
    def test_success(self, mock_cmd, mock_file, mock_prompt, handlers, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        pipeline = tmp_path / "pipe.yaml"
        pipeline.write_text("name: test")
        handlers._execute_pipeline(pipeline)
        handlers.menu.add_recent_file.assert_called_with("/tmp/test.txt")

    @patch("qualia.cli.interactive.handlers.choose_file", return_value=None)
    def test_no_file(self, mock_file, handlers, tmp_path):
        handlers._execute_pipeline(tmp_path / "pipe.yaml")
        handlers.menu.add_recent_file.assert_not_called()


class TestShowGeneratedFiles:

    def test_shows_files(self, handlers, tmp_path):
        (tmp_path / "a.json").write_text("{}")
        (tmp_path / "b.png").write_bytes(b"\x89PNG")
        # Não deve crashar
        handlers._show_generated_files(tmp_path)

    def test_empty_dir(self, handlers, tmp_path):
        handlers._show_generated_files(tmp_path)

    def test_nonexistent_dir(self, handlers, tmp_path):
        handlers._show_generated_files(tmp_path / "nope")


class TestOpenFile:

    @patch("subprocess.run")
    def test_open_darwin(self, mock_run, handlers):
        with patch.object(sys, 'platform', 'darwin'):
            handlers._open_file("/tmp/test.png")
            mock_run.assert_called_with(["open", "/tmp/test.png"])

    @patch("subprocess.run")
    def test_open_linux(self, mock_run, handlers):
        with patch.object(sys, 'platform', 'linux'):
            handlers._open_file("/tmp/test.png")
            mock_run.assert_called_with(["xdg-open", "/tmp/test.png"])

    @patch("subprocess.run")
    def test_open_windows(self, mock_run, handlers):
        with patch.object(sys, 'platform', 'win32'):
            handlers._open_file("/tmp/test.png")
            mock_run.assert_called_with(["start", "/tmp/test.png"], shell=True)


# =============================================================================
# MENU — estrutura e inicialização
# =============================================================================

class TestQualiaInteractiveMenu:

    def test_init(self):
        from qualia.cli.interactive.menu import QualiaInteractiveMenu
        menu = QualiaInteractiveMenu()
        assert menu.current_analysis is None
        assert menu.recent_files == []
        assert menu.handlers is not None

    def test_add_recent_file(self):
        from qualia.cli.interactive.menu import QualiaInteractiveMenu
        menu = QualiaInteractiveMenu()
        menu.add_recent_file("/tmp/a.txt")
        assert "/tmp/a.txt" in menu.recent_files

    def test_add_recent_file_no_duplicates(self):
        from qualia.cli.interactive.menu import QualiaInteractiveMenu
        menu = QualiaInteractiveMenu()
        menu.add_recent_file("/tmp/a.txt")
        menu.add_recent_file("/tmp/a.txt")
        assert menu.recent_files.count("/tmp/a.txt") == 1

    def test_add_recent_file_max_10(self):
        from qualia.cli.interactive.menu import QualiaInteractiveMenu
        menu = QualiaInteractiveMenu()
        for i in range(15):
            menu.add_recent_file(f"/tmp/file_{i}.txt")
        assert len(menu.recent_files) == 10
        # Deve manter os mais recentes
        assert "/tmp/file_14.txt" in menu.recent_files
        assert "/tmp/file_0.txt" not in menu.recent_files

    @patch("qualia.cli.interactive.menu.Prompt.ask", return_value="0")
    @patch("qualia.cli.interactive.menu.QualiaInteractiveMenu.show_banner")
    def test_run_exit(self, mock_banner, mock_prompt):
        """Menu sai imediatamente com opção 0"""
        from qualia.cli.interactive.menu import QualiaInteractiveMenu
        menu = QualiaInteractiveMenu()
        menu.run()


# =============================================================================
# WIZARDS
# =============================================================================

class TestPipelineWizard:

    def test_init(self):
        from qualia.cli.interactive.wizards import PipelineWizard
        wizard = PipelineWizard()
        assert wizard is not None

    @patch("qualia.cli.interactive.wizards.Confirm.ask")
    @patch("qualia.cli.interactive.wizards.Prompt.ask")
    @patch("qualia.cli.interactive.wizards.choose_plugin", return_value=None)
    def test_create_pipeline_no_steps(self, mock_plugin, mock_prompt, mock_confirm,
                                      tmp_path, monkeypatch):
        """Pipeline sem steps não é salvo"""
        from qualia.cli.interactive.wizards import PipelineWizard
        monkeypatch.chdir(tmp_path)
        mock_prompt.side_effect = ["test_pipeline", "descricao"]
        wizard = PipelineWizard()
        wizard.create_pipeline()
        # Não deve criar arquivo
        assert not (tmp_path / "configs" / "pipelines" / "test_pipeline.yaml").exists()

    @patch("qualia.cli.interactive.wizards.Confirm.ask")
    @patch("qualia.cli.interactive.wizards.Prompt.ask")
    @patch("qualia.cli.interactive.wizards.choose_plugin")
    @patch("qualia.cli.interactive.wizards.configure_parameters", return_value={})
    def test_create_pipeline_one_step(self, mock_params, mock_plugin, mock_prompt,
                                      mock_confirm, tmp_path, monkeypatch):
        """Pipeline com um step é salvo corretamente"""
        from qualia.cli.interactive.wizards import PipelineWizard
        monkeypatch.chdir(tmp_path)

        mock_plugin.side_effect = ["word_frequency", None]  # primeiro step, depois sai
        mock_prompt.side_effect = ["meu_pipeline", "descricao do pipeline"]
        # Confirm: save output? no, add desc? no, add more? -> sai por plugin=None
        # add metadata? no, view? no
        mock_confirm.side_effect = [False, False, True, False, False]

        wizard = PipelineWizard()
        wizard.create_pipeline()
        pipeline_file = tmp_path / "configs" / "pipelines" / "meu_pipeline.yaml"
        assert pipeline_file.exists()


class TestGetValidName:

    @patch("qualia.cli.interactive.wizards.Prompt.ask", return_value="My Pipeline")
    def test_sanitizes_name(self, mock_prompt, tmp_path, monkeypatch):
        from qualia.cli.interactive.wizards import PipelineWizard
        monkeypatch.chdir(tmp_path)
        wizard = PipelineWizard()
        name = wizard._get_valid_name()
        assert name == "my_pipeline"

    @patch("qualia.cli.interactive.wizards.Prompt.ask")
    @patch("qualia.cli.interactive.wizards.Confirm.ask", return_value=True)
    def test_overwrite_existing(self, mock_confirm, mock_prompt, tmp_path, monkeypatch):
        from qualia.cli.interactive.wizards import PipelineWizard
        monkeypatch.chdir(tmp_path)
        # Criar pipeline existente
        pipeline_dir = tmp_path / "configs" / "pipelines"
        pipeline_dir.mkdir(parents=True)
        (pipeline_dir / "existing.yaml").write_text("old")

        mock_prompt.return_value = "existing"
        wizard = PipelineWizard()
        name = wizard._get_valid_name()
        assert name == "existing"


class TestGetMetadata:

    @patch("qualia.cli.interactive.wizards.Confirm.ask", return_value=False)
    @patch("qualia.cli.interactive.wizards.Prompt.ask")
    def test_basic_metadata(self, mock_prompt, mock_confirm):
        from qualia.cli.interactive.wizards import PipelineWizard
        mock_prompt.side_effect = ["tag1, tag2", "Autor"]
        wizard = PipelineWizard()
        meta = wizard._get_metadata()
        assert meta["tags"] == ["tag1", "tag2"]
        assert meta["author"] == "Autor"

    @patch("qualia.cli.interactive.wizards.Confirm.ask", return_value=False)
    @patch("qualia.cli.interactive.wizards.Prompt.ask")
    def test_empty_metadata(self, mock_prompt, mock_confirm):
        from qualia.cli.interactive.wizards import PipelineWizard
        mock_prompt.side_effect = ["", ""]
        wizard = PipelineWizard()
        meta = wizard._get_metadata()
        assert "tags" not in meta
        assert "author" not in meta


class TestReportWizard:

    def test_create_report_placeholder(self):
        from qualia.cli.interactive.wizards import ReportWizard
        wizard = ReportWizard()
        wizard.create_report()  # Não deve crashar


class TestMethodologyWizard:

    def test_create_methodology_placeholder(self):
        from qualia.cli.interactive.wizards import MethodologyWizard
        wizard = MethodologyWizard()
        wizard.create_methodology()  # Não deve crashar


# =============================================================================
# START_MENU (entry point)
# =============================================================================

class TestStartMenu:

    @patch("qualia.cli.interactive.QualiaInteractiveMenu")
    def test_keyboard_interrupt(self, mock_menu_cls):
        """Ctrl+C é tratado graciosamente"""
        from qualia.cli.interactive import start_menu
        mock_menu_cls.return_value.run.side_effect = KeyboardInterrupt
        start_menu()  # Não deve levantar exceção

    @patch("qualia.cli.interactive.QualiaInteractiveMenu")
    def test_normal_exit(self, mock_menu_cls):
        """Saída normal funciona"""
        from qualia.cli.interactive import start_menu
        start_menu()
        mock_menu_cls.return_value.run.assert_called_once()

    @patch("qualia.cli.interactive.QualiaInteractiveMenu")
    def test_exception_propagates(self, mock_menu_cls):
        """Exceções são re-levantadas após logging"""
        from qualia.cli.interactive import start_menu
        mock_menu_cls.return_value.run.side_effect = RuntimeError("boom")
        with pytest.raises(RuntimeError, match="boom"):
            start_menu()
