<script>
  import { onMount } from 'svelte';
  import { get } from 'svelte/store';
  import { pluginsByType, pendingPluginId } from '../lib/stores.js';
  import { fetchPluginSchema, transcribe } from '../lib/api.js';
  import ParamForm from '../components/ParamForm.svelte';
  import FileUpload from '../components/FileUpload.svelte';

  const AUDIO_ACCEPT = '.mp3,.mp4,.mpeg,.mpga,.m4a,.wav,.webm,.ogg,.opus,.flac';

  let selectedPluginId = $state('');

  onMount(() => {
    const pending = get(pendingPluginId);
    if (pending) {
      selectedPluginId = pending;
      pendingPluginId.set(null);
      onSelectPlugin();
    }
  });
  let schema = $state(null);
  let configValues = $state({});
  let file = $state(null);
  let loading = $state(false);
  let loadingStatus = $state('');
  let loadingElapsed = $state(0);
  let loadingTimer = null;
  let result = $state(null);
  let error = $state('');
  let copied = $state(false);

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

  async function onSelectPlugin() {
    if (!selectedPluginId) { schema = null; return; }
    try {
      const s = await fetchPluginSchema(selectedPluginId);
      schema = s.parameters || s;
      configValues = {};
    } catch (e) {
      error = e.message || 'Failed to load plugin schema';
    }
  }

  async function runTranscription() {
    if (!selectedPluginId || !file) return;
    loading = true;
    error = '';
    result = null;
    startTimer('Uploading and transcribing...');
    try {
      result = await transcribe(selectedPluginId, file, configValues);
    } catch (e) {
      error = typeof e.message === 'string' ? e.message : JSON.stringify(e.message);
    } finally {
      stopTimer();
      loading = false;
    }
  }

  async function copyText() {
    if (result?.result?.transcription) {
      await navigator.clipboard.writeText(result.result.transcription);
      copied = true;
      setTimeout(() => copied = false, 2000);
    }
  }
</script>

<div class="transcribe-page">
  <header class="page-header">
    <h1 class="page-title">Transcribe</h1>
    <p class="page-desc">Transcribe audio or video files</p>
  </header>

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
        {#each $pluginsByType.document as p}
          <option value={p.id}>{p.name}</option>
        {/each}
      </select>
      <span class="select-chevron">&#9662;</span>
    </div>
  </div>

  {#if schema}
    <div class="section" style="animation: fadeUp 0.3s ease">
      <label class="label" for="file-upload">File</label>
      <FileUpload bind:file accept={AUDIO_ACCEPT} id="file-upload" />
    </div>

    <div class="section" style="animation: fadeUp 0.3s ease 0.05s backwards">
      <ParamForm parameters={schema} bind:values={configValues} />
    </div>

    <div class="action-bar" style="animation: fadeUp 0.3s ease 0.1s backwards">
      <button
        class="run-btn"
        onclick={runTranscription}
        disabled={loading || !file}
      >
        {#if loading}
          <span class="spinner"></span> Transcribing...
        {:else}
          Transcribe
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

  {#if result?.result}
    <div class="result-section" style="animation: fadeUp 0.35s ease">
      <div class="result-meta">
        {#if result.result.language}
          <span class="meta-tag">
            <span class="meta-label">Language</span>
            <span class="meta-value">{result.result.language}</span>
          </span>
        {/if}
        {#if result.result.duration}
          <span class="meta-tag">
            <span class="meta-label">Duration</span>
            <span class="meta-value">{result.result.duration.toFixed(1)}s</span>
          </span>
        {/if}
        {#if result.filename}
          <span class="meta-tag">
            <span class="meta-label">File</span>
            <span class="meta-value">{result.filename}</span>
          </span>
        {/if}
      </div>
      <div class="transcription-box">
        <div class="transcription-header">
          <span class="transcription-label">Transcription</span>
          <button class="copy-btn" class:copied onclick={copyText}>
            {copied ? 'Copied!' : 'Copy'}
          </button>
        </div>
        <textarea class="transcription-text" readonly>{result.result.transcription}</textarea>
      </div>
    </div>
  {/if}
</div>

<style>
  .transcribe-page {
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
    appearance: none;
    cursor: pointer;
    transition: all var(--transition);
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

  .result-section {
    margin-top: 36px;
    padding-top: 28px;
    border-top: 1px solid var(--border);
  }

  .result-meta {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
    margin-bottom: 18px;
  }

  .meta-tag {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 6px 14px;
    background: var(--bg-input);
    border-radius: var(--radius-sm);
  }

  .meta-label {
    font-size: 0.7em;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .meta-value {
    font-size: 0.82em;
    color: var(--text-primary);
    font-family: var(--font-mono);
    font-weight: 500;
  }

  .transcription-box {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    overflow: hidden;
  }

  .transcription-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 18px;
    border-bottom: 1px solid var(--border-subtle);
  }

  .transcription-label {
    font-size: 0.76em;
    font-weight: 600;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.8px;
  }

  .copy-btn {
    padding: 5px 14px;
    background: var(--bg-input);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    color: var(--text-secondary);
    font-size: 0.76em;
    font-family: var(--font-mono);
    transition: all var(--transition);
  }

  .copy-btn:hover {
    border-color: var(--accent);
    color: var(--accent);
  }

  .copy-btn.copied {
    border-color: var(--accent-green);
    color: var(--accent-green);
    background: var(--accent-green-dim);
  }

  .transcription-text {
    width: 100%;
    min-height: 220px;
    padding: 18px;
    background: transparent;
    border: none;
    color: var(--text-primary);
    font-size: 0.9em;
    line-height: 1.75;
    resize: vertical;
    outline: none;
  }
</style>
