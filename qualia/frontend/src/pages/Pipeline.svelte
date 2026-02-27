<script>
  import { plugins } from '../lib/stores.js';
  import { fetchPluginSchema } from '../lib/api.js';
  import ParamForm from '../components/ParamForm.svelte';
  import TextInput from '../components/TextInput.svelte';
  import ResultView from '../components/ResultView.svelte';

  let steps = $state([]);
  let text = $state('');
  let loading = $state(false);
  let results = $state(null);
  let error = $state('');

  const availablePlugins = $derived(
    $plugins.filter(p => p.type === 'analyzer' || p.type === 'document')
  );

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
    if (!text.trim() || steps.length === 0) return;
    loading = true;
    error = '';
    results = null;
    try {
      const pipelineSteps = steps
        .filter(s => s.pluginId)
        .map(s => ({ plugin_id: s.pluginId, config: s.config }));

      const res = await fetch('/pipeline', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, steps: pipelineSteps }),
      });
      if (!res.ok) throw await res.json();
      results = await res.json();
    } catch (e) {
      error = typeof e.message === 'string' ? e.message : JSON.stringify(e);
    } finally {
      loading = false;
    }
  }

  const validSteps = $derived(steps.filter(s => s.pluginId).length);
</script>

<div class="pipeline-page">
  <header class="page-header">
    <div>
      <h1 class="page-title">Pipeline</h1>
      <p class="page-desc">Chain multiple plugins in sequence</p>
    </div>
  </header>

  <div class="section">
    <label class="label" for="pipeline-text">Input Text</label>
    <TextInput bind:value={text} id="pipeline-text" placeholder="Text to process through the pipeline..." />
  </div>

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
                {#each availablePlugins as p}
                  <option value={p.id}>{p.name}</option>
                {/each}
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

  {#if steps.length > 0}
    <div class="action-bar">
      <button
        class="run-btn"
        onclick={runPipeline}
        disabled={loading || !text.trim() || validSteps === 0}
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
          <ResultView result={{ result: stepResult.result || stepResult }} />
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
