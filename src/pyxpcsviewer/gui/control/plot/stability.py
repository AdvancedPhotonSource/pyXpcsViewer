# Copyright © UChicago Argonne LLC
# See LICENSE file for details
from .saxs_1d import get_pyqtgraph_anchor_params, plot_line_with_marker


def plot(
    fc,
    pg_hdl,
    plot_type: int = 2,
    plot_norm: int = 0,
    title: str | None = None,
    loc: str = "upper right",
    **kwargs,
) -> None:
    """Plot SAXS-1D segments (partial intensity vs Q) with optional log-log display.

    Args:
        fc: An :class:`~pyxpcsviewer.core.xpcs_file.XpcsFile` instance.
        pg_hdl: pyqtgraph ``PlotWidget`` to draw on.
        plot_type: Bitmask controlling axes — bit 0 = x-log, bits 1-2 = y-log.
        plot_norm: Normalisation index (0=None, 1=q², 2=q⁴, 3=I₀).
        title: Plot title shown as the file label.
        loc: Anchor position for the legend box.
        **kwargs: Ignored (reserved for future extensions).
    """
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

    q, Iqp, xlabel, ylabel = fc.get_saxs1d_data(target="saxs1d_partial", norm_method=norm_method)
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
