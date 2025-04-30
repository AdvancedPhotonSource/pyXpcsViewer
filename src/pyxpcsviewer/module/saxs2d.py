import numpy as np


def fill_center(input, out):
    v, h = input.shape
    out[
        out.shape[0] // 2 - v // 2 : out.shape[0] // 2 - v // 2 + v,
        out.shape[1] // 2 - h // 2 : out.shape[1] // 2 - h // 2 + h,
    ] = input
    return


def list_to_numpy(ans, rotate=True):
    v_size = 0
    h_size = 0

    for n in range(len(ans)):
        if rotate:
            ans[n] = ans[n].swapaxes(0, 1)

    for x in ans:
        v_size = max(v_size, x.shape[0])
        h_size = max(h_size, x.shape[1])
    new_size = (v_size, h_size)

    ret = np.zeros(shape=(len(ans), *new_size), dtype=np.float32)
    for n, x in enumerate(ans):
        if x.shape == ret.shape[1:]:
            ret[n] = x
        else:
            fill_center(x, ret[n])

    return ret, rotate


def plot(
    xf_list,
    pg_hdl=None,
    plot_type="log",
    cmap="jet",
    rotate=False,
    epsilon=None,
    autolevel=False,
    autorange=False,
    vmin=None,
    vmax=None,
):
    center = (xf_list[0].bcx, xf_list[0].bcy)
    saxs_2d_list = [xf.saxs_2d for xf in xf_list]

    ans, rotate = list_to_numpy(saxs_2d_list, rotate)
    if plot_type == "log":
        if epsilon is None or epsilon < 0:
            temp = ans.ravel()
            try:
                epsilon = np.min(temp[temp > 0])
            except Exception as e:
                epsilon = 1
        ans = np.log10(ans + epsilon)
    ans = ans.astype(np.float32)

    if cmap is not None:
        pg_hdl.set_colormap(cmap)

    img = ans[0]
    prev_img = pg_hdl.image
    shape_changed = prev_img is None or prev_img.shape != img.shape
    do_autorange = autorange or shape_changed

    # Save view range if keeping it
    if not do_autorange:
        view_range = pg_hdl.view.viewRange()

    # Set new image
    pg_hdl.setImage(img, autoLevels=autolevel, autoRange=do_autorange)

    # Restore view range if we skipped auto-ranging
    if not do_autorange:
        pg_hdl.view.setRange(xRange=view_range[0], yRange=view_range[1], padding=0)

    # Restore levels if needed
    if not autolevel and vmin is not None and vmax is not None:
        pg_hdl.setLevels(vmin, vmax)

    # Restore intensity levels (if needed)
    if not autolevel:
        if vmin is not None and vmax is not None:
            pg_hdl.setLevels(vmin, vmax)

    if center is not None:
        pg_hdl.add_roi(sl_type="Center", center=center, label="Center")

    return rotate
