import numpy as np
import h5py



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
    """
    Check if the G2 field exists in the specified HDF5 file.

    Parameters
    ----------
    fname : str
        The path to the HDF5 file.

    Returns
    -------
    bool
        True if the G2 field exists, False otherwise.
    """
    with h5py.File(fname, "r", libver="latest") as f:
        return keymap["G2"] in f


def average_by_qindex(idx_map, arr):
    """
    Calculate the average of an array based on a Q-index map.

    Parameters
    ----------
    idx_map : ndarray
        An index map where each value represents a Q-index.
    arr : ndarray
        A 2D array of values to be averaged. The second dimension size
        must match the size of the flattened index map.

    Returns
    -------
    ndarray
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


def compute_g2(sqmap, dqmap, G2):
    """
    Compute g2 and its error using static and dynamic ROI maps.

    Parameters
    ----------
    sqmap : ndarray
        The static ROI map.
    dqmap : ndarray
        The dynamic ROI map.
    G2 : ndarray
        The unnormalized G2 data with shape (n_delays, n_channels, img_v, img_h).

    Returns
    -------
    tuple of ndarray
        - g2: The normalized g2 values with shape (n_delays, n_dq).
        - g2_err: The standard deviation error of g2.
    """
    # G2 is (N_delay x 3 x IMG_V x IMG_H)
    shape = G2.shape  #
    n_delays, n_channels, img_v, img_h = shape
    G2 = G2.reshape(n_delays, n_channels, -1)
    sqmap = sqmap.ravel()
    dqmap = dqmap.ravel()

    IP_IF = G2[:, 1] * G2[:, 2]
    IP_IF[IP_IF <= 0] = 1.0
    g2_pixel = G2[:, 0] / IP_IF

    n_sq = np.max(sqmap)
    n_dq = np.max(dqmap)
    G2_sq = average_by_qindex(sqmap, G2.reshape(n_delays * n_channels, -1))
    G2_sq = G2_sq.reshape(n_delays, n_channels, n_sq)

    IP_IF_sq = G2_sq[:, 1] * G2_sq[:, 2]
    IP_IF_sq[IP_IF_sq == 0] = 1.0
    g2_sq = G2_sq[:, 0] / IP_IF_sq

    g2 = np.zeros((n_delays, n_dq))
    g2_err = np.zeros_like(g2)

    for idx in range(1, n_dq + 1):
        roi_dq = dqmap == idx
        temp = g2_pixel[:, roi_dq]

        if temp.shape[1] > 0:
            g2_err[:, idx - 1] = np.std(temp, axis=1) / np.sqrt(temp.shape[1])
            # the sqmap index - 1 gives the index in the G2q
            # roi = sqmap[idx_corr].long().unique() - 1
            # [1, 2, 3, 4]
            roi_sq = np.unique(sqmap[roi_dq]) - 1
            g2[:, idx - 1] = np.mean(g2_sq[:, roi_sq], axis=1)

    return g2, g2_err


def apply_new_G2_to_file(fname, avg_result):
    """
    Update an HDF5 file with newly computed G2, g2, and g2_err data.

    Parameters
    ----------
    fname : str
        The path to the HDF5 file to be updated.
    avg_result : dict
        A dictionary containing the results, with "G2" as a required key.
        The function will also add "g2" and "g2_err" to this dictionary.

    Returns
    -------
    str
        The path to the updated HDF5 file.
    """
    config = {}
    with h5py.File(fname, "r") as f:
        for key in ["sqmap", "dqmap"]:
            config[key] = f[keymap[key]][()]
    g2, g2_err = compute_g2(config["sqmap"], config["dqmap"], avg_result["G2"])
    avg_result["g2"] = g2
    avg_result["g2_err"] = g2_err

    with h5py.File(fname, "a") as f:
        for key, data in avg_result.items():
            field = keymap[key]
            if field in f:
                del f[field]

            if key != "G2":
                compression = "lzf" if key == "G2" else None
                f.create_dataset(field, data=data, compression=compression)
    return fname


def test(fname):
    """
    Test the g2 computation by comparing it with existing results in a file.

    Parameters
    ----------
    fname : str
        The path to the HDF5 file containing the test data.
    """
    result = {}
    with h5py.File(fname, "r") as f:
        for key, field in keymap.items():
            result[key] = f[field][()]
            print(key, result[key].shape)

    g2, g2_err = compute_g2(result["sqmap"], result["dqmap"], result["G2"])
    print(np.max(np.abs(result["g2"] - g2)))
    print(np.max(np.abs(result["g2_err"] - g2_err)))

    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(6, 4, figsize=(12, 8))
    ax = ax.flatten()
    for n in range(min(len(ax), g2.shape[1])):
        ax[n].plot(g2[:, n])
        ax[n].plot(result["g2"][:, n])
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    fname = "./data/Ia0069_PC10P-15wv-35C_a0006_f004000_r00350_results.hdf"
    test(fname)
