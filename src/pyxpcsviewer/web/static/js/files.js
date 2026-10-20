// The files column: the folder's result files (filter, sort, rescan), the one shown and the ones
// checked, and the metadata card of the file shown.
import { get, file } from "./api.js";
import { state, update, subscribe, fileRow } from "./state.js";
import { el, debounce, setMessage } from "./widgets.js";

const nodes = {};
let anchor = null;      // the row last clicked, for shift-click ranges
let listRequest = 0;

function badges(row) {
    if (!row.atype) { return [el("span", { class: "badge bad", text: "?", title: "not a readable result file" })]; }
    return row.atype.map((t) => t === "Multitau"
        ? el("span", { class: "badge mt", text: "MT", title: "multi-tau (g2)" })
        : el("span", { class: "badge tt", text: "TT", title: "two-time (C2)" }));
}

/** A label with a line-break opportunity after every underscore or hyphen. */
function breakable(label) {
    const parts = String(label).split(/(?<=[_-])/);
    const out = [];
    parts.forEach((part, i) => { if (i) { out.push(el("wbr")); } out.push(part); });
    return out;
}

function renderRows() {
    const checked = new Set(state.selection);
    const body = nodes.rows;
    body.replaceChildren();
    if (!state.files.length) {
        body.append(el("tr", { class: "empty" }, [el("td", { colspan: 4, text: state.total
            ? "No file matches the filter." : "No result files (.hdf, .h5) in this folder." })]));
    }
    state.files.forEach((row) => {
        const tr = el("tr", { dataset: { id: row.id }, title: row.id }, [
            el("td", { class: "check" }, [el("input", { type: "checkbox", checked: checked.has(row.id),
                                                       disabled: !row.atype, "aria-label": `check ${row.label}` })]),
            el("td", { class: "name" }, breakable(row.label)),
            el("td", { class: "type" }, badges(row)),
            el("td", { class: "time" }, [row.modified.slice(0, 10), el("br"), row.modified.slice(11)]),
        ]);
        tr.classList.toggle("active", row.id === state.active);
        tr.classList.toggle("checked", checked.has(row.id));
        tr.classList.toggle("unreadable", !row.atype);
        body.append(tr);
    });
    renderHint();
}

function renderHint() {
    const shown = state.files.length;
    const n = state.selection.length;
    const parts = [`${shown}${shown < state.total ? ` of ${state.total}` : ""} file${state.total === 1 ? "" : "s"}`];
    parts.push(n ? `${n} checked` : "none checked");
    nodes.hint.replaceChildren(
        parts.join(" · "), " — ",
        el("button", { class: "link-button", type: "button", text: "check shown", onclick: () => checkShown(true) }),
        " · ",
        el("button", { class: "link-button", type: "button", text: "clear", onclick: () => checkShown(false),
                       disabled: !n }),
    );
    const all = nodes.checkAll;
    const readable = state.files.filter((f) => f.atype);
    const checkedShown = readable.filter((f) => state.selection.includes(f.id)).length;
    all.checked = readable.length > 0 && checkedShown === readable.length;
    all.indeterminate = checkedShown > 0 && checkedShown < readable.length;
}

function orderedSelection(ids) {
    const order = new Map(state.files.map((f, i) => [f.id, i]));
    const kept = ids.filter((id) => order.has(id));
    kept.sort((a, b) => order.get(a) - order.get(b));
    return kept;
}

function setChecked(id, on) {
    const has = state.selection.includes(id);
    if (on === has) { return; }
    const next = on ? [...state.selection, id] : state.selection.filter((x) => x !== id);
    update({ selection: orderedSelection(next) });
}

function checkShown(on) {
    const shown = state.files.filter((f) => f.atype).map((f) => f.id);
    const next = on ? [...new Set([...state.selection, ...shown])] : state.selection.filter((id) => !shown.includes(id));
    update({ selection: orderedSelection(next) });
}

function checkRange(from, to, on) {
    const ids = state.files.map((f) => f.id);
    let a = ids.indexOf(from);
    let b = ids.indexOf(to);
    if (a < 0 || b < 0) { return; }
    if (a > b) { [a, b] = [b, a]; }
    const span = ids.slice(a, b + 1).filter((id) => (fileRow(id) || {}).atype);
    const next = on ? [...new Set([...state.selection, ...span])] : state.selection.filter((id) => !span.includes(id));
    update({ selection: orderedSelection(next) });
}

function params() {
    const [sort, direction] = nodes.sort.value.split(":");
    return { pattern: nodes.search.value || "", sort, reverse: direction === "desc" };
}

/** List the folder (again, with `rescan`); the files shown and checked that vanished are dropped. */
export async function loadFiles({ rescan = false } = {}) {
    const request = ++listRequest;
    nodes.rescan.disabled = true;
    try {
        const result = await get("/api/files", { ...params(), rescan });
        if (request !== listRequest) { return; }
        const ids = new Set(result.files.map((f) => f.id));
        const patch = { files: result.files, total: result.total };
        // a filtered-out file stays checked and shown: only files gone from the folder are dropped
        if (rescan) {
            const listing = await get("/api/files", { limit: 100000 });
            const all = new Set(listing.files.map((f) => f.id));
            patch.selection = state.selection.filter((id) => all.has(id));
            if (state.active && !all.has(state.active)) { patch.active = null; }
        }
        update(patch);
        renderRows();
        if (!ids.size && !state.active) { renderMeta(); }
    } catch (error) {
        nodes.rows.replaceChildren(el("tr", { class: "empty" }, [el("td", { colspan: 4, text: error.message })]));
    } finally {
        if (request === listRequest) { nodes.rescan.disabled = false; }
    }
}

// ── the metadata card ────────────────────────────────────────────────────────────────────────
let metaRequest = 0;
async function renderMeta() {
    const name = state.active;
    const request = ++metaRequest;
    nodes.metaBadges.replaceChildren();
    if (!name) {
        nodes.metaBody.replaceChildren(el("p", { class: "card-empty", text: "Click a file to see its metadata." }));
        return;
    }
    try {
        const summary = await get(`${file(name)}/summary`);
        if (request !== metaRequest) { return; }
        const row = fileRow(name);
        if (row) { nodes.metaBadges.replaceChildren(...badges(row)); }
        nodes.metaBody.replaceChildren(el("table", { class: "meta-table" }, [el("tbody", {},
            summary.rows.map(([label, value]) => el("tr", {}, [el("th", { text: label }), el("td", { text: value })])))]));
    } catch (error) {
        if (request !== metaRequest) { return; }
        nodes.metaBody.replaceChildren(el("p", { class: "card-empty error", text: error.message }));
    }
}

function moveActive(step) {
    const ids = state.files.map((f) => f.id);
    if (!ids.length) { return; }
    let i = ids.indexOf(state.active);
    i = i < 0 ? (step > 0 ? 0 : ids.length - 1) : Math.max(0, Math.min(ids.length - 1, i + step));
    update({ active: ids[i] });
    const row = nodes.rows.querySelector(`tr[data-id="${CSS.escape(ids[i])}"]`);
    if (row) { row.scrollIntoView({ block: "nearest" }); }
}

export function initFiles() {
    nodes.search = document.getElementById("file-search");
    nodes.sort = document.getElementById("file-sort");
    nodes.rescan = document.getElementById("file-rescan");
    nodes.rows = document.getElementById("file-rows");
    nodes.hint = document.getElementById("file-hint");
    nodes.checkAll = document.getElementById("file-check-all");
    nodes.metaBody = document.getElementById("meta-body");
    nodes.metaBadges = document.getElementById("meta-badges");
    nodes.wrap = document.getElementById("file-table-wrap");

    nodes.search.addEventListener("input", debounce(() => loadFiles(), 200));
    nodes.sort.addEventListener("change", () => loadFiles());
    nodes.rescan.addEventListener("click", () => loadFiles({ rescan: true }));
    nodes.checkAll.addEventListener("change", () => checkShown(nodes.checkAll.checked));

    nodes.rows.addEventListener("click", (event) => {
        const tr = event.target.closest("tr[data-id]");
        if (!tr) { return; }
        const id = tr.dataset.id;
        if (event.target.type === "checkbox") {
            if (event.shiftKey && anchor && anchor !== id) { checkRange(anchor, id, event.target.checked); }
            else { setChecked(id, event.target.checked); }
            anchor = id;
            return;
        }
        if (event.shiftKey && anchor && anchor !== id) {
            checkRange(anchor, id, true);
        } else if (event.ctrlKey || event.metaKey) {
            const row = fileRow(id);
            if (row && row.atype) { setChecked(id, !state.selection.includes(id)); }
        } else {
            update({ active: id });
        }
        anchor = id;
    });
    nodes.wrap.addEventListener("keydown", (event) => {
        if (event.target.tagName === "INPUT" && event.target.type !== "checkbox") { return; }
        if (event.key === "ArrowDown") { event.preventDefault(); moveActive(1); }
        else if (event.key === "ArrowUp") { event.preventDefault(); moveActive(-1); }
        else if (event.key === " " && state.active) {
            event.preventDefault();
            const row = fileRow(state.active);
            if (row && row.atype) { setChecked(state.active, !state.selection.includes(state.active)); }
        }
    });

    subscribe((changed) => {
        if (changed.includes("active")) { renderMeta(); }
        if (changed.includes("active") || changed.includes("selection") || changed.includes("files")) { renderRows(); }
    });
    renderMeta();
}
