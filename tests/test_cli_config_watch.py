"""
Testes dos comandos CLI config e watch do Qualia.

Cobre config validate, config list, config create (interativo),
e watch (validacao de argumentos + QualiaFileHandler).
"""

import pytest
import json
import yaml
from pathlib import Path
from unittest.mock import patch, MagicMock
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
    """Cria arquivo de texto temporario"""
    f = tmp_path / "sample.txt"
    f.write_text("O gato sentou no tapete. O gato e bonito. O tapete e macio.")
    return f


@pytest.fixture
def valid_plugin_config_yaml(tmp_path):
    """Config valida em YAML"""
    config = {"min_word_length": 3, "max_words": 50}
    f = tmp_path / "config.yaml"
    f.write_text(yaml.dump(config))
    return f


@pytest.fixture
def valid_plugin_config_json(tmp_path):
    """Config valida em JSON"""
    config = {"min_word_length": 4, "max_words": 100}
    f = tmp_path / "config.json"
    f.write_text(json.dumps(config))
    return f


@pytest.fixture
def invalid_yaml(tmp_path):
    """YAML com sintaxe quebrada"""
    f = tmp_path / "bad.yaml"
    f.write_text(": : : not valid yaml [[[")
    return f


@pytest.fixture
def invalid_json(tmp_path):
    """JSON com sintaxe quebrada"""
    f = tmp_path / "bad.json"
    f.write_text("{invalid json here!!!")
    return f


@pytest.fixture
def pipeline_config_valid(tmp_path):
    """Pipeline config com plugin real"""
    config = {
        "name": "pipeline_teste",
        "steps": [
            {"plugin": "word_frequency", "config": {"min_word_length": 2}},
        ],
    }
    f = tmp_path / "pipeline.yaml"
    f.write_text(yaml.dump(config))
    return f


@pytest.fixture
def pipeline_config_missing_name(tmp_path):
    """Pipeline sem campo name"""
    config = {
        "steps": [
            {"plugin": "word_frequency"},
        ],
    }
    f = tmp_path / "pipeline_no_name.yaml"
    f.write_text(yaml.dump(config))
    return f


@pytest.fixture
def pipeline_config_invalid_plugin(tmp_path):
    """Pipeline com plugin inexistente"""
    config = {
        "name": "pipeline_ruim",
        "steps": [
            {"plugin": "plugin_que_nao_existe"},
        ],
    }
    f = tmp_path / "pipeline_bad_plugin.yaml"
    f.write_text(yaml.dump(config))
    return f


@pytest.fixture
def pipeline_config_missing_plugin_in_step(tmp_path):
    """Pipeline com step sem campo plugin"""
    config = {
        "name": "pipeline_sem_plugin",
        "steps": [
            {"config": {"min_word_length": 2}},
        ],
    }
    f = tmp_path / "pipeline_no_plugin.yaml"
    f.write_text(yaml.dump(config))
    return f


@pytest.fixture
def configs_dir_with_files(tmp_path, monkeypatch):
    """Cria diretorio configs/ com arquivos dentro e muda cwd"""
    configs = tmp_path / "configs"
    configs.mkdir()

    # Config de plugin
    plugin_cfg = {"min_word_length": 3}
    (configs / "word_freq.yaml").write_text(yaml.dump(plugin_cfg))

    # Config de pipeline
    pipeline_cfg = {
        "name": "meu_pipeline",
        "steps": [{"plugin": "word_frequency"}],
    }
    (configs / "pipeline.yaml").write_text(yaml.dump(pipeline_cfg))

    # JSON tambem
    (configs / "outro.json").write_text(json.dumps({"top_n": 10}))

    monkeypatch.chdir(tmp_path)
    return configs


@pytest.fixture
def configs_dir_empty(tmp_path, monkeypatch):
    """Cria diretorio configs/ vazio e muda cwd"""
    configs = tmp_path / "configs"
    configs.mkdir()
    monkeypatch.chdir(tmp_path)
    return configs


@pytest.fixture
def no_configs_dir(tmp_path, monkeypatch):
    """Cwd sem diretorio configs/"""
    monkeypatch.chdir(tmp_path)
    return tmp_path


# =============================================================================
# CONFIG VALIDATE
# =============================================================================

class TestConfigValidate:

    def test_validate_valid_yaml(self, runner, valid_plugin_config_yaml):
        result = runner.invoke(cli, ["config", "validate", str(valid_plugin_config_yaml)])
        assert result.exit_code == 0
        assert "válido" in result.output.lower() or "valid" in result.output.lower()

    def test_validate_valid_json(self, runner, valid_plugin_config_json):
        result = runner.invoke(cli, ["config", "validate", str(valid_plugin_config_json)])
        assert result.exit_code == 0
        assert "válido" in result.output.lower() or "valid" in result.output.lower()

    def test_validate_invalid_yaml(self, runner, invalid_yaml):
        result = runner.invoke(cli, ["config", "validate", str(invalid_yaml)])
        # Deve reportar erro de parsing
        output_lower = result.output.lower()
        assert ("inválido" in output_lower or "invalid" in output_lower
                or "erro" in output_lower or result.exit_code != 0)

    def test_validate_invalid_json(self, runner, invalid_json):
        result = runner.invoke(cli, ["config", "validate", str(invalid_json)])
        output_lower = result.output.lower()
        assert ("inválido" in output_lower or "invalid" in output_lower
                or "erro" in output_lower or result.exit_code != 0)

    def test_validate_pipeline_valid(self, runner, pipeline_config_valid):
        """Pipeline com plugin real deve validar OK"""
        result = runner.invoke(cli, ["config", "validate", str(pipeline_config_valid)])
        assert result.exit_code == 0
        assert "Pipeline" in result.output or "pipeline" in result.output.lower()
        # word_frequency existe, entao step deve passar
        assert "word_frequency" in result.output.lower() or "Step 1" in result.output

    def test_validate_pipeline_missing_name(self, runner, pipeline_config_missing_name):
        """Pipeline sem name deve avisar"""
        result = runner.invoke(cli, ["config", "validate", str(pipeline_config_missing_name)])
        assert result.exit_code == 0
        # Deve conter aviso sobre name ausente
        assert "name" in result.output.lower()

    def test_validate_pipeline_invalid_plugin(self, runner, pipeline_config_invalid_plugin):
        """Pipeline com plugin inexistente deve reportar erro"""
        result = runner.invoke(cli, ["config", "validate", str(pipeline_config_invalid_plugin)])
        assert result.exit_code == 0
        assert "não encontrado" in result.output or "not found" in result.output.lower()

    def test_validate_pipeline_missing_plugin_in_step(self, runner, pipeline_config_missing_plugin_in_step):
        """Pipeline com step sem campo plugin deve avisar"""
        result = runner.invoke(cli, ["config", "validate", str(pipeline_config_missing_plugin_in_step)])
        assert result.exit_code == 0
        assert "não especificado" in result.output or "especificado" in result.output.lower()

    def test_validate_nonexistent_file(self, runner):
        """Arquivo que nao existe — Click valida exists=True"""
        result = runner.invoke(cli, ["config", "validate", "/nonexistent/file.yaml"])
        assert result.exit_code != 0

    def test_validate_empty_yaml(self, tmp_path, runner):
        """YAML vazio (None) nao deve crashar"""
        f = tmp_path / "empty.yaml"
        f.write_text("")
        result = runner.invoke(cli, ["config", "validate", str(f)])
        # Pode ser valido (yaml.safe_load retorna None) ou reportar algo
        # O importante e nao crashar
        assert result.exit_code == 0 or "inválido" in result.output.lower()


# =============================================================================
# CONFIG LIST
# =============================================================================

class TestConfigList:

    def test_list_no_configs_dir(self, runner, no_configs_dir):
        """Sem diretorio configs/ deve avisar"""
        result = runner.invoke(cli, ["config", "list"])
        assert result.exit_code == 0
        assert "não encontrado" in result.output or "encontrado" in result.output.lower()

    def test_list_empty_configs_dir(self, runner, configs_dir_empty):
        """Diretorio configs/ vazio deve avisar"""
        result = runner.invoke(cli, ["config", "list"])
        assert result.exit_code == 0
        assert "nenhuma" in result.output.lower() or "encontrad" in result.output.lower()

    def test_list_with_files(self, runner, configs_dir_with_files):
        """Deve listar configs de plugin e pipeline"""
        result = runner.invoke(cli, ["config", "list"])
        assert result.exit_code == 0
        # Deve mostrar os arquivos
        assert "word_freq" in result.output or "pipeline" in result.output
        # Pipeline deve mostrar nome e steps
        assert "meu_pipeline" in result.output or "Pipeline" in result.output


# =============================================================================
# CONFIG CREATE (interativo)
# =============================================================================

class TestConfigCreate:

    def test_create_with_known_plugin(self, runner, tmp_path):
        """Cria config para word_frequency com defaults, sem pipeline, salvando"""
        output_file = tmp_path / "wf_config.yaml"
        # Simula input: aceitar defaults para cada parametro (Enter para cada),
        # nao criar pipeline (n), confirmar salvamento (y)
        # word_frequency tem parametros, entao mandamos Enter para cada um + n (no pipeline) + y (salvar)
        user_input = "\n" * 20 + "n\ny\n"
        result = runner.invoke(cli, [
            "config", "create", "-p", "word_frequency", "-o", str(output_file),
        ], input=user_input)
        assert result.exit_code == 0
        assert "Configurando" in result.output or "Preview" in result.output

    def test_create_with_invalid_plugin(self, runner):
        """Plugin inexistente deve avisar"""
        result = runner.invoke(cli, [
            "config", "create", "-p", "plugin_fantasma",
        ], input="\n")
        assert result.exit_code == 0
        assert "não encontrado" in result.output

    def test_create_json_format(self, runner, tmp_path):
        """Cria config em JSON"""
        output_file = tmp_path / "config.json"
        user_input = "\n" * 20 + "n\ny\n"
        result = runner.invoke(cli, [
            "config", "create", "-p", "word_frequency",
            "-f", "json", "-o", str(output_file),
        ], input=user_input)
        assert result.exit_code == 0

    def test_create_pipeline_mode(self, runner, tmp_path):
        """Cria pipeline config: aceita defaults, sim para pipeline, nao para mais steps, salvar"""
        output_file = tmp_path / "pipe.yaml"
        # Inputs: defaults para params + y (criar pipeline) + Enter (nome default) + n (mais steps) + y (salvar)
        user_input = "\n" * 20 + "y\n\nn\ny\n"
        result = runner.invoke(cli, [
            "config", "create", "-p", "word_frequency", "-o", str(output_file),
        ], input=user_input)
        assert result.exit_code == 0

    def test_create_cancel_save(self, runner, tmp_path):
        """Cancelar salvamento nao deve criar arquivo"""
        output_file = tmp_path / "nao_salva.yaml"
        # 8 params (Enter para defaults) + n (sem pipeline) + n (nao salvar)
        user_input = "\n" * 8 + "n\nn\n"
        result = runner.invoke(cli, [
            "config", "create", "-p", "word_frequency", "-o", str(output_file),
        ], input=user_input)
        assert result.exit_code == 0
        assert "não salva" in result.output.lower() or not output_file.exists()

    def test_create_choose_plugin_interactively(self, runner, tmp_path):
        """Sem -p, deve listar plugins e permitir escolher por numero"""
        output_file = tmp_path / "chosen.yaml"
        # Input: escolher plugin 1 + defaults + nao pipeline + salvar
        user_input = "1\n" + "\n" * 20 + "n\ny\n"
        result = runner.invoke(cli, [
            "config", "create", "-o", str(output_file),
        ], input=user_input)
        assert result.exit_code == 0
        assert "Plugins disponíveis" in result.output or "disponíveis" in result.output.lower() or "disponveis" in result.output


# =============================================================================
# WATCH — validacao de argumentos
# =============================================================================

class TestWatchCommand:

    def test_watch_nonexistent_folder(self, runner):
        """Pasta inexistente — Click valida exists=True"""
        result = runner.invoke(cli, [
            "watch", "/pasta/que/nao/existe", "-p", "word_frequency",
        ])
        assert result.exit_code != 0

    def test_watch_invalid_plugin(self, runner, tmp_path):
        """Plugin inexistente deve retornar exit code 1"""
        result = runner.invoke(cli, [
            "watch", str(tmp_path), "-p", "plugin_fantasma",
        ])
        assert result.exit_code == 1
        assert "não encontrado" in result.output

    def test_watch_missing_plugin_option(self, runner, tmp_path):
        """Sem --plugin deve dar erro (required=True)"""
        result = runner.invoke(cli, ["watch", str(tmp_path)])
        assert result.exit_code != 0

    def test_watch_file_instead_of_folder(self, runner, tmp_path):
        """Arquivo ao inves de pasta — Click valida file_okay=False"""
        f = tmp_path / "arquivo.txt"
        f.write_text("conteudo")
        result = runner.invoke(cli, [
            "watch", str(f), "-p", "word_frequency",
        ])
        assert result.exit_code != 0


# =============================================================================
# WATCH — QualiaFileHandler direto
# =============================================================================

class TestQualiaFileHandler:

    def test_handler_pattern_matching_txt(self, tmp_path):
        """Handler deve processar arquivos que casam com o padrao"""
        from qualia.cli.commands.watch import QualiaFileHandler

        handler = QualiaFileHandler(
            plugin_id="word_frequency",
            config={},
            output_dir=tmp_path / "output",
            pattern="*.txt",
        )
        (tmp_path / "output").mkdir(exist_ok=True)

        # Arquivo que casa com padrao
        txt_file = tmp_path / "documento.txt"
        txt_file.write_text("Texto de teste com palavras repetidas. Palavras sao boas.")

        handler._process_file(str(txt_file))
        assert handler.stats["processed"] == 1
        assert handler.stats["errors"] == 0

        # Verificar que resultado foi salvo
        result_file = tmp_path / "output" / "documento_result.json"
        assert result_file.exists()
        data = json.loads(result_file.read_text())
        assert isinstance(data, dict)

    def test_handler_pattern_no_match(self, tmp_path):
        """Arquivo que nao casa com padrao deve ser ignorado"""
        from qualia.cli.commands.watch import QualiaFileHandler

        handler = QualiaFileHandler(
            plugin_id="word_frequency",
            config={},
            pattern="*.txt",
        )

        # Arquivo .md nao casa com *.txt
        md_file = tmp_path / "readme.md"
        md_file.write_text("# Titulo")

        handler._process_file(str(md_file))
        assert handler.stats["processed"] == 0

    def test_handler_pattern_md(self, tmp_path):
        """Handler com padrao *.md deve processar .md"""
        from qualia.cli.commands.watch import QualiaFileHandler

        handler = QualiaFileHandler(
            plugin_id="word_frequency",
            config={},
            pattern="*.md",
        )

        md_file = tmp_path / "notas.md"
        md_file.write_text("Notas importantes sobre o projeto de pesquisa qualitativa.")

        handler._process_file(str(md_file))
        assert handler.stats["processed"] == 1

    def test_handler_without_output_dir(self, tmp_path):
        """Sem output_dir nao deve salvar arquivo mas deve processar"""
        from qualia.cli.commands.watch import QualiaFileHandler

        handler = QualiaFileHandler(
            plugin_id="word_frequency",
            config={},
            output_dir=None,
            pattern="*.txt",
        )

        txt_file = tmp_path / "teste.txt"
        txt_file.write_text("Conteudo simples para testar processamento.")

        handler._process_file(str(txt_file))
        assert handler.stats["processed"] == 1
        # Nenhum arquivo de resultado deve existir em tmp_path
        result_files = list(tmp_path.glob("*_result.json"))
        assert len(result_files) == 0

    def test_handler_tracks_processed_files(self, tmp_path):
        """Deve adicionar arquivo ao set de processed_files"""
        from qualia.cli.commands.watch import QualiaFileHandler

        handler = QualiaFileHandler(
            plugin_id="word_frequency",
            config={},
            pattern="*.txt",
        )

        txt_file = tmp_path / "rastreado.txt"
        txt_file.write_text("Arquivo para rastreamento de processamento.")

        handler._process_file(str(txt_file))
        assert txt_file in handler.processed_files

    def test_handler_binary_file_latin1_fallback(self, tmp_path):
        """Arquivo binario é lido via fallback latin-1 (não falha no encoding)"""
        from qualia.cli.commands.watch import QualiaFileHandler

        handler = QualiaFileHandler(
            plugin_id="word_frequency",
            config={},
            pattern="*.bin",
        )

        bin_file = tmp_path / "dados.bin"
        bin_file.write_bytes(b"\x80\x81\x82\x83\xff\xfe")

        handler._process_file(str(bin_file))
        # latin-1 fallback lê sem erro de encoding; processamento pode passar ou falhar
        assert handler.stats["errors"] + handler.stats["processed"] == 1

    def test_handler_empty_file(self, tmp_path):
        """Arquivo vazio deve ser processado sem crash"""
        from qualia.cli.commands.watch import QualiaFileHandler

        handler = QualiaFileHandler(
            plugin_id="word_frequency",
            config={},
            pattern="*.txt",
        )

        empty_file = tmp_path / "vazio.txt"
        empty_file.write_text("")

        # Nao deve crashar — pode processar ou dar erro, mas nao exception nao tratada
        handler._process_file(str(empty_file))
        total = handler.stats["processed"] + handler.stats["errors"]
        assert total == 1

    def test_handler_with_config_params(self, tmp_path):
        """Handler deve respeitar config passada"""
        from qualia.cli.commands.watch import QualiaFileHandler

        handler = QualiaFileHandler(
            plugin_id="word_frequency",
            config={"min_word_length": 5},
            output_dir=tmp_path / "out",
            pattern="*.txt",
        )
        (tmp_path / "out").mkdir()

        txt_file = tmp_path / "texto.txt"
        txt_file.write_text("A gata dormiu no sofazinho confortavelmente durante a madrugada.")

        handler._process_file(str(txt_file))
        assert handler.stats["processed"] == 1

        result_file = tmp_path / "out" / "texto_result.json"
        assert result_file.exists()
        data = json.loads(result_file.read_text())
        # Com min_word_length=5, palavras curtas (a, no) nao devem aparecer
        if "word_frequencies" in data:
            for word in data["word_frequencies"]:
                assert len(word) >= 5

    def test_handler_on_created_event(self, tmp_path):
        """on_created deve chamar _process_file para arquivos"""
        from qualia.cli.commands.watch import QualiaFileHandler
        from watchdog.events import FileCreatedEvent

        handler = QualiaFileHandler(
            plugin_id="word_frequency",
            config={},
            pattern="*.txt",
        )

        txt_file = tmp_path / "criado.txt"
        txt_file.write_text("Arquivo novo criado para teste.")

        event = FileCreatedEvent(str(txt_file))
        handler.on_created(event)
        assert handler.stats["processed"] == 1

    def test_handler_on_created_ignores_directories(self, tmp_path):
        """on_created nao deve processar diretorios"""
        from qualia.cli.commands.watch import QualiaFileHandler
        from watchdog.events import DirCreatedEvent

        handler = QualiaFileHandler(
            plugin_id="word_frequency",
            config={},
            pattern="*.txt",
        )

        event = DirCreatedEvent(str(tmp_path / "nova_pasta"))
        handler.on_created(event)
        assert handler.stats["processed"] == 0
