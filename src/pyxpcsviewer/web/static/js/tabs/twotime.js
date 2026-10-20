// The two-time tab: the C2 correlation map of one q-bin of the file shown (picked here or by a
// click on the image), its color levels, and the g2 computed from it over the whole run and
// per time segment.
import { get, file, unpack, unpackFlat } from "../api.js";
import { state, update, subscribe, atypeOf } from "../state.js";
import { axis, logAxis, baseLayout, draw, placeholder, colorscale, orderedColor, INK, logTicks } from "../charts.js";
import { readForm, onChange, persistForm, clampNumbers, setMessage, busy, el, fmt } from "../widgets.js";
import { makeTab, EMPTY } from "./base.js";

const nodes = {};
let bins = null;       // /twotime/bins of the file shown
let last = null;       // the C2 shown
let request = 0;
const LEVEL_KEYS = new Set(["autolevel", "vmin", "vmax", "cmap"]);

function levelAt(levels, percent) { return levels[Math.min(levels.length - 1, Math.round(percent * 2))]; }

function levels(form) {
    if (!last) { return [0, 1]; }
    if (!form.autolevel && form.vmin !== null && form.vmax !== null && form.vmax > form.vmin) { return [form.vmin, form.vmax]; }
    const table = unpackFlat(last.levels);
    return [levelAt(table, 0.5), levelAt(table, 99.5)];
}

function redrawC2() {
    const form = readForm(nodes.controls);
    const [zmin, zmax] = levels(form);
    const z = unpack(last.c2);
    const dt = last.delta_t;
    const extent = last.shape[0] * dt;
    draw(nodes.c2, [{
        type: "heatmap", z, x0: dt / 2, dx: dt, y0: dt / 2, dy: dt, zmin, zmax, zsmooth: false, colorscale: colorscale(form.cmap),
        colorbar: { thickness: 9, len: 0.9, outlinewidth: 0, tickfont: { size: 9.5 }, x: 1.005, title: { text: "C2", side: "right", font: { size: 10 } } },
        hovertemplate: "t₁ %{x:.4g} s<br>t₂ %{y:.4g} s<br>C2 %{z:.4f}<extra></extra>",
    }], baseLayout({
        margin: { l: 52, r: 8, t: 10, b: 40 }, showlegend: false, dragmode: "pan",
        xaxis: axis({ title: { text: "t₁ (s)" }, constrain: "domain", range: [0, extent] }),
        yaxis: axis({ title: { text: "t₂ (s)" }, scaleanchor: "x", scaleratio: 1, constrain: "domain", range: [0, extent] }),
        uirevision: `${last.file}:${last.shape[0]}:${dt}`,
    }), { scrollZoom: true });
    if (!form.autolevel && (form.vmin === null || form.vmax === null)) {
        nodes.controls.querySelector('[name="vmin"]').value = fmt(zmin, 4);
        nodes.controls.querySelector('[name="vmax"]').value = fmt(zmax, 4);
    }
}

function redrawG2() {
    const form = readForm(nodes.controls);
    const full = unpackFlat(last.g2_full);
    const partial = unpack(last.g2_partial);
    const period = last.acquire_period;
    const data = [];
    partial.forEach((row, n) => {
        const x = [];
        const y = [];
        for (let i = 1; i < row.length; i += 1) { x.push(i * period); y.push(row[i]); }
        data.push({ type: "scatter", mode: "lines", x, y, name: `segment ${n + 1}`, line: { color: orderedColor(n, partial.length), width: 1 },
                    hovertemplate: `segment ${n + 1}<br>t %{x:.4g} s<br>g2 %{y:.4f}<extra></extra>` });
    });
    const x = [];
    const y = [];
    for (let i = 1; i < full.length; i += 1) { x.push(i * period); y.push(full[i]); }
    data.push({ type: "scatter", mode: "lines", x, y, name: "whole run", line: { color: INK, width: 2.2 },
                hovertemplate: "whole run<br>t %{x:.4g} s<br>g2 %{y:.4f}<extra></extra>" });
    draw(nodes.g2, data, baseLayout({
        margin: { l: 46, r: 8, t: 8, b: 32 }, legend: { font: { size: 9.5 } },
        xaxis: (form.g2log ? logAxis : axis)({ title: { text: "t (s)" }, ...(form.g2log ? logTicks(period, full.length * period) : {}) }),
        yaxis: axis({ title: { text: "g2" } }),
    }));
}

async function loadC2() {
    const name = state.active;
    const id = ++request;
    if (!name || !bins || !bins.bins.length) { return; }
    const form = readForm(nodes.controls);
    const selection = Math.min(state.twotime.selection, bins.bins.length - 1);
    busy(nodes.result, true);
    try {
        const result = await get(`${file(name)}/twotime/c2`, { selection, correct_diag: form.diag, max_size: form.maxsize || 512 });
        if (id !== request) { return; }
        last = result;
        redrawC2();
        redrawG2();
        setMessage(nodes.message, `${last.label} — ${last.bin_label} (bin ${last.qbin})`, "note");
    } catch (error) {
        if (id !== request) { return; }
        last = null;
        placeholder(nodes.c2, error.message, { error: true });
        placeholder(nodes.g2, "");
    } finally {
        if (id === request) { busy(nodes.result, false); }
    }
}

function fillBins() {
    nodes.bin.replaceChildren();
    (bins ? bins.bins : []).forEach((b) => nodes.bin.append(el("option", { value: b.index, text: b.label })));
    nodes.bin.disabled = !bins;
    nodes.prev.disabled = !bins;
    nodes.next.disabled = !bins;
    if (bins) { nodes.bin.value = String(Math.min(state.twotime.selection, bins.bins.length - 1)); }
}

async function refresh() {
    const name = state.active;
    const id = ++request;
    if (!name || !atypeOf(name).includes("Twotime")) {
        bins = null; last = null; fillBins();
        placeholder(nodes.c2, EMPTY.twotime);
        placeholder(nodes.g2, "");
        setMessage(nodes.message, "");
        return;
    }
    busy(nodes.result, true);
    try {
        const result = await get(`${file(name)}/twotime/bins`);
        if (id !== request) { return; }
        bins = result;
        if (state.twotime.selection >= bins.bins.length) { update({ twotime: { ...state.twotime, selection: 0 } }); }
        fillBins();
        await loadC2();
    } catch (error) {
        if (id !== request) { return; }
        bins = null;
        placeholder(nodes.c2, error.message, { error: true });
    } finally {
        if (id === request) { busy(nodes.result, false); }
    }
}

function select(index) {
    if (!bins) { return; }
    const n = Math.max(0, Math.min(bins.bins.length - 1, index));
    if (n !== state.twotime.selection) { update({ twotime: { ...state.twotime, selection: n } }); }
}

function init() {
    nodes.controls = document.getElementById("twotime-controls");
    nodes.c2 = document.getElementById("twotime-c2");
    nodes.g2 = document.getElementById("twotime-g2");
    nodes.result = nodes.c2.closest(".result");
    nodes.message = document.getElementById("twotime-message");
    nodes.bin = document.getElementById("twotime-bin");
    nodes.prev = document.getElementById("twotime-prev");
    nodes.next = document.getElementById("twotime-next");
    const cmap = nodes.controls.querySelector('[name="cmap"]');
    (state.info ? state.info.colormaps : []).forEach((n) => cmap.append(el("option", { value: n, text: n })));
    persistForm(nodes.controls, "twotime");
    clampNumbers(nodes.controls);
    fillBins();
    nodes.bin.addEventListener("change", () => select(Number(nodes.bin.value)));
    nodes.prev.addEventListener("click", () => select(state.twotime.selection - 1));
    nodes.next.addEventListener("click", () => select(state.twotime.selection + 1));
    onChange(nodes.controls, (form, input) => {
        if (!last) { return; }
        if (LEVEL_KEYS.has(input.name)) { redrawC2(); }
        else if (input.name === "g2log") { redrawG2(); }
        else { loadC2(); }
    });
    subscribe((changed) => {
        if (changed.includes("twotime")) {
            if (bins) { nodes.bin.value = String(state.twotime.selection); }
            if (tab.visible && bins) { loadC2(); } else { tab.stale = true; }
        }
    });
    document.addEventListener("keydown", (event) => {
        if (!tab.visible || event.target.matches("input, select, textarea")) { return; }
        if (event.key === "ArrowRight" || event.key === "]") { select(state.twotime.selection + 1); }
        else if (event.key === "ArrowLeft" || event.key === "[") { select(state.twotime.selection - 1); }
    });
}

function resize() { if (last) { Plotly.Plots.resize(nodes.c2); Plotly.Plots.resize(nodes.g2); } }

export const tab = makeTab({ id: "twotime", deps: ["active"], init, refresh, resize });
