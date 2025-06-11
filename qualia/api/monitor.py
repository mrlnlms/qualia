"""
Real-time monitoring system for Qualia Core API.

Provides Server-Sent Events (SSE) stream with metrics and activity.
"""

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

# Middleware to track metrics
async def track_request(endpoint: str, plugin_id: str = None, error: str = None):
    """Track API request for metrics."""
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
    
    # Notify active streams
    await notify_streams()

async def track_webhook(webhook_type: str):
    """Track webhook activity."""
    metrics.webhook_stats[webhook_type] += 1
    await notify_streams()

async def notify_streams():
    """Notify all active SSE streams of metric updates."""
    if not active_streams:
        return
    
    # Update uptime
    metrics.uptime_seconds = time.time() - start_time
    metrics.active_connections = len(active_streams)
    
    # Create event data
    event_data = {
        "timestamp": datetime.now().isoformat(),
        "metrics": asdict(metrics)
    }
    
    # Send to all active streams
    for stream in list(active_streams):
        try:
            await stream.put(json.dumps(event_data))
        except:
            active_streams.discard(stream)

# SSE endpoint
@router.get("/stream")
async def monitor_stream(request: Request):
    """
    Server-Sent Events stream for real-time monitoring.
    
    Sends metric updates every second.
    """
    async def event_generator():
        queue = asyncio.Queue()
        active_streams.add(queue)
        
        try:
            # Send initial data
            metrics.uptime_seconds = time.time() - start_time
            metrics.active_connections = len(active_streams)
            
            initial_data = {
                "timestamp": datetime.now().isoformat(),
                "metrics": asdict(metrics)
            }
            yield f"data: {json.dumps(initial_data)}\n\n"
            
            # Stream updates
            while True:
                try:
                    # Wait for update or timeout
                    data = await asyncio.wait_for(queue.get(), timeout=1.0)
                    yield f"data: {data}\n\n"
                except asyncio.TimeoutError:
                    # Send heartbeat
                    yield f": heartbeat\n\n"
                    
                # Check if client disconnected
                if await request.is_disconnected():
                    break
                    
        finally:
            active_streams.discard(queue)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

# Dashboard HTML
@router.get("/")
async def monitor_dashboard():
    """
    Simple HTML dashboard for monitoring.
    
    No external dependencies - pure HTML/CSS/JS.
    """
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Qualia Core - Monitor</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background-color: #0a0a0a;
            color: #e0e0e0;
            line-height: 1.6;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        header {
            text-align: center;
            margin-bottom: 40px;
            padding: 20px 0;
            border-bottom: 1px solid #333;
        }
        
        h1 {
            font-size: 2.5em;
            font-weight: 300;
            background: linear-gradient(45deg, #00f260, #0575e6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }
        
        .status {
            display: inline-flex;
            align-items: center;
            gap: 10px;
            padding: 8px 16px;
            background: #1a1a1a;
            border-radius: 20px;
            font-size: 0.9em;
        }
        
        .status-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: #00ff00;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
        
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }
        
        .metric-card {
            background: #1a1a1a;
            border: 1px solid #333;
            border-radius: 10px;
            padding: 20px;
            transition: transform 0.2s, border-color 0.2s;
        }
        
        .metric-card:hover {
            transform: translateY(-2px);
            border-color: #0575e6;
        }
        
        .metric-label {
            font-size: 0.85em;
            color: #888;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 5px;
        }
        
        .metric-value {
            font-size: 2em;
            font-weight: 600;
            color: #fff;
        }
        
        .metric-unit {
            font-size: 0.8em;
            color: #888;
            margin-left: 5px;
        }
        
        .chart-container {
            background: #1a1a1a;
            border: 1px solid #333;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
        }
        
        .chart-title {
            font-size: 1.2em;
            margin-bottom: 15px;
            color: #e0e0e0;
        }
        
        canvas {
            max-width: 100%;
            height: 200px;
        }
        
        .plugin-usage {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-top: 10px;
        }
        
        .plugin-tag {
            padding: 5px 12px;
            background: #2a2a2a;
            border-radius: 15px;
            font-size: 0.85em;
            border: 1px solid #444;
        }
        
        .plugin-count {
            color: #0575e6;
            font-weight: 600;
            margin-left: 5px;
        }
        
        .error-box {
            background: #2a1a1a;
            border: 1px solid #ff4444;
            border-radius: 10px;
            padding: 15px;
            margin-top: 20px;
            display: none;
        }
        
        .error-box.show {
            display: block;
        }
        
        .error-title {
            color: #ff4444;
            font-weight: 600;
            margin-bottom: 5px;
        }
        
        .footer {
            text-align: center;
            padding: 20px 0;
            margin-top: 40px;
            border-top: 1px solid #333;
            color: #666;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Qualia Core Monitor</h1>
            <div class="status">
                <span class="status-dot"></span>
                <span id="status-text">Connecting...</span>
            </div>
        </header>
        
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-label">Total Requests</div>
                <div class="metric-value" id="requests-total">0</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-label">Requests/Min</div>
                <div class="metric-value">
                    <span id="requests-per-minute">0</span>
                    <span class="metric-unit">req/min</span>
                </div>
            </div>
            
            <div class="metric-card">
                <div class="metric-label">Active Connections</div>
                <div class="metric-value" id="active-connections">0</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-label">Uptime</div>
                <div class="metric-value" id="uptime">00:00:00</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-label">Total Errors</div>
                <div class="metric-value" id="errors-total">0</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-label">Webhooks Processed</div>
                <div class="metric-value" id="webhooks-total">0</div>
            </div>
        </div>
        
        <div class="chart-container">
            <h3 class="chart-title">Requests per Minute (Live)</h3>
            <canvas id="rpm-chart"></canvas>
        </div>
        
        <div class="chart-container">
            <h3 class="chart-title">Plugin Usage</h3>
            <div id="plugin-usage" class="plugin-usage"></div>
        </div>
        
        <div class="chart-container">
            <h3 class="chart-title">Webhook Activity</h3>
            <div id="webhook-stats" class="plugin-usage"></div>
        </div>
        
        <div class="error-box" id="error-box">
            <div class="error-title">Last Error</div>
            <div id="last-error"></div>
        </div>
        
        <footer class="footer">
            Qualia Core v0.1.0 | Real-time Monitor
        </footer>
    </div>
    
    <script>
        // Initialize chart data
        const rpmData = Array(60).fill(0);
        let rpmChart = null;
        
        // Create simple line chart
        function drawRpmChart() {
            const canvas = document.getElementById('rpm-chart');
            const ctx = canvas.getContext('2d');
            const width = canvas.width = canvas.offsetWidth;
            const height = canvas.height = 200;
            
            // Clear canvas
            ctx.clearRect(0, 0, width, height);
            
            // Draw grid
            ctx.strokeStyle = '#333';
            ctx.lineWidth = 1;
            
            // Horizontal lines
            for (let i = 0; i <= 4; i++) {
                const y = (height / 4) * i;
                ctx.beginPath();
                ctx.moveTo(0, y);
                ctx.lineTo(width, y);
                ctx.stroke();
            }
            
            // Draw data
            ctx.strokeStyle = '#0575e6';
            ctx.lineWidth = 2;
            ctx.beginPath();
            
            const stepX = width / (rpmData.length - 1);
            const maxValue = Math.max(...rpmData, 10);
            
            rpmData.forEach((value, i) => {
                const x = i * stepX;
                const y = height - (value / maxValue) * height;
                
                if (i === 0) {
                    ctx.moveTo(x, y);
                } else {
                    ctx.lineTo(x, y);
                }
            });
            
            ctx.stroke();
            
            // Fill area
            ctx.lineTo(width, height);
            ctx.lineTo(0, height);
            ctx.closePath();
            ctx.fillStyle = 'rgba(5, 117, 230, 0.1)';
            ctx.fill();
        }
        
        // Format uptime
        function formatUptime(seconds) {
            const hours = Math.floor(seconds / 3600);
            const minutes = Math.floor((seconds % 3600) / 60);
            const secs = Math.floor(seconds % 60);
            
            return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
        }
        
        // Update metrics
        function updateMetrics(data) {
            const metrics = data.metrics;
            
            // Update counters
            document.getElementById('requests-total').textContent = metrics.requests_total;
            document.getElementById('requests-per-minute').textContent = Math.round(metrics.requests_per_minute);
            document.getElementById('active-connections').textContent = metrics.active_connections;
            document.getElementById('uptime').textContent = formatUptime(metrics.uptime_seconds);
            document.getElementById('errors-total').textContent = metrics.errors_total;
            
            // Update webhooks total
            const webhooksTotal = Object.values(metrics.webhook_stats).reduce((a, b) => a + b, 0);
            document.getElementById('webhooks-total').textContent = webhooksTotal;
            
            // Update RPM chart
            rpmData.shift();
            rpmData.push(metrics.requests_per_minute);
            drawRpmChart();
            
            // Update plugin usage
            const pluginUsageEl = document.getElementById('plugin-usage');
            pluginUsageEl.innerHTML = '';
            
            Object.entries(metrics.plugin_usage).forEach(([plugin, count]) => {
                const tag = document.createElement('div');
                tag.className = 'plugin-tag';
                tag.innerHTML = `${plugin}<span class="plugin-count">${count}</span>`;
                pluginUsageEl.appendChild(tag);
            });
            
            // Update webhook stats
            const webhookStatsEl = document.getElementById('webhook-stats');
            webhookStatsEl.innerHTML = '';
            
            Object.entries(metrics.webhook_stats).forEach(([type, count]) => {
                const tag = document.createElement('div');
                tag.className = 'plugin-tag';
                tag.innerHTML = `${type}<span class="plugin-count">${count}</span>`;
                webhookStatsEl.appendChild(tag);
            });
            
            // Update error
            if (metrics.last_error) {
                document.getElementById('error-box').classList.add('show');
                document.getElementById('last-error').textContent = metrics.last_error;
            }
        }
        
        // Connect to SSE
        function connect() {
            const eventSource = new EventSource('/monitor/stream');
            
            eventSource.onopen = () => {
                document.getElementById('status-text').textContent = 'Connected';
                document.querySelector('.status-dot').style.background = '#00ff00';
            };
            
            eventSource.onmessage = (event) => {
                const data = JSON.parse(event.data);
                updateMetrics(data);
            };
            
            eventSource.onerror = () => {
                document.getElementById('status-text').textContent = 'Disconnected';
                document.querySelector('.status-dot').style.background = '#ff4444';
                
                // Reconnect after 5 seconds
                setTimeout(connect, 5000);
                eventSource.close();
            };
        }
        
        // Initialize
        connect();
        drawRpmChart();
        
        // Redraw chart on resize
        window.addEventListener('resize', drawRpmChart);
    </script>
</body>
</html>
    """
    
    return HTMLResponse(content=html_content)

# Export tracking functions for use in main API
__all__ = ['router', 'track_request', 'track_webhook', 'metrics']