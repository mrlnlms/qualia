<script>
  import { onMount } from 'svelte';
  import { currentPage, navigate } from '../lib/stores.js';

  const navItems = [
    { id: 'home', label: 'Home', icon: 'H' },
    { id: 'transcribe', label: 'Transcribe', icon: 'T' },
    { id: 'analyze', label: 'Analyze', icon: 'A' },
    { id: 'pipeline', label: 'Pipeline', icon: 'P' },
    { id: 'workflow', label: 'Workflow', icon: 'W' },
    { id: 'monitor', label: 'Monitor', icon: 'M' },
  ];

  let darkMode = $state(false);

  onMount(() => {
    darkMode = localStorage.getItem('qualia-theme') === 'dark';
    applyTheme();
  });

  function toggleTheme() {
    darkMode = !darkMode;
    localStorage.setItem('qualia-theme', darkMode ? 'dark' : 'light');
    applyTheme();
  }

  function applyTheme() {
    document.documentElement.setAttribute('data-theme', darkMode ? 'dark' : 'light');
  }
</script>

<div class="layout">
  <nav class="sidebar">
    <div class="sidebar-header">
      <span class="logo">Qualia</span>
    </div>
    <ul class="nav-list">
      {#each navItems as item}
        <li>
          <button
            class="nav-item"
            class:active={$currentPage === item.id}
            onclick={() => navigate(item.id)}
          >
            <span class="nav-key">{item.icon}</span>
            <span class="nav-label">{item.label}</span>
          </button>
        </li>
      {/each}
    </ul>
    <div class="sidebar-footer">
      <span class="version">v0.2.0-beta</span>
      <button class="theme-toggle" onclick={toggleTheme} title={darkMode ? 'Light mode' : 'Dark mode'}>
        {darkMode ? 'light' : 'dark'}
      </button>
      <a class="api-link" href="/docs" target="_blank">api</a>
    </div>
  </nav>
  <main class="content">
    <div class="content-inner">
      <slot />
    </div>
  </main>
</div>

<style>
  .layout {
    display: flex;
    height: 100vh;
    overflow: hidden;
  }

  .sidebar {
    width: var(--sidebar-width);
    min-width: var(--sidebar-width);
    background: var(--bg-secondary);
    border-right: 1px solid var(--border);
    display: flex;
    flex-direction: column;
  }

  .sidebar-header {
    padding: 24px 20px 20px;
  }

  .logo {
    font-family: var(--font-serif);
    font-size: 1.25em;
    font-weight: 600;
    color: var(--text-primary);
    letter-spacing: -0.3px;
  }

  .nav-list {
    list-style: none;
    padding: 4px 10px;
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 1px;
  }

  .nav-item {
    width: 100%;
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 8px 12px;
    border: none;
    background: transparent;
    color: var(--text-muted);
    font-size: 0.88em;
    border-radius: var(--radius);
    transition: all var(--transition);
  }

  .nav-item:hover {
    background: var(--bg-hover);
    color: var(--text-secondary);
  }

  .nav-item.active {
    background: var(--accent-dim);
    color: var(--accent);
  }

  .nav-key {
    width: 20px;
    height: 20px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.68em;
    font-weight: 500;
    font-family: var(--font-mono);
    border-radius: 3px;
    background: var(--bg-input);
    color: var(--text-muted);
    flex-shrink: 0;
  }

  .nav-item.active .nav-key {
    background: var(--accent);
    color: var(--bg-card);
  }

  .nav-label {
    font-weight: 400;
  }

  .nav-item.active .nav-label {
    font-weight: 500;
  }

  .sidebar-footer {
    padding: 14px 20px 18px;
    border-top: 1px solid var(--border-subtle);
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .version {
    font-size: 0.68em;
    color: var(--text-muted);
    font-family: var(--font-mono);
  }

  .theme-toggle {
    background: none;
    border: none;
    color: var(--text-muted);
    font-size: 0.68em;
    font-family: var(--font-mono);
    padding: 2px 0;
    transition: color var(--transition);
  }

  .theme-toggle:hover {
    color: var(--accent);
  }

  .api-link {
    font-size: 0.68em;
    font-family: var(--font-mono);
    color: var(--text-muted);
    text-decoration: none;
    margin-left: auto;
    transition: color var(--transition);
  }

  .api-link:hover {
    color: var(--accent);
  }

  .content {
    flex: 1;
    overflow-y: auto;
    background: var(--bg-primary);
  }

  .content-inner {
    padding: 36px 40px;
    min-height: 100%;
  }
</style>
