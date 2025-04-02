import numpy as np
from ..plothandler.matplot_qt import get_color_marker
import pyqtgraph as pg

pg.setConfigOption("background", "w")


# Mapping from integer codes to string codes (based on Matplotlib docs)
_MPL_LOC_INT_TO_STR = {
    1: "upper right",
    2: "upper left",
    3: "lower left",
    4: "lower right",
    5: "right",  # Often equivalent to center right in placement
    6: "center left",
    7: "center right",
    8: "lower center",
    9: "upper center",
    10: "center",
}


def get_pyqtgraph_anchor_params(loc, padding=10):
    """
    Converts a Matplotlib loc string or code to pyqtgraph anchor parameters.

    Calculates the 'itemPos', 'parentPos', and 'offset' needed to position
    a pyqtgraph LegendItem similarly to how Matplotlib places legends
    using the 'loc' parameter.

    Args:
        loc (str or int): Matplotlib location code. Accepts standard strings
                          ('upper left', 'center', etc.) or integer codes (0-10).
        padding (int): Pixel padding to use for the offset from the anchor point.
                       Positive values generally push the legend inwards from
                       the edge/corner. Defaults to 10.

    Returns:
        dict or None: A dictionary with keys 'itemPos', 'parentPos', and 'offset'
                      suitable for unpacking into LegendItem.anchor(**params),
                      or None if loc='best' (code 0) as it's not directly
                      supported by pyqtgraph's deterministic anchoring.

    Raises:
        ValueError: If the loc code or type is invalid.

    Example Usage:
        plot_item = pg.PlotItem()
        legend = plot_item.addLegend()
        # ... plot data ...
        try:
            anchor_params = get_pyqtgraph_anchor_params('lower left', padding=15)
            if anchor_params:
                legend.anchor(**anchor_params)
            else:
                print("Using default legend position for 'best'.") # Handle 'best'
        except ValueError as e:
            print(f"Error setting legend position: {e}")

    """
    if isinstance(loc, int):
        if loc in _MPL_LOC_INT_TO_STR:
            loc_str = _MPL_LOC_INT_TO_STR[loc]
        else:
            raise ValueError(f"Invalid Matplotlib integer location code: {loc}")
    elif isinstance(loc, str):
        loc_str = (
            loc.lower().replace(" ", "").replace("_", "")
        )  # Normalize input string
    else:
        raise ValueError(f"Invalid loc type: {type(loc)}. Must be str or int.")

    # --- Define anchor points and offset multipliers ---
    # Map: loc_string -> (itemPos, parentPos, offset_multipliers)
    # Offset multipliers (mult_x, mult_y) determine offset direction based on padding
    _ANCHOR_MAP = {
        # Corners
        "upperleft": ((0.0, 0.0), (0.0, 0.0), (1, 1)),  # Offset moves down-right
        "upperright": ((1.0, 0.0), (1.0, 0.0), (-1, 1)),  # Offset moves down-left
        "lowerleft": ((0.0, 1.0), (0.0, 1.0), (1, -1)),  # Offset moves up-right
        "lowerright": ((1.0, 1.0), (1.0, 1.0), (-1, -1)),  # Offset moves up-left
        # Centers
        "center": ((0.5, 0.5), (0.5, 0.5), (0, 0)),  # No offset needed usually
        "lowercenter": ((0.5, 1.0), (0.5, 1.0), (0, -1)),  # Offset moves up
        "uppercenter": ((0.5, 0.0), (0.5, 0.0), (0, 1)),  # Offset moves down
        # Sides (center align on edge)
        "centerleft": ((0.0, 0.5), (0.0, 0.5), (1, 0)),  # Offset moves right
        "centerright": ((1.0, 0.5), (1.0, 0.5), (-1, 0)),  # Offset moves left
        "right": (
            (1.0, 0.5),
            (1.0, 0.5),
            (-1, 0),
        ),  # Treat 'right' same as 'centerright'
    }

    if loc_str in _ANCHOR_MAP:
        itemPos, parentPos, offset_mult = _ANCHOR_MAP[loc_str]
        offset = (padding * offset_mult[0], padding * offset_mult[1])
        return {"itemPos": itemPos, "parentPos": parentPos, "offset": offset}
    else:
        raise ValueError(f"Invalid or unsupported Matplotlib location string: '{loc}'")


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
    valid = y > 0
    x_trans = np.log10(x[valid]) if log_x else x
    y_trans = np.log10(y[valid]) if log_y else y

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

    pg_hdl.clear()
    plot_item = pg_hdl.getPlotItem()
    plot_item.setTitle(title)
    legend = plot_item.addLegend()
    anchor_param = get_pyqtgraph_anchor_params(loc, padding=15)
    legend.anchor(**anchor_param)

    alpha = np.ones(len(xf_list)) * 1.0
    if not rows:
        alpha *= 0.85
        for t in rows:
            alpha[t] = 1.0

    if not subtract_background:
        bkg_file = None
    norm_method = [None, "q2", "q4", "I0"][plot_norm]
    log_x = (False, True)[plot_type % 2]
    log_y = (False, True)[plot_type // 2]
    plot_item.setLogMode(x=log_x, y=log_y)

    plot_id = 0
    for n, fi in enumerate(xf_list):
        q, Iq, xlabel, ylabel = fi.get_saxs1d_data(
            bkg_xf=bkg_file,
            bkg_weight=weight,
            qrange=(qmin, qmax),
            sampling=sampling,
            norm_method=norm_method,
            use_absolute_crosssection=absolute_crosssection,
        )

        num_lines = Iq.shape[0] if all_phi else 1
        for m in range(num_lines):
            plot_line_with_marker(
                plot_item,
                q,
                Iq[m],
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

    plot_item.setLabel("bottom", xlabel)
    plot_item.setLabel("left", ylabel)
    plot_item.showGrid(x=True, y=True, alpha=0.3)

    return
