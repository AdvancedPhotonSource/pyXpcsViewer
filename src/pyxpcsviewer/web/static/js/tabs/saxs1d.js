// The SAXS 1D tab: I(q) of the checked files — axes, normalization, offsets, every φ slice,
// a background file subtracted.
import { post, unpackFlat, unpack } from "../api.js";
import { state, subscribe, filesForAnalysis, labelOf } from "../state.js";
import { axis, logAxis, baseLayout, draw, placeholder, seriesColor, symbol, heightFor, logTicks, positiveExtent } from "../charts.js";
import { readForm, onChange, persistForm, clampNumbers, setMessage, busy, range, el } from "../widgets.js";
import { makeTab, EMPTY } from "./base.js";

const nodes = {};
let last = null;
let request = 0;
const DRAW_KEYS = new Set(["logx", "logy", "offset", "marker"]);

function redraw() {
    const form = readForm(nodes.controls);
    if (!last || !last.files.length) { placeholder(nodes.graph, last && last.skipped.length ? last.skipped[0].reason : EMPTY.none); return; }
    const data = [];
    let index = 0;
    last.files.forEach((f, m) => {
        const q = Array.from(unpackFlat(f.q));
        const lines = unpack(f.I);
        const scale = form.logy ? 10 ** ((form.offset || 0) * m) : 1;
        const shift = form.logy ? 0 : (form.offset || 0) * m;
        lines.forEach((line, k) => {
            const color = seriesColor(index);
            const y = Array.from(line, (v) => (Number.isNaN(v) ? null : v * scale + shift));
            data.push({ type: "scatter", mode: "lines+markers", x: q, y, name: f.labels[k] || f.label,
                        line: { color, width: 1.4 }, marker: { symbol: symbol(index), size: form.marker || 4, color, line: { width: 1, color } },
                        hovertemplate: `${f.labels[k] || f.label}<br>q %{x:.5g} Å⁻¹<br>I %{y:.4g}<extra></extra>` });
            index += 1;
        });
    });
    const first = last.files[0];
    const qs = positiveExtent(data.map((t) => t.x)) || [1e-3, 1];
    const is = positiveExtent(data.map((t) => t.y.filter((v) => v !== null))) || [1e-3, 1];
    const layout = baseLayout({
        height: heightFor(nodes.graph), margin: { l: 58, r: 14, t: 18, b: 44 },
        xaxis: (form.logx ? logAxis : axis)({ title: { text: first.xlabel }, ...(form.logx ? logTicks(...qs) : {}) }),
        yaxis: (form.logy ? logAxis : axis)({ title: { text: first.ylabel }, ...(form.logy ? logTicks(...is) : {}) }),
    });
    draw(nodes.graph, data, layout);
    setMessage(nodes.message, last.skipped.map((s) => s.reason).join(" · "), "note");
}

async function refresh() {
    const ids = filesForAnalysis();
    const id = ++request;
    if (!ids.length) { last = null; redraw(); return; }
    const form = readForm(nodes.controls);
    busy(nodes.result, true);
    try {
        const result = await post("/api/saxs1d", {
            names: ids, q_range: range(form.qmin, form.qmax), norm: form.norm || "none", sampling: form.sampling || 1,
            all_phi: form.allphi, background: form.bkg || null, bkg_weight: form.weight ?? 1, absolute: form.absolute,
        });
        if (id !== request) { return; }
        last = result;
        redraw();
    } catch (error) {
        if (id !== request) { return; }
        last = null;
        placeholder(nodes.graph, error.message, { error: true });
    } finally {
        if (id === request) { busy(nodes.result, false); }
    }
}

function fillBackgrounds() {
    const select = nodes.controls.querySelector('[name="bkg"]');
    const current = select.value;
    select.replaceChildren(el("option", { value: "", text: "none" }));
    state.files.filter((f) => f.atype).forEach((f) => select.append(el("option", { value: f.id, text: f.label })));
    select.value = state.files.some((f) => f.id === current) ? current : "";
}

function init() {
    nodes.controls = document.getElementById("saxs1d-controls");
    nodes.graph = document.getElementById("saxs1d-graph");
    nodes.result = nodes.graph.closest(".result");
    nodes.message = document.getElementById("saxs1d-message");
    fillBackgrounds();
    persistForm(nodes.controls, "saxs1d");
    clampNumbers(nodes.controls);
    onChange(nodes.controls, (form, input) => { if (DRAW_KEYS.has(input.name)) { redraw(); } else { tab.invalidate(); } });
    subscribe((changed) => { if (changed.includes("files")) { fillBackgrounds(); } });
}

function resize() { if (last && last.files.length) { Plotly.relayout(nodes.graph, { height: heightFor(nodes.graph) }); } }

export const tab = makeTab({ id: "saxs1d", init, refresh, resize });
