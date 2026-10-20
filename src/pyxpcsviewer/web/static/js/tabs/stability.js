// The stability tab: the file shown over time — I(q) of each time segment, or (when the file
// stores them) the g2 of each segment.
import { get, file, unpackFlat, unpack } from "../api.js";
import { state } from "../state.js";
import { axis, logAxis, baseLayout, draw, placeholder, orderedColor, heightFor, logTicks, positiveExtent } from "../charts.js";
import { readForm, onChange, persistForm, clampNumbers, setMessage, busy, range } from "../widgets.js";
import { g2Figure } from "../g2figure.js";
import { makeTab, EMPTY } from "./base.js";

const nodes = {};
let last = null;
let lastRows = 1;
let request = 0;
const FETCH_KEYS = new Set(["source", "norm", "qmin", "qmax", "qauto", "tmin", "tmax", "tauto"]);

function redrawSaxs(form) {
    const q = Array.from(unpackFlat(last.q));
    const lines = unpack(last.I);
    const data = lines.map((line, k) => {
        const color = orderedColor(k, lines.length);
        return { type: "scatter", mode: "lines", x: q, y: Array.from(line, (v) => (Number.isNaN(v) ? null : v)),
                 name: last.labels[k], line: { color, width: 1.3 },
                 hovertemplate: `${last.labels[k]}<br>q %{x:.5g} Å⁻¹<br>I %{y:.4g}<extra></extra>` };
    });
    lastRows = 1;
    const qs = positiveExtent([q]) || [1e-3, 1];
    const is = positiveExtent(data.map((t) => t.y.filter((v) => v !== null))) || [1e-3, 1];
    draw(nodes.graph, data, baseLayout({
        height: heightFor(nodes.graph), margin: { l: 58, r: 14, t: 18, b: 44 },
        xaxis: (form.logx ? logAxis : axis)({ title: { text: last.xlabel }, ...(form.logx ? logTicks(...qs) : {}) }),
        yaxis: (form.logy ? logAxis : axis)({ title: { text: last.ylabel }, ...(form.logy ? logTicks(...is) : {}) }),
        title: { text: last.label, font: { size: 12 }, x: 0.02, xanchor: "left", y: 0.99, yanchor: "top" },
    }));
}

function redrawG2(form) {
    const g2 = unpack(last.g2);     // [segment][time][q]
    const err = unpack(last.err);
    const segments = g2.map((rows, s) => ({ label: `segment ${last.segments[s]}`, q: last.q, labels: last.labels,
                                            t: last.t, g2: rows, err: err[s], fit: null }));
    const fig = g2Figure(segments, { mode: form.layout || "q", cols: form.cols || 2, offset: form.offset || 0,
                                     markerSize: form.marker || 5, legend: form.legend,
                                     tRange: form.tauto ? null : range(form.tmin, form.tmax),
                                     yRange: form.yauto ? null : range(form.ymin, form.ymax) });
    lastRows = fig.rows;
    draw(nodes.graph, fig.data, { ...fig.layout, height: heightFor(nodes.graph, fig.rows, 250) });
}

function redraw() {
    const form = readForm(nodes.controls);
    if (!last) { placeholder(nodes.graph, EMPTY.none); return; }
    if (last.kind === "g2") { redrawG2(form); } else { redrawSaxs(form); }
    setMessage(nodes.message, "");
}

async function refresh() {
    const name = state.active;
    const id = ++request;
    if (!name) { last = null; redraw(); return; }
    const form = readForm(nodes.controls);
    busy(nodes.result, true);
    try {
        let result;
        if (form.source === "g2") {
            const q = form.qauto ? null : range(form.qmin, form.qmax);
            const t = form.tauto ? null : range(form.tmin, form.tmax);
            result = await get(`${file(name)}/g2_stability`, { q_min: q && q[0], q_max: q && q[1], t_min: t && t[0], t_max: t && t[1] });
            result.kind = "g2";
        } else {
            result = await get(`${file(name)}/stability`, { norm: form.norm || "none" });
            result.kind = "saxs";
        }
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

function showSource() {
    const form = readForm(nodes.controls);
    nodes.controls.querySelectorAll("[data-source]").forEach((node) => {
        node.hidden = node.dataset.source !== (form.source || "saxs");
    });
}

function init() {
    nodes.controls = document.getElementById("stability-controls");
    nodes.graph = document.getElementById("stability-graph");
    nodes.result = nodes.graph.closest(".result");
    nodes.message = document.getElementById("stability-message");
    persistForm(nodes.controls, "stability");
    clampNumbers(nodes.controls);
    showSource();
    onChange(nodes.controls, (form, input) => {
        if (input.name === "source") { showSource(); }
        if (FETCH_KEYS.has(input.name)) { tab.invalidate(); } else { redraw(); }
    });
}

function resize() { if (last) { Plotly.relayout(nodes.graph, { height: heightFor(nodes.graph, lastRows, 250) }); } }

export const tab = makeTab({ id: "stability", deps: ["active"], init, refresh, resize });
