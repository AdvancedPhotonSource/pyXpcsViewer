import h5py
import numpy as np
from .aps_8idi import key as key_map
from functools import lru_cache


class QMap:
    def __init__(self, fname=None, root_key='/xpcs/qmap'):
        self.root_key = root_key 
        self.fname = fname
        self.load_dataset()
        self.extent = self.get_detector_extent()
        self.qmap, self.qmap_units = self.compute_qmap()
    
    def load_dataset(self):
        info = {}
        with h5py.File(self.fname, 'r') as f:
            for key in ("mask", "dqmap", "sqmap", "dqlist", "sqlist", 
                        "dplist", "splist", "bcx", "bcy", "X_energy",
                        "static_index_mapping", "dynamic_index_mapping",
                        "pixel_size", "det_dist", "dynamic_num_pts",
                        "static_num_pts"):
                path = key_map['nexus'][key]
                info[key] = f[path][()]
        info['k0'] = 2 * np.pi / (12.398 / info['X_energy'])
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

    def compute_qmap(self):
        shape = self.mask.shape
        v = np.arange(shape[0], dtype=np.uint32) - self.bcy
        h = np.arange(shape[1], dtype=np.uint32) - self.bcx
        vg, hg = np.meshgrid(v, h, indexing='ij')

        r = np.hypot(vg * self.pixel_size, hg * self.pixel_size)
        phi = np.arctan2(hg, vg)

        alpha = np.arctan(r / self.det_dist)
        qr = np.sin(alpha) * self.k0
        qx = qr * np.cos(phi)
        qy = qr * np.sin(phi)
        phi = np.rad2deg(phi)

        # keep phi and q as np.float64 to keep the precision.
        qmap = {
            'phi': phi,
            'alpha': alpha.astype(np.float32),
            'q': qr,
            'qx': qx.astype(np.float32),
            'qy': qy.astype(np.float32),
            'x': hg,
            'y': vg,
        }

        qmap_unit = {
            'phi': 'deg',
            'alpha': 'deg',
            'q': '1/Å',
            'qx': '1/Å',
            'qy': '1/Å',
            'x': 'pixel',
            'y': 'pixel',
        }
        return qmap, qmap_unit
    
    def reshape_phi_analysis(self, compressed_data, label, mode='saxs_1d'):
        """
        the saxs1d and stability data are compressed. the values of the empty 
        static bins are not saved. this function reshapes the array and fills
        the empty bins with nan. nanmean is performed to get the correct
        results;
        """
        assert mode in ('saxs_1d', 'stability')
        num_samples = compressed_data.size // self.static_index_mapping.size
        assert num_samples * self.static_index_mapping.size == compressed_data.size
        shape = (num_samples, len(self.sqlist), len(self.splist))
        compressed_data = compressed_data.reshape(num_samples, -1)

        if shape[2] == 1:
            labels = [self.label]
            avg = compressed_data.reshape(shape[0], -1)
        else:
            full_data = np.full((shape[0], shape[1] * shape[2]), fill_value=np.nan)
            for i in range(num_samples):
                full_data[i, self.static_index_mapping] = compressed_data[i]
            full_data = full_data.reshape(shape)
            avg = np.nanmean(full_data, axis=2)

        if mode == 'saxs_1d':
            assert num_samples == 1, "saxs1d mode only supports one sample"
            if shape[2] > 1:
                saxs1d= np.concatenate([avg[..., None], full_data], axis=-1)
                saxs1d = saxs1d[0].T    # shape: (num_lines + 1, num_q)
                labels = [label + "_%d" % (n + 1) for n in range(shape[2])]
                labels = [label] + labels
            else:
                saxs1d = avg.reshape(1, -1) # shape: (1, num_q)
                labels = [label]
            saxs1d_info = {
                "q": self.sqlist,
                "Iq": saxs1d,
                "phi": self.splist,
                "num_lines": shape[2],
                "labels": labels}
            return saxs1d_info

        elif mode == 'stability':   # saxs1d_segments
            # avg shape is (num_samples, num_q)
            return avg


def get_hash(fname, root_key='/xpcs/qmap'):
    """Extracts the hash from the HDF5 file."""
    with h5py.File(fname, 'r') as f:
        return f[root_key].attrs['hash']


@lru_cache(None)
def _get_qmap_by_hash(hash_value, **kwargs):
    """Caches QMap objects based only on hash_value, ignoring fname."""
    return QMap(**kwargs)  # fname is ignored for caching


def get_qmap(fname):
    """Retrieves a QMap instance, caching based on the file hash."""
    hash_value = get_hash(fname)  # Compute hash
    kwargs = {'fname': fname}
    return _get_qmap_by_hash(hash_value, **kwargs)  # Retrieve from cache


def test_qmap_manager():
    import time
    for i in range(5):
        t0 = time.perf_counter()
        qmap = get_qmap('/net/s8iddata/export/8-id-ECA/MQICHU/projects/2025_0223_boost_corr_nexus/cluster_results1/Z1113_Sanjeeva-h60_a0004_t0600_f008000_r00003_results.hdf')
        qmap = get_qmap('/net/s8iddata/export/8-id-ECA/MQICHU/projects/2025_0223_boost_corr_nexus/cluster_results1/Z1113_Sanjeeva-h60_a0004_t0600_f008000_r00003_results2.hdf')
        qmap = get_qmap('/net/s8iddata/export/8-id-ECA/MQICHU/projects/2025_0223_boost_corr_nexus/cluster_results1/Z1113_Sanjeeva-h60_a0004_t0600_f008000_r00003_results3.hdf')
        t1 = time.perf_counter()
        print('time: ', t1 - t0)


if __name__ == '__main__':
    test_qmap_manager()