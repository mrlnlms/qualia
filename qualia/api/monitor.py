"""
Real-time monitoring system for Qualia Core API.

Provides Server-Sent Events (SSE) stream with metrics and activity.
"""

from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse, HTMLResponse
from typing import Dict, Any, List
from datetime import datetime, timedelta
from collections import defaultdict, deque
import asyncio
import json
import time
from dataclasses import dataclass, asdict

router = APIRouter(prefix="/monitor", tags=["monitoring"])

# Global metrics storage
@dataclass
class Metrics:
    """System metrics."""
    requests_total: int = 0
    requests_per_minute: float = 0.0
    active_connections: int = 0
    plugin_usage: Dict[str, int] = None
    webhook_stats: Dict[str, int] = None
    errors_total: int = 0
    last_error: str = ""
    uptime_seconds: float = 0.0
    
    def __post_init__(self):
        if self.plugin_usage is None:
            self.plugin_usage = defaultdict(int)
        if self.webhook_stats is None:
            self.webhook_stats = defaultdict(int)

# Global state
metrics = Metrics()
start_time = time.time()
request_times = deque(maxlen=100)  # Last 100 request timestamps
active_streams = set()  # Active SSE connections
_metrics_lock = asyncio.Lock()

# Middleware to track metrics
async def track_request(endpoint: str, plugin_id: str = None, error: str = None):
    """Track API request for metrics."""
    async with _metrics_lock:
        metrics.requests_total += 1
        request_times.append(time.time())

        if plugin_id:
            metrics.plugin_usage[plugin_id] += 1

        if error:
            metrics.errors_total += 1
            metrics.last_error = f"{endpoint}: {error}"

        # Calculate requests per minute
        now = time.time()
        recent_requests = sum(1 for t in request_times if now - t <= 60)
        metrics.requests_per_minute = recent_requests

    # Notify active streams (fora do lock — notify_streams tem seu próprio fluxo)
    await notify_streams()

async def track_webhook(webhook_type: str):
    """Track webhook activity."""
    async with _metrics_lock:
        metrics.webhook_stats[webhook_type] += 1
    await notify_streams()

async def notify_streams():
    """Notify all active SSE streams of metric updates."""
    if not active_streams:
        return

    # Snapshot metrics under lock
    async with _metrics_lock:
        metrics.uptime_seconds = time.time() - start_time
        metrics.active_connections = len(active_streams)
        event_data = {
            "timestamp": datetime.now().isoformat(),
            "metrics": asdict(metrics)
        }

    # Send fora do lock — I/O não deve segurar o lock
    failed = []
    for stream in list(active_streams):
        try:
            await stream.put(json.dumps(event_data))
        except Exception:
            failed.append(stream)

    if failed:
        async with _metrics_lock:
            for stream in failed:
                active_streams.discard(stream)
            metrics.active_connections = len(active_streams)

# SSE endpoint
@router.get("/stream")
async def monitor_stream(request: Request):
    """
    Server-Sent Events stream for real-time monitoring.
    
    Sends metric updates every second.
    """
    async def event_generator():
        queue = asyncio.Queue()

        # Add stream e snapshot inicial sob lock
        async with _metrics_lock:
            active_streams.add(queue)
            metrics.uptime_seconds = time.time() - start_time
            metrics.active_connections = len(active_streams)
            initial_data = {
                "timestamp": datetime.now().isoformat(),
                "metrics": asdict(metrics)
            }

        yield f"data: {json.dumps(initial_data)}\n\n"

        try:
            while True:
                try:
                    data = await asyncio.wait_for(queue.get(), timeout=1.0)
                    yield f"data: {data}\n\n"
                except asyncio.TimeoutError:
                    yield f": heartbeat\n\n"

                if await request.is_disconnected():
                    break

        finally:
            async with _metrics_lock:
                active_streams.discard(queue)
                metrics.active_connections = len(active_streams)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

_TEMPLATE_DIR = Path(__file__).parent / "templates"

# Dashboard HTML
@router.get("/")
async def monitor_dashboard():
    """Simple HTML dashboard for monitoring. Template in templates/monitor.html."""
    html_path = _TEMPLATE_DIR / "monitor.html"
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"))

# Export tracking functions for use in main API
__all__ = ['router', 'track_request', 'track_webhook', 'metrics']