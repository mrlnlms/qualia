<script>
  import ParamForm from './ParamForm.svelte';
  import TextInput from './TextInput.svelte';
  import FileUpload from './FileUpload.svelte';
  import ResultView from './ResultView.svelte';
  import { typeConfig } from '../lib/constants.js';

  const AUDIO_ACCEPT = '.mp3,.mp4,.mpeg,.mpga,.m4a,.wav,.webm,.ogg,.opus,.flac';

  let {
    node,
    inputText = $bindable(''),
    inputFile = $bindable(null),
    onClose = null,
    onDelete = null,
  } = $props();

  const tc = $derived(node?.pluginType ? typeConfig[node.pluginType] : null);
</script>

{#if node}
  <div class="drawer">
    <div class="drawer-header">
      <div class="drawer-title-row">
        {#if node.nodeType === 'input'}
          <span class="drawer-badge input-badge">input</span>
          <span class="drawer-name">Input Node</span>
        {:else}
          {#if tc}
            <span class="drawer-badge" style="color: {tc.color}; background: {tc.bg};">{tc.label}</span>
          {/if}
          <span class="drawer-name">{node.pluginName || node.pluginId}</span>
        {/if}
        <button class="close-btn" onclick={() => onClose?.()}>×</button>
      </div>

      {#if node.nodeType === 'plugin'}
        {#if node.pluginProvides?.length}
          <div class="drawer-meta">
            <span class="meta-label">provides:</span>
            <span class="meta-value">{node.pluginProvides.join(', ')}</span>
          </div>
        {/if}
        {#if node.pluginRequires?.length}
          <div class="drawer-meta">
            <span class="meta-label">requires:</span>
            <span class="meta-value">{node.pluginRequires.join(', ')}</span>
          </div>
        {/if}
      {/if}
    </div>

    <div class="drawer-body">
      {#if node.nodeType === 'input'}
        <div class="input-toggle">
          <button
            class="toggle-btn"
            class:active={node.inputMode === 'text'}
            onclick={() => node.inputMode = 'text'}
          >Text</button>
          <button
            class="toggle-btn"
            class:active={node.inputMode === 'file'}
            onclick={() => node.inputMode = 'file'}
          >File</button>
        </div>

        {#if node.inputMode === 'text'}
          <TextInput bind:value={inputText} placeholder="Input text for the workflow..." />
        {:else}
          <FileUpload bind:file={inputFile} accept={AUDIO_ACCEPT} />
        {/if}
      {:else}
        {#if node.schema && Object.keys(node.schema).length > 0}
          <div class="drawer-section">
            <div class="section-label">Configuration</div>
            <ParamForm parameters={node.schema} bind:values={node.config} />
          </div>
        {/if}

        <button class="delete-btn" onclick={() => onDelete?.(node.id)}>
          Remove node
        </button>
      {/if}

      {#if node.result && node.status === 'done'}
        <div class="drawer-section result-section">
          <div class="section-label">Result</div>
          <ResultView result={node.result} />
        </div>
      {/if}

      {#if node.status === 'error' && node.result}
        <div class="drawer-error">
          {typeof node.result === 'string' ? node.result : JSON.stringify(node.result)}
        </div>
      {/if}
    </div>
  </div>
{/if}

<style>
  .drawer {
    position: absolute;
    right: 0;
    top: 0;
    bottom: 0;
    width: 320px;
    background: var(--bg-secondary);
    border-left: 1px solid var(--border);
    z-index: 10;
    display: flex;
    flex-direction: column;
    animation: slideIn 0.2s ease;
    overflow-y: auto;
  }

  @keyframes slideIn {
    from { transform: translateX(100%); }
    to { transform: translateX(0); }
  }

  .drawer-header {
    padding: 14px 14px 10px;
    border-bottom: 1px solid var(--border-subtle);
  }

  .drawer-title-row {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .drawer-badge {
    font-size: 0.6em;
    font-family: var(--font-mono);
    padding: 1px 5px;
    border-radius: 3px;
    flex-shrink: 0;
  }

  .input-badge {
    color: var(--text-muted);
    background: var(--bg-hover);
  }

  .drawer-name {
    font-size: 0.88em;
    font-weight: 500;
    color: var(--text-primary);
    flex: 1;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .close-btn {
    width: 24px;
    height: 24px;
    border: none;
    background: transparent;
    color: var(--text-muted);
    font-size: 1.1em;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: var(--radius);
    transition: all var(--transition);
    flex-shrink: 0;
  }

  .close-btn:hover {
    background: var(--bg-hover);
    color: var(--text-primary);
  }

  .drawer-meta {
    margin-top: 6px;
    font-size: 0.7em;
    font-family: var(--font-mono);
    display: flex;
    gap: 6px;
  }

  .meta-label { color: var(--text-muted); }
  .meta-value { color: var(--text-secondary); }

  .drawer-body {
    padding: 14px;
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 14px;
  }

  .input-toggle {
    display: flex;
    gap: 2px;
    background: var(--bg-input);
    border-radius: var(--radius);
    padding: 2px;
  }

  .toggle-btn {
    flex: 1;
    padding: 5px;
    border: none;
    background: transparent;
    color: var(--text-muted);
    font-size: 0.78em;
    font-family: var(--font-mono);
    border-radius: var(--radius-sm);
    transition: all var(--transition);
  }

  .toggle-btn.active {
    background: var(--bg-card);
    color: var(--text-primary);
    box-shadow: var(--shadow-sm);
  }

  .drawer-section {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .section-label {
    font-size: 0.68em;
    font-family: var(--font-mono);
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .result-section {
    border-top: 1px solid var(--border-subtle);
    padding-top: 14px;
  }

  .delete-btn {
    padding: 6px 12px;
    background: transparent;
    border: 1px solid var(--error-dim);
    border-radius: var(--radius);
    color: var(--error);
    font-size: 0.75em;
    font-family: var(--font-mono);
    transition: all var(--transition);
    align-self: flex-start;
  }

  .delete-btn:hover {
    background: var(--error-bg);
    border-color: var(--error);
  }

  .drawer-error {
    padding: 10px;
    background: var(--error-bg);
    border-left: 2px solid var(--error);
    font-size: 0.78em;
    color: var(--text-primary);
    word-break: break-word;
  }
</style>
