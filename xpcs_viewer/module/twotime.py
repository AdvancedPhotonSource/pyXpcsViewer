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


def plot_twotime_map(xfile,
                     hdl,
                     scale='log',
                     auto_crop=True,
                     highlight_xy=None,
                     highlight_dqbin=None,
                     auto_rotate=True):

    dqmap, saxs = xfile.get_twotime_maps()

    if auto_crop:
        idx = np.nonzero(dqmap >= 1)
        sl_v = slice(np.min(idx[0]), np.max(idx[0]))
        sl_h = slice(np.min(idx[1]), np.max(idx[1]))
        dqmap = dqmap[sl_v, sl_h]
        saxs = saxs[sl_v, sl_h]

    if auto_rotate:
        if dqmap.shape[0] > dqmap.shape[1]:
            dqmap = np.swapaxes(dqmap, 0, 1)
            saxs = np.swapaxes(saxs, 0, 1)

    # emphasize the beamstop region which has qindex = 0;
    qindex_max = np.max(dqmap)
    dqmap = dqmap.astype(np.float32)
    dqmap[dqmap == 0] = np.nan

    if scale == 'log':
        min_val = np.min(saxs[saxs > 0])
        saxs[saxs <= 0] = min_val
        saxs = np.log10(saxs).astype(np.float32)
    hdl['saxs'].setImage(saxs)
    hdl['saxs_colorbar'].setLevels(low=np.min(saxs), high=np.max(saxs))

    dqmap_disp = np.copy(dqmap)
    dq_bin = None
    if highlight_dqbin is not None:
        dq_bin = highlight_dqbin
    elif highlight_xy is not None:
        x, y = highlight_xy
        # dqmap_disp[highlight_xy] = qindex_max + 1
        if (x >= 0 and y >= 0 and x < dqmap.shape[1] and y < dqmap.shape[0]):
            dq_bin = dqmap[y, x]
    if dq_bin is not None and dq_bin != np.nan and dq_bin > 0:
        dqmap_disp[dqmap == dq_bin] = qindex_max + 1
    else:
        dq_bin = None

    hdl['dqmap'].setImage(dqmap_disp)
    hdl['dqmap_colorbar'].setLevels(low=np.nanmin(dqmap), high=qindex_max + 1)
    return dq_bin


def update_twotime_map(meta, hdl):
    dqmap = meta['twotime_dqmap']

    selection = np.zeros_like(dqmap, dtype=np.uint8)
    for n, x in enumerate(meta['twotime_plot_list']):
        if x > 0:
            selection += (dqmap == x).astype(np.uint8) * (n + 1)
    hdl.axes[2].imshow(selection, vmin=0, vmax=2)
    hdl.draw()


def plot_twotime(xfile, hdl, meta, cmap='jet', 
                vmin=None, vmax=None, show_box=False, correct_diag=False,
                layout='1x1'):

    if xfile.type != 'Twotime':
        return None
    c2_result = xfile.get_twotime_c2()
    if c2_result is None:
        return None
    c2, delta_t = c2_result['c2_all'], c2_result['delta_t']

    meta['twotime_ims'] = np.copy(c2)
    # t = meta['twotime_scale'] * np.arange(c2.shape[0])

    if correct_diag:
        c2 = correct_diagonal_c2(c2)

    hdl['tt'].imageItem.setScale(delta_t)
    hdl['tt'].setImage(c2, autoRange=True)
    # hdl['tt'].setImage(c2, autoRange=False)
    # Set x and y limits to match the image dimensions
    # x_max = c2.shape[2] * delta_t
    # y_max = c2.shape[1] * delta_t
    # hdl['tt'].view.setLimits(xMin=0, xMax=x_max, yMin=0, yMax=y_max)
    # hdl['tt'].view.setXRange(0, x_max, padding=0)
    # hdl['tt'].view.setYRange(0, y_max, padding=0)

    cmap = pg.colormap.getFromMatplotlib(cmap)
    hdl['tt'].setColorMap(cmap)
    hdl['tt'].ui.histogram.setHistogramRange(mn=0, mx=3)
    if vmin is not None and vmax is not None:
        hdl['tt'].setLevels(min=vmin, max=vmax)
