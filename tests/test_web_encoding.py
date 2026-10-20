# Copyright © UChicago Argonne LLC
# See LICENSE file for details
"""web.encoding: packed arrays and JSON-ready values."""

import base64
import json

import numpy as np

from pyxpcsviewer.web.encoding import jsonable, pack


def _decode(spec):
    dtype = {"f4": "<f4", "f8": "<f8", "i4": "<i4", "u1": "u1", "u2": "<u2"}[spec["dtype"]]
    return np.frombuffer(base64.b64decode(spec["bdata"]), dtype=dtype).reshape(spec["shape"])


def test_pack_round_trips_and_shrinks_64_bit_floats():
    arr = np.arange(12, dtype=np.float64).reshape(3, 4) / 7
    spec = pack(arr)
    assert spec["dtype"] == "f4" and spec["shape"] == [3, 4]
    assert np.allclose(_decode(spec), arr.astype(np.float32))
    assert json.dumps(spec)


def test_pack_keeps_requested_dtype_and_handles_bool_and_int64():
    assert pack(np.arange(3), "int32")["dtype"] == "i4"
    assert pack(np.array([True, False]))["dtype"] == "u1"
    assert pack(np.arange(3, dtype=np.int64))["dtype"] == "i4"
    spec = pack(np.array([1.5, 2.5]), "float64")
    assert spec["dtype"] == "f8" and _decode(spec).tolist() == [1.5, 2.5]


def test_jsonable_converts_numpy_and_non_finite():
    value = {
        "a": np.float32(1.5),
        "b": np.array([1, 2]),
        "c": (np.int64(3), b"x"),
        "d": np.nan,
        "e": np.inf,
        "f": np.bool_(True),
    }
    out = jsonable(value)
    assert out == {"a": 1.5, "b": [1, 2], "c": [3, "x"], "d": None, "e": None, "f": True}
    assert json.dumps(out)
