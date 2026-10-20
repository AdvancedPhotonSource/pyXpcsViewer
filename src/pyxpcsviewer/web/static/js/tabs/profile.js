// The I(q) panel under the image, one of three views: the I(q) of each time segment of the file
// shown (its stability), the g2 of each segment (when the file stores them), or the SAXS 1D of
// the checked files.
import { get, post, file, unpackFlat, unpack } from "../api.js";
import { state, filesForAnalysis } from "../state.js";
import { axis, logAxis, baseLayout, draw, placeholder, seriesColor, symbol, orderedColor, heightFor, logTicks,
         positiveExtent } from "../charts.js";
import { readForm, onChange, persistForm, clampNumbers, setMessage, busy } from "../widgets.js";
import { g2Figure } from "../g2figure.js";
import { makeTab, EMPTY } from "./base.js";

const nodes = {};
let last = null;       // the server's answer, with .mode
let lastRows = 1;
let request = 0;
const FETCH_KEYS = new Set(["mode", "allphi", "absolute"]);

function profileAxes(form, xlabel, ylabel, xs, ys) {
    return {
        xaxis: (form.logx ? logAxis : axis)({ title: { text: xlabel }, ...(form.logx ? logTicks(...xs) : {}) }),
        yaxis: (form.logy ? logAxis : axis)({ title: { text: ylabel }, ...(form.logy ? logTicks(...ys) : {}) }),
    };
}

function drawSegments(form) {
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
        height: heightFor(nodes.graph), margin: { l: 50, r: 10, t: 10, b: 36 }, legend: { font: { size: 9.5 } },
        ...profileAxes(form, last.xlabel, last.ylabel, qs, is),
    }));
    setMessage(nodes.message, `${last.label} — I(q) of ${lines.length} time segments, dark first`, "note");
}

function drawSegmentG2(form) {
    const g2 = unpack(last.g2);     // [segment][time][q]
    const err = unpack(last.err);
    const segments = g2.map((rows, s) => ({ label: `segment ${last.segments[s]}`, q: last.q, labels: last.labels,
                                            t: last.t, g2: rows, err: err[s], fit: null }));
    const fig = g2Figure(segments, { mode: form.layout || "q", cols: form.cols || 2, markerSize: 4, legend: true });
    lastRows = fig.rows;
    draw(nodes.graph, fig.data, { ...fig.layout, height: heightFor(nodes.graph, fig.rows, 220) });
    setMessage(nodes.message, `${last.label} — g2 of ${segments.length} time segments`, "note");
}

function drawSaxs1d(form) {
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
    lastRows = 1;
    const first = last.files[0];
    const qs = positiveExtent(data.map((t) => t.x)) || [1e-3, 1];
    const is = positiveExtent(data.map((t) => t.y.filter((v) => v !== null))) || [1e-3, 1];
    draw(nodes.graph, data, baseLayout({
        height: heightFor(nodes.graph), margin: { l: 50, r: 10, t: 10, b: 36 },
        ...profileAxes(form, first.xlabel, first.ylabel, qs, is),
    }));
    setMessage(nodes.message, last.skipped.map((s) => s.reason).join(" · "), "note");
}

function redraw() {
    const form = readForm(nodes.controls);
    if (!last) { placeholder(nodes.graph, EMPTY.none); setMessage(nodes.message, ""); return; }
    if (last.mode === "saxs1d") {
        if (!last.files.length) { placeholder(nodes.graph, last.skipped.length ? last.skipped[0].reason : EMPTY.none); return; }
        drawSaxs1d(form);
    } else if (last.mode === "g2") { drawSegmentG2(form); } else { drawSegments(form); }
}

async function refresh() {
    const form = readForm(nodes.controls);
    const mode = form.mode || "saxs";
    const id = ++request;
    const ids = mode === "saxs1d" ? filesForAnalysis() : (state.active ? [state.active] : []);
    if (!ids.length) { last = null; redraw(); return; }
    busy(nodes.panel, true);
    try {
        let result;
        if (mode === "saxs1d") {
            result = await post("/api/saxs1d", { names: ids, all_phi: form.allphi, absolute: form.absolute });
        } else if (mode === "g2") {
            result = await get(`${file(ids[0])}/g2_stability`);
        } else {
            result = await get(`${file(ids[0])}/stability`);
        }
        if (id !== request) { return; }
        result.mode = mode;
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

function showMode() {
    const mode = readForm(nodes.controls).mode || "saxs";
    nodes.controls.querySelectorAll("[data-mode]").forEach((node) => {
        node.hidden = !node.dataset.mode.split(" ").includes(mode);
    });
}

function init() {
    nodes.controls = document.getElementById("profile-controls");
    nodes.graph = document.getElementById("profile-graph");
    nodes.panel = document.getElementById("profile-panel");
    nodes.message = document.getElementById("profile-message");
    persistForm(nodes.controls, "profile");
    clampNumbers(nodes.controls);
    showMode();
    onChange(nodes.controls, (form, input) => {
        if (input.name === "mode") { showMode(); }
        if (FETCH_KEYS.has(input.name)) { tab.invalidate(); } else { redraw(); }
    });
}

function resize() { if (last) { Plotly.relayout(nodes.graph, { height: heightFor(nodes.graph, lastRows, 220) }); } }

export const tab = makeTab({ id: "profile", init, refresh, resize });
