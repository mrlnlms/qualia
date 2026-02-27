<script>
  let { data } = $props();

  let expanded = $state(false);

  const topWords = $derived(
    data?.top_words && Array.isArray(data.top_words) ? data.top_words.slice(0, 20) : null
  );

  const maxCount = $derived(
    topWords ? Math.max(...topWords.map(w => w[1])) : 0
  );

  // Separate scalar metrics (for summary cards) from other entries
  const numericMetrics = $derived(
    data ? Object.entries(data).filter(([k, v]) => typeof v === 'number') : []
  );

  const stringMetrics = $derived(
    data ? Object.entries(data).filter(([k, v]) => typeof v === 'string' && v.length <= 100) : []
  );

  // Long text fields (like transcription) — render as full-width blocks
  const longTextFields = $derived(
    data ? Object.entries(data).filter(([k, v]) => typeof v === 'string' && v.length > 100) : []
  );

  // Show bar chart for results with 4+ numeric metrics (like readability)
  // but not for word_frequency (which has its own top_words chart)
  const showMetricBars = $derived(
    !topWords && numericMetrics.length >= 4
  );

  const metricBarsMax = $derived(
    showMetricBars ? Math.max(...numericMetrics.map(([, v]) => Math.abs(v)), 1) : 0
  );

  // For summary grid, show string metrics + numeric metrics if no bar chart
  const summaryKeys = $derived(
    data ? [
      ...stringMetrics.slice(0, 4),
      ...(showMetricBars ? [] : numericMetrics.slice(0, 6))
    ].slice(0, 6) : []
  );

  function formatJson(obj) {
    return JSON.stringify(obj, null, 2);
  }

  function formatKey(key) {
    return key.replace(/_/g, ' ');
  }

  function formatValue(val) {
    if (typeof val === 'number') {
      if (Number.isInteger(val)) return val.toLocaleString();
      return val.toLocaleString(undefined, { maximumFractionDigits: 2 });
    }
    return String(val);
  }
</script>

<div class="json-result">
  {#if summaryKeys.length > 0 && !topWords}
    <div class="summary-grid">
      {#each summaryKeys as [key, val], i}
        <div class="summary-item" style="animation-delay: {i * 50}ms">
          <span class="summary-label">{formatKey(key)}</span>
          <span class="summary-value">{formatValue(val)}</span>
        </div>
      {/each}
    </div>
  {/if}

  {#if longTextFields.length > 0}
    {#each longTextFields as [key, val], i}
      <div class="long-text-section" style="animation-delay: {i * 50}ms">
        <div class="long-text-header">
          <span class="summary-label">{formatKey(key)}</span>
          <span class="chart-meta">{val.length.toLocaleString()} chars</span>
        </div>
        <div class="long-text-content">{val}</div>
      </div>
    {/each}
  {/if}

  {#if showMetricBars}
    <div class="chart-section">
      <div class="chart-header">
        <h4 class="section-title">Metrics</h4>
        <span class="chart-meta">{numericMetrics.length} values</span>
      </div>
      <div class="bar-chart">
        {#each numericMetrics as [key, val], i}
          <div class="bar-row" style="animation-delay: {i * 30}ms">
            <span class="bar-label">{formatKey(key)}</span>
            <div class="bar-track">
              <div class="bar-fill" style:width="{(Math.abs(val) / metricBarsMax) * 100}%"></div>
            </div>
            <span class="bar-count">{formatValue(val)}</span>
          </div>
        {/each}
      </div>
    </div>
  {/if}

  {#if topWords}
    <div class="chart-section">
      <div class="chart-header">
        <h4 class="section-title">Top Words</h4>
        {#if data?.vocabulary_size}
          <span class="chart-meta">{data.vocabulary_size.toLocaleString()} unique words</span>
        {/if}
      </div>
      <div class="bar-chart">
        {#each topWords as [word, count], i}
          <div class="bar-row" style="animation-delay: {i * 30}ms">
            <span class="bar-rank">{i + 1}</span>
            <span class="bar-label">{word}</span>
            <div class="bar-track">
              <div class="bar-fill" style:width="{(count / maxCount) * 100}%"></div>
            </div>
            <span class="bar-count">{count}</span>
          </div>
        {/each}
      </div>
    </div>
  {/if}

  <div class="raw-section">
    <button class="toggle-raw" onclick={() => expanded = !expanded}>
      <span class="toggle-icon" class:open={expanded}>&#9656;</span>
      Raw JSON
    </button>
    {#if expanded}
      <pre class="json-code">{formatJson(data)}</pre>
    {/if}
  </div>
</div>

<style>
  .json-result {
    display: flex;
    flex-direction: column;
    gap: 24px;
  }

  .summary-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
    gap: 10px;
  }

  .summary-item {
    background: var(--bg-input);
    border-radius: var(--radius-sm);
    padding: 14px 16px;
    display: flex;
    flex-direction: column;
    gap: 4px;
    animation: fadeUp 0.3s ease backwards;
  }

  .summary-label {
    font-size: 0.7em;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.8px;
  }

  .summary-value {
    font-size: 1.2em;
    font-weight: 600;
    color: var(--text-primary);
    font-family: var(--font-mono);
  }

  .long-text-section {
    animation: fadeUp 0.3s ease backwards;
  }

  .long-text-header {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    margin-bottom: 8px;
  }

  .long-text-content {
    padding: 18px;
    background: var(--bg-input);
    border-radius: var(--radius-sm);
    border: 1px solid var(--border-subtle);
    font-size: 0.88em;
    color: var(--text-secondary);
    line-height: 1.7;
    max-height: 320px;
    overflow-y: auto;
    white-space: pre-wrap;
    word-wrap: break-word;
  }

  .chart-header {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    margin-bottom: 14px;
  }

  .section-title {
    font-size: 0.82em;
    font-weight: 600;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 1px;
  }

  .chart-meta {
    font-size: 0.74em;
    color: var(--text-muted);
    font-family: var(--font-mono);
  }

  .bar-chart {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .bar-row {
    display: flex;
    align-items: center;
    gap: 8px;
    animation: fadeUp 0.3s ease backwards;
  }

  .bar-rank {
    width: 22px;
    font-size: 0.68em;
    color: var(--text-muted);
    font-family: var(--font-mono);
    text-align: right;
    flex-shrink: 0;
    opacity: 0.6;
  }

  .bar-label {
    width: 90px;
    font-size: 0.82em;
    color: var(--text-secondary);
    text-align: right;
    font-family: var(--font-mono);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    flex-shrink: 0;
  }

  .bar-track {
    flex: 1;
    height: 22px;
    background: var(--bg-input);
    border-radius: 4px;
    overflow: hidden;
  }

  .bar-fill {
    height: 100%;
    background: var(--accent-gradient);
    border-radius: 4px;
    transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1);
    min-width: 2px;
    position: relative;
  }

  .bar-fill::after {
    content: '';
    position: absolute;
    top: 0;
    right: 0;
    bottom: 0;
    width: 30%;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.08));
  }

  .bar-count {
    width: 44px;
    font-size: 0.76em;
    color: var(--text-muted);
    font-family: var(--font-mono);
    flex-shrink: 0;
    text-align: right;
  }

  .toggle-raw {
    background: none;
    border: none;
    color: var(--text-muted);
    font-size: 0.8em;
    font-family: var(--font-mono);
    padding: 4px 0;
    transition: color var(--transition);
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .toggle-raw:hover {
    color: var(--text-secondary);
  }

  .toggle-icon {
    display: inline-block;
    transition: transform var(--transition);
    font-size: 0.8em;
  }

  .toggle-icon.open {
    transform: rotate(90deg);
  }

  .json-code {
    margin-top: 8px;
    padding: 18px;
    background: var(--bg-input);
    border-radius: var(--radius-sm);
    border: 1px solid var(--border-subtle);
    font-family: var(--font-mono);
    font-size: 0.76em;
    color: var(--text-secondary);
    overflow-x: auto;
    line-height: 1.65;
    max-height: 400px;
    overflow-y: auto;
    animation: fadeIn 0.2s ease;
  }
</style>
