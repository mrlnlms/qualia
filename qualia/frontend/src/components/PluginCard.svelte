<script>
  let { plugin, onUse } = $props();

  import { typeConfig } from '../lib/constants.js';

  const config = $derived(typeConfig[plugin.type] || typeConfig.analyzer);
</script>

<div class="card">
  <div class="card-header">
    <span class="type-badge" style:--tc={config.color} style:--tbg={config.bg}>
      {config.label}
    </span>
    <span class="version">{plugin.version}</span>
  </div>
  <h3 class="name">{plugin.name}</h3>
  <p class="description">{plugin.description}</p>
  <div class="card-footer">
    <div class="provides">
      {#each plugin.provides.slice(0, 3) as tag}
        <span class="tag">{tag}</span>
      {/each}
      {#if plugin.provides.length > 3}
        <span class="tag accent">+{plugin.provides.length - 3}</span>
      {/if}
    </div>
    {#if onUse}
      <button class="use-btn" onclick={() => onUse(plugin)}>
        Use
        <span class="use-arrow">&rarr;</span>
      </button>
    {/if}
  </div>
</div>

<style>
  .card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 22px;
    transition: all var(--transition);
    display: flex;
    flex-direction: column;
    gap: 12px;
    position: relative;
    overflow: hidden;
  }

  .card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--border), transparent);
    opacity: 0;
    transition: opacity var(--transition);
  }

  .card:hover {
    border-color: var(--border-focus);
    transform: translateY(-2px);
    box-shadow: var(--shadow);
  }

  .card:hover::before {
    opacity: 1;
    background: linear-gradient(90deg, transparent, var(--accent), transparent);
  }

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
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

  .version {
    font-size: 0.72em;
    color: var(--text-muted);
    font-family: var(--font-mono);
  }

  .name {
    font-size: 1.02em;
    font-weight: 600;
    color: var(--text-primary);
    letter-spacing: -0.2px;
  }

  .description {
    font-size: 0.85em;
    color: var(--text-secondary);
    line-height: 1.55;
    flex: 1;
  }

  .card-footer {
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    margin-top: 4px;
    gap: 12px;
  }

  .provides {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
  }

  .tag {
    font-size: 0.68em;
    padding: 2px 8px;
    background: var(--bg-input);
    border-radius: var(--radius);
    color: var(--text-muted);
    font-family: var(--font-mono);
  }

  .tag.accent {
    color: var(--accent);
    background: var(--accent-dim);
  }

  .use-btn {
    padding: 7px 16px;
    background: var(--accent-dim);
    color: var(--accent);
    border: 1px solid transparent;
    border-radius: var(--radius-sm);
    font-size: 0.8em;
    font-weight: 500;
    transition: all var(--transition);
    flex-shrink: 0;
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .use-arrow {
    transition: transform var(--transition);
    font-size: 0.9em;
  }

  .use-btn:hover {
    background: var(--accent);
    color: var(--bg-primary);
    border-color: var(--accent);
  }

  .use-btn:hover .use-arrow {
    transform: translateX(2px);
  }
</style>
