# Copyright © UChicago Argonne LLC
# See LICENSE file for details
import warnings
from typing import Any

import h5py
import numpy as np

keymap = {
    "g2": "/xpcs/multitau/normalized_g2",
    "g2_err": "/xpcs/multitau/normalized_g2_err",
    "G2": "/xpcs/multitau/unnormalized_G2",
    "saxs2d": "/xpcs/temporal_mean/scattering_2d",
    "saxs1d": "/xpcs/temporal_mean/scattering_1d",
    "saxs1d_segments": "/xpcs/temporal_mean/scattering_1d_segments",
    "sqmap": "/xpcs/qmap/static_roi_map",
    "dqmap": "/xpcs/qmap/dynamic_roi_map",
}


def has_G2_field(fname):
    """Check if the G2 field exists in the specified HDF5 file.

    Args:
        fname: Path to the HDF5 file.

    Returns:
        ``True`` if the G2 field exists, ``False`` otherwise.
    """
    with h5py.File(fname, "r", libver="latest") as f:
        return keymap["G2"] in f


def normalize_g2(G2_3ch):
    """Normalize a 3-channel G2 array by dividing channel 0 by the product of channels 1 and 2.

    The three channels are ``(IP, IF, IF)``.  Products that are zero or negative
    are clamped to ``1.0`` to avoid division-by-zero and sign flips.

    Args:
        G2_3ch: Array of shape ``(n_delays, 3, n_something)``.

    Returns:
        Normalized g2 of shape ``(n_delays, n_something)``.
    """
    ip_if = G2_3ch[:, 1] * G2_3ch[:, 2]
    ip_if[ip_if <= 0] = 1.0
    return G2_3ch[:, 0] / ip_if


def average_by_qindex(idx_map, arr):
    """Calculate the average of an array based on a Q-index map.

    Args:
        idx_map: An index map where each value represents a Q-index.
        arr: A 2D array of values to be averaged. The second dimension size
            must match the size of the flattened index map.

    Returns:
        A 2D array containing the averaged values for each Q-index.
    """
    size = np.max(idx_map) + 1
    idx_map = idx_map.ravel()
    assert idx_map.size == arr.shape[1], "Index map size must match array columns"
    assert arr.ndim == 2, "Array must be 2D"
    count = np.bincount(idx_map, minlength=size)[1:]
    count = np.clip(count, a_min=1, a_max=None)

    result = []
    for n in range(arr.shape[0]):
        value = np.bincount(idx_map, weights=arr[n], minlength=size)[1:]
        avg_value = value / count
        result.append(avg_value)

    return np.array(result)


def find_g2_pixel_outliers(sqmap, g2_pixel, threshold=3.0, method="MeanAbsoluteDeviation", combine_outlier=False):
    """Flag per-pixel, per-delay g2 outliers within each sqmap bin.

    Detection is independent for each ``(sq bin, delay)`` pair: pixels with
    ``g2_pixel == 0`` (photon-starved, not bad) are excluded from both the
    center/spread statistics and the rejection test, and only an upper bound
    is applied (``center + threshold * spread``) — there is no lower bound.

    When *combine_outlier* is ``False`` (default), a pixel flagged at one delay
    is not flagged at any other delay.  When *combine_outlier* is ``True``, the
    union of outlier pixels across **all** delays is taken for each sq bin so
    that a pixel found bad at *any* delay is excluded from *every* delay.

    Args:
        sqmap: Static ROI map, raveled, shape ``(n_pixels,)``.
        g2_pixel: Normalised per-pixel g2, shape ``(n_delays, n_pixels)``.
        threshold: Number of MADs (or standard deviations) above center for rejection.
        method: ``"MeanAbsoluteDeviation"`` or ``"StandardDeviation"``.
        combine_outlier: If ``True``, union outliers across all delays per sq bin
            so each flagged pixel is excluded at every delay.

    Returns:
        Boolean mask, shape ``(n_delays, n_pixels)``, ``True`` where the pixel
        is flagged as an outlier.
    """
    n_sq = int(np.max(sqmap))
    bad = np.zeros_like(g2_pixel, dtype=bool)

    for idx in range(1, n_sq + 1):
        roi = sqmap == idx
        if not roi.any():
            continue

        g2_roi = g2_pixel[:, roi]  # (n_delays, n_pixels_in_roi)
        g2_roi_nan = np.where(g2_roi == 0, np.nan, g2_roi)

        with warnings.catch_warnings():
            # a delay with zero nonzero pixels in this bin produces an all-NaN row,
            # which is a legitimate case handled below via nan_to_num, not an error
            warnings.simplefilter("ignore", category=RuntimeWarning)
            if method == "StandardDeviation":
                center = np.nanmean(g2_roi_nan, axis=1, keepdims=True)
                spread = np.nanstd(g2_roi_nan, axis=1, keepdims=True)
            else:  # default: MeanAbsoluteDeviation
                center = np.nanmedian(g2_roi_nan, axis=1, keepdims=True)
                spread = np.nanmedian(np.abs(g2_roi_nan - center), axis=1, keepdims=True)

        center = np.nan_to_num(center, nan=0.0)
        spread = np.nan_to_num(spread, nan=1.0)
        spread[spread == 0] = 1.0
        hi = center + threshold * spread

        bad[:, roi] = g2_roi > hi

    if combine_outlier:
        # Union across all delays per sq bin: a pixel bad at any delay is bad at all delays.
        for idx in range(1, int(np.max(sqmap)) + 1):
            roi = sqmap == idx
            if not roi.any():
                continue
            union_bad = bad[:, roi].any(axis=0)  # (n_pixels_in_roi,)
            bad[:, roi] = union_bad  # broadcast to all delays

    return bad


def compute_g2(sqmap, dqmap, G2, outlier_method="MeanAbsoluteDeviation", outlier_threshold=-1.0, combine_outlier=False):
    """Compute g2 and its error using static and dynamic ROI maps.

    Args:
        sqmap: The static ROI map.
        dqmap: The dynamic ROI map.
        G2: The unnormalized G2 data with shape ``(n_delays, n_channels, img_v, img_h)``.
        outlier_method: ``"MeanAbsoluteDeviation"`` or ``"StandardDeviation"``, consulted
            only when ``outlier_threshold >= 0``.
        outlier_threshold: Reject pixels with ``g2_pixel`` above ``center + threshold * spread``
            within their sq bin, evaluated independently per delay (see
            :func:`find_g2_pixel_outliers`). Negative (default) disables rejection entirely.
        combine_outlier: If ``True``, union the outlier masks across all delays for each sq bin
            so that a pixel flagged as an outlier at *any* delay is excluded from *all* delays.
            Only consulted when ``outlier_threshold >= 0``. Default ``False``.

    Returns:
        Tuple of ``(g2, g2_err)`` where *g2* is the normalized g2 values with shape
        ``(n_delays, n_dq)`` and *g2_err* is the standard error of the mean of *g2_sq*
        across the sq bins making up each dq bin.
    """
    # G2 is (N_delay x 3 x IMG_V x IMG_H)
    shape = G2.shape  #
    n_delays, n_channels, _, _ = shape
    G2 = G2.reshape(n_delays, n_channels, -1)
    sqmap_1d = sqmap.ravel().copy()
    dqmap_1d = dqmap.ravel().copy()

    # exclude pixels with zero signal in both IF channels at every delay (true dead pixels)
    dead = np.all((G2[:, 1] == 0) & (G2[:, 2] == 0), axis=0)
    sqmap_1d[dead] = 0
    dqmap_1d[dead] = 0

    g2_pixel = normalize_g2(G2)

    bad = None
    if outlier_threshold >= 0:
        bad = find_g2_pixel_outliers(
            sqmap_1d, g2_pixel, threshold=outlier_threshold, method=outlier_method, combine_outlier=combine_outlier
        )

    n_dq = int(np.max(dqmap_1d))
    # average by sqmap to get G2_sq;
    n_sq = int(np.max(sqmap_1d))
    G2_flat = G2.reshape(n_delays * n_channels, -1)
    if bad is None:
        G2_sq = average_by_qindex(sqmap_1d, G2_flat)
        G2_sq = G2_sq.reshape(n_delays, n_channels, n_sq)
    else:
        # Apply the bad mask delay-by-delay.  When combine_outlier=False, bad[d] is independent
        # per delay (default).  When combine_outlier=True, bad[d] is the union across all delays
        # for each sq bin — computed upstream in find_g2_pixel_outliers — so a pixel excluded
        # at any delay is excluded at every delay.  Either way the mask is never written back
        # into sqmap_1d/dqmap_1d (those arrays stay intact for the g2_err computation below).
        G2_sq = np.empty((n_delays, n_channels, n_sq))
        for d in range(n_delays):
            sqmap_d = sqmap_1d.copy()
            sqmap_d[bad[d]] = 0
            G2_sq[d] = average_by_qindex(sqmap_d, G2[d])

    g2_sq = normalize_g2(G2_sq)

    g2 = np.zeros((n_delays, n_dq))
    g2_err = np.zeros_like(g2)

    for idx in range(1, n_dq + 1):
        roi_dq = dqmap_1d == idx
        temp = g2_pixel[:, roi_dq]

        if temp.shape[1] > 0:
            roi_sq = np.unique(sqmap_1d[roi_dq]) - 1
            g2[:, idx - 1] = np.mean(g2_sq[:, roi_sq], axis=1)
            g2_err[:, idx - 1] = np.std(g2_sq[:, roi_sq], axis=1) / np.sqrt(len(roi_sq))

    return g2, g2_err


def save_G2_to_file(fname, avg_result):
    """Update an HDF5 file with averaged G2 results.

    Writes the averaged G2, g2, and g2_err data to the specified HDF5 file.
    If the datasets already exist, they are deleted and recreated.

    Args:
        fname: Path to the HDF5 file to be updated.
        avg_result: Dictionary containing the averaged results. Keys should match
            those in the keymap (e.g., ``'G2'``, ``'g2'``, ``'g2_err'``), and
            values are numpy arrays containing the data to be written.
    """
    with h5py.File(fname, "a") as f:
        for key, data in avg_result.items():
            field = keymap[key]
            if field in f:
                del f[field]
            compression = "lzf" if key == "G2" else None
            f.create_dataset(field, data=data, compression=compression)


def regroup_G2_with_qmap_array(
    avg_result, sqmap, dqmap, outlier_method="MeanAbsoluteDeviation", outlier_threshold=-1.0, combine_outlier=False
):
    """Compute g2 and g2_err from G2 data using Q-maps and add them to results.

    Takes the unnormalized G2 data from avg_result and computes the normalized g2
    and its error using the provided static and dynamic Q-maps. The computed g2
    and g2_err are added to the avg_result dictionary.

    Args:
        avg_result: Dictionary containing at least the ``'G2'`` key with
            unnormalized G2 data. Modified in-place to include ``'g2'`` and
            ``'g2_err'``.
        sqmap: The static ROI map used for averaging.
        dqmap: The dynamic ROI map used for grouping.
        outlier_method: ``"MeanAbsoluteDeviation"`` or ``"StandardDeviation"``, consulted
            only when ``outlier_threshold >= 0``.
        outlier_threshold: Per-delay, per-sq-bin upper-bound outlier rejection threshold
            (see :func:`find_g2_pixel_outliers`). Negative (default) disables rejection.
        combine_outlier: If ``True``, union outlier masks across all delays per sq bin
            before exclusion. Only consulted when ``outlier_threshold >= 0``. Default ``False``.

    Returns:
        The updated avg_result dictionary with ``'g2'`` and ``'g2_err'`` added.
    """
    g2, g2_err = compute_g2(
        sqmap,
        dqmap,
        avg_result["G2"],
        outlier_method=outlier_method,
        outlier_threshold=outlier_threshold,
        combine_outlier=combine_outlier,
    )
    avg_result["g2"] = g2
    avg_result["g2_err"] = g2_err
    return avg_result


def regroup_G2(
    fname,
    avg_result,
    qmap_fname=None,
    outlier_method="MeanAbsoluteDeviation",
    outlier_threshold=-1.0,
    combine_outlier=False,
):
    """Regroup G2 data using Q-maps and update the HDF5 file with all results.

    Reads the static and dynamic Q-maps from an HDF5 file, computes g2 and g2_err
    from the G2 data in avg_result, and adds them to the avg_result dictionary.

    Args:
        fname: Path to the HDF5 file to be updated with the results.
        avg_result: Dictionary containing at least the ``'G2'`` key with
            unnormalized G2 data. May also contain other keys like
            ``'saxs2d'``, ``'saxs1d'``, etc.
        qmap_fname: Path to the HDF5 file containing the Q-maps (sqmap and dqmap).
            If ``None``, the Q-maps are read from the same file as *fname*.
        outlier_method: ``"MeanAbsoluteDeviation"`` or ``"StandardDeviation"``, consulted
            only when ``outlier_threshold >= 0``.
        outlier_threshold: Per-delay, per-sq-bin upper-bound outlier rejection threshold
            (see :func:`find_g2_pixel_outliers`). Negative (default) disables rejection.
        combine_outlier: If ``True``, union outlier masks across all delays per sq bin
            before exclusion. Only consulted when ``outlier_threshold >= 0``. Default ``False``.

    Returns:
        The updated avg_result dictionary with ``'g2'`` and ``'g2_err'`` added.
    """
    qmap_fname = qmap_fname or fname

    def _load_qmap(f, qmap_key):
        """Try to load Q-map with or without /xpcs/ prefix."""
        path = keymap[qmap_key]
        if path in f:
            return f[path][()]

        # Try without /xpcs/ prefix for raw qmap files
        alt_path = path.replace("/xpcs/", "")
        if alt_path in f:
            return f[alt_path][()]

        return None

    with h5py.File(qmap_fname, "r") as f:
        dqmap = _load_qmap(f, "dqmap")
        sqmap = _load_qmap(f, "sqmap")

        if dqmap is None or sqmap is None:
            raise ValueError("Q-maps not found in the HDF5 file.")

    return regroup_G2_with_qmap_array(
        avg_result,
        sqmap,
        dqmap,
        outlier_method=outlier_method,
        outlier_threshold=outlier_threshold,
        combine_outlier=combine_outlier,
    )


def compute_g2_debug_bundle(
    sqmap: np.ndarray,
    dqmap: np.ndarray,
    G2: np.ndarray,
    outlier_method: str = "MeanAbsoluteDeviation",
    outlier_threshold: float = 3.0,
    combine_outlier: bool = False,
) -> dict[str, Any]:
    """Compute the per-pixel data the G2 outlier debug dialog plots.

    Mirrors :func:`compute_g2` preprocessing exactly (dead-pixel masking,
    normalize) and runs the same outlier pass, so the dialog visualizes what
    ReGroup actually sees. Pure numpy, no file IO.

    Args:
        sqmap: Static ROI map, shape ``(img_v, img_h)``.
        dqmap: Dynamic ROI map, shape ``(img_v, img_h)``.
        G2: Unnormalized G2, shape ``(n_delays, 3, img_v, img_h)``.
        outlier_method: ``"MeanAbsoluteDeviation"`` or ``"StandardDeviation"``.
        outlier_threshold: Upper-bound rejection threshold (MADs / std devs).
        combine_outlier: If ``True``, union outlier masks across all delays
            per sq bin (same semantics as :func:`find_g2_pixel_outliers`).

    Returns:
        Dict with ``g2_pixel`` (n_delays, n_pixels), ``bad`` (bool, same shape),
        ``sqmap_1d`` / ``dqmap_1d`` (dead pixels set to 0), ``img_shape``
        ``(img_v, img_h)``, ``n_delays``, ``n_sq``, ``n_dq``, ``n_dead``.
    """
    n_delays, n_channels, img_v, img_h = G2.shape
    G2 = G2.reshape(n_delays, n_channels, -1)
    sqmap_1d = sqmap.ravel().copy()
    dqmap_1d = dqmap.ravel().copy()

    dead = np.all((G2[:, 1] == 0) & (G2[:, 2] == 0), axis=0)
    n_dead = int(np.sum(dead))
    sqmap_1d[dead] = 0
    dqmap_1d[dead] = 0

    g2_pixel = normalize_g2(G2)  # type: ignore[no-untyped-call]
    bad = find_g2_pixel_outliers(  # type: ignore[no-untyped-call]
        sqmap_1d, g2_pixel, threshold=outlier_threshold, method=outlier_method, combine_outlier=combine_outlier
    )

    return {
        "g2_pixel": g2_pixel,
        "bad": bad,
        "sqmap_1d": sqmap_1d,
        "dqmap_1d": dqmap_1d,
        "img_shape": (img_v, img_h),
        "n_delays": n_delays,
        "n_sq": int(np.max(sqmap_1d)),
        "n_dq": int(np.max(dqmap_1d)),
        "n_dead": n_dead,
    }
