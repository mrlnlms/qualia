<script>
  let { file = $bindable(null), accept = '*', maxSize = 25 * 1024 * 1024, id = 'file-upload' } = $props();

  let dragover = $state(false);
  let error = $state('');

  function handleFile(f) {
    error = '';
    if (f.size > maxSize) {
      error = `File too large (${(f.size / 1024 / 1024).toFixed(1)}MB). Max: ${(maxSize / 1024 / 1024).toFixed(0)}MB`;
      return;
    }
    file = f;
  }

  function onDrop(e) {
    e.preventDefault();
    dragover = false;
    if (e.dataTransfer.files.length) handleFile(e.dataTransfer.files[0]);
  }

  function onInput(e) {
    if (e.target.files.length) handleFile(e.target.files[0]);
  }

  function clear() {
    file = null;
    error = '';
  }

  function formatSize(bytes) {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
  }

  const ext = $derived(file ? file.name.split('.').pop()?.toUpperCase() : '');
</script>

<div class="upload-wrapper">
  {#if file}
    <div class="file-info">
      <div class="file-icon">{ext}</div>
      <div class="file-details">
        <span class="file-name">{file.name}</span>
        <span class="file-size">{formatSize(file.size)}</span>
      </div>
      <button class="clear-btn" onclick={clear}>&times;</button>
    </div>
  {:else}
    <div
      class="dropzone"
      class:dragover
      role="button"
      tabindex="0"
      ondragover={(e) => { e.preventDefault(); dragover = true; }}
      ondragleave={() => { dragover = false; }}
      ondrop={onDrop}
    >
      <div class="drop-visual">
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
          <polyline points="17 8 12 3 7 8" />
          <line x1="12" y1="3" x2="12" y2="15" />
        </svg>
      </div>
      <span class="drop-text">Drop file here or <strong>browse</strong></span>
      <span class="drop-hint">Max {(maxSize / 1024 / 1024).toFixed(0)}MB</span>
      <input type="file" {accept} {id} class="file-input" oninput={onInput} />
    </div>
  {/if}
  {#if error}
    <span class="error-text">{error}</span>
  {/if}
</div>

<style>
  .upload-wrapper {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .dropzone {
    position: relative;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 10px;
    padding: 44px 20px;
    border: 1.5px dashed var(--border);
    border-radius: var(--radius);
    background: var(--bg-input);
    transition: all var(--transition);
    cursor: pointer;
  }

  .dropzone:hover, .dropzone.dragover {
    border-color: var(--accent);
    background: var(--accent-dim);
  }

  .dropzone:hover .drop-visual, .dropzone.dragover .drop-visual {
    color: var(--accent);
    transform: translateY(-2px);
  }

  .drop-visual {
    color: var(--text-muted);
    transition: all var(--transition);
  }

  .drop-text {
    font-size: 0.88em;
    color: var(--text-secondary);
  }

  .drop-text strong {
    color: var(--accent);
    font-weight: 500;
  }

  .drop-hint {
    font-size: 0.72em;
    color: var(--text-muted);
    font-family: var(--font-mono);
  }

  .file-input {
    position: absolute;
    inset: 0;
    opacity: 0;
    cursor: pointer;
  }

  .file-info {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 14px 16px;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    animation: fadeUp 0.2s ease;
  }

  .file-icon {
    width: 40px;
    height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--accent-dim);
    color: var(--accent);
    border-radius: var(--radius-sm);
    font-size: 0.62em;
    font-weight: 600;
    font-family: var(--font-mono);
    letter-spacing: 0.5px;
    flex-shrink: 0;
  }

  .file-details {
    display: flex;
    flex-direction: column;
    gap: 2px;
    flex: 1;
    min-width: 0;
  }

  .file-name {
    font-size: 0.88em;
    color: var(--text-primary);
    font-weight: 500;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .file-size {
    font-size: 0.72em;
    color: var(--text-muted);
    font-family: var(--font-mono);
  }

  .clear-btn {
    background: none;
    border: none;
    color: var(--text-muted);
    font-size: 1.3em;
    padding: 4px 6px;
    transition: color var(--transition);
    line-height: 1;
    border-radius: 6px;
  }

  .clear-btn:hover {
    color: var(--error);
    background: var(--error-bg);
  }

  .error-text {
    font-size: 0.78em;
    color: var(--error);
  }
</style>
