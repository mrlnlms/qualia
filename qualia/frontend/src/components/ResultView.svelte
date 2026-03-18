<script>
  import JsonResult from './JsonResult.svelte';
  import ImageResult from './ImageResult.svelte';
  import HtmlResult from './HtmlResult.svelte';

  let { result } = $props();

  const resultType = $derived(detectType(result));

  function detectType(r) {
    if (!r) return 'empty';
    if (r.encoding === 'base64') return 'image';
    if (r.html) return 'html';
    return 'json';
  }
</script>

{#if resultType === 'image'}
  <ImageResult data={result.data} format={result.format} />
{:else if resultType === 'html'}
  <HtmlResult html={result.html} />
{:else if resultType === 'json'}
  <JsonResult data={result.result || result} />
{:else}
  <p class="empty">No results yet.</p>
{/if}

<style>
  .empty {
    color: var(--text-muted);
    font-size: 0.9em;
    text-align: center;
    padding: 40px;
  }
</style>
