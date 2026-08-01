# Copyright © UChicago Argonne LLC
# See LICENSE file for details
from .view_utils import apply_zoom_limit


def plot(
    xfile,
    pg_hdl=None,
    plot_type: str = "log",
    cmap: str = "jet",
    rotate: bool = False,
    autolevel: bool = False,
    autorange: bool = False,
    vmin: float | None = None,
    vmax: float | None = None,
) -> bool:
    """Display a SAXS 2D image on a pyqtgraph ``ImageView`` widget.

    Args:
        xfile: An :class:`~pyxpcsviewer.core.xpcs_file.XpcsFile` instance.
        pg_hdl: The ``ImageView`` handler to draw on.
        plot_type: ``"log"`` for logarithmic, anything else for linear intensity.
        cmap: Name of the colour map (e.g. ``"jet"``, ``"viridis"``).
        rotate: Whether a 180° image rotation is needed.
        autolevel: Auto-scale colour levels each call.
        autorange: Reset the view range on first show or dimension change.
        vmin: Manual lower colour level (ignored if *autolevel*).
        vmax: Manual upper colour level (ignored if *autolevel*).

    Returns:
        The original *rotate* flag for caller-side widget rotation.
    """
    center = (xfile.bcx, xfile.bcy)
    img = xfile.saxs_2d_log if plot_type == "log" else xfile.saxs_2d

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
    apply_zoom_limit(pg_hdl, img.shape)

    # Restore view range if we skipped auto-ranging
    if not do_autorange:
        pg_hdl.view.setRange(xRange=view_range[0], yRange=view_range[1], padding=0)

    # Restore levels if needed
    if not autolevel and vmin is not None and vmax is not None:
        pg_hdl.setLevels(vmin, vmax)

    if center is not None:
        pg_hdl.add_roi(sl_type="Center", center=center, label="Center")

    return rotate
