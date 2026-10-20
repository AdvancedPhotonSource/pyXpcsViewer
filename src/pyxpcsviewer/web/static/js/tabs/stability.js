// The stability panel under the image: the file shown over time — I(q) of each time segment, or
// (when the file stores them) the g2 of each segment.
import { get, file, unpackFlat, unpack } from "../api.js";
import { state } from "../state.js";
import { axis, logAxis, baseLayout, draw, placeholder, orderedColor, heightFor, logTicks, positiveExtent } from "../charts.js";
import { readForm, onChange, persistForm, clampNumbers, setMessage, busy } from "../widgets.js";
import { g2Figure } from "../g2figure.js";
import { makeTab, EMPTY } from "./base.js";

const nodes = {};
let last = null;
let lastRows = 1;
let request = 0;

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
        height: heightFor(nodes.graph), margin: { l: 50, r: 10, t: 10, b: 36 },
        xaxis: (form.logx ? logAxis : axis)({ title: { text: last.xlabel }, ...(form.logx ? logTicks(...qs) : {}) }),
        yaxis: (form.logy ? logAxis : axis)({ title: { text: last.ylabel }, ...(form.logy ? logTicks(...is) : {}) }),
        legend: { font: { size: 9.5 } },
    }));
}

function redrawG2(form) {
    const g2 = unpack(last.g2);     // [segment][time][q]
    const err = unpack(last.err);
    const segments = g2.map((rows, s) => ({ label: `segment ${last.segments[s]}`, q: last.q, labels: last.labels,
                                            t: last.t, g2: rows, err: err[s], fit: null }));
    const fig = g2Figure(segments, { mode: form.layout || "q", cols: form.cols || 2, markerSize: 4, legend: true });
    lastRows = fig.rows;
    draw(nodes.graph, fig.data, { ...fig.layout, height: heightFor(nodes.graph, fig.rows, 220) });
}

function redraw() {
    const form = readForm(nodes.controls);
    if (!last) { placeholder(nodes.graph, EMPTY.none); return; }
    if (last.kind === "g2") { redrawG2(form); } else { redrawSaxs(form); }
    setMessage(nodes.message, last.label, "note");
}

async function refresh() {
    const name = state.active;
    const id = ++request;
    if (!name) { last = null; redraw(); setMessage(nodes.message, ""); return; }
    const form = readForm(nodes.controls);
    busy(nodes.panel, true);
    try {
        let result;
        if (form.source === "g2") {
            result = await get(`${file(name)}/g2_stability`);
            result.kind = "g2";
        } else {
            result = await get(`${file(name)}/stability`);
            result.kind = "saxs";
        }
        if (id !== request) { return; }
        last = result;
        redraw();
    } catch (error) {
        if (id !== request) { return; }
        last = null;
        setMessage(nodes.message, "");
        placeholder(nodes.graph, error.message, { error: true });
    } finally {
        if (id === request) { busy(nodes.panel, false); }
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
    nodes.panel = document.getElementById("stability-panel");
    nodes.message = document.getElementById("stability-message");
    persistForm(nodes.controls, "stability");
    clampNumbers(nodes.controls);
    showSource();
    onChange(nodes.controls, (form, input) => {
        if (input.name === "source") { showSource(); tab.invalidate(); } else { redraw(); }
    });
}

function resize() { if (last) { Plotly.relayout(nodes.graph, { height: heightFor(nodes.graph, lastRows, 220) }); } }

export const tab = makeTab({ id: "stability", deps: ["active"], init, refresh, resize });
