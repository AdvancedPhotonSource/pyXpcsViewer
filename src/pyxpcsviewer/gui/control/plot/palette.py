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
# Marker symbols
# ---------------------------------------------------------------------------

MARKERS_MPL = ("o", "v", "^", ">", "<", "s", "p", "h", "*", "+", "d", "x")

MARKERS_PYG = ("o", "t", "t1", "t2", "t3", "s", "p", "h", "star", "+", "d", "x")


def get_color_marker(n: int, backend: str = "pyqtgraph") -> tuple[str, str]:
    """Return a colour and marker symbol for the n-th data series.

    Args:
        n: Series index (modulo-cycled through the palette).
        backend: ``"matplotlib"`` or ``"pyqtgraph"`` — selects the marker set.

    Returns:
        Tuple of ``(colour_hex, marker_str)``.
    """
    mk = MARKERS_MPL[n % len(MARKERS_MPL)] if backend == "matplotlib" else MARKERS_PYG[n % len(MARKERS_PYG)]
    cl = COLORS_HEX[n % len(COLORS_HEX)]
    return (cl, mk)