# Copyright © UChicago Argonne LLC
# See LICENSE file for details
"""Intensity-vs-time helpers: moving average, subsampling and the Fourier spectrum."""

from __future__ import annotations

import numpy as np


def smooth_intensity(y: np.ndarray, window: int = 1, sampling: int = 1) -> tuple[np.ndarray, np.ndarray]:
    """A moving average over ``window`` frames, then every ``sampling``-th point.

    Args:
        y: Intensity per frame.
        window: Moving-average span in frames; 1 leaves the trace as it is.
        sampling: Keep one point in ``sampling``; 1 keeps every point.

    Returns:
        ``(frame_index, intensity)``; the frame index of a smoothed point is the last frame
        of its window.
    """
    y = np.asarray(y, dtype=np.float64)
    x = np.arange(y.shape[0])
    if window > 1:
        cumulative = np.cumsum(y, dtype=np.float64)
        y = (cumulative[window:] - cumulative[:-window]) / window
        x = x[window:]
    if sampling >= 2:
        y = y[::sampling]
        x = x[::sampling]
    return x, y


def intensity_spectrum(y: np.ndarray, frame_time: float) -> tuple[np.ndarray, np.ndarray]:
    """The magnitude spectrum of an intensity trace (the zero-frequency term set to 0).

    Args:
        y: Intensity per frame.
        frame_time: Seconds between frames.

    Returns:
        ``(frequency_hz, magnitude)`` for the positive frequencies.
    """
    magnitude = np.abs(np.fft.fft(np.asarray(y, dtype=np.float64)))
    freq = np.arange(magnitude.size) / (magnitude.size * frame_time)
    half = magnitude.size // 2
    magnitude = magnitude[:half].copy()
    if magnitude.size:
        magnitude[0] = 0.0
    return freq[:half], magnitude


def block_average(x: np.ndarray, y: np.ndarray, max_points: int) -> tuple[np.ndarray, np.ndarray]:
    """``(x, y)`` reduced to at most ``max_points`` points by averaging consecutive blocks.

    A trace of 100k frames is more than a plot can show; the mean of each block keeps the
    level of the trace (a plain subsample would keep its noise). ``x`` becomes the mean position
    of each block; a last partial block is kept.
    """
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    n = y.shape[0]
    if max_points <= 0 or n <= max_points:
        return x, y
    factor = -(-n // max_points)  # ceil
    count = -(-n // factor)
    sums = np.add.reduceat(y, np.arange(0, n, factor))
    xs = np.add.reduceat(x, np.arange(0, n, factor))
    sizes = np.full(count, factor, dtype=np.float64)
    sizes[-1] = n - factor * (count - 1)
    return xs / sizes, sums / sizes
