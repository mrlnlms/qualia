# tests/test_transcription.py
"""
Testes para o plugin de transcrição de áudio/vídeo.

Todos os testes são mockados — não chamam a API real do Groq.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from plugins.transcription import TranscriptionPlugin, MAX_FILE_SIZE_BYTES
from qualia.core import Document, PluginType


@pytest.fixture
def plugin():
    return TranscriptionPlugin()


@pytest.fixture
def temp_audio():
    """Cria arquivo temporário simulando um áudio."""
    with tempfile.NamedTemporaryFile(suffix=".opus", delete=False) as f:
        f.write(b"\x00" * 1024)  # 1KB fake audio
        path = f.name
    yield path
    Path(path).unlink(missing_ok=True)


@pytest.fixture
def doc_with_file(temp_audio):
    """Document com file_path no metadata."""
    doc = Document(id="test_audio", content="")
    doc.metadata["file_path"] = temp_audio
    return doc


# ============================================================================
# meta() — Schema
# ============================================================================

class TestMeta:
    def test_meta_id(self, plugin):
        assert plugin.meta().id == "transcription"

    def test_meta_type(self, plugin):
        assert plugin.meta().type == PluginType.DOCUMENT

    def test_meta_provides(self, plugin):
        provides = plugin.meta().provides
        assert "transcription" in provides
        assert "language" in provides
        assert "duration" in provides

    def test_meta_parameters(self, plugin):
        params = plugin.meta().parameters
        assert "language" in params
        assert "model" in params
        assert "temperature" in params

    def test_language_options(self, plugin):
        lang = plugin.meta().parameters["language"]
        assert lang["default"] == "auto"
        assert "pt" in lang["options"]
        assert "en" in lang["options"]

    def test_model_options(self, plugin):
        model = plugin.meta().parameters["model"]
        assert model["default"] == "whisper-large-v3"
        assert "whisper-large-v3-turbo" in model["options"]

    def test_temperature_range(self, plugin):
        temp = plugin.meta().parameters["temperature"]
        assert temp["default"] == 0.0
        assert temp["range"] == [0.0, 1.0]


# ============================================================================
# Validações de entrada
# ============================================================================

class TestValidation:
    def test_no_file_path(self, plugin):
        """Sem file_path no metadata → erro descritivo."""
        doc = Document(id="no_file", content="")
        result = plugin._process_impl(doc, {}, {})
        assert result["status"] == "error"
        assert "arquivo" in result["error"].lower() or "file" in result["error"].lower()

    def test_file_not_found(self, plugin):
        """Arquivo não existe → erro descritivo."""
        doc = Document(id="missing", content="")
        doc.metadata["file_path"] = "/tmp/inexistente_abc123.opus"
        result = plugin._process_impl(doc, {}, {})
        assert result["status"] == "error"
        assert "não encontrado" in result["error"].lower() or "not found" in result["error"].lower()

    def test_file_too_large(self, plugin, tmp_path):
        """Arquivo > 25MB → erro descritivo."""
        big_file = tmp_path / "big.mp3"
        big_file.write_bytes(b"\x00" * (MAX_FILE_SIZE_BYTES + 1))

        doc = Document(id="big", content="")
        doc.metadata["file_path"] = str(big_file)
        result = plugin._process_impl(doc, {}, {})
        assert result["status"] == "error"
        assert "25" in result["error"]


# ============================================================================
# Dependências — groq não instalado / API key ausente
# ============================================================================

class TestDependencies:
    def test_groq_not_installed(self, plugin, doc_with_file):
        """groq não instalado → erro descritivo."""
        import plugins.transcription as mod
        original = mod.HAS_GROQ
        try:
            mod.HAS_GROQ = False
            result = plugin._process_impl(doc_with_file, {}, {})
            assert result["status"] == "error"
            assert "groq" in result["error"].lower()
        finally:
            mod.HAS_GROQ = original

    @patch.dict(os.environ, {}, clear=False)
    def test_no_api_key(self, plugin, doc_with_file):
        """GROQ_API_KEY não definida → erro descritivo."""
        import plugins.transcription as mod
        original = mod.HAS_GROQ
        try:
            mod.HAS_GROQ = True
            os.environ.pop("GROQ_API_KEY", None)
            result = plugin._process_impl(doc_with_file, {}, {})
            assert result["status"] == "error"
            assert "GROQ_API_KEY" in result["error"]
        finally:
            mod.HAS_GROQ = original


# ============================================================================
# Transcrição com sucesso (mockada)
# ============================================================================

class TestTranscription:
    """Testes com Groq mockado (não requer pip install groq)."""

    @pytest.fixture(autouse=True)
    def _enable_groq(self):
        """Habilita HAS_GROQ e injeta mock Groq no módulo para todos os testes desta classe."""
        import plugins.transcription as mod
        original_has = mod.HAS_GROQ
        original_groq = mod.Groq
        mod.HAS_GROQ = True
        mod.Groq = MagicMock  # placeholder, cada teste sobrescreve com seu mock
        yield
        mod.HAS_GROQ = original_has
        mod.Groq = original_groq

    @patch.dict(os.environ, {"GROQ_API_KEY": "test-key-123"}, clear=False)
    def test_successful_transcription(self, plugin, doc_with_file):
        """Transcrição com sucesso retorna texto e metadados."""
        import plugins.transcription as mod

        mock_result = MagicMock()
        mock_result.text = "Olá, isto é um teste de transcrição."
        mock_result.language = "pt"
        mock_result.duration = 5.2

        mock_client = MagicMock()
        mock_client.audio.transcriptions.create.return_value = mock_result
        mod.Groq = MagicMock(return_value=mock_client)

        result = plugin._process_impl(doc_with_file, {
            "language": "pt",
            "model": "whisper-large-v3",
            "temperature": 0.0,
        }, {})

        assert result["status"] == "completed"
        assert result["transcription"] == "Olá, isto é um teste de transcrição."
        assert result["language"] == "pt"
        assert result["duration"] == 5.2
        assert result["error"] is None

    @patch.dict(os.environ, {"GROQ_API_KEY": "test-key-123"}, clear=False)
    def test_auto_language(self, plugin, doc_with_file):
        """language=auto não passa language pra API."""
        import plugins.transcription as mod

        mock_result = MagicMock()
        mock_result.text = "Hello world"
        mock_result.language = "en"
        mock_result.duration = 2.0

        mock_client = MagicMock()
        mock_client.audio.transcriptions.create.return_value = mock_result
        mod.Groq = MagicMock(return_value=mock_client)

        result = plugin._process_impl(doc_with_file, {
            "language": "auto",
        }, {})

        # Verifica que language NÃO foi passado na chamada
        call_kwargs = mock_client.audio.transcriptions.create.call_args
        assert "language" not in call_kwargs.kwargs

    @patch.dict(os.environ, {"GROQ_API_KEY": "test-key-123"}, clear=False)
    def test_api_error(self, plugin, doc_with_file):
        """Erro da API Groq → status error com mensagem."""
        import plugins.transcription as mod

        mock_client = MagicMock()
        mock_client.audio.transcriptions.create.side_effect = Exception("Rate limit exceeded")
        mod.Groq = MagicMock(return_value=mock_client)

        result = plugin._process_impl(doc_with_file, {}, {})

        assert result["status"] == "error"
        assert "Rate limit" in result["error"]
        assert result["transcription"] is None


# ============================================================================
# Integração com ConfigurationRegistry
# ============================================================================

class TestConfigIntegration:
    def test_plugin_loads_in_core(self):
        """Plugin é descoberto pelo QualiaCore."""
        from qualia.core import QualiaCore
        core = QualiaCore()
        core.discover_plugins()
        assert "transcription" in core.plugins

    def test_registry_has_schema(self):
        """ConfigurationRegistry normaliza o schema do plugin."""
        from qualia.core import QualiaCore
        core = QualiaCore()
        core.discover_plugins()
        registry = core.get_config_registry()
        schema = registry.get_plugin_schema("transcription")
        assert schema is not None
        assert "language" in schema["parameters"]
