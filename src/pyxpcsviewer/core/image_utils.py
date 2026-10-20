# Copyright © UChicago Argonne LLC
# See LICENSE file for details
"""Pure NumPy helpers for showing detector images: downsampling, log scaling, contrast levels.

Shared by the web viewer (which sends images to a browser) and usable from any front end.
"""

from __future__ import annotations

import numpy as np


def downsample_factor(shape: tuple[int, ...], max_size: int | None) -> int:
    """The integer factor that brings both image axes to at most ``max_size`` pixels (1 = none)."""
    if not max_size or max_size <= 0:
        return 1
    longest = max(int(shape[0]), int(shape[1]))
    return max(1, -(-longest // int(max_size)))  # ceil division


def block_mean(img: np.ndarray, factor: int) -> np.ndarray:
    """Downsample a 2-D image by averaging ``factor`` by ``factor`` blocks.

    Rows and columns past the last full block are dropped, so block ``(i, j)`` covers the
    source pixels ``i*factor .. i*factor+factor-1`` and its center sits at ``i*factor + (factor-1)/2``.
    NaNs are ignored in the mean (a block of only NaNs stays NaN).
    """
    if factor <= 1:
        return np.asarray(img)
    img = np.asarray(img)
    rows = (img.shape[0] // factor) * factor
    cols = (img.shape[1] // factor) * factor
    blocks = img[:rows, :cols].reshape(rows // factor, factor, cols // factor, factor)
    if np.issubdtype(img.dtype, np.floating) and np.isnan(img).any():
        with np.errstate(invalid="ignore"):
            return np.asarray(np.nanmean(blocks.astype(np.float64), axis=(1, 3)), dtype=np.float32)
    return np.asarray(blocks.astype(np.float64).mean(axis=(1, 3)), dtype=np.float32)


def subsample(img: np.ndarray, factor: int) -> np.ndarray:
    """Downsample a label map (q-bin indices, a mask) by keeping every ``factor``-th pixel,
    aligned with :func:`block_mean`'s block grid (the first pixel of each block)."""
    if factor <= 1:
        return np.asarray(img)
    img = np.asarray(img)
    rows = (img.shape[0] // factor) * factor
    cols = (img.shape[1] // factor) * factor
    return img[:rows:factor, :cols:factor]


def log10_clamped(img: np.ndarray) -> np.ndarray:
    """``log10`` of an intensity image with non-positive pixels clamped to the smallest positive
    value (the rule of :attr:`XpcsFile.saxs_2d_log`); an image without positive pixels gives zeros."""
    img = np.asarray(img, dtype=np.float64)
    positive = img > 0
    if not positive.any():
        return np.zeros(img.shape, dtype=np.float32)
    floor = img[positive].min()
    return np.log10(np.where(positive, img, floor)).astype(np.float32)


def percentile_table(img: np.ndarray, count: int = 201) -> np.ndarray:
    """Values at ``count`` evenly spaced percentiles (0 … 100) of the finite pixels, so a contrast
    slider can map percentiles to levels without another pass over the image."""
    values = np.asarray(img, dtype=np.float64).ravel()
    values = values[np.isfinite(values)]
    if values.size == 0:
        return np.zeros(count, dtype=np.float32)
    return np.percentile(values, np.linspace(0.0, 100.0, count)).astype(np.float32)
