import h5py
import numpy as np
from .aps_8idi import key as key_map
import logging

logger = logging.getLogger(__name__)


class QMapManager:
    def __init__(self):
        self.db = {}

    def get_qmap(self, fname):
        hash_value = get_hash(fname)  # Compute hash
        if hash_value not in self.db:
            qmap = QMap(fname=fname)
            self.db[hash_value] = qmap
        return self.db[hash_value]


class QMap:
    def __init__(self, fname=None, root_key="/xpcs/qmap"):
        self.root_key = root_key
        self.fname = fname
        self.load_dataset()
        self.extent = self.get_detector_extent()
        self.qmap, self.qmap_units = self.compute_qmap()
        self.qbin_labels = self.create_qbin_labels()

    def load_dataset(self):
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
        """
        get the angular extent on the detector, for saxs2d, qmap/display;
        :return:
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

    def get_qmap_at_pos(self, x, y):
        shape = self.mask.shape
        if x < 0 or x >= shape[1] or y < 0 or y >= shape[0]:
            return None
        else:
            qmap, qmap_units = self.qmap, self.qmap_units
            result = ""
            for key in self.qmap.keys():
                if key in ["q", "qx", "qy", "phi", "alpha"]:
                    result += f" {key}={qmap[key][y, x]:.3f} {qmap_units[key]},"
                else:
                    result += f" {key}={qmap[key][y, x]} {qmap_units[key]},"
            return result[:-1]

    def create_qbin_labels(self):
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

    def get_qbin_label(self, qbin: int):
        qbin_absolute = self.dynamic_index_mapping[qbin - 1]
        if qbin_absolute < 0 or qbin_absolute > len(self.qbin_labels):
            return "invalid qbin"
        else:
            return self.qbin_labels[qbin_absolute]

    def get_qbin_in_qrange(self, qrange, zero_based=True):
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
        for qbin_cprs, qbin_nature in zip(index_compressed, index_nature):
            if qselected[qbin_nature]:
                qbin_valid.append(qbin_cprs)

        qbin_valid = np.array(qbin_valid)
        qvalues = qlist.flatten()[qselected]

        if not zero_based:
            qbin_valid += 1
        return qbin_valid, qvalues

    def get_qbinlist_at_qindex(self, qindex, zero_based=True):
        # qindex is zero based; index of dyanmic_map_dim0
        assert self.map_names == ["q", "phi"], "only q-phi map is supported"
        qp_idx = np.ones(self.dynamic_num_pts, dtype=int).flatten() * (-1)
        qp_idx[self.dynamic_index_mapping] = np.arange(len(self.dynamic_index_mapping))
        qp_column_at_qindex = qp_idx.reshape(self.dynamic_num_pts)[qindex]
        qbin_list = [int(idx) for idx in qp_column_at_qindex if idx != -1]
        # if zero_based; it returns the numpy array index in g2[:, xx]
        if not zero_based:
            qbin_list = [idx + 1 for idx in qbin_list]
        return qbin_list

    def compute_qmap(self):
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
        """
        the saxs1d and stability data are compressed. the values of the empty
        static bins are not saved. this function reshapes the array and fills
        the empty bins with nan. nanmean is performed to get the correct
        results;
        """
        assert mode in ("saxs_1d", "stability")
        num_samples = compressed_data_raw.size // self.static_index_mapping.size
        assert num_samples * self.static_index_mapping.size == compressed_data_raw.size
        shape = (num_samples, len(self.sqlist), len(self.splist))
        compressed_data = compressed_data_raw.reshape(num_samples, -1)

        if shape[2] == 1:
            labels = [label]
            avg = compressed_data.reshape(shape[0], -1)
        else:
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
            saxs1d_info = {
                "q": self.sqlist,
                "Iq": saxs1d,
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
    """Extracts the hash from the HDF5 file."""
    with h5py.File(fname, "r") as f:
        return f[root_key].attrs["hash"]


def get_qmap(fname, **kwargs):
    return QMap(fname, **kwargs)


def test_qmap_manager():
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
