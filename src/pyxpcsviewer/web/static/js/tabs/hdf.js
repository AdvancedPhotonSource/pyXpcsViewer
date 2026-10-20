// The metadata tab: the instrument, sample, user and analysis settings stored in the file shown,
// as a tree that a filter narrows.
import { get, file } from "../api.js";
import { state } from "../state.js";
import { el, debounce, fmt } from "../widgets.js";
import { makeTab, EMPTY } from "./base.js";

const nodes = {};
let groups = null;
let request = 0;

function valueText(value) {
    if (value === null || value === undefined) { return "–"; }
    if (Array.isArray(value)) {
        const flat = value.flat(Infinity);
        if (flat.length > 12) { return `[${flat.slice(0, 8).map((v) => (typeof v === "number" ? fmt(v) : v)).join(", ")}, … ${flat.length} values]`; }
        return `[${flat.map((v) => (typeof v === "number" ? fmt(v) : v)).join(", ")}]`;
    }
    if (typeof value === "number") { return fmt(value, 6); }
    return String(value);
}

function highlight(text, words) {
    if (!words.length) { return text; }
    const pattern = new RegExp(`(${words.map((w) => w.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")).join("|")})`, "ig");
    const parts = text.split(pattern);
    return parts.map((part) => (part && words.some((w) => w.toLowerCase() === part.toLowerCase()) ? el("mark", { text: part }) : part));
}

/** The tree of one group; returns null when nothing in it matches the filter words. */
function tree(name, value, words, depth) {
    if (value && typeof value === "object" && !Array.isArray(value)) {
        const children = Object.entries(value);
        const nested = children.filter(([, v]) => v && typeof v === "object" && !Array.isArray(v));
        const leaves = children.filter(([, v]) => !(v && typeof v === "object" && !Array.isArray(v)));
        const rows = leaves.map(([k, v]) => {
            const text = valueText(v);
            if (words.length && !words.every((w) => `${k} ${text}`.toLowerCase().includes(w))) { return null; }
            return el("tr", {}, [el("td", { class: "key" }, highlight(k, words)), el("td", { class: "val" }, highlight(text, words))]);
        }).filter(Boolean);
        const subs = nested.map(([k, v]) => tree(k, v, words, depth + 1)).filter(Boolean);
        if (!rows.length && !subs.length) { return null; }
        const details = el("details", { open: words.length > 0 || depth === 0 }, [el("summary", { text: name })]);
        if (rows.length) { details.append(el("table", {}, [el("tbody", {}, rows)])); }
        subs.forEach((s) => details.append(s));
        return details;
    }
    return null;
}

function render() {
    const words = (nodes.filter.value || "").toLowerCase().split(/\s+/).filter(Boolean);
    if (!groups) { nodes.tree.replaceChildren(el("p", { class: "card-empty", text: EMPTY.none })); return; }
    const parts = Object.entries(groups).map(([name, value]) => tree(name, value, words, 0)).filter(Boolean);
    nodes.tree.replaceChildren(...(parts.length ? parts : [el("p", { class: "card-empty", text: "Nothing matches the filter." })]));
}

async function refresh() {
    const name = state.active;
    const id = ++request;
    if (!name) { groups = null; render(); return; }
    nodes.tree.classList.add("busy");
    try {
        const result = await get(`${file(name)}/hdf`);
        if (id !== request) { return; }
        groups = result.groups;
        render();
    } catch (error) {
        if (id !== request) { return; }
        groups = null;
        nodes.tree.replaceChildren(el("p", { class: "card-empty error", text: error.message }));
    } finally {
        if (id === request) { nodes.tree.classList.remove("busy"); }
    }
}

function init() {
    nodes.filter = document.getElementById("hdf-filter");
    nodes.tree = document.getElementById("hdf-tree");
    nodes.filter.addEventListener("input", debounce(render, 120));
    document.getElementById("hdf-expand").addEventListener("click", () => nodes.tree.querySelectorAll("details").forEach((d) => { d.open = true; }));
    document.getElementById("hdf-collapse").addEventListener("click", () => nodes.tree.querySelectorAll("details").forEach((d) => { d.open = false; }));
}

export const tab = makeTab({ id: "hdf", deps: ["active"], init, refresh });
