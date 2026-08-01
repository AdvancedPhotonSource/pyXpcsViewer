# Copyright © UChicago Argonne LLC
# See LICENSE file for details
"""Tests for pyxpcsviewer.core.fitting.

Focus: fit_g2_batch's flattened (file, bin-chunk) ProcessPoolExecutor
parallelism must be numerically identical to the serial build_g2_fit_summary
path, since each q-bin's curve_fit call is independent -- chunking is a
scheduling change only.
"""

import numpy as np
import pytest

from pyxpcsviewer.core import fitting as fitting_module
from pyxpcsviewer.core.fitting import (
    _MIN_CHUNK_SIZE,
    _resolve_fit_params,
    build_g2_fit_summary,
    create_fit_pool,
    fit_g2_batch,
    fit_with_fixed,
)

BOUNDS_SINGLE = ([0.0, 1e-6, 0.5, 0.9], [1.0, 1.0, 1.5, 1.1])

_REAL_FIT_WITH_FIXED = fitting_module.fit_with_fixed


def _add_one(x):
    """Trivial picklable task for confirming an externally-owned pool is still usable."""
    return x + 1


def _raise_for_sentinel_sigma(base_func, x, y, sigma, bounds, fit_flag, fit_x, p0):
    """Stand-in for fit_with_fixed that raises for chunks marked via a sentinel sigma value.

    Module-level (not a closure) so it pickles cleanly for ProcessPoolExecutor.
    Delegates to the real fit_with_fixed (captured before any patching) for
    everything else, so unmarked files/chunks behave exactly as normal.
    """
    if np.all(sigma > 50):
        raise RuntimeError("synthetic worker failure")
    return _REAL_FIT_WITH_FIXED(base_func, x, y, sigma, bounds, fit_flag, fit_x, p0)


def _make_synthetic_file(n_bins, n_time=60, seed=0, sigma_value=0.01):
    """Build a (q_val, t_el, g2, sigma, label) tuple matching XpcsFile.get_g2_data()'s shape."""
    rng = np.random.default_rng(seed)
    t_el = np.logspace(-6, 1, n_time)
    q_val = np.linspace(0.001, 0.05, n_bins)
    label = [f"q{j}" for j in range(n_bins)]

    tau_true = 10 ** rng.uniform(-4, -1, n_bins)
    cts_true = rng.uniform(0.2, 0.4, n_bins)
    g2 = np.empty((n_time, n_bins))
    for j in range(n_bins):
        g2[:, j] = cts_true[j] * np.exp(-2 * (t_el / tau_true[j])) + 1.0
    g2 += rng.normal(scale=0.002, size=g2.shape)
    sigma = np.full_like(g2, sigma_value)
    return q_val, t_el, g2, sigma, label


def test_resolve_fit_params_rejects_bad_bounds_shape():
    with pytest.raises(AssertionError):
        _resolve_fit_params(([0, 0, 0], [1, 1, 1]), None, "single")


def test_build_g2_fit_summary_dict_shape():
    file_input = _make_synthetic_file(n_bins=8)
    summary = build_g2_fit_summary(*file_input, BOUNDS_SINGLE)
    assert set(summary) == {
        "fit_func",
        "fit_val",
        "t_el",
        "q_val",
        "q_range",
        "t_range",
        "bounds",
        "fit_flag",
        "fit_line",
        "label",
    }
    assert summary["fit_val"].shape == (8, 2, 4)
    assert len(summary["fit_line"]) == 8


def test_build_g2_fit_summary_recovers_known_params():
    file_input = _make_synthetic_file(n_bins=5)
    summary = build_g2_fit_summary(*file_input, BOUNDS_SINGLE)
    assert all(fl["success"] for fl in summary["fit_line"])
    # baseline (param index 3) should recover close to the synthetic truth of 1.0
    assert np.allclose(summary["fit_val"][:, 0, 3], 1.0, atol=0.02)


@pytest.mark.parametrize(
    "n_bins",
    sorted({1, _MIN_CHUNK_SIZE - 1, _MIN_CHUNK_SIZE, _MIN_CHUNK_SIZE + 1, 2 * _MIN_CHUNK_SIZE, 500}),
)
def test_fit_g2_batch_matches_serial_single_file(n_bins):
    file_input = _make_synthetic_file(n_bins=n_bins)
    serial = build_g2_fit_summary(*file_input, BOUNDS_SINGLE)
    (batch,) = fit_g2_batch([file_input], BOUNDS_SINGLE, max_workers=2)

    assert batch is not None
    np.testing.assert_array_equal(batch["fit_val"], serial["fit_val"])
    assert batch["fit_func"] == serial["fit_func"]
    assert batch["fit_flag"] == serial["fit_flag"]
    for a, b in zip(batch["fit_line"], serial["fit_line"], strict=True):
        assert a["success"] == b["success"]
        np.testing.assert_array_equal(a["fit_x"], b["fit_x"])
        if b["fit_y"] is None:
            assert a["fit_y"] is None
        else:
            np.testing.assert_array_equal(a["fit_y"], b["fit_y"])


def test_fit_g2_batch_zero_bin_file():
    q_val, t_el, g2, sigma, label = _make_synthetic_file(n_bins=5)
    file_input = (q_val[:0], t_el, g2[:, :0], sigma[:, :0], label[:0])

    (result,) = fit_g2_batch([file_input], BOUNDS_SINGLE, max_workers=2)

    assert result is not None
    assert result["fit_val"].shape == (0, 2, 4)
    assert result["fit_line"] == []


def test_fit_g2_batch_multi_file_mixed_sizes_matches_serial():
    inputs = [_make_synthetic_file(n_bins=n, seed=n) for n in (3, 20, 500)]
    serials = [build_g2_fit_summary(*fi, BOUNDS_SINGLE) for fi in inputs]

    batch_results = fit_g2_batch(inputs, BOUNDS_SINGLE, max_workers=4)

    assert len(batch_results) == 3
    for batch, serial in zip(batch_results, serials, strict=True):
        assert batch is not None
        np.testing.assert_array_equal(batch["fit_val"], serial["fit_val"])


def test_fit_g2_batch_per_bin_failure_isolated():
    q_val, t_el, g2, sigma, label = _make_synthetic_file(n_bins=5)
    g2[:, 2] = np.nan  # curve_fit's finite-check raises for this bin only
    file_input = (q_val, t_el, g2, sigma, label)

    (result,) = fit_g2_batch([file_input], BOUNDS_SINGLE, max_workers=2)

    assert result is not None
    assert result["fit_line"][2]["success"] is False
    assert np.all(result["fit_val"][2, 1, :] == -1)
    for n in (0, 1, 3, 4):
        assert result["fit_line"][n]["success"] is True


def test_fit_g2_batch_whole_file_failure_nulls_file_but_not_siblings(monkeypatch):
    # fit_with_fixed's own per-bin try/except is robust enough that ordinary bad data
    # (NaN, sigma=0, ...) fails individual bins gracefully rather than raising out of
    # the whole (file, chunk) task -- see test_fit_g2_batch_per_bin_failure_isolated.
    # To exercise fit_g2_batch's own except-per-chunk/null-the-file path, patch
    # fit_with_fixed itself to raise for a sentinel-marked file's chunks.
    monkeypatch.setattr(fitting_module, "fit_with_fixed", _raise_for_sentinel_sigma)

    good_input = _make_synthetic_file(n_bins=20, seed=1)
    bad_input = _make_synthetic_file(n_bins=20, seed=2, sigma_value=100.0)  # sentinel

    results = fit_g2_batch([good_input, bad_input], BOUNDS_SINGLE, max_workers=2)

    assert results[0] is not None
    assert results[1] is None


def test_fit_g2_batch_progress_callback_counts_chunks_not_files():
    file_input = _make_synthetic_file(n_bins=500)
    calls = []

    fit_g2_batch(
        [file_input],
        BOUNDS_SINGLE,
        max_workers=4,
        progress_callback=lambda done, total: calls.append((done, total)),
    )

    assert calls
    done, total = calls[-1]
    assert done == total
    assert total > 1  # a single 500-bin file must split into more than one chunk


def test_fit_g2_batch_empty_file_list():
    assert fit_g2_batch([], BOUNDS_SINGLE) == []


def test_create_fit_pool_returns_usable_executor():
    pool = create_fit_pool()
    try:
        _q_val, t_el, g2, sigma, _label = _make_synthetic_file(n_bins=5)
        fit_x = np.logspace(np.log10(np.min(t_el)) - 0.5, np.log10(np.max(t_el)) + 0.5, 128)
        fit_flag = [True, True, True, True]
        p0 = np.mean(BOUNDS_SINGLE, axis=0)
        p0[1] = np.sqrt(BOUNDS_SINGLE[0][1] * BOUNDS_SINGLE[1][1])

        future = pool.submit(
            fit_with_fixed, fitting_module.single_exp_all, t_el, g2, sigma, BOUNDS_SINGLE, fit_flag, fit_x, p0
        )
        fit_line, fit_val = future.result()

        assert fit_val.shape == (5, 2, 4)
        assert all(fl["success"] for fl in fit_line)
    finally:
        pool.shutdown()


def test_fit_g2_batch_with_external_executor_matches_default():
    file_input = _make_synthetic_file(n_bins=50)
    default_result = fit_g2_batch([file_input], BOUNDS_SINGLE, max_workers=2)[0]

    pool = create_fit_pool()
    try:
        (external_result,) = fit_g2_batch([file_input], BOUNDS_SINGLE, executor=pool)
        assert external_result is not None
        np.testing.assert_array_equal(external_result["fit_val"], default_result["fit_val"])

        # fit_g2_batch must not have shut down a pool it doesn't own -- confirm
        # the same pool still runs a plain task afterward.
        assert pool.submit(_add_one, 1).result() == 2
    finally:
        pool.shutdown()
