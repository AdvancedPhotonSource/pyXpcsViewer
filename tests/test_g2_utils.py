# Copyright © UChicago Argonne LLC
# See LICENSE file for details
"""Tests for pyxpcsviewer.core.g2_utils.compute_g2_debug_bundle.

The bundle is what the G2 outlier debug dialog plots. It must mirror
compute_g2's preprocessing (dead-pixel masking, normalize_g2) and its
outlier pass (find_g2_pixel_outliers) exactly, so the dialog shows what
ReGroup actually sees.
"""

import numpy as np

from pyxpcsviewer.core.g2_utils import compute_g2_debug_bundle, find_g2_pixel_outliers, normalize_g2


def make_data():
    """(2 delays, 3 ch, 4x4) synthetic G2 with known outliers.

    Flat pixel index = row*4+col:
      0  = (0,0): IF1=IF2=0 at every delay -> dead
      15 = (3,3): g2_pixel=10 at delay 0 only (sq 2)
      8  = (2,0): g2_pixel=10 at delay 1 only (sq 2)
    sq 1 = rows 0-1 (pixels 0-7), sq 2 = rows 2-3 (pixels 8-15); single dq bin.
    """
    IP = np.ones((2, 4, 4), dtype=np.float32)
    IP[0, 3, 3] = 10.0
    IP[1, 2, 0] = 10.0
    IF = np.ones((2, 4, 4), dtype=np.float32)
    IF[:, 0, 0] = 0.0
    G2 = np.stack([IP, IF, IF], axis=1).astype(np.float32)  # (2, 3, 4, 4)
    sqmap = np.zeros((4, 4), dtype=np.uint16)
    sqmap[:2, :] = 1
    sqmap[2:, :] = 2
    dqmap = np.ones((4, 4), dtype=np.uint16)
    return G2, sqmap, dqmap


def test_bundle_shapes():
    G2, sqmap, dqmap = make_data()
    b = compute_g2_debug_bundle(sqmap, dqmap, G2)
    assert b["g2_pixel"].shape == (2, 16)
    assert b["g2_pixel"].dtype == np.float32
    assert b["bad"].shape == (2, 16)
    assert b["bad"].dtype == bool
    assert b["img_shape"] == (4, 4)
    assert b["n_delays"] == 2
    assert b["n_sq"] == 2
    assert b["n_dq"] == 1
    assert b["n_dead"] == 1


def test_bundle_dead_pixel_masked():
    G2, sqmap, dqmap = make_data()
    b = compute_g2_debug_bundle(sqmap, dqmap, G2)
    assert b["sqmap_1d"][0] == 0  # dead pixel removed from its sq bin
    assert b["dqmap_1d"][0] == 0
    assert (b["sqmap_1d"][1:] != 0).all()
    assert sqmap[0, 0] == 1  # input not mutated


def test_bundle_g2_pixel_matches_normalize_g2():
    G2, sqmap, dqmap = make_data()
    b = compute_g2_debug_bundle(sqmap, dqmap, G2)
    n_delays, n_channels, _, _ = G2.shape
    expected = normalize_g2(G2.reshape(n_delays, n_channels, -1))
    np.testing.assert_allclose(b["g2_pixel"], expected)


def test_bundle_bad_matches_outlier_pass():
    G2, sqmap, dqmap = make_data()
    b = compute_g2_debug_bundle(sqmap, dqmap, G2, outlier_threshold=3.0, outlier_method="MeanAbsoluteDeviation")
    expected = find_g2_pixel_outliers(b["sqmap_1d"], b["g2_pixel"], threshold=3.0, method="MeanAbsoluteDeviation")
    np.testing.assert_array_equal(b["bad"], expected)
    assert b["bad"].sum() == 2
    assert b["bad"][0, 15]
    assert b["bad"][1, 8]


def test_bundle_known_outliers():
    G2, sqmap, dqmap = make_data()
    b = compute_g2_debug_bundle(sqmap, dqmap, G2, outlier_threshold=3.0)
    # bin of seven 1s + one 10: median 1, MAD 0 -> clamped to 1, hi = 1+3 = 4
    assert b["bad"][0, 15]
    assert b["bad"][1, 8]
    assert not b["bad"][0, 0]  # dead pixels are out of all sq bins
    b100 = compute_g2_debug_bundle(sqmap, dqmap, G2, outlier_threshold=100.0)
    assert b100["bad"].sum() == 0


def test_bundle_combine_outlier_union():
    G2, sqmap, dqmap = make_data()
    b = compute_g2_debug_bundle(sqmap, dqmap, G2, outlier_threshold=3.0, combine_outlier=True)
    # sq 2 union = {8, 15} -> both flagged at every delay; sq 1 unaffected
    assert b["bad"][0, 8] and b["bad"][0, 15]
    assert b["bad"][1, 8] and b["bad"][1, 15]
    assert b["bad"].sum() == 4


# --- Characterization tests for a planned presort+slice rewrite of
# find_g2_pixel_outliers (currently a per-bin `sqmap == idx` Python loop).
# These pin down existing behavior so the rewrite can be verified against
# them without changing any expected value.


def test_find_outliers_skips_gap_in_bin_numbering():
    """sq bin ids need not be contiguous; an id with zero pixels must not crash."""
    sqmap_1d = np.array([1, 1, 3, 3], dtype=np.uint16)  # id 2 has no pixels
    g2_pixel = np.array([[1.0, 1.0, 1.0, 1.0], [1.0, 1.0, 1.0, 1.0]])
    bad = find_g2_pixel_outliers(sqmap_1d, g2_pixel, threshold=3.0)
    assert bad.shape == (2, 4)
    assert not bad.any()


def test_find_outliers_all_photon_starved_at_one_delay_not_flagged():
    """A bin that is all-zero at one delay only: center/spread clamp to 0/1,
    hi == threshold, and the raw (non-nan) zero values must not exceed it.
    """
    sqmap_1d = np.array([1, 1, 1, 1], dtype=np.uint16)
    g2_pixel = np.array(
        [
            [0.0, 0.0, 0.0, 0.0],  # delay 0: fully photon-starved in this bin
            [1.0, 1.0, 1.0, 10.0],  # delay 1: pixel 3 is a real outlier
        ]
    )
    bad = find_g2_pixel_outliers(sqmap_1d, g2_pixel, threshold=3.0)
    assert not bad[0].any()
    assert bad[1, 3] and not bad[1, :3].any()


def test_find_outliers_threshold_boundary_is_exclusive():
    """hi = median(1) + 3*MAD(0 -> clamped 1) = 4. A pixel exactly at hi
    must NOT be flagged (comparison is strict '>'); one epsilon above it must.
    """
    sqmap_1d = np.array([1] * 7 + [1], dtype=np.uint16)
    g2_pixel = np.array([[1.0] * 7 + [4.0]])
    bad = find_g2_pixel_outliers(sqmap_1d, g2_pixel, threshold=3.0)
    assert not bad.any()

    g2_pixel_above = np.array([[1.0] * 7 + [4.0 + 1e-9]])
    bad_above = find_g2_pixel_outliers(sqmap_1d, g2_pixel_above, threshold=3.0)
    assert bad_above[0, 7]


def test_find_outliers_standard_deviation_method():
    sqmap_1d = np.array([1, 1, 1, 1, 1], dtype=np.uint16)
    g2_pixel = np.array([[1.0, 1.0, 1.0, 1.0, 10.0]])
    bad = find_g2_pixel_outliers(sqmap_1d, g2_pixel, threshold=1.0, method="StandardDeviation")
    assert bad[0, 4]
    assert not bad[0, :4].any()


def _find_g2_pixel_outliers_reference(
    sqmap, g2_pixel, threshold=3.0, method="MeanAbsoluteDeviation", combine_outlier=False
):
    """Frozen copy of the original per-bin loop implementation (pre-rewrite),
    kept only as an independent ground truth for the equivalence test below.
    """
    import warnings

    n_sq = int(np.max(sqmap))
    bad = np.zeros_like(g2_pixel, dtype=bool)

    for idx in range(1, n_sq + 1):
        roi = sqmap == idx
        if not roi.any():
            continue

        g2_roi = g2_pixel[:, roi]
        g2_roi_nan = np.where(g2_roi == 0, np.nan, g2_roi)

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=RuntimeWarning)
            if method == "StandardDeviation":
                center = np.nanmean(g2_roi_nan, axis=1, keepdims=True)
                spread = np.nanstd(g2_roi_nan, axis=1, keepdims=True)
            else:
                center = np.nanmedian(g2_roi_nan, axis=1, keepdims=True)
                spread = np.nanmedian(np.abs(g2_roi_nan - center), axis=1, keepdims=True)

        center = np.nan_to_num(center, nan=0.0)
        spread = np.nan_to_num(spread, nan=1.0)
        spread[spread == 0] = 1.0
        hi = center + threshold * spread

        bad[:, roi] = g2_roi > hi

    if combine_outlier:
        for idx in range(1, int(np.max(sqmap)) + 1):
            roi = sqmap == idx
            if not roi.any():
                continue
            union_bad = bad[:, roi].any(axis=0)
            bad[:, roi] = union_bad

    return bad


def test_find_outliers_matches_reference_on_random_data():
    """Equivalence check for the presort+slice rewrite: random pixels, gappy
    bin ids, zeros (photon-starved), multiple delays -- new implementation
    must match the frozen reference bit-for-bit (both gather values via the
    same left-to-right pixel order, so no floating-point drift is expected).
    """
    rng = np.random.default_rng(12345)
    n_pixels = 4000
    n_delays = 6
    # gappy bin ids: only odd ids 1..199 are used, others are gaps
    sqmap_1d = rng.choice(np.arange(1, 200, 2, dtype=np.uint16), size=n_pixels)
    g2_pixel = rng.exponential(scale=1.0, size=(n_delays, n_pixels))
    # scatter some photon-starved zeros
    zero_mask = rng.random((n_delays, n_pixels)) < 0.05
    g2_pixel[zero_mask] = 0.0

    for combine_outlier in (False, True):
        for method in ("MeanAbsoluteDeviation", "StandardDeviation"):
            expected = _find_g2_pixel_outliers_reference(
                sqmap_1d, g2_pixel, threshold=3.0, method=method, combine_outlier=combine_outlier
            )
            actual = find_g2_pixel_outliers(
                sqmap_1d, g2_pixel, threshold=3.0, method=method, combine_outlier=combine_outlier
            )
            np.testing.assert_array_equal(actual, expected)
