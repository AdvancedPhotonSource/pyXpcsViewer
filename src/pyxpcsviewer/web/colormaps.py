# Copyright © UChicago Argonne LLC
# See LICENSE file for details
"""Color maps for the page's images, as Plotly color scales built from matplotlib's maps."""

from __future__ import annotations

from functools import lru_cache

# perceptual, single-direction maps first; jet (a rainbow, familiar at the beamline) last
COLORMAPS: tuple[str, ...] = ("viridis", "inferno", "magma", "plasma", "cividis", "turbo", "hot", "gray", "jet")


@lru_cache(maxsize=1)
def colorscales(stops: int = 32) -> dict[str, list[list[float | str]]]:
    """``{name: [[position, "rgb(r,g,b)"], ...]}`` for every map of :data:`COLORMAPS`."""
    import matplotlib

    scales: dict[str, list[list[float | str]]] = {}
    for name in COLORMAPS:
        cmap = matplotlib.colormaps[name]
        scale: list[list[float | str]] = []
        for i in range(stops):
            pos = i / (stops - 1)
            r, g, b, _ = cmap(pos)
            scale.append([round(pos, 4), f"rgb({round(r * 255)},{round(g * 255)},{round(b * 255)})"])
        scales[name] = scale
    return scales
