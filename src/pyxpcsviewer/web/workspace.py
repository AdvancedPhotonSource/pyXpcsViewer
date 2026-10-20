# Copyright © UChicago Argonne LLC
# See LICENSE file for details
"""One result folder as the web viewer sees it: the files in it, the open
:class:`~pyxpcsviewer.core.xpcs_file.XpcsFile` objects, and every analysis the page shows,
each returned as a JSON-ready dict (large arrays packed by :func:`~pyxpcsviewer.web.encoding.pack`).

No web framework is imported here: :mod:`pyxpcsviewer.web.app` wraps these methods as routes,
and a test can call them directly.
"""

from __future__ import annotations

import datetime as _dt
import logging
import os
import threading
from collections import OrderedDict
from typing import Any

import numpy as np

from pyxpcsviewer.core.file_io.discover import ResultFile, list_result_files
from pyxpcsviewer.core.file_io.hdf_reader import get_analysis_type, get_shape
from pyxpcsviewer.core.file_io.qmap_utils import QMapManager
from pyxpcsviewer.core.image_utils import (
    block_mean,
    downsample_factor,
    log10_clamped,
    percentile_table,
    subsample,
)
from pyxpcsviewer.core.intt_utils import smooth_intensity
from pyxpcsviewer.core.xpcs_file import XpcsFile, create_id

from .encoding import jsonable, pack

logger = logging.getLogger(__name__)

IMAGE_KINDS = ("saxs", "dqmap", "sqmap", "mask")
NORM_METHODS: dict[str, str | None] = {"none": None, "q2": "q2", "q4": "q4", "I0": "I0"}
FIT_PARAMS_SINGLE = ("a", "b", "c", "d")
FIT_PARAMS_DOUBLE = ("a", "b", "c", "d", "b2", "c2", "f")
PARAM_NAMES = {
    "a": "contrast",
    "b": "τ (s)",
    "c": "stretch",
    "d": "baseline",
    "b2": "τ₂ (s)",
    "c2": "stretch₂",
    "f": "fraction",
}
# the Qt viewer's defaults, offered to the page as a starting point
DEFAULT_G2_BOUNDS = {
    "single": ([0.04, 1e-5, 0.5, 0.95], [0.8, 100.0, 2.0, 1.05]),
    "double": ([0.04, 1e-5, 0.5, 0.95, 1e-5, 0.5, 0.0], [0.8, 100.0, 2.0, 1.05, 1.0, 2.0, 1.0]),
}
DEFAULT_TAUQ_BOUNDS = ([1e-12, -2.5], [1e-3, -0.5])


class WorkspaceError(ValueError):
    """A request the workspace cannot serve (unknown file, no such data in it, bad parameter)."""


def _split_words(pattern: str) -> list[str]:
    return [w.lower() for w in (pattern or "").split() if w]


def _pair(values: list[float] | None) -> tuple[float, float] | None:
    """A (low, high) range from the page, None for "all"."""
    if not values or len(values) != 2 or values[0] is None or values[1] is None:
        return None
    lo, hi = float(values[0]), float(values[1])
    return (lo, hi) if lo <= hi else (hi, lo)


class Workspace:
    """The result files under ``root`` and the analyses the page shows for them.

    Args:
        root: The folder to browse.
        label_style: Underscore-separated indices for the short file labels (as the CLI's
            ``--label-style``).
        cache_size: Open files kept in memory (least recently used dropped first).
    """

    def __init__(self, root: str, label_style: str | None = None, cache_size: int = 8):
        self.root = os.path.abspath(root)
        if not os.path.isdir(self.root):
            raise NotADirectoryError(self.root)
        self.label_style = label_style
        self.cache_size = max(1, int(cache_size))
        self.listing_version = 0
        self._lock = threading.RLock()
        self._qmaps = QMapManager()
        self._files: list[ResultFile] | None = None
        self._types: dict[tuple[str, float, int], list[str] | None] = {}
        self._open: OrderedDict[str, tuple[XpcsFile, float]] = OrderedDict()
        self._images: OrderedDict[tuple[Any, ...], dict[str, Any]] = OrderedDict()

    # ── files ────────────────────────────────────────────────────────────────────────────────

    def scan(self) -> list[ResultFile]:
        """Read the folder again."""
        with self._lock:
            self._files = list_result_files(self.root)
            self.listing_version += 1
            return list(self._files)

    def _listing(self, rescan: bool = False) -> list[ResultFile]:
        with self._lock:
            if self._files is None or rescan:
                self.scan()
            assert self._files is not None
            return list(self._files)

    def _analysis_type(self, f: ResultFile) -> list[str] | None:
        """``["Multitau", "Twotime"]`` (either, or both) for a result file, None when the file
        is not one; cached by name, modification time and size."""
        key = (f.name, f.mtime, f.size)
        with self._lock:
            if key in self._types:
                return self._types[key]
        try:
            atype: list[str] | None = sorted(get_analysis_type(f.path))
        except Exception:
            atype = None
        with self._lock:
            self._types[key] = atype
        return atype

    def files(
        self,
        pattern: str = "",
        sort: str = "name",
        reverse: bool = False,
        rescan: bool = False,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        """The folder's result files matching ``pattern`` (every space-separated word must occur
        in the name, case-insensitively), sorted by ``"name"`` or ``"time"``."""
        words = _split_words(pattern)
        files = [f for f in self._listing(rescan) if all(w in f.name.lower() for w in words)]
        key = (lambda f: (f.mtime, f.name)) if sort == "time" else (lambda f: f.name)
        files.sort(key=key, reverse=reverse)
        if limit:
            files = files[: int(limit)]
        rows = []
        for f in files:
            rows.append(
                {
                    "id": f.name,
                    "label": self.label(f.name),
                    "modified": _dt.datetime.fromtimestamp(f.mtime).strftime("%Y-%m-%d %H:%M"),
                    "mtime": f.mtime,
                    "size": f.size,
                    "atype": self._analysis_type(f),
                }
            )
        return rows

    def count_files(self, pattern: str = "") -> int:
        words = _split_words(pattern)
        return sum(1 for f in self._listing() if all(w in f.name.lower() for w in words))

    def label(self, name: str) -> str:
        return str(create_id(name, label_style=self.label_style))

    def path_of(self, name: str) -> str:
        """The full path of a file of the folder; a name that is not a plain file name in it
        (a path, a missing file) is refused."""
        if not name or os.path.basename(name) != name:
            raise WorkspaceError(f"not a file of the folder: {name!r}")
        path = os.path.join(self.root, name)
        if not os.path.isfile(path):
            raise WorkspaceError(f"no such file: {name}")
        return path

    def open(self, name: str) -> XpcsFile:
        """The :class:`XpcsFile` of ``name``, opened once and kept (``cache_size`` of them)."""
        path = self.path_of(name)
        mtime = os.path.getmtime(path)
        with self._lock:
            entry = self._open.get(name)
            if entry is not None and entry[1] == mtime:
                self._open.move_to_end(name)
                return entry[0]
        try:
            xf = XpcsFile(path, label_style=self.label_style, qmap_manager=self._qmaps)
        except Exception as exc:
            raise WorkspaceError(f"cannot open {name}: {exc}") from exc
        with self._lock:
            self._open[name] = (xf, mtime)
            self._open.move_to_end(name)
            while len(self._open) > self.cache_size:
                dropped, _ = self._open.popitem(last=False)
                self._images = OrderedDict((k, v) for k, v in self._images.items() if k[0] != dropped)
        return xf

    def _multitau(self, name: str) -> XpcsFile:
        xf = self.open(name)
        if "Multitau" not in xf.atype:
            raise WorkspaceError(f"{self.label(name)} has no multi-tau (g2) analysis")
        return xf

    def _twotime(self, name: str) -> XpcsFile:
        xf = self.open(name)
        if "Twotime" not in xf.atype:
            raise WorkspaceError(f"{self.label(name)} has no two-time analysis")
        return xf

    # ── the file shown: summary and metadata ─────────────────────────────────────────────────

    def summary(self, name: str) -> list[list[str]]:
        """``[label, value]`` rows of the metadata card."""
        xf = self.open(name)
        rows: list[list[str]] = [
            ["File", name],
            ["Analysis", ", ".join(xf.atype)],
        ]
        if xf.start_time:
            rows.append(["Start", str(xf.start_time)])
        shape = get_shape(xf.fname, "saxs_2d")
        if shape:
            dims = shape[-2:]
            rows.append(["Detector", f"{dims[0]} × {dims[1]} px"])  # noqa: RUF001
        rows += [
            ["Beam center", f"x {xf.bcx:.1f}, y {xf.bcy:.1f} px"],
            ["Distance", f"{xf.det_dist:.4g} m"],
            ["Pixel", f"{xf.pixel_size * 1e6:.3g} µm"],
            ["Energy", f"{xf.X_energy:.5g} keV"],
            ["Frames", f"{xf.Int_t.shape[1]}"],
        ]
        if xf.t1 is not None:
            rows.append(["Count time", f"{xf.t1:.6g} s"])
        if "Multitau" in xf.atype and xf.tau is not None and xf.t_el is not None:
            rows.append(["g2 delays", f"{xf.tau.size} ({xf.t_el[0]:.4g} … {xf.t_el[-1]:.4g} s)"])
            rows.append(["Delay unit", f"{xf.g2_t0:.6g} s"])
        else:
            rows.append(["Frame time", f"{xf.t0:.6g} s"])
        times = " × "  # noqa: RUF001
        rows.append(
            ["Dynamic bins", times.join(str(int(n)) for n in xf.dynamic_num_pts) + f" ({', '.join(xf.map_names)})"]
        )
        if xf.static_num_pts is not None:
            rows.append(["Static bins", times.join(str(int(n)) for n in xf.static_num_pts)])
        if "Twotime" in xf.atype and xf.c2_processed_bins is not None:
            rows.append(["Two-time bins", f"{xf.c2_processed_bins.size}"])
            rows.append(["C2 time step", f"{xf.c2_t0:.6g} s"])
        return rows

    def hdf_info(self, name: str) -> dict[str, Any]:
        """The instrument, sample, user and analysis-config groups of the file as nested dicts."""
        info: dict[str, Any] = jsonable(self.open(name).get_hdf_info())
        return info

    # ── the detector image ───────────────────────────────────────────────────────────────────

    def image(self, name: str, kind: str = "saxs", scale: str = "log", max_size: int = 1024) -> dict[str, Any]:
        """A detector-sized map, downsampled so that no side exceeds ``max_size`` pixels.

        Args:
            name: The file.
            kind: ``"saxs"`` (the time-averaged intensity), ``"dqmap"`` / ``"sqmap"`` (the dynamic /
                static q-bin index per pixel, 0 outside every bin) or ``"mask"``.
            scale: For the intensity, ``"log"`` (log10 of the intensity) or ``"linear"``.
            max_size: Longest side of the image sent, in pixels (0: full resolution).

        Returns:
            The map ``z`` (packed) with its sampling (``factor``, the source pixels per sent pixel;
            ``x0``/``y0`` the center of the first sent pixel in source pixel units), the percentile
            table ``levels`` (201 values, for the contrast slider), the beam center and the q extent.
        """
        if kind not in IMAGE_KINDS:
            raise WorkspaceError(f"kind must be one of {IMAGE_KINDS}")
        if scale not in ("log", "linear"):
            raise WorkspaceError("scale must be log or linear")
        xf = self.open(name)
        source = xf.saxs_2d if kind == "saxs" else getattr(xf, kind)
        factor = downsample_factor(source.shape, max_size)
        key = (name, os.path.getmtime(xf.fname), kind, scale, factor)
        with self._lock:
            cached = self._images.get(key)
            if cached is not None:
                self._images.move_to_end(key)
                return cached
        if kind == "saxs":
            img = block_mean(xf.saxs_2d, factor)
            z = log10_clamped(img) if scale == "log" else img.astype(np.float32)
            levels = percentile_table(z)
            zmin, zmax = float(levels[2]), float(levels[-2])  # 1 % and 99.5 %
        elif kind == "mask":
            z = subsample(xf.mask, factor).astype(np.uint8)
            levels = np.array([0.0, 1.0], dtype=np.float32)
            zmin, zmax = 0.0, 1.0
        else:
            labels = subsample(source, factor).astype(np.float32)
            labels[labels <= 0] = np.nan
            z = labels
            top = float(np.nanmax(z)) if np.isfinite(z).any() else 1.0
            levels = np.array([1.0, top], dtype=np.float32)
            zmin, zmax = 1.0, top
        result = {
            "file": name,
            "label": xf.label,
            "kind": kind,
            "scale": scale if kind == "saxs" else "linear",
            "factor": factor,
            "shape_full": [int(source.shape[0]), int(source.shape[1])],
            "shape": [int(z.shape[0]), int(z.shape[1])],
            "x0": (factor - 1) / 2,
            "y0": (factor - 1) / 2,
            "z": pack(z),
            "levels": pack(levels),
            "zmin": zmin,
            "zmax": zmax,
            "beam_center": [float(xf.bcx), float(xf.bcy)],
            "extent_q": [float(v) for v in xf.get_detector_extent()],
            "pixel_size": float(xf.pixel_size),
            "det_dist": float(xf.det_dist),
            "energy": float(xf.X_energy),
        }
        with self._lock:
            self._images[key] = result
            while len(self._images) > 6:
                self._images.popitem(last=False)
        return result

    def pixel(self, name: str, x: float, y: float) -> dict[str, Any]:
        """What is at detector pixel (column ``x``, row ``y``): intensity, q, φ, the q-bins."""
        xf = self.open(name)
        col, row = round(float(x)), round(float(y))
        shape = xf.saxs_2d.shape
        if not (0 <= col < shape[1] and 0 <= row < shape[0]):
            return {"on_detector": False, "x": col, "y": row}
        qmap = xf.qmap.qmap
        dq = int(xf.dqmap[row, col])
        sq = int(xf.sqmap[row, col])
        info: dict[str, Any] = jsonable(
            {
                "on_detector": True,
                "x": col,
                "y": row,
                "intensity": float(xf.saxs_2d[row, col]),
                "q": float(qmap["q"][row, col]),
                "phi": float(qmap["phi"][row, col]),
                "qx": float(qmap["qx"][row, col]),
                "qy": float(qmap["qy"][row, col]),
                "masked": not bool(xf.mask[row, col]),
                "dq_bin": dq,
                "dq_label": xf.get_qbin_label(dq) if dq > 0 else None,
                "sq_bin": sq,
            }
        )
        return info

    # ── g2 ───────────────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _fit_payload(xf: XpcsFile, q_values: np.ndarray) -> dict[str, Any] | None:
        """The stored g2 fit of ``xf`` matched to the plotted q values (None without a fit)."""
        summary: dict[str, Any] | None = xf.fit_summary
        if summary is None:
            return None
        fit_q = np.asarray(summary["q_val"])
        index = []
        for q in q_values:
            hits = np.flatnonzero(np.isclose(fit_q, q, rtol=0, atol=1e-12))
            index.append(int(hits[0]) if hits.size else -1)
        lines = summary["fit_line"]
        fit_x = np.asarray(lines[0]["fit_x"]) if lines else np.zeros(0)
        fit_y = np.full((len(index), fit_x.size), np.nan, dtype=np.float32)
        success = []
        for n, i in enumerate(index):
            ok = i >= 0 and bool(lines[i].get("success", False))
            success.append(ok)
            if ok:
                fit_y[n] = lines[i]["fit_y"]
        val = np.asarray(summary["fit_val"])  # (nq, 2, nparams)
        params = [val[i, 0].tolist() if i >= 0 else None for i in index]
        errors = [val[i, 1].tolist() if i >= 0 else None for i in index]
        names = FIT_PARAMS_SINGLE if summary["fit_func"] == "single" else FIT_PARAMS_DOUBLE
        payload: dict[str, Any] = jsonable(
            {
                "func": summary["fit_func"],
                "param_names": list(names),
                "fit_x": pack(fit_x),
                "fit_y": pack(fit_y),
                "success": success,
                "params": params,
                "errors": errors,
                "bounds": summary.get("bounds"),
                "q_range": summary.get("q_range"),
                "t_range": summary.get("t_range"),
            }
        )
        return payload

    def g2(
        self,
        names: list[str],
        q_range: list[float] | None = None,
        t_range: list[float] | None = None,
        with_fit: bool = True,
    ) -> dict[str, Any]:
        """The multi-tau g2 of the files, with their stored fits when ``with_fit``."""
        qr = _pair(q_range)
        tr = _pair(t_range)
        files, skipped = [], []
        for name in names:
            try:
                xf = self._multitau(name)
            except WorkspaceError as exc:
                skipped.append({"file": name, "reason": str(exc)})
                continue
            q, t_el, g2, g2_err, labels = xf.get_g2_data(qrange=qr, trange=tr)
            files.append(
                {
                    "file": name,
                    "label": xf.label,
                    "q": [float(v) for v in q],
                    "labels": list(labels),
                    "t": pack(t_el),
                    "g2": pack(g2),
                    "err": pack(g2_err),
                    "fit": self._fit_payload(xf, q) if with_fit else None,
                }
            )
        return {"files": files, "skipped": skipped}

    def fit_g2(
        self,
        names: list[str],
        q_range: list[float] | None,
        t_range: list[float] | None,
        fit_func: str = "single",
        bounds: list[list[float]] | None = None,
        fit_flag: list[bool] | None = None,
    ) -> dict[str, Any]:
        """Fit every q-bin's g2 of the files (stored on each file for the τ(q) tab), then the
        same payload as :meth:`g2`."""
        if fit_func not in ("single", "double"):
            raise WorkspaceError("fit_func must be single or double")
        if bounds is None:
            bounds = [list(b) for b in DEFAULT_G2_BOUNDS[fit_func]]
        count = 4 if fit_func == "single" else 7
        if len(bounds) != 2 or len(bounds[0]) != count or len(bounds[1]) != count:
            raise WorkspaceError(f"bounds must be two lists of {count} values")
        lower = [float(v) for v in bounds[0]]
        upper = [float(v) for v in bounds[1]]
        for lo, hi in zip(lower, upper, strict=True):
            if lo > hi:
                raise WorkspaceError("every lower bound must not exceed its upper bound")
        flags = [bool(f) for f in (fit_flag or [True] * count)]
        if len(flags) != count:
            raise WorkspaceError(f"fit_flag must have {count} entries")
        qr = _pair(q_range)
        tr = _pair(t_range)
        for name in names:
            try:
                xf = self._multitau(name)
            except WorkspaceError:
                continue
            try:
                xf.fit_g2(q_range=qr, t_range=tr, bounds=[lower, upper], fit_flag=flags, fit_func=fit_func)
            except Exception as exc:
                raise WorkspaceError(f"fitting {xf.label} failed: {exc}") from exc
        return self.g2(names, q_range, t_range, with_fit=True)

    def tauq(
        self,
        names: list[str],
        q_range: list[float] | None = None,
        bounds: list[list[float]] | None = None,
        fit_flag: list[bool] | None = None,
        fit: bool = True,
    ) -> dict[str, Any]:
        """τ(q) of the fitted files: the fitted relaxation times, a power-law fit through them
        (when ``fit``) and every fit parameter against q."""
        if bounds is None:
            bounds = [list(b) for b in DEFAULT_TAUQ_BOUNDS]
        if len(bounds) != 2 or len(bounds[0]) != 2 or len(bounds[1]) != 2:
            raise WorkspaceError("bounds must be two lists of 2 values (a, b)")
        flags = [bool(f) for f in (fit_flag or [True, True])]
        files: list[dict[str, Any]] = []
        skipped: list[dict[str, str]] = []
        for name in names:
            try:
                xf = self._multitau(name)
            except WorkspaceError as exc:
                skipped.append({"file": name, "reason": str(exc)})
                continue
            summary: dict[str, Any] | None = xf.fit_summary
            if summary is None:
                skipped.append({"file": name, "reason": f"{xf.label}: fit g2 first"})
                continue
            q_all = np.asarray(summary["q_val"], dtype=float)
            qr = [float(q_all.min()), float(q_all.max())] if not q_range else [float(v) for v in q_range]
            val = np.asarray(summary["fit_val"])
            if fit and any(flags):
                try:
                    xf.fit_tauq(
                        q_range=(qr[0], qr[1]),
                        bounds=(np.asarray(bounds[0], float), np.asarray(bounds[1], float)),
                        fit_flag=flags,
                    )
                except Exception as exc:
                    logger.warning("tau(q) fit failed for %s: %s", name, exc)
                    summary["tauq_success"] = False
            tau, tau_err = val[:, 0, 1], val[:, 1, 1]
            valid = (tau_err > 0) & (q_all >= qr[0]) & (q_all <= qr[1])
            entry: dict[str, Any] = {
                "file": name,
                "label": xf.label,
                "q": q_all[valid].tolist(),
                "tau": tau[valid].tolist(),
                "tau_err": tau_err[valid].tolist(),
                "params_vs_q": {
                    "q": q_all.tolist(),
                    "names": list(FIT_PARAMS_SINGLE if summary["fit_func"] == "single" else FIT_PARAMS_DOUBLE),
                    "titles": [
                        PARAM_NAMES[n]
                        for n in (FIT_PARAMS_SINGLE if summary["fit_func"] == "single" else FIT_PARAMS_DOUBLE)
                    ],
                    "values": val[:, 0, :].T.tolist(),
                    "errors": val[:, 1, :].T.tolist(),
                    "bounds": summary.get("bounds"),
                },
                "fit": None,
            }
            if summary.get("tauq_success", False):
                line = summary["tauq_fit_line"]
                v = summary["tauq_fit_val"]
                entry["fit"] = {
                    "x": np.asarray(line["fit_x"]).tolist(),
                    "y": np.asarray(line["fit_y"]).tolist(),
                    "a": float(v[0, 0]),
                    "a_err": float(v[1, 0]),
                    "b": float(v[0, 1]),
                    "b_err": float(v[1, 1]),
                }
            files.append(entry)
        result: dict[str, Any] = jsonable({"files": files, "skipped": skipped})
        return result

    # ── SAXS 1D and stability ────────────────────────────────────────────────────────────────

    def saxs1d(
        self,
        names: list[str],
        q_range: list[float] | None = None,
        norm: str = "none",
        sampling: int = 1,
        all_phi: bool = False,
        background: str | None = None,
        bkg_weight: float = 1.0,
        absolute: bool = False,
    ) -> dict[str, Any]:
        """The azimuthally averaged I(q) of the files (every φ slice with ``all_phi``)."""
        if norm not in NORM_METHODS:
            raise WorkspaceError(f"norm must be one of {list(NORM_METHODS)}")
        bkg = self.open(background) if background else None
        qr = _pair(q_range)
        files, skipped = [], []
        for name in names:
            try:
                xf = self.open(name)
            except WorkspaceError as exc:
                skipped.append({"file": name, "reason": str(exc)})
                continue
            q, Iq, xlabel, ylabel = xf.get_saxs1d_data(
                bkg_xf=bkg,
                bkg_weight=float(bkg_weight),
                qrange=qr,
                sampling=max(1, int(sampling)),
                norm_method=NORM_METHODS[norm],
                use_absolute_crosssection=bool(absolute),
            )
            lines = Iq if all_phi else Iq[:1]
            files.append(
                {
                    "file": name,
                    "label": xf.label,
                    "labels": list(xf.saxs_1d["labels"][: lines.shape[0]]),
                    "q": pack(q),
                    "I": pack(np.asarray(lines)),
                    "xlabel": xlabel,
                    "ylabel": ylabel
                    if norm != "none"
                    else ("Intensity (1/cm)" if absolute else "Intensity (photon/pixel/frame)"),
                }
            )
        return {"files": files, "skipped": skipped}

    def stability(self, name: str, norm: str = "none") -> dict[str, Any]:
        """The I(q) of each time segment of a file (its SAXS stability)."""
        if norm not in NORM_METHODS:
            raise WorkspaceError(f"norm must be one of {list(NORM_METHODS)}")
        xf = self.open(name)
        q, Iqp, xlabel, ylabel = xf.get_saxs1d_data(target="saxs1d_partial", norm_method=NORM_METHODS[norm])
        return {
            "file": name,
            "label": xf.label,
            "q": pack(q),
            "I": pack(np.asarray(Iqp)),
            "labels": [f"segment {n + 1}" for n in range(Iqp.shape[0])],
            "xlabel": xlabel,
            "ylabel": ylabel,
        }

    def g2_stability(
        self, name: str, q_range: list[float] | None = None, t_range: list[float] | None = None
    ) -> dict[str, Any]:
        """The partial (per time segment) g2 of a multi-tau file, when the file stores them."""
        xf = self._multitau(name)
        if xf.g2_partial is None or xf.g2_partial_err is None:
            raise WorkspaceError(f"{xf.label} stores no partial g2")
        qr = _pair(q_range)
        tr = _pair(t_range)
        q, t_el, g2, g2_err, qbin_labels, labels = xf.get_g2_stability_data(qrange=qr, trange=tr)
        payload: dict[str, Any] = jsonable(
            {
                "file": name,
                "label": xf.label,
                "q": [float(v) for v in q],
                "labels": list(qbin_labels),
                "segments": [str(v) for v in np.asarray(labels).tolist()],
                "t": pack(t_el),
                "g2": pack(np.asarray(g2)),
                "err": pack(np.asarray(g2_err)),
            }
        )
        return payload

    # ── intensity vs time ────────────────────────────────────────────────────────────────────

    def intt(self, names: list[str], window: int = 1, sampling: int = 1) -> dict[str, Any]:
        """The intensity per frame of the files (smoothed, subsampled) and its spectrum."""
        files, skipped = [], []
        for name in names:
            try:
                xf = self.open(name)
            except WorkspaceError as exc:
                skipped.append({"file": name, "reason": str(exc)})
                continue
            x, y = smooth_intensity(xf.Int_t[1], window=max(1, int(window)), sampling=max(1, int(sampling)))
            freq, mag = xf.Int_t_fft
            files.append(
                {
                    "file": name,
                    "label": xf.label,
                    "frame_time": float(xf.t0),
                    "frames": int(xf.Int_t.shape[1]),
                    "x": pack(x, "int32"),
                    "y": pack(y),
                    "fft_x": pack(freq),
                    "fft_y": pack(mag),
                }
            )
        return {"files": files, "skipped": skipped}

    # ── two-time ─────────────────────────────────────────────────────────────────────────────

    def twotime_bins(self, name: str) -> dict[str, Any]:
        """The q-bins a two-time file was processed for, in the order of its C2 blocks."""
        xf = self._twotime(name)
        assert xf.c2_processed_bins is not None
        bins = [int(b) for b in xf.c2_processed_bins.tolist()]
        labels = xf.get_twotime_qbin_labels()
        return {
            "file": name,
            "label": xf.label,
            "bins": [
                {"index": i, "qbin": b, "label": lbl} for i, (b, lbl) in enumerate(zip(bins, labels, strict=True))
            ],
            "time_step": float(xf.c2_t0) if xf.c2_t0 is not None else float(xf.t0),
        }

    def twotime_bin_at(self, name: str, x: float, y: float) -> dict[str, Any]:
        """The C2 block index of the q-bin at detector pixel (``x``, ``y``), or None."""
        xf = self._twotime(name)
        assert xf.c2_processed_bins is not None
        col, row = round(float(x)), round(float(y))
        shape = xf.dqmap.shape
        selection = None
        qbin = 0
        if 0 <= col < shape[1] and 0 <= row < shape[0]:
            qbin = int(xf.dqmap[row, col])
            hits = np.flatnonzero(xf.c2_processed_bins == qbin)
            if qbin > 0 and hits.size:
                selection = int(hits[0])
        return {"x": col, "y": row, "qbin": qbin, "selection": selection}

    def twotime_c2(
        self, name: str, selection: int = 0, correct_diag: bool = True, max_size: int = 512
    ) -> dict[str, Any]:
        """The two-time correlation of one q-bin, at most ``max_size`` by ``max_size``, with the
        g2 computed from it (whole run and time segments)."""
        xf = self._twotime(name)
        assert xf.c2_processed_bins is not None
        count = int(xf.c2_processed_bins.size)
        if not 0 <= int(selection) < count:
            raise WorkspaceError(f"selection must be in 0 … {count - 1}")
        result = xf.get_twotime_c2(selection=int(selection), correct_diag=bool(correct_diag), max_size=int(max_size))
        c2 = np.asarray(result["c2_mat"], dtype=np.float32)
        levels = percentile_table(c2)
        g2_full = np.asarray(result["g2_full"], dtype=np.float32)
        g2_partial = np.asarray(result["g2_partial"], dtype=np.float32)
        qbin = int(xf.c2_processed_bins[int(selection)])
        return {
            "file": name,
            "label": xf.label,
            "selection": int(selection),
            "qbin": qbin,
            "bin_label": xf.get_qbin_label(qbin),
            "c2": pack(c2),
            "shape": [int(c2.shape[0]), int(c2.shape[1])],
            "delta_t": float(result["delta_t"]),
            "acquire_period": float(result["acquire_period"]),
            "levels": pack(levels),
            "zmin": float(levels[1]),  # 0.5 %
            "zmax": float(levels[-2]),  # 99.5 %
            "g2_full": pack(g2_full),
            "g2_partial": pack(g2_partial),
        }
