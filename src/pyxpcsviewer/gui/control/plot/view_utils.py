# Copyright © UChicago Argonne LLC
# See LICENSE file for details
"""Small pyqtgraph ``ImageView`` helpers shared across the plot/ modules."""

from collections.abc import Sequence
from typing import Any


def apply_zoom_limit(
    image_view: Any, img_shape: Sequence[int] | None, min_zoom: float = 0.25, scale: float = 1.0
) -> None:
    """Prevent an ``ImageView`` from being zoomed out past a fraction of the image size.

    Without a floor, repeatedly scrolling to zoom out leaves the image a
    barely visible speck, with no way back short of reloading the file.

    Args:
        image_view: Any object exposing pyqtgraph's ``ImageView.getView()``.
        img_shape: The displayed array's ``.shape``; the first two axes are
            treated as ``(height, width)``, matching the row-major image axis
            order used throughout this app.
        min_zoom: Smallest fraction of the image's native extent the view may
            be zoomed out to (e.g. ``0.25`` == 25%).
        scale: Uniform scale factor applied to the image item (e.g. via
            ``ImageItem.setScale()``), so the limit is expressed in the same
            data-coordinate units the ViewBox actually ranges over.
    """
    if img_shape is None or len(img_shape) < 2:
        return
    height, width = img_shape[0] * scale, img_shape[1] * scale
    view = image_view.getView()
    vb = view.vb if hasattr(view, "vb") else view
    vb.setLimits(maxXRange=width / min_zoom, maxYRange=height / min_zoom)
