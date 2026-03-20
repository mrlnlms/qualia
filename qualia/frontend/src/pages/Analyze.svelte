<script>
  import { onMount, onDestroy } from 'svelte';
  import { plugins, pluginsByType, navigate } from '../lib/stores.js';
  import { fetchPluginSchema, analyze, visualize, resolveConfig } from '../lib/api.js';
  import ParamForm from '../components/ParamForm.svelte';
  import TextInput from '../components/TextInput.svelte';
  import ResultView from '../components/ResultView.svelte';
  import { typeConfig } from '../lib/constants.js';

  let { pluginId = null } = $props();

  const plugin = $derived($plugins.find(p => p.id === pluginId) || null);

  let schema = $state(null);
  let configValues = $state({});
  let text = $state('');
  let loading = $state(false);
  let loadingStatus = $state('');
  let loadingElapsed = $state(0);
  let loadingTimer = null;
  let result = $state(null);
  let error = $state('');
  let currentTextSize = $state('medium');
  let calibrating = $state(false);
  let calibrated = $state(false);
  let paramsOpen = $state(false);

  let vizPluginId = $state('');
  let vizLoading = $state(false);
  let vizResult = $state(null);

  const tconf = $derived(plugin ? (typeConfig[plugin.type] || typeConfig.analyzer) : typeConfig.analyzer);

  const compatibleVisualizers = $derived.by(() => {
    if (!result?.result) return [];
    const resultKeys = new Set(Object.keys(result.result));
    return $pluginsByType.visualizers.filter(v => {
      if (!v.requires || v.requires.length === 0) return true;
      return v.requires.every(req => resultKeys.has(req));
    });
  });

  onMount(async () => {
    if (!pluginId) return;
    try {
      const s = await fetchPluginSchema(pluginId);
      schema = s.parameters || s;
    } catch (e) {
      error = e.message || 'Failed to load plugin schema';
    }
  });

  onDestroy(() => { if (loadingTimer) clearInterval(loadingTimer); });

  function onTextSizeChange(size) {
    currentTextSize = size;
    calibrated = false;
  }

  async function calibrateParams() {
    if (!pluginId) return;
    calibrating = true;
    try {
      const res = await resolveConfig(pluginId, currentTextSize);
      configValues = { ...configValues, ...res.resolved_config };
      calibrated = true;
    } catch (e) {
      error = 'Calibration failed';
    } finally {
      calibrating = false;
    }
  }

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

  async function runAnalysis() {
    if (!pluginId || !text.trim()) return;
    loading = true;
    error = '';
    result = null;
    vizResult = null;
    startTimer('Analyzing...');
    try {
      result = await analyze(pluginId, text, configValues);
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
    startTimer('Visualizing...');
    try {
      vizResult = await visualize(vizPluginId, result.result, {}, 'html');
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

<div class="page">
  {#if !pluginId}
    <!-- Plugin picker — no specific plugin selected -->
    <div class="picker">
      <div class="picker-hero">
        <svg class="picker-illus" width="200" height="120" viewBox="0 0 200 120" fill="none">
          <rect x="20" y="10" width="72" height="90" rx="4" stroke="var(--accent)" stroke-width="1.5" fill="var(--bg-card)"/>
          <line x1="32" y1="26" x2="80" y2="26" stroke="var(--accent)" stroke-width="1" opacity="0.2"/>
          <line x1="32" y1="34" x2="74" y2="34" stroke="var(--accent)" stroke-width="1" opacity="0.2"/>
          <line x1="32" y1="42" x2="78" y2="42" stroke="var(--accent)" stroke-width="1" opacity="0.2"/>
          <line x1="32" y1="50" x2="66" y2="50" stroke="var(--accent)" stroke-width="1" opacity="0.2"/>
          <line x1="32" y1="58" x2="72" y2="58" stroke="var(--accent)" stroke-width="1" opacity="0.2"/>
          <line x1="32" y1="66" x2="62" y2="66" stroke="var(--accent)" stroke-width="1" opacity="0.2"/>
          <line x1="32" y1="74" x2="80" y2="74" stroke="var(--accent)" stroke-width="1" opacity="0.2"/>
          <rect x="32" y="32" width="22" height="5" rx="1" fill="var(--accent)" opacity="0.12"/>
          <rect x="50" y="56" width="26" height="5" rx="1" fill="var(--accent)" opacity="0.12"/>
          <rect x="32" y="72" width="16" height="5" rx="1" fill="var(--accent)" opacity="0.12"/>
          <path d="M100 55 L118 55" stroke="var(--border)" stroke-width="1.5"/>
          <polygon points="116,50 126,55 116,60" fill="var(--border)"/>
          <rect x="134" y="20" width="48" height="68" rx="4" stroke="var(--accent)" stroke-width="1.5" fill="var(--accent-dim)"/>
          <rect x="142" y="66" width="8" height="14" rx="1.5" fill="var(--accent)" opacity="0.5"/>
          <rect x="154" y="52" width="8" height="28" rx="1.5" fill="var(--accent)" opacity="0.7"/>
          <rect x="166" y="58" width="8" height="22" rx="1.5" fill="var(--accent)" opacity="0.4"/>
          <circle cx="146" cy="36" r="2" fill="var(--accent)" opacity="0.4"/>
          <circle cx="158" cy="36" r="2" fill="var(--accent)" opacity="0.6"/>
          <circle cx="170" cy="36" r="2" fill="var(--accent)" opacity="0.3"/>
        </svg>
        <h1 class="picker-title">Analyze</h1>
        <p class="picker-desc">
          Run qualitative analysis on your text — extract frequencies, patterns, and structural insights.
        </p>
        <div class="picker-features">
          <span class="picker-feat">
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><circle cx="6" cy="6" r="4" stroke="currentColor" stroke-width="1.2"/><path d="M9 9l3 3" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/></svg>
            Paste text and run
          </span>
          <span class="picker-feat">
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><rect x="1" y="8" width="3" height="4" rx="0.5" fill="currentColor" opacity="0.5"/><rect x="5.5" y="5" width="3" height="7" rx="0.5" fill="currentColor" opacity="0.7"/><rect x="10" y="2" width="3" height="10" rx="0.5" fill="currentColor" opacity="0.4"/></svg>
            Auto-calibrate &amp; visualize
          </span>
        </div>
      </div>
      <div class="picker-grid">
        {#each $pluginsByType.analyzers as p, i}
          <button class="picker-card" style="animation-delay: {i * 50}ms" onclick={() => navigate('analyze', p.id)}>
            <span class="pc-name">{p.name}</span>
            <span class="pc-desc">{p.description}</span>
            <div class="pc-tags">
              {#each p.provides.slice(0, 4) as tag}
                <span class="pc-tag">{tag}</span>
              {/each}
            </div>
          </button>
        {/each}
      </div>
    </div>
  {:else if plugin}
    <!-- Plugin page -->
    <div class="two-col" class:has-result={!!result}>
      <div class="col-input">
        <!-- Plugin identity -->
        <div class="plugin-hero" class:compact={!!result}>
          <button class="back-link" onclick={() => navigate('analyze')}>
            &larr; all analyzers
          </button>
          <div class="plugin-header">
            <span class="type-badge" style:--tc={tconf.color} style:--tbg={tconf.bg}>{tconf.label}</span>
            <span class="plugin-version">{plugin.version}</span>
          </div>
          <h1 class="plugin-name">{plugin.name}</h1>
          {#if !result}
            <p class="plugin-desc">{plugin.description}</p>
            <div class="plugin-provides">
              {#each plugin.provides as tag}
                <span class="provide-tag">{tag}</span>
              {/each}
            </div>
          {/if}
        </div>

        <!-- Controls -->
        {#if schema}
          <div class="field">
            <label class="field-label" for="text-input">text</label>
            <TextInput bind:value={text} id="text-input" {onTextSizeChange} />
          </div>

          <div class="action-row">
            <button class="run-btn" onclick={runAnalysis} disabled={loading || !text.trim()}>
              {#if loading}
                <span class="spinner"></span> analyzing
              {:else}
                run analysis
              {/if}
            </button>
            <button class="cfg-btn" class:active={paramsOpen} onclick={() => paramsOpen = !paramsOpen} title="Parameters">
              <svg width="15" height="15" viewBox="0 0 15 15" fill="none">
                <path d="M7.5 9.5a2 2 0 1 0 0-4 2 2 0 0 0 0 4z" stroke="currentColor" stroke-width="1.1"/>
                <path d="M12.3 9.2l.8 1.3-1.2 1.2-1.3-.8a4.2 4.2 0 0 1-1.1.5V13H8v-1.6a4.2 4.2 0 0 1-1.1-.5l-1.3.8L4.4 10.5l.8-1.3a4.2 4.2 0 0 1 0-1.4l-.8-1.3L5.6 5.3l1.3.8a4.2 4.2 0 0 1 1.1-.5V4h1.5v1.6c.4.1.8.3 1.1.5l1.3-.8 1.2 1.2-.8 1.3a4.2 4.2 0 0 1 0 1.4z" stroke="currentColor" stroke-width="1.1" stroke-linejoin="round"/>
              </svg>
            </button>
          </div>

          {#if paramsOpen}
            <div class="params-panel">
              <ParamForm parameters={schema} bind:values={configValues} />
              {#if hasCalibration && text.trim()}
                <button class="cal-btn" class:done={calibrated} onclick={calibrateParams} disabled={calibrating}>
                  {#if calibrating}<span class="cal-spinner"></span>{:else if calibrated}&#10003;{/if}
                  {calibrated ? `calibrated (${currentTextSize})` : `auto-calibrate (${currentTextSize})`}
                </button>
              {/if}
            </div>
          {/if}
        {/if}

        {#if loadingStatus}
          <div class="progress">
            <div class="progress-track"><div class="progress-fill"></div></div>
            <div class="progress-info">
              <span class="progress-status">{loadingStatus}</span>
              <span class="progress-t">{loadingElapsed}s</span>
            </div>
          </div>
        {/if}

        {#if error}
          <div class="err">{error}</div>
        {/if}
      </div>

      {#if result}
        <div class="col-result">
          <div class="result-panel">
            <div class="result-bar">
              <span class="result-label">Result</span>
              <span class="result-id">{result.plugin_id}</span>
            </div>
            <div class="result-body">
              <ResultView {result} />
            </div>
            {#if compatibleVisualizers.length > 0}
              <div class="viz-section">
                <div class="viz-bar"><span class="viz-label">Visualize</span></div>
                <div class="viz-controls">
                  <select class="sel viz-sel" bind:value={vizPluginId}>
                    <option value="">-- select --</option>
                    {#each compatibleVisualizers as v}
                      <option value={v.id}>{v.name}</option>
                    {/each}
                  </select>
                  <button class="run-btn small" onclick={runVisualization} disabled={vizLoading || !vizPluginId}>
                    {vizLoading ? 'wait' : 'generate'}
                  </button>
                </div>
                {#if vizResult}
                  <div class="viz-result"><ResultView result={vizResult} /></div>
                {/if}
              </div>
            {/if}
          </div>
        </div>
      {/if}
    </div>
  {/if}
</div>

<style>
  .page { max-width: 100%; }

  /* === Picker (no plugin selected) === */
  .picker {
    max-width: 700px;
    margin: 0 auto;
    padding-top: 40px;
  }

  .picker-title {
    font-family: var(--font-serif);
    font-size: 1.6em;
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: 6px;
  }

  .picker-hero {
    text-align: center;
    margin-bottom: 32px;
    animation: fadeUp 0.35s ease backwards;
  }

  .picker-illus {
    margin-bottom: 20px;
    opacity: 0.8;
  }

  .picker-desc {
    font-size: 0.9em;
    color: var(--text-secondary);
    line-height: 1.6;
    margin-bottom: 14px;
    max-width: 400px;
    margin-left: auto;
    margin-right: auto;
  }

  .picker-features {
    display: flex;
    gap: 20px;
    justify-content: center;
    flex-wrap: wrap;
    margin-bottom: 8px;
  }

  .picker-feat {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-size: 0.78em;
    color: var(--text-muted);
  }

  .picker-feat svg {
    color: var(--accent);
    flex-shrink: 0;
  }

  .picker-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 12px;
  }

  .picker-card {
    text-align: left;
    padding: 18px 20px;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    cursor: pointer;
    transition: all var(--transition);
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .picker-card {
    animation: fadeUp 0.3s ease backwards;
  }

  .picker-card:hover {
    border-color: var(--accent);
    transform: translateY(-1px);
    box-shadow: var(--shadow-sm);
  }

  .pc-name {
    font-size: 0.95em;
    font-weight: 600;
    color: var(--text-primary);
  }

  .pc-desc {
    font-size: 0.82em;
    color: var(--text-secondary);
    line-height: 1.5;
  }

  .pc-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
    margin-top: 4px;
  }

  .pc-tag {
    font-size: 0.66em;
    font-family: var(--font-mono);
    padding: 2px 7px;
    background: var(--bg-input);
    border-radius: var(--radius);
    color: var(--text-muted);
  }

  /* === Plugin page === */
  .back-link {
    background: none;
    border: none;
    color: var(--text-muted);
    font-size: 0.78em;
    font-family: var(--font-mono);
    padding: 0;
    margin-bottom: 16px;
    cursor: pointer;
    transition: color var(--transition);
  }

  .back-link:hover {
    color: var(--accent);
  }

  .plugin-hero {
    margin-bottom: 24px;
    transition: margin 0.3s ease;
  }

  .plugin-hero.compact {
    margin-bottom: 20px;
  }

  .plugin-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 10px;
  }

  .type-badge {
    font-size: 0.66em;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: var(--tc);
    padding: 2px 8px;
    background: var(--tbg);
    border-radius: var(--radius);
  }

  .plugin-version {
    font-size: 0.7em;
    color: var(--text-muted);
    font-family: var(--font-mono);
  }

  .plugin-name {
    font-family: var(--font-serif);
    font-size: 1.5em;
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: 8px;
    letter-spacing: -0.3px;
  }

  .plugin-hero.compact .plugin-name {
    font-size: 1.2em;
    margin-bottom: 4px;
  }

  .plugin-desc {
    font-size: 0.88em;
    color: var(--text-secondary);
    line-height: 1.6;
    margin-bottom: 14px;
    max-width: 440px;
  }

  .plugin-provides {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
  }

  .provide-tag {
    font-size: 0.7em;
    font-family: var(--font-mono);
    padding: 3px 10px;
    background: var(--accent-dim);
    color: var(--accent);
    border-radius: var(--radius);
  }

  /* === Two column === */
  .two-col {
    display: flex;
    gap: 32px;
    align-items: flex-start;
  }

  .col-input {
    flex: 0 0 auto;
    width: 420px;
    min-width: 300px;
    max-width: 420px;
  }

  .col-result {
    flex: 1;
    min-width: 0;
    position: sticky;
    top: 0;
  }

  .two-col:not(.has-result) .col-input {
    max-width: 520px;
    width: auto;
    flex: 1;
  }

  /* Fields */
  .field { margin-bottom: 18px; }

  .field-label {
    display: block;
    font-size: 0.7em;
    font-family: var(--font-mono);
    color: var(--text-muted);
    letter-spacing: 0.5px;
    margin-bottom: 6px;
  }

  .sel {
    width: 100%;
    padding: 7px 10px;
    background: var(--bg-input);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    color: var(--text-primary);
    font-size: 0.82em;
    font-family: var(--font-mono);
    outline: none;
    appearance: none;
    cursor: pointer;
  }

  .sel:focus { border-color: var(--border-focus); }

  .action-row {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 16px;
  }

  .run-btn {
    padding: 7px 18px;
    background: transparent;
    color: var(--accent);
    border: 1px solid var(--accent);
    border-radius: var(--radius);
    font-size: 0.8em;
    font-family: var(--font-mono);
    transition: all var(--transition);
    display: inline-flex;
    align-items: center;
    gap: 8px;
  }

  .run-btn:hover:not(:disabled) { background: var(--accent); color: #fff; }
  .run-btn:disabled { opacity: 0.35; cursor: not-allowed; }
  .run-btn.small { padding: 5px 12px; font-size: 0.76em; }

  .cfg-btn {
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: transparent;
    border: 1px solid var(--border);
    border-radius: var(--radius);
    color: var(--text-muted);
    transition: all var(--transition);
  }

  .cfg-btn:hover { border-color: var(--text-muted); color: var(--text-secondary); }
  .cfg-btn.active { border-color: var(--accent); color: var(--accent); }

  .spinner {
    width: 12px; height: 12px;
    border: 1.5px solid var(--border);
    border-top-color: var(--accent);
    border-radius: 50%;
    animation: spin 0.6s linear infinite;
  }

  .params-panel {
    padding: 14px;
    border: 1px solid var(--border);
    border-radius: var(--radius);
    margin-bottom: 16px;
  }

  .cal-btn {
    margin-top: 10px;
    padding: 6px 12px;
    background: transparent;
    border: 1px solid var(--border);
    border-radius: var(--radius);
    color: var(--text-muted);
    font-size: 0.76em;
    font-family: var(--font-mono);
    display: flex;
    align-items: center;
    gap: 6px;
    transition: all var(--transition);
  }

  .cal-btn:hover:not(:disabled) { border-color: var(--text-muted); color: var(--text-secondary); }
  .cal-btn.done { border-color: var(--accent-green); color: var(--accent-green); }

  .cal-spinner {
    width: 10px; height: 10px;
    border: 1.5px solid var(--border);
    border-top-color: var(--accent);
    border-radius: 50%;
    animation: spin 0.6s linear infinite;
  }

  .progress {
    margin-top: 14px;
    padding: 10px 14px;
    border: 1px solid var(--border);
    border-radius: var(--radius);
  }

  .progress-track { height: 2px; background: var(--bg-input); overflow: hidden; margin-bottom: 8px; }

  .progress-fill {
    height: 100%; width: 40%;
    background: var(--accent);
    animation: progressSlide 1.5s ease-in-out infinite;
  }

  .progress-info { display: flex; justify-content: space-between; }
  .progress-status { font-size: 0.76em; font-family: var(--font-mono); color: var(--text-muted); }
  .progress-t { font-size: 0.7em; color: var(--text-muted); font-family: var(--font-mono); }

  .err {
    margin-top: 14px;
    padding: 10px 14px;
    background: var(--error-bg);
    border-left: 2px solid var(--error);
    color: var(--text-primary);
    font-size: 0.82em;
  }

  /* Result */
  .result-panel {
    border: 1px solid var(--border);
    border-radius: var(--radius);
    overflow: hidden;
  }

  .result-bar {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    padding: 10px 16px;
    background: var(--bg-secondary);
    border-bottom: 1px solid var(--border-subtle);
  }

  .result-label { font-size: 0.82em; font-weight: 500; color: var(--text-primary); }
  .result-id { font-size: 0.68em; font-family: var(--font-mono); color: var(--text-muted); }
  .result-body { padding: 16px; max-height: 65vh; overflow-y: auto; }

  .viz-section { border-top: 1px solid var(--border-subtle); }
  .viz-bar { padding: 10px 16px 0; }
  .viz-label { font-size: 0.72em; font-weight: 500; color: var(--text-muted); }
  .viz-controls { display: flex; gap: 8px; padding: 8px 16px 12px; }
  .viz-sel { flex: 1; }
  .viz-result { padding: 0 16px 16px; }

  @media (max-width: 900px) {
    .two-col { flex-direction: column; }
    .col-input, .col-result { max-width: 100%; width: 100%; }
    .col-result { position: static; }
  }
</style>
