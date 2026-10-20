// The JSON API of pyxpcsviewer.web.app, and the decoding of the packed arrays it sends.

export class ApiError extends Error {
    constructor(message, status) { super(message); this.status = status; }
}

async function handle(response) {
    if (response.ok) { return response.json(); }
    let detail = response.statusText;
    try {
        const body = await response.json();
        if (body && body.detail) {
            detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
        }
    } catch (e) { /* not JSON */ }
    throw new ApiError(detail, response.status);
}

export async function get(path, params) {
    const url = new URL(path, window.location.href);
    if (params) {
        Object.entries(params).forEach(([k, v]) => {
            if (v !== undefined && v !== null) { url.searchParams.set(k, v); }
        });
    }
    return handle(await fetch(url, { headers: { Accept: "application/json" } }));
}

export async function post(path, body) {
    return handle(await fetch(path, {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify(body || {}),
    }));
}

export const file = (name) => `/api/files/${encodeURIComponent(name)}`;

// ── packed arrays: {dtype, bdata, shape} → a typed array (1-D) or rows of one (2-D+) ──────────
const TYPED = { f4: Float32Array, f8: Float64Array, i1: Int8Array, u1: Uint8Array, i2: Int16Array,
                u2: Uint16Array, i4: Int32Array, u4: Uint32Array };

function bytesOf(b64) {
    const binary = atob(b64);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i += 1) { bytes[i] = binary.charCodeAt(i); }
    return bytes;
}

/** A packed array as a flat typed array. */
export function unpackFlat(spec) {
    if (spec === null || spec === undefined) { return null; }
    if (ArrayBuffer.isView(spec) || Array.isArray(spec)) { return spec; }
    const Type = TYPED[spec.dtype];
    if (!Type) { throw new Error(`unknown dtype ${spec.dtype}`); }
    const bytes = bytesOf(spec.bdata);
    return new Type(bytes.buffer, bytes.byteOffset, bytes.byteLength / Type.BYTES_PER_ELEMENT);
}

/** A packed array as a typed array (1-D) or an array of typed-array rows (2-D; 3-D nests once more). */
export function unpack(spec) {
    if (spec === null || spec === undefined) { return null; }
    if (ArrayBuffer.isView(spec) || Array.isArray(spec)) { return spec; }
    const flat = unpackFlat(spec);
    const shape = spec.shape || [flat.length];
    if (shape.length <= 1) { return flat; }
    const split = (array, dims) => {
        const [n, ...rest] = dims;
        const size = rest.reduce((a, b) => a * b, 1);
        const out = new Array(n);
        for (let i = 0; i < n; i += 1) {
            const piece = array.subarray(i * size, (i + 1) * size);
            out[i] = rest.length > 1 ? split(piece, rest) : piece;
        }
        return out;
    };
    return split(flat, shape);
}

/** Column `j` of a 2-D packed array as a plain array. */
export function column(rows, j) {
    const out = new Array(rows.length);
    for (let i = 0; i < rows.length; i += 1) { out[i] = rows[i][j]; }
    return out;
}
