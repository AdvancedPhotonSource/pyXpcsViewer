import numpy as np


def fill_center(input, out):
    v, h = input.shape
    out[out.shape[0] // 2 - v // 2: out.shape[0] // 2 - v // 2 + v,
        out.shape[1] // 2 - h // 2: out.shape[1] // 2 - h // 2 + h] = input
    return


def list_to_numpy(ans, autorotate=True):
    v_size = 0
    h_size = 0

    rotate = False
    for n in range(len(ans)):
        if autorotate and ans[n].shape[0] > ans[n].shape[1]:
            ans[n] = ans[n].swapaxes(0, 1)
            rotate = True

    for x in ans:
        v_size = max(v_size, x.shape[0])
        h_size = max(h_size, x.shape[1])
    new_size = (v_size, h_size)

    ret = np.zeros(shape=(len(ans), *new_size), dtype=np.float32)
    for n, x in enumerate(ans):
        if x.shape == ret:
            ret[n] = x
        else:
            fill_center(x, ret[n])

    return ret, rotate


def plot(ans, pg_hdl=None, plot_type='log', cmap='jet', autorotate=False,
         epsilon=None, display=None, extent=None, autorange=True, vmin=None,
         vmax=None):

    ans, rotate = list_to_numpy(ans, autorotate)
    # if pg_hdl is None:
    #     from pyqtgraph_handler import ImageViewDev
    #     pg_hdl = ImageViewDev()

    if plot_type == 'log':
        if epsilon is None or epsilon < 0:
            temp = ans.ravel()
            epsilon = np.min(temp[temp > 0])
        ans = np.log10(ans + epsilon)
    ans = ans.astype(np.float32)

    if rotate and extent is not None:
        extent = (*extent[2:4], *extent[0:2])

    if cmap is not None:
        pg_hdl.set_colormap(cmap)

    pg_hdl.reset_limits()
    if ans.shape[0] > 1:
        xvals = np.arange(ans.shape[0])
        pg_hdl.setImage(ans, xvals=xvals)
    else:
        pg_hdl.setImage(ans[0])
    
    if not autorange:
        if vmin is not None and vmax is not None:
            pg_hdl.setLevels(vmin, vmax)

    pg_hdl.adjust_viewbox()
    if extent is not None:
        pg_hdl.add_readback(display=display, extent=extent)

    return rotate # , pg_hdl.levelMin, pg_hdl.levelMax
