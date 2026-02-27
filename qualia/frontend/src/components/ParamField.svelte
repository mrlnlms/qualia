<script>
  let { name, spec, value = $bindable() } = $props();

  function handleNumberInput(e) {
    const v = spec.type === 'float' ? parseFloat(e.target.value) : parseInt(e.target.value);
    if (!isNaN(v)) value = v;
  }
</script>

<div class="field">
  <label class="label" for={name}>
    <span class="label-text">{spec.description || name}</span>
    {#if spec.range}
      <span class="label-hint">{spec.range[0]}..{spec.range[1]}</span>
    {/if}
  </label>

  {#if spec.type === 'bool'}
    <label class="toggle">
      <input type="checkbox" bind:checked={value} id={name} />
      <span class="toggle-track">
        <span class="toggle-knob"></span>
      </span>
      <span class="toggle-label">{value ? 'On' : 'Off'}</span>
    </label>
  {:else if spec.options}
    <div class="select-wrapper">
      <select bind:value id={name} class="select">
        {#each spec.options as opt}
          <option value={opt}>{opt}</option>
        {/each}
      </select>
      <span class="select-chevron">&#9662;</span>
    </div>
  {:else if spec.type === 'int' || spec.type === 'float'}
    <div class="number-group">
      <input
        type="number"
        {value}
        oninput={handleNumberInput}
        min={spec.range?.[0]}
        max={spec.range?.[1]}
        step={spec.type === 'float' ? 0.1 : 1}
        id={name}
        class="number-input"
      />
      {#if spec.range}
        <div class="range-wrapper">
          <input
            type="range"
            {value}
            oninput={handleNumberInput}
            min={spec.range[0]}
            max={spec.range[1]}
            step={spec.type === 'float' ? 0.1 : 1}
            class="range-input"
          />
        </div>
      {/if}
    </div>
  {:else}
    <input type="text" bind:value id={name} class="text-input" />
  {/if}
</div>

<style>
  .field {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .label {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
  }

  .label-text {
    font-size: 0.82em;
    color: var(--text-secondary);
    font-weight: 500;
  }

  .label-hint {
    font-size: 0.7em;
    color: var(--text-muted);
    font-family: var(--font-mono);
    opacity: 0.7;
  }

  .select-wrapper {
    position: relative;
  }

  .select {
    width: 100%;
    padding: 9px 32px 9px 12px;
    background: var(--bg-input);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    color: var(--text-primary);
    font-size: 0.88em;
    transition: all var(--transition);
    outline: none;
    appearance: none;
    cursor: pointer;
  }

  .select:focus {
    border-color: var(--border-focus);
    box-shadow: 0 0 0 3px var(--accent-dim);
  }

  .select-chevron {
    position: absolute;
    right: 12px;
    top: 50%;
    transform: translateY(-50%);
    color: var(--text-muted);
    font-size: 0.7em;
    pointer-events: none;
  }

  .text-input, .number-input {
    padding: 9px 12px;
    background: var(--bg-input);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    color: var(--text-primary);
    font-size: 0.88em;
    transition: all var(--transition);
    outline: none;
  }

  .text-input:focus, .number-input:focus {
    border-color: var(--border-focus);
    box-shadow: 0 0 0 3px var(--accent-dim);
  }

  .number-group {
    display: flex;
    gap: 12px;
    align-items: center;
  }

  .number-input {
    width: 88px;
    flex-shrink: 0;
    font-family: var(--font-mono);
    font-size: 0.84em;
  }

  .range-wrapper {
    flex: 1;
    padding: 0 4px;
  }

  .range-input {
    width: 100%;
    height: 4px;
    -webkit-appearance: none;
    appearance: none;
    background: var(--border);
    border-radius: 2px;
    outline: none;
    cursor: pointer;
  }

  .range-input::-webkit-slider-thumb {
    -webkit-appearance: none;
    width: 16px;
    height: 16px;
    border-radius: 50%;
    background: var(--accent);
    cursor: pointer;
    transition: all var(--transition);
    box-shadow: 0 0 0 3px var(--bg-primary), 0 0 0 4px var(--border);
  }

  .range-input::-webkit-slider-thumb:hover {
    transform: scale(1.15);
    box-shadow: 0 0 0 3px var(--bg-primary), 0 0 0 4px var(--accent), var(--shadow-glow);
  }

  .toggle {
    display: flex;
    align-items: center;
    gap: 10px;
    cursor: pointer;
  }

  .toggle input {
    display: none;
  }

  .toggle-track {
    width: 38px;
    height: 22px;
    background: var(--border);
    border-radius: 11px;
    position: relative;
    transition: all var(--transition);
  }

  .toggle-knob {
    position: absolute;
    width: 16px;
    height: 16px;
    border-radius: 50%;
    background: var(--text-muted);
    top: 3px;
    left: 3px;
    transition: all var(--transition);
  }

  .toggle input:checked ~ .toggle-track {
    background: var(--accent);
  }

  .toggle input:checked ~ .toggle-track .toggle-knob {
    left: 19px;
    background: #fff;
    box-shadow: 0 1px 3px rgba(0,0,0,0.3);
  }

  .toggle-label {
    font-size: 0.78em;
    color: var(--text-muted);
    font-family: var(--font-mono);
    min-width: 24px;
  }
</style>
