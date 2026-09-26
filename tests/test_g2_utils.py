# Copyright © UChicago Argonne LLC
# See LICENSE file for details
"""Tests for pyxpcsviewer.core.g2_utils (compute_g2_debug_bundle, compute_g2 error models).

The bundle is what the G2 outlier debug dialog plots. It must mirror
compute_g2's preprocessing (dead-pixel masking, normalize_g2) and its
outlier pass (find_g2_pixel_outliers) exactly, so the dialog shows what
ReGroup actually sees.

The compute_g2 cases cover the ``error_model`` switch: ``"per-pixel"`` (default,
SEM over the pixels in the dq bin) vs ``"sq-group"`` (SEM over the sq-bin averages).
"""

import numpy as np
import pytest

from pyxpcsviewer.core.g2_utils import (
    DEFAULT_OUTLIER_TARGET,
    OUTLIER_METHODS,
    OUTLIER_TARGETS,
    compute_g2,
    compute_g2_debug_bundle,
    find_g2_pixel_outliers,
    find_g2_smooth_bkg_outliers,
    fit_scattering_scale,
    normalize_g2,
    regroup_G2,
)


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
    assert b["values"].shape == (2, 16)
    assert b["values"].dtype == np.float32
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


def test_bundle_values_are_normalize_g2_for_the_g2_target():
    G2, sqmap, dqmap = make_data()
    b = compute_g2_debug_bundle(sqmap, dqmap, G2, target="g2-per-pixel")
    n_delays, n_channels, _, _ = G2.shape
    expected = normalize_g2(G2.reshape(n_delays, n_channels, -1))
    np.testing.assert_allclose(b["values"], expected)
    assert b["target"] == "g2-per-pixel"


def test_bundle_values_are_the_numerator_for_the_G2_target():
    G2, sqmap, dqmap = make_data()
    b = compute_g2_debug_bundle(sqmap, dqmap, G2, target="G2")
    n_delays, n_channels, _, _ = G2.shape
    np.testing.assert_allclose(b["values"], G2.reshape(n_delays, n_channels, -1)[:, 0])
    assert b["target"] == "G2"


def test_bundle_rejects_unknown_target():
    G2, sqmap, dqmap = make_data()
    with pytest.raises(ValueError, match="target"):
        compute_g2_debug_bundle(sqmap, dqmap, G2, target="IP")


def test_bundle_bad_matches_outlier_pass():
    G2, sqmap, dqmap = make_data()
    b = compute_g2_debug_bundle(sqmap, dqmap, G2, outlier_threshold=3.0, outlier_method="MeanAbsoluteDeviation")
    expected = find_g2_pixel_outliers(b["sqmap_1d"], b["values"], threshold=3.0, method="MeanAbsoluteDeviation")
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


def test_compute_g2_error_model_default_is_per_pixel():
    """The default g2_err is the per-pixel SEM (the pre-outlier-rejection behaviour)."""
    G2, sqmap, dqmap = make_data()
    _, err_default = compute_g2(sqmap, dqmap, G2)
    _, err_pixel = compute_g2(sqmap, dqmap, G2, error_model="per-pixel")
    np.testing.assert_array_equal(err_default, err_pixel)


def test_compute_g2_error_models_match_their_formulas():
    """Both models reproduce their reference formula, and g2 itself is model-independent."""
    G2, sqmap, dqmap = make_data()

    n_delays, n_channels = G2.shape[:2]
    G2_flat = G2.reshape(n_delays, n_channels, -1)
    sqmap_1d = sqmap.ravel().copy()
    dqmap_1d = dqmap.ravel().copy()
    dead = np.all((G2_flat[:, 1] == 0) & (G2_flat[:, 2] == 0), axis=0)
    sqmap_1d[dead] = 0
    dqmap_1d[dead] = 0
    g2_pixel = normalize_g2(G2_flat)

    g2_pix, err_pix = compute_g2(sqmap, dqmap, G2, error_model="per-pixel")
    g2_sqg, err_sqg = compute_g2(sqmap, dqmap, G2, error_model="sq-group")

    # only the error changes with the model
    np.testing.assert_allclose(g2_pix, g2_sqg)

    roi_dq = dqmap_1d == 1
    temp = g2_pixel[:, roi_dq]
    np.testing.assert_allclose(err_pix[:, 0], np.std(temp, axis=1) / np.sqrt(temp.shape[1]))

    # sq-group averages 2 sq bins here, per-pixel averages 15 live pixels
    assert not np.allclose(err_pix, err_sqg)
    assert err_sqg.shape == err_pix.shape


def test_compute_g2_rejects_unknown_error_model():
    G2, sqmap, dqmap = make_data()
    with pytest.raises(ValueError, match="error_model"):
        compute_g2(sqmap, dqmap, G2, error_model="per_pixel")


# --- Outlier target: which per-pixel quantity the rejection statistic runs on.
# make_data() above sets IF == 1 everywhere, so G2[:, 0] == g2_pixel there and it
# cannot tell the two targets apart. make_target_data() is built so they
# disagree on every pixel that matters.


def make_target_data():
    """(1 delay, 3 ch, 4x4) G2 where the two outlier targets disagree.

    One sq bin (all pixels), one dq bin. Baseline pixels cycle IP over
    {0.9, 1.0, 1.1} with IF1=IF2=1, so both G2[:, 0] and g2_pixel have a
    non-degenerate MAD (0.1) -- these expectations do not lean on the
    spread==0 -> 1.0 clamp.

      pixel 5  "hot":  IP=10,  IF=sqrt(10) -> G2=10   (outlier), g2=1.0 (not)
      pixel 10 "corr": IP=1,   IF=0.1      -> G2=1    (not),     g2=100 (outlier)
      pixel 0  "dead": IP=1e6, IF1=IF2=0   -> excluded from every bin
    """
    ip = np.array([0.9, 1.0, 1.1] * 6, dtype=np.float32)[:16].reshape(4, 4)
    IP = ip[None].copy()
    IF = np.ones((1, 4, 4), dtype=np.float32)
    IP[0, 1, 1] = 10.0
    IF[0, 1, 1] = np.sqrt(10.0)  # pixel 5
    IP[0, 2, 2] = 1.0
    IF[0, 2, 2] = 0.1  # pixel 10
    IP[0, 0, 0] = 1.0e6
    IF[0, 0, 0] = 0.0  # pixel 0, dead
    G2 = np.stack([IP, IF, IF], axis=1).astype(np.float32)
    sqmap = np.ones((4, 4), dtype=np.uint16)
    dqmap = np.ones((4, 4), dtype=np.uint16)
    return G2, sqmap, dqmap


def _bad_mask(G2, sqmap, dqmap, **kw):
    """Outlier mask compute_g2 would use, via the debug bundle (same code path)."""
    return compute_g2_debug_bundle(sqmap, dqmap, G2, outlier_threshold=3.0, **kw)["bad"]


def test_target_G2_flags_the_bright_pixel_not_the_correlated_one():
    G2, sqmap, dqmap = make_target_data()
    bad = _bad_mask(G2, sqmap, dqmap, target="G2")
    assert bad[0, 5]  # G2 = 10 in a bin whose median is ~1
    assert not bad[0, 10]  # G2 = 1, unremarkable


def test_target_g2_per_pixel_flags_the_correlated_pixel_not_the_bright_one():
    G2, sqmap, dqmap = make_target_data()
    bad = _bad_mask(G2, sqmap, dqmap, target="g2-per-pixel")
    assert bad[0, 10]  # g2 = 100
    assert not bad[0, 5]  # g2 = 10/10 = 1.0


def test_default_target_is_g2_per_pixel():
    """Default is the normalized statistic. A raw per-delay G2 cut biases g2
    below 1 on real data (see DEFAULT_OUTLIER_TARGET's note), so G2 is opt-in
    and belongs with a min_tag_count persistence filter."""
    G2, sqmap, dqmap = make_target_data()
    np.testing.assert_array_equal(_bad_mask(G2, sqmap, dqmap), _bad_mask(G2, sqmap, dqmap, target="g2-per-pixel"))
    assert DEFAULT_OUTLIER_TARGET == "g2-per-pixel"
    assert OUTLIER_TARGETS[0] == DEFAULT_OUTLIER_TARGET  # GUI combo shows item 0 first


def test_compute_g2_target_changes_the_result():
    """g2 itself differs between targets -- the argument is load-bearing, not cosmetic."""
    G2, sqmap, dqmap = make_target_data()
    g2_G2, _ = compute_g2(sqmap, dqmap, G2, outlier_threshold=3.0, target="G2")
    g2_pix, _ = compute_g2(sqmap, dqmap, G2, outlier_threshold=3.0, target="g2-per-pixel")
    assert not np.allclose(g2_G2, g2_pix)


def test_target_G2_excludes_dead_pixels():
    """Pixel 0 has IF1=IF2=0 (dead) and a huge IP; it must never be flagged,
    and it must not inflate the bin statistics."""
    G2, sqmap, dqmap = make_target_data()
    b = compute_g2_debug_bundle(sqmap, dqmap, G2, outlier_threshold=3.0, target="G2")
    assert b["sqmap_1d"][0] == 0
    assert b["dqmap_1d"][0] == 0
    assert b["n_dead"] == 1
    assert not b["bad"][:, 0].any()


def test_target_G2_statistics_are_per_sq_bin():
    """A numerator of 1000 is normal in a bright bin and an outlier in a dim one.
    Global (non-per-bin) statistics would flag both or neither."""
    sqmap_1d = np.array([1] * 8 + [2] * 8, dtype=np.uint16)
    values = np.concatenate(
        [
            np.array([1.0, 1.1, 0.9, 1.0, 1.1, 0.9, 1.0, 1000.0]),  # bin 1: dim, one spike
            np.array([1000.0, 1100.0, 900.0, 1000.0, 1100.0, 900.0, 1000.0, 1000.0]),  # bin 2: bright
        ]
    )[None]
    bad = find_g2_pixel_outliers(sqmap_1d, values, threshold=3.0)
    assert bad[0, 7]  # 1000 among ~1s
    assert not bad[0, 8:].any()  # the same magnitude is normal in bin 2


def test_outlier_rejection_has_no_lower_bound():
    """Only `> center + threshold*spread` rejects; small values never do."""
    sqmap_1d = np.ones(8, dtype=np.uint16)
    values = np.array([[1.0, 1.1, 0.9, 1.0, 1.1, 0.9, 1.0, 1e-6]])
    assert not find_g2_pixel_outliers(sqmap_1d, values, threshold=3.0).any()


def test_compute_g2_rejects_unknown_target():
    G2, sqmap, dqmap = make_data()
    with pytest.raises(ValueError, match="target"):
        compute_g2(sqmap, dqmap, G2, target="IP")


# --- min_tag_count: reject only pixels whose flag repeats across delays.
# This is what makes target="G2" usable -- a single-delay G2 flag mostly
# tracks the intensity gradient across a q ring, a repeating one is a hot pixel.


def _three_delay_values():
    """One sq bin, 3 delays, 8 pixels.

    pixel 6: outlier at all 3 delays (persistent -- a hot pixel)
    pixel 7: outlier at delay 1 only (transient)
    """
    base = [1.0, 1.1, 0.9, 1.0, 1.1, 0.9]
    values = np.array([[*base, 100.0, 1.0], [*base, 100.0, 100.0], [*base, 100.0, 1.0]])
    return np.ones(8, dtype=np.uint16), values


def test_min_tag_count_zero_keeps_per_delay_flags():
    sqmap_1d, values = _three_delay_values()
    bad = find_g2_pixel_outliers(sqmap_1d, values, threshold=3.0)
    assert bad[:, 6].tolist() == [True, True, True]
    assert bad[:, 7].tolist() == [False, True, False]


def test_min_tag_count_drops_transient_flags_and_spreads_persistent_ones():
    sqmap_1d, values = _three_delay_values()
    bad = find_g2_pixel_outliers(sqmap_1d, values, threshold=3.0, min_tag_count=2)
    assert bad[:, 6].all()  # 3 tags >= 2 -> rejected at every delay
    assert not bad[:, 7].any()  # 1 tag < 2 -> not rejected at all, not even at delay 1
    assert not bad[:, :6].any()


def test_min_tag_count_one_equals_combine_outlier():
    """combine_outlier is the min_tag_count == 1 special case."""
    sqmap_1d, values = _three_delay_values()
    np.testing.assert_array_equal(
        find_g2_pixel_outliers(sqmap_1d, values, threshold=3.0, min_tag_count=1),
        find_g2_pixel_outliers(sqmap_1d, values, threshold=3.0, combine_outlier=True),
    )


def test_min_tag_count_above_delay_count_rejects_nothing():
    sqmap_1d, values = _three_delay_values()
    assert not find_g2_pixel_outliers(sqmap_1d, values, threshold=3.0, min_tag_count=4).any()


def test_min_tag_count_takes_precedence_over_combine_outlier():
    sqmap_1d, values = _three_delay_values()
    bad = find_g2_pixel_outliers(sqmap_1d, values, threshold=3.0, combine_outlier=True, min_tag_count=2)
    assert not bad[:, 7].any()  # combine_outlier alone would have flagged it everywhere


def test_compute_g2_forwards_min_tag_count():
    """A transient flag must not change g2 once a persistence filter is on."""
    G2, sqmap, dqmap = make_target_data()
    g2_persistent, _ = compute_g2(sqmap, dqmap, G2, outlier_threshold=3.0, target="G2", min_tag_count=2)
    g2_none, _ = compute_g2(sqmap, dqmap, G2, outlier_threshold=-1.0)
    # the fixture has a single delay, so nothing can reach 2 tags -> no rejection
    np.testing.assert_allclose(g2_persistent, g2_none)


def test_bundle_forwards_min_tag_count():
    G2, sqmap, dqmap = make_data()
    b = compute_g2_debug_bundle(sqmap, dqmap, G2, outlier_threshold=3.0, min_tag_count=2)
    assert not b["bad"].any()  # each known outlier is flagged at one delay only


# --- G2-smooth-bkg: a third outlier method with no per-bin center/spread --
# it fits one global scale factor against the file's own scattering_1d and
# flat-cuts G2[:, 0] / IPIF_smooth**2 at threshold.


def make_smooth_bkg_data(scale=5.0):
    """(3 delays, 3 ch, 4x4) G2 where IP/IF exactly track scale*scattering_1d per sq bin.

    sq 1 = rows 0-1 (pixels 0-7), sq 2 = rows 2-3 (pixels 8-15); single dq bin.
    g2 (= G2[:,0] / (IP*IF)) is 1.0 everywhere except pixel (0, 0) at delay 0,
    which is a smooth-bkg outlier (g2=100) but NOT a per-bin MAD/StdDev outlier
    (that method flags the correlated pixel too, since it looks the same on
    both counts here -- this fixture isolates the smooth-bkg statistic).
    """
    n_delays = 3
    sqmap = np.zeros((4, 4), dtype=np.uint16)
    sqmap[:2, :] = 1
    sqmap[2:, :] = 2
    scattering_1d = np.array([10.0, 20.0])
    IP = np.zeros((n_delays, 4, 4))
    IF = np.zeros((n_delays, 4, 4))
    for idx, sq_val in enumerate(scattering_1d, start=1):
        mask = sqmap == idx
        IP[:, mask] = scale * sq_val
        IF[:, mask] = scale * sq_val
    g2 = np.ones((n_delays, 4, 4))
    g2[0, 0, 0] = 100.0
    G2 = np.stack([g2 * IP * IF, IP, IF], axis=1)
    dqmap = np.ones((4, 4), dtype=np.uint16)
    return G2, sqmap, dqmap, scattering_1d


def test_fit_scattering_scale_recovers_known_scale():
    G2, sqmap, _, scattering_1d = make_smooth_bkg_data(scale=5.0)
    sqmap_1d = sqmap.ravel()
    scale = fit_scattering_scale(G2, sqmap_1d, scattering_1d)
    assert scale == pytest.approx(5.0)


def test_fit_scattering_scale_excludes_nan_bins():
    """A masked/missing sq bin (NaN in scattering_1d) must not corrupt the fit."""
    G2, sqmap, _, scattering_1d = make_smooth_bkg_data(scale=5.0)
    scattering_1d_with_nan = scattering_1d.copy()
    scattering_1d_with_nan[1] = np.nan
    scale = fit_scattering_scale(G2, sqmap.ravel(), scattering_1d_with_nan)
    assert scale == pytest.approx(5.0)


def test_fit_scattering_scale_rejects_too_short_scattering_1d():
    G2, sqmap, _, scattering_1d = make_smooth_bkg_data()
    with pytest.raises(ValueError, match="scattering_1d"):
        fit_scattering_scale(G2, sqmap.ravel(), scattering_1d[:1])


def test_fit_scattering_scale_rejects_all_nan_scattering_1d():
    G2, sqmap, _, scattering_1d = make_smooth_bkg_data()
    with pytest.raises(ValueError, match="scattering_1d"):
        fit_scattering_scale(G2, sqmap.ravel(), np.full_like(scattering_1d, np.nan))


def test_find_g2_smooth_bkg_outliers_flags_the_bright_pixel():
    G2, sqmap, _, scattering_1d = make_smooth_bkg_data(scale=5.0)
    sqmap_1d = sqmap.ravel()
    scale = fit_scattering_scale(G2, sqmap_1d, scattering_1d)
    bad = find_g2_smooth_bkg_outliers(sqmap_1d, G2[:, 0].reshape(3, -1), scattering_1d, scale, threshold=3.0)
    assert bad[0, 0]  # pixel (0,0), delay 0: g2=100 -> flagged
    assert not bad[1:, 0].any()  # same pixel, other delays: g2=1 -> not flagged
    assert not bad[:, 1:].any()  # no other pixel is ever flagged


def test_find_g2_smooth_bkg_outliers_has_no_lower_bound():
    sqmap_1d = np.ones(4, dtype=np.uint16)
    scattering_1d = np.array([1.0])
    G2_channel0 = np.array([[1e-6, 1.0, 1.0, 1.0]])
    assert not find_g2_smooth_bkg_outliers(sqmap_1d, G2_channel0, scattering_1d, scale=1.0, threshold=3.0).any()


def test_find_g2_smooth_bkg_outliers_excludes_missing_bin_pixels():
    """Pixels whose sq bin has no finite scattering_1d value are never flagged,
    even with an enormous G2_channel0 -- same treatment as photon-starved pixels."""
    sqmap_1d = np.array([1, 2], dtype=np.uint16)
    scattering_1d = np.array([1.0, np.nan])
    G2_channel0 = np.array([[1.0, 1e12]])
    bad = find_g2_smooth_bkg_outliers(sqmap_1d, G2_channel0, scattering_1d, scale=1.0, threshold=3.0)
    assert not bad.any()


def test_find_g2_smooth_bkg_outliers_persistence_filter():
    """min_tag_count composes with the smooth-bkg flat cut exactly as it does
    for the MAD/StdDev methods (shared _apply_persistence_filter helper)."""
    sqmap_1d = np.ones(2, dtype=np.uint16)
    scattering_1d = np.array([1.0])
    G2_channel0 = np.array([[100.0, 1.0], [100.0, 1.0], [1.0, 1.0]])  # pixel 0 flagged at delays 0,1
    bad = find_g2_smooth_bkg_outliers(sqmap_1d, G2_channel0, scattering_1d, scale=1.0, threshold=3.0, min_tag_count=2)
    assert bad[:, 0].all()
    bad_none = find_g2_smooth_bkg_outliers(
        sqmap_1d, G2_channel0, scattering_1d, scale=1.0, threshold=3.0, min_tag_count=3
    )
    assert not bad_none.any()


def test_compute_g2_dispatches_to_smooth_bkg():
    G2, sqmap, dqmap, scattering_1d = make_smooth_bkg_data(scale=5.0)
    g2_smooth, _ = compute_g2(
        sqmap, dqmap, G2, outlier_method="G2-smooth-bkg", outlier_threshold=3.0, scattering_1d=scattering_1d
    )
    g2_none, _ = compute_g2(sqmap, dqmap, G2, outlier_threshold=-1.0)
    # the outlier pixel biases g2 upward when included; excluding it should
    # bring the sq-1 bin's contribution back toward 1.0
    assert g2_smooth[0, 0] < g2_none[0, 0]


def test_compute_g2_smooth_bkg_requires_scattering_1d():
    G2, sqmap, dqmap, _ = make_smooth_bkg_data()
    with pytest.raises(ValueError, match="scattering_1d"):
        compute_g2(sqmap, dqmap, G2, outlier_method="G2-smooth-bkg", outlier_threshold=3.0)


def test_compute_g2_rejects_unknown_outlier_method():
    G2, sqmap, dqmap = make_data()
    with pytest.raises(ValueError, match="outlier_method"):
        compute_g2(sqmap, dqmap, G2, outlier_method="bogus", outlier_threshold=3.0)


def test_outlier_methods_contains_smooth_bkg():
    assert OUTLIER_METHODS == ("MeanAbsoluteDeviation", "StandardDeviation", "G2-smooth-bkg")


def test_bundle_dispatches_to_smooth_bkg():
    G2, sqmap, dqmap, scattering_1d = make_smooth_bkg_data(scale=5.0)
    b = compute_g2_debug_bundle(
        sqmap, dqmap, G2, outlier_method="G2-smooth-bkg", outlier_threshold=3.0, scattering_1d=scattering_1d
    )
    assert b["target"] == "G2-smooth-bkg"
    assert b["scale"] == pytest.approx(5.0)
    assert b["bad"][0, 0]
    assert not b["bad"][1:, 0].any()


def test_bundle_smooth_bkg_requires_scattering_1d():
    G2, sqmap, dqmap, _ = make_smooth_bkg_data()
    with pytest.raises(ValueError, match="scattering_1d"):
        compute_g2_debug_bundle(sqmap, dqmap, G2, outlier_method="G2-smooth-bkg", outlier_threshold=3.0)


def test_bundle_rejects_unknown_outlier_method():
    G2, sqmap, dqmap = make_data()
    with pytest.raises(ValueError, match="outlier_method"):
        compute_g2_debug_bundle(sqmap, dqmap, G2, outlier_method="bogus")


def test_regroup_G2_rejects_smooth_bkg_with_external_qmap(tmp_path):
    """scattering_1d's sq-bin indexing only matches fname's own internal Q-map."""
    import h5py

    fname = tmp_path / "a.h5"
    qmap_fname = tmp_path / "b.h5"
    G2, sqmap, dqmap, _ = make_smooth_bkg_data()
    for path, own_sqmap in ((fname, sqmap), (qmap_fname, sqmap)):
        with h5py.File(path, "w") as f:
            f.create_dataset("/xpcs/qmap/static_roi_map", data=own_sqmap)
            f.create_dataset("/xpcs/qmap/dynamic_roi_map", data=dqmap)

    with pytest.raises(ValueError, match="G2-smooth-bkg"):
        regroup_G2(
            str(fname),
            {"G2": G2},
            qmap_fname=str(qmap_fname),
            outlier_method="G2-smooth-bkg",
            outlier_threshold=3.0,
        )


def test_regroup_G2_allows_smooth_bkg_with_its_own_qmap(tmp_path):
    """qmap_fname == fname (or None, defaulting to fname) is not 'external'."""
    import h5py

    fname = tmp_path / "a.h5"
    G2, sqmap, dqmap, scattering_1d = make_smooth_bkg_data(scale=5.0)
    with h5py.File(fname, "w") as f:
        f.create_dataset("/xpcs/qmap/static_roi_map", data=sqmap)
        f.create_dataset("/xpcs/qmap/dynamic_roi_map", data=dqmap)

    avg_result = regroup_G2(
        str(fname),
        {"G2": G2},
        outlier_method="G2-smooth-bkg",
        outlier_threshold=3.0,
        scattering_1d=scattering_1d,
    )
    assert "g2" in avg_result and "g2_err" in avg_result
