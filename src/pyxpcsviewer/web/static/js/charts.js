// The look of every Plotly figure of the page (the tokens of style.css), and the pieces the
// tabs build figures from: a panel grid, colors in series order, a color-scale sampler.
import { state } from "./state.js";

// categorical series colors in a fixed order (validated for color-vision deficiency as ordered)
export const SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"];
export const SYMBOLS = ["circle-open", "square-open", "diamond-open", "triangle-up-open", "triangle-down-open",
                        "pentagon-open", "hexagon-open", "star-open"];
export const INK = "#1f1f1d";
export const INK2 = "#4b4a46";
export const MUTED = "#62615d";
export const GRID = "#ecebe7";
export const SURFACE = "#ffffff";
export const ACCENT = "#2a78d6";
export const FONT = { family: "xpcs-ui, Inter, system-ui, -apple-system, 'Segoe UI', sans-serif", size: 12, color: INK };
export const CONFIG = {
    responsive: true, displaylogo: false, scrollZoom: false,
    modeBarButtonsToRemove: ["lasso2d", "select2d", "autoScale2d", "toggleSpikelines", "hoverCompareCartesian",
                             "hoverClosestCartesian"],
    toImageButtonOptions: { scale: 2 },
};

export const seriesColor = (i) => SERIES[((i % SERIES.length) + SERIES.length) % SERIES.length];
export const symbol = (i) => SYMBOLS[((i % SYMBOLS.length) + SYMBOLS.length) % SYMBOLS.length];

export function withAlpha(color, alpha) {
    const m = /^#([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})$/i.exec(color);
    if (m) { return `rgba(${parseInt(m[1], 16)},${parseInt(m[2], 16)},${parseInt(m[3], 16)},${alpha})`; }
    const rgb = /rgba?\(([^)]+)\)/.exec(color);
    if (rgb) { const [r, g, b] = rgb[1].split(",").map((v) => parseFloat(v)); return `rgba(${r},${g},${b},${alpha})`; }
    return color;
}

/** An axis in the page's style; `extra` overrides. */
export function axis(extra = {}) {
    return { showline: true, linecolor: MUTED, linewidth: 1, ticks: "outside", tickcolor: MUTED, ticklen: 4,
             gridcolor: GRID, zeroline: false, exponentformat: "power", automargin: true,
             title: { standoff: 6, font: { size: 12, color: INK2 } }, ...extra };
}

/** A log axis: ranges given in data units are written as their log10. */
export function logAxis(extra = {}) {
    const out = axis({ type: "log", ...extra });
    if (extra.range) { out.range = extra.range.map((v) => Math.log10(v)); }
    return out;
}

/** Tick settings of a log axis spanning `lo` … `hi`: one per decade when there are a few,
    else 2 and 5 as well (an axis over less than a decade is labeled at every digit otherwise). */
export function logTicks(lo, hi) {
    if (!(lo > 0) || !(hi > 0)) { return {}; }
    const decades = Math.abs(Math.log10(hi) - Math.log10(lo));
    return decades >= 2.5 ? { dtick: 1 } : { dtick: "D2" };
}

/** The finite positive extent [min, max] of some arrays (for log axes), or null. */
export function positiveExtent(arrays) {
    let lo = Infinity;
    let hi = -Infinity;
    arrays.forEach((a) => { for (let i = 0; i < a.length; i += 1) { const v = a[i]; if (v > 0 && Number.isFinite(v)) { if (v < lo) { lo = v; } if (v > hi) { hi = v; } } } });
    return lo <= hi ? [lo, hi] : null;
}

export function baseLayout(extra = {}) {
    return {
        font: FONT, paper_bgcolor: SURFACE, plot_bgcolor: SURFACE,
        margin: { l: 56, r: 14, t: 26, b: 44 },
        hovermode: "closest",
        hoverlabel: { bgcolor: INK, bordercolor: INK, font: { ...FONT, color: "#fff", size: 11.5 }, align: "left" },
        legend: { bgcolor: "rgba(255,255,255,0.8)", borderwidth: 0, font: { size: 11 }, x: 1, xanchor: "right",
                  y: 1, yanchor: "top", itemsizing: "constant", tracegroupgap: 2 },
        ...extra,
    };
}

export function draw(el, data, layout, config) {
    return Plotly.react(el, data, layout, { ...CONFIG, ...(config || {}) });
}

/** An empty figure with a centered message (nothing selected yet, or an error). */
export function placeholder(el, text, { error = false } = {}) {
    return Plotly.react(el, [], baseLayout({
        xaxis: { visible: false }, yaxis: { visible: false }, margin: { l: 16, r: 16, t: 16, b: 16 },
        annotations: [{ text, showarrow: false, xref: "paper", yref: "paper", x: 0.5, y: 0.5,
                        font: { size: 13, color: error ? "#c43d3d" : MUTED } }],
    }), { ...CONFIG, displayModeBar: false });
}

/** The height a figure of `rows` panel rows takes in its (scrolling) wrapper: the wrapper's
    height, or more when the panels need it. */
export function heightFor(el, rows = 1, panelHeight = 240) {
    const wrap = el.parentElement;
    const available = Math.max(160, (wrap ? wrap.clientHeight : 0) - 4);
    if (rows <= 1) { return available; }
    return Math.max(available, rows * panelHeight + 60);
}

/**
 * `count` panels in `cols` columns, top-left first: the axis objects to merge into a layout and,
 * per panel, the axis names its traces use. Titles become small annotations above each panel.
 */
export function grid(count, cols, { titles = [], gapX = 0.12, gapY = 0.22, xaxis = {}, yaxis = {} } = {}) {
    const c = Math.max(1, Math.min(cols, count || 1));
    const rows = Math.max(1, Math.ceil((count || 1) / c));
    const layout = { annotations: [] };
    const panels = [];
    // gaps are a share of a panel's size, so any number of rows fits
    const w = 1 / (c + gapX * (c - 1));
    const h = 1 / (rows + gapY * (rows - 1));
    for (let i = 0; i < (count || 1); i += 1) {
        const col = i % c;
        const row = Math.floor(i / c);
        const n = i === 0 ? "" : String(i + 1);
        const xdomain = [col * w * (1 + gapX), col * w * (1 + gapX) + w];
        const ydomain = [1 - row * h * (1 + gapY) - h, 1 - row * h * (1 + gapY)];
        layout[`xaxis${n}`] = axis({ ...xaxis, domain: xdomain, anchor: `y${n}` });
        layout[`yaxis${n}`] = axis({ ...yaxis, domain: ydomain, anchor: `x${n}` });
        if (xaxis.type === "log" && xaxis.range) { layout[`xaxis${n}`].range = xaxis.range.map((v) => Math.log10(v)); }
        if (yaxis.type === "log" && yaxis.range) { layout[`yaxis${n}`].range = yaxis.range.map((v) => Math.log10(v)); }
        if (titles[i]) {
            layout.annotations.push({ text: titles[i], showarrow: false, xref: "paper", yref: "paper",
                                      x: xdomain[0], y: ydomain[1], xanchor: "left", yanchor: "bottom",
                                      font: { size: 11.5, color: INK2 }, yshift: 2 });
        }
        panels.push({ x: `x${n}`, y: `y${n}`, xaxis: `xaxis${n}`, yaxis: `yaxis${n}`, xdomain, ydomain, row, col });
    }
    return { layout, panels, rows, cols: c };
}

/** A legend outside the panels: along the top for a few entries (rows of about three), down the
    right side (scrolling) for many. Returns the legend and the margins it needs. */
export function outerLegend(series = 1) {
    if (series > 8) {
        return { legend: { orientation: "v", x: 1.01, xanchor: "left", y: 1, yanchor: "top", bgcolor: "rgba(255,255,255,0)",
                           font: { size: 10.5 }, itemsizing: "constant", itemwidth: 24, tracegroupgap: 0 },
                 marginTop: 24, marginRight: 150 };
    }
    const rows = Math.max(1, Math.ceil(series / 3));
    return { legend: { orientation: "h", x: 0, xanchor: "left", y: 1, yanchor: "top", yref: "container",
                       bgcolor: "rgba(255,255,255,0)", font: { size: 11 }, itemsizing: "constant", itemwidth: 30 },
             marginTop: 24 + 18 * rows, marginRight: 12 };
}

/** The Plotly color scale of a color map, from the server's table (a built-in name as a fallback). */
export function colorscale(name) {
    return state.colormaps[name] || "Viridis";
}

function parseRgb(text) {
    const m = /rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)/.exec(text);
    if (m) { return [+m[1], +m[2], +m[3]]; }
    const hex = /^#([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})$/i.exec(text);
    return hex ? [parseInt(hex[1], 16), parseInt(hex[2], 16), parseInt(hex[3], 16)] : [0, 0, 0];
}

/** The color at `t` (0 … 1) of a color scale, for series in a natural order (q bins, segments). */
export function sampleScale(scale, t) {
    if (!Array.isArray(scale) || !scale.length) { return ACCENT; }
    const v = Math.min(1, Math.max(0, t));
    let i = 0;
    while (i < scale.length - 1 && scale[i + 1][0] < v) { i += 1; }
    const [p0, c0] = scale[i];
    const [p1, c1] = scale[Math.min(i + 1, scale.length - 1)];
    const f = p1 > p0 ? (v - p0) / (p1 - p0) : 0;
    const a = parseRgb(c0);
    const b = parseRgb(c1);
    const mix = a.map((x, k) => Math.round(x + (b[k] - x) * f));
    return `rgb(${mix[0]},${mix[1]},${mix[2]})`;
}

/** A color per ordered series: a perceptual map from dark to bright (never its two ends). */
export function orderedColor(i, count, name = "viridis") {
    const t = count <= 1 ? 0.5 : 0.08 + 0.84 * (i / (count - 1));
    return sampleScale(colorscale(name), t);
}

/** A discrete color scale: `colors[k]` for values k - 0.5 … k + 0.5. */
export function discreteScale(colors) {
    const n = colors.length;
    const out = [];
    colors.forEach((c, k) => { out.push([k / n, c], [(k + 1) / n, c]); });
    return out;
}

/** The marker + error-bar style of a measured curve. */
export function markers(color, size = 6, sym = "circle-open") {
    return { symbol: sym, size, color, line: { width: 1.3, color } };
}
export function errorBars(values, color) {
    return { type: "data", array: values, visible: true, color, thickness: 1, width: 0 };
}
