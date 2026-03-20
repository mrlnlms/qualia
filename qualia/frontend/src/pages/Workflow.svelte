<script>
  import { onDestroy } from 'svelte';
  import { plugins } from '../lib/stores.js';
  import { fetchPluginSchema, executePipeline } from '../lib/api.js';
  import {
    createInputNode, createPluginNode,
    addEdge, removeEdge, removeNode,
    topoSort, toPipelineSteps, NODE_WIDTH,
  } from '../lib/workflow.js';
  import WorkflowCanvas from '../components/WorkflowCanvas.svelte';
  import WorkflowPalette from '../components/WorkflowPalette.svelte';
  import WorkflowDrawer from '../components/WorkflowDrawer.svelte';

  // State
  let nodes = $state([createInputNode(100, 200)]);
  let edges = $state([]);
  let selectedNodeId = $state(null);
  let selectedEdgeId = $state(null);
  let inputText = $state('');
  let inputFile = $state(null);
  let loading = $state(false);
  let loadingElapsed = $state(0);
  let loadingTimer = null;
  let error = $state('');
  let paletteOpen = $state(false);

  const selectedNode = $derived(nodes.find(n => n.id === selectedNodeId) || null);
  const pluginNodeCount = $derived(nodes.filter(n => n.nodeType === 'plugin').length);
  const inputNode = $derived(nodes.find(n => n.nodeType === 'input'));

  // Build provides→plugin lookup from all available plugins
  const providesMap = $derived.by(() => {
    const map = {};
    for (const p of $plugins) {
      for (const field of (p.provides || [])) {
        if (!map[field]) map[field] = [];
        map[field].push(p.name);
      }
    }
    return map;
  });

  function validateDependencies(state, order) {
    const pluginNodes = order
      .map(id => state.nodes.find(n => n.id === id))
      .filter(n => n && n.nodeType === 'plugin');

    // Accumulate what's provided by steps before each node
    const available = new Set();
    for (const node of pluginNodes) {
      const requires = node.pluginRequires || [];
      for (const req of requires) {
        if (!available.has(req)) {
          const providers = providesMap[req];
          if (providers?.length) {
            return `"${node.pluginName}" needs "${req}" — add ${providers.join(' or ')} before it.`;
          }
          return `"${node.pluginName}" requires "${req}" but no plugin in this workflow provides it.`;
        }
      }
      const provides = node.pluginProvides || [];
      for (const p of provides) {
        available.add(p);
      }
    }
    return null;
  }

  function selectNode(id) {
    selectedNodeId = id;
    selectedEdgeId = null;
  }

  function selectEdge(id) {
    selectedEdgeId = id;
    selectedNodeId = null;
  }

  function deselectAll() {
    selectedNodeId = null;
    selectedEdgeId = null;
  }

  function moveNode(id, x, y) {
    const node = nodes.find(n => n.id === id);
    if (node) {
      node.x = x;
      node.y = y;
    }
  }

  function connectNodes(sourceId, targetId) {
    const state = { nodes, edges };
    const result = addEdge(state, sourceId, targetId);
    edges = result.edges;
  }

  function deleteEdge(edgeId) {
    edges = edges.filter(e => e.id !== edgeId);
    selectedEdgeId = null;
  }

  function deleteNode(nodeId) {
    const node = nodes.find(n => n.id === nodeId);
    if (!node || node.nodeType === 'input') return;
    const result = removeNode({ nodes, edges }, nodeId);
    nodes = result.nodes;
    edges = result.edges;
    selectedNodeId = null;
  }

  function handleKeydown(e) {
    if (e.key === 'Delete' || e.key === 'Backspace') {
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.tagName === 'SELECT') return;
      if (selectedEdgeId) {
        deleteEdge(selectedEdgeId);
      } else if (selectedNodeId) {
        deleteNode(selectedNodeId);
      }
    }
    if (e.key === 'Escape') {
      deselectAll();
      paletteOpen = false;
    }
  }

  async function handleAddPlugin(plugin) {
    // Position new node to the right of the rightmost node
    const maxX = Math.max(...nodes.map(n => n.x));
    const newX = maxX + NODE_WIDTH + 80;
    const avgY = nodes.reduce((sum, n) => sum + n.y, 0) / nodes.length;
    const newNode = createPluginNode(plugin, newX, avgY);

    // Fetch schema
    try {
      const s = await fetchPluginSchema(plugin.id);
      newNode.schema = s.parameters || s;
    } catch (e) {
      // schema optional, continue without it
    }

    nodes = [...nodes, newNode];
    selectedNodeId = newNode.id;
    paletteOpen = false;
  }

  function startTimer() {
    loadingElapsed = 0;
    loadingTimer = setInterval(() => loadingElapsed++, 1000);
  }

  function stopTimer() {
    clearInterval(loadingTimer);
    loadingTimer = null;
    loadingElapsed = 0;
  }

  onDestroy(() => { if (loadingTimer) clearInterval(loadingTimer); });

  function fmtTime(s) {
    const m = Math.floor(s / 60);
    const sec = s % 60;
    return m > 0 ? `${m}m ${sec}s` : `${sec}s`;
  }

  async function runWorkflow() {
    error = '';
    const state = { nodes, edges };
    const order = topoSort(state);
    if (!order) {
      error = 'Cycle detected in workflow. Remove a connection to fix.';
      return;
    }

    const steps = toPipelineSteps(state, order);
    if (steps.length === 0) {
      error = 'Add at least one plugin node to run.';
      return;
    }

    // Validate dependencies: check requires vs provides in pipeline order
    const depError = validateDependencies(state, order);
    if (depError) {
      error = depError;
      return;
    }

    const inp = inputNode;
    const hasInput = inp?.inputMode === 'file' ? !!inputFile : !!inputText.trim();
    if (!hasInput) {
      error = inp?.inputMode === 'file'
        ? 'Upload a file in the Input node.'
        : 'Enter text in the Input node.';
      return;
    }

    loading = true;
    startTimer();

    // Set all plugin nodes to running
    for (const n of nodes) {
      if (n.nodeType === 'plugin') {
        n.status = 'running';
        n.result = null;
      }
    }

    try {
      const result = await executePipeline(steps, {
        text: inp.inputMode === 'file' ? undefined : inputText,
        file: inp.inputMode === 'file' ? inputFile : undefined,
      });

      // Map results to nodes by order
      const pluginOrder = order.filter(id => {
        const n = nodes.find(nd => nd.id === id);
        return n && n.nodeType === 'plugin';
      });

      if (result.results) {
        for (let i = 0; i < result.results.length; i++) {
          const nodeId = pluginOrder[i];
          if (!nodeId) continue;
          const node = nodes.find(n => n.id === nodeId);
          if (node) {
            node.status = 'done';
            node.result = result.results[i].result || result.results[i];
          }
        }
      }

      // Mark any remaining running nodes as done
      for (const n of nodes) {
        if (n.status === 'running') n.status = 'done';
      }

      // Also mark input node done
      if (inp) inp.status = 'done';
    } catch (e) {
      const msg = typeof e.message === 'string' ? e.message : JSON.stringify(e);
      error = msg;
      for (const n of nodes) {
        if (n.status === 'running') {
          n.status = 'error';
          n.result = msg;
        }
      }
    } finally {
      stopTimer();
      loading = false;
    }
  }

  function resetStatus() {
    for (const n of nodes) {
      n.status = 'idle';
      n.result = null;
    }
    error = '';
  }
</script>

<svelte:window onkeydown={handleKeydown} />

<div class="workflow-page">
  <!-- Toolbar -->
  <div class="toolbar">
    <div class="toolbar-left">
      <h1 class="toolbar-title">Workflow</h1>
      <span class="toolbar-meta">
        {pluginNodeCount} node{pluginNodeCount !== 1 ? 's' : ''}
      </span>
    </div>
    <div class="toolbar-right">
      {#if loading}
        <span class="toolbar-timer">{fmtTime(loadingElapsed)}</span>
        <div class="toolbar-progress">
          <div class="toolbar-progress-fill"></div>
        </div>
      {/if}
      <button
        class="run-btn"
        onclick={runWorkflow}
        disabled={loading || pluginNodeCount === 0}
      >
        {#if loading}
          <span class="spinner"></span> running
        {:else}
          run
        {/if}
      </button>
    </div>
  </div>

  {#if error}
    <div class="error-banner">
      <span>{error}</span>
      <button class="error-dismiss" onclick={() => error = ''}>×</button>
    </div>
  {/if}

  <!-- Canvas area -->
  <div class="canvas-area">
    <WorkflowCanvas
      {nodes}
      {edges}
      {selectedNodeId}
      {selectedEdgeId}
      onSelectNode={selectNode}
      onSelectEdge={selectEdge}
      onMoveNode={moveNode}
      onConnect={connectNodes}
      onDeleteEdge={deleteEdge}
      onDeselectAll={deselectAll}
    />

    <WorkflowPalette
      open={paletteOpen}
      onToggle={() => paletteOpen = !paletteOpen}
      onAddPlugin={handleAddPlugin}
    />

    {#if selectedNode}
      <WorkflowDrawer
        node={selectedNode}
        bind:inputText
        bind:inputFile
        onClose={deselectAll}
        onDelete={deleteNode}
      />
    {/if}
  </div>
</div>

<style>
  .workflow-page {
    position: fixed;
    top: 0;
    left: var(--sidebar-width);
    right: 0;
    bottom: 0;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    background: var(--bg-primary);
    z-index: 1;
  }

  /* Toolbar */
  .toolbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 16px;
    border-bottom: 1px solid var(--border);
    background: var(--bg-secondary);
    flex-shrink: 0;
    z-index: 5;
  }

  .toolbar-left {
    display: flex;
    align-items: baseline;
    gap: 10px;
  }

  .toolbar-title {
    font-family: var(--font-serif);
    font-size: 1.15em;
    font-weight: 600;
    color: var(--text-primary);
    letter-spacing: -0.3px;
  }

  .toolbar-meta {
    font-size: 0.7em;
    font-family: var(--font-mono);
    color: var(--text-muted);
  }

  .toolbar-right {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .toolbar-timer {
    font-size: 0.7em;
    font-family: var(--font-mono);
    color: var(--text-muted);
  }

  .toolbar-progress {
    width: 60px;
    height: 2px;
    background: var(--bg-input);
    overflow: hidden;
    border-radius: 1px;
  }

  .toolbar-progress-fill {
    height: 100%;
    width: 30%;
    background: var(--accent);
    animation: progressSlide 1.5s ease-in-out infinite;
  }

  .run-btn {
    padding: 6px 16px;
    background: transparent;
    color: var(--accent);
    border: 1px solid var(--accent);
    border-radius: var(--radius);
    font-size: 0.78em;
    font-family: var(--font-mono);
    transition: all var(--transition);
    display: inline-flex;
    align-items: center;
    gap: 6px;
  }

  .run-btn:hover:not(:disabled) {
    background: var(--accent);
    color: #fff;
  }

  .run-btn:disabled {
    opacity: 0.35;
    cursor: not-allowed;
  }

  .spinner {
    width: 12px;
    height: 12px;
    border: 1.5px solid var(--border);
    border-top-color: var(--accent);
    border-radius: 50%;
    animation: spin 0.6s linear infinite;
  }

  /* Error banner */
  .error-banner {
    padding: 8px 14px;
    background: var(--error-bg);
    border-bottom: 1px solid var(--error-dim);
    color: var(--text-primary);
    font-size: 0.78em;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    flex-shrink: 0;
  }

  .error-dismiss {
    background: none;
    border: none;
    color: var(--text-muted);
    font-size: 1.1em;
    padding: 0 4px;
  }

  .error-dismiss:hover {
    color: var(--error);
  }

  /* Canvas area */
  .canvas-area {
    flex: 1;
    position: relative;
    overflow: hidden;
    display: flex;
    min-height: 0;
  }
</style>
