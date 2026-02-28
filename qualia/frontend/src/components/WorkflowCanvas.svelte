<script>
  import WorkflowNode from './WorkflowNode.svelte';
  import WorkflowEdge from './WorkflowEdge.svelte';
  import { bezierPath, outputPortPos, inputPortPos, NODE_WIDTH, PORT_OFFSET_Y } from '../lib/workflow.js';

  let {
    nodes,
    edges,
    selectedNodeId = null,
    selectedEdgeId = null,
    onSelectNode = null,
    onSelectEdge = null,
    onMoveNode = null,
    onConnect = null,
    onDeleteEdge = null,
    onDeselectAll = null,
  } = $props();

  let viewportEl = $state(null);
  let panX = $state(0);
  let panY = $state(0);
  let panning = $state(false);
  let panStartX = 0;
  let panStartY = 0;
  let panOriginX = 0;
  let panOriginY = 0;

  // Temp edge state (while dragging from output port)
  let tempEdge = $state(null); // { sourceId, x1, y1, x2, y2 }

  function onBgPointerDown(e) {
    if (e.target !== e.currentTarget && !e.target.closest('.canvas-transform')) return;
    if (e.target.closest('.wf-node') || e.target.closest('.port')) return;
    panning = true;
    panStartX = e.clientX;
    panStartY = e.clientY;
    panOriginX = panX;
    panOriginY = panY;
    onDeselectAll?.();
  }

  function onBgPointerMove(e) {
    if (panning) {
      panX = panOriginX + (e.clientX - panStartX);
      panY = panOriginY + (e.clientY - panStartY);
      return;
    }
    if (tempEdge) {
      const rect = viewportEl.getBoundingClientRect();
      tempEdge = {
        ...tempEdge,
        x2: e.clientX - rect.left - panX,
        y2: e.clientY - rect.top - panY,
      };
    }
  }

  function onBgPointerUp(e) {
    panning = false;
    if (tempEdge) {
      // Convert pointer screen coords to canvas coords
      const rect = viewportEl.getBoundingClientRect();
      const cx = e.clientX - rect.left - panX;
      const cy = e.clientY - rect.top - panY;

      // Find closest input port within 30px snap radius
      const SNAP = 30;
      let bestId = null;
      let bestDist = SNAP;
      for (const n of nodes) {
        if (n.nodeType === 'input') continue; // input nodes have no input port
        if (n.id === tempEdge.sourceId) continue;
        const port = inputPortPos(n);
        const dx = cx - port.x;
        const dy = cy - port.y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < bestDist) {
          bestDist = dist;
          bestId = n.id;
        }
      }

      if (bestId) {
        handlePortDragEnd(bestId);
      } else {
        tempEdge = null;
      }
    }
  }

  function handlePortDragStart(sourceId, clientX, clientY) {
    const sourceNode = nodes.find(n => n.id === sourceId);
    if (!sourceNode) return;
    const pos = outputPortPos(sourceNode);
    tempEdge = { sourceId, x1: pos.x, y1: pos.y, x2: pos.x, y2: pos.y };
  }

  function handlePortDragEnd(targetId) {
    if (tempEdge && tempEdge.sourceId !== targetId) {
      onConnect?.(tempEdge.sourceId, targetId);
    }
    tempEdge = null;
  }

  const tempPath = $derived(
    tempEdge ? bezierPath(tempEdge.x1, tempEdge.y1, tempEdge.x2, tempEdge.y2) : null
  );

  // Midpoint of selected edge for the HTML delete button
  const selectedEdgeMid = $derived.by(() => {
    if (!selectedEdgeId) return null;
    const edge = edges.find(e => e.id === selectedEdgeId);
    if (!edge) return null;
    const src = nodes.find(n => n.id === edge.sourceNodeId);
    const tgt = nodes.find(n => n.id === edge.targetNodeId);
    if (!src || !tgt) return null;
    const from = outputPortPos(src);
    const to = inputPortPos(tgt);
    return { x: (from.x + to.x) / 2, y: (from.y + to.y) / 2 };
  });
</script>

<!-- Global listeners for port drag (so we don't lose tracking outside viewport) -->
<svelte:window onpointermove={onBgPointerMove} onpointerup={onBgPointerUp} />

<!-- svelte-ignore a11y_no_static_element_interactions -->
<div
  class="canvas-viewport"
  bind:this={viewportEl}
  onpointerdown={onBgPointerDown}
>
  <div class="canvas-transform" style="transform: translate({panX}px, {panY}px);">
    <!-- SVG edge layer -->
    <svg class="edge-layer">
      {#each edges as edge (edge.id)}
        <WorkflowEdge
          {edge}
          {nodes}
          selected={selectedEdgeId === edge.id}
          onSelect={onSelectEdge}
          onDelete={onDeleteEdge}
        />
      {/each}
      {#if tempPath}
        <path d={tempPath} fill="none" stroke="var(--accent)" stroke-width="1.5"
          stroke-dasharray="6 4" opacity="0.6" style="pointer-events: none;" />
      {/if}
    </svg>

    <!-- Node layer -->
    <div class="node-layer">
      {#each nodes as node (node.id)}
        <WorkflowNode
          {node}
          selected={selectedNodeId === node.id}
          onSelect={onSelectNode}
          onMove={onMoveNode}
          onPortDragStart={handlePortDragStart}
        />
      {/each}

      <!-- Edge delete button (HTML, not SVG) -->
      {#if selectedEdgeMid && selectedEdgeId}
        {@const edgeToDelete = selectedEdgeId}
        <button
          class="edge-delete-btn"
          style="left: {selectedEdgeMid.x}px; top: {selectedEdgeMid.y}px;"
          onpointerdown={(e) => e.stopPropagation()}
          onclick={(e) => { e.stopPropagation(); onDeleteEdge?.(edgeToDelete); }}
        >×</button>
      {/if}
    </div>
  </div>
</div>

<style>
  .canvas-viewport {
    flex: 1;
    width: 100%;
    height: 100%;
    min-height: 0;
    overflow: hidden;
    position: relative;
    background:
      radial-gradient(circle, var(--border-subtle) 1px, transparent 1px);
    background-size: 20px 20px;
    cursor: grab;
  }

  .canvas-viewport:active {
    cursor: grabbing;
  }

  .canvas-transform {
    position: absolute;
    top: 0;
    left: 0;
  }

  .edge-layer {
    position: absolute;
    top: 0;
    left: 0;
    width: 1px;
    height: 1px;
    overflow: visible;
    pointer-events: none;
  }

  .edge-layer :global(path) {
    pointer-events: stroke;
  }

  .edge-layer :global(.edge-delete) {
    pointer-events: all;
  }

  .node-layer {
    position: absolute;
    top: 0;
    left: 0;
  }

  .edge-delete-btn {
    position: absolute;
    transform: translate(-50%, -50%);
    width: 22px;
    height: 22px;
    border-radius: 50%;
    border: 1.5px solid var(--error);
    background: var(--bg-secondary);
    color: var(--error);
    font-size: 14px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    z-index: 5;
    transition: background 0.12s ease;
    line-height: 1;
    padding: 0;
  }

  .edge-delete-btn:hover {
    background: var(--error-bg);
  }
</style>
