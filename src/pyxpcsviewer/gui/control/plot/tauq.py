# Copyright © UChicago Argonne LLC
# See LICENSE file for details
import warnings

import numpy as np
import pyqtgraph as pg

from .palette import get_color_marker


def _log_errorbar_coords(
    x: np.ndarray, y: np.ndarray, e: np.ndarray, log_x: bool, log_y: bool
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Compute (x, y, top, bottom) for an ``ErrorBarItem`` on a log-scaled axis.

    ``pg.ErrorBarItem`` has no ``setLogMode``, so unlike curves/markers added via
    ``PlotItem.plot()`` it is never transformed by ``PlotItem.setLogMode`` — its
    coordinates must be pre-converted here or the bars land off the marker.
    """
    x_disp = np.log10(x) if log_x else x
    if not log_y:
        return x_disp, y, e, e

    y_disp = np.log10(y)
    top = np.log10(y + e) - y_disp
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        lower = np.log10(y - e)
    bottom = np.where(np.isfinite(lower), y_disp - lower, 0.0)
    return x_disp, y_disp, top, bottom


def _plot_scatter_with_errors(
    ax,
    x: np.ndarray,
    y: np.ndarray,
    e: np.ndarray,
    idx: int,
    *,
    log_x: bool = False,
    log_y: bool = False,
    symbol_size: int = 3,
    label: str | None = None,
) -> None:
    """Plot scatter markers with log-aware error bars on *ax*.

    Args:
        ax: pyqtgraph ``PlotItem`` to draw on.
        x, y, e: Data arrays (same length).
        idx: Series index used to look up colour and marker from the palette.
        log_x / log_y: Whether the axis uses a log scale.
        symbol_size: Marker diameter in points.
        label: Legend label (``None`` → no entry).
    """
    color, marker = get_color_marker(idx, backend="pyqtgraph")
    ax.plot(
        x,
        y,
        pen=None,
        symbol=marker,
        symbolSize=symbol_size,
        symbolBrush=pg.mkBrush(255, 255, 255, 128),
        symbolPen=pg.mkPen(color=color, width=1),
        name=label,
    )
    x_err, y_err, top, bottom = _log_errorbar_coords(x, y, e, log_x, log_y)
    ax.addItem(pg.ErrorBarItem(x=x_err, y=y_err, top=top, bottom=bottom, pen=color))


def plot(
    xf_list,
    hdl,
    q_range: tuple,
    offset: float,
    plot_type: int = 3,
) -> None:
    """Plot ``tau(q)`` data with optional vertical offsets and per-file fit lines.

    Args:
        xf_list: List of :class:`~pyxpcsviewer.core.xpcs_file.XpcsFile` instances with g2 fits.
        hdl: pyqtgraph ``PlotWidget`` to draw on.
        q_range: Ignored (reserved for future Q filtering).
        offset: Vertical log-offset between files.
        plot_type: Bitmask controlling axes scales — bit 0 = x-log, bits 1-2 = y-log.
    """
    hdl.clear()

    log_x = bool(plot_type % 2)
    log_y = bool(plot_type // 2)

    for n, xf in enumerate(xf_list):
        s = 10 ** (offset * n)
        x = xf.fit_summary["q_val"]
        y = xf.fit_summary["fit_val"][:, 0, 1] / s
        e = xf.fit_summary["fit_val"][:, 1, 1] / s
        valid_idx = e > 0
        x = x[valid_idx]
        y = y[valid_idx]
        e = e[valid_idx]

        _plot_scatter_with_errors(
            hdl, x, y, e, n, log_x=log_x, log_y=log_y, label=xf.label
        )

        if xf.fit_summary.get("tauq_success", False):
            color, _ = get_color_marker(n, backend="pyqtgraph")
            fit_x = xf.fit_summary["tauq_fit_line"]["fit_x"]
            fit_y = xf.fit_summary["tauq_fit_line"]["fit_y"] / s
            hdl.plot(fit_x, fit_y, pen=color)

    hdl.setLabel("bottom", "q (Å⁻¹)")
    hdl.setLabel("left", "τ (s)")
    hdl.addLegend()
    hdl.setLogMode(x=log_x, y=log_y)


def plot_pre(xf_list, hdl) -> None:
    """Display a 2x2 subplot grid of g2 fitting parameters (a, tau, c, d) vs q.

    Args:
        xf_list: List of :class:`~pyxpcsviewer.core.xpcs_file.XpcsFile` instances with fits.
        hdl: pyqtgraph ``GraphicsLayoutWidget`` to draw on.
    """
    hdl.clear()
    layout = hdl.addLayout()

    titles = ["contrast", "τ (s)", "stretch", "baseline"]
    yscales = ["linear", "linear", "log", "linear"]

    plots = []
    for i in range(4):
        plot_item = layout.addPlot(row=i // 2, col=i % 2)
        plot_item.setLabel("bottom", "q (Å⁻¹)")
        if yscales[i] == "log":
            plot_item.setLogMode(x=False, y=True)
        plots.append(plot_item)

    for idx, xf in enumerate(xf_list):
        for n in range(4):
            x = xf.fit_summary["q_val"]
            y = xf.fit_summary["fit_val"][:, 0, n]
            e = xf.fit_summary["fit_val"][:, 1, n]
            _plot_scatter_with_errors(
                plots[n], x, y, e, idx, log_y=yscales[n] == "log"
            )

    last = xf_list[-1] if xf_list else None
    if last and last.fit_summary.get("bounds") is not None:
        bounds = last.fit_summary["bounds"]
        xmin = np.min(last.fit_summary["q_val"])
        xmax = np.max(last.fit_summary["q_val"])

        for n in range(4):
            plots[n].setTitle(titles[n])

            ymin = bounds[0][n]
            ymax = bounds[1][n]
            y_lo, y_hi = ymin * 0.8, ymax * 1.2
            if yscales[n] == "log":
                y_lo, y_hi = np.log10(y_lo), np.log10(y_hi)
            plots[n].setYRange(y_lo, y_hi)

            for y_val, pen_color, lbl in zip(
                (ymin, ymax), ("b", "g"), ("lower bound", "upper bound"), strict=True
            ):
                plots[n].plot(
                    [xmin, xmax], [y_val, y_val],
                    pen=pg.mkPen(pen_color, width=1),
                    name=lbl,
                )
