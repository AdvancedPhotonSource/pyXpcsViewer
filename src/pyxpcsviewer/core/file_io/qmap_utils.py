# Copyright © UChicago Argonne LLC
# See LICENSE file for details
import logging

import h5py
import numpy as np

from .aps_8idi import key as key_map

logger = logging.getLogger(__name__)


class QMapManager:
    """Cache manager for :class:`QMap` objects keyed by content hash."""

    def __init__(self):
        """Initialize an empty cache dictionary."""
        self.db = {}

    def get_qmap(self, fname: str) -> "QMap":
        """Return a :class:`QMap` for *fname*, loading from disk only once.

        Args:
            fname: Path to the HDF5 result file.

        Returns:
            A :class:`QMap` instance (cached by content hash).
        """
        hash_value = get_hash(fname)  # Compute hash
        if hash_value not in self.db:
            qmap = QMap(fname=fname)
            self.db[hash_value] = qmap
        return self.db[hash_value]


class QMap:
    """Detector Q-map extracted from a NeXus HDF5 result file.

    Holds masks, scattering maps, beam center, pixel geometry, and
    computed q-value arrays (qx, qy, phi, alpha).
    """

    # Populated dynamically by load_dataset() (self.__dict__.update(info));
    # declared here so static type checkers/IDEs know these attributes exist.
    mask: np.ndarray
    dqmap: np.ndarray
    sqmap: np.ndarray
    dqlist: np.ndarray
    sqlist: np.ndarray
    dplist: np.ndarray
    splist: np.ndarray
    bcx: float
    bcy: float
    X_energy: float
    static_index_mapping: np.ndarray
    dynamic_index_mapping: np.ndarray
    pixel_size: float
    det_dist: float
    dynamic_num_pts: np.ndarray
    static_num_pts: np.ndarray
    map_names: list[str]
    map_units: list[str]
    k0: float
    is_loaded: bool

    def __init__(self, fname=None, root_key="/xpcs/qmap"):
        """Initialize and load Q-map datasets from *fname*.

        Args:
            fname: Path to the HDF5 result file.
            root_key: HDF5 group path for Q-map data.
        """
        self.root_key = root_key
        self.fname = fname
        self.load_dataset()
        self.extent = self.get_detector_extent()
        self.qmap, self.qmap_units = self.compute_qmap()
        self.qbin_labels = self.create_qbin_labels()

    def load_dataset(self) -> dict:
        """Read all Q-map datasets from the HDF5 file into instance attributes.

        Returns:
            Dict mapping dataset names to their loaded values.
        """
        info = {}
        with h5py.File(self.fname, "r") as f:
            for key in (
                "mask",
                "dqmap",
                "sqmap",
                "dqlist",
                "sqlist",
                "dplist",
                "splist",
                "bcx",
                "bcy",
                "X_energy",
                "static_index_mapping",
                "dynamic_index_mapping",
                "pixel_size",
                "det_dist",
                "dynamic_num_pts",
                "static_num_pts",
                "map_names",
                "map_units",
            ):
                path = key_map["nexus"][key]
                info[key] = f[path][()]
        info["k0"] = 2 * np.pi / (12.398 / info["X_energy"])
        info["map_names"] = [item.decode("utf-8") for item in info["map_names"]]
        info["map_units"] = [item.decode("utf-8") for item in info["map_units"]]
        self.__dict__.update(info)
        self.is_loaded = True
        return info

    def get_detector_extent(self):
        """Return the angular extent on the detector for SAXS-2D / Q-map display.

        Returns:
            Tuple of ``(qx_min, qx_max, qy_min, qy_max)`` covering the detector area.
        """
        shape = self.mask.shape
        pix2q_x = self.pixel_size / self.det_dist * self.k0
        pix2q_y = self.pixel_size / self.det_dist * self.k0

        qx_min = (0 - self.bcx) * pix2q_x
        qx_max = (shape[1] - self.bcx) * pix2q_x
        qy_min = (0 - self.bcy) * pix2q_y
        qy_max = (shape[0] - self.bcy) * pix2q_y

        extent = (qx_min, qx_max, qy_min, qy_max)
        return extent

    def get_qmap_at_pos(self, x: int, y: int) -> str | None:
        """Return a formatted string of Q-map values at detector pixel *(x, y)*.

        Args:
            x: Column index in the detector mask.
            y: Row index in the detector mask.

        Returns:
            Formatted string of q-value pairs, or ``None`` if out of bounds.
        """
        shape = self.mask.shape
        if x < 0 or x >= shape[1] or y < 0 or y >= shape[0]:
            return None
        else:
            qmap, qmap_units = self.qmap, self.qmap_units
            result = ""
            for key in self.qmap.keys():
                if key in ["q", "qy", "phi", "alpha", "x", "y"]:
                    result += f" {key}={qmap[key][y, x]:.3f} {qmap_units[key]},"
                elif key in ["qx", "qr"]:
                    result += f" {key}={qmap[key][y, x]:.6f} {qmap_units[key]},"
                else:
                    result += f" {key}={qmap[key][y, x]} {qmap_units[key]},"
            return result[:-1]

    def create_qbin_labels(self) -> list[str]:
        """Generate human-readable labels for each Q-bin from dynamic/static lists.

        Returns:
            List of label strings (single or double-axis depending on configuration).
        """
        if self.map_names == ["q", "phi"]:
            label_0 = [f"q={x:.5f} {self.map_units[0]}" for x in self.dqlist]
            label_1 = [f"φ={y:.1f} {self.map_units[1]}" for y in self.dplist]
        elif self.map_names == ["x", "y"]:
            label_0 = [f"x={x:.1f} {self.map_units[0]}" for x in self.dqlist]
            label_1 = [f"y={y:.1f} {self.map_units[1]}" for y in self.dplist]
        else:
            name0, name1 = self.map_names
            label_0 = [f"{name0}={x:.3f} {self.map_units[0]}" for x in self.dqlist]
            label_1 = [f"{name1}={y:.3f} {self.map_units[1]}" for y in self.dplist]

        if self.dynamic_num_pts[1] == 1:
            return label_0
        else:
            combined_list = []
            for item_a in label_0:
                for item_b in label_1:
                    combined_list.append(f"{item_a}, {item_b}")
            return combined_list

    def get_qbin_label(self, qbin: int, append_qbin: bool = False) -> str:
        """Return the label string for a given Q-bin index.

        Args:
            qbin: 1-based Q-bin index.
            append_qbin: If ``True``, prepend ``"qbin=N, "`` to the label.

        Returns:
            Formatted label string, or ``"invalid qbin"`` if out of range.
        """
        qbin_absolute = self.dynamic_index_mapping[qbin - 1]
        if qbin_absolute < 0 or qbin_absolute > len(self.qbin_labels):
            return "invalid qbin"
        else:
            label = self.qbin_labels[qbin_absolute]
            if append_qbin:
                label = f"qbin={qbin}, {label}"
            return label

    def get_qbin_in_qrange(
        self, qrange: tuple[float, float] | None, zero_based: bool = True
    ) -> tuple[np.ndarray, np.ndarray]:
        """Return Q-bin indices and corresponding q-values within a Q-range.

        Args:
            qrange: ``(qmin, qmax)`` pair, or ``None`` to select all bins.
            zero_based: If ``True``, return zero-based numpy indices.

        Returns:
            Tuple of ``(valid_qbin_indices, q_values)``, where both are arrays.
        """
        if self.map_names[0] != "q":
            logger.info("qrange is only supported for qmaps with 0-axis as q")
            qrange = None

        qlist = np.tile(self.dqlist[:, np.newaxis], self.dynamic_num_pts[1])
        if qrange is None:
            qselected = np.ones_like(qlist, dtype=bool)
        else:
            qselected = (qlist >= qrange[0]) * (qlist <= qrange[1])
        qselected = qselected.flatten()
        if np.sum(qselected) == 0:
            qselected = np.ones_like(qlist, dtype=bool).flatten()

        qbin_valid = []
        index_compressed = np.arange(len(self.dynamic_index_mapping))
        index_nature = self.dynamic_index_mapping
        for qbin_cprs, qbin_nature in zip(index_compressed, index_nature, strict=False):
            if qselected[qbin_nature]:
                qbin_valid.append(qbin_cprs)

        qbin_valid = np.array(qbin_valid)
        qvalues = qlist.flatten()[qselected]

        if not zero_based:
            qbin_valid += 1
        return qbin_valid, qvalues

    def get_qbinlist_at_qindex(self, qindex: int, zero_based: bool = True) -> list[int]:
        """Return Q-bin indices corresponding to a single dynamic-axis column.

        Args:
            qindex: Zero-based index into the dynamic axis.
            zero_based: If ``False``, return 1-based indices.

        Returns:
            List of valid Q-bin indices for that column.
        """
        # qindex is zero based; index of dyanmic_map_dim0
        # assert self.map_names == ["q", "phi"], "only q-phi map is supported"
        qp_idx = np.ones(self.dynamic_num_pts, dtype=int).flatten() * (-1)
        qp_idx[self.dynamic_index_mapping] = np.arange(len(self.dynamic_index_mapping))
        qp_column_at_qindex = qp_idx.reshape(self.dynamic_num_pts)[qindex]
        qbin_list = [int(idx) for idx in qp_column_at_qindex if idx != -1]
        # if zero_based; it returns the numpy array index in g2[:, xx]
        if not zero_based:
            qbin_list = [idx + 1 for idx in qbin_list]
        return qbin_list

    def get_cropped_qmap(self, target: str = "dqmap", enabled: bool = True) -> np.ndarray:
        """Return the cropped Q-map (or S-map) array limited to valid detector pixels.

        Args:
            target: Either ``"dqmap"`` or ``"sqmap"``.
            enabled: If ``True``, crop to the bounding box of non-zero entries.

        Returns:
            2D Numpy array cropped to the active region.
        """
        assert target in ["dqmap", "sqmap"]
        obj = getattr(self, target).copy()
        if enabled:
            idx = np.nonzero(obj >= 1)
            sl_v = slice(np.min(idx[0]), np.max(idx[0]) + 1)
            sl_h = slice(np.min(idx[1]), np.max(idx[1]) + 1)
            obj = obj[sl_v, sl_h]
        return obj

    def get_display_dqmap(
        self,
        auto_crop: bool = True,
        highlight_xy: tuple[int, int] | None = None,
        selection: int | None = None,
    ) -> tuple[np.ndarray, int | None]:
        """Build a display-ready dqmap, optionally highlighting one Q-bin.

        Args:
            auto_crop: Crop the Q-map to its active bounding box.
            highlight_xy: Pixel coordinates whose q-bin will be highlighted.
            selection: Direct q-bin index to highlight (mutually exclusive with *highlight_xy*).

        Returns:
            Tuple of ``(dqmap_display, selected_qbin_index)``.
        """
        # emphasize the beamstop region which has qindex = 0;
        dqmap = self.get_cropped_qmap(target="dqmap", enabled=auto_crop)

        qindex_max = np.max(dqmap)
        dqlist = np.unique(dqmap)[1:]
        dqmap = dqmap.astype(np.float32)
        dqmap[dqmap == 0] = np.nan

        dqmap_disp = np.flipud(np.copy(dqmap))

        dq_bin = None
        if highlight_xy is not None:
            x, y = highlight_xy
            if x >= 0 and y >= 0 and x < dqmap.shape[1] and y < dqmap.shape[0]:
                dq_bin = dqmap_disp[y, x]
        elif selection is not None:
            dq_bin = dqlist[selection]

        if dq_bin is not None and dq_bin != np.nan and dq_bin > 0:
            # highlight the selected qbin if it's valid
            dqmap_disp[dqmap_disp == dq_bin] = qindex_max + 1
            selection = np.where(dqlist == dq_bin)[0][0]
        else:
            selection = None
        return dqmap_disp, selection

    def compute_qmap(self) -> tuple[dict, dict]:
        """Compute q-value arrays from detector geometry (pixel positions, beam center, energy).

        Returns:
            Tuple of ``(qmap_dict, unit_dict)`` containing per-pixel q, qx, qy, phi, alpha
            and their corresponding units.
        """
        shape = self.mask.shape
        v = np.arange(shape[0], dtype=np.uint32) - self.bcy
        h = np.arange(shape[1], dtype=np.uint32) - self.bcx
        vg, hg = np.meshgrid(v, h, indexing="ij")

        r = np.hypot(vg, hg) * self.pixel_size
        phi = np.arctan2(vg, hg) * (-1)
        alpha = np.arctan(r / self.det_dist)

        qr = np.sin(alpha) * self.k0
        qx = qr * np.cos(phi)
        qy = qr * np.sin(phi)
        phi = np.rad2deg(phi)

        # keep phi and q as np.float64 to keep the precision.
        qmap = {
            "phi": phi,
            "alpha": alpha.astype(np.float32),
            "q": qr,
            "qx": qx.astype(np.float32),
            "qy": qy.astype(np.float32),
            "x": hg,
            "y": vg,
        }

        qmap_unit = {
            "phi": "°",
            "alpha": "°",
            "q": "Å⁻¹",
            "qx": "Å⁻¹",
            "qy": "Å⁻¹",
            "x": "pixel",
            "y": "pixel",
        }
        return qmap, qmap_unit

    def reshape_phi_analysis(self, compressed_data_raw, label, mode="saxs_1d"):
        """Reshape compressed SAXS-1D / stability data and fill empty static bins with NaN.

        The SAXS-1D and stability data are compressed by omitting empty static bins.
        This function expands the array back to the full shape (filling empty bins
        with NaN) and computes the NaN-mean for correct results.

        Args:
            compressed_data_raw: Flattened/compressed data array from the HDF5 file.
            label: Label string for the source dataset.
            mode: One of ``"saxs_1d"`` or ``"stability"``.
        """
        assert mode in ("saxs_1d", "stability")
        num_samples = compressed_data_raw.size // self.static_index_mapping.size
        assert num_samples * self.static_index_mapping.size == compressed_data_raw.size
        shape = (num_samples, len(self.sqlist), len(self.splist))
        compressed_data = compressed_data_raw.reshape(num_samples, -1)

        # recover the full data with nan for empty static bins
        full_data = np.full((shape[0], shape[1] * shape[2]), fill_value=np.nan)
        for i in range(num_samples):
            full_data[i, self.static_index_mapping] = compressed_data[i]
        full_data = full_data.reshape(shape)
        avg = np.nanmean(full_data, axis=2)

        if mode == "saxs_1d":
            assert num_samples == 1, "saxs1d mode only supports one sample"
            if shape[2] > 1:
                saxs1d = np.concatenate([avg[..., None], full_data], axis=-1)
                saxs1d = saxs1d[0].T  # shape: (num_lines + 1, num_q)
                labels = [label + "_%d" % (n + 1) for n in range(shape[2])]
                labels = [label] + labels
            else:
                saxs1d = avg.reshape(1, -1)  # shape: (1, num_q)
                labels = [label]
            if self.sqlist.size != saxs1d.shape[1]:
                logger.warning(
                    "sqlist size (%d) does not match saxs1d shape (%d), truncating to min size",
                    self.sqlist.size,
                    saxs1d.shape[1],
                )
            max_size = min(self.sqlist.size, saxs1d.shape[1])
            saxs1d_info = {
                "q": self.sqlist[0:max_size],
                "Iq": saxs1d[:, 0:max_size],
                "phi": self.splist,
                "num_lines": shape[2],
                "labels": labels,
                "data_raw": compressed_data_raw,
            }
            return saxs1d_info

        elif mode == "stability":  # saxs1d_segments
            # avg shape is (num_samples, num_q)
            return avg


def get_hash(fname, root_key="/xpcs/qmap"):
    """Compute and return the content hash for Q-map caching.

    Args:
        fname: Path to the HDF5 file.
        root_key: HDF5 group path for the Q-map data.

    Returns:
        The hash attribute string stored in the Q-map group.
    """
    with h5py.File(fname, "r") as f:
        return f[root_key].attrs["hash"]


def get_qmap(fname: str, **kwargs) -> "QMap":
    """Convenience function to create and return a :class:`QMap`.

    Args:
        fname: Path to the HDF5 result file.
        **kwargs: Additional keyword arguments forwarded to :class:`QMap`.

    Returns:
        A new :class:`QMap` instance.
    """
    return QMap(fname, **kwargs)


def test_qmap_manager():
    """Smoke-test: load three Q-maps and print elapsed time."""
    import time

    for i in range(5):
        t0 = time.perf_counter()
        qmap = get_qmap(
            "/net/s8iddata/export/8-id-ECA/MQICHU/projects/2025_0223_boost_corr_nexus/cluster_results1/Z1113_Sanjeeva-h60_a0004_t0600_f008000_r00003_results.hdf"
        )
        qmap = get_qmap(
            "/net/s8iddata/export/8-id-ECA/MQICHU/projects/2025_0223_boost_corr_nexus/cluster_results1/Z1113_Sanjeeva-h60_a0004_t0600_f008000_r00003_results2.hdf"
        )
        qmap = get_qmap(
            "/net/s8iddata/export/8-id-ECA/MQICHU/projects/2025_0223_boost_corr_nexus/cluster_results1/Z1113_Sanjeeva-h60_a0004_t0600_f008000_r00003_results3.hdf"
        )
        t1 = time.perf_counter()
        print("time: ", t1 - t0)


if __name__ == "__main__":
    test_qmap_manager()
