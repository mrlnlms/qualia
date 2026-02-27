<script>
  let { value = $bindable(''), placeholder = 'Paste or type your text here...', id = 'text-input', onTextSizeChange = null } = $props();

  const wordCount = $derived(
    value.trim() ? value.trim().split(/\s+/).length : 0
  );

  const textSize = $derived(
    wordCount <= 500 ? 'short' : wordCount <= 5000 ? 'medium' : 'long'
  );

  const sizeConfig = {
    short: { color: 'var(--accent-green)', label: 'short' },
    medium: { color: 'var(--accent)', label: 'medium' },
    long: { color: 'var(--warning)', label: 'long' },
  };

  // Notify parent of text size changes
  $effect(() => {
    if (onTextSizeChange && wordCount > 0) {
      onTextSizeChange(textSize, wordCount);
    }
  });
</script>

<div class="text-input-wrapper">
  <textarea
    bind:value
    {placeholder}
    class="textarea"
    rows="8"
    {id}
  ></textarea>
  <div class="status-bar">
    <div class="status-left">
      <span class="word-count">{wordCount.toLocaleString()} words</span>
    </div>
    {#if wordCount > 0}
      <span
        class="size-badge"
        style:--badge-color={sizeConfig[textSize].color}
      >
        <span class="size-dot"></span>
        {sizeConfig[textSize].label}
      </span>
    {/if}
  </div>
</div>

<style>
  .text-input-wrapper {
    display: flex;
    flex-direction: column;
    border: 1px solid var(--border);
    border-radius: var(--radius);
    overflow: hidden;
    transition: all var(--transition);
    background: var(--bg-input);
  }

  .text-input-wrapper:focus-within {
    border-color: var(--border-focus);
    box-shadow: 0 0 0 3px var(--accent-dim);
  }

  .textarea {
    width: 100%;
    padding: 18px;
    background: transparent;
    border: none;
    color: var(--text-primary);
    font-size: 0.9em;
    line-height: 1.75;
    resize: vertical;
    min-height: 180px;
    outline: none;
  }

  .textarea::placeholder {
    color: var(--text-muted);
    font-style: italic;
  }

  .status-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 18px;
    background: var(--bg-card);
    border-top: 1px solid var(--border-subtle);
  }

  .word-count {
    font-size: 0.74em;
    color: var(--text-muted);
    font-family: var(--font-mono);
  }

  .size-badge {
    font-size: 0.72em;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    color: var(--badge-color);
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .size-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--badge-color);
  }
</style>
