// The image column: the detector map of the file shown (intensity, q-bins, mask) with its color
// settings, the beam center, the q-bins as an overlay (the two-time bin shown highlighted), a
// readout of the pixel under the cursor; a click picks the two-time bin.
import { get, file, unpack, unpackFlat } from "./api.js";
import { state, update, subscribe } from "./state.js";
import { axis, baseLayout, colorscale, discreteScale, draw, placeholder, SERIES, ACCENT } from "./charts.js";
import { readForm, onChange, persistForm, debounce, busy, fmt, el } from "./widgets.js";

const nodes = {};
let request = 0;
const cache = { file: null, image: null, overlay: null, bins: null };
const HINT = "Hover over the image for q and φ. Scroll to zoom, double-click to reset; click a q-bin to show its two-time correlation.";

/** The color levels of a map: the 1st to the 99.9th percentile of an intensity image (the server
    computes them), the whole range of a label map. */
function levels(image) {
    const zmin = image.zmin;
    const zmax = image.zmax > zmin ? image.zmax : zmin + 1e-6;
    return [zmin, zmax];
}

function overlayTraces(overlay, image, form) {
    const traces = [];
    if (!overlay) { return traces; }
    const rows = unpack(overlay.z);
    const selectedBin = selectedQbin();
    const cat = rows.map((r) => Array.from(r, (v) => (Number.isNaN(v) ? NaN : (v - 1) % SERIES.length)));
    traces.push({ type: "heatmap", z: cat, x0: overlay.x0, dx: overlay.factor, y0: overlay.y0, dy: overlay.factor,
                  colorscale: discreteScale(SERIES), zmin: -0.5, zmax: SERIES.length - 0.5, opacity: 0.4,
                  showscale: false, hoverinfo: "none", zsmooth: false, name: "q-bins" });
    if (selectedBin !== null && form.kind === "saxs") {
        const hl = rows.map((r) => Array.from(r, (v) => (v === selectedBin ? 1 : NaN)));
        traces.push({ type: "heatmap", z: hl, x0: overlay.x0, dx: overlay.factor, y0: overlay.y0, dy: overlay.factor,
                      colorscale: [[0, "#ffffff"], [1, "#ffffff"]], zmin: 0, zmax: 1, opacity: 0.85, showscale: false,
                      hoverinfo: "none", zsmooth: false, name: "two-time bin" });
    }
    return traces;
}

/** The q-bin (the dqmap's value) of the two-time block shown, when the file shown is a two-time file. */
function selectedQbin() {
    if (!cache.bins || cache.bins.file !== state.active) { return null; }
    const entry = cache.bins.bins[state.twotime.selection];
    return entry ? entry.qbin : null;
}

function render() {
    const image = cache.image;
    const form = readForm(nodes.toolbar);
    if (!image) { return; }
    const z = unpack(image.z);
    const [zmin, zmax] = levels(image);
    const main = { type: "heatmap", z, x0: image.x0, dx: image.factor, y0: image.y0, dy: image.factor, zmin, zmax,
                   zsmooth: false, hoverinfo: "none", showscale: image.kind !== "mask", name: image.kind,
                   colorbar: { thickness: 9, len: 0.85, outlinewidth: 0, tickfont: { size: 9.5 }, x: 1.005,
                               title: { text: image.kind === "saxs" ? (image.scale === "log" ? "log₁₀ I" : "I") : "bin",
                                        side: "right", font: { size: 10 } } } };
    if (image.kind === "saxs") { main.colorscale = colorscale(form.cmap); }
    else if (image.kind === "mask") { main.colorscale = [[0, "#e9e8e4"], [1, ACCENT]]; }
    else {
        main.colorscale = colorscale(form.cmap === "gray" ? "viridis" : form.cmap);
    }
    const traces = [main, ...(form.bins && image.kind === "saxs" ? overlayTraces(cache.overlay, image, form) : [])];
    if (form.center) {
        const [bx, by] = image.beam_center;
        traces.push({ type: "scatter", x: [bx], y: [by], mode: "markers", hoverinfo: "none", showlegend: false,
                      marker: { symbol: "cross-thin", size: 16, color: "rgba(0,0,0,0)", line: { width: 4, color: "rgba(0,0,0,0.55)" } } });
        traces.push({ type: "scatter", x: [bx], y: [by], mode: "markers", hoverinfo: "none", showlegend: false,
                      marker: { symbol: "cross-thin", size: 16, color: "rgba(0,0,0,0)", line: { width: 1.6, color: "#ffffff" } } });
    }
    const [h, w] = image.shape_full;
    const layout = baseLayout({
        margin: { l: 46, r: 10, t: 8, b: 36 }, showlegend: false, dragmode: "pan",
        xaxis: axis({ title: { text: "column (px)" }, constrain: "domain", range: [-0.5, w - 0.5], exponentformat: "none" }),
        yaxis: axis({ title: { text: "row (px)" }, scaleanchor: "x", scaleratio: 1, constrain: "domain",
                      range: [-0.5, h - 0.5], exponentformat: "none" }),
        uirevision: `${image.file}:${w}x${h}`,
    });
    draw(nodes.graph, traces, layout, { scrollZoom: true, doubleClick: "reset" });
}

async function refresh({ keep = false } = {}) {
    const name = state.active;
    const form = readForm(nodes.toolbar);
    const id = ++request;
    if (!name) {
        cache.file = null; cache.image = null; cache.overlay = null; cache.bins = null;
        placeholder(nodes.graph, "Click a file to show its detector image.");
        nodes.readout.textContent = HINT;
        return;
    }
    const sameFile = keep && cache.file === name;
    busy(nodes.wrap, true);
    try {
        const kind = form.kind || "saxs";
        const scale = form.scale || "log";
        const maxSize = Number(form.size);
        const imageKey = `${kind}|${scale}|${maxSize}`;
        const needImage = !(sameFile && cache.image && cache.imageKey === imageKey);
        const wantOverlay = form.bins && kind === "saxs";
        const needOverlay = wantOverlay && !(sameFile && cache.overlay && cache.overlayKey === String(maxSize));
        const isTwotime = ((state.files.find((f) => f.id === name) || {}).atype || []).includes("Twotime");
        const needBins = isTwotime && !(cache.bins && cache.bins.file === name);
        const [image, overlay, bins] = await Promise.all([
            needImage ? get(`${file(name)}/image`, { kind, scale, max_size: maxSize }) : cache.image,
            needOverlay ? get(`${file(name)}/image`, { kind: "dqmap", scale: "linear", max_size: maxSize }) : (wantOverlay ? cache.overlay : null),
            needBins ? get(`${file(name)}/twotime/bins`) : (isTwotime ? cache.bins : null),
        ]);
        if (id !== request) { return; }
        cache.file = name; cache.image = image; cache.overlay = overlay; cache.bins = bins;
        cache.imageKey = imageKey; cache.overlayKey = String(maxSize);
        render();
        if (!sameFile) { nodes.readout.textContent = HINT; }
    } catch (error) {
        if (id !== request) { return; }
        placeholder(nodes.graph, `${name}: ${error.message}`, { error: true });
    } finally {
        if (id === request) { busy(nodes.wrap, false); }
    }
}

const readout = debounce(async (x, y) => {
    const name = state.active;
    if (!name) { return; }
    try {
        const p = await get(`${file(name)}/pixel`, { x, y });
        if (name !== state.active) { return; }
        if (!p.on_detector) { nodes.readout.textContent = "Outside the detector."; return; }
        const sep = () => el("span", { class: "sep", text: "·" });
        const parts = [el("b", { text: `x ${p.x}, y ${p.y}` }), sep(), `I ${fmt(p.intensity)}`, sep(),
                       `q ${fmt(p.q, 5)} Å⁻¹`, sep(), `φ ${fmt(p.phi, 4)}°`, sep(),
                       `qx ${fmt(p.qx, 4)}, qy ${fmt(p.qy, 4)}`];
        if (p.masked) { parts.push(sep(), el("span", { class: "muted", text: "masked" })); }
        if (p.dq_bin > 0) { parts.push(sep(), `bin ${p.dq_bin} (${p.dq_label})`); }
        if (p.sq_bin > 0) { parts.push(sep(), `static bin ${p.sq_bin}`); }
        nodes.readout.replaceChildren(...parts);
    } catch (e) { /* the next hover tries again */ }
}, 40);

async function pickBin(x, y) {
    const name = state.active;
    if (!name || !cache.bins || cache.bins.file !== name) { return; }
    try {
        const hit = await get(`${file(name)}/twotime/bin_at`, { x, y });
        if (hit.selection !== null && hit.selection !== undefined) {
            update({ twotime: { ...state.twotime, selection: hit.selection } });
            if (state.tab !== "twotime") { update({ tab: "twotime" }); }
        }
    } catch (e) { /* not a two-time file */ }
}

export async function initImage() {
    nodes.toolbar = document.getElementById("image-toolbar");
    nodes.graph = document.getElementById("image-graph");
    nodes.wrap = nodes.graph.parentElement;
    nodes.readout = document.getElementById("image-readout");
    nodes.cmap = nodes.toolbar.querySelector('[name="cmap"]');
    (state.info ? state.info.colormaps : []).forEach((name) => nodes.cmap.append(el("option", { value: name, text: name })));
    persistForm(nodes.toolbar, "image");
    onChange(nodes.toolbar, (form, input) => {
        if (input.name === "cmap") {
            if (cache.image && cache.image.kind !== "mask") { Plotly.restyle(nodes.graph, { colorscale: [colorscale(form.cmap)] }, [0]); }
            return;
        }
        if (input.name === "center") { render(); return; }
        refresh({ keep: true });
    });
    await placeholder(nodes.graph, "Click a file to show its detector image.");
    nodes.graph.on("plotly_hover", (event) => {
        const p = event.points && event.points[0];
        if (p && typeof p.x === "number" && typeof p.y === "number") { readout(p.x, p.y); }
    });
    nodes.graph.on("plotly_click", (event) => {
        const p = event.points && event.points[0];
        if (p && typeof p.x === "number" && typeof p.y === "number") { pickBin(p.x, p.y); }
    });
    if (state.tab === "twotime") { nodes.toolbar.querySelector('[name="bins"]').checked = true; }
    subscribe((changed) => {
        if (changed.includes("active")) { refresh(); }
        else if (changed.includes("twotime") && cache.image) { render(); }
        if (changed.includes("tab") && state.tab === "twotime") {
            const bins = nodes.toolbar.querySelector('[name="bins"]');
            if (!bins.checked) { bins.checked = true; refresh({ keep: true }); }
        }
    });
    refresh();
}
