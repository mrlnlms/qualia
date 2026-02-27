<script>
  let { html } = $props();
</script>

<div class="html-result">
  <iframe srcdoc={html} sandbox="allow-scripts" title="Visualization"></iframe>
</div>

<style>
  .html-result {
    border: 1px solid var(--border);
    border-radius: var(--radius);
    overflow: hidden;
  }

  iframe {
    width: 100%;
    height: 500px;
    border: none;
    background: #fff;
  }
</style>
