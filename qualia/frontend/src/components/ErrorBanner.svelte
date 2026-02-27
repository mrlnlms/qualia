<script>
  let { message, onDismiss } = $props();
</script>

<div class="error-banner">
  <div class="error-stripe"></div>
  <div class="error-content">
    <span class="error-message">{message}</span>
    {#if onDismiss}
      <button class="dismiss" onclick={onDismiss}>&times;</button>
    {/if}
  </div>
</div>

<style>
  .error-banner {
    background: var(--error-bg);
    border: 1px solid rgba(240, 96, 96, 0.2);
    border-radius: var(--radius);
    margin-bottom: 24px;
    animation: fadeUp 0.25s ease backwards;
    overflow: hidden;
  }

  .error-stripe {
    height: 2px;
    background: linear-gradient(90deg, var(--error), transparent);
  }

  .error-content {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 14px 18px;
    gap: 12px;
  }

  .error-message {
    flex: 1;
    color: var(--text-primary);
    font-size: 0.88em;
  }

  .dismiss {
    background: none;
    border: none;
    color: var(--text-muted);
    font-size: 1.3em;
    padding: 0 4px;
    transition: color var(--transition);
    line-height: 1;
  }

  .dismiss:hover {
    color: var(--error);
  }
</style>
