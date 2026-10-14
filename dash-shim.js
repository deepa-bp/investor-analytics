/*
 * Local stand-in for the dashboard runtime's `dash` API, so the page runs outside Claude.
 * Replace DATASETS with real API endpoints (CRM, event log, fund administrator) when wiring production data.
 * Implements: data, onData, calc, loader (no-op), params, setParams, resetParams, setLink, refresh, colors.
 */
window.dash = (function () {
  const DATASETS = {
    investors: 'data/sample_investors.csv',
    events: 'data/sample_events.csv',
    flows: 'data/sample_flows.csv',
    funnel: 'data/sample_funnel.csv',
  };
  const DEFAULT_PARAMS = { channel: 'all', investor: null };
  const COLORS = ['#0f7c7e', '#d9673a', '#3b6fd8', '#9a5cc9', '#c9a227', '#d0508a', '#2b5f75', '#6b7a8f'];

  const store = {};
  const calcs = {};
  const listeners = [];
  let params = { ...DEFAULT_PARAMS };

  const emit = () => listeners.forEach((fn) => { try { fn(); } catch (e) { console.error(e); } });

  function runCalcs() {
    for (const [id, c] of Object.entries(calcs)) {
      const inputs = c.inputs.map((i) => store[i]);
      if (inputs.some((s) => !s || s.status === 'error')) { store[id] = { status: 'error', data: [], message: 'An input failed to load' }; continue; }
      if (!inputs.every((s) => s.status === 'ok')) continue;
      try { store[id] = { status: 'ok', data: c.fn(...inputs.map((s) => s.data)) }; }
      catch (e) { console.error('calc ' + id, e); store[id] = { status: 'error', data: [], message: e.message }; }
    }
  }

  async function load(id) {
    store[id] = { status: 'loading', data: [] };
    try {
      const res = await fetch(DATASETS[id]);
      if (!res.ok) throw new Error(res.status + ' ' + res.statusText);
      const rows = d3.csvParse(await res.text());
      store[id] = { status: 'ok', data: rows, columns: rows.columns };
    } catch (e) {
      console.error('dataset ' + id, e);
      store[id] = { status: 'error', data: [], message: String(e) };
    }
  }

  Promise.all(Object.keys(DATASETS).map(load)).then(() => { runCalcs(); emit(); });

  let t;
  window.addEventListener('resize', () => { clearTimeout(t); t = setTimeout(emit, 150); });

  return {
    data: (id) => store[id] || { status: 'loading', data: [] },
    onData(fn) { listeners.push(fn); try { fn(); } catch (e) { console.error(e); } },
    calc(id, def) { calcs[id] = def; },
    loader() {},
    params: () => ({ ...params }),
    setParams(p) { params = { ...params, ...p }; emit(); },
    resetParams() { params = { ...DEFAULT_PARAMS }; emit(); },
    setLink(name) { history.replaceState(null, '', '#' + name); },
    async refresh(id) { if (DATASETS[id]) { await load(id); runCalcs(); emit(); } },
    colors: COLORS,
  };
})();
