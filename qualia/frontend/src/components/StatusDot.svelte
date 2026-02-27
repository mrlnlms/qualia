<script>
  let { connected = false } = $props();
</script>

<span class="dot" class:connected>
  {#if connected}
    <span class="dot-ring"></span>
  {/if}
</span>

<style>
  .dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--error);
    display: inline-flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    position: relative;
  }

  .dot.connected {
    background: var(--success);
  }

  .dot-ring {
    position: absolute;
    width: 100%;
    height: 100%;
    border-radius: 50%;
    background: var(--success);
    animation: ping 2s cubic-bezier(0, 0, 0.2, 1) infinite;
  }

  @keyframes ping {
    0% { transform: scale(1); opacity: 0.6; }
    75%, 100% { transform: scale(2.5); opacity: 0; }
  }
</style>
