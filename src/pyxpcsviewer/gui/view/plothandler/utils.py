# Copyright © UChicago Argonne LLC
# See LICENSE file for details
"""Shared GUI utilities (canvas sizing, etc.)."""

from PySide6.QtCore import QSize


def adjust_canvas_size(widget, num_col: int, num_row: int) -> None:
    """Resize a widget's minimum height to fit a *num_col* x *num_row* plot grid.

    The target aspect ratio is the golden-ratio conjugate (1 / φ ≈ 0.618).

    Args:
        widget: The Qt widget whose minimum size to adjust.
        num_col: Number of columns in the plot grid.
        num_row: Number of rows in the plot grid.
    """
    t = widget.parent().parent().parent()
    aspect = 1 / 1.618 if t is None else t.height() / widget.width()

    min_size = t.height() - 20 if t is not None else widget.height() - 20
    width = widget.width()
    canvas_size = max(min_size, int(width / num_col * aspect * num_row))
    widget.setMinimumSize(QSize(0, canvas_size))
