# Copyright © UChicago Argonne LLC
# See LICENSE file for details
"""Shared colour palettes and marker symbols for pyqtgraph/matplotlib plots.

All palettes here are the matplotlib ``default`` colour cycle
(https://matplotlib.org/stable/tutorials/colors/colors.html).
"""

# Hex forms — used by matplotlib and by pyqtgraph ``mkPen(color="#...")``
COLORS_HEX = (
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
)

# RGB tuples — used by pyqtgraph ``mkPen(color=(r, g, b))``
COLORS_RGB = (
    (31, 119, 180),
    (255, 127, 14),
    (44, 160, 44),
    (214, 39, 40),
    (148, 103, 189),
    (140, 86, 75),
    (227, 119, 194),
    (127, 127, 127),
    (188, 189, 34),
    (23, 190, 207),
)

# Marker symbols for matplotlib (via :func:`matplot_qt.get_color_marker`)
MARKERS_MPL = ("o", "v", "^", ">", "<", "s", "p", "h", "*", "+", "d", "x")

# Marker symbols for pyqtgraph (via :func:`matplot_qt.get_color_marker`)
MARKERS_PYG = ("o", "t", "t1", "t2", "t3", "s", "p", "h", "star", "+", "d", "x")