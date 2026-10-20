// The I(t) tab: the intensity per frame of the checked files (smoothed, subsampled) with a range
// slider to zoom, and its Fourier spectrum.
import { post, unpackFlat } from "../api.js";
import { filesForAnalysis } from "../state.js";
import { axis, logAxis, baseLayout, draw, placeholder, seriesColor, heightFor } from "../charts.js";
import { readForm, onChange, persistForm, clampNumbers, setMessage, busy } from "../widgets.js";
import { makeTab, EMPTY } from "./base.js";

const nodes = {};
let last = null;
let request = 0;
const DRAW_KEYS = new Set(["xunit", "logfft"]);

function redraw() {
    const form = readForm(nodes.controls);
    if (!last || !last.files.length) { placeholder(nodes.graph, last && last.skipped.length ? last.skipped[0].reason : EMPTY.none); return; }
    const seconds = form.xunit === "time";
    // SVG lines up to a few ten-thousand points (they draw everywhere); WebGL beyond that
    const points = last.files.reduce((n, f) => n + f.x.shape[0], 0);
    const type = points > 60000 ? "scattergl" : "scatter";
    const data = [];
    last.files.forEach((f, m) => {
        const color = seriesColor(m);
        const frames = unpackFlat(f.x);
        const x = seconds ? Array.from(frames, (v) => v * f.frame_time) : Array.from(frames);
        data.push({ type, mode: "lines", x, y: Array.from(unpackFlat(f.y)), name: f.label, legendgroup: `f${m}`,
                    line: { color, width: 1 }, hovertemplate: `${f.label}<br>${seconds ? "t %{x:.4g} s" : "frame %{x}"}<br>I %{y:.4g}<extra></extra>` });
        data.push({ type, mode: "lines", x: Array.from(unpackFlat(f.fft_x)), y: Array.from(unpackFlat(f.fft_y)),
                    name: f.label, legendgroup: `f${m}`, showlegend: false, line: { color, width: 1 }, xaxis: "x2", yaxis: "y2",
                    hovertemplate: `${f.label}<br>%{x:.4g} Hz<br>%{y:.4g}<extra></extra>` });
    });
    const layout = baseLayout({
        height: heightFor(nodes.graph), margin: { l: 58, r: 14, t: 24, b: 40 },
        xaxis: axis({ title: { text: seconds ? "t (s)" : "frame" }, domain: [0, 1], anchor: "y",
                      rangeslider: { visible: true, thickness: 0.07, bgcolor: "#f7f6f3", bordercolor: "#e5e4df", borderwidth: 1 } }),
        yaxis: axis({ title: { text: "I (cts / pixel)" }, domain: [0.54, 1], anchor: "x" }),
        xaxis2: axis({ title: { text: "frequency (Hz)" }, domain: [0, 1], anchor: "y2" }),
        yaxis2: (form.logfft ? logAxis : axis)({ title: { text: "|FFT|" }, domain: [0, 0.26], anchor: "x2" }),
        annotations: [{ text: "Fourier spectrum", showarrow: false, xref: "paper", yref: "paper", x: 0, y: 0.26,
                        xanchor: "left", yanchor: "bottom", font: { size: 10.5, color: "#4b4a46" }, yshift: 2 }],
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
        const result = await post("/api/intt", { names: ids, window: form.window || 1, sampling: form.sampling || 1 });
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

function init() {
    nodes.controls = document.getElementById("intt-controls");
    nodes.graph = document.getElementById("intt-graph");
    nodes.result = nodes.graph.closest(".result");
    nodes.message = document.getElementById("intt-message");
    persistForm(nodes.controls, "intt");
    clampNumbers(nodes.controls);
    onChange(nodes.controls, (form, input) => { if (DRAW_KEYS.has(input.name)) { redraw(); } else { tab.invalidate(); } });
}

function resize() { if (last && last.files.length) { Plotly.relayout(nodes.graph, { height: heightFor(nodes.graph) }); } }

export const tab = makeTab({ id: "intt", init, refresh, resize });
