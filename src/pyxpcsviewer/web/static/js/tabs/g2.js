// The g2 tab: the multi-tau g2 of the checked files, their fits (single or double exponential,
// bounds and fixed parameters) and the fit parameters in a summary.
import { post } from "../api.js";
import { filesForAnalysis, atypeOf } from "../state.js";
import { draw, placeholder, heightFor } from "../charts.js";
import { readForm, onChange, persistForm, clampNumbers, setMessage, busy, range, fmt, el } from "../widgets.js";
import { g2Figure } from "../g2figure.js";
import { makeTab, EMPTY } from "./base.js";

const nodes = {};
let last = null;       // the server's last answer
let lastRows = 1;
let request = 0;
const FETCH_KEYS = new Set(["qmin", "qmax", "qauto", "tmin", "tmax", "tauto"]);
const PARAMS = { single: ["a", "b", "c", "d"], double: ["a", "b", "c", "d", "b2", "c2", "f"] };

function names() {
    return filesForAnalysis().filter((id) => atypeOf(id).includes("Multitau"));
}

function ranges(form) {
    return { q_range: form.qauto ? null : range(form.qmin, form.qmax),
             t_range: form.tauto ? null : range(form.tmin, form.tmax) };
}

function fitSettings(form) {
    const keys = PARAMS[form.func] || PARAMS.single;
    return {
        fit_func: form.func || "single",
        bounds: [keys.map((k) => form[`${k}_min`]), keys.map((k) => form[`${k}_max`])],
        fit_flag: keys.map((k) => Boolean(form[`${k}_fit`])),
    };
}

function redraw() {
    const form = readForm(nodes.controls);
    if (!last || !last.files.length) {
        placeholder(nodes.graph, last && last.skipped.length ? last.skipped[0].reason : EMPTY.multitau);
        lastRows = 1;
        return;
    }
    const fig = g2Figure(last.files, {
        mode: form.layout || "q", cols: form.cols || 2, showFit: form.showfit,
        subtractBaseline: form.baseline, markerSize: form.marker || 6, legend: form.legend,
        tRange: form.tauto ? null : range(form.tmin, form.tmax), yRange: form.yauto ? null : range(form.ymin, form.ymax),
    });
    lastRows = fig.rows;
    draw(nodes.graph, fig.data, { ...fig.layout, height: heightFor(nodes.graph, fig.rows, 230) });
    const notes = last.skipped.map((s) => s.reason);
    if (form.showfit && !last.files.some((f) => f.fit)) { notes.push("No fit yet: press Fit g2."); }
    setMessage(nodes.message, notes.join(" · "), "note");
    renderFitInfo();
}

const PARAM_TITLES = { a: "a · contrast", b: "b · τ (s)", c: "c · stretch", d: "d · baseline", b2: "b₂ · τ₂ (s)",
                       c2: "c₂ · stretch₂", f: "f · fraction" };

function boundsRows(fit, names) {
    const lower = fit.bounds ? fit.bounds[0] : [];
    const upper = fit.bounds ? fit.bounds[1] : [];
    const flags = fit.fit_flag || [];
    return [
        el("tr", { class: "bounds" }, [el("td", { text: "lower" }), ...names.map((_, i) => el("td", { text: fmt(lower[i], 4) }))]),
        el("tr", { class: "bounds" }, [el("td", { text: "upper" }), ...names.map((_, i) => el("td", { text: fmt(upper[i], 4) }))]),
        el("tr", { class: "bounds" }, [el("td", { text: "fit" }), ...names.map((_, i) => el("td", { text: flags[i] === false ? "fixed" : "✓" }))]),
    ];
}

const sameSettings = (a, b) => JSON.stringify([a.bounds, a.fit_flag, a.func]) === JSON.stringify([b.bounds, b.fit_flag, b.func]);

/** The fit results as a table: the bounds and flags on top, then every q-bin of every file. */
function renderFitInfo() {
    const fitted = (last ? last.files : []).filter((f) => f.fit);
    nodes.info.hidden = !fitted.length;
    if (!fitted.length) { nodes.info.replaceChildren(); return; }
    const first = fitted[0].fit;
    const names = first.param_names;
    const head = el("tr", {}, [el("th", { text: "q (Å⁻¹)" }), ...names.map((n) => el("th", { text: PARAM_TITLES[n] || n }))]);
    const rows = boundsRows(first, names);
    fitted.forEach((f) => {
        const own = f.fit.param_names.length === names.length ? f.fit : null;
        rows.push(el("tr", { class: "group" }, [el("td", { colspan: names.length + 1, text: f.label })]));
        if (!own) {
            rows.push(el("tr", {}, [el("td", { colspan: names.length + 1, class: "failed", text: `fitted with the ${f.fit.func} exponential` })]));
            return;
        }
        if (!sameSettings(own, first)) { rows.push(...boundsRows(own, names)); }
        f.q.forEach((q, n) => {
            const cells = [el("td", { text: fmt(q, 5) })];
            if (!own.success[n]) {
                cells.push(el("td", { colspan: names.length, class: "failed", text: "fit failed" }));
            } else {
                names.forEach((_, i) => cells.push(el("td", {}, [fmt(own.params[n][i], 4), " ",
                                                                  el("span", { class: "err", text: `± ${fmt(own.errors[n][i], 2)}` })])));
            }
            rows.push(el("tr", {}, cells));
        });
    });
    nodes.info.replaceChildren(el("table", { class: "fit-table" }, [el("thead", {}, [head]), el("tbody", {}, rows)]));
}

async function refresh() {
    const ids = names();
    const id = ++request;
    if (!ids.length) { last = null; redraw(); return; }
    const form = readForm(nodes.controls);
    busy(nodes.result, true);
    try {
        const result = await post("/api/g2", { names: ids, ...ranges(form), with_fit: true });
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

async function fit() {
    const ids = names();
    if (!ids.length) { setMessage(nodes.message, EMPTY.multitau, "note"); return; }
    const form = readForm(nodes.controls);
    const id = ++request;
    nodes.fit.disabled = true;
    nodes.fit.textContent = "Fitting…";
    busy(nodes.result, true);
    try {
        const result = await post("/api/g2/fit", { names: ids, ...ranges(form), ...fitSettings(form) });
        if (id !== request) { return; }
        last = result;
        const show = nodes.controls.querySelector('[name="showfit"]');
        if (!show.checked) { show.checked = true; show.dispatchEvent(new Event("change", { bubbles: true })); }
        redraw();
    } catch (error) {
        if (id !== request) { return; }
        setMessage(nodes.message, error.message);
    } finally {
        nodes.fit.disabled = false;
        nodes.fit.textContent = "Fit g2";
        if (id === request) { busy(nodes.result, false); }
    }
}

function toggleDoubleRows() {
    const form = readForm(nodes.controls);
    nodes.controls.querySelectorAll("tr[data-double]").forEach((tr) => tr.classList.toggle("off", form.func !== "double"));
}

function init() {
    nodes.controls = document.getElementById("g2-controls");
    nodes.graph = document.getElementById("g2-graph");
    nodes.result = nodes.graph.closest(".result");
    nodes.message = document.getElementById("g2-message");
    nodes.info = document.getElementById("g2-fit-info");
    nodes.fit = document.getElementById("g2-fit");
    persistForm(nodes.controls, "g2");
    clampNumbers(nodes.controls);
    toggleDoubleRows();
    onChange(nodes.controls, (form, input) => {
        if (input.name === "func") { toggleDoubleRows(); return; }
        if (/_(min|max|fit)$/.test(input.name)) { return; }      // bounds act when Fit is pressed
        if (FETCH_KEYS.has(input.name)) { tab.invalidate(); } else { redraw(); }
    });
    nodes.fit.addEventListener("click", fit);
    document.getElementById("g2-clear-fit").addEventListener("click", () => {
        const show = nodes.controls.querySelector('[name="showfit"]');
        show.checked = false;
        show.dispatchEvent(new Event("change", { bubbles: true }));
    });
}

function resize() {
    if (last && last.files.length) { Plotly.relayout(nodes.graph, { height: heightFor(nodes.graph, lastRows, 230) }); }
}

export const tab = makeTab({ id: "g2", init, refresh, resize });
