# plugins/transcription/__init__.py
"""
Plugin de transcrição de áudio/vídeo usando Groq Whisper API.

Recebe arquivo de áudio/vídeo, transcreve via Groq e devolve texto.
Migrado do projeto WhatsApp (wrangling.py → transcribe_media_groq).

Exemplo de uso via API:
    curl -X POST http://localhost:8000/transcribe/transcription \
      -F "file=@audio.opus" \
      -F 'config={"language": "pt"}'

Requer:
    - pip install groq
    - GROQ_API_KEY no ambiente
"""

import os
from pathlib import Path
from typing import Dict, Any, Tuple, Optional

from qualia.core import BaseDocumentPlugin, PluginMetadata, PluginType, Document

# Importação guarded — plugin funciona sem groq instalado
try:
    from groq import Groq
    HAS_GROQ = True
except ImportError:
    Groq = None
    HAS_GROQ = False


# Limite da Groq API
MAX_FILE_SIZE_MB = 25
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

SUPPORTED_FORMATS = [
    "mp3", "mp4", "mpeg", "mpga", "m4a", "wav", "webm", "ogg", "opus", "flac"
]


class TranscriptionPlugin(BaseDocumentPlugin):
    """Transcreve áudio/vídeo usando Groq Whisper API."""

    def meta(self) -> PluginMetadata:
        return PluginMetadata(
            id="transcription",
            type=PluginType.DOCUMENT,
            name="Audio/Video Transcription",
            description="Transcreve arquivos de áudio e vídeo usando Groq Whisper API",
            version="0.1.0",
            provides=["transcription", "language", "duration"],
            requires=[],
            parameters={
                "language": {
                    "type": "str",
                    "description": "Idioma do áudio (auto para detecção automática)",
                    "default": "auto",
                    "options": ["auto", "pt", "en", "es"],
                },
                "model": {
                    "type": "str",
                    "description": "Modelo Whisper a usar",
                    "default": "whisper-large-v3",
                    "options": [
                        "whisper-large-v3",
                        "whisper-large-v3-turbo",
                        "distil-whisper-large-v3-en",
                    ],
                },
                "temperature": {
                    "type": "float",
                    "description": "Temperatura de sampling (0.0 = determinístico)",
                    "default": 0.0,
                    "range": [0.0, 1.0],
                },
            },
        )

    def _process_impl(
        self, document: Document, config: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Transcreve o arquivo referenciado em document.metadata['file_path']."""

        file_path = document.metadata.get("file_path")
        if not file_path:
            return {
                "transcription": None,
                "status": "error",
                "language": None,
                "duration": None,
                "error": "Nenhum arquivo fornecido. Use o endpoint /transcribe com upload de arquivo.",
            }

        file_path = Path(file_path)

        # Validar que arquivo existe
        if not file_path.exists():
            return {
                "transcription": None,
                "status": "error",
                "language": None,
                "duration": None,
                "error": f"Arquivo não encontrado: {file_path}",
            }

        # Validar tamanho
        file_size = file_path.stat().st_size
        if file_size > MAX_FILE_SIZE_BYTES:
            size_mb = file_size / (1024 * 1024)
            return {
                "transcription": None,
                "status": "error",
                "language": None,
                "duration": None,
                "error": (
                    f"Arquivo muito grande: {size_mb:.1f}MB. "
                    f"Limite da Groq API: {MAX_FILE_SIZE_MB}MB."
                ),
            }

        # Verificar dependência groq
        if not HAS_GROQ:
            return {
                "transcription": None,
                "status": "error",
                "language": None,
                "duration": None,
                "error": "Groq não instalado. Execute: pip install groq",
            }

        # Verificar API key
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            return {
                "transcription": None,
                "status": "error",
                "language": None,
                "duration": None,
                "error": "GROQ_API_KEY não configurada no ambiente.",
            }

        # Montar kwargs da API
        model = config.get("model", "whisper-large-v3")
        temperature = config.get("temperature", 0.0)
        language = config.get("language", "auto")

        api_kwargs = {
            "model": model,
            "response_format": "verbose_json",
            "temperature": temperature,
        }
        if language != "auto":
            api_kwargs["language"] = language

        # Chamar Groq API
        try:
            client = Groq(api_key=api_key)

            with open(file_path, "rb") as audio_file:
                transcription = client.audio.transcriptions.create(
                    file=(file_path.name, audio_file.read()),
                    **api_kwargs,
                )

            return {
                "transcription": transcription.text,
                "status": "completed",
                "language": getattr(transcription, "language", "unknown"),
                "duration": getattr(transcription, "duration", None),
                "error": None,
            }

        except Exception as e:
            return {
                "transcription": None,
                "status": "error",
                "language": None,
                "duration": None,
                "error": f"Erro na transcrição: {str(e)}",
            }
