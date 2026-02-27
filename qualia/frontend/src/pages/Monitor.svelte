<script>
  import { onMount } from 'svelte';
  import { createMonitorStream } from '../lib/api.js';
  import StatusDot from '../components/StatusDot.svelte';

  let connected = $state(false);
  let metrics = $state(null);
  let rpmHistory = $state(Array(60).fill(0));
  let source = null;

  function formatUptime(seconds) {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = Math.floor(seconds % 60);
    return `${String(h).padStart(2,'0')}:${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`;
  }

  function onMessage(data) {
    connected = true;
    metrics = data.metrics;
    rpmHistory = [...rpmHistory.slice(1), data.metrics.requests_per_minute];
  }

  function onError() {
    connected = false;
  }

  onMount(() => {
    source = createMonitorStream(onMessage, onError);
    return () => { if (source) source.close(); };
  });

  const chartWidth = 400;
  const chartHeight = 80;
  const maxRpm = $derived(Math.max(...rpmHistory, 10));
  const points = $derived(
    rpmHistory.map((v, i) => {
      const x = (i / (rpmHistory.length - 1)) * chartWidth;
      const y = chartHeight - (v / maxRpm) * (chartHeight - 4) - 2;
      return `${x},${y}`;
    }).join(' ')
  );
  const areaPoints = $derived(
    `0,${chartHeight} ${points} ${chartWidth},${chartHeight}`
  );

  const pluginEntries = $derived(
    metrics ? Object.entries(metrics.plugin_usage).sort((a, b) => b[1] - a[1]) : []
  );

  const webhooksTotal = $derived(
    metrics ? Object.values(metrics.webhook_stats).reduce((sum, c) => sum + c, 0) : 0
  );

  const metricCards = $derived([
    { label: 'Total Requests', value: metrics?.requests_total ?? 0, mono: false },
    { label: 'Requests/Min', value: Math.round(metrics?.requests_per_minute ?? 0), unit: 'req/min', mono: false },
    { label: 'Connections', value: metrics?.active_connections ?? 0, mono: false },
    { label: 'Uptime', value: formatUptime(metrics?.uptime_seconds ?? 0), mono: true },
    { label: 'Errors', value: metrics?.errors_total ?? 0, error: (metrics?.errors_total ?? 0) > 0 },
    { label: 'Webhooks', value: webhooksTotal, mono: false },
  ]);
</script>

<div class="monitor-page">
  <div class="monitor-header">
    <div>
      <h1 class="page-title">Monitor</h1>
      <p class="page-desc">Real-time system metrics</p>
    </div>
    <div class="conn-status">
      <StatusDot {connected} />
      <span class="conn-text">{connected ? 'Live' : 'Disconnected'}</span>
    </div>
  </div>

  <div class="metrics-grid">
    {#each metricCards as card, i}
      <div class="metric-card" style="animation-delay: {i * 50}ms">
        <div class="metric-label">{card.label}</div>
        <div class="metric-value" class:mono={card.mono} class:error-val={card.error}>
          {card.value}
          {#if card.unit}
            <span class="metric-unit">{card.unit}</span>
          {/if}
        </div>
      </div>
    {/each}
  </div>

  <div class="chart-card">
    <div class="chart-header">
      <h3 class="card-title">Requests per Minute</h3>
      <span class="chart-live">
        <span class="live-dot"></span>
        live
      </span>
    </div>
    <svg viewBox="0 0 {chartWidth} {chartHeight}" class="chart-svg" preserveAspectRatio="none">
      <defs>
        <linearGradient id="chartGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="var(--accent)" stop-opacity="0.15" />
          <stop offset="100%" stop-color="var(--accent)" stop-opacity="0" />
        </linearGradient>
      </defs>
      {#each [0.25, 0.5, 0.75] as frac}
        <line x1="0" y1={chartHeight * frac} x2={chartWidth} y2={chartHeight * frac}
          stroke="var(--border-subtle)" stroke-width="0.5" />
      {/each}
      <polygon points={areaPoints} fill="url(#chartGrad)" />
      <polyline points={points} fill="none" stroke="var(--accent)" stroke-width="1.5" stroke-linejoin="round" />
    </svg>
  </div>

  {#if pluginEntries.length > 0}
    <div class="chart-card">
      <h3 class="card-title">Plugin Usage</h3>
      <div class="usage-bars">
        {#each pluginEntries as [name, count], i}
          <div class="usage-row" style="animation-delay: {i * 40}ms">
            <span class="usage-name">{name}</span>
            <div class="usage-track">
              <div class="usage-fill"
                style:width="{Math.max((count / Math.max(...pluginEntries.map(e => e[1]))) * 100, 4)}%">
              </div>
            </div>
            <span class="usage-count">{count}</span>
          </div>
        {/each}
      </div>
    </div>
  {/if}

  {#if metrics?.last_error}
    <div class="error-card">
      <div class="error-stripe"></div>
      <div class="error-content">
        <h3 class="error-title">Last Error</h3>
        <p class="error-text">{metrics.last_error}</p>
      </div>
    </div>
  {/if}
</div>

<style>
  .monitor-page {
    max-width: 980px;
  }

  .monitor-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 36px;
  }

  .page-title {
    font-size: 1.65em;
    font-weight: 500;
    color: var(--text-primary);
    letter-spacing: -0.3px;
    margin-bottom: 2px;
  }

  .page-desc {
    color: var(--text-muted);
    font-size: 0.9em;
  }

  .conn-status {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 8px 16px;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 20px;
  }

  .conn-text {
    font-size: 0.82em;
    color: var(--text-secondary);
    font-family: var(--font-mono);
  }

  .metrics-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
    gap: 12px;
    margin-bottom: 24px;
  }

  .metric-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 20px;
    transition: all var(--transition);
    animation: fadeUp 0.3s ease backwards;
  }

  .metric-card:hover {
    border-color: var(--border-focus);
    box-shadow: var(--shadow-glow);
  }

  .metric-label {
    font-size: 0.68em;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 8px;
  }

  .metric-value {
    font-size: 1.9em;
    font-weight: 600;
    color: var(--text-primary);
    line-height: 1.1;
  }

  .metric-value.mono {
    font-family: var(--font-mono);
    font-size: 1.5em;
    font-weight: 500;
  }

  .metric-value.error-val {
    color: var(--error);
  }

  .metric-unit {
    font-size: 0.38em;
    color: var(--text-muted);
    font-weight: 400;
    margin-left: 4px;
  }

  .chart-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 22px;
    margin-bottom: 14px;
  }

  .chart-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 14px;
  }

  .card-title {
    font-size: 0.82em;
    color: var(--text-secondary);
    font-weight: 500;
  }

  .chart-live {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 0.7em;
    color: var(--text-muted);
    font-family: var(--font-mono);
    text-transform: uppercase;
    letter-spacing: 1px;
  }

  .live-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--accent-green);
    animation: ping 2s cubic-bezier(0, 0, 0.2, 1) infinite;
  }

  @keyframes ping {
    0% { opacity: 1; }
    50% { opacity: 0.4; }
    100% { opacity: 1; }
  }

  .chart-svg {
    width: 100%;
    height: 80px;
  }

  .usage-bars {
    display: flex;
    flex-direction: column;
    gap: 8px;
    margin-top: 4px;
  }

  .usage-row {
    display: flex;
    align-items: center;
    gap: 12px;
    animation: fadeUp 0.3s ease backwards;
  }

  .usage-name {
    width: 130px;
    font-size: 0.82em;
    color: var(--text-secondary);
    font-family: var(--font-mono);
    text-align: right;
    flex-shrink: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .usage-track {
    flex: 1;
    height: 20px;
    background: var(--bg-input);
    border-radius: 4px;
    overflow: hidden;
  }

  .usage-fill {
    height: 100%;
    background: var(--accent-gradient);
    border-radius: 4px;
    transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1);
  }

  .usage-count {
    width: 44px;
    font-size: 0.76em;
    color: var(--accent);
    font-family: var(--font-mono);
    font-weight: 500;
    text-align: right;
    flex-shrink: 0;
  }

  .error-card {
    background: var(--error-bg);
    border: 1px solid rgba(240, 96, 96, 0.2);
    border-radius: var(--radius);
    margin-top: 14px;
    overflow: hidden;
  }

  .error-stripe {
    height: 2px;
    background: linear-gradient(90deg, var(--error), transparent);
  }

  .error-content {
    padding: 16px 22px;
  }

  .error-title {
    color: var(--error);
    font-size: 0.82em;
    font-weight: 600;
    margin-bottom: 6px;
  }

  .error-text {
    color: var(--text-secondary);
    font-size: 0.82em;
    font-family: var(--font-mono);
    line-height: 1.5;
  }
</style>
