<script>
  import { health, pluginsByType, navigate } from '../lib/stores.js';
  import PluginCard from '../components/PluginCard.svelte';
  import StatusDot from '../components/StatusDot.svelte';

  function usePlugin(plugin) {
    if (plugin.type === 'analyzer') navigate('analyze', plugin.id);
    else if (plugin.type === 'document') navigate('transcribe', plugin.id);
  }

  const sections = $derived([
    { key: 'analyzers', title: 'Analyzers', plugins: $pluginsByType.analyzers, showUse: true },
    { key: 'document', title: 'Document Processors', plugins: $pluginsByType.document, showUse: true },
    { key: 'visualizers', title: 'Visualizers', plugins: $pluginsByType.visualizers, showUse: false },
  ].filter(s => s.plugins.length > 0));
</script>

<div class="home">
  <header class="hero">
    <div class="hero-text">
      <h1 class="title">
        <span class="title-q">Q</span>ualia
      </h1>
      <p class="subtitle">Qualitative analysis engine</p>
    </div>
    <div class="health-pill">
      <StatusDot connected={!!$health} />
      {#if $health}
        <span class="health-text">
          <strong>{$health.plugins_loaded}</strong> plugins loaded
        </span>
      {:else}
        <span class="health-text disconnected">API not connected</span>
      {/if}
    </div>
  </header>

  {#each sections as section, si}
    <section class="section" style="animation-delay: {120 + si * 80}ms">
      <div class="section-header">
        <h2 class="section-title">{section.title}</h2>
        <span class="section-count">{section.plugins.length}</span>
      </div>
      <div class="plugin-grid">
        {#each section.plugins as plugin, pi}
          <div style="animation-delay: {200 + si * 80 + pi * 50}ms" class="card-wrapper">
            <PluginCard {plugin} onUse={section.showUse ? usePlugin : undefined} />
          </div>
        {/each}
      </div>
    </section>
  {/each}
</div>

<style>
  .home {
    max-width: 980px;
  }

  .hero {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 52px;
    animation: fadeUp 0.4s ease backwards;
  }

  .title {
    font-family: var(--font-serif);
    font-size: 2.2em;
    font-weight: 400;
    color: var(--text-primary);
    letter-spacing: -0.5px;
    margin-bottom: 4px;
    line-height: 1.1;
  }

  .title-q {
    font-weight: 600;
    background: var(--accent-gradient);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }

  .subtitle {
    font-size: 1em;
    color: var(--text-muted);
    font-weight: 400;
  }

  .health-pill {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 8px 16px;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 20px;
    animation: fadeIn 0.5s ease 0.2s backwards;
  }

  .health-text {
    font-size: 0.82em;
    color: var(--text-secondary);
  }

  .health-text strong {
    color: var(--text-primary);
    font-weight: 600;
  }

  .health-text.disconnected {
    color: var(--error);
  }

  .section {
    margin-bottom: 44px;
    animation: fadeUp 0.4s ease backwards;
  }

  .section-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 18px;
  }

  .section-title {
    font-size: 0.78em;
    font-weight: 600;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 1.5px;
  }

  .section-count {
    font-size: 0.68em;
    font-family: var(--font-mono);
    color: var(--text-muted);
    background: var(--bg-input);
    padding: 2px 8px;
    border-radius: 10px;
    opacity: 0.7;
  }

  .plugin-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(290px, 1fr));
    gap: 14px;
  }

  .card-wrapper {
    animation: fadeUp 0.35s ease backwards;
  }
</style>
