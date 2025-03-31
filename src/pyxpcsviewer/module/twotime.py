import numpy as np
import pyqtgraph as pg


def correct_diagonal_c2(c2):
    size = c2.shape[1]
    for n in range(c2.shape[0]):
        side_band = c2[n][(np.arange(size - 1), np.arange(1, size))]
        diag_val = np.zeros(size)
        diag_val[:-1] += side_band
        diag_val[1:] += side_band
        norm = np.ones(size)
        norm[1:-1] = 2
        c2[n, np.diag_indices(size)] = diag_val / norm
    return c2


def plot_twotime_map(
    xfile, hdl, scale="log", auto_crop=True, highlight_xy=None, highlight_dqbin=None
):

    dqmap, saxs = xfile.get_twotime_maps()

    if auto_crop:
        idx = np.nonzero(dqmap >= 1)
        sl_v = slice(np.min(idx[0]), np.max(idx[0]))
        sl_h = slice(np.min(idx[1]), np.max(idx[1]))
        dqmap = dqmap[sl_v, sl_h]
        saxs = saxs[sl_v, sl_h]

    # emphasize the beamstop region which has qindex = 0;
    qindex_max = np.max(dqmap)
    dqmap = dqmap.astype(np.float32)
    dqmap[dqmap == 0] = np.nan

    if scale == "log":
        min_val = np.min(saxs[saxs > 0])
        saxs[saxs <= 0] = min_val
        saxs = np.log10(saxs).astype(np.float32)
    hdl["saxs"].setImage(np.flipud(saxs))
    hdl["saxs_colorbar"].setLevels(low=np.min(saxs), high=np.max(saxs))

    dqmap_disp = np.flipud(np.copy(dqmap))
    dq_bin = None
    if highlight_dqbin is not None:
        dq_bin = highlight_dqbin
    elif highlight_xy is not None:
        x, y = highlight_xy
        # dqmap_disp[highlight_xy] = qindex_max + 1
        if x >= 0 and y >= 0 and x < dqmap.shape[1] and y < dqmap.shape[0]:
            dq_bin = dqmap_disp[y, x]
    if dq_bin is not None and dq_bin != np.nan and dq_bin > 0:
        dqmap_disp[dqmap_disp == dq_bin] = qindex_max + 1
    else:
        dq_bin = None
    hdl["dqmap"].setImage(dqmap_disp)
    hdl["dqmap_colorbar"].setLevels(low=np.nanmin(dqmap), high=qindex_max + 1)
    plot_twotime_g2(xfile, hdl, dq_bin)
    return dq_bin


def plot_twotime_correlation(
    xfile, hdl, cmap="jet", vmin=None, vmax=None, correct_diag=False, dq_bin=1
):
    assert "Twotime" in xfile.atype, "Not a twotime file"
    c2_result = xfile.get_twotime_c2()
    if c2_result is None:
        return None
    c2, delta_t = c2_result["c2_all"], c2_result["delta_t"]

    if correct_diag:
        c2 = correct_diagonal_c2(c2)

    hdl["tt"].imageItem.setScale(delta_t)
    hdl["tt"].setImage(c2, autoRange=True)

    cmap = pg.colormap.getFromMatplotlib(cmap)
    hdl["tt"].setColorMap(cmap)
    hdl["tt"].ui.histogram.setHistogramRange(mn=0, mx=3)
    if vmin is not None and vmax is not None:
        hdl["tt"].setLevels(min=vmin, max=vmax)
    plot_twotime_g2(xfile, hdl, dq_bin=dq_bin)


def plot_twotime_g2(xfile, hdl, dq_bin=0):
    if dq_bin is None or dq_bin <= 0:
        return
    plot_idx = int(dq_bin) - 1

    if "Twotime" not in xfile.atype:
        return None

    c2_result = xfile.get_twotime_c2()
    if c2_result is None:
        return None

    g2_full, g2_partial = c2_result["g2_full"], c2_result["g2_partial"]
    plot_idx = min(plot_idx, g2_full.shape[0] - 1)

    hdl["c2g2"].clear()
    hdl["c2g2"].setLabel("left", "g2")
    hdl["c2g2"].setLabel("bottom", "t (s)")
    hdl["c2g2"].setTitle(f"qbin={plot_idx + 1}")
    acquire_period = c2_result["acquire_period"]

    colors = [
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

    xaxis = np.arange(g2_full.shape[1]) * acquire_period
    hdl["c2g2"].plot(
        x=xaxis[1:],
        y=g2_full[plot_idx][1:],
        pen=pg.mkPen(color=colors[-1], width=4),
        name="g2_full",
    )
    for n in range(g2_partial.shape[1]):
        xaxis = np.arange(g2_partial.shape[2]) * acquire_period
        hdl["c2g2"].plot(
            x=xaxis[1:],
            y=g2_partial[plot_idx][n][1:],
            pen=pg.mkPen(color=colors[n], width=1),
            name=f"g2_partial_{n}",
        )
    hdl["c2g2"].setLogMode(x=True, y=False)
    hdl["c2g2"].autoRange()
    # hdl['c2g2'].addLegend()
