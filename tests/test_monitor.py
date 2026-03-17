"""
Testes do sistema de monitoring do Qualia.

Cobre Metrics dataclass, funções de tracking e SSE stream.
"""

import pytest
import asyncio
import json
import time

from qualia.api.monitor import (
    Metrics,
    metrics,
    track_request,
    track_webhook,
    notify_streams,
    request_times,
    active_streams,
)


# =============================================================================
# METRICS DATACLASS
# =============================================================================

class TestMetrics:

    def test_default_initialization(self):
        m = Metrics()
        assert m.requests_total == 0
        assert m.requests_per_minute == 0.0
        assert m.active_connections == 0
        assert m.errors_total == 0
        assert m.last_error == ""
        assert m.uptime_seconds == 0.0

    def test_post_init_creates_defaultdicts(self):
        m = Metrics()
        # Acessar chave inexistente não deve dar KeyError
        assert m.plugin_usage["nonexistent"] == 0
        assert m.webhook_stats["nonexistent"] == 0

    def test_explicit_none_becomes_defaultdict(self):
        m = Metrics(plugin_usage=None, webhook_stats=None)
        assert m.plugin_usage["any_key"] == 0
        assert m.webhook_stats["any_key"] == 0


# =============================================================================
# TRACK REQUEST
# =============================================================================

class TestTrackRequest:

    @pytest.fixture(autouse=True)
    def _reset(self, reset_monitor_state):
        """Usa fixture do conftest para resetar estado global"""
        pass

    def test_increments_total(self):
        asyncio.get_event_loop().run_until_complete(
            track_request("/analyze/word_frequency")
        )
        assert metrics.requests_total == 1

    def test_tracks_plugin_usage(self):
        asyncio.get_event_loop().run_until_complete(
            track_request("/analyze/word_frequency", plugin_id="word_frequency")
        )
        assert metrics.plugin_usage["word_frequency"] == 1

    def test_tracks_error(self):
        asyncio.get_event_loop().run_until_complete(
            track_request("/analyze/bad", error="Plugin not found")
        )
        assert metrics.errors_total == 1
        assert "Plugin not found" in metrics.last_error

    def test_calculates_rpm(self):
        # Disparar 3 requests
        for _ in range(3):
            asyncio.get_event_loop().run_until_complete(
                track_request("/test")
            )
        # Todos dentro do último minuto
        assert metrics.requests_per_minute == 3


# =============================================================================
# TRACK WEBHOOK
# =============================================================================

class TestTrackWebhook:

    @pytest.fixture(autouse=True)
    def _reset(self, reset_monitor_state):
        pass

    def test_increments_webhook_stats(self):
        asyncio.get_event_loop().run_until_complete(
            track_webhook("generic")
        )
        assert metrics.webhook_stats["generic"] == 1


# =============================================================================
# NOTIFY STREAMS
# =============================================================================

class TestNotifyStreams:

    @pytest.fixture(autouse=True)
    def _reset(self, reset_monitor_state):
        pass

    def test_no_streams_no_error(self):
        """Sem streams ativos, notify_streams não faz nada"""
        asyncio.get_event_loop().run_until_complete(notify_streams())
        # Se chegou aqui sem erro, passou

    def test_sends_to_active_queue(self):
        queue = asyncio.Queue()
        active_streams.add(queue)
        try:
            asyncio.get_event_loop().run_until_complete(notify_streams())
            # Deve ter colocado dados na queue
            assert not queue.empty()
            data = json.loads(queue.get_nowait())
            assert "timestamp" in data
            assert "metrics" in data
        finally:
            active_streams.discard(queue)


# =============================================================================
# SSE ENDPOINT
# =============================================================================

class TestSSEEndpoint:

    @pytest.fixture(autouse=True)
    def _reset(self, reset_monitor_state):
        pass

    def test_monitor_dashboard_returns_html(self, client):
        """GET /monitor/ retorna HTML do dashboard"""
        response = client.get("/monitor/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Qualia Core Monitor" in response.text

    def test_monitor_dashboard_has_metrics_elements(self, client):
        """Dashboard HTML contém os IDs de métricas esperados"""
        response = client.get("/monitor/")
        html = response.text
        for element_id in ["requests-total", "requests-per-minute", "active-connections", "uptime"]:
            assert element_id in html, f"Elemento {element_id} não encontrado no dashboard"

    def test_monitor_dashboard_has_sse_connection(self, client):
        """Dashboard HTML contém script de conexão SSE"""
        response = client.get("/monitor/")
        html = response.text
        assert "EventSource" in html
        assert "/monitor/stream" in html

    def test_monitor_dashboard_has_error_section(self, client):
        """Dashboard HTML contém seção de erros"""
        response = client.get("/monitor/")
        html = response.text
        assert "error-box" in html
        assert "last-error" in html

    def test_monitor_stream_returns_sse_data(self):
        """event_generator produz dados iniciais no formato SSE correto"""
        from unittest.mock import AsyncMock, MagicMock

        # Simula Request que desconecta após receber dados iniciais
        mock_request = MagicMock()
        mock_request.is_disconnected = AsyncMock(return_value=True)

        from qualia.api.monitor import monitor_stream
        response = asyncio.get_event_loop().run_until_complete(
            monitor_stream(mock_request)
        )

        # Verifica headers do StreamingResponse
        assert response.media_type == "text/event-stream"
        assert response.headers.get("cache-control") == "no-cache"
        assert response.headers.get("x-accel-buffering") == "no"

        # Consome o generator para pegar dados iniciais
        gen = response.body_iterator
        first_chunk = asyncio.get_event_loop().run_until_complete(gen.__anext__())

        assert first_chunk.startswith("data: ")
        assert first_chunk.endswith("\n\n")
        data = json.loads(first_chunk[len("data: "):-2])
        assert "timestamp" in data
        assert "metrics" in data
        m = data["metrics"]
        assert "requests_total" in m
        assert "uptime_seconds" in m
        assert "active_connections" in m
        assert "plugin_usage" in m
        assert "webhook_stats" in m

    def test_monitor_stream_sends_queued_updates(self):
        """event_generator envia dados da queue quando disponíveis"""
        from unittest.mock import AsyncMock, MagicMock

        call_count = 0

        async def disconnect_after_second_call():
            nonlocal call_count
            call_count += 1
            # Desconecta após receber o update da queue
            return call_count >= 2

        mock_request = MagicMock()
        mock_request.is_disconnected = AsyncMock(side_effect=disconnect_after_second_call)

        from qualia.api.monitor import monitor_stream

        response = asyncio.get_event_loop().run_until_complete(
            monitor_stream(mock_request)
        )

        gen = response.body_iterator

        # Pular dados iniciais
        asyncio.get_event_loop().run_until_complete(gen.__anext__())

        # Colocar dados na queue que foi registrada em active_streams
        test_data = json.dumps({"test": True})
        for q in list(active_streams):
            asyncio.get_event_loop().run_until_complete(q.put(test_data))

        # Próximo chunk deve ser o dado da queue
        chunk = asyncio.get_event_loop().run_until_complete(gen.__anext__())
        assert "data:" in chunk
        parsed = json.loads(chunk.strip().replace("data: ", ""))
        assert parsed.get("test") is True

    def test_monitor_stream_sends_heartbeat_on_timeout(self):
        """event_generator envia heartbeat quando queue não recebe dados"""
        from unittest.mock import AsyncMock, MagicMock

        call_count = 0

        async def disconnect_after_heartbeat():
            nonlocal call_count
            call_count += 1
            return call_count >= 1

        mock_request = MagicMock()
        mock_request.is_disconnected = AsyncMock(side_effect=disconnect_after_heartbeat)

        from qualia.api.monitor import monitor_stream

        response = asyncio.get_event_loop().run_until_complete(
            monitor_stream(mock_request)
        )

        gen = response.body_iterator

        # Pular dados iniciais
        asyncio.get_event_loop().run_until_complete(gen.__anext__())

        # Sem dados na queue, deve dar timeout e enviar heartbeat
        chunk = asyncio.get_event_loop().run_until_complete(gen.__anext__())
        assert chunk == ": heartbeat\n\n"

    def test_monitor_stream_cleans_up_on_disconnect(self):
        """Queue é removida de active_streams quando cliente desconecta"""
        from unittest.mock import AsyncMock, MagicMock

        mock_request = MagicMock()
        mock_request.is_disconnected = AsyncMock(return_value=True)

        from qualia.api.monitor import monitor_stream

        streams_before = len(active_streams)

        response = asyncio.get_event_loop().run_until_complete(
            monitor_stream(mock_request)
        )

        # Consumir todo o generator
        gen = response.body_iterator
        chunks = []
        try:
            while True:
                chunk = asyncio.get_event_loop().run_until_complete(gen.__anext__())
                chunks.append(chunk)
        except StopAsyncIteration:
            pass

        # Após terminar, a queue deve ter sido removida
        assert len(active_streams) == streams_before


# =============================================================================
# NOTIFY STREAMS — EDGE CASES
# =============================================================================

class TestNotifyStreamsEdgeCases:

    @pytest.fixture(autouse=True)
    def _reset(self, reset_monitor_state):
        pass

    def test_broken_queue_is_discarded(self):
        """Queue que falha no put() é removida de active_streams"""

        class BrokenQueue:
            """Simula queue que levanta exceção no put"""
            async def put(self, data):
                raise RuntimeError("Queue quebrada")

        broken = BrokenQueue()
        active_streams.add(broken)

        # Não deve levantar exceção
        asyncio.get_event_loop().run_until_complete(notify_streams())

        # Queue quebrada deve ter sido removida
        assert broken not in active_streams

    def test_mixed_good_and_broken_queues(self):
        """Queue boa recebe dados mesmo com queue quebrada na lista"""

        class BrokenQueue:
            async def put(self, data):
                raise RuntimeError("Falhou")

        good_queue = asyncio.Queue()
        broken = BrokenQueue()

        active_streams.add(good_queue)
        active_streams.add(broken)

        asyncio.get_event_loop().run_until_complete(notify_streams())

        # Queue boa recebeu dados
        assert not good_queue.empty()
        data = json.loads(good_queue.get_nowait())
        assert "metrics" in data

        # Queue quebrada foi removida
        assert broken not in active_streams
        # Queue boa permanece
        assert good_queue in active_streams

        active_streams.discard(good_queue)

    def test_notify_updates_uptime_and_connections(self):
        """notify_streams atualiza uptime e active_connections"""
        queue = asyncio.Queue()
        active_streams.add(queue)

        try:
            asyncio.get_event_loop().run_until_complete(notify_streams())
            data = json.loads(queue.get_nowait())
            # active_connections deve refletir a queue adicionada
            assert data["metrics"]["active_connections"] >= 1
            # uptime deve ser positivo
            assert data["metrics"]["uptime_seconds"] > 0
        finally:
            active_streams.discard(queue)


# =============================================================================
# TRACK REQUEST — EDGE CASES
# =============================================================================

class TestTrackRequestEdgeCases:

    @pytest.fixture(autouse=True)
    def _reset(self, reset_monitor_state):
        pass

    def test_request_without_plugin_or_error(self):
        """Request sem plugin_id e sem error só incrementa total"""
        asyncio.get_event_loop().run_until_complete(
            track_request("/health")
        )
        assert metrics.requests_total == 1
        assert metrics.errors_total == 0
        assert metrics.last_error == ""
        assert len(metrics.plugin_usage) == 0

    def test_multiple_plugins_tracked_independently(self):
        """Diferentes plugins são contabilizados separadamente"""
        asyncio.get_event_loop().run_until_complete(
            track_request("/analyze/sentiment", plugin_id="sentiment_analyzer")
        )
        asyncio.get_event_loop().run_until_complete(
            track_request("/analyze/sentiment", plugin_id="sentiment_analyzer")
        )
        asyncio.get_event_loop().run_until_complete(
            track_request("/analyze/readability", plugin_id="readability_analyzer")
        )
        assert metrics.plugin_usage["sentiment_analyzer"] == 2
        assert metrics.plugin_usage["readability_analyzer"] == 1

    def test_error_message_format(self):
        """Mensagem de erro contém endpoint e descrição"""
        asyncio.get_event_loop().run_until_complete(
            track_request("/process/bad_plugin", error="Timeout exceeded")
        )
        assert metrics.last_error == "/process/bad_plugin: Timeout exceeded"

    def test_consecutive_errors_keep_last(self):
        """Último erro sobrescreve o anterior"""
        asyncio.get_event_loop().run_until_complete(
            track_request("/a", error="Erro 1")
        )
        asyncio.get_event_loop().run_until_complete(
            track_request("/b", error="Erro 2")
        )
        assert metrics.errors_total == 2
        assert "Erro 2" in metrics.last_error
        assert "/b" in metrics.last_error


# =============================================================================
# TRACK WEBHOOK — EDGE CASES
# =============================================================================

class TestTrackWebhookEdgeCases:

    @pytest.fixture(autouse=True)
    def _reset(self, reset_monitor_state):
        pass

    def test_multiple_webhook_types(self):
        """Diferentes tipos de webhook são contabilizados separadamente"""
        asyncio.get_event_loop().run_until_complete(track_webhook("generic"))
        asyncio.get_event_loop().run_until_complete(track_webhook("generic"))
        asyncio.get_event_loop().run_until_complete(track_webhook("custom"))
        assert metrics.webhook_stats["generic"] == 2
        assert metrics.webhook_stats["custom"] == 1

    def test_webhook_notifies_streams(self):
        """track_webhook envia atualização para streams ativos"""
        queue = asyncio.Queue()
        active_streams.add(queue)

        try:
            asyncio.get_event_loop().run_until_complete(track_webhook("test"))
            assert not queue.empty()
            data = json.loads(queue.get_nowait())
            assert data["metrics"]["webhook_stats"]["test"] == 1
        finally:
            active_streams.discard(queue)
