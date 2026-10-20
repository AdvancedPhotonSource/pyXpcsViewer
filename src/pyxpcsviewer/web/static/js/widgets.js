// Small DOM helpers: forms of named inputs, their persistence, a two-thumb range, messages.

export function el(tag, attrs = {}, children = []) {
    const node = document.createElement(tag);
    Object.entries(attrs).forEach(([k, v]) => {
        if (v === null || v === undefined || v === false) { return; }
        if (k === "class") { node.className = v; }
        else if (k === "text") { node.textContent = v; }
        else if (k === "html") { node.innerHTML = v; }
        else if (k.startsWith("on") && typeof v === "function") { node.addEventListener(k.slice(2), v); }
        else if (k === "dataset") { Object.assign(node.dataset, v); }
        else if (v === true) { node.setAttribute(k, ""); }
        else { node.setAttribute(k, v); }
    });
    (Array.isArray(children) ? children : [children]).forEach((child) => {
        if (child === null || child === undefined) { return; }
        node.append(child instanceof Node ? child : document.createTextNode(String(child)));
    });
    return node;
}

/** A compact number: 4 significant digits, trailing zeros dropped. */
export function fmt(x, digits = 4) {
    if (x === null || x === undefined || Number.isNaN(x)) { return "–"; }
    if (x === 0) { return "0"; }
    const abs = Math.abs(x);
    if (abs >= 1e5 || abs < 1e-3) { return Number(x).toExponential(digits - 1).replace(/\.?0+e/, "e"); }
    return String(parseFloat(Number(x).toPrecision(digits)));
}

/** `{name: value}` of the named inputs in `container`: numbers as numbers (blank → null),
    check boxes as booleans, radios as the checked value, the rest as strings. */
export function readForm(container) {
    const out = {};
    container.querySelectorAll("input[name], select[name], textarea[name]").forEach((input) => {
        const name = input.name;
        if (input.type === "checkbox") { out[name] = input.checked; }
        else if (input.type === "radio") { if (input.checked) { out[name] = input.value; } else if (!(name in out)) { out[name] = null; } }
        else if (input.type === "number" || input.type === "range") {
            out[name] = input.value === "" ? null : Number(input.value);
        } else { out[name] = input.value; }
    });
    return out;
}

export function writeForm(container, values) {
    Object.entries(values || {}).forEach(([name, value]) => {
        container.querySelectorAll(`[name="${CSS.escape(name)}"]`).forEach((input) => {
            if (input.type === "checkbox") { input.checked = Boolean(value); }
            else if (input.type === "radio") { input.checked = input.value === String(value); }
            else if (value === null || value === undefined) { input.value = ""; }
            else { input.value = value; }
        });
    });
}

/** Keep the form's values in localStorage under `key` (restored now, saved on every change). */
export function persistForm(container, key) {
    const storageKey = `xpcsweb:${key}`;
    try {
        const saved = JSON.parse(window.localStorage.getItem(storageKey));
        if (saved) { writeForm(container, saved); }
    } catch (e) { /* nothing saved, or no storage */ }
    const save = () => {
        try { window.localStorage.setItem(storageKey, JSON.stringify(readForm(container))); } catch (e) { /* no storage */ }
    };
    container.addEventListener("change", save);
    container.addEventListener("input", save);
}

/** Call `handler(values, changedInput)` when a named input of the form changes; `input` events
    (every keystroke) only for inputs marked `data-live`. */
export function onChange(container, handler) {
    const fire = (event) => {
        const input = event.target;
        if (!input || !input.name) { return; }
        if (event.type === "input" && !("live" in input.dataset) && input.type !== "range") { return; }
        handler(readForm(container), input);
    };
    container.addEventListener("change", fire);
    container.addEventListener("input", fire);
}

/** A number input clamped to its min/max when a value is entered. */
export function clampNumbers(container) {
    container.addEventListener("change", (event) => {
        const box = event.target;
        if (!box || box.type !== "number" || box.value === "") { return; }
        const value = parseFloat(box.value);
        const low = box.min === "" ? NaN : parseFloat(box.min);
        const high = box.max === "" ? NaN : parseFloat(box.max);
        let clamped = value;
        if (!Number.isNaN(high) && clamped > high) { clamped = high; }
        if (!Number.isNaN(low) && clamped < low) { clamped = low; }
        if (clamped !== value) { box.value = String(clamped); }
    }, true);
}

export function setMessage(node, text, kind = "error") {
    node.textContent = text || "";
    node.classList.toggle("note", kind === "note");
}

export function busy(node, on) { node.classList.toggle("busy", Boolean(on)); }

export function debounce(fn, wait = 150) {
    let timer = null;
    return (...args) => {
        if (timer) { window.clearTimeout(timer); }
        timer = window.setTimeout(() => { timer = null; fn(...args); }, wait);
    };
}

/** The ordered pair [a, b] of two numbers (either may be null), or null when either is missing. */
export function range(a, b) {
    if (a === null || b === null || a === undefined || b === undefined || Number.isNaN(a) || Number.isNaN(b)) { return null; }
    return a <= b ? [a, b] : [b, a];
}
