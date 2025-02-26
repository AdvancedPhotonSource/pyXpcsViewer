import h5py
import numpy as np
from functools import lru_cache
from multiprocessing import Pool
from ..fileIO.aps_8idi import key as key_map

key_map = key_map['nexus']


def get_single_c2(args):
    full_path, index_str, max_size = args
    c2_prefix = key_map['c2_prefix']
    with h5py.File(full_path, "r") as f:
        c2_half = f[f"{c2_prefix}/{index_str}"][()]
        c2 = c2_half + np.transpose(c2_half)
        diag_idx = np.diag_indices(c2_half.shape[0], ndim=2)
        c2[diag_idx] /= 2
        sampling_rate = 1
        if max_size > 0 and max_size < c2.shape[0]:
            sampling_rate = (c2.shape[0] + max_size - 1) // max_size
            c2 = c2[::sampling_rate, ::sampling_rate] 
    return c2, sampling_rate


@lru_cache(maxsize=16)
def get_c2_from_hdf_fast(full_path, dq_selection=None, max_c2_num=32,
                              max_size=512, num_workers=12):
    # t0 = time.perf_counter()
    idx_toload = []
    c2_prefix = key_map['c2_prefix']
    g2_full_key = key_map['c2_g2']                 # Dataset {5000, 25}
    g2_partial_key = key_map['c2_g2_segments']     # Dataset {1000, 5, 25} 
    acquire_period_key = key_map['t0']

    with h5py.File(full_path, "r") as f:
        if c2_prefix not in f:
            return None
        idxlist = list(f[c2_prefix])
        acquire_period = f[acquire_period_key][()]
        g2_full = f[g2_full_key][()]
        g2_partial = f[g2_partial_key][()]
        for idx in idxlist:
            if dq_selection is not None and int(idx[4:]) not in dq_selection:
                continue
            else:
                idx_toload.append(idx)
            if max_c2_num > 0 and len(idx_toload) > max_c2_num:
                break
    args_list = [(full_path, index, max_size) for index in idx_toload]
    g2_full = np.swapaxes(g2_full, 0, 1)
    g2_partial = np.swapaxes(g2_partial, 0, 2)

    if len(args_list) >= 6:
        with Pool(min(len(args_list), num_workers)) as p:
            result = p.map(get_single_c2, args_list)
    else:
        result = [get_single_c2(args) for args in args_list]

    c2_all = np.array([res[0] for res in result])
    sampling_rate_all = set([res[1] for res in result])
    assert len(sampling_rate_all) == 1, f"Sampling rate not consistent {sampling_rate_all}"
    sampling_rate = list(sampling_rate_all)[0]
    c2_result = {
        "c2_all": c2_all,
        "g2_full": g2_full,
        "g2_partial": g2_partial,
        "delta_t": acquire_period * sampling_rate,
        "acquire_period": acquire_period,
        "dq_selection": dq_selection,
    }
    return c2_result
