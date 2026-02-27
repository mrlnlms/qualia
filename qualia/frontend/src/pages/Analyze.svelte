<script>
  import { pluginsByType } from '../lib/stores.js';
  import { fetchPluginSchema, analyze, visualize, resolveConfig } from '../lib/api.js';
  import ParamForm from '../components/ParamForm.svelte';
  import TextInput from '../components/TextInput.svelte';
  import ResultView from '../components/ResultView.svelte';

  let selectedPluginId = $state('');
  let schema = $state(null);
  let configValues = $state({});
  let text = $state('');
  let loading = $state(false);
  let loadingStatus = $state('');
  let loadingElapsed = $state(0);
  let loadingTimer = null;
  let result = $state(null);
  let error = $state('');

  function startTimer(status) {
    loadingStatus = status;
    loadingElapsed = 0;
    loadingTimer = setInterval(() => loadingElapsed++, 1000);
  }
  function stopTimer() {
    clearInterval(loadingTimer);
    loadingTimer = null;
    loadingElapsed = 0;
    loadingStatus = '';
  }
  let currentTextSize = $state('medium');
  let calibrating = $state(false);
  let calibrated = $state(false);

  // Visualization
  let vizPluginId = $state('');
  let vizLoading = $state(false);
  let vizResult = $state(null);

  // Filter visualizers to only those compatible with current result
  const compatibleVisualizers = $derived.by(() => {
    if (!result?.result) return [];
    const resultKeys = new Set(Object.keys(result.result));
    return $pluginsByType.visualizers.filter(v => {
      if (!v.requires || v.requires.length === 0) return true;
      return v.requires.every(req => resultKeys.has(req));
    });
  });

  async function onSelectPlugin() {
    if (!selectedPluginId) { schema = null; return; }
    try {
      const s = await fetchPluginSchema(selectedPluginId);
      schema = s.parameters || s;
      configValues = {};
      calibrated = false;
    } catch (e) {
      error = e.message || 'Failed to load plugin schema';
    }
  }

  function onTextSizeChange(size, wordCount) {
    currentTextSize = size;
    calibrated = false;
  }

  async function calibrateParams() {
    if (!selectedPluginId) return;
    calibrating = true;
    try {
      const res = await resolveConfig(selectedPluginId, currentTextSize);
      configValues = { ...configValues, ...res.resolved_config };
      calibrated = true;
    } catch (e) {
      error = 'Calibration failed';
    } finally {
      calibrating = false;
    }
  }

  async function runAnalysis() {
    if (!selectedPluginId || !text.trim()) return;
    loading = true;
    error = '';
    result = null;
    vizResult = null;
    startTimer('Analyzing text...');
    try {
      result = await analyze(selectedPluginId, text, configValues);
      vizPluginId = '';
    } catch (e) {
      error = typeof e.message === 'string' ? e.message : JSON.stringify(e.message);
    } finally {
      stopTimer();
      loading = false;
    }
  }

  async function runVisualization() {
    if (!vizPluginId || !result?.result) return;
    vizLoading = true;
    startTimer('Generating visualization...');
    try {
      vizResult = await visualize(vizPluginId, result.result, {}, 'png');
    } catch (e) {
      error = e.message || 'Visualization failed';
    } finally {
      stopTimer();
      vizLoading = false;
    }
  }

  const hasCalibration = $derived(
    schema ? Object.values(schema).some(s => s.text_size_adjustments) : false
  );
</script>

<div class="analyze-page">
  <header class="page-header">
    <h1 class="page-title">Analyze</h1>
    <p class="page-desc">Run an analyzer plugin on your text</p>
  </header>

  <div class="two-col" class:has-result={!!result}>
    <!-- Left: Input -->
    <div class="col-input">
      <div class="section">
        <label class="label" for="plugin-select">Plugin</label>
        <div class="select-wrapper">
          <select
            id="plugin-select"
            class="select"
            bind:value={selectedPluginId}
            onchange={onSelectPlugin}
          >
            <option value="">Select a plugin...</option>
            {#each $pluginsByType.analyzers as p}
              <option value={p.id}>{p.name}</option>
            {/each}
          </select>
          <span class="select-chevron">&#9662;</span>
        </div>
      </div>

      {#if schema}
        <div class="section" style="animation: fadeUp 0.3s ease">
          <label class="label" for="text-input">Text</label>
          <TextInput bind:value={text} id="text-input" {onTextSizeChange} />
        </div>

        <div class="section" style="animation: fadeUp 0.3s ease 0.05s backwards">
          <div class="params-header">
            <ParamForm parameters={schema} bind:values={configValues} />
            {#if hasCalibration && text.trim()}
              <button
                class="calibrate-btn"
                class:calibrated
                onclick={calibrateParams}
                disabled={calibrating}
              >
                {#if calibrating}
                  <span class="cal-spinner"></span>
                {:else if calibrated}
                  <span class="cal-check">&#10003;</span>
                {/if}
                {calibrated ? `Calibrated for ${currentTextSize}` : `Auto-calibrate for ${currentTextSize} text`}
              </button>
            {/if}
          </div>
        </div>

        <div class="action-bar" style="animation: fadeUp 0.3s ease 0.1s backwards">
          <button
            class="run-btn"
            onclick={runAnalysis}
            disabled={loading || !text.trim()}
          >
            {#if loading}
              <span class="spinner"></span> Analyzing...
            {:else}
              Run Analysis
              <span class="run-key">&#9166;</span>
            {/if}
          </button>
        </div>
      {/if}

      {#if loadingStatus}
        <div class="progress-bar" style="animation: fadeUp 0.2s ease">
          <div class="progress-track">
            <div class="progress-fill"></div>
          </div>
          <div class="progress-info">
            <span class="progress-status">{loadingStatus}</span>
            <span class="progress-time">{loadingElapsed}s</span>
          </div>
        </div>
      {/if}

      {#if error}
        <div class="error-msg" style="animation: fadeUp 0.2s ease">{error}</div>
      {/if}
    </div>

    <!-- Right: Results -->
    {#if result}
      <div class="col-result" style="animation: fadeUp 0.35s ease">
        <div class="result-panel">
          <div class="result-header">
            <h2 class="result-title">Result</h2>
            <span class="result-meta">{result.plugin_id}</span>
          </div>
          <div class="result-body">
            <ResultView {result} />
          </div>

          {#if compatibleVisualizers.length > 0}
            <div class="viz-section">
              <h3 class="viz-title">Visualize</h3>
              <div class="viz-controls">
                <div class="select-wrapper viz-select">
                  <select class="select" bind:value={vizPluginId}>
                    <option value="">Select visualizer...</option>
                    {#each compatibleVisualizers as v}
                      <option value={v.id}>{v.name}</option>
                    {/each}
                  </select>
                  <span class="select-chevron">&#9662;</span>
                </div>
                <button
                  class="run-btn small"
                  onclick={runVisualization}
                  disabled={vizLoading || !vizPluginId}
                >
                  {vizLoading ? 'Generating...' : 'Generate'}
                </button>
              </div>
              {#if vizResult}
                <ResultView result={vizResult} />
              {/if}
            </div>
          {/if}
        </div>
      </div>
    {/if}
  </div>
</div>

<style>
  .analyze-page {
    max-width: 100%;
  }

  .page-header {
    margin-bottom: 36px;
  }

  .page-title {
    font-size: 1.65em;
    font-weight: 500;
    color: var(--text-primary);
    letter-spacing: -0.3px;
    margin-bottom: 4px;
  }

  .page-desc {
    color: var(--text-muted);
    font-size: 0.9em;
  }

  /* Two-column layout */
  .two-col {
    display: flex;
    gap: 32px;
    align-items: flex-start;
  }

  .col-input {
    flex: 1;
    min-width: 0;
    max-width: 720px;
  }

  .col-result {
    flex: 1;
    min-width: 0;
    max-width: 560px;
    position: sticky;
    top: 0;
  }

  /* When no result yet, input takes full width */
  .two-col:not(.has-result) .col-input {
    max-width: 720px;
  }

  .result-panel {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    overflow: hidden;
  }

  .result-header {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    padding: 18px 22px;
    border-bottom: 1px solid var(--border-subtle);
  }

  .result-title {
    font-size: 0.95em;
    font-weight: 600;
    color: var(--text-primary);
  }

  .result-meta {
    font-size: 0.72em;
    color: var(--text-muted);
    font-family: var(--font-mono);
    padding: 2px 8px;
    background: var(--bg-input);
    border-radius: 6px;
  }

  .result-body {
    padding: 22px;
    max-height: 60vh;
    overflow-y: auto;
  }

  .viz-section {
    padding: 18px 22px;
    border-top: 1px solid var(--border-subtle);
  }

  .viz-title {
    font-size: 0.74em;
    font-weight: 600;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 1.2px;
    margin-bottom: 12px;
  }

  .viz-controls {
    display: flex;
    gap: 10px;
    margin-bottom: 14px;
  }

  .viz-select {
    flex: 1;
  }

  /* Shared form styles */
  .section {
    margin-bottom: 24px;
  }

  .label {
    display: block;
    font-size: 0.78em;
    font-weight: 600;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 1.2px;
    margin-bottom: 8px;
  }

  .select-wrapper {
    position: relative;
  }

  .select {
    width: 100%;
    padding: 11px 36px 11px 14px;
    background: var(--bg-input);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    color: var(--text-primary);
    font-size: 0.9em;
    outline: none;
    transition: all var(--transition);
    appearance: none;
    cursor: pointer;
  }

  .select:focus {
    border-color: var(--border-focus);
    box-shadow: 0 0 0 3px var(--accent-dim);
  }

  .select-chevron {
    position: absolute;
    right: 14px;
    top: 50%;
    transform: translateY(-50%);
    color: var(--text-muted);
    font-size: 0.7em;
    pointer-events: none;
  }

  .params-header {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .calibrate-btn {
    align-self: flex-start;
    padding: 8px 16px;
    background: var(--bg-input);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    color: var(--text-secondary);
    font-size: 0.8em;
    transition: all var(--transition);
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .calibrate-btn:hover:not(:disabled) {
    border-color: var(--accent);
    color: var(--accent);
    background: var(--accent-dim);
  }

  .calibrate-btn.calibrated {
    border-color: var(--accent-green);
    color: var(--accent-green);
    background: var(--accent-green-dim);
  }

  .cal-spinner {
    width: 12px;
    height: 12px;
    border: 1.5px solid var(--border);
    border-top-color: var(--accent);
    border-radius: 50%;
    animation: spin 0.6s linear infinite;
  }

  .cal-check {
    font-size: 0.9em;
  }

  .action-bar {
    margin-bottom: 8px;
  }

  .run-btn {
    padding: 12px 28px;
    background: var(--accent);
    color: #fff;
    border: none;
    border-radius: var(--radius-sm);
    font-size: 0.9em;
    font-weight: 500;
    transition: all var(--transition);
    display: inline-flex;
    align-items: center;
    gap: 10px;
  }

  .run-btn:hover:not(:disabled) {
    background: var(--accent-hover);
    box-shadow: var(--shadow-glow);
  }

  .run-btn:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }

  .run-btn.small {
    padding: 9px 18px;
    font-size: 0.84em;
  }

  .run-key {
    font-size: 0.85em;
    opacity: 0.5;
  }

  .spinner {
    width: 14px;
    height: 14px;
    border: 2px solid rgba(255,255,255,0.25);
    border-top-color: #fff;
    border-radius: 50%;
    animation: spin 0.6s linear infinite;
  }

  .progress-bar {
    margin-top: 16px;
    padding: 14px 18px;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
  }

  .progress-track {
    height: 3px;
    background: var(--bg-input);
    border-radius: 2px;
    overflow: hidden;
    margin-bottom: 10px;
  }

  .progress-fill {
    height: 100%;
    width: 40%;
    background: var(--accent-gradient);
    border-radius: 2px;
    animation: progressSlide 1.5s ease-in-out infinite;
  }

  @keyframes progressSlide {
    0% { transform: translateX(-100%); }
    100% { transform: translateX(350%); }
  }

  .progress-info {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .progress-status {
    font-size: 0.8em;
    color: var(--text-secondary);
  }

  .progress-time {
    font-size: 0.74em;
    color: var(--text-muted);
    font-family: var(--font-mono);
  }

  .error-msg {
    margin-top: 16px;
    padding: 14px 18px;
    background: var(--error-bg);
    border: 1px solid rgba(240, 96, 96, 0.2);
    border-radius: var(--radius-sm);
    color: var(--text-primary);
    font-size: 0.85em;
  }

  /* Responsive: stack on narrow screens */
  @media (max-width: 900px) {
    .two-col {
      flex-direction: column;
    }

    .col-input, .col-result {
      max-width: 100%;
    }

    .col-result {
      position: static;
    }
  }
</style>
