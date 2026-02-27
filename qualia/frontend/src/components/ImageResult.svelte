<script>
  let { data, format = 'png' } = $props();
</script>

<div class="image-result">
  <img src="data:image/{format};base64,{data}" alt="Visualization result" />
</div>

<style>
  .image-result {
    display: flex;
    justify-content: center;
    padding: 16px;
    background: var(--bg-card);
    border-radius: var(--radius);
    border: 1px solid var(--border);
  }

  img {
    max-width: 100%;
    height: auto;
    border-radius: var(--radius-sm);
  }
</style>
