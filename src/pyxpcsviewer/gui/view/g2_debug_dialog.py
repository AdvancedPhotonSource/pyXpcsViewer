# Copyright © UChicago Argonne LLC
# See LICENSE file for details
"""G2 outlier-rejection debug dialog (G2_regroup tab).

The "Debug" button in the Group Setting box opens this dialog for the first
selected Multitau file. It visualizes what the configured outlier settings
(method / threshold / combine) do to the per-pixel g2:

* "sq-bin histograms" tab: per-sq-bin histograms of g2_pixel with the
  center + threshold*spread bounds used by find_g2_pixel_outliers, for all
  delays of one selectable bin (bin sweep).
* "Bad-pixel map" tab: detector image of how many delays each pixel was
  flagged as an outlier, with a minimum-tag filter.

The heavy HDF5 load + outlier pass runs on G2DebugWorker (QThread); plot
building is synchronous and lives in build_debug_plots() so offscreen tests
can exercise it directly with a synthetic bundle (the dict returned by
core.g2_utils.compute_g2_debug_bundle).
"""

from __future__ import annotations

import math
import os
from typing import Any, Protocol

import numpy as np
import pyqtgraph as pg  # type: ignore[import-untyped]
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMessageBox

from pyxpcsviewer.core.g2_utils import compute_g2_debug_bundle


class _XpcsFileLike(Protocol):
    """Structural subset of core.xpcs_file.XpcsFile the dialog needs."""

    fname: str
    sqmap: np.ndarray
    dqmap: np.ndarray

    @property
    def G2(self) -> np.ndarray | None: ...


def _center_and_hi(values: np.ndarray, method: str, threshold: float) -> tuple[float, float]:
    """Center and upper bound exactly as find_g2_pixel_outliers computes them.

    ``values`` must already be the non-zero (alive) g2_pixel values for one
    (sq bin, delay) pair.
    """
    if method == "StandardDeviation":
        center = float(np.mean(values))
        spread = float(np.std(values))
    else:  # MeanAbsoluteDeviation (default)
        center = float(np.median(values))
        spread = float(np.median(np.abs(values - center)))
    if spread == 0:
        spread = 1.0
    return center, center + threshold * spread


def _add_hist(
    item: pg.PlotItem,
    values: np.ndarray,
    n_outlier: int,
    title_prefix: str,
    method: str,
    threshold: float,
) -> None:
    """Draw one histogram subplot with center / hi-bound lines and a title.

    Zero (photon-starved) values must already be removed from ``values``;
    an empty array renders a labeled empty axis.
    """
    if values.size == 0:
        item.setTitle(f"{title_prefix}  (all zero)")
        return
    center, hi = _center_and_hi(values, method, threshold)
    counts, edges = np.histogram(values, bins=40)
    item.addItem(
        pg.BarGraphItem(
            x=0.5 * (edges[1:] + edges[:-1]),
            height=counts,
            width=float(edges[1] - edges[0]),
            brush=pg.mkBrush("steelblue"),
        )
    )
    item.addLine(x=center, pen=pg.mkPen("g", width=1))
    item.addLine(x=hi, pen=pg.mkPen("r", style=Qt.PenStyle.DashLine, width=1))
    item.setTitle(f"{title_prefix}  n={values.size}  out={n_outlier}")


class _BinSweepPanel(QtWidgets.QWidget):
    """All-delay histogram grid for one selectable sq bin."""

    def __init__(
        self,
        bundle: dict[str, Any],
        method: str,
        threshold: float,
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._bundle = bundle
        self._method = method
        self._threshold = threshold

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        top = QtWidgets.QHBoxLayout()
        top.addWidget(QtWidgets.QLabel("sq bin:"))
        self.spin = QtWidgets.QSpinBox()
        self.spin.setObjectName("g2_debug_sq_spin")
        self.spin.setRange(1, bundle["n_sq"])
        self.spin.valueChanged.connect(self._render)
        top.addWidget(self.spin)
        top.addStretch(1)
        layout.addLayout(top)

        n_delays = bundle["n_delays"]
        self._cols = math.ceil(math.sqrt(n_delays))
        self.glw = pg.GraphicsLayoutWidget()
        layout.addWidget(self.glw)
        self._render()

    def _render(self) -> None:
        self.glw.clear()
        d = self.spin.value()
        roi = self._bundle["sqmap_1d"] == d
        if int(roi.sum()) == 0:
            item = self.glw.addPlot(row=0, col=0)
            item.setTitle(f"sq={d}  (empty)")
            return
        for delay in range(self._bundle["n_delays"]):
            row, col = divmod(delay, self._cols)
            item = self.glw.addPlot(row=row, col=col)
            values = self._bundle["g2_pixel"][delay][roi]
            values = values[values != 0]
            n_outlier = int(self._bundle["bad"][delay][roi].sum())
            _add_hist(item, values, n_outlier, f"delay={delay}", self._method, self._threshold)


class _BadMapPanel(QtWidgets.QWidget):
    """Detector image of outlier tag counts with a minimum-tag filter."""

    def __init__(self, bundle: dict[str, Any], parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self._counts = bundle["bad"].sum(axis=0).reshape(bundle["img_shape"])
        self._n_dead = bundle["n_dead"]

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        top = QtWidgets.QHBoxLayout()
        top.addWidget(QtWidgets.QLabel("min tag count:"))
        self.spin = QtWidgets.QSpinBox()
        self.spin.setObjectName("g2_debug_mintag_spin")
        self.spin.setRange(1, max(1, int(self._counts.max())))
        self.spin.valueChanged.connect(self._render)
        top.addWidget(self.spin)
        self.summary = QtWidgets.QLabel("")
        self.summary.setObjectName("g2_debug_map_summary")
        top.addWidget(self.summary)
        top.addStretch(1)
        layout.addLayout(top)

        self.view = pg.ImageView()
        self.view.setObjectName("g2_debug_map_view")
        self.view.roi.setVisible(False)
        self.view.setColorMap(pg.colormap.getFromMatplotlib("hot"))
        layout.addWidget(self.view)
        self._render()

    def _render(self) -> None:
        min_tag = self.spin.value()
        img = self._counts.astype(float)
        img[self._counts < min_tag] = 0.0
        vmax = max(1, int(self._counts.max()))
        self.view.setImage(img)
        # keep the level range non-degenerate: at min_tag == vmax, levels
        # (c, c) would map the remaining pixels to the colormap's low color
        lo = min(min_tag, vmax - 1) if vmax > 1 else 0
        self.view.setLevels(lo, vmax)
        n = int(np.sum(self._counts >= min_tag))
        total = int(self._counts.size)
        self.summary.setText(
            f"tagged ≥{min_tag}: {n} ({100.0 * n / total:.3f}%), "
            f"max count = {int(self._counts.max())}, dead pixels = {self._n_dead}"
        )


def build_debug_plots(
    widget: QtWidgets.QWidget,
    bundle: dict[str, Any],
    fname: str,
    method: str,
    threshold: float,
    combine_outlier: bool,
) -> QtWidgets.QTabWidget:
    """Populate *widget* with the debug header and the two tabs.

    Appends to *widget*'s existing layout and returns the QTabWidget.
    Tab 1 is the bad-pixel map panel (``_BadMapPanel``).
    """
    layout = widget.layout()
    if layout is None:
        raise RuntimeError("build_debug_plots() needs a host widget with a layout")
    header = QtWidgets.QLabel(
        f"{os.path.basename(fname)} | delays={bundle['n_delays']}  sq={bundle['n_sq']}  "
        f"dq={bundle['n_dq']}  dead={bundle['n_dead']} | "
        f"method={method}, threshold={threshold:g}, combine={combine_outlier}"
    )
    header.setObjectName("g2_debug_header")
    header.setWordWrap(True)
    layout.addWidget(header)

    tabs = QtWidgets.QTabWidget()
    tabs.addTab(_BinSweepPanel(bundle, method, threshold), "sq-bin histograms")
    tabs.addTab(_BadMapPanel(bundle), "Bad-pixel map")
    layout.addWidget(tabs)
    return tabs


class G2DebugWorker(QtCore.QThread):
    """Load the unnormalized G2 (fresh h5py handle per read — thread-safe)
    and run the outlier pass off the main thread."""

    progress_stage = QtCore.Signal(str)
    finished_bundle = QtCore.Signal(object)
    failed = QtCore.Signal(str)

    def __init__(
        self,
        xfile: _XpcsFileLike,
        method: str,
        threshold: float,
        combine_outlier: bool,
        parent: QtCore.QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._xfile = xfile
        self._method = method
        self._threshold = threshold
        self._combine = combine_outlier

    def run(self) -> None:
        try:
            self.progress_stage.emit("Loading G2…")
            G2 = self._xfile.G2
            if G2 is None:
                raise ValueError("file has no unnormalized G2 (/xpcs/multitau/unnormalized_G2)")
            sqmap = self._xfile.sqmap
            dqmap = self._xfile.dqmap
            self.progress_stage.emit("Detecting outliers…")
            bundle = compute_g2_debug_bundle(
                sqmap,
                dqmap,
                G2,
                outlier_method=self._method,
                outlier_threshold=self._threshold,
                combine_outlier=self._combine,
            )
        except Exception as exc:  # report any failure to the UI
            self.failed.emit(f"{type(exc).__name__}: {exc}")
            return
        self.finished_bundle.emit(bundle)


class G2DebugDialog(QtWidgets.QDialog):
    """Modeless debug dialog: placeholder while the worker runs, then the
    plot tabs. Close is ignored while the worker is running (the HDF5 read
    cannot be interrupted mid-read)."""

    def __init__(
        self,
        xfile: _XpcsFileLike,
        method: str,
        threshold: float,
        combine_outlier: bool,
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._fname = xfile.fname
        self._method = method
        self._threshold = threshold
        self._combine = combine_outlier
        self._worker_running = True
        self.setWindowTitle(f"G2 outlier debug — {os.path.basename(self._fname)}")
        self.setMinimumSize(900, 700)

        layout = QtWidgets.QVBoxLayout(self)
        self._placeholder = QtWidgets.QLabel("Computing G2 debug data…\n(close is disabled until this finishes)")
        self._placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._stage = QtWidgets.QLabel("…")
        self._progress = QtWidgets.QProgressBar()
        self._progress.setRange(0, 0)  # indeterminate
        layout.addWidget(self._placeholder)
        layout.addWidget(self._stage)
        layout.addWidget(self._progress)

        self._worker = G2DebugWorker(xfile, method, threshold, combine_outlier, self)
        self._worker.progress_stage.connect(self._on_stage)
        self._worker.finished_bundle.connect(self._on_bundle)
        self._worker.failed.connect(self._on_failed)
        self._worker.start()

    def _on_stage(self, text: str) -> None:
        self._stage.setText(text)

    def _on_bundle(self, bundle: dict[str, Any]) -> None:
        self._worker_running = False
        layout = self.layout()
        if layout is None:  # created in __init__; the dialog cannot lose it
            raise RuntimeError("G2DebugDialog lost its layout before the bundle arrived")
        for w in (self._placeholder, self._stage, self._progress):
            layout.removeWidget(w)
            w.deleteLater()
        build_debug_plots(self, bundle, self._fname, self._method, self._threshold, self._combine)

    def _on_failed(self, msg: str) -> None:
        self._worker_running = False
        self._show_failure(msg)
        self.close()

    def _show_failure(self, msg: str) -> None:
        QMessageBox.critical(self, "G2 debug failed", msg)

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        if self._worker_running:
            event.ignore()
            return
        event.accept()
