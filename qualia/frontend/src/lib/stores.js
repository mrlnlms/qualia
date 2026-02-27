import { writable, derived } from 'svelte/store';

export const plugins = writable([]);
export const health = writable(null);
export const currentPage = writable(getInitialPage());
export const globalError = writable(null);

export const pluginsByType = derived(plugins, ($plugins) => ({
  analyzers: $plugins.filter(p => p.type === 'analyzer'),
  visualizers: $plugins.filter(p => p.type === 'visualizer'),
  document: $plugins.filter(p => p.type === 'document'),
}));

function getInitialPage() {
  const hash = window.location.hash.replace('#/', '').replace('#', '');
  return hash || 'home';
}

// Sync hash changes to store
if (typeof window !== 'undefined') {
  window.addEventListener('hashchange', () => {
    const hash = window.location.hash.replace('#/', '').replace('#', '');
    currentPage.set(hash || 'home');
  });
}

export function navigate(page) {
  window.location.hash = `#/${page}`;
}
