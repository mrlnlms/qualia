const BASE = '';

async function request(url, options = {}) {
  const res = await fetch(`${BASE}${url}`, options);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ message: res.statusText }));
    throw err;
  }
  return res.json();
}

export function fetchHealth() {
  return request('/health');
}

export function fetchPlugins(type = null) {
  const url = type ? `/plugins?plugin_type=${type}` : '/plugins';
  return request(url);
}

export function fetchPlugin(id) {
  return request(`/plugins/${id}`);
}

export function fetchPluginSchema(id) {
  return request(`/plugins/${id}/schema`);
}

export function fetchConsolidated() {
  return request('/config/consolidated');
}

export function resolveConfig(pluginId, textSize) {
  return request('/config/resolve', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ plugin_id: pluginId, text_size: textSize }),
  });
}

export function analyze(pluginId, text, config = {}, context = {}) {
  return request(`/analyze/${pluginId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, config, context }),
  });
}

export async function analyzeFile(pluginId, file, config = {}) {
  const form = new FormData();
  form.append('file', file);
  form.append('config', JSON.stringify(config));
  return request(`/analyze/${pluginId}/file`, { method: 'POST', body: form });
}

export async function transcribe(pluginId, file, config = {}) {
  const form = new FormData();
  form.append('file', file);
  form.append('config', JSON.stringify(config));
  return request(`/transcribe/${pluginId}`, { method: 'POST', body: form });
}

export async function executePipeline(steps, { text, file } = {}) {
  const form = new FormData();
  form.append('steps', JSON.stringify(steps));
  if (file) form.append('file', file);
  if (text) form.append('text', text);
  return request('/pipeline', { method: 'POST', body: form });
}

export function visualize(pluginId, data, config = {}, outputFormat = 'html') {
  return request(`/visualize/${pluginId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ data, config, output_format: outputFormat }),
  });
}

export function createMonitorStream(onMessage, onError) {
  const source = new EventSource(`${BASE}/monitor/stream`);
  source.onmessage = (e) => onMessage(JSON.parse(e.data));
  source.onerror = onError;
  return source;
}
