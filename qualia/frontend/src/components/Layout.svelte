<script>
  import { currentPage, navigate } from '../lib/stores.js';

  const navItems = [
    { id: 'home', label: 'Home', icon: 'H' },
    { id: 'analyze', label: 'Analyze', icon: 'A' },
    { id: 'transcribe', label: 'Transcribe', icon: 'T' },
    { id: 'pipeline', label: 'Pipeline', icon: 'P' },
    { id: 'monitor', label: 'Monitor', icon: 'M' },
  ];
</script>

<div class="layout">
  <nav class="sidebar">
    <div class="sidebar-header">
      <div class="logo-mark">Q</div>
      <div class="logo-text">
        <span class="logo-name">Qualia</span>
        <span class="logo-sub">analysis engine</span>
      </div>
    </div>
    <ul class="nav-list">
      {#each navItems as item, i}
        <li style="animation-delay: {60 + i * 40}ms">
          <button
            class="nav-item"
            class:active={$currentPage === item.id}
            onclick={() => navigate(item.id)}
          >
            <span class="nav-icon">{item.icon}</span>
            <span class="nav-label">{item.label}</span>
            {#if $currentPage === item.id}
              <span class="nav-indicator"></span>
            {/if}
          </button>
        </li>
      {/each}
    </ul>
    <div class="sidebar-footer">
      <div class="footer-line"></div>
      <div class="footer-info">
        <span class="version">v0.1.0</span>
        <a class="api-link" href="/docs" target="_blank">API Docs</a>
      </div>
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
    border-right: 1px solid var(--border-subtle);
    display: flex;
    flex-direction: column;
    position: relative;
  }

  .sidebar::after {
    content: '';
    position: absolute;
    top: 0;
    right: 0;
    bottom: 0;
    width: 1px;
    background: linear-gradient(
      to bottom,
      transparent 0%,
      var(--border) 20%,
      var(--border) 80%,
      transparent 100%
    );
  }

  .sidebar-header {
    padding: 28px 22px 24px;
    display: flex;
    align-items: center;
    gap: 14px;
  }

  .logo-mark {
    width: 36px;
    height: 36px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.15em;
    font-weight: 600;
    background: var(--accent-gradient);
    color: var(--bg-primary);
    border-radius: 10px;
    letter-spacing: -0.5px;
    flex-shrink: 0;
  }

  .logo-text {
    display: flex;
    flex-direction: column;
    gap: 0;
  }

  .logo-name {
    font-size: 1.1em;
    font-weight: 600;
    color: var(--text-primary);
    letter-spacing: 0.3px;
    line-height: 1.2;
  }

  .logo-sub {
    font-size: 0.7em;
    color: var(--text-muted);
    letter-spacing: 0.5px;
  }

  .nav-list {
    list-style: none;
    padding: 8px 10px;
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .nav-list li {
    animation: fadeIn 0.3s ease backwards;
  }

  .nav-item {
    width: 100%;
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 14px;
    border: none;
    background: transparent;
    color: var(--text-muted);
    font-size: 0.9em;
    font-weight: 400;
    border-radius: var(--radius-sm);
    transition: all var(--transition);
    position: relative;
  }

  .nav-item:hover {
    background: var(--bg-hover);
    color: var(--text-secondary);
  }

  .nav-item.active {
    background: var(--accent-dim);
    color: var(--accent);
    font-weight: 500;
  }

  .nav-icon {
    width: 24px;
    height: 24px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.72em;
    font-weight: 600;
    font-family: var(--font-mono);
    letter-spacing: -0.3px;
    border-radius: 6px;
    background: var(--bg-input);
    color: var(--text-muted);
    transition: all var(--transition);
    flex-shrink: 0;
  }

  .nav-item.active .nav-icon {
    background: var(--accent);
    color: var(--bg-primary);
  }

  .nav-indicator {
    position: absolute;
    left: 0;
    top: 50%;
    transform: translateY(-50%);
    width: 3px;
    height: 16px;
    background: var(--accent);
    border-radius: 0 3px 3px 0;
  }

  .sidebar-footer {
    padding: 16px 22px 20px;
  }

  .footer-line {
    height: 1px;
    background: linear-gradient(to right, var(--border), transparent);
    margin-bottom: 14px;
  }

  .footer-info {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .version {
    font-size: 0.72em;
    color: var(--text-muted);
    font-family: var(--font-mono);
  }

  .api-link {
    font-size: 0.72em;
    color: var(--text-muted);
    text-decoration: none;
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
    padding: 40px 48px;
    animation: fadeUp 0.35s ease backwards;
    min-height: 100%;
  }
</style>
