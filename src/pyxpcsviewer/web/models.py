# Copyright © UChicago Argonne LLC
# See LICENSE file for details
"""The response models of the web API: what every route answers, as the OpenAPI document and
the frontend's generated types describe it.

Large arrays travel as :class:`PackedArray` (base64 typed arrays) on the JSON routes; the
binary routes send them as raw bytes instead (:mod:`beamline_webkit.arrays`). Every model
refuses unknown keys, so a workspace payload that drifts from its model fails in the tests
rather than silently in the browser; a non-finite number is sent as ``null``.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, RootModel


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid", ser_json_inf_nan="null")


class PackedArray(Model):
    """A typed array as base64: ``dtype`` is the code the browser maps to a typed array
    (``f4`` Float32Array, ``u1`` Uint8Array, …), ``bdata`` its little-endian bytes."""

    dtype: Literal["f4", "f8", "i1", "u1", "i2", "u2", "i4", "u4"]
    bdata: str
    shape: list[int]


Range = tuple[float, float]
"""A (low, high) pair; ``null`` for "all"."""


# ── the folder ───────────────────────────────────────────────────────────────────────────────


class Defaults(Model):
    """The Qt viewer's fit bounds, offered to the page as a starting point: ``[lower, upper]``."""

    g2_bounds: dict[str, list[list[float]]] = Field(description="by fit function: single, double")
    tauq_bounds: list[list[float]]


class Info(Model):
    root: str = Field(description="the folder served")
    version: str = Field(description="the xpcs-viewer package version")
    schema_version: str = Field(description="the API schema version; a frontend refuses a different major")
    label_style: str | None
    colormaps: list[str]
    defaults: Defaults


class Colormaps(RootModel[dict[str, list[tuple[float, str]]]]):
    """Plotly color scales by name: ``[[position, "rgb(r,g,b)"], ...]``."""


class FileRow(Model):
    id: str = Field(description="the file name, the key of every per-file route")
    label: str = Field(description="the short label")
    modified: str = Field(description="the modification time, YYYY-MM-DD HH:MM")
    mtime: float
    size: int
    atype: list[str] | None = Field(description="Multitau, Twotime or both; null for a file that is not a result")


class Files(Model):
    files: list[FileRow]
    total: int = Field(description="files matching the pattern before the limit")
    version: int = Field(description="bumped at every rescan of the folder")


# ── one file ─────────────────────────────────────────────────────────────────────────────────


class Summary(Model):
    file: str
    label: str
    rows: list[tuple[str, str]] = Field(description="[label, value] rows of the metadata card")


class HdfInfo(Model):
    file: str
    groups: dict[str, Any] = Field(description="the instrument, sample, user and analysis groups, nested")


class Image(Model):
    file: str
    label: str
    kind: Literal["saxs", "dqmap", "sqmap", "mask"]
    scale: Literal["log", "linear"]
    factor: int = Field(description="source pixels per sent pixel, per axis")
    shape_full: tuple[int, int] = Field(description="rows, columns of the detector")
    shape: tuple[int, int] = Field(description="rows, columns of the array sent")
    x0: float = Field(description="center of the first sent column, in source pixels")
    y0: float
    z: PackedArray
    levels: PackedArray = Field(description="the percentile table of z: 201 values")
    zmin: float
    zmax: float
    beam_center: tuple[float, float] = Field(description="x, y in detector pixels")
    extent_q: list[float] = Field(description="the q range of the detector edges")
    pixel_size: float
    det_dist: float
    energy: float


class Pixel(Model):
    """What is at a detector pixel; only ``x``, ``y`` and ``on_detector`` off the detector."""

    on_detector: bool
    x: int
    y: int
    intensity: float | None = None
    q: float | None = None
    phi: float | None = None
    qx: float | None = None
    qy: float | None = None
    masked: bool | None = None
    dq_bin: int | None = None
    dq_label: str | None = None
    sq_bin: int | None = None


class Stability(Model):
    file: str
    label: str
    q: PackedArray
    I: PackedArray  # noqa: E741  (one row per time segment)
    labels: list[str]
    xlabel: str
    ylabel: str


class G2Stability(Model):
    file: str
    label: str
    q: list[float]
    labels: list[str]
    segments: list[str]
    t: PackedArray
    g2: PackedArray = Field(description="shape (segments, delays, q-bins)")
    err: PackedArray


class TwotimeBin(Model):
    index: int = Field(description="the C2 block index: the selection of the c2 route")
    qbin: int
    label: str


class TwotimeBins(Model):
    file: str
    label: str
    bins: list[TwotimeBin]
    time_step: float


class TwotimeBinAt(Model):
    x: int
    y: int
    qbin: int
    selection: int | None = Field(description="the C2 block index at the pixel, null off every bin")


class TwotimeC2(Model):
    file: str
    label: str
    selection: int
    qbin: int
    bin_label: str
    c2: PackedArray
    shape: tuple[int, int]
    delta_t: float
    acquire_period: float
    levels: PackedArray
    zmin: float
    zmax: float
    g2_full: PackedArray
    g2_partial: PackedArray = Field(description="shape (segments, delays)")


# ── several files ────────────────────────────────────────────────────────────────────────────


class Skipped(Model):
    file: str
    reason: str


class G2Fit(Model):
    func: Literal["single", "double"]
    param_names: list[str]
    fit_x: PackedArray
    fit_y: PackedArray = Field(description="shape (q-bins, points); NaN rows for bins without a fit")
    success: list[bool]
    params: list[list[float | None] | None]
    errors: list[list[float | None] | None]
    bounds: list[list[float]] | None
    fit_flag: list[bool]
    q_range: Range | None
    t_range: Range | None


class G2File(Model):
    file: str
    label: str
    q: list[float]
    labels: list[str]
    t: PackedArray
    g2: PackedArray = Field(description="shape (delays, q-bins)")
    err: PackedArray
    fit: G2Fit | None


class G2(Model):
    files: list[G2File]
    skipped: list[Skipped]


class ParamsVsQ(Model):
    q: list[float]
    names: list[str]
    titles: list[str]
    values: list[list[float | None]] = Field(description="one row per parameter")
    errors: list[list[float | None]]
    bounds: list[list[float]] | None


class TauqFit(Model):
    x: list[float]
    y: list[float]
    a: float | None
    a_err: float | None
    b: float | None
    b_err: float | None


class TauqFile(Model):
    file: str
    label: str
    q: list[float]
    tau: list[float]
    tau_err: list[float]
    params_vs_q: ParamsVsQ
    fit: TauqFit | None


class Tauq(Model):
    files: list[TauqFile]
    skipped: list[Skipped]


class Saxs1dFile(Model):
    file: str
    label: str
    labels: list[str]
    q: PackedArray
    I: PackedArray  # noqa: E741  (one row per φ slice)
    xlabel: str
    ylabel: str


class Saxs1d(Model):
    files: list[Saxs1dFile]
    skipped: list[Skipped]


class InttFile(Model):
    file: str
    label: str
    frame_time: float
    frames: int
    points: int
    x: PackedArray
    y: PackedArray
    fft_x: PackedArray
    fft_y: PackedArray


class Intt(Model):
    files: list[InttFile]
    skipped: list[Skipped]
