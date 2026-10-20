# Copyright © UChicago Argonne LLC
# See LICENSE file for details
"""core.image_utils: downsampling, log scaling and contrast tables of detector images."""

import numpy as np

from pyxpcsviewer.core.image_utils import (
    block_mean,
    downsample_factor,
    log10_clamped,
    percentile_table,
    subsample,
)


def test_downsample_factor():
    assert downsample_factor((2162, 2068), 1024) == 3
    assert downsample_factor((2162, 2068), 2162) == 1
    assert downsample_factor((100, 50), 0) == 1
    assert downsample_factor((100, 50), None) == 1
    assert downsample_factor((100, 50), 30) == 4


def test_block_mean_averages_blocks_and_drops_the_remainder():
    img = np.arange(5 * 7, dtype=float).reshape(5, 7)
    out = block_mean(img, 2)
    assert out.shape == (2, 3)
    assert out.dtype == np.float32
    assert out[0, 0] == img[:2, :2].mean()
    assert out[1, 2] == img[2:4, 4:6].mean()
    assert block_mean(img, 1) is img


def test_block_mean_ignores_nan():
    img = np.ones((4, 4))
    img[0, 0] = np.nan
    out = block_mean(img, 2)
    assert out[0, 0] == 1.0
    img[:2, :2] = np.nan
    assert np.isnan(block_mean(img, 2)[0, 0])


def test_subsample_aligns_with_block_grid():
    img = np.arange(6 * 6).reshape(6, 6)
    out = subsample(img, 3)
    assert out.shape == (2, 2)
    assert out[1, 1] == img[3, 3]


def test_log10_clamped_floors_non_positive_pixels():
    img = np.array([[10.0, 0.0], [-5.0, 100.0]])
    out = log10_clamped(img)
    assert out.dtype == np.float32
    assert np.allclose(out, [[1.0, 1.0], [1.0, 2.0]])
    assert np.all(log10_clamped(np.zeros((2, 2))) == 0)


def test_percentile_table_is_monotonic_and_ignores_nan():
    rng = np.random.default_rng(0)
    img = rng.normal(size=(50, 50))
    img[0, 0] = np.nan
    table = percentile_table(img)
    assert table.shape == (201,)
    assert np.all(np.diff(table) >= 0)
    assert np.isclose(table[0], np.nanmin(img)) and np.isclose(table[-1], np.nanmax(img))
    assert np.all(percentile_table(np.full((3, 3), np.nan)) == 0)
