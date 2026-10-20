// The I(t) panel under the image: the intensity per frame of the checked files (averaged down to
// at most 16k points by the server) and its Fourier spectrum.
import { post, unpackFlat } from "../api.js";
import { filesForAnalysis } from "../state.js";
import { axis, baseLayout, draw, placeholder, seriesColor, heightFor } from "../charts.js";
import { readForm, onChange, persistForm, setMessage, busy } from "../widgets.js";
import { makeTab, EMPTY } from "./base.js";

const nodes = {};
let last = null;
let request = 0;

function redraw() {
    const form = readForm(nodes.controls);
    if (!last || !last.files.length) {
        placeholder(nodes.graph, last && last.skipped.length ? last.skipped[0].reason : EMPTY.none);
        nodes.note.textContent = "";
        return;
    }
    const seconds = form.xunit === "time";
    const data = [];
    last.files.forEach((f, m) => {
        const color = seriesColor(m);
        const frames = unpackFlat(f.x);
        const x = seconds ? Array.from(frames, (v) => v * f.frame_time) : Array.from(frames);
        data.push({ type: "scatter", mode: "lines", x, y: Array.from(unpackFlat(f.y)), name: f.label, legendgroup: `f${m}`,
                    line: { color, width: 1 }, hovertemplate: `${f.label}<br>${seconds ? "t %{x:.4g} s" : "frame %{x:.0f}"}<br>I %{y:.4g}<extra></extra>` });
        data.push({ type: "scatter", mode: "lines", x: Array.from(unpackFlat(f.fft_x)), y: Array.from(unpackFlat(f.fft_y)),
                    name: f.label, legendgroup: `f${m}`, showlegend: false, line: { color, width: 1 }, xaxis: "x2", yaxis: "y2",
                    hovertemplate: `${f.label}<br>%{x:.4g} Hz<br>%{y:.4g}<extra></extra>` });
    });
    draw(nodes.graph, data, baseLayout({
        height: heightFor(nodes.graph), margin: { l: 50, r: 10, t: 10, b: 34 }, showlegend: false,
        xaxis: axis({ title: { text: seconds ? "t (s)" : "frame" }, domain: [0, 1], anchor: "y" }),
        yaxis: axis({ title: { text: "I (cts / pixel)" }, domain: [0.54, 1], anchor: "x" }),
        xaxis2: axis({ title: { text: "frequency (Hz)" }, domain: [0, 1], anchor: "y2" }),
        yaxis2: axis({ title: { text: "|FFT|" }, domain: [0, 0.38], anchor: "x2" }),
    }));
    setMessage(nodes.message, last.skipped.map((s) => s.reason).join(" · "), "note");
    const averaged = last.files.filter((f) => f.points < f.frames);
    nodes.note.textContent = averaged.length
        ? `${averaged[0].frames.toLocaleString()} frames averaged to ${averaged[0].points.toLocaleString()} points` : "";
}

async function refresh() {
    const ids = filesForAnalysis();
    const id = ++request;
    if (!ids.length) { last = null; redraw(); return; }
    busy(nodes.panel, true);
    try {
        const result = await post("/api/intt", { names: ids, max_points: 16000 });
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
    nodes.controls = document.getElementById("intt-controls");
    nodes.graph = document.getElementById("intt-graph");
    nodes.panel = document.getElementById("intt-panel");
    nodes.message = document.getElementById("intt-message");
    nodes.note = document.getElementById("intt-note");
    persistForm(nodes.controls, "intt");
    onChange(nodes.controls, () => redraw());
}

function resize() { if (last && last.files.length) { Plotly.relayout(nodes.graph, { height: heightFor(nodes.graph) }); } }

export const tab = makeTab({ id: "intt", init, refresh, resize });
