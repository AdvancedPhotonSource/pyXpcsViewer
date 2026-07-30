# Copyright © UChicago Argonne LLC
# See LICENSE file for details
import logging
import os
import re
import shutil
import warnings
from functools import cached_property

import numpy as np

from .file_io.hdf_reader import get, get_analysis_type, read_metadata_to_dict
from .file_io.qmap_utils import get_qmap
from .fitting import double_exp_all, fit_with_fixed, power_law, single_exp_all
from .twotime_utils import get_c2_stream, get_single_c2_from_hdf

logger = logging.getLogger(__name__)


def create_id(fname, label_style=None, simplify_flag=True):
    """Generate a simplified or customized ID string from a filename.

    Args:
        fname: Input file name, possibly with path and extension.
        label_style: Comma-separated string of indices to extract specific components
            from the file name.
        simplify_flag: Whether to simplify the file name by removing leading zeros
            and stripping suffixes.

    Returns:
        A simplified or customized ID string derived from the input filename.
    """
    fname = os.path.basename(fname)

    if simplify_flag:
        # Remove leading zeros from structured parts like '_t0600' → '_t600'
        fname = re.sub(r"_(\w)0+(\d+)", r"_\1\2", fname)
        # Remove trailing _results and file extension
        fname = re.sub(r"(_results)?\.hdf$", "", fname, flags=re.IGNORECASE)

    if len(fname) < 10 or not label_style:
        return fname

    try:
        selection = [int(x.strip()) for x in label_style.split(",")]
        if not selection:
            warnings.warn(
                "Empty label_style selection. Returning simplified filename.",
                stacklevel=2,
            )
            return fname
    except ValueError:
        warnings.warn(
            "Invalid label_style format. Must be comma-separated integers.",
            stacklevel=2,
        )
        return fname

    segments = fname.split("_")
    selected_segments = []

    for i in selection:
        if i < len(segments):
            selected_segments.append(segments[i])
        else:
            warnings.warn(
                f"Index {i} out of range for segments {segments}",
                stacklevel=2,
            )

    if not selected_segments:
        return fname  # fallback if nothing valid was selected

    return "_".join(selected_segments)


class XpcsFile:
    """
    XpcsFile is a class that wraps an Xpcs analysis hdf file;
    """

    def __init__(self, fname: str, label_style=None, qmap_manager=None):
        """Open an XPCS result HDF5 file and lazily load core datasets.

        Args:
            fname: Absolute path to the HDF5 result file.
            label_style: Comma-separated indices for deriving a short file ID.
            qmap_manager: Optional :class:`QMapManager` to share Q-map caches.
        """
        self.fname = fname
        if qmap_manager is None:
            self.qmap = get_qmap(self.fname)
        else:
            self.qmap = qmap_manager.get_qmap(self.fname)
        self.atype = get_analysis_type(self.fname)
        self.label = self.update_label(label_style)

        payload = self.load_data()

        # present regardless of analysis type
        self.saxs_1d: dict[str, np.ndarray] = payload.pop("saxs_1d")
        self.Iqp: np.ndarray = payload.pop("Iqp")
        self.Int_t: np.ndarray = payload.pop("Int_t")
        self.t0: float = payload.pop("t0")
        self.t1: float = payload.pop("t1")
        self.start_time: str = payload.pop("start_time")
        self.abs_cross_section_scale: float = payload.pop("abs_cross_section_scale")

        # only present for Multitau files
        self.tau: np.ndarray | None = payload.pop("tau", None)
        self.g2: np.ndarray | None = payload.pop("g2", None)
        self.g2_err: np.ndarray | None = payload.pop("g2_err", None)
        self.t_el: np.ndarray | None = payload.pop("t_el", None)
        self.g2_t0: float | None = payload.pop("g2_t0", None)

        # only present for Twotime files
        self.c2_g2: np.ndarray | None = payload.pop("c2_g2", None)
        self.c2_g2_segments: np.ndarray | None = payload.pop("c2_g2_segments", None)
        self.c2_processed_bins: np.ndarray | None = payload.pop("c2_processed_bins", None)
        self.c2_t0: float | None = payload.pop("c2_t0", None)

        self.hdf_info = None
        self.fit_summary = None
        self.c2_all_data = None
        self.c2_kwargs = None

    def update_label(self, label_style) -> str:
        """Re-derive the short label from the current filename.

        Args:
            label_style: Comma-separated indices for ID generation.

        Returns:
            The newly computed label string.
        """
        self.label = create_id(self.fname, label_style=label_style)
        return self.label

    def __str__(self) -> str:
        """Multi-line representation showing filename and all attribute shapes."""
        ans = ["File:" + str(self.fname)]
        for key, val in self.__dict__.items():
            # omit those to avoid lengthy output
            if key == "hdf_info":
                continue
            elif isinstance(val, np.ndarray) and val.size > 1:
                val = str(val.shape)
            else:
                val = str(val)
            ans.append(f"   {key.ljust(12)}: {val.ljust(30)}")
        return "\n".join(ans)

    def __repr__(self) -> str:
        """Class name followed by the output of :meth:`__str__`."""
        ans = str(type(self))
        ans = "\n".join([ans, self.__str__()])
        return ans

    def get_hdf_info(self, fstr=None):
        """Return a tree-structured text representation of the HDF5 file.

        Results are cached on the instance after first call.

        Args:
            fstr: List of filter strings to include (e.g. ``["string_1", "string_2"]``).

        Returns:
            List of strings describing the file structure.
        """
        # cache the data because it may take long time to generate the str
        if self.hdf_info is None:
            self.hdf_info = read_metadata_to_dict(self.fname)
        return self.hdf_info

    def has_field(self, field: str) -> bool:
        """Check whether *field* exists in the HDF5 file via the alias key map.

        Args:
            field: Semantic field name (e.g. ``"g2"``, ``"saxs_2d"``).

        Returns:
            ``True`` if the field is resolvable and present, else ``False``.
        """
        try:
            get(self.fname, [field], "alias", ftype="nexus")
            return True
        except (KeyError, ValueError):
            return False

    def load_data(self) -> dict:
        """Load the default datasets for this file's analysis type from the HDF5 file.

        Handles g2_err correction, time-step multiplication, and Q-map reshaping
        for SAXS 1D / stability data before returning everything as a flat dict.

        Returns:
            Dict of loaded dataset values keyed by their semantic names.
        """
        # default common fields for both twotime and multitau analysis;
        fields = ["saxs_1d", "Iqp", "Int_t", "t0", "t1", "start_time"]

        if "Multitau" in self.atype:
            fields = fields + ["tau", "g2", "g2_err", "stride_frame", "avg_frame"]
        if "Twotime" in self.atype:
            fields = fields + [
                "c2_g2",
                "c2_g2_segments",
                "c2_processed_bins",
                "c2_stride_frame",
                "c2_avg_frame",
            ]

        ret = get(self.fname, fields, "alias", ftype="nexus")

        if "Twotime" in self.atype:
            stride_frame = ret.pop("c2_stride_frame")
            avg_frame = ret.pop("c2_avg_frame")
            ret["c2_t0"] = ret["t0"] * stride_frame * avg_frame
        if "Multitau" in self.atype:
            # correct g2_err to avoid fitting divergence
            # ret['g2_err_mod'] = self.correct_g2_err(ret['g2_err'])
            ret["g2_err"] = self.correct_g2_err(ret["g2_err"])
            stride_frame = ret.pop("stride_frame")
            avg_frame = ret.pop("avg_frame")
            ret["t0"] = ret["t0"] * stride_frame * avg_frame
            ret["t_el"] = ret["tau"] * ret["t0"]
            ret["g2_t0"] = ret["t0"]

        ret["saxs_1d"] = self.qmap.reshape_phi_analysis(ret["saxs_1d"], self.label, mode="saxs_1d")
        ret["Iqp"] = self.qmap.reshape_phi_analysis(ret["Iqp"], self.label, mode="stability")

        ret["abs_cross_section_scale"] = 1.0
        return ret

    # -- Q-map delegation -------------------------------------------------
    # Plain (uncached) properties: self.qmap is assigned once in __init__
    # and never reassigned, so each access is just one extra attribute hop.

    @property
    def sqlist(self) -> np.ndarray:
        return self.qmap.sqlist

    @property
    def dqlist(self) -> np.ndarray:
        return self.qmap.dqlist

    @property
    def dqmap(self) -> np.ndarray:
        return self.qmap.dqmap

    @property
    def sqmap(self) -> np.ndarray:
        return self.qmap.sqmap

    @property
    def mask(self) -> np.ndarray:
        return self.qmap.mask

    @property
    def bcx(self) -> float:
        return self.qmap.bcx

    @property
    def bcy(self) -> float:
        return self.qmap.bcy

    @property
    def det_dist(self) -> float:
        return self.qmap.det_dist

    @property
    def pixel_size(self) -> float:
        return self.qmap.pixel_size

    @property
    def X_energy(self) -> float:
        return self.qmap.X_energy

    @property
    def splist(self) -> np.ndarray:
        return self.qmap.splist

    @property
    def dplist(self) -> np.ndarray:
        return self.qmap.dplist

    @property
    def static_num_pts(self) -> np.ndarray:
        return self.qmap.static_num_pts

    @property
    def dynamic_num_pts(self) -> np.ndarray:
        return self.qmap.dynamic_num_pts

    @property
    def map_names(self) -> list[str]:
        return self.qmap.map_names

    @property
    def map_units(self) -> list[str]:
        return self.qmap.map_units

    # -- Lazily loaded / derived data --------------------------------------

    @cached_property
    def saxs_2d(self) -> np.ndarray:
        """Full 2D detector image, read from disk on first access only."""
        return get(self.fname, ["saxs_2d"], "alias", ftype="nexus")["saxs_2d"]

    @cached_property
    def saxs_2d_log(self) -> np.ndarray:
        """Log10 of :attr:`saxs_2d`, with non-positive pixels clamped to the image minimum."""
        saxs = np.copy(self.saxs_2d)
        roi = saxs > 0
        if not np.any(roi):
            return np.zeros_like(saxs, dtype=np.uint8)
        min_val = np.min(saxs[roi])
        saxs[~roi] = min_val
        return np.log10(saxs).astype(np.float32)

    @cached_property
    def Int_t_fft(self) -> np.ndarray:
        """FFT magnitude spectrum of the intensity-vs-time trace."""
        y = np.abs(np.fft.fft(self.Int_t[1]))
        x = np.arange(y.size) / (y.size * self.t0)
        x = x[: y.size // 2]
        y = y[: y.size // 2]
        y[0] = 0
        return np.stack((x, y), axis=1).astype(np.float32).T

    def _load_optional_field(self, key: str) -> np.ndarray | None:
        """Fetch *key* from the HDF5 file, or ``None`` if this file doesn't have it."""
        try:
            return get(self.fname, [key], "alias", ftype="nexus")[key]
        except (KeyError, ValueError) as e:
            logger.warning("cannot load %s due to %s", key, e)
            return None

    @cached_property
    def G2(self) -> np.ndarray | None:
        return self._load_optional_field("G2")

    @cached_property
    def g2_partial(self) -> np.ndarray | None:
        return self._load_optional_field("g2_partial")

    @cached_property
    def g2_partial_err(self) -> np.ndarray | None:
        return self._load_optional_field("g2_partial_err")

    @cached_property
    def g2_partial_labels(self) -> np.ndarray | None:
        return self._load_optional_field("g2_partial_labels")

    def get_info_at_position(self, x: int, y: int) -> str | None:
        """Return a formatted string with scattering intensity and Q-map values at *(x, y)*.

        Args:
            x: Column pixel index on the 2D detector.
            y: Row pixel index on the 2D detector.

        Returns:
            Formatted intensity + Q-map info, or ``None`` if out of bounds.
        """
        x, y = int(x), int(y)
        shape = self.saxs_2d.shape
        if x < 0 or x >= shape[1] or y < 0 or y >= shape[0]:
            return None
        else:
            scat_intensity = self.saxs_2d[y, x]
            qmap_info = self.qmap.get_qmap_at_pos(x, y)
            return f"I={scat_intensity:.4e} {qmap_info}"

    def get_detector_extent(self) -> tuple[float, float, float, float]:
        """Return the Q-value extent of the detector (qx_min, qx_max, qy_min, qy_max)."""
        return self.qmap.extent

    def get_qbin_label(self, qbin: int, append_qbin: bool = False) -> str:
        """Delegate to :meth:`QMap.get_qbin_label` for this file's Q-map.

        Args:
            qbin: 1-based Q-bin index.
            append_qbin: If ``True``, prepend ``"qbin=N, "`` to the label.

        Returns:
            Human-readable Q-bin label string.
        """
        return self.qmap.get_qbin_label(qbin, append_qbin=append_qbin)

    def get_qbinlist_at_qindex(self, qindex: int, zero_based: bool = True) -> list[int]:
        """Delegate to :meth:`QMap.get_qbinlist_at_qindex` for this file's Q-map.

        Args:
            qindex: Zero-based column index on the dynamic axis.
            zero_based: If ``False``, return 1-based indices.

        Returns:
            List of valid Q-bin indices for that column.
        """
        return self.qmap.get_qbinlist_at_qindex(qindex, zero_based=zero_based)

    def get_g2_stability_data(self, qrange=None, trange=None):
        """Extract G2 stability data (partial G2 vs time) for a single file.

        Args:
            qrange: Optional Q-range filter ``(q_min, q_max)``.
            trange: Optional time-range filter on the elapsed axis.

        Returns:
            Tuple of ``(q_values, t_elapsed, g2_array, g2_err_array, qbin_labels, frame_labels)``.
        """
        assert "Multitau" in self.atype, "only multitau is supported"
        assert self.g2_partial is not None and self.g2_partial_err is not None and self.t_el is not None
        # qrange can be None
        qindex_selected, qvalues = self.qmap.get_qbin_in_qrange(qrange, zero_based=True)
        g2 = self.g2_partial[:, :, qindex_selected]
        g2_err = self.g2_partial_err[:, :, qindex_selected]

        qbin_labels = [f"qbin={qbin + 1}, {self.qmap.get_qbin_label(qbin + 1)}" for qbin in qindex_selected]
        labels = self.g2_partial_labels

        if trange is not None:
            t_roi = (self.t_el >= trange[0]) * (self.t_el <= trange[1])
            g2 = g2[:, t_roi]
            g2_err = g2_err[:, t_roi]
            t_el = self.t_el[t_roi]
        else:
            t_el = self.t_el

        return qvalues, t_el, g2, g2_err, qbin_labels, labels

    def get_G2_data(self, target: str = "G2", delay_index: int = 0) -> np.ndarray:
        """Extract a single G2 channel array (raw counts, correlations, or fraction) for one delay bin.

        Args:
            target: One of ``"G2"``, ``"IP"``, ``"IF"``, or ``"g2_per_pixel"``.
            delay_index: Index into the first (delay) axis.

        Returns:
            2D detector array for the requested channel.
        """
        assert target in ["G2", "IP", "IF", "g2_per_pixel"]
        G2 = self.G2
        assert G2 is not None
        delay_index = min(delay_index, G2.shape[0] - 1)

        if target in ["G2", "IP", "IF"]:
            channel_index = {"G2": 0, "IP": 1, "IF": 2}[target]
            return G2[delay_index, channel_index]
        elif target == "g2_per_pixel":
            denominator = G2[delay_index, 1] * G2[delay_index, 2]
            denominator[denominator == 0] = 1
            g2_per_pixel = G2[delay_index, 0] / denominator
            return g2_per_pixel

    def get_g2_data(
        self,
        qrange: tuple[float, float] | None = None,
        trange: tuple[float, float] | None = None,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, list[str]]:
        """Return multitau G2 data optionally filtered by Q-range and time range.

        Args:
            qrange: ``(q_min, q_max)`` filter or ``None`` for all Q values.
            trange: ``(t_min, t_max)`` filter on the elapsed time axis.

        Returns:
            Tuple of ``(q_values, t_elapsed, g2_array, g2_err_array, labels)``.
        """
        assert "Multitau" in self.atype, "only multitau is supported"
        assert self.g2 is not None and self.g2_err is not None and self.t_el is not None
        # qrange can be None
        qindex_selected, qvalues = self.qmap.get_qbin_in_qrange(qrange, zero_based=True)
        g2 = self.g2[:, qindex_selected]
        g2_err = self.g2_err[:, qindex_selected]
        labels = [f"qbin={qbin + 1}, {self.qmap.get_qbin_label(qbin + 1)}" for qbin in qindex_selected]

        if trange is not None:
            t_roi = (self.t_el >= trange[0]) * (self.t_el <= trange[1])
            g2 = g2[t_roi]
            g2_err = g2_err[t_roi]
            t_el = self.t_el[t_roi]
        else:
            t_el = self.t_el

        return qvalues, t_el, g2, g2_err, labels

    def get_saxs1d_data(
        self,
        bkg_xf=None,
        bkg_weight=1.0,
        qrange=None,
        sampling=1,
        use_absolute_crosssection=False,
        norm_method=None,
        target="saxs1d",
    ):
        """Extract SAXS 1D data with optional background subtraction, Q filtering, and normalization.

        Args:
            bkg_xf: Background :class:`~pyxpcsviewer.core.xpcs_file.XpcsFile` for subtraction.
            bkg_weight: Weighting factor for background subtraction.
            qrange: Optional ``(q_min, q_max)`` filter.
            sampling: Q-axis subsample factor.
            use_absolute_crosssection: Apply absolute cross-section scaling.
            norm_method: Normalisation mode — ``None``, ``"q2"``, ``"q4"``, or ``"I0"``.
            target: Data source — ``"saxs1d"`` or ``"saxs1d_partial"``.

        Returns:
            Tuple of ``(q, Iq, xlabel, ylabel)`` where *xlabel* and *ylabel* describe the axes.
        """
        assert target in ["saxs1d", "saxs1d_partial"]
        if target == "saxs1d":
            q, Iq = self.saxs_1d["q"], self.saxs_1d["Iq"]
        else:
            q, Iq = self.saxs_1d["q"], self.Iqp
        if bkg_xf is not None:
            if np.allclose(q, bkg_xf.saxs_1d["q"]):
                Iq = Iq - bkg_weight * bkg_xf.saxs_1d["Iq"]
                Iq[Iq < 0] = np.nan
            else:
                logger.warning("background subtraction is not applied because q is not matched")
        if qrange is not None:
            q_roi = (q >= qrange[0]) * (q <= qrange[1])
            if q_roi.sum() > 0:
                q = q[q_roi]
                Iq = Iq[:, q_roi]
            else:
                logger.warning("qrange is not applied because it is out of range")
        if use_absolute_crosssection and self.abs_cross_section_scale is not None:
            Iq *= self.abs_cross_section_scale

        # apply sampling
        if sampling > 1:
            q, Iq = q[::sampling], Iq[::sampling]
        # apply normalization
        q, Iq, xlabel, ylabel = self.norm_saxs_data(q, Iq, norm_method=norm_method)
        return q, Iq, xlabel, ylabel

    def norm_saxs_data(
        self, q: np.ndarray, Iq: np.ndarray, norm_method: str | None = None
    ) -> tuple[np.ndarray, np.ndarray, str, str]:
        """Apply an optional normalisation to SAXS 1D data (q², q⁴, or I₀ scaling).

        Args:
            q: Momentum-transfer array.
            Iq: Intensity array (possibly multi-line).
            norm_method: ``None``, ``"q2"``, ``"q4"``, or ``"I0"``.

        Returns:
            Tuple of ``(q, Iq_normalised, xlabel, ylabel)``.
        """
        assert norm_method in (None, "q2", "q4", "I0")
        if norm_method is None:
            return q, Iq, "q (Å⁻¹)", "Intensity"
        ylabel = "Intensity"
        if norm_method == "q2":
            Iq = Iq * np.square(q)
            ylabel = ylabel + " * q^2"
        elif norm_method == "q4":
            Iq = Iq * np.square(np.square(q))
            ylabel = ylabel + " * q^4"
        elif norm_method == "I0":
            baseline = Iq[0]
            Iq = Iq / baseline
            ylabel = ylabel + " / I_0"
        xlabel = "q (Å⁻¹)"
        return q, Iq, xlabel, ylabel

    def get_twotime_qbin_labels(self) -> list[str]:
        """Generate human-readable labels for each C2-processed Q-bin."""
        assert self.c2_processed_bins is not None, "only twotime is supported"
        qbin_labels = []
        for qbin in self.c2_processed_bins.tolist():
            qbin_labels.append(self.get_qbin_label(qbin, append_qbin=True))
        return qbin_labels

    def get_cropped_qmap(self, target: str = "dqmap", enabled: bool = True) -> np.ndarray:
        """Delegate to :meth:`QMap.get_cropped_qmap` for this file's Q-map.

        Args:
            target: Either ``"dqmap"`` or ``"sqmap"``.
            enabled: If ``True``, crop to the bounding box of non-zero entries.

        Returns:
            2D Numpy array cropped to the active region.
        """
        return self.qmap.get_cropped_qmap(target, enabled)

    def get_offseted_g2(self, normalization: bool = False) -> np.ndarray:
        """Return a copy of the multitau G2 data with optional baseline offset.

        Args:
            normalization: If ``True``, subtract the first-frame baseline and restore
                its mean level.

        Returns:
            Offset- or normalised G2 array.
        """
        assert self.g2 is not None, "only multitau is supported"
        g2 = self.g2.copy()
        if normalization:
            g2_baseline = g2[0]
            g2 = g2 - g2_baseline + np.mean(g2_baseline)
        return g2

    def regroup_G2(self, **kwargs) -> None:
        """Re-group the per-pixel G2 correlation data into multitau bins.

        The result is stored in-place as ``self.g2`` and ``self.g2_err``.

        Args:
            **kwargs: Forwarded to :func:`g2_utils.regroup_G2`.
        """
        from .g2_utils import regroup_G2

        avg_result = regroup_G2(self.fname, {"G2": self.G2}, **kwargs)
        self.g2 = avg_result["g2"]
        self.g2_err = avg_result["g2_err"]

    def save_G2(self, save_fname: str | None = None) -> bool:
        """Save the current ``self.g2`` / ``self.g2_err`` back to an HDF5 file.

        Args:
            save_fname: Destination path; defaults to ``self.fname`` (overwrites).

        Returns:
            ``True`` on success, ``False`` if an exception occurred.
        """
        from .g2_utils import save_G2_to_file

        try:
            if save_fname is None:
                save_fname = self.fname
            else:
                shutil.copy(self.fname, save_fname)
            save_G2_to_file(save_fname, {"g2": self.g2, "g2_err": self.g2_err})
        except Exception as e:
            logger.error(f"Failed to save G2: {e}")
            return False
        return True

    def get_twotime_maps(
        self,
        scale: str = "log",
        auto_crop: bool = True,
        highlight_xy: tuple[int, int] | None = None,
        selection: int | None = None,
    ) -> tuple[np.ndarray, np.ndarray, int | None]:
        """Return the detector Q-map overlay and SAXS 2D background for two-time analysis display.

        Optionally highlights a specific q-bin or pixel position by modifying the colour map index.

        Args:
            scale: Display scale — ``"log"`` or ``"linear"``.
            auto_crop: Crop the Q-map to its active bounding box.
            highlight_xy: Pixel coordinates whose q-bin will be highlighted.
            selection: Direct q-bin index to highlight (mutually exclusive with *highlight_xy*).

        Returns:
            Tuple of ``(dqmap_display, saxs_2d_background, selected_qbin_index)``.
        """
        saxs = self.saxs_2d_log if scale == "log" else self.saxs_2d
        dqmap_disp, selection = self.qmap.get_display_dqmap(auto_crop, highlight_xy, selection)
        return dqmap_disp, saxs, selection

    def get_twotime_c2(
        self, selection: int = 0, correct_diag: bool = True, max_size: int = 32678
    ) -> dict[str, np.ndarray | float | int]:
        """Retrieve the C2 matrix for a single q-bin (cached per call signature).

        Args:
            selection: Index into ``c2_processed_bins``.
            correct_diag: Apply diagonal correction.
            max_size: Maximum dimension for the returned C2 matrix.

        Returns:
            Dict with keys ``c2_mat``, ``delta_t``, ``acquire_period``, etc.
        """
        assert self.c2_processed_bins is not None, "only twotime is supported"
        dq_processed = tuple(self.c2_processed_bins.tolist())
        assert selection >= 0 and selection < len(dq_processed), f"selection {selection} out of range {dq_processed}"
        config = (selection, correct_diag, max_size)
        if self.c2_kwargs == config:
            return self.c2_all_data
        else:
            c2_result = get_single_c2_from_hdf(
                self.fname,
                selection=selection,
                max_size=max_size,
                t0=self.t0,
                correct_diag=correct_diag,
            )
            self.c2_all_data = c2_result
            self.c2_kwargs = config
        return c2_result

    def get_twotime_stream(self, **kwargs) -> tuple[list[str], object]:
        """Return the C2 stream index list and a generator yielding C2 blocks.

        Args:
            **kwargs: Forwarded to :func:`twotime_utils.get_c2_stream`.

        Returns:
            Tuple of ``(idxlist, generator)`` where each yielded value is ``(index, c2_array)``.
        """
        return get_c2_stream(self.fname, **kwargs)

    #     """
    #     get the fitting line for q, within tor
    #     """
    #     if self.fit_summary is None:
    #         return None, None
    #     idx = np.argmin(np.abs(self.fit_summary["q_val"] - q))
    #     if abs(self.fit_summary["q_val"][idx] - q) > tor:
    #         return None, None

    #     fit_x = self.fit_summary["fit_line"][idx]["fit_x"]
    #     fit_y = self.fit_summary["fit_line"][idx]["fit_y"]
    #     return fit_x, fit_y

    def get_fitting_info(self, mode: str = "g2_fitting") -> dict | str:
        """Format the stored fitting summary into a human-readable dictionary or message.

        Args:
            mode: Either ``"g2_fitting"`` or ``"tauq_fitting"``.

        Returns:
            Dict of fitting results for g2 mode, or a descriptive string when no
            fit is available or an unknown *mode* is requested.
        """
        if self.fit_summary is None:
            return f"fitting is not ready for {self.label}"

        if mode == "g2_fitting":
            result = self.fit_summary.copy()
            # fit_line is not useful to display
            result.pop("fit_line", None)
            val = result.pop("fit_val", None)
            prefix = ["a", "b", "c", "d"] if result["fit_func"] == "single" else ["a", "b", "c", "d", "b2", "c2", "f"]

            msg = []
            for n in range(val.shape[0]):
                temp = []
                for m in range(len(prefix)):
                    temp.append("%s = %f ± %f" % (prefix[m], val[n, 0, m], val[n, 1, m]))
                msg.append(", ".join(temp))
            result["fit_val"] = np.array(msg)

        elif mode == "tauq_fitting":
            if "tauq_fit_val" not in self.fit_summary:
                result = "tauq fitting is not available"
            else:
                v = self.fit_summary["tauq_fit_val"]
                result = "a = %e ± %e; b = %f ± %f" % (
                    v[0, 0],
                    v[1, 0],
                    v[0, 1],
                    v[1, 1],
                )
        else:
            raise ValueError("mode not supported.")

        return result

    def fit_g2(self, q_range=None, t_range=None, bounds=None, fit_flag=None, fit_func="single"):
        """Fit G2 values with single or double exponential decay.

        Args:
            q_range: Tuple of (q_min, q_max) for the Q-axis filter.
            t_range: Tuple of (t_min, t_max) for the time-axis filter.
            bounds: Fitting bounds as ``(lower, upper)``.
            fit_flag: Tuple of bools — ``True`` to fit, ``False`` to hold fixed.
            fit_func: Either ``"single"`` or ``"double"`` to select the
                exponential model.

        Returns:
            Dictionary with the fitting results.
        """
        assert len(bounds) == 2
        if fit_func == "single":
            assert len(bounds[0]) == 4, "for single exp, the shape of bounds must be (2, 4)"
            if fit_flag is None:
                fit_flag = [True for _ in range(4)]
            func = single_exp_all
        else:
            assert len(bounds[0]) == 7, "for single exp, the shape of bounds must be (2, 4)"
            if fit_flag is None:
                fit_flag = [True for _ in range(7)]
            func = double_exp_all

        q_val, t_el, g2, sigma, label = self.get_g2_data(qrange=q_range, trange=t_range)

        # set the initial guess
        p0 = np.array(bounds).mean(axis=0)
        # tau"s bounds are in log scale, set as the geometric average
        p0[1] = np.sqrt(bounds[0][1] * bounds[1][1])
        if fit_func == "double":
            p0[4] = np.sqrt(bounds[0][4] * bounds[1][4])

        fit_x = np.logspace(np.log10(np.min(t_el)) - 0.5, np.log10(np.max(t_el)) + 0.5, 128)

        fit_line, fit_val = fit_with_fixed(func, t_el, g2, sigma, bounds, fit_flag, fit_x, p0=p0)

        self.fit_summary = {
            "fit_func": fit_func,
            "fit_val": fit_val,
            "t_el": t_el,
            "q_val": q_val,
            "q_range": str(q_range),
            "t_range": str(t_range),
            "bounds": bounds,
            "fit_flag": str(fit_flag),
            "fit_line": fit_line,
            "label": label,
        }

        return self.fit_summary

    @staticmethod
    def correct_g2_err(g2_err: np.ndarray | None = None, threshold: float = 1e-6) -> np.ndarray:
        """Replace near-zero G2 errors with the column mean to prevent fitting divergence.

        Args:
            g2_err: Error array of shape ``(time, q_bins)``.
            threshold: Below this value an error is considered too small.

        Returns:
            A copy of *g2_err* with corrected errors.
        """
        # correct the err for some data points with really small error, which
        # may cause the fitting to blowup

        g2_err_mod = np.copy(g2_err)
        for n in range(g2_err.shape[1]):
            data = g2_err[:, n]
            idx = data > threshold
            # avoid averaging of empty slice
            if np.sum(idx) > 0:
                avg = np.mean(data[idx])
            else:
                avg = threshold
            g2_err_mod[np.logical_not(idx), n] = avg

        return g2_err_mod

    def fit_tauq(
        self,
        q_range: tuple[float, float],
        bounds: tuple[np.ndarray, np.ndarray],
        fit_flag: list[bool],
    ) -> dict | None:
        """Fit ``tau(q)`` to a power law after g2 fitting is complete.

        Args:
            q_range: ``(q_min, q_max)`` range for selecting data points.
            bounds: Lower and upper parameter bounds for the fit.
            fit_flag: Boolean flags indicating which parameters are free.

        Returns:
            Updated ``fit_summary`` dict (with tau-q fitting keys) or ``None`` if
            no g2 fit summary is available.
        """
        if self.fit_summary is None:
            return

        x = self.fit_summary["q_val"]
        q_slice = (x >= q_range[0]) * (x <= q_range[1])
        x = x[q_slice]

        y = self.fit_summary["fit_val"][q_slice, 0, 1]
        sigma = self.fit_summary["fit_val"][q_slice, 1, 1]

        # filter out those invalid fittings; failed g2 fitting has -1 err
        valid_idx = sigma > 0

        if np.sum(valid_idx) == 0:
            self.fit_summary["tauq_success"] = False
            return

        x = x[valid_idx]
        y = y[valid_idx]
        sigma = sigma[valid_idx]

        # reshape to two-dimension so the fit_with_fixed function works
        y = y.reshape(-1, 1)
        sigma = sigma.reshape(-1, 1)

        # the initial value for typical gel systems
        p0 = [1.0e-7, -2.0]
        fit_x = np.logspace(np.log10(np.min(x) / 1.1), np.log10(np.max(x) * 1.1), 128)

        fit_line, fit_val = fit_with_fixed(power_law, x, y, sigma, bounds, fit_flag, fit_x, p0=p0)

        # fit_line and fit_val are lists with just one element;
        self.fit_summary["tauq_success"] = fit_line[0]["success"]
        self.fit_summary["tauq_q"] = x
        self.fit_summary["tauq_tau"] = np.squeeze(y)
        self.fit_summary["tauq_tau_err"] = np.squeeze(sigma)
        self.fit_summary["tauq_fit_line"] = fit_line[0]
        self.fit_summary["tauq_fit_val"] = fit_val[0]

        return self.fit_summary

    def get_roi_data(self, roi_parameter: dict, phi_num: int = 180) -> tuple[np.ndarray, np.ndarray]:
        """Extract SAXS 1D data within a circular or pie-slice ROI on the detector.

        Supports ``"Pie"`` (angular sector) and ``"Ring"`` (radial annulus) ROI types.

        Args:
            roi_parameter: Dict containing at least ``sl_type`` and either
                ``angle_range`` / ``radius`` and optionally ``dist``.
            phi_num: Number of bins for ring-type ROIs (azimuthal resolution).

        Returns:
            Tuple of ``(x_axis, intensity_array)`` — either *q-intensity* or *phi-intensity*.
        """
        qmap_all = self.compute_qmap()
        qmap = qmap_all["q"]
        pmap = qmap_all["phi"]
        rmap = qmap_all["r_pixel"]

        if roi_parameter["sl_type"] == "Pie":
            pmin, pmax = roi_parameter["angle_range"]
            if pmax < pmin:
                pmax += 360.0
                pmap[pmap < pmin] += 360.0
            proi = np.logical_and(pmap >= pmin, pmap < pmax)
            proi = np.logical_and(proi, (self.mask > 0))
            qmap_idx = np.zeros_like(qmap, dtype=np.uint32)

            index = 1
            qsize = len(self.sqspan) - 1
            for n in range(qsize):
                q0, q1 = self.sqspan[n : n + 2]
                select = (qmap >= q0) * (qmap < q1)
                qmap_idx[select] = index
                index += 1
            qmap_idx = (qmap_idx * proi).ravel()

            saxs_roi = np.bincount(qmap_idx, self.saxs_2d.ravel(), minlength=qsize + 1)
            saxs_nor = np.bincount(qmap_idx, minlength=qsize + 1)
            saxs_nor[saxs_nor == 0] = 1.0
            saxs_roi = saxs_roi * 1.0 / saxs_nor

            # remove the 0th term
            saxs_roi = saxs_roi[1:]

            # set the qmax cutoff
            dist = roi_parameter["dist"]
            # qmax = qmap[int(self.bcy), int(self.bcx + dist)]
            wlength = 12.398 / self.X_energy
            qmax = dist * self.pix_dim_x / self.det_dist * 2 * np.pi / wlength
            saxs_roi[self.sqlist >= qmax] = 0
            saxs_roi[saxs_roi <= 0] = np.nan
            return self.sqlist, saxs_roi

        elif roi_parameter["sl_type"] == "Ring":
            rmin, rmax = roi_parameter["radius"]
            if rmin > rmax:
                rmin, rmax = rmax, rmin
            rroi = np.logical_and(rmap >= rmin, rmap < rmax)
            rroi = np.logical_and(rroi, (self.mask > 0))

            phi_min, phi_max = np.min(pmap[rroi]), np.max(pmap[rroi])
            x = np.linspace(phi_min, phi_max, phi_num)
            delta = (phi_max - phi_min) / phi_num
            index = ((pmap - phi_min) / delta).astype(np.int64)
            index[index == phi_num] = phi_num - 1
            index += 1
            # q_avg = qmap[rroi].mean()
            index = (index * rroi).ravel()

            saxs_roi = np.bincount(index, self.saxs_2d.ravel(), minlength=phi_num + 1)
            saxs_nor = np.bincount(index, minlength=phi_num + 1)
            saxs_nor[saxs_nor == 0] = 1.0
            saxs_roi = saxs_roi * 1.0 / saxs_nor

            # remove the 0th term
            saxs_roi = saxs_roi[1:]
            return x, saxs_roi

    def export_saxs1d(self, roi_list: list[dict], folder: str) -> None:
        """Write SAXS 1D data (ROI-extracted and full) to text files in *folder*.

        Args:
            roi_list: List of ROI parameter dicts (each with ``sl_type``).
            folder: Destination directory for the output ``.txt`` files.

        Returns:
            None. Creates one file per ROI plus a combined ``saxs1d.txt`` file.
        """
        # export ROI
        idx = 0
        for roi in roi_list:
            fname = os.path.join(folder, self.label + "_" + roi["sl_type"] + f"_{idx:03d}.txt")
            idx += 1
            x, y = self.get_roi_data(roi)
            if roi["sl_type"] == "Ring":
                header = "phi(degree) Intensity"
            else:
                header = "q(1/Angstron) Intensity"
            np.savetxt(fname, np.vstack([x, y]).T, header=header)

        # export all saxs1d
        fname = os.path.join(folder, self.label + "_" + "saxs1d.txt")
        Iq, q = self.saxs_1d["Iq"], self.saxs_1d["q"]
        header = "q(1/Angstron) Intensity"
        for n in range(Iq.shape[0] - 1):
            header += f" Intensity_phi{n + 1:03d}"
        np.savetxt(fname, np.vstack([q, Iq]).T, header=header)
