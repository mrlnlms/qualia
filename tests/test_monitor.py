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
