// Drag the gutters between the columns, and between an analysis' result and its controls, to
// resize them; double-click a gutter to go back to the default size. The sizes are CSS variables
// on the page (--col1, --col3, --result-h), kept in localStorage for the next visit.
const KEY = "xpcsweb-layout";
const root = document.documentElement;
const MIN = { "--col1": 220, "--col3": 360, "--result-h": 160 };
const IMAGE_MIN = 320;      // the image column keeps at least this width
const CONTROLS_MIN = 120;   // the controls under a result keep at least this height

let sizes = {};
try { sizes = JSON.parse(window.localStorage.getItem(KEY)) || {}; } catch (e) { sizes = {}; }
Object.keys(sizes).forEach((name) => root.style.setProperty(name, sizes[name] + "px"));

function store() {
    try { window.localStorage.setItem(KEY, JSON.stringify(sizes)); } catch (e) { /* private window */ }
}
let pending = null;
export function relayout() {   // plots follow their containers
    if (pending) { return; }
    pending = window.setTimeout(() => { pending = null; window.dispatchEvent(new Event("resize")); }, 60);
}
function width(selector) {
    const el = document.querySelector(selector);
    return el ? el.getBoundingClientRect().width : 0;
}

export function installGutters() {
    let drag = null;
    document.addEventListener("mousedown", (event) => {
        const gutter = event.target.closest ? event.target.closest("[data-gutter]") : null;
        if (!gutter || event.button !== 0) { return; }
        const target = gutter.dataset.target === "previous" ? gutter.previousElementSibling
            : document.querySelector(gutter.dataset.target);
        if (!target) { return; }
        event.preventDefault();
        const axis = gutter.dataset.axis === "y" ? "y" : "x";
        const rect = target.getBoundingClientRect();
        let max;
        if (gutter.dataset.gutter === "--col1") {
            max = window.innerWidth - width(".analysis-panel") - IMAGE_MIN;
        } else if (gutter.dataset.gutter === "--col3") {
            max = window.innerWidth - width(".side-panel") - IMAGE_MIN;
        } else {
            max = target.parentElement.getBoundingClientRect().height - CONTROLS_MIN;
        }
        drag = { name: gutter.dataset.gutter, axis, sign: gutter.dataset.sign === "-1" ? -1 : 1,
                 start: axis === "y" ? event.clientY : event.clientX,
                 size: axis === "y" ? rect.height : rect.width, max };
        document.body.classList.add("dragging", axis === "y" ? "dragging-y" : "dragging-x");
    });
    document.addEventListener("mousemove", (event) => {
        if (!drag) { return; }
        const position = drag.axis === "y" ? event.clientY : event.clientX;
        let value = drag.size + drag.sign * (position - drag.start);
        value = Math.round(Math.max(MIN[drag.name] || 100, Math.min(drag.max, value)));
        root.style.setProperty(drag.name, value + "px");
        sizes[drag.name] = value;
        relayout();
    });
    document.addEventListener("mouseup", () => {
        if (!drag) { return; }
        drag = null;
        document.body.classList.remove("dragging", "dragging-x", "dragging-y");
        store();
        relayout();
    });
    document.addEventListener("dblclick", (event) => {
        const gutter = event.target.closest ? event.target.closest("[data-gutter]") : null;
        if (!gutter) { return; }
        root.style.removeProperty(gutter.dataset.gutter);
        delete sizes[gutter.dataset.gutter];
        store();
        relayout();
    });
}
