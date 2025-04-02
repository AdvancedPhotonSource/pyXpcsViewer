from .saxs1d import get_pyqtgraph_anchor_params, plot_line_with_marker
import numpy as np


def plot(
    fc,
    pg_hdl,
    plot_type=2,
    plot_norm=0,
    legend=None,
    title=None,
    loc="upper right",
    **kwargs,
):

    pg_hdl.clear()
    plot_item = pg_hdl.getPlotItem()

    plot_item.setTitle(fc.label)
    legend = plot_item.addLegend()
    anchor_param = get_pyqtgraph_anchor_params(loc, padding=15)
    legend.anchor(**anchor_param)

    norm_method = [None, "q2", "q4", "I0"][plot_norm]
    log_x = (False, True)[plot_type % 2]
    log_y = (False, True)[plot_type // 2]
    plot_item.setLogMode(x=log_x, y=log_y)

    q, Iqp, xlabel, ylabel = fc.get_saxs1d_data(
        target="saxs1d_partial", norm_method=norm_method
    )
    for n in range(Iqp.shape[0]):
        plot_line_with_marker(
            plot_item,
            q,
            Iqp[n],
            n,
            f"p{n}",  # label
            1.0,  # alpha
            marker_size=6,
            log_x=log_x,
            log_y=log_y,
        )

    plot_item.setLabel("bottom", xlabel)
    plot_item.setLabel("left", ylabel)
    plot_item.showGrid(x=True, y=True, alpha=0.3)
