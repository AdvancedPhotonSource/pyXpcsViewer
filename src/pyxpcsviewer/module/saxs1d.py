import numpy as np
from .g2mod import create_slice
from ..plothandler.matplot_qt import get_color_marker
import pyqtgraph as pg

pg.setConfigOption("background", "w")


def offset_intensity(Iq, n, plot_offset=None, yscale=None):
    """
    offset the intensity accordingly in both linear and log scale
    """
    if yscale == "linear":
        offset = -1 * plot_offset * n * np.max(Iq)
        Iq = offset + Iq

    elif yscale == "log":
        offset = 10 ** (plot_offset * n)
        Iq = Iq / offset
    return Iq


def norm_saxs_data(Iq, q, plot_norm=0):
    """
    normalize small angle scattering data to enhance the visual difference;
    log / linear plot is handled by matplotlib ax objects;
    Args:
        Iq: SAXS Intensity, numpy.ndarray
        q: wave transfer;
        plot_norm: [0, 1, 2, 3]
            0: no normalization
            1: q^2
            2: q^4
            3: I / I0
    Return:
        Iq: normalized SAXS data
        xlabel:
        ylabel:
    Raise:
        ValueError: if plot_norm not in [0, 1, 2, 3]
    """
    if plot_norm not in range(4):
        raise ValueError("plot_norm must be in [0, 1, 2, 3]")

    ylabel = "Intensity"
    if plot_norm == 1:
        Iq = Iq * np.square(q)
        ylabel = ylabel + " * q^2"
    elif plot_norm == 2:
        Iq = Iq * np.square(np.square(q))
        ylabel = ylabel + " * q^4"
    elif plot_norm == 3:
        baseline = Iq[0]
        Iq = Iq / baseline
        ylabel = ylabel + " / I_0"

    xlabel = "q (Å⁻¹)"
    return Iq, q, xlabel, ylabel


def switch_line_builder(hdl, lb_type=None):
    hdl.link_line_builder(lb_type)


def plot_line_with_marker(
    plot_item, x, y, index, label, alpha_val, marker_size=6, log_x=False, log_y=False
):
    color_hex, marker = get_color_marker(index, backend="pyqtgraph")
    rgba = pg.mkColor(color_hex).getRgb()[:3] + (int(alpha_val * 255),)

    # Line: works fine with log scales
    plot_item.plot(x, y, pen=pg.mkPen(color=rgba, width=1.5), name=label)

    # Transform for log-scale scatter alignment
    x_trans = np.log10(x) if log_x else x
    y_trans = np.log10(y) if log_y else y

    # Marker: manually apply log transform
    scatter = pg.ScatterPlotItem(
        x=x_trans,
        y=y_trans,
        symbol=marker,
        size=marker_size,
        pen=pg.mkPen(color=rgba, width=1.5),
        brush=None,
    )
    plot_item.addItem(scatter)


def pg_plot(
    xf_list,
    pg_hdl,
    plot_type=2,
    plot_norm=0,
    plot_offset=0,
    title=None,
    rows=None,
    qmax=10.0,
    qmin=0,
    loc="best",
    marker_size=3,
    sampling=1,
    all_phi=False,
    absolute_crosssection=False,
    subtract_background=False,
    bkg_file=None,
    weight=1.0,
    roi_list=None,
    show_roi=True,
    show_phi_roi=True,
):

    xscale = ["linear", "log"][plot_type % 2]
    yscale = ["linear", "log"][plot_type // 2]

    pg_hdl.clear()
    plot_item = pg_hdl.getPlotItem()
    plot_item.setTitle(title)
    plot_item.addLegend()

    if rows in [None, []]:
        alpha = np.ones(len(xf_list)) * 0.85
    else:
        alpha = np.ones(len(xf_list)) * 0.5
        for t in rows:
            if t < len(xf_list):
                alpha[t] = 1.0

    if subtract_background and bkg_file is not None:
        Iq_bkg = np.copy(bkg_file.saxs_1d["Iq"])
        q_bkg = np.copy(bkg_file.saxs_1d["q"])
        # apply sampling
        Iq_bkg, q_bkg = Iq_bkg[:, ::sampling], q_bkg[::sampling]

        sl = create_slice(q_bkg, (qmin, qmax))
        Iq_bkg = Iq_bkg[:, sl]
        q_bkg = q_bkg[sl]
        if absolute_crosssection and bkg_file.abs_cross_section_scale is not None:
            Iq_bkg *= bkg_file.abs_cross_section_scale

    log_x = xscale == "log"
    log_y = yscale == "log"
    plot_item.setLogMode(x=log_x, y=log_y)
    plot_id = 0
    for n, fi in enumerate(xf_list):
        Iq, q = np.copy(fi.saxs_1d["Iq"]), np.copy(fi.saxs_1d["q"])
        # apply sampling
        Iq, q = Iq[:, ::sampling], q[::sampling]

        # apply qrange
        sl = create_slice(q, (qmin, qmax))
        Iq = Iq[:, sl]
        q = q[sl]

        if absolute_crosssection and fi.abs_cross_section_scale is not None:
            Iq *= fi.abs_cross_section_scale

        if subtract_background and bkg_file is not None:
            if np.allclose(q, q_bkg):
                Iq = Iq - weight * Iq_bkg
                bad_index = Iq <= 0
                Iq[bad_index] = float("nan")
            else:
                print("bkg not applied because bkg q has different values.")

        if all_phi:
            num_lines = Iq.shape[0]
        else:
            num_lines = 1

        if show_phi_roi:
            num_lines = 0

        for m in range(num_lines):
            Iqm = offset_intensity(Iq[m], plot_id, plot_offset, yscale)
            Iqm, _, xlabel, ylabel = norm_saxs_data(Iqm, q, plot_norm)
            plot_line_with_marker(
                plot_item,
                q,
                Iqm,
                plot_id,
                fi.saxs_1d["labels"][m],
                alpha[n],
                marker_size=marker_size,
                log_x=log_x,
                log_y=log_y,
            )
            plot_id += 1

    if plot_norm == 0:  # no normalization
        if absolute_crosssection:
            ylabel = "Intensity (1/cm)"
        else:
            ylabel = "Intensity (photon/pixel/frame)"

    if show_phi_roi:
        plot_item.setLabel("bottom", "phi (degree)")  # x-axis label
        plot_item.setLabel("left", "Intensity (a.u.)")  # y-axis label
    else:
        plot_item.setLabel("bottom", xlabel)
        plot_item.setLabel("left", ylabel)

    if show_phi_roi:
        xscale = "linear"
    plot_item.showGrid(x=True, y=True, alpha=0.3)

    return
