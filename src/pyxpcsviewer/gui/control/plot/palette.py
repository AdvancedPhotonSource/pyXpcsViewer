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
# intt palette (16 colours, distinct from the default cycle)
# ---------------------------------------------------------------------------

INTT_COLORS = (
    (192, 0, 0),
    (0, 176, 80),
    (0, 32, 96),
    (255, 0, 0),
    (0, 176, 240),
    (0, 32, 96),
    (255, 164, 0),
    (146, 208, 80),
    (0, 112, 192),
    (112, 48, 160),
    (54, 96, 146),
    (150, 54, 52),
    (118, 147, 60),
    (96, 73, 122),
    (49, 134, 155),
    (226, 107, 10),
)

# ---------------------------------------------------------------------------
# Marker symbols
# ---------------------------------------------------------------------------

MARKERS_MPL = ("o", "v", "^", ">", "<", "s", "p", "h", "*", "+", "d", "x")

MARKERS_PYG = ("o", "t", "t1", "t2", "t3", "s", "p", "h", "star", "+", "d", "x")