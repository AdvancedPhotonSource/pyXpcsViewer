# Copyright © UChicago Argonne LLC
# See LICENSE file for details
"""JSON encoding of NumPy data for the browser.

Large arrays travel as base64 typed arrays, ``{"dtype": "f4", "bdata": "...", "shape": [rows, cols]}``,
the layout plotly.js and ``static/js/api.js`` decode; everything else is turned into plain
Python values by :func:`jsonable`.
"""

from __future__ import annotations

import base64
from typing import Any

import numpy as np

# NumPy dtype name -> the short code the browser maps to a typed array
DTYPE_CODES: dict[str, str] = {
    "float32": "f4",
    "float64": "f8",
    "int8": "i1",
    "uint8": "u1",
    "int16": "i2",
    "uint16": "u2",
    "int32": "i4",
    "uint32": "u4",
}


def pack(array: Any, dtype: str | None = None) -> dict[str, Any]:
    """An array as a base64 typed-array spec.

    Args:
        array: Anything ``np.asarray`` accepts.
        dtype: NumPy dtype to send (``"float32"`` and so on). By default 64-bit floats are
            sent as 32-bit (plenty for a plot), 64-bit integers as 32-bit, booleans as bytes
            and other types unchanged.

    Returns:
        ``{"dtype": code, "bdata": base64, "shape": [...]}``.
    """
    arr = np.ascontiguousarray(np.asarray(array))
    if dtype is not None:
        arr = arr.astype(dtype, copy=False)
    elif arr.dtype == np.float64:
        arr = arr.astype(np.float32)
    elif arr.dtype == np.int64:
        arr = arr.astype(np.int32)
    elif arr.dtype == np.uint64:
        arr = arr.astype(np.uint32)
    elif arr.dtype == np.bool_:
        arr = arr.astype(np.uint8)
    elif arr.dtype.name not in DTYPE_CODES:
        arr = arr.astype(np.float32)
    arr = arr.astype(arr.dtype.newbyteorder("<"), copy=False)  # browsers read little-endian
    return {
        "dtype": DTYPE_CODES[arr.dtype.name],
        "bdata": base64.b64encode(arr.tobytes()).decode("ascii"),
        "shape": list(arr.shape),
    }


def jsonable(value: Any) -> Any:
    """``value`` with NumPy scalars and arrays (and bytes) replaced by plain Python values,
    recursively through dicts, lists and tuples. Non-finite floats become ``None``."""
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(v) for v in value]
    if isinstance(value, np.ndarray):
        return jsonable(value.tolist())
    if isinstance(value, (bytes, np.bytes_)):
        return value.decode("utf-8", errors="replace")
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, (np.integer, int)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        number = float(value)
        return number if np.isfinite(number) else None
    if isinstance(value, np.str_):
        return str(value)
    return value
