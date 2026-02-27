<script>
  import { plugins } from '../lib/stores.js';
  import { fetchPluginSchema, executePipeline } from '../lib/api.js';
  import ParamForm from '../components/ParamForm.svelte';
  import TextInput from '../components/TextInput.svelte';
  import FileUpload from '../components/FileUpload.svelte';
  import ResultView from '../components/ResultView.svelte';

  const AUDIO_ACCEPT = '.mp3,.mp4,.mpeg,.mpga,.m4a,.wav,.webm,.ogg,.opus,.flac';

  let steps = $state([]);
  let text = $state('');
  let file = $state(null);
  let loading = $state(false);
  let loadingElapsed = $state(0);
  let loadingTimer = null;
  let results = $state(null);
  let error = $state('');

  const availablePlugins = $derived(
    $plugins.filter(p => p.type === 'analyzer' || p.type === 'document' || p.type === 'visualizer')
  );

  // Determine if the first step is a document plugin (file input needed)
  const firstStepType = $derived.by(() => {
    if (steps.length === 0 || !steps[0].pluginId) return null;
    const p = $plugins.find(pl => pl.id === steps[0].pluginId);
    return p ? p.type : null;
  });

  const needsFile = $derived(firstStepType === 'document');

  function startTimer() {
    loadingElapsed = 0;
    loadingTimer = setInterval(() => loadingElapsed++, 1000);
  }
  function stopTimer() {
    clearInterval(loadingTimer);
    loadingTimer = null;
    loadingElapsed = 0;
  }

  async function addStep() {
    steps = [...steps, { id: crypto.randomUUID(), pluginId: '', schema: null, config: {} }];
  }

  function removeStep(id) {
    steps = steps.filter(s => s.id !== id);
  }

  function moveStep(idx, dir) {
    const arr = [...steps];
    const target = idx + dir;
    if (target < 0 || target >= arr.length) return;
    [arr[idx], arr[target]] = [arr[target], arr[idx]];
    steps = arr;
  }

  async function onPluginChange(step) {
    if (!step.pluginId) { step.schema = null; step.config = {}; return; }
    try {
      const s = await fetchPluginSchema(step.pluginId);
      step.schema = s.parameters || s;
      step.config = {};
    } catch (e) {
      error = e.message || 'Failed to load schema';
    }
  }

  async function runPipeline() {
    const hasInput = needsFile ? !!file : !!text.trim();
    if (!hasInput || validSteps === 0) return;

    loading = true;
    error = '';
    results = null;
    startTimer();

    try {
      const pipelineSteps = steps
        .filter(s => s.pluginId)
        .map(s => ({ plugin_id: s.pluginId, config: s.config }));

      results = await executePipeline(pipelineSteps, {
        text: needsFile ? undefined : text,
        file: needsFile ? file : undefined,
      });
    } catch (e) {
      error = typeof e.message === 'string' ? e.message : JSON.stringify(e);
    } finally {
      stopTimer();
      loading = false;
    }
  }

  const validSteps = $derived(steps.filter(s => s.pluginId).length);

  function fmtTime(s) {
    const m = Math.floor(s / 60);
    const sec = s % 60;
    return m > 0 ? `${m}m ${sec}s` : `${sec}s`;
  }
</script>

<div class="pipeline-page">
  <header class="page-header">
    <div>
      <h1 class="page-title">Pipeline</h1>
      <p class="page-desc">Chain multiple plugins in sequence</p>
    </div>
  </header>

  <!-- Steps come first so user picks plugins before input -->
  <div class="steps-section">
    <div class="steps-header">
      <h3 class="steps-title">Steps</h3>
      <span class="steps-count">{validSteps} of {steps.length}</span>
    </div>

    {#if steps.length === 0}
      <div class="empty-state">
        <p class="empty-text">No steps added yet. Add a plugin to start building your pipeline.</p>
      </div>
    {/if}

    <div class="steps-list">
      {#each steps as step, i (step.id)}
        <div class="step-card" style="animation: fadeUp 0.25s ease">
          <div class="step-header">
            <div class="step-number">{i + 1}</div>
            <div class="select-wrapper step-select">
              <select
                class="select"
                bind:value={step.pluginId}
                onchange={() => onPluginChange(step)}
              >
                <option value="">Select plugin...</option>
                <optgroup label="Analyzers">
                  {#each availablePlugins.filter(p => p.type === 'analyzer') as p}
                    <option value={p.id}>{p.name}</option>
                  {/each}
                </optgroup>
                <optgroup label="Visualizers">
                  {#each availablePlugins.filter(p => p.type === 'visualizer') as p}
                    <option value={p.id}>{p.name}</option>
                  {/each}
                </optgroup>
                <optgroup label="Document">
                  {#each availablePlugins.filter(p => p.type === 'document') as p}
                    <option value={p.id}>{p.name}</option>
                  {/each}
                </optgroup>
              </select>
              <span class="select-chevron">&#9662;</span>
            </div>
            <div class="step-actions">
              <button class="step-btn" onclick={() => moveStep(i, -1)} disabled={i === 0}>&#9650;</button>
              <button class="step-btn" onclick={() => moveStep(i, 1)} disabled={i === steps.length - 1}>&#9660;</button>
              <button class="step-btn remove" onclick={() => removeStep(step.id)}>&times;</button>
            </div>
          </div>
          {#if step.schema}
            <div class="step-params">
              <ParamForm parameters={step.schema} bind:values={step.config} />
            </div>
          {/if}
          {#if i < steps.length - 1}
            <div class="step-connector">
              <span class="connector-line"></span>
              <span class="connector-arrow">&#9660;</span>
              <span class="connector-line"></span>
            </div>
          {/if}
        </div>
      {/each}
    </div>

    <button class="add-step-btn" onclick={addStep}>
      <span class="add-icon">+</span>
      Add Step
    </button>
  </div>

  <!-- Dynamic input: shown after steps are configured -->
  {#if validSteps > 0}
    <div class="section input-section" style="animation: fadeUp 0.25s ease">
      <div class="input-label-row">
        {#if needsFile}
          <label class="label">Input File</label>
          <span class="input-hint">Step 1 is a document plugin — upload a file</span>
        {:else}
          <label class="label" for="pipeline-text">Input Text</label>
          <span class="input-hint">Text will flow through all steps</span>
        {/if}
      </div>
      {#if needsFile}
        <FileUpload bind:file accept={AUDIO_ACCEPT} />
      {:else}
        <TextInput bind:value={text} id="pipeline-text" placeholder="Text to process through the pipeline..." />
      {/if}
    </div>
  {/if}

  {#if steps.length > 0}
    <div class="action-bar">
      <button
        class="run-btn"
        onclick={runPipeline}
        disabled={loading || (needsFile ? !file : !text.trim()) || validSteps === 0}
      >
        {#if loading}
          <span class="spinner"></span> Running pipeline...
        {:else}
          Run Pipeline
          <span class="step-badge">{validSteps} steps</span>
        {/if}
      </button>
    </div>
  {/if}

  {#if loading}
    <div class="progress-section" style="animation: fadeUp 0.2s ease">
      <div class="progress-bar-track">
        <div class="progress-bar-fill"></div>
      </div>
      <span class="progress-time">{fmtTime(loadingElapsed)}</span>
    </div>
  {/if}

  {#if error}
    <div class="error-msg" style="animation: fadeUp 0.2s ease">{error}</div>
  {/if}

  {#if results}
    <div class="results-section" style="animation: fadeUp 0.35s ease">
      <div class="results-header">
        <h2 class="results-title">Pipeline Results</h2>
        <span class="results-meta">{results.steps_executed} steps executed</span>
      </div>
      {#each results.results as stepResult, i}
        <div class="result-step" style="animation-delay: {i * 100}ms">
          <div class="result-step-header">
            <span class="result-step-num">{i + 1}</span>
            <span class="result-step-plugin">{stepResult.plugin_id || `Step ${i + 1}`}</span>
          </div>
          <ResultView result={stepResult.result || stepResult} />
        </div>
      {/each}
    </div>
  {/if}
</div>

<style>
  .pipeline-page {
    max-width: 820px;
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

  .section {
    margin-bottom: 28px;
  }

  .input-section {
    padding: 20px;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
  }

  .input-label-row {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    margin-bottom: 8px;
  }

  .input-label-row .label {
    margin-bottom: 0;
  }

  .input-hint {
    font-size: 0.72em;
    color: var(--text-muted);
    font-style: italic;
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

  .steps-section {
    margin-bottom: 28px;
  }

  .steps-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 16px;
  }

  .steps-title {
    font-size: 0.78em;
    font-weight: 600;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 1.2px;
  }

  .steps-count {
    font-size: 0.68em;
    color: var(--text-muted);
    font-family: var(--font-mono);
    background: var(--bg-input);
    padding: 2px 8px;
    border-radius: 10px;
  }

  .empty-state {
    padding: 32px;
    text-align: center;
    border: 1.5px dashed var(--border);
    border-radius: var(--radius);
    margin-bottom: 16px;
  }

  .empty-text {
    font-size: 0.88em;
    color: var(--text-muted);
  }

  .steps-list {
    display: flex;
    flex-direction: column;
    gap: 0;
    margin-bottom: 16px;
  }

  .step-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    overflow: hidden;
    margin-bottom: 4px;
  }

  .step-header {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 14px 16px;
  }

  .step-number {
    width: 28px;
    height: 28px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--accent-dim);
    color: var(--accent);
    border-radius: 8px;
    font-size: 0.76em;
    font-weight: 600;
    font-family: var(--font-mono);
    flex-shrink: 0;
  }

  .select-wrapper {
    position: relative;
    flex: 1;
  }

  .select {
    width: 100%;
    padding: 9px 32px 9px 12px;
    background: var(--bg-input);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    color: var(--text-primary);
    font-size: 0.88em;
    outline: none;
    appearance: none;
    cursor: pointer;
    transition: all var(--transition);
  }

  .select:focus {
    border-color: var(--border-focus);
  }

  .select-chevron {
    position: absolute;
    right: 12px;
    top: 50%;
    transform: translateY(-50%);
    color: var(--text-muted);
    font-size: 0.7em;
    pointer-events: none;
  }

  .step-actions {
    display: flex;
    gap: 4px;
    flex-shrink: 0;
  }

  .step-btn {
    width: 28px;
    height: 28px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--bg-input);
    border: 1px solid var(--border);
    border-radius: 6px;
    color: var(--text-muted);
    font-size: 0.7em;
    transition: all var(--transition);
  }

  .step-btn:hover:not(:disabled) {
    border-color: var(--accent);
    color: var(--accent);
  }

  .step-btn:disabled {
    opacity: 0.3;
    cursor: not-allowed;
  }

  .step-btn.remove:hover:not(:disabled) {
    border-color: var(--error);
    color: var(--error);
    background: var(--error-bg);
  }

  .step-params {
    padding: 4px 16px 16px;
    border-top: 1px solid var(--border-subtle);
  }

  .step-connector {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    padding: 4px 0;
    color: var(--text-muted);
    font-size: 0.7em;
  }

  .connector-line {
    flex: 1;
    height: 1px;
    background: var(--border-subtle);
  }

  .add-step-btn {
    width: 100%;
    padding: 12px;
    background: transparent;
    border: 1.5px dashed var(--border);
    border-radius: var(--radius);
    color: var(--text-muted);
    font-size: 0.88em;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    transition: all var(--transition);
  }

  .add-step-btn:hover {
    border-color: var(--accent);
    color: var(--accent);
    background: var(--accent-dim);
  }

  .add-icon {
    font-size: 1.2em;
    line-height: 1;
  }

  .action-bar {
    margin-bottom: 16px;
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

  .step-badge {
    font-size: 0.78em;
    padding: 2px 8px;
    background: rgba(255,255,255,0.15);
    border-radius: 10px;
    font-family: var(--font-mono);
  }

  .spinner {
    width: 14px;
    height: 14px;
    border: 2px solid rgba(255,255,255,0.25);
    border-top-color: #fff;
    border-radius: 50%;
    animation: spin 0.6s linear infinite;
  }

  .progress-section {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 16px;
  }

  .progress-bar-track {
    flex: 1;
    height: 4px;
    background: var(--bg-input);
    border-radius: 2px;
    overflow: hidden;
  }

  .progress-bar-fill {
    height: 100%;
    width: 30%;
    background: var(--accent);
    border-radius: 2px;
    animation: indeterminate 1.5s ease-in-out infinite;
  }

  @keyframes indeterminate {
    0%   { width: 0%; margin-left: 0; }
    50%  { width: 40%; margin-left: 30%; }
    100% { width: 0%; margin-left: 100%; }
  }

  .progress-time {
    font-size: 0.74em;
    color: var(--text-muted);
    font-family: var(--font-mono);
    min-width: 40px;
    text-align: right;
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

  .results-section {
    margin-top: 36px;
    padding-top: 28px;
    border-top: 1px solid var(--border);
  }

  .results-header {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    margin-bottom: 20px;
  }

  .results-title {
    font-size: 1.05em;
    font-weight: 600;
    color: var(--text-primary);
  }

  .results-meta {
    font-size: 0.74em;
    color: var(--text-muted);
    font-family: var(--font-mono);
  }

  .result-step {
    margin-bottom: 20px;
    animation: fadeUp 0.3s ease backwards;
  }

  .result-step-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 12px;
  }

  .result-step-num {
    width: 24px;
    height: 24px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--accent-dim);
    color: var(--accent);
    border-radius: 6px;
    font-size: 0.72em;
    font-weight: 600;
    font-family: var(--font-mono);
  }

  .result-step-plugin {
    font-size: 0.82em;
    color: var(--text-secondary);
    font-family: var(--font-mono);
  }
</style>
