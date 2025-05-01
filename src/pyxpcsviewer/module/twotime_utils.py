import h5py
import numpy as np
from functools import lru_cache
from multiprocessing import Pool
from ..fileIO.aps_8idi import key as key_map

key_map = key_map["nexus"]


def correct_diagonal_c2(c2_mat):
    size = c2_mat.shape[0]
    side_band = c2_mat[(np.arange(size - 1), np.arange(1, size))]
    diag_val = np.zeros(size)
    diag_val[:-1] += side_band
    diag_val[1:] += side_band
    norm = np.ones(size)
    norm[1:-1] = 2
    c2_mat[np.diag_indices(size)] = diag_val / norm
    return c2_mat


def read_single_c2(args):
    full_path, index_str, max_size, correct_diag = args
    c2_prefix = key_map["c2_prefix"]
    with h5py.File(full_path, "r") as f:
        c2_half = f[f"{c2_prefix}/{index_str}"][()]
        c2 = c2_half + np.transpose(c2_half)
        diag_idx = np.diag_indices(c2_half.shape[0], ndim=2)
        c2[diag_idx] /= 2
        sampling_rate = 1
        if max_size > 0 and max_size < c2.shape[0]:
            sampling_rate = (c2.shape[0] + max_size - 1) // max_size
            c2 = c2[::sampling_rate, ::sampling_rate]
    if correct_diag:
        c2 = correct_diagonal_c2(c2)
    return c2, sampling_rate


@lru_cache(maxsize=16)
def get_all_c2_from_hdf(
    full_path,
    dq_selection=None,
    max_c2_num=32,
    max_size=512,
    num_workers=12,
    correct_diag=True,
):
    # t0 = time.perf_counter()
    idx_toload = []
    c2_prefix = key_map["c2_prefix"]

    with h5py.File(full_path, "r") as f:
        if c2_prefix not in f:
            return None
        idxlist = list(f[c2_prefix])
        for idx in idxlist:
            if dq_selection is not None and int(idx[4:]) not in dq_selection:
                continue
            else:
                idx_toload.append(idx)
            if max_c2_num > 0 and len(idx_toload) > max_c2_num:
                break

    args_list = [(full_path, index, max_size, correct_diag) for index in idx_toload]
    if len(args_list) >= 6:
        with Pool(min(len(args_list), num_workers)) as p:
            result = p.map(read_single_c2, args_list)
    else:
        result = [read_single_c2(args) for args in args_list]

    c2_all = np.array([res[0] for res in result])
    sampling_rate_all = set([res[1] for res in result])
    assert (
        len(sampling_rate_all) == 1
    ), f"Sampling rate not consistent {sampling_rate_all}"
    sampling_rate = list(sampling_rate_all)[0]
    c2_result = {
        "c2_all": c2_all,
        "delta_t": 1.0 * sampling_rate,  # put absolute time in xpcs_file
        "acquire_period": 1.0,
        "dq_selection": dq_selection,
    }
    return c2_result


@lru_cache(maxsize=16)
def get_single_c2_from_hdf(
    full_path, selection=0, max_size=512, t0=1, correct_diag=True
):
    c2_prefix = key_map["c2_prefix"]
    with h5py.File(full_path, "r") as f:
        if c2_prefix not in f:
            return None
        idxstr = list(f[c2_prefix])[selection]

    c2_mat, sampling_rate = read_single_c2((full_path, idxstr, max_size, correct_diag))
    g2_partials = get_c2_g2partials_from_hdf(full_path)
    c2_result = {
        "c2_mat": c2_mat,
        "delta_t": t0 * sampling_rate,  # put absolute time in xpcs_file
        "acquire_period": t0,
        "dq_selection": selection,
        "g2_full": g2_partials["g2_full"][selection],
        "g2_partial": g2_partials["g2_partial"][selection],
    }
    return c2_result


@lru_cache(maxsize=16)
def get_c2_g2partials_from_hdf(full_path):
    # t0 = time.perf_counter()
    c2_prefix = key_map["c2_prefix"]
    g2_full_key = key_map["c2_g2"]  # Dataset {5000, 25}
    g2_partial_key = key_map["c2_g2_segments"]  # Dataset {1000, 5, 25}

    with h5py.File(full_path, "r") as f:
        if c2_prefix not in f:
            return None
        g2_full = f[g2_full_key][()]
        g2_partial = f[g2_partial_key][()]

    g2_full = np.swapaxes(g2_full, 0, 1)
    g2_partial = np.swapaxes(g2_partial, 0, 2)

    g2_partials = {
        "g2_full": g2_full,
        "g2_partial": g2_partial,
    }
    return g2_partials


def get_c2_stream(full_path, max_size=-1):
    """Returns (idxlist, generator) where the generator yields C2 streams."""
    c2_prefix = key_map["c2_prefix"]

    with h5py.File(full_path, "r") as f:
        if c2_prefix in f:
            idxlist = list(f[c2_prefix])  # Extract the list of indices
        else:
            idxlist = []  # Return empty list if prefix is missing

    def generator():
        for idx in idxlist:  # Use idxlist for iteration
            c2, sampling_rate = get_single_c2((full_path, idx, max_size))
            yield int(idx[3:]), c2

    return idxlist, generator()
