<script>
  import { bezierPath, outputPortPos, inputPortPos } from '../lib/workflow.js';

  let { edge, nodes, selected = false, onSelect = null, onDelete = null } = $props();

  const sourceNode = $derived(nodes.find(n => n.id === edge.sourceNodeId));
  const targetNode = $derived(nodes.find(n => n.id === edge.targetNodeId));

  const from = $derived(sourceNode ? outputPortPos(sourceNode) : null);
  const to = $derived(targetNode ? inputPortPos(targetNode) : null);

  const path = $derived(
    from && to ? bezierPath(from.x, from.y, to.x, to.y) : ''
  );

  // Midpoint for the delete button
  const mid = $derived(from && to ? { x: (from.x + to.x) / 2, y: (from.y + to.y) / 2 } : null);

  function handleClick(e) {
    e.stopPropagation();
    onSelect?.(edge.id);
  }
</script>

<!-- svelte-ignore a11y_click_events_have_key_events -->
<!-- svelte-ignore a11y_no_static_element_interactions -->
{#if path}
  <!-- Invisible fat hit area -->
  <path d={path} fill="none" stroke="transparent" stroke-width="14"
    role="button" tabindex="-1"
    style="cursor: pointer; pointer-events: stroke;"
    onclick={handleClick} />
  <!-- Visible path -->
  <path d={path} fill="none"
    class="edge-path" class:selected
    stroke-width="1.5"
    style="pointer-events: none;" />
{/if}

<style>
  .edge-path {
    stroke: var(--border);
    transition: stroke 0.15s ease;
  }
  .edge-path.selected {
    stroke: var(--accent);
  }
</style>
