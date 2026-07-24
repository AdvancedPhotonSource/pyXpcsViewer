import logging

import numpy as np
import pyqtgraph as pg

pg.setConfigOption("foreground", pg.mkColor(80, 80, 80))
# pg.setConfigOption("background", 'w')
logger = logging.getLogger(__name__)

# colors converted from
# https://matplotlib.org/stable/tutorials/colors/colors.html
# colors = ('#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
#           '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf')

colors = (
    (31, 119, 180),
    (255, 127, 14),
    (44, 160, 44),
    (214, 39, 40),
    (148, 103, 189),
    (140, 86, 75),
    (227, 119, 194),
    (127, 127, 127),
    (188, 189, 34),
    (23, 190, 207),
)


# https://www.geeksforgeeks.org/pyqtgraph-symbols/
symbols = ["o", "t", "t1", "t2", "t3", "s", "p", "h", "star", "+", "d", "x"]


def get_g2_data(xf_list, q_range=None, t_range=None):
    """Extract G2 data arrays from a list of ``XpcsFile`` objects, optionally filtered by Q and time ranges.

    Args:
        xf_list: List of :class:`~pyxpcsviewer.core.xpcs_file.XpcsFile` instances (must contain ``Multitau`` data).
        q_range: Optional ``(q_min, q_max)`` filter.
        t_range: Optional ``(t_min, t_max)`` filter on the elapsed time axis.

    Returns:
        Tuple of ``(q_values, tel, g2, g2_err, labels)`` for each file, or
        ``(False, None, None, None, None)`` if any file lacks ``Multitau`` data.
    """
    for xf in xf_list:
        if "Multitau" not in xf.atype:
            return False, None, None, None, None

    q, tel, g2, g2_err, labels = [], [], [], [], []
    for fc in xf_list:
        _q, _tel, _g2, _g2_err, _labels = fc.get_g2_data(qrange=q_range, trange=t_range)
        q.append(_q)
        tel.append(_tel)
        g2.append(_g2)
        g2_err.append(_g2_err)
        labels.append(_labels)
    return q, tel, g2, g2_err, labels


def get_g2_stability_data(xf_obj, q_range=None, t_range=None):
    """Extract G2 stability data (from ``g2_partial``) for a single multitau file.

    Args:
        xf_obj: An :class:`~pyxpcsviewer.core.xpcs_file.XpcsFile` instance with ``Multitau`` data.
        q_range: Optional ``(q_min, q_max)`` filter.
        t_range: Optional ``(t_min, t_max)`` filter on the elapsed time axis.

    Returns:
        Tuple of ``(q_values, tel, g2, g2_err, qbin_labels, labels)`` or
        ``(False, None, None, None, None, None)`` if data is invalid.
    """
    if "Multitau" not in xf_obj.atype:
        return False, None, None, None, None

    q, tel, g2, g2_err, qbin_labels, labels = xf_obj.get_g2_stability_data(qrange=q_range, trange=t_range)
    return q, tel, g2, g2_err, qbin_labels, labels


def compute_geometry(g2, plot_type):
    """
    compute the number of figures and number of plot lines for a given type
    and dataset;
    :param g2: input g2 data; 2D array; dim0: t_el; dim1: q_vals
    :param plot_type: string in ['multiple', 'single', 'single-combined']
    :return: tuple of (number_of_figures, number_of_lines)
    """
    if plot_type == "multiple":
        num_figs = g2[0].shape[1]
        num_lines = len(g2)
    elif plot_type == "single":
        num_figs = len(g2)
        num_lines = g2[0].shape[1]
    elif plot_type == "single-combined":
        num_figs = 1
        num_lines = g2[0].shape[1] * len(g2)
    else:
        raise ValueError("plot_type not support.")
    return num_figs, num_lines


def pg_plot(
    hdl,
    xf_list,
    q_range,
    t_range,
    y_range,
    y_auto=False,
    q_auto=False,
    t_auto=False,
    num_col=4,
    rows=None,
    offset=0,
    show_fit=False,
    show_label=False,
    bounds=None,
    fit_flag=None,
    plot_type: str = "multiple",
    subtract_baseline=True,
    marker_size=5,
    label_size=4,
    fit_func="single",
    **kwargs,
):
    """Plot multitau G2 curves in a multi-panel pyqtgraph layout.

    Supports ``"multiple"``, ``"single"``, and ``"single-combined"`` layouts,
    optional g2 fitting overlay, and baseline subtraction.

    Args:
        hdl: Matplotlib plot handler supporting ``addPlot``, ``adjust_canvas_size``, ``clear``.
        xf_list: List of :class:`~pyxpcsviewer.core.xpcs_file.XpcsFile` instances (Multitau).
        q_range: Q-value filter ``(q_min, q_max)``.
        t_range: Elapsed-time filter ``(t_min, t_max)``.
        y_range: Fixed Y-axis range for all subplots.
        y_auto: Allow auto-range on the y-axis.
        q_auto: Override *q_range* with ``None`` (no Q filter).
        t_auto: Override *t_range* with ``None`` (no time filter).
        num_col: Number of columns in the subplot grid.
        rows: Row indices to display (default all).
        offset: Vertical log-offset per file for stacking.
        show_fit: Overlay g2 fitting curves.
        show_label: Show legend with file labels.
        bounds: Parameter bounds for g2 fitting.
        fit_flag: Boolean flags for free/fixed fit parameters.
        plot_type: Layout mode — ``"multiple"``, ``"single"``, or ``"single-combined"``.
        subtract_baseline: Subtract the fitted baseline from each curve.
        marker_size: Diameter of scatter markers in points.
        label_size: Ignored (reserved for future use).
        fit_func: Fitting model — ``"single"`` or ``"double"`` exponential.
        **kwargs: Reserved for future extensions.
    """
    if q_auto:
        q_range = None
    if t_auto:
        t_range = None
    if y_auto:
        y_range = None

    _q, tel, g2, g2_err, labels = get_g2_data(xf_list, q_range=q_range, t_range=t_range)
    num_figs, _num_lines = compute_geometry(g2, plot_type)

    num_data, num_qval = len(g2), g2[0].shape[1]
    # col and rows for the 2d layout
    col = min(num_figs, num_col)
    row = (num_figs + col - 1) // col

    if len(rows) == 0:
        rows = list(range(len(xf_list)))

    hdl.adjust_canvas_size(num_col=col, num_row=row)
    hdl.clear()
    # a bug in pyqtgraph; the log scale in x-axis doesn't apply
    if t_range:
        t0_range = np.log10(t_range)
    axes = []
    for n in range(num_figs):
        i_col = n % col
        i_row = n // col
        t = hdl.addPlot(row=i_row, col=i_col)
        axes.append(t)
        if show_label:
            t.addLegend(offset=(-1, 1), labelTextSize="9pt", verSpacing=-10)

        t.setMouseEnabled(x=False, y=y_auto)

    for m in range(num_data):
        # default base line to be 1.0; used for non-fitting or fit error cases
        baseline_offset = np.ones(num_qval)
        if show_fit:
            fit_summary = xf_list[m].fit_g2(q_range, t_range, bounds, fit_flag, fit_func)
            # make sure the fitting is successful
            if fit_summary is not None and subtract_baseline and fit_summary["fit_line"][n].get("success", False):
                baseline_offset = fit_summary["fit_val"][:, 0, 3]

        for n in range(num_qval):
            color = colors[rows[m] % len(colors)]
            label = None
            if plot_type == "multiple":
                ax = axes[n]
                title = labels[m][n]
                label = xf_list[m].label
                if m == 0:
                    ax.setTitle(title)
            elif plot_type == "single":
                ax = axes[m]
                # overwrite color; use the same color for the same set;
                color = colors[n % len(colors)]
                title = xf_list[m].label
                # label = labels[m][n]
                ax.setTitle(title)
            elif plot_type == "single-combined":
                ax = axes[0]
                label = xf_list[m].label + labels[m][n]

            ax.setLabel("bottom", "tau (s)")
            ax.setLabel("left", "g2")

            symbol = symbols[rows[m] % len(symbols)]

            x = tel[m]
            # normalize baseline
            y = g2[m][:, n] - baseline_offset[n] + 1.0 + m * offset
            y_err = g2_err[m][:, n]

            pg_plot_one_g2(
                ax,
                x,
                y,
                y_err,
                color,
                label=label,
                symbol=symbol,
                symbol_size=marker_size,
            )
            # if t_range is not None:
            if not y_auto:
                ax.setRange(yRange=y_range)
            if not t_auto:
                ax.setRange(xRange=t0_range)

            if show_fit and fit_summary is not None and fit_summary["fit_line"][n].get("success", False):
                y_fit = fit_summary["fit_line"][n]["fit_y"] + m * offset
                # normalize baseline
                y_fit = y_fit - baseline_offset[n] + 1.0
                ax.plot(
                    fit_summary["fit_line"][n]["fit_x"],
                    y_fit,
                    pen=pg.mkPen(color, width=2.5),
                )
    return


def pg_plot_stability(
    hdl,
    xf_obj,
    q_range,
    t_range,
    y_range,
    y_auto=False,
    q_auto=False,
    t_auto=False,
    num_col=4,
    rows=None,
    offset=0,
    show_fit=False,
    show_label=False,
    bounds=None,
    fit_flag=None,
    plot_type: str = "multiple",
    subtract_baseline=True,
    marker_size=5,
    label_size=4,
    fit_func="single",
    **kwargs,
):
    """Plot G2 stability curves from ``g2_partial`` for a single file.

    Similar to :func:`pg_plot` but works on partial G2 data and does not attempt fitting.

    Args:
        hdl: Plot handler supporting ``addPlot``, ``adjust_canvas_size``, ``clear``.
        xf_obj: A single :class:`~pyxpcsviewer.core.xpcs_file.XpcsFile` instance (Multitau).
        q_range: Q-value filter ``(q_min, q_max)``.
        t_range: Elapsed-time filter ``(t_min, t_max)``.
        y_range: Fixed Y-axis range for all subplots.
        y_auto: Allow auto-range on the y-axis.
        q_auto: Override *q_range* with ``None``.
        t_auto: Override *t_range* with ``None``.
        num_col: Number of columns in the subplot grid.
        rows: Ignored (always uses all data indices).
        offset: Vertical log-offset per frame for stacking.
        show_fit: Not used for stability plots.
        show_label: Show legend with file labels.
        bounds: Reserved for future fitting support.
        fit_flag: Reserved for future fitting support.
        plot_type: Layout mode — ``"multiple"``, ``"single"``, or ``"single-combined"``.
        subtract_baseline: Not used (always baseline = 1.0).
        marker_size: Diameter of scatter markers in points.
        label_size: Ignored (reserved for future use).
        fit_func: Reserved for future fitting support.
        **kwargs: Reserved for future extensions.
    """
    if q_auto:
        q_range = None
    if t_auto:
        t_range = None
    if y_auto:
        y_range = None

    _q, tel, g2, g2_err, qbin_labels, labels = get_g2_stability_data(xf_obj, q_range=q_range, t_range=t_range)

    num_figs, _num_lines = compute_geometry(g2, plot_type)

    num_data, num_qval = len(g2), g2[0].shape[1]
    # col and rows for the 2d layout
    col = min(num_figs, num_col)
    row = (num_figs + col - 1) // col

    rows = np.arange(num_data)

    hdl.adjust_canvas_size(num_col=col, num_row=row)
    hdl.clear()
    # a bug in pyqtgraph; the log scale in x-axis doesn't apply
    if t_range:
        t0_range = np.log10(t_range)
    axes = []
    for n in range(num_figs):
        i_col = n % col
        i_row = n // col
        t = hdl.addPlot(row=i_row, col=i_col)
        axes.append(t)
        if show_label:
            # t.addLegend(offset=(-1, 1), labelTextSize="9pt", verSpacing=-10)
            legend = t.addLegend(labelTextSize="6pt")
            legend.anchor(itemPos=(1, 0), parentPos=(1, 0), offset=(0, 0))

        t.setMouseEnabled(x=False, y=y_auto)

    for m in range(num_data):
        # default base line to be 1.0; used for non-fitting or fit error cases
        baseline_offset = np.ones(num_qval)

        for n in range(num_qval):
            color = colors[rows[m] % len(colors)]
            label = None
            if plot_type == "multiple":
                ax = axes[n]
                title = qbin_labels[n]
                label = f"frame={int(labels[m])}"
                if m == 0:
                    ax.setTitle(title)
            elif plot_type == "single":
                ax = axes[m]
                # overwrite color; use the same color for the same set;
                color = colors[n % len(colors)]
                title = labels[m]
                # label = labels[m][n]
                ax.setTitle(title)
            elif plot_type == "single-combined":
                ax = axes[0]
                label = labels[m] + labels[m][n]

            ax.setLabel("bottom", "tau (s)")
            ax.setLabel("left", "g2")

            symbol = symbols[rows[m] % len(symbols)]

            x = tel
            # normalize baseline
            y = g2[m][:, n] - baseline_offset[n] + 1.0 + m * offset
            y_err = g2_err[m][:, n]

            pg_plot_one_g2(
                ax,
                x,
                y,
                y_err,
                color,
                label=label,
                symbol=symbol,
                symbol_size=marker_size,
            )
            # if t_range is not None:
            if not y_auto:
                ax.setRange(yRange=y_range)
            if not t_auto:
                ax.setRange(xRange=t0_range)

    return


def pg_plot_one_g2(ax, x, y, dy, color: tuple[int, ...], label: str | None, symbol: str, symbol_size: int = 5) -> None:
    """Plot a single G2 curve with error bars on a pyqtgraph axis.

    Args:
        ax: pyqtgraph ``PlotWidget`` / ``PlotItem`` to draw on.
        x: Elapsed time array.
        y: Normalized G2 values.
        dy: G2 error bars (displayed as upper errors only).
        color: RGB colour tuple for the curve and markers.
        label: Legend label, or ``None`` for no entry.
        symbol: pyqtgraph marker symbol name.
        symbol_size: Diameter of markers in points.
    """
    pen = pg.mkPen(color=color, width=2)

    line = pg.ErrorBarItem(x=np.log10(x), y=y, top=dy, bottom=dy, pen=pen)
    pen = pg.mkPen(color=color, width=1)
    ax.plot(
        x,
        y,
        pen=None,
        symbol=symbol,
        name=label,
        symbolSize=symbol_size,
        symbolPen=pen,
        symbolBrush=pg.mkBrush(color=(*color, 0)),
    )

    ax.setLogMode(x=True, y=None)
    ax.addItem(line)
    return
