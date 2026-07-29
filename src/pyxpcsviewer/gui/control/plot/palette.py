# Copyright © UChicago Argonne LLC
# See LICENSE file for details
"""Shared colour palettes and marker symbols for pyqtgraph/matplotlib plots.

All palettes here are the matplotlib ``default`` colour cycle
(https://matplotlib.org/stable/tutorials/colors/colors.html), unless noted.
"""

# ---------------------------------------------------------------------------
# Matplotlib default colour cycle (10 colours)
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# intt palette — alias, same cycle as the rest of the app
# ---------------------------------------------------------------------------

INTT_COLORS = COLORS_HEX

# ---------------------------------------------------------------------------
# Marker symbols
# ---------------------------------------------------------------------------

MARKERS_MPL = ("o", "v", "^", ">", "<", "s", "p", "h", "*", "+", "d", "x")

MARKERS_PYG = ("o", "t", "t1", "t2", "t3", "s", "p", "h", "star", "+", "d", "x")