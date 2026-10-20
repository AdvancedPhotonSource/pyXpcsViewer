// The τ(q) tab: the relaxation times from the g2 fits of the checked files, a power law τ = a·q^b
// fitted through them, and every g2 fit parameter against q.
import { post } from "../api.js";
import { filesForAnalysis, atypeOf } from "../state.js";
import { axis, baseLayout, draw, placeholder, seriesColor, symbol, markers, errorBars, heightFor, INK2, logTicks, positiveExtent } from "../charts.js";
import { readForm, onChange, persistForm, clampNumbers, setMessage, busy, range, fmt } from "../widgets.js";
import { makeTab } from "./base.js";

const nodes = {};
let last = null;
let request = 0;
const DRAW_KEYS = new Set(["logx", "logy", "offset", "params"]);
const PANEL_H = 210;

function names() { return filesForAnalysis().filter((id) => atypeOf(id).includes("Multitau")); }

function settings(form) {
    return { q_range: range(form.qmin, form.qmax),
             bounds: [[form.a_min, form.b_min], [form.a_max, form.b_max]],
             fit_flag: [Boolean(form.a_fit), Boolean(form.b_fit)] };
}

function logAware(flag, extra) {
    const out = axis({ ...extra, ...(flag ? { type: "log" } : {}) });
    return out;
}

function redraw() {
    const form = readForm(nodes.controls);
    if (!last || !last.files.length) {
        placeholder(nodes.graph, last && last.skipped.length ? last.skipped[0].reason : "Fit the g2 of a multi-tau file first (g2 tab).");
        return;
    }
    const showParams = form.params && last.files[0].params_vs_q;
    const data = [];
    const layout = baseLayout({ margin: { l: 58, r: 14, t: 20, b: 42 }, annotations: [] });
    const mainBottom = showParams ? 0.54 : 0;
    const qs = positiveExtent(last.files.map((f) => f.q)) || [1e-3, 1e-1];
    const ts = positiveExtent(last.files.map((f) => f.tau)) || [1e-4, 1e2];
    layout.xaxis = logAware(form.logx, { title: { text: "q (Å⁻¹)" }, domain: [0, 1], anchor: "y", ...(form.logx ? logTicks(...qs) : {}) });
    layout.yaxis = logAware(form.logy, { title: { text: "τ (s)" }, domain: [mainBottom, 1], anchor: "x", ...(form.logy ? logTicks(...ts) : {}) });
    last.files.forEach((f, m) => {
        const color = seriesColor(m);
        const scale = 10 ** ((form.offset || 0) * m);
        data.push({ type: "scatter", mode: "markers", x: f.q, y: f.tau.map((v) => v / scale), name: f.label, legendgroup: `f${m}`,
                    marker: markers(color, 7, symbol(m)), error_y: errorBars(f.tau_err.map((v) => v / scale), color),
                    hovertemplate: `${f.label}<br>q %{x:.5g} Å⁻¹<br>τ %{y:.4g} s<extra></extra>` });
        if (f.fit) {
            data.push({ type: "scatter", mode: "lines", x: f.fit.x, y: f.fit.y.map((v) => v / scale), legendgroup: `f${m}`,
                        showlegend: false, line: { color, width: 2 }, hoverinfo: "skip" });
        }
    });
    if (showParams) {
        const p = last.files[0].params_vs_q;
        const count = Math.min(4, p.names.length);
        const gapX = 0.09;
        const gapY = 0.14;
        const w = (1 - gapX) / 2;
        const top = 0.42;                      // the parameter panels fill the figure below the main one
        const h = (top - gapY) / 2;
        const bounds = last.files[last.files.length - 1].params_vs_q.bounds;
        for (let i = 0; i < count; i += 1) {
            const col = i % 2;
            const row = Math.floor(i / 2);
            const n = i + 2;
            const xdomain = [col * (w + gapX), col * (w + gapX) + w];
            const ydomain = [top - row * (h + gapY) - h, top - row * (h + gapY)];
            const log = p.names[i] === "b" || p.names[i] === "b2";
            // the bounds frame each panel (as the Qt viewer), so one wild error bar cannot flatten it
            let range;
            if (bounds) {
                const lo = bounds[0][i];
                const hi = bounds[1][i];
                range = log ? [Math.log10(Math.max(lo, 1e-300) * 0.5), Math.log10(hi * 2)] : [lo - 0.15 * (hi - lo), hi + 0.15 * (hi - lo)];
            }
            layout[`xaxis${n}`] = axis({ domain: xdomain, anchor: `y${n}`, title: row === 1 ? { text: "q (Å⁻¹)" } : undefined });
            const decades = log && range ? range[1] - range[0] : 0;
            layout[`yaxis${n}`] = axis({ domain: ydomain, anchor: `x${n}`, ...(log ? { type: "log", dtick: decades > 4 ? 2 : 1 } : {}),
                                         ...(range ? { range } : {}) });
            layout.annotations.push({ text: p.titles[i], showarrow: false, xref: "paper", yref: "paper", x: xdomain[0], y: ydomain[1],
                                      xanchor: "left", yanchor: "bottom", font: { size: 11.5, color: INK2 }, yshift: 2 });
            last.files.forEach((f, m) => {
                const q = f.params_vs_q;
                const color = seriesColor(m);
                data.push({ type: "scatter", mode: "markers", x: q.q, y: q.values[i], legendgroup: `f${m}`, showlegend: false,
                            marker: markers(color, 5, symbol(m)), error_y: errorBars(q.errors[i], color), xaxis: `x${n}`, yaxis: `y${n}`,
                            hovertemplate: `${f.label}<br>q %{x:.5g}<br>${p.titles[i]} %{y:.4g}<extra></extra>` });
            });
            if (bounds) {
                const qs = last.files[last.files.length - 1].params_vs_q.q;
                const xr = [Math.min(...qs), Math.max(...qs)];
                [[bounds[0][i], "lower"], [bounds[1][i], "upper"]].forEach(([v, which]) => {
                    data.push({ type: "scatter", mode: "lines", x: xr, y: [v, v], showlegend: false, hoverinfo: "skip",
                                line: { color: "#b8b6ae", width: 1, dash: "dot" }, xaxis: `x${n}`, yaxis: `y${n}`, name: `${which} bound` });
                });
            }
        }
    }
    layout.height = heightFor(nodes.graph, showParams ? 3 : 1, PANEL_H);
    draw(nodes.graph, data, layout);
    const notes = last.skipped.map((s) => s.reason);
    setMessage(nodes.message, notes.join(" · "), "note");
    const lines = last.files.filter((f) => f.fit).map((f) =>
        `${f.label}:  τ = a·q^b   a = ${fmt(f.fit.a, 4)} ± ${fmt(f.fit.a_err, 2)}   b = ${fmt(f.fit.b, 4)} ± ${fmt(f.fit.b_err, 2)}`);
    nodes.info.textContent = lines.join("\n");
}

async function run(fit) {
    const ids = names();
    const id = ++request;
    if (!ids.length) { last = null; redraw(); return; }
    const form = readForm(nodes.controls);
    busy(nodes.result, true);
    if (fit) { nodes.fit.disabled = true; nodes.fit.textContent = "Fitting…"; }
    try {
        const result = await post("/api/tauq", { names: ids, ...settings(form), fit });
        if (id !== request) { return; }
        last = result;
        redraw();
    } catch (error) {
        if (id !== request) { return; }
        if (fit) { setMessage(nodes.message, error.message); } else { last = null; placeholder(nodes.graph, error.message, { error: true }); }
    } finally {
        if (id === request) { busy(nodes.result, false); }
        nodes.fit.disabled = false;
        nodes.fit.textContent = "Fit τ(q)";
    }
}

function init() {
    nodes.controls = document.getElementById("tauq-controls");
    nodes.graph = document.getElementById("tauq-graph");
    nodes.result = nodes.graph.closest(".result");
    nodes.message = document.getElementById("tauq-message");
    nodes.info = document.getElementById("tauq-info");
    nodes.fit = document.getElementById("tauq-fit");
    persistForm(nodes.controls, "tauq");
    clampNumbers(nodes.controls);
    onChange(nodes.controls, (form, input) => {
        if (DRAW_KEYS.has(input.name)) { redraw(); return; }
        if (/_(min|max|fit)$/.test(input.name)) { return; }
        tab.invalidate();
    });
    nodes.fit.addEventListener("click", () => run(true));
}

function resize() {
    if (!last || !last.files.length) { return; }
    const form = readForm(nodes.controls);
    Plotly.relayout(nodes.graph, { height: heightFor(nodes.graph, form.params ? 3 : 1, PANEL_H) });
}

/** The g2 tab fitted (or re-fitted) files: the τ(q) shown is stale. */
export function invalidateTauq() { tab.invalidate(); }

export const tab = makeTab({ id: "tauq", init, refresh: () => run(false), resize });
