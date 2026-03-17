"""
Testes dos webhooks do Qualia.

Cobre WebhookProcessor, GenericWebhookProcessor e endpoints.

Nota: analyze_text() em webhooks.py chama core.execute_plugin()
diretamente (sem asyncio.to_thread), diferente dos endpoints
principais da API. Inconsistência documentada, não corrigida aqui.
"""

import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch

from fastapi import HTTPException
from qualia.api.webhooks import (
    WebhookProcessor,
    WebhookType,
    GenericWebhookProcessor,
    processors,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def generic_processor():
    """Processador genérico limpo para cada teste"""
    proc = GenericWebhookProcessor()
    proc.stats = {
        "total_received": 0,
        "total_processed": 0,
        "total_errors": 0,
        "last_processed": None,
    }
    return proc


@pytest.fixture
def mock_core(monkeypatch):
    """Mock do core injetado no módulo webhooks"""
    import qualia.api.webhooks as wh_module

    fake_core = MagicMock()
    fake_doc = MagicMock()
    fake_core.add_document.return_value = fake_doc
    fake_core.execute_plugin.return_value = {
        "word_frequencies": {"teste": 3},
        "total_words": 5,
    }
    monkeypatch.setattr(wh_module, "core", fake_core)
    monkeypatch.setattr(wh_module, "track_webhook_callback", None)
    return fake_core


# =============================================================================
# GENERIC WEBHOOK PROCESSOR — UNIT
# =============================================================================

class TestGenericExtractText:
    """Testa extração de texto de diferentes formatos de payload"""

    def test_extract_text_field(self, generic_processor):
        payload = {"text": "Olá mundo"}
        result = asyncio.get_event_loop().run_until_complete(
            generic_processor.extract_text(payload)
        )
        assert result == "Olá mundo"

    def test_extract_content_field(self, generic_processor):
        payload = {"content": "Conteúdo aqui"}
        result = asyncio.get_event_loop().run_until_complete(
            generic_processor.extract_text(payload)
        )
        assert result == "Conteúdo aqui"

    def test_extract_message_field(self, generic_processor):
        payload = {"message": "Mensagem recebida"}
        result = asyncio.get_event_loop().run_until_complete(
            generic_processor.extract_text(payload)
        )
        assert result == "Mensagem recebida"

    def test_extract_nested_body_text(self, generic_processor):
        payload = {"body": {"text": "Texto aninhado"}}
        result = asyncio.get_event_loop().run_until_complete(
            generic_processor.extract_text(payload)
        )
        assert result == "Texto aninhado"

    def test_extract_returns_none_for_unknown(self, generic_processor):
        payload = {"unknown_field": 42, "other": [1, 2, 3]}
        result = asyncio.get_event_loop().run_until_complete(
            generic_processor.extract_text(payload)
        )
        assert result is None

    def test_extract_empty_payload(self, generic_processor):
        result = asyncio.get_event_loop().run_until_complete(
            generic_processor.extract_text({})
        )
        assert result is None


class TestGenericDeterminePlugin:

    def test_default_plugin(self, generic_processor):
        result = asyncio.get_event_loop().run_until_complete(
            generic_processor.determine_plugin({})
        )
        assert result == "word_frequency"

    def test_custom_plugin(self, generic_processor):
        result = asyncio.get_event_loop().run_until_complete(
            generic_processor.determine_plugin({"plugin": "sentiment_analyzer"})
        )
        assert result == "sentiment_analyzer"


# =============================================================================
# WEBHOOK PROCESSOR — STATS
# =============================================================================

class TestWebhookStats:

    def test_process_increments_received(self, generic_processor, mock_core):
        asyncio.get_event_loop().run_until_complete(
            generic_processor.process({"text": "teste"}, {})
        )
        assert generic_processor.stats["total_received"] == 1

    def test_process_increments_processed_on_success(self, generic_processor, mock_core):
        asyncio.get_event_loop().run_until_complete(
            generic_processor.process({"text": "teste"}, {})
        )
        assert generic_processor.stats["total_processed"] == 1

    def test_process_increments_errors_on_failure(self, generic_processor, mock_core):
        mock_core.execute_plugin.side_effect = Exception("boom")
        with pytest.raises(Exception):
            asyncio.get_event_loop().run_until_complete(
                generic_processor.process({"text": "teste"}, {})
            )
        assert generic_processor.stats["total_errors"] == 1

    def test_process_skips_when_no_text(self, generic_processor, mock_core):
        result = asyncio.get_event_loop().run_until_complete(
            generic_processor.process({"random": 123}, {})
        )
        assert result["status"] == "skipped"
        # Recebido mas não processado
        assert generic_processor.stats["total_received"] == 1
        assert generic_processor.stats["total_processed"] == 0

    def test_process_returns_success_structure(self, generic_processor, mock_core):
        result = asyncio.get_event_loop().run_until_complete(
            generic_processor.process({"text": "teste"}, {})
        )
        assert result["status"] == "success"
        assert result["webhook_type"] == "generic"
        assert result["plugin_used"] == "word_frequency"
        assert "result" in result


# =============================================================================
# ENDPOINTS — INTEGRATION
# =============================================================================

class TestWebhookEndpoints:

    def test_custom_webhook_happy_path(self, client):
        response = client.post("/webhook/custom", json={"text": "Texto de teste simples"})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["webhook_type"] == "generic"
        assert "result" in data

    def test_custom_webhook_content_field(self, client):
        response = client.post("/webhook/custom", json={"content": "Conteúdo via content"})
        assert response.status_code == 200
        assert response.json()["status"] == "success"

    def test_custom_webhook_with_plugin(self, client):
        response = client.post(
            "/webhook/custom",
            json={"text": "Teste de sentimento positivo", "plugin": "sentiment_analyzer"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["plugin_used"] == "sentiment_analyzer"

    def test_custom_webhook_no_text_returns_skipped(self, client):
        response = client.post("/webhook/custom", json={"metadata": {"source": "test"}})
        assert response.status_code == 200
        assert response.json()["status"] == "skipped"

    def test_webhook_stats_endpoint(self, client):
        response = client.get("/webhook/stats")
        assert response.status_code == 200
        data = response.json()
        assert "stats" in data
        assert "generic" in data["stats"]

    def test_webhook_stats_increment(self, client):
        # Processar um webhook
        client.post("/webhook/custom", json={"text": "Contagem"})
        # Verificar stats
        response = client.get("/webhook/stats")
        stats = response.json()["stats"]["generic"]
        assert stats["total_received"] >= 1


# =============================================================================
# EDGE CASES — webhooks.py uncovered lines
# =============================================================================

class TestWebhookEdgeCases:
    """Testa branches nao cobertos em webhooks.py"""

    def test_webhook_processor_extract_text_not_implemented(self):
        """Base WebhookProcessor.extract_text levanta NotImplementedError"""
        proc = WebhookProcessor(WebhookType.GENERIC)
        with pytest.raises(NotImplementedError):
            asyncio.get_event_loop().run_until_complete(
                proc.extract_text({})
            )

    def test_webhook_processor_determine_plugin_default(self):
        """Base WebhookProcessor.determine_plugin retorna word_frequency"""
        proc = WebhookProcessor(WebhookType.GENERIC)
        result = asyncio.get_event_loop().run_until_complete(
            proc.determine_plugin({})
        )
        assert result == "word_frequency"

    def test_generic_webhook_string_payload(self):
        """GenericWebhookProcessor.extract_text com string retorna a string"""
        proc = GenericWebhookProcessor()
        result = asyncio.get_event_loop().run_until_complete(
            proc.extract_text("just a string")
        )
        assert result == "just a string"

    def test_set_tracking_callback(self):
        """set_tracking_callback define o callback global"""
        from qualia.api.webhooks import set_tracking_callback
        import qualia.api.webhooks as wh_module

        old = wh_module.track_webhook_callback
        try:
            mock_cb = MagicMock()
            set_tracking_callback(mock_cb)
            assert wh_module.track_webhook_callback is mock_cb
        finally:
            wh_module.track_webhook_callback = old

    def test_webhook_verify_signature_failure(self, mock_core):
        """Falha na verificacao de assinatura levanta HTTPException"""

        class StrictProcessor(WebhookProcessor):
            def __init__(self):
                super().__init__(WebhookType.GENERIC)

            async def extract_text(self, payload):
                return payload.get("text")

            async def verify_signature(self, payload, headers):
                return False

        proc = StrictProcessor()
        with pytest.raises(HTTPException) as exc_info:
            asyncio.get_event_loop().run_until_complete(
                proc.process({"text": "teste"}, {})
            )
        # A HTTPException 401 do verify_signature e capturada pelo except
        # generico do process(), que re-wrapa como HTTPException 500
        assert "Invalid signature" in exc_info.value.detail
        assert proc.stats["total_errors"] == 1
