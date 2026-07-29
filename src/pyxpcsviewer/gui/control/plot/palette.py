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


def _hex_to_rgb(hexcolor: str) -> tuple[int, int, int]:
    """Convert a ``"#rrggbb"`` hex string to an ``(r, g, b)`` tuple."""
    return (int(hexcolor[1:3], 16), int(hexcolor[3:5], 16), int(hexcolor[5:7], 16))


COLORS_RGB = tuple(_hex_to_rgb(c) for c in COLORS_HEX)


# ---------------------------------------------------------------------------
# intt palette — now uses the same default cycle as the rest of the app
# ---------------------------------------------------------------------------

# Alias so intt.py imports remain unchanged
INTT_COLORS = COLORS_HEX

# ---------------------------------------------------------------------------
# Marker symbols
# ---------------------------------------------------------------------------

MARKERS_MPL = ("o", "v", "^", ">", "<", "s", "p", "h", "*", "+", "d", "x")

MARKERS_PYG = ("o", "t", "t1", "t2", "t3", "s", "p", "h", "star", "+", "d", "x")