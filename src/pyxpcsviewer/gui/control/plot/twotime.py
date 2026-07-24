# Copyright © UChicago Argonne LLC
# See LICENSE file for details
import numpy as np
import pyqtgraph as pg

PG_COLORS = [
    "#1f77b4",
    "#ff7f0e",
    "#2ca02c",
    "#d62728",
    "#9467bd",
    "#8c564b",
    "#e377c2",
    "#7f7f7f",
    "#bcbd22",
    "#17becf",
]


def plot_twotime(
    xfile,
    hdl,
    scale: str = "log",
    auto_crop: bool = True,
    highlight_xy: tuple[int, int] | None = None,
    cmap: str = "jet",
    vmin: float | None = None,
    vmax: float | None = None,
    autolevel: bool = True,
    correct_diag: bool = False,
    selection: int = 0,
) -> None:
    """Plot two-time correlation (C2) maps alongside SAXS-2D background and G2 traces.

    Args:
        xfile: An :class:`~pyxpcsviewer.core.xpcs_file.XpcsFile` with ``Twotime`` data.
        hdl: Dict-like handle mapping names to ``ImageView`` / ``PlotWidget`` widgets.
        scale: ``"log"`` or ``"linear"`` for the SAXS-2D background display.
        auto_crop: Crop Q-map to its active bounding box.
        highlight_xy: Pixel coordinates whose q-bin is highlighted on the Q-map.
        cmap: Colour map for all image displays.
        vmin / vmax: Manual colour range (ignored if *autolevel*).
        autolevel: Auto-scale colour levels each call.
        correct_diag: Apply diagonal correction to the C2 matrix.
        selection: Q-bin index for the C2 block.
    """
    assert "Twotime" in xfile.atype, "Not a twotime file"

    # display dqmap and saxs
    dqmap_disp, saxs, selection_xy = xfile.get_twotime_maps(
        scale=scale,
        auto_crop=auto_crop,
        highlight_xy=highlight_xy,
        selection=selection,
    )

    if selection_xy is not None:
        selection = selection_xy

    hdl["saxs"].setImage(np.flipud(saxs))
    hdl["dqmap"].setImage(dqmap_disp)

    c2_result = xfile.get_twotime_c2(selection=selection, correct_diag=correct_diag)
    if c2_result is None:
        return None

    c2, delta_t = c2_result["c2_mat"], c2_result["delta_t"]

    hdl["tt"].imageItem.setScale(delta_t)
    hdl["tt"].setImage(c2, autoRange=True)

    cmap = pg.colormap.getFromMatplotlib(cmap)
    hdl["tt"].setColorMap(cmap)
    hdl["tt"].ui.histogram.setHistogramRange(mn=0, mx=3)
    if not autolevel and vmin is not None and vmax is not None:
        hdl["tt"].setLevels(min=vmin, max=vmax)
    else:
        vmin, vmax = np.percentile(c2, [0.5, 99.5])
        hdl["tt"].setLevels(min=vmin, max=vmax)
    plot_twotime_g2(hdl, c2_result)


def plot_twotime_g2(hdl, c2_result) -> None:
    """Plot full G2 and partial G2 traces inside the C2 plot area.

    Args:
        hdl: Dict-like handle with a ``"c2g2"`` key pointing to a pyqtgraph PlotWidget.
        c2_result: Dict returned by :meth:`~pyxpcsviewer.core.xpcs_file.XpcsFile.get_twotime_c2`.
    """
    g2_full, g2_partial = c2_result["g2_full"], c2_result["g2_partial"]

    hdl["c2g2"].clear()
    hdl["c2g2"].setLabel("left", "g2")
    hdl["c2g2"].setLabel("bottom", "t (s)")
    acquire_period = c2_result["acquire_period"]

    xaxis = np.arange(g2_full.size) * acquire_period
    hdl["c2g2"].plot(
        x=xaxis[1:],
        y=g2_full[1:],
        pen=pg.mkPen(color=PG_COLORS[-1], width=4),
        name="g2_full",
    )
    for n in range(g2_partial.shape[0]):
        xaxis = np.arange(g2_partial.shape[1]) * acquire_period
        hdl["c2g2"].plot(
            x=xaxis[1:],
            y=g2_partial[n][1:],
            pen=pg.mkPen(color=PG_COLORS[n], width=1),
            name=f"g2_partial_{n}",
        )
    hdl["c2g2"].setLogMode(x=True, y=False)
    hdl["c2g2"].autoRange()
