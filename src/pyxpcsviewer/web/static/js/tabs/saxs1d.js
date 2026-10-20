// The SAXS 1D panel under the image: I(q) of the checked files (every φ slice on request).
import { post, unpackFlat, unpack } from "../api.js";
import { filesForAnalysis } from "../state.js";
import { axis, logAxis, baseLayout, draw, placeholder, seriesColor, symbol, heightFor, logTicks, positiveExtent } from "../charts.js";
import { readForm, onChange, persistForm, clampNumbers, setMessage, busy } from "../widgets.js";
import { makeTab, EMPTY } from "./base.js";

const nodes = {};
let last = null;
let request = 0;
const DRAW_KEYS = new Set(["logx", "logy", "marker"]);

function redraw() {
    const form = readForm(nodes.controls);
    if (!last || !last.files.length) { placeholder(nodes.graph, last && last.skipped.length ? last.skipped[0].reason : EMPTY.none); return; }
    const data = [];
    let index = 0;
    last.files.forEach((f) => {
        const q = Array.from(unpackFlat(f.q));
        unpack(f.I).forEach((line, k) => {
            const color = seriesColor(index);
            const name = f.labels[k] || f.label;
            data.push({ type: "scatter", mode: form.marker > 0 ? "lines+markers" : "lines", x: q,
                        y: Array.from(line, (v) => (Number.isNaN(v) ? null : v)), name, line: { color, width: 1.4 },
                        marker: { symbol: symbol(index), size: form.marker || 4, color, line: { width: 1, color } },
                        hovertemplate: `${name}<br>q %{x:.5g} Å⁻¹<br>I %{y:.4g}<extra></extra>` });
            index += 1;
        });
    });
    const first = last.files[0];
    const qs = positiveExtent(data.map((t) => t.x)) || [1e-3, 1];
    const is = positiveExtent(data.map((t) => t.y.filter((v) => v !== null))) || [1e-3, 1];
    draw(nodes.graph, data, baseLayout({
        height: heightFor(nodes.graph), margin: { l: 50, r: 10, t: 10, b: 36 },
        xaxis: (form.logx ? logAxis : axis)({ title: { text: first.xlabel }, ...(form.logx ? logTicks(...qs) : {}) }),
        yaxis: (form.logy ? logAxis : axis)({ title: { text: first.ylabel }, ...(form.logy ? logTicks(...is) : {}) }),
    }));
    setMessage(nodes.message, last.skipped.map((s) => s.reason).join(" · "), "note");
}

async function refresh() {
    const ids = filesForAnalysis();
    const id = ++request;
    if (!ids.length) { last = null; redraw(); return; }
    const form = readForm(nodes.controls);
    busy(nodes.panel, true);
    try {
        const result = await post("/api/saxs1d", { names: ids, all_phi: form.allphi, absolute: form.absolute });
        if (id !== request) { return; }
        last = result;
        redraw();
    } catch (error) {
        if (id !== request) { return; }
        last = null;
        placeholder(nodes.graph, error.message, { error: true });
    } finally {
        if (id === request) { busy(nodes.panel, false); }
    }
}

function init() {
    nodes.controls = document.getElementById("saxs1d-controls");
    nodes.graph = document.getElementById("saxs1d-graph");
    nodes.panel = document.getElementById("saxs1d-panel");
    nodes.message = document.getElementById("saxs1d-message");
    persistForm(nodes.controls, "saxs1d");
    clampNumbers(nodes.controls);
    onChange(nodes.controls, (form, input) => { if (DRAW_KEYS.has(input.name)) { redraw(); } else { tab.invalidate(); } });
}

function resize() { if (last && last.files.length) { Plotly.relayout(nodes.graph, { height: heightFor(nodes.graph) }); } }

export const tab = makeTab({ id: "saxs1d", init, refresh, resize });
