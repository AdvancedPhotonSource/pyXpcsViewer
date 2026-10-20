// The g2 figure shared by the g2 tab and the stability tab: curves with error bars in a grid of
// panels — one per q-bin, one per file, or all together — with the fits when asked for.
import { unpack, unpackFlat, column } from "./api.js";
import { grid, outerLegend, seriesColor, orderedColor, symbol, markers, errorBars, baseLayout, logAxis, axis, logTicks, positiveExtent } from "./charts.js";

const shortLabel = (label) => {
    const m = /^qbin=(\d+),\s*(.*)$/.exec(label || "");
    return m ? `${m[2]}  ·  bin ${m[1]}` : label;
};

/**
 * @param files [{label, q, labels, t, g2, err, fit}] as the server sends them (arrays packed)
 * @param options mode ("q" | "file" | "combined"), cols, offset, showFit, subtractBaseline,
 *        markerSize, legend, tRange, yRange, seriesLabel (the name of a file's series)
 */
export function g2Figure(files, options = {}) {
    const { mode = "q", cols = 2, offset = 0, showFit = false, subtractBaseline = true, markerSize = 6,
            legend = true, tRange = null, yRange = null } = options;
    const decoded = files.map((f) => ({
        ...f, t: unpackFlat(f.t), g2: unpack(f.g2), err: unpack(f.err),
        fitX: f.fit ? unpackFlat(f.fit.fit_x) : null, fitY: f.fit ? unpack(f.fit.fit_y) : null,
    }));
    const nq = Math.min(...decoded.map((f) => f.q.length));
    const nf = decoded.length;
    const count = mode === "q" ? nq : mode === "file" ? nf : 1;
    const titles = mode === "q" ? decoded[0].labels.slice(0, nq).map(shortLabel)
        : mode === "file" ? decoded.map((f) => f.label) : [];
    const span = tRange || positiveExtent(decoded.map((f) => f.t)) || [1e-6, 1e3];
    const xaxis = { type: "log", ...logTicks(span[0], span[1]), ...(tRange ? { range: tRange } : {}) };
    const yaxis = yRange ? { range: yRange } : {};
    const g = grid(count, cols, { titles, xaxis, yaxis });
    const data = [];
    decoded.forEach((f, m) => {
        for (let n = 0; n < nq; n += 1) {
            const panel = g.panels[mode === "q" ? n : mode === "file" ? m : 0];
            const color = mode === "file" ? orderedColor(n, nq) : seriesColor(m);
            const qName = (f.labels[n] || "").replace(/^qbin=\d+,\s*/, "");
            const name = mode === "q" ? f.label : mode === "file" ? qName : `${f.label} · ${qName}`;
            const group = mode === "q" ? `f${m}` : mode === "file" ? `q${n}` : `f${m}q${n}`;
            const first = mode === "q" ? n === 0 : mode === "file" ? m === 0 : true;
            const fitted = showFit && f.fit && f.fit.success[n];
            const shift = (fitted && subtractBaseline ? 1 - f.fit.params[n][3] : 0) + m * offset;
            const x = [];
            const y = [];
            const e = [];
            const g2 = column(f.g2, n);
            const err = column(f.err, n);
            for (let i = 0; i < f.t.length; i += 1) {
                if (f.t[i] > 0) { x.push(f.t[i]); y.push(g2[i] + shift); e.push(err[i]); }
            }
            data.push({ type: "scatter", mode: "markers", x, y, name, legendgroup: group, showlegend: legend && first,
                        xaxis: panel.x, yaxis: panel.y, marker: markers(color, markerSize, symbol(mode === "file" ? 0 : m)),
                        error_y: errorBars(e, color),
                        hovertemplate: `${name}<br>τ %{x:.4g} s<br>g2 %{y:.4f}<extra></extra>` });
            if (fitted) {
                data.push({ type: "scatter", mode: "lines", x: Array.from(f.fitX), y: Array.from(f.fitY[n], (v) => v + shift),
                            line: { color, width: 2 }, legendgroup: group, showlegend: false, hoverinfo: "skip",
                            xaxis: panel.x, yaxis: panel.y });
            }
        }
    });
    const entries = mode === "q" ? nf : mode === "file" ? nq : nf * nq;
    const outer = legend ? outerLegend(entries) : { legend: {}, marginTop: 24, marginRight: 12 };
    const layout = baseLayout({ ...g.layout, margin: { l: 50, r: outer.marginRight, t: outer.marginTop, b: 42 },
                                showlegend: legend, legend: outer.legend });
    g.panels.forEach((panel) => {
        const bottomRow = panel.row === g.rows - 1 || panel.row === Math.floor((count - 1) / g.cols);
        if (bottomRow) { layout[panel.xaxis].title = { ...layout[panel.xaxis].title, text: "τ (s)" }; }
        if (panel.col === 0) { layout[panel.yaxis].title = { ...layout[panel.yaxis].title, text: "g2" }; }
    });
    return { data, layout, rows: g.rows };
}

export { logAxis, axis };
