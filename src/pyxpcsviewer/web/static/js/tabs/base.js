// What every analysis tab shares: it refreshes when shown and stale, and the state changes it
// depends on make it stale (a dot on its tab while it waits to be shown).
export function makeTab({ id, deps = ["active", "selection"], init = null, refresh, resize = null }) {
    const tab = {
        id, stale: true, visible: false, shown: false, init, resize,
        show() { tab.visible = true; tab.shown = true; if (tab.stale) { tab.run(); } else if (resize) { resize(); } },
        hide() { tab.visible = false; },
        invalidate() { tab.stale = true; mark(id, tab.shown && !tab.visible); if (tab.visible) { tab.run(); } },
        async run() { tab.stale = false; mark(id, false); await refresh(); },
        onState(changed) { if (changed.some((k) => deps.includes(k))) { tab.invalidate(); } },
    };
    return tab;
}

function mark(id, on) {
    const button = document.querySelector(`.tab[data-tab="${id}"]`);
    if (button) { button.classList.toggle("stale", on); }
}

export const EMPTY = {
    none: "Click a file, or check several, to show it here.",
    multitau: "Check or click a multi-tau file (MT) to show its g2.",
    twotime: "Click a two-time file (TT) to show its correlation map.",
};
