// Workflow data model — nodes, edges, topoSort, bezier, validation

let _id = 0;
function uid() { return 'n' + (++_id) + '_' + Date.now().toString(36); }

export function createInputNode(x = 100, y = 200) {
  return {
    id: uid(),
    pluginId: null,
    nodeType: 'input',
    x, y,
    config: {},
    schema: null,
    status: 'idle',
    result: null,
    inputMode: 'text',
  };
}

export function createPluginNode(plugin, x = 300, y = 200) {
  return {
    id: uid(),
    pluginId: plugin.id,
    pluginName: plugin.name,
    pluginType: plugin.type,
    pluginProvides: plugin.provides || [],
    pluginRequires: plugin.requires || [],
    nodeType: 'plugin',
    x, y,
    config: {},
    schema: null,
    status: 'idle',
    result: null,
    inputMode: null,
  };
}

export function addEdge(state, sourceId, targetId) {
  if (!canConnect(state, sourceId, targetId)) return state;
  const id = 'e' + (++_id) + '_' + Date.now().toString(36);
  return {
    ...state,
    edges: [...state.edges, { id, sourceNodeId: sourceId, targetNodeId: targetId }],
  };
}

export function removeEdge(state, edgeId) {
  return { ...state, edges: state.edges.filter(e => e.id !== edgeId) };
}

export function removeNode(state, nodeId) {
  return {
    ...state,
    nodes: state.nodes.filter(n => n.id !== nodeId),
    edges: state.edges.filter(e => e.sourceNodeId !== nodeId && e.targetNodeId !== nodeId),
  };
}

export function canConnect(state, sourceId, targetId) {
  if (sourceId === targetId) return false;
  const sourceNode = state.nodes.find(n => n.id === sourceId);
  const targetNode = state.nodes.find(n => n.id === targetId);
  if (!sourceNode || !targetNode) return false;
  // Input nodes can't receive connections
  if (targetNode.nodeType === 'input') return false;
  // Max 1 input per node
  if (state.edges.some(e => e.targetNodeId === targetId)) return false;
  // No duplicate edge
  if (state.edges.some(e => e.sourceNodeId === sourceId && e.targetNodeId === targetId)) return false;
  // Cycle detection: would adding this edge create a cycle?
  if (wouldCreateCycle(state, sourceId, targetId)) return false;
  return true;
}

function wouldCreateCycle(state, sourceId, targetId) {
  // Check if targetId can reach sourceId via existing edges
  const visited = new Set();
  const queue = [sourceId];
  while (queue.length > 0) {
    const curr = queue.shift();
    if (curr === targetId) continue; // skip the edge we're about to add
    if (visited.has(curr)) continue;
    visited.add(curr);
    for (const e of state.edges) {
      if (e.targetNodeId === curr && !visited.has(e.sourceNodeId)) {
        queue.push(e.sourceNodeId);
      }
    }
  }
  // Now check: can we reach sourceId from targetId through existing edges?
  const visited2 = new Set();
  const queue2 = [targetId];
  while (queue2.length > 0) {
    const curr = queue2.shift();
    if (curr === sourceId) return true;
    if (visited2.has(curr)) continue;
    visited2.add(curr);
    for (const e of state.edges) {
      if (e.sourceNodeId === curr && !visited2.has(e.targetNodeId)) {
        queue2.push(e.targetNodeId);
      }
    }
  }
  return false;
}

// Kahn's algorithm — returns ordered array of node IDs or null if cycle
// Uses X position as tiebreaker: left-to-right visual order
export function topoSort(state) {
  const { nodes, edges } = state;
  const nodeMap = {};
  const inDegree = {};
  const adj = {};
  for (const n of nodes) {
    nodeMap[n.id] = n;
    inDegree[n.id] = 0;
    adj[n.id] = [];
  }
  for (const e of edges) {
    inDegree[e.targetNodeId] = (inDegree[e.targetNodeId] || 0) + 1;
    adj[e.sourceNodeId] = adj[e.sourceNodeId] || [];
    adj[e.sourceNodeId].push(e.targetNodeId);
  }
  // Priority queue sorted by X position (leftmost first)
  let queue = nodes
    .filter(n => inDegree[n.id] === 0)
    .sort((a, b) => a.x - b.x)
    .map(n => n.id);
  const order = [];
  while (queue.length > 0) {
    const curr = queue.shift();
    order.push(curr);
    const ready = [];
    for (const next of (adj[curr] || [])) {
      inDegree[next]--;
      if (inDegree[next] === 0) ready.push(next);
    }
    if (ready.length > 0) {
      ready.sort((a, b) => (nodeMap[a]?.x || 0) - (nodeMap[b]?.x || 0));
      queue.push(...ready);
    }
  }
  if (order.length !== nodes.length) return null; // cycle
  return order;
}

// Convert workflow to pipeline steps array for POST /pipeline
export function toPipelineSteps(state, order) {
  return order
    .map(id => state.nodes.find(n => n.id === id))
    .filter(n => n && n.nodeType === 'plugin' && n.pluginId)
    .map(n => ({ plugin_id: n.pluginId, config: n.config || {} }));
}

// Cubic bezier path between two points
export function bezierPath(x1, y1, x2, y2) {
  const dx = Math.abs(x2 - x1) * 0.5;
  const cx1 = x1 + dx;
  const cy1 = y1;
  const cx2 = x2 - dx;
  const cy2 = y2;
  return `M ${x1} ${y1} C ${cx1} ${cy1}, ${cx2} ${cy2}, ${x2} ${y2}`;
}

// Port positions for a node
export const NODE_WIDTH = 180;
export const PORT_OFFSET_Y = 30;

export function outputPortPos(node) {
  return { x: node.x + NODE_WIDTH, y: node.y + PORT_OFFSET_Y };
}

export function inputPortPos(node) {
  return { x: node.x, y: node.y + PORT_OFFSET_Y };
}
