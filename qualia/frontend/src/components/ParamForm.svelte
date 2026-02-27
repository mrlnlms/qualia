<script>
  import ParamField from './ParamField.svelte';

  let { parameters = {}, values = $bindable({}) } = $props();

  // Initialize defaults
  $effect(() => {
    for (const [key, spec] of Object.entries(parameters)) {
      if (values[key] === undefined && spec.default !== undefined) {
        values[key] = spec.default;
      }
    }
  });

  const entries = $derived(Object.entries(parameters));
</script>

{#if entries.length > 0}
  <div class="param-form">
    <h4 class="form-title">Parameters</h4>
    <div class="fields">
      {#each entries as [name, spec]}
        <ParamField {name} {spec} bind:value={values[name]} />
      {/each}
    </div>
  </div>
{/if}

<style>
  .param-form {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .form-title {
    font-size: 0.85em;
    font-weight: 600;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 1px;
  }

  .fields {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
    gap: 16px;
  }
</style>
