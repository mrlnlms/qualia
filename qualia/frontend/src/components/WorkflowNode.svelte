<script>
  import { NODE_WIDTH } from '../lib/workflow.js';
  import { typeConfig } from '../lib/constants.js';

  let {
    node,
    selected = false,
    onSelect = null,
    onMove = null,
    onPortDragStart = null,
  } = $props();

  let dragging = false;
  let dragStartX = 0;
  let dragStartY = 0;
  let nodeStartX = 0;
  let nodeStartY = 0;

  const tc = $derived(node.pluginType ? typeConfig[node.pluginType] : null);

  const statusIcon = $derived.by(() => {
    switch (node.status) {
      case 'running': return '⟳';
      case 'done': return '✓';
      case 'error': return '!';
      default: return '';
    }
  });

  function onPointerDown(e) {
    if (e.target.closest('.port')) return;
    e.stopPropagation();
    dragging = true;
    dragStartX = e.clientX;
    dragStartY = e.clientY;
    nodeStartX = node.x;
    nodeStartY = node.y;
    e.target.closest('.wf-node').setPointerCapture(e.pointerId);
    onSelect?.(node.id);
  }

  function onPointerMove(e) {
    if (!dragging) return;
    e.stopPropagation();
    const dx = e.clientX - dragStartX;
    const dy = e.clientY - dragStartY;
    onMove?.(node.id, nodeStartX + dx, nodeStartY + dy);
  }

  function onPointerUp(e) {
    if (!dragging) return;
    dragging = false;
  }

  function onOutputPortDown(e) {
    e.stopPropagation();
    e.preventDefault();
    onPortDragStart?.(node.id, e.clientX, e.clientY);
  }


</script>

<!-- svelte-ignore a11y_click_events_have_key_events -->
<!-- svelte-ignore a11y_no_static_element_interactions -->
<div
  class="wf-node"
  class:selected
  class:running={node.status === 'running'}
  class:done={node.status === 'done'}
  class:error={node.status === 'error'}
  style="left: {node.x}px; top: {node.y}px; width: {NODE_WIDTH}px;"
  onpointerdown={onPointerDown}
  onpointermove={onPointerMove}
  onpointerup={onPointerUp}
>
  <div class="node-header">
    {#if node.nodeType === 'input'}
      <span class="node-badge input-badge">input</span>
      <span class="node-name">
        {node.inputMode === 'file' ? 'File Input' : 'Text Input'}
      </span>
    {:else}
      {#if tc}
        <span class="node-badge" style="color: {tc.color}; background: {tc.bg};">{tc.label}</span>
      {/if}
      <span class="node-name">{node.pluginName || node.pluginId}</span>
    {/if}
    {#if statusIcon}
      <span class="node-status" class:status-running={node.status === 'running'} class:status-done={node.status === 'done'} class:status-error={node.status === 'error'}>
        {statusIcon}
      </span>
    {/if}
  </div>

  {#if node.result && node.status === 'done'}
    <div class="node-preview">
      {#if typeof node.result === 'object' && node.result.encoding === 'base64'}
        <span class="preview-tag">image</span>
      {:else}
        <span class="preview-tag">result ready</span>
      {/if}
    </div>
  {/if}

  <!-- Input port (not on input node) -->
  {#if node.nodeType !== 'input'}
    <div class="port port-in" data-port-in={node.id}></div>
  {/if}

  <!-- Output port -->
  <!-- svelte-ignore a11y_no_static_element_interactions -->
  <div class="port port-out" onpointerdown={onOutputPortDown}></div>
</div>

<style>
  .wf-node {
    position: absolute;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius-lg);
    cursor: grab;
    user-select: none;
    touch-action: none;
    transition: border-color 0.15s ease, box-shadow 0.15s ease;
    z-index: 1;
  }

  .wf-node:hover {
    border-color: var(--text-muted);
  }

  .wf-node.selected {
    border-color: var(--border-focus);
    box-shadow: 0 0 0 2px var(--accent-dim);
    z-index: 2;
  }

  .wf-node.running {
    border-color: var(--accent);
  }

  .wf-node.done {
    border-color: var(--success);
  }

  .wf-node.error {
    border-color: var(--error);
  }

  .node-header {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 8px 10px;
    min-height: 38px;
  }

  .node-badge {
    font-size: 0.6em;
    font-family: var(--font-mono);
    padding: 1px 5px;
    border-radius: 3px;
    flex-shrink: 0;
    text-transform: lowercase;
  }

  .input-badge {
    color: var(--text-muted);
    background: var(--bg-hover);
  }

  .node-name {
    font-size: 0.78em;
    color: var(--text-primary);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    flex: 1;
  }

  .node-status {
    font-size: 0.75em;
    flex-shrink: 0;
    width: 18px;
    height: 18px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
  }

  .status-running {
    animation: spin 1s linear infinite;
    color: var(--accent);
  }

  .status-done {
    color: var(--success);
    background: var(--accent-dim);
  }

  .status-error {
    color: var(--error);
    background: var(--error-dim);
  }

  .node-preview {
    padding: 0 10px 8px;
  }

  .preview-tag {
    font-size: 0.65em;
    font-family: var(--font-mono);
    color: var(--text-muted);
    background: var(--bg-hover);
    padding: 2px 6px;
    border-radius: 3px;
  }

  /* Ports */
  .port {
    position: absolute;
    width: 14px;
    height: 14px;
    background: var(--bg-input);
    border: 2px solid var(--border);
    border-radius: 50%;
    top: 22px;
    cursor: crosshair;
    transition: transform 0.12s ease, border-color 0.12s ease, background 0.12s ease;
    z-index: 3;
  }

  .port:hover {
    transform: scale(1.4);
    border-color: var(--accent);
    background: var(--accent-dim);
  }

  .port-in {
    left: -7px;
  }

  .port-out {
    right: -7px;
  }
</style>
