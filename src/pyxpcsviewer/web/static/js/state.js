// The page's shared state: the files, the one shown (active), the ones checked (selection), the
// current tab. Subscribers are told which keys changed.

const listeners = new Set();
export const state = {
    info: null,          // /api/info
    colormaps: {},       // name → plotly colorscale
    files: [],           // rows of /api/files, as listed
    total: 0,
    active: null,        // the file shown (its id)
    selection: [],       // the files checked, in list order
    tab: "g2",
    twotime: { selection: 0 },   // the C2 block shown, shared by the image overlay and the tab
};

export function subscribe(fn) { listeners.add(fn); return () => listeners.delete(fn); }

export function update(patch) {
    const changed = [];
    Object.entries(patch).forEach(([key, value]) => {
        if (state[key] !== value) { state[key] = value; changed.push(key); }
    });
    if (changed.length) { listeners.forEach((fn) => fn(changed)); }
}

export function fileRow(id) { return state.files.find((f) => f.id === id) || null; }
export function labelOf(id) { const row = fileRow(id); return row ? row.label : id; }
export function atypeOf(id) { const row = fileRow(id); return (row && row.atype) || []; }

/** The files an analysis of several files works on: the checked ones, else the one shown. */
export function filesForAnalysis() {
    if (state.selection.length) { return state.selection.slice(); }
    return state.active ? [state.active] : [];
}
