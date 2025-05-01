def plot(
    xfile,
    pg_hdl=None,
    plot_type="log",
    cmap="jet",
    rotate=False,
    autolevel=False,
    autorange=False,
    vmin=None,
    vmax=None,
):
    center = (xfile.bcx, xfile.bcy)
    if plot_type == "log":
        img = xfile.saxs_2d_log
    else:
        img = xfile.saxs_2d

    if cmap is not None:
        pg_hdl.set_colormap(cmap)

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
