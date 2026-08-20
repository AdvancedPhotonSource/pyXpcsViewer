# Copyright © UChicago Argonne LLC
# See LICENSE file for details
"""G2 outlier-rejection debug dialog (G2_regroup tab).

The "Debug" button in the Group Setting box opens this dialog for the first
selected Multitau file. It visualizes what the configured outlier settings
(method / threshold / combine) do to the per-pixel g2:

* "sq-bin histograms" tab: per-sq-bin histograms of g2_pixel with the
  center + threshold*spread bounds used by find_g2_pixel_outliers — either
  all delays for one bin (bin sweep) or all bins for one delay (delay sweep,
  paged).
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
from PySide6 import QtWidgets
from PySide6.QtCore import Qt


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
    Tab 1 (bad-pixel map) is filled in by a later task.
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
    tabs.addTab(QtWidgets.QWidget(), "Bad-pixel map")
    layout.addWidget(tabs)
    return tabs
