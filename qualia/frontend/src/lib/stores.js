import { writable, derived } from 'svelte/store';

export const plugins = writable([]);
export const health = writable(null);
export const globalError = writable(null);

// Route state: { page: 'analyze', pluginId: 'word_frequency' }
export const route = writable(parseHash());
export const currentPage = derived(route, ($route) => $route.page);

export const pluginsByType = derived(plugins, ($plugins) => ({
  analyzers: $plugins.filter(p => p.type === 'analyzer'),
  visualizers: $plugins.filter(p => p.type === 'visualizer'),
  document: $plugins.filter(p => p.type === 'document'),
}));

function parseHash() {
  const raw = window.location.hash.replace('#/', '').replace('#', '');
  if (!raw) return { page: 'home', pluginId: null };
  const parts = raw.split('/');
  return { page: parts[0], pluginId: parts[1] || null };
}

if (typeof window !== 'undefined') {
  window.addEventListener('hashchange', () => {
    route.set(parseHash());
  });
}

export function navigate(page, pluginId) {
  if (pluginId) {
    window.location.hash = `#/${page}/${pluginId}`;
  } else {
    window.location.hash = `#/${page}`;
  }
}
