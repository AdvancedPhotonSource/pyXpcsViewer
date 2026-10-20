// pyXPCSViewer web: wires the page together — the files column, the image column, the analysis
// tabs — over the state store.
import { get } from "./api.js";
import { state, update, subscribe, labelOf } from "./state.js";
import { installGutters } from "./layout.js";
import { initFiles, loadFiles } from "./files.js";
import { initImage } from "./image.js";
import { tab as g2 } from "./tabs/g2.js";
import { tab as saxs1d } from "./tabs/saxs1d.js";
import { tab as stability } from "./tabs/stability.js";
import { tab as intt } from "./tabs/intt.js";
import { tab as tauq } from "./tabs/tauq.js";
import { tab as twotime } from "./tabs/twotime.js";
import { tab as hdf } from "./tabs/hdf.js";

const TABS = [g2, tauq, twotime, hdf];              // the right column, one shown at a time
const PANELS = [saxs1d, intt, stability];            // under the image, always shown
const TAB_KEY = "xpcsweb:tab";

function activateTab(id) {
    document.querySelectorAll(".tab[data-tab]").forEach((b) => b.classList.toggle("active", b.dataset.tab === id));
    document.querySelectorAll(".analysis-tab[data-tab]").forEach((s) => s.classList.toggle("active", s.dataset.tab === id));
    TABS.forEach((t) => { if (t.id === id) { t.show(); } else { t.hide(); } });
    try { window.localStorage.setItem(TAB_KEY, id); } catch (e) { /* no storage */ }
}

function renderStatus() {
    const status = document.getElementById("status");
    if (state.active) {
        status.textContent = labelOf(state.active);
        status.classList.remove("quiet");
    } else {
        status.textContent = "No file shown";
        status.classList.add("quiet");
    }
    document.title = state.active ? `${labelOf(state.active)} — pyXPCSViewer` : "pyXPCSViewer";
}

async function boot() {
    const [info, colormaps] = await Promise.all([get("/api/info"), get("/api/colormaps")]);
    state.info = info;
    state.colormaps = colormaps;
    document.getElementById("root").textContent = info.root;
    document.getElementById("root").title = info.root;
    document.getElementById("version").textContent = `v${info.version}`;

    // the page's URL names the file shown, the files checked and the tab (a link to share)
    const query = new URLSearchParams(window.location.search);
    let initial = query.get("tab") || "";
    if (!initial) { try { initial = window.localStorage.getItem(TAB_KEY) || "g2"; } catch (e) { initial = "g2"; } }
    if (!TABS.some((t) => t.id === initial)) { initial = "g2"; }
    state.tab = initial;

    installGutters();
    initFiles();
    await initImage();
    TABS.forEach((t) => { if (t.init) { t.init(); } });
    PANELS.forEach((panel) => { panel.init(); panel.show(); });

    document.getElementById("tabs").addEventListener("click", (event) => {
        const button = event.target.closest(".tab[data-tab]");
        if (button) { update({ tab: button.dataset.tab }); }
    });
    subscribe((changed) => {
        if (changed.includes("tab")) { activateTab(state.tab); }
        if (changed.includes("active") || changed.includes("files")) { renderStatus(); }
        TABS.forEach((t) => t.onState(changed));
        PANELS.forEach((panel) => panel.onState(changed));
    });
    window.addEventListener("resize", () => {
        const current = TABS.find((t) => t.id === state.tab);
        if (current && current.visible && current.resize) { current.resize(); }
        PANELS.forEach((panel) => { if (panel.resize) { panel.resize(); } });
    });
    document.addEventListener("keydown", (event) => {
        if (event.target.matches("input, select, textarea") || event.ctrlKey || event.metaKey || event.altKey) { return; }
        const n = Number(event.key);
        if (n >= 1 && n <= TABS.length) { update({ tab: TABS[n - 1].id }); }
    });

    activateTab(initial);
    renderStatus();
    await loadFiles();
    const patch = {};
    const wanted = query.get("file");
    if (wanted && state.files.some((f) => f.id === wanted)) { patch.active = wanted; }
    const checked = (query.get("check") || "").split(",").filter((id) => state.files.some((f) => f.id === id));
    if (checked.length) { patch.selection = checked; }
    if (Object.keys(patch).length) { update(patch); }
    subscribe((changed) => {
        if (!changed.some((k) => ["active", "selection", "tab"].includes(k))) { return; }
        const next = new URLSearchParams();
        if (state.active) { next.set("file", state.active); }
        if (state.selection.length) { next.set("check", state.selection.join(",")); }
        next.set("tab", state.tab);
        window.history.replaceState(null, "", `${window.location.pathname}?${next.toString()}`);
    });
}

boot().catch((error) => {
    document.getElementById("status").textContent = `Could not start: ${error.message}`;
    console.error(error);
});
