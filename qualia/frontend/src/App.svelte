<script>
  import { onMount } from 'svelte';
  import { route, plugins, health, globalError } from './lib/stores.js';
  import { fetchPlugins, fetchHealth } from './lib/api.js';
  import Layout from './components/Layout.svelte';
  import Home from './pages/Home.svelte';
  import Analyze from './pages/Analyze.svelte';
  import Transcribe from './pages/Transcribe.svelte';
  import Pipeline from './pages/Pipeline.svelte';
  import Workflow from './pages/Workflow.svelte';
  import Monitor from './pages/Monitor.svelte';
  import ErrorBanner from './components/ErrorBanner.svelte';

  onMount(async () => {
    try {
      const [pluginList, healthData] = await Promise.all([
        fetchPlugins(),
        fetchHealth(),
      ]);
      plugins.set(pluginList);
      health.set(healthData);
    } catch (e) {
      globalError.set('Failed to connect to Qualia API. Is it running on port 8000?');
    }
  });
</script>

<Layout>
  {#if $globalError}
    <ErrorBanner message={$globalError} onDismiss={() => globalError.set(null)} />
  {/if}

  {#key $route.page + '/' + ($route.pluginId || '')}
    {#if $route.page === 'home'}
      <Home />
    {:else if $route.page === 'analyze'}
      <Analyze pluginId={$route.pluginId} />
    {:else if $route.page === 'transcribe'}
      <Transcribe pluginId={$route.pluginId} />
    {:else if $route.page === 'pipeline'}
      <Pipeline />
    {:else if $route.page === 'workflow'}
      <Workflow />
    {:else if $route.page === 'monitor'}
      <Monitor />
    {:else}
      <Home />
    {/if}
  {/key}
</Layout>
