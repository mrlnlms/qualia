<script>
  import { plugins } from '../lib/stores.js';
  import { typeConfig } from '../lib/constants.js';

  let { open = false, onToggle = null, onAddPlugin = null } = $props();

  const grouped = $derived({
    analyzer: $plugins.filter(p => p.type === 'analyzer'),
    visualizer: $plugins.filter(p => p.type === 'visualizer'),
    document: $plugins.filter(p => p.type === 'document'),
  });

  const groups = $derived(
    Object.entries(grouped).filter(([, list]) => list.length > 0)
  );
</script>

<div class="palette" class:open>
  <button class="palette-toggle" onclick={() => onToggle?.()}>
    {open ? '×' : '+'}
  </button>

  {#if open}
    <div class="palette-body">
      <div class="palette-title">Add Node</div>
      {#each groups as [type, list]}
        {@const tc = typeConfig[type]}
        <div class="palette-group">
          <div class="group-label" style="color: {tc?.color}">{type}s</div>
          {#each list as plugin}
            <button class="palette-item" onclick={() => onAddPlugin?.(plugin)}>
              <span class="item-name">{plugin.name}</span>
              {#if plugin.provides?.length}
                <span class="item-tags">
                  {plugin.provides.join(', ')}
                </span>
              {/if}
            </button>
          {/each}
        </div>
      {/each}
    </div>
  {/if}
</div>

<style>
  .palette {
    position: absolute;
    left: 12px;
    top: 12px;
    z-index: 10;
  }

  .palette-toggle {
    width: 32px;
    height: 32px;
    border-radius: var(--radius);
    border: 1px solid var(--border);
    background: var(--bg-secondary);
    color: var(--text-secondary);
    font-size: 1.1em;
    font-family: var(--font-mono);
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all var(--transition);
  }

  .palette-toggle:hover {
    border-color: var(--accent);
    color: var(--accent);
  }

  .palette-body {
    margin-top: 6px;
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: var(--radius-lg);
    padding: 10px;
    width: 200px;
    max-height: 400px;
    overflow-y: auto;
    animation: fadeUp 0.15s ease;
    box-shadow: var(--shadow-lg);
  }

  .palette-title {
    font-size: 0.72em;
    font-family: var(--font-mono);
    color: var(--text-muted);
    margin-bottom: 8px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .palette-group {
    margin-bottom: 10px;
  }

  .palette-group:last-child {
    margin-bottom: 0;
  }

  .group-label {
    font-size: 0.68em;
    font-family: var(--font-mono);
    margin-bottom: 4px;
    text-transform: lowercase;
  }

  .palette-item {
    width: 100%;
    text-align: left;
    padding: 6px 8px;
    background: transparent;
    border: 1px solid transparent;
    border-radius: var(--radius);
    color: var(--text-primary);
    font-size: 0.78em;
    display: flex;
    flex-direction: column;
    gap: 2px;
    transition: all var(--transition);
  }

  .palette-item:hover {
    background: var(--bg-hover);
    border-color: var(--border);
  }

  .item-name {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .item-tags {
    font-size: 0.82em;
    font-family: var(--font-mono);
    color: var(--text-muted);
  }
</style>
