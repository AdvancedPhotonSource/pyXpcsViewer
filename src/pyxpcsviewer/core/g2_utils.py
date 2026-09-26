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

#: Accepted values for the ``error_model`` argument of :func:`compute_g2`.
#:
#: ``"per-pixel"``: g2_err is the standard error of the mean of the per-pixel g2
#: values inside the dq bin -- ``std(g2_pixel) / sqrt(n_pixels_in_dq_bin)``.
#: ``"sq-group"``: g2_err is the standard error of the mean of the sq-bin averaged
#: g2 values making up the dq bin -- ``std(g2_sq) / sqrt(n_sq_bins_in_dq_bin)``.
ERROR_MODELS = ("per-pixel", "sq-group")

#: Default error model, matching the historical (pre-outlier-rejection) behaviour.
DEFAULT_ERROR_MODEL = "per-pixel"

#: Accepted values for the ``target`` argument -- which per-pixel quantity the
#: outlier statistic is computed on.
#:
#: ``"G2"``: the unnormalized correlation numerator ``G2[:, 0]``.  Outliers are
#: pixels whose *raw* correlation is anomalous for their sq bin, which in practice
#: means bright/hot pixels (``G2 ~ I**2 * g2``).
#: ``"g2-per-pixel"``: the normalized per-pixel g2 (:func:`normalize_g2`).  Outliers
#: are pixels whose *correlation* is anomalous independent of their brightness.
#:
#: The ``"G2"`` name also appears in
#: :meth:`~pyxpcsviewer.core.xpcs_file.XpcsFile.get_G2_data`, where it selects the
#: same array (channel 0) to *display* -- a different code path; don't conflate.
OUTLIER_TARGETS = ("g2-per-pixel", "G2")

#: Default outlier target.
#:
#: ``"g2-per-pixel"``, not ``"G2"``: measured on real data (A0096 glassy carbon,
#: a static scatterer whose true g2 is flat), a per-delay ``G2`` cut at 3 MADs
#: rejects 21.6% of samples and drags the g2 baseline to 0.91 with q-bins down to
#: 0.55 -- impossible values.  ``g2 = <I**2 g2_pix> / <I>**2``, so trimming the
#: brightest pixels strips tail mass from a mean-of-squares far faster than from a
#: square-of-mean and biases the ratio down.  That is intrinsic to cutting on the
#: numerator, not a threshold to tune.  ``G2`` is still the right statistic for
#: finding persistently hot pixels -- see *min_tag_count*.
DEFAULT_OUTLIER_TARGET = "g2-per-pixel"

#: Accepted values for the ``outlier_method`` argument of :func:`compute_g2`.
#:
#: ``"MeanAbsoluteDeviation"`` / ``"StandardDeviation"``: per-``(sq bin, delay)``
#: center + threshold*spread cut computed by :func:`find_g2_pixel_outliers` on
#: whichever per-pixel statistic ``target`` selects.
#: ``"G2-smooth-bkg"``: a single global smooth-background reference built from
#: the file's own time-averaged ``scattering_1d``, scaled to match the
#: intensity channels (see :func:`fit_scattering_scale`), with a flat
#: ``> threshold`` cut on ``G2[:, 0] / IPIF_smooth**2`` (see
#: :func:`find_g2_smooth_bkg_outliers`). ``target`` is not consulted for this
#: method -- it always uses the raw numerator.
OUTLIER_METHODS = ("MeanAbsoluteDeviation", "StandardDeviation", "G2-smooth-bkg")


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


def _apply_persistence_filter(bad, combine_outlier=False, min_tag_count=0):
    """Turn independent per-delay flags into a persistence-filtered mask, in place.

    Shared tail of :func:`find_g2_pixel_outliers` and
    :func:`find_g2_smooth_bkg_outliers` -- see the former's docstring for the
    semantics of *combine_outlier* / *min_tag_count*.

    Args:
        bad: Boolean mask, shape ``(n_delays, n_pixels)``. Modified in place.
        combine_outlier: If ``True``, equivalent to ``min_tag_count=1``. Ignored
            when *min_tag_count* is set.
        min_tag_count: Reject only pixels flagged at this many delays or more, at
            every delay. ``0`` (default) keeps the per-delay flags as they are.

    Returns:
        *bad*, for convenience.
    """
    n_tags = min_tag_count if min_tag_count > 0 else (1 if combine_outlier else 0)
    if n_tags > 0:
        bad[:] = bad.sum(axis=0) >= n_tags
    return bad


def find_g2_pixel_outliers(
    sqmap, values, threshold=3.0, method="MeanAbsoluteDeviation", combine_outlier=False, min_tag_count=0
):
    """Flag per-pixel, per-delay outliers of *values* within each sqmap bin.

    *values* is whichever per-pixel statistic the caller selected via ``target``
    (see :data:`OUTLIER_TARGETS`) -- either the unnormalized numerator ``G2[:, 0]``
    or the normalized per-pixel g2.  Nothing here assumes one or the other.

    Detection is independent for each ``(sq bin, delay)`` pair: pixels with
    ``values == 0`` (photon-starved, not bad) are excluded from both the
    center/spread statistics and the rejection test, and only an upper bound
    is applied (``center + threshold * spread``) — there is no lower bound.
    The zero test picks the same pixels under either target, since
    ``g2_pixel == 0`` exactly when ``G2[:, 0] == 0`` (:func:`normalize_g2` clamps
    its denominator away from zero).

    By default a pixel flagged at one delay is not flagged at any other delay.
    *min_tag_count* turns on a **persistence filter** instead: a pixel flagged at
    fewer than *min_tag_count* delays is not rejected at all, and one flagged at
    at least that many is rejected at *every* delay.  This is how the ``"G2"``
    target is usable -- a single-delay ``G2`` flag mostly tracks the intensity
    gradient across a q ring, while a flag that repeats across most delays is a
    genuinely hot pixel.  On A0096, ``G2`` flags 3279 pixels at all 34 delays
    that ``"g2-per-pixel"`` never flags at even 30.

    *combine_outlier* is the ``min_tag_count == 1`` special case (flagged
    anywhere -> flagged everywhere), kept for callers that predate the count.

    Args:
        sqmap: Static ROI map, raveled, shape ``(n_pixels,)``.
        values: Per-pixel outlier statistic, shape ``(n_delays, n_pixels)``.
        threshold: Number of MADs (or standard deviations) above center for rejection.
        method: ``"MeanAbsoluteDeviation"`` or ``"StandardDeviation"``.
        combine_outlier: If ``True``, equivalent to ``min_tag_count=1``. Ignored
            when *min_tag_count* is set.
        min_tag_count: Reject only pixels flagged at this many delays or more, at
            every delay. ``0`` (default) keeps the per-delay flags as they are.

    Returns:
        Boolean mask, shape ``(n_delays, n_pixels)``, ``True`` where the pixel
        is flagged as an outlier.
    """
    n_sq = int(np.max(sqmap))
    bad = np.zeros_like(values, dtype=bool)

    # Group pixels by sq bin once via a stable sort instead of re-scanning the full
    # pixel array with `sqmap == idx` on every one of the n_sq loop iterations (that
    # was O(n_sq * n_pixels) and dominated runtime on large detectors/bin counts).
    # Stable sort preserves each bin's pixels in their original left-to-right order,
    # so `order[starts[idx-1]:starts[idx]]` selects the same pixels, in the same
    # order, that `sqmap == idx` would have.
    order = np.argsort(sqmap, kind="stable")
    sorted_sq = sqmap[order]
    starts = np.searchsorted(sorted_sq, np.arange(1, n_sq + 2))

    for idx in range(1, n_sq + 1):
        pix_idx = order[starts[idx - 1] : starts[idx]]
        if pix_idx.size == 0:
            continue

        vals_roi = values[:, pix_idx]  # (n_delays, n_pixels_in_roi)
        vals_roi_nan = np.where(vals_roi == 0, np.nan, vals_roi)

        with warnings.catch_warnings():
            # a delay with zero nonzero pixels in this bin produces an all-NaN row,
            # which is a legitimate case handled below via nan_to_num, not an error
            warnings.simplefilter("ignore", category=RuntimeWarning)
            if method == "StandardDeviation":
                center = np.nanmean(vals_roi_nan, axis=1, keepdims=True)
                spread = np.nanstd(vals_roi_nan, axis=1, keepdims=True)
            else:  # default: MeanAbsoluteDeviation
                center = np.nanmedian(vals_roi_nan, axis=1, keepdims=True)
                spread = np.nanmedian(np.abs(vals_roi_nan - center), axis=1, keepdims=True)

        center = np.nan_to_num(center, nan=0.0)
        spread = np.nan_to_num(spread, nan=1.0)
        spread[spread == 0] = 1.0
        hi = center + threshold * spread

        bad[:, pix_idx] = vals_roi > hi

    # Persistence filter: trust a flag only if it repeats. Pixels outside every
    # sq bin are never flagged above, so their count is 0 and they stay clean.
    # n_tags == 1 reproduces the old per-bin union exactly (that loop was a
    # per-pixel any() over delays; the bin partition never affected the result).
    return _apply_persistence_filter(bad, combine_outlier=combine_outlier, min_tag_count=min_tag_count)


def fit_scattering_scale(G2, sqmap_1d, scattering_1d):
    """Fit the closed-form scale factor between the IP/IF channels and ``scattering_1d``.

    Empirically, the sq-bin-averaged IP and IF channels (``G2[:, 1]``,
    ``G2[:, 2]``) are each, to within noise, a constant multiple of the file's
    own time-averaged ``scattering_1d`` -- both are the same mean detector
    intensity per sq bin, just accumulated (and possibly frame-normalized)
    differently. This fits that multiple by ordinary least squares in closed
    form: ``scale = sum(combined_sq * scattering_1d) / sum(scattering_1d**2)``,
    where ``combined_sq`` is ``(IP + IF) / 2`` averaged over delays and folded
    into per-sq-bin means via :func:`average_by_qindex`.

    Only sq bins that are both populated (at least one live pixel) and finite
    in *scattering_1d* (not NaN -- masked/missing static bins) contribute to
    the fit.

    Args:
        G2: Unnormalized G2, shape ``(n_delays, 3, n_pixels)`` or
            ``(n_delays, 3, img_v, img_h)``.
        sqmap_1d: Static ROI map, raveled, shape ``(n_pixels,)``. Dead pixels
            should already be zeroed by the caller (as :func:`compute_g2` does).
        scattering_1d: Time-averaged SAXS-1D intensity indexed by sq bin
            (1-based bin *n* at index *n - 1*), shape ``(n_sq,)`` or larger
            (only the first ``n_sq`` entries are used). May contain NaN for
            masked/missing bins.

    Returns:
        The fitted scale factor (float).

    Raises:
        ValueError: If *scattering_1d* has fewer entries than the number of sq
            bins in *sqmap_1d*, or no sq bin qualifies for the fit.
    """
    n_delays, n_channels = G2.shape[0], G2.shape[1]
    G2 = G2.reshape(n_delays, n_channels, -1)
    n_sq = int(np.max(sqmap_1d))
    scattering_1d = np.asarray(scattering_1d)
    if scattering_1d.size < n_sq:
        raise ValueError(f"scattering_1d has {scattering_1d.size} entries, fewer than the {n_sq} sq bins in sqmap")
    scattering_1d = scattering_1d[:n_sq].astype(float)

    combined = (G2[:, 1] + G2[:, 2]) / 2.0  # (n_delays, n_pixels)
    combined_mean = np.mean(combined, axis=0, keepdims=True)  # (1, n_pixels)
    combined_sq = average_by_qindex(sqmap_1d, combined_mean)[0]  # (n_sq,)

    count = np.bincount(sqmap_1d.ravel(), minlength=n_sq + 1)[1 : n_sq + 1]
    valid = (count > 0) & np.isfinite(scattering_1d)
    if not np.any(valid):
        raise ValueError("no populated sq bin has a finite scattering_1d value; cannot fit scale")

    denom = np.sum(scattering_1d[valid] ** 2)
    if denom == 0:
        raise ValueError("scattering_1d is all zero over the populated sq bins; cannot fit scale")

    return float(np.sum(combined_sq[valid] * scattering_1d[valid]) / denom)


def find_g2_smooth_bkg_outliers(
    sqmap_1d, G2_channel0, scattering_1d, scale, threshold=3.0, combine_outlier=False, min_tag_count=0
):
    """Flag per-pixel, per-delay outliers against a smooth-background reference.

    Builds a per-pixel smooth-intensity reference ``IPIF_smooth`` by broadcasting
    ``scale * scattering_1d`` through *sqmap_1d* (sq bin *n* gets
    ``scale * scattering_1d[n - 1]``), then flags pixels where
    ``G2_channel0 / IPIF_smooth ** 2 > threshold``. Unlike
    :func:`find_g2_pixel_outliers` there is no per-bin center/spread estimate --
    the smooth background *is* the reference, so this is a flat cut, with no
    "method" (MAD vs. std dev) to choose.

    Pixels outside every sq bin, and pixels whose sq bin has no finite
    *scattering_1d* value (masked/missing static bin), have no valid smooth
    reference and are never flagged -- the same treatment
    :func:`find_g2_pixel_outliers` gives photon-starved (``value == 0``) pixels.

    Args:
        sqmap_1d: Static ROI map, raveled, shape ``(n_pixels,)``.
        G2_channel0: Unnormalized correlation numerator ``G2[:, 0]``, shape
            ``(n_delays, n_pixels)``.
        scattering_1d: Time-averaged SAXS-1D intensity indexed by sq bin,
            shape ``(n_sq,)`` or larger (only the first ``n_sq`` entries are
            used). May contain NaN for masked/missing bins.
        scale: Scale factor from :func:`fit_scattering_scale`.
        threshold: Reject a pixel when ``G2_channel0 / IPIF_smooth ** 2``
            exceeds this value. Upper bound only -- there is no lower bound.
        combine_outlier: If ``True``, equivalent to ``min_tag_count=1``. Ignored
            when *min_tag_count* is set.
        min_tag_count: Reject only pixels flagged at this many delays or more, at
            every delay (see :func:`find_g2_pixel_outliers`). ``0`` (default)
            keeps the per-delay flags as they are.

    Returns:
        Boolean mask, shape ``(n_delays, n_pixels)``, ``True`` where the pixel
        is flagged as an outlier.
    """
    n_sq = int(np.max(sqmap_1d))
    scattering_1d = np.asarray(scattering_1d)[:n_sq].astype(float)

    # index 0 is unused (sqmap is 1-based; 0 means "outside every sq bin"), and
    # stays 0 for bins without a finite scattering_1d value -- both end up
    # excluded via the `live` mask below.
    smooth_by_bin = np.zeros(n_sq + 1)
    finite = np.isfinite(scattering_1d)
    smooth_by_bin[1:][finite] = scale * scattering_1d[finite]
    ipif_smooth = smooth_by_bin[sqmap_1d]  # (n_pixels,)

    live = ipif_smooth > 0
    bad = np.zeros_like(G2_channel0, dtype=bool)
    bad[:, live] = (G2_channel0[:, live] / ipif_smooth[live] ** 2) > threshold

    return _apply_persistence_filter(bad, combine_outlier=combine_outlier, min_tag_count=min_tag_count)


def compute_g2(
    sqmap,
    dqmap,
    G2,
    outlier_method="MeanAbsoluteDeviation",
    outlier_threshold=-1.0,
    combine_outlier=False,
    min_tag_count=0,
    error_model=DEFAULT_ERROR_MODEL,
    target=DEFAULT_OUTLIER_TARGET,
    scattering_1d=None,
):
    """Compute g2 and its error using static and dynamic ROI maps.

    Args:
        sqmap: The static ROI map.
        dqmap: The dynamic ROI map.
        G2: The unnormalized G2 data with shape ``(n_delays, n_channels, img_v, img_h)``.
        outlier_method: One of :data:`OUTLIER_METHODS`, consulted only when
            ``outlier_threshold >= 0``. ``"MeanAbsoluteDeviation"`` /
            ``"StandardDeviation"`` use :func:`find_g2_pixel_outliers`;
            ``"G2-smooth-bkg"`` uses :func:`find_g2_smooth_bkg_outliers` instead
            and requires *scattering_1d*; ``target`` is not consulted for it.
        outlier_threshold: Reject pixels with ``g2_pixel`` above ``center + threshold * spread``
            within their sq bin, evaluated independently per delay (see
            :func:`find_g2_pixel_outliers`). Negative (default) disables rejection entirely.
            For ``outlier_method="G2-smooth-bkg"``, this is instead a flat cut on
            ``G2[:, 0] / IPIF_smooth ** 2`` (see :func:`find_g2_smooth_bkg_outliers`).
        combine_outlier: The ``min_tag_count=1`` special case, kept for older callers.
            Only consulted when ``outlier_threshold >= 0``. Default ``False``.
        min_tag_count: Reject only pixels flagged at this many delays or more, at every
            delay (see :func:`find_g2_pixel_outliers`). ``0`` (default) keeps the
            per-delay flags. This is what makes ``target="G2"`` usable: on A0096 a raw
            per-delay G2 cut biases g2 below 1, while ``min_tag_count=30`` of 34 removes
            5027 hot pixels and leaves the curve flat and physical.
        error_model: One of :data:`ERROR_MODELS`; selects how ``g2_err`` is estimated.
            ``"per-pixel"`` (default) takes the scatter of the individual pixels in the
            dq bin; ``"sq-group"`` takes the scatter of the sq-bin averages making up the
            dq bin.  Only ``g2_err`` is affected -- ``g2`` itself is identical either way.
        target: One of :data:`OUTLIER_TARGETS`; selects which per-pixel quantity the
            outlier statistic runs on. Default :data:`DEFAULT_OUTLIER_TARGET`.
            This only changes *which pixels are rejected* -- the reported ``g2`` is
            always the normalized sq-bin average either way. Only consulted when
            ``outlier_threshold >= 0`` and ``outlier_method != "G2-smooth-bkg"``.
        scattering_1d: Time-averaged SAXS-1D intensity indexed by sq bin, required
            when ``outlier_method="G2-smooth-bkg"`` and ``outlier_threshold >= 0``
            (see :func:`fit_scattering_scale`). Ignored otherwise.

    Returns:
        Tuple of ``(g2, g2_err)`` where *g2* is the normalized g2 values with shape
        ``(n_delays, n_dq)``, always the mean of *g2_sq* over the sq bins in each dq bin,
        and *g2_err* is the standard error of the mean selected by *error_model*.

    Raises:
        ValueError: If *error_model* is not one of :data:`ERROR_MODELS`, *target*
            is not one of :data:`OUTLIER_TARGETS`, *outlier_method* is not one of
            :data:`OUTLIER_METHODS`, or *outlier_method* is ``"G2-smooth-bkg"``
            with rejection enabled but *scattering_1d* is ``None``.
    """
    if error_model not in ERROR_MODELS:
        raise ValueError(f"error_model must be one of {ERROR_MODELS}, got {error_model!r}")
    if target not in OUTLIER_TARGETS:
        raise ValueError(f"target must be one of {OUTLIER_TARGETS}, got {target!r}")
    if outlier_method not in OUTLIER_METHODS:
        raise ValueError(f"outlier_method must be one of {OUTLIER_METHODS}, got {outlier_method!r}")
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
        if outlier_method == "G2-smooth-bkg":
            if scattering_1d is None:
                raise ValueError("outlier_method='G2-smooth-bkg' requires scattering_1d")
            scale = fit_scattering_scale(G2, sqmap_1d, scattering_1d)
            bad = find_g2_smooth_bkg_outliers(
                sqmap_1d,
                G2[:, 0],
                scattering_1d,
                scale,
                threshold=outlier_threshold,
                combine_outlier=combine_outlier,
                min_tag_count=min_tag_count,
            )
        else:
            # G2 is already (n_delays, n_channels, n_pixels) here, so G2[:, 0] is a strided
            # view of the numerator -- no copy of a multi-hundred-MB cube.
            values = G2[:, 0] if target == "G2" else g2_pixel
            bad = find_g2_pixel_outliers(
                sqmap_1d,
                values,
                threshold=outlier_threshold,
                method=outlier_method,
                combine_outlier=combine_outlier,
                min_tag_count=min_tag_count,
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
            if error_model == "per-pixel":
                # scatter of the raw pixels in this dq bin; note this reads g2_pixel, so
                # outlier-flagged pixels still contribute to the error even though they
                # were excluded from the g2 average above.
                g2_err[:, idx - 1] = np.std(temp, axis=1) / np.sqrt(temp.shape[1])
            else:  # "sq-group"
                # scatter of the sq-bin averages that make up this dq bin
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
    avg_result,
    sqmap,
    dqmap,
    outlier_method="MeanAbsoluteDeviation",
    outlier_threshold=-1.0,
    combine_outlier=False,
    min_tag_count=0,
    error_model=DEFAULT_ERROR_MODEL,
    target=DEFAULT_OUTLIER_TARGET,
    scattering_1d=None,
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
        outlier_method: One of :data:`OUTLIER_METHODS`, consulted only when
            ``outlier_threshold >= 0`` (see :func:`compute_g2`).
        outlier_threshold: Per-delay, per-sq-bin upper-bound outlier rejection threshold
            (see :func:`find_g2_pixel_outliers`). Negative (default) disables rejection.
        combine_outlier: The ``min_tag_count=1`` special case, kept for older callers.
            Only consulted when ``outlier_threshold >= 0``. Default ``False``.
        min_tag_count: Reject only pixels flagged at this many delays or more, at every
            delay (see :func:`find_g2_pixel_outliers`). ``0`` (default) keeps per-delay flags.
        error_model: One of :data:`ERROR_MODELS`; selects the ``g2_err`` estimator
            (see :func:`compute_g2`). Default ``"per-pixel"``.
        target: One of :data:`OUTLIER_TARGETS`; selects the per-pixel quantity the
            outlier statistic runs on (see :func:`compute_g2`).
            Default :data:`DEFAULT_OUTLIER_TARGET`.
        scattering_1d: Time-averaged SAXS-1D intensity indexed by sq bin, required
            when ``outlier_method="G2-smooth-bkg"`` and ``outlier_threshold >= 0``
            (see :func:`compute_g2`).

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
        min_tag_count=min_tag_count,
        error_model=error_model,
        target=target,
        scattering_1d=scattering_1d,
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
    min_tag_count=0,
    error_model=DEFAULT_ERROR_MODEL,
    target=DEFAULT_OUTLIER_TARGET,
    scattering_1d=None,
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
        outlier_method: One of :data:`OUTLIER_METHODS`, consulted only when
            ``outlier_threshold >= 0`` (see :func:`compute_g2`).
        outlier_threshold: Per-delay, per-sq-bin upper-bound outlier rejection threshold
            (see :func:`find_g2_pixel_outliers`). Negative (default) disables rejection.
        combine_outlier: The ``min_tag_count=1`` special case, kept for older callers.
            Only consulted when ``outlier_threshold >= 0``. Default ``False``.
        min_tag_count: Reject only pixels flagged at this many delays or more, at every
            delay (see :func:`find_g2_pixel_outliers`). ``0`` (default) keeps per-delay flags.
        error_model: One of :data:`ERROR_MODELS`; selects the ``g2_err`` estimator
            (see :func:`compute_g2`). Default ``"per-pixel"``.
        target: One of :data:`OUTLIER_TARGETS`; selects the per-pixel quantity the
            outlier statistic runs on (see :func:`compute_g2`).
            Default :data:`DEFAULT_OUTLIER_TARGET`.
        scattering_1d: Time-averaged SAXS-1D intensity indexed by sq bin, required
            when ``outlier_method="G2-smooth-bkg"`` and ``outlier_threshold >= 0``.
            Its sq-bin indexing must match *fname*'s own internal Q-map, so this
            is incompatible with an external/drawn *qmap_fname*.

    Returns:
        The updated avg_result dictionary with ``'g2'`` and ``'g2_err'`` added.

    Raises:
        ValueError: If ``outlier_method="G2-smooth-bkg"`` and *qmap_fname* names a
            file other than *fname* (an external or drawn Q-map) -- *scattering_1d*'s
            sq-bin indexing would not correspond to that Q-map's bins.
    """
    if outlier_method == "G2-smooth-bkg" and qmap_fname is not None and qmap_fname != fname:
        raise ValueError(
            "outlier_method='G2-smooth-bkg' requires the file's own internal Q-map; "
            "it is incompatible with an external or drawn Q-map"
        )
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
        min_tag_count=min_tag_count,
        error_model=error_model,
        target=target,
        scattering_1d=scattering_1d,
    )


def compute_g2_debug_bundle(
    sqmap: np.ndarray,
    dqmap: np.ndarray,
    G2: np.ndarray,
    outlier_method: str = "MeanAbsoluteDeviation",
    outlier_threshold: float = 3.0,
    combine_outlier: bool = False,
    min_tag_count: int = 0,
    target: str = DEFAULT_OUTLIER_TARGET,
    scattering_1d: np.ndarray | None = None,
) -> dict[str, Any]:
    """Compute the per-pixel data the G2 outlier debug dialog plots.

    Mirrors :func:`compute_g2` preprocessing exactly (dead-pixel masking,
    normalize) and runs the same outlier pass, so the dialog visualizes what
    ReGroup actually sees. Pure numpy, no file IO.

    Args:
        sqmap: Static ROI map, shape ``(img_v, img_h)``.
        dqmap: Dynamic ROI map, shape ``(img_v, img_h)``.
        G2: Unnormalized G2, shape ``(n_delays, 3, img_v, img_h)``.
        outlier_method: One of :data:`OUTLIER_METHODS`. ``"G2-smooth-bkg"``
            requires *scattering_1d* and ignores *target*.
        outlier_threshold: Upper-bound rejection threshold. For
            ``"MeanAbsoluteDeviation"`` / ``"StandardDeviation"`` this is in
            MADs / std devs above each ``(sq bin, delay)`` center; for
            ``"G2-smooth-bkg"`` it is a flat cut on
            ``G2[:, 0] / IPIF_smooth ** 2``.
        combine_outlier: If ``True``, equivalent to ``min_tag_count=1``
            (same semantics as :func:`find_g2_pixel_outliers`).
        min_tag_count: Persistence filter (see :func:`find_g2_pixel_outliers`).
            Leave at ``0`` to plot the raw per-delay flags -- the bad-pixel map's
            tag-count slider is how you pick a value for it.
        target: One of :data:`OUTLIER_TARGETS`; selects the per-pixel quantity the
            outlier statistic runs on, and hence what ``values`` holds. Ignored
            when ``outlier_method="G2-smooth-bkg"``.
        scattering_1d: Time-averaged SAXS-1D intensity indexed by sq bin,
            required when ``outlier_method="G2-smooth-bkg"`` (see
            :func:`fit_scattering_scale`). Ignored otherwise.

    Returns:
        Dict with ``values`` (the per-pixel statistic actually fed to the outlier
        pass, ``(n_delays, n_pixels)``), ``target`` (str -- ``"G2-smooth-bkg"``
        when that method is used, regardless of the *target* argument), ``bad``
        (bool, same shape as ``values``), ``sqmap_1d`` / ``dqmap_1d`` (dead
        pixels set to 0), ``img_shape`` ``(img_v, img_h)``, ``n_delays``,
        ``n_sq``, ``n_dq``, ``n_dead``, and (only for ``"G2-smooth-bkg"``)
        ``scale`` (the fitted scale factor from :func:`fit_scattering_scale`).

    Raises:
        ValueError: If *target* is not one of :data:`OUTLIER_TARGETS`,
            *outlier_method* is not one of :data:`OUTLIER_METHODS`, or
            *outlier_method* is ``"G2-smooth-bkg"`` but *scattering_1d* is
            ``None``.
    """
    if target not in OUTLIER_TARGETS:
        raise ValueError(f"target must be one of {OUTLIER_TARGETS}, got {target!r}")
    if outlier_method not in OUTLIER_METHODS:
        raise ValueError(f"outlier_method must be one of {OUTLIER_METHODS}, got {outlier_method!r}")
    n_delays, n_channels, img_v, img_h = G2.shape
    G2 = G2.reshape(n_delays, n_channels, -1)
    sqmap_1d = sqmap.ravel().copy()
    dqmap_1d = dqmap.ravel().copy()

    dead = np.all((G2[:, 1] == 0) & (G2[:, 2] == 0), axis=0)
    n_dead = int(np.sum(dead))
    sqmap_1d[dead] = 0
    dqmap_1d[dead] = 0

    bundle: dict[str, Any] = {
        "sqmap_1d": sqmap_1d,
        "dqmap_1d": dqmap_1d,
        "img_shape": (img_v, img_h),
        "n_delays": n_delays,
        "n_sq": int(np.max(sqmap_1d)),
        "n_dq": int(np.max(dqmap_1d)),
        "n_dead": n_dead,
    }

    if outlier_method == "G2-smooth-bkg":
        if scattering_1d is None:
            raise ValueError("outlier_method='G2-smooth-bkg' requires scattering_1d")
        scale = fit_scattering_scale(G2, sqmap_1d, scattering_1d)
        n_sq = bundle["n_sq"]
        scattering_arr = np.asarray(scattering_1d)[:n_sq].astype(float)
        smooth_by_bin = np.zeros(n_sq + 1)
        finite = np.isfinite(scattering_arr)
        smooth_by_bin[1:][finite] = scale * scattering_arr[finite]
        ipif_smooth = smooth_by_bin[sqmap_1d]
        live = ipif_smooth > 0
        values = np.full_like(G2[:, 0], np.nan)
        values[:, live] = G2[:, 0][:, live] / ipif_smooth[live] ** 2
        bad = find_g2_smooth_bkg_outliers(  # type: ignore[no-untyped-call]
            sqmap_1d,
            G2[:, 0],
            scattering_1d,
            scale,
            threshold=outlier_threshold,
            combine_outlier=combine_outlier,
            min_tag_count=min_tag_count,
        )
        bundle["target"] = "G2-smooth-bkg"
        bundle["scale"] = scale
    else:
        # only materialize the normalized per-pixel g2 when it is the target -- on a
        # 1 Mpixel detector with 60 delays that array is ~240 MB, and nothing else in
        # the bundle needs it. G2[:, 0] is a view, so the G2 branch allocates nothing.
        values = G2[:, 0] if target == "G2" else normalize_g2(G2)  # type: ignore[no-untyped-call]
        bad = find_g2_pixel_outliers(  # type: ignore[no-untyped-call]
            sqmap_1d,
            values,
            threshold=outlier_threshold,
            method=outlier_method,
            combine_outlier=combine_outlier,
            min_tag_count=min_tag_count,
        )
        bundle["target"] = target

    bundle["values"] = values
    bundle["bad"] = bad
    return bundle
