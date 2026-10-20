# Copyright © UChicago Argonne LLC
# See LICENSE file for details
import logging
from typing import Any

import h5py
import numpy as np

from .aps_8idi import key as hdf_key

logger = logging.getLogger(__name__)


def put(save_path, result, ftype="nexus", mode="raw"):
    """Save result data to an HDF5 file.

    Args:
        save_path: Path to save the result file.
        result: Dictionary of datasets to save.
        ftype: File type — ``"nexus"`` or ``"aps_8idi"``.
        mode: ``"raw"`` uses the literal key; ``"alias"`` resolves via the key map.
    """
    with h5py.File(save_path, "a") as f:
        for key, val in result.items():
            if mode == "alias":
                key = hdf_key[ftype][key]
            if key in f:
                del f[key]
            if isinstance(val, np.ndarray) and val.ndim == 1:
                val = np.reshape(val, (1, -1))
            f[key] = val
        return


def get_abs_cs_scale(fname: str, ftype: str = "nexus") -> float | None:
    """Retrieve the absolute cross-section scaling factor from an HDF5 file.

    Args:
        fname: Path to the HDF5 file.
        ftype: File format — ``"nexus"`` or ``"aps_8idi"``.

    Returns:
        The scaling factor as a float, or ``None`` if not present.
    """
    key = hdf_key[ftype]["abs_cross_section_scale"]
    with h5py.File(fname, "r") as f:
        if key not in f:
            return None
        else:
            return float(f[key][()])


def read_metadata_to_dict(file_path):
    """Read an HDF5 file and load its contents into a nested dictionary.

    Args:
        file_path: Path to the HDF5 file.

    Returns:
        A nested dictionary containing datasets as NumPy arrays.
    """

    def recursive_read(h5_group, target_dict):
        """Recursively reads groups and datasets into the dictionary."""
        for key in h5_group:
            obj = h5_group[key]
            if isinstance(obj, h5py.Dataset):
                val = obj[()]
                if type(val) in [np.bytes_, bytes]:
                    val = val.decode()
                units = obj.attrs.get("units", None)
                if units is not None:
                    units = units.decode() if isinstance(units, bytes) else units
                    target_dict[key + f" ({units})"] = val
                else:
                    target_dict[key] = val
            elif isinstance(obj, h5py.Group):
                target_dict[key] = {}
                recursive_read(obj, target_dict[key])

    data_dict = {}
    groups = [
        "/entry/instrument",
        "/xpcs/multitau/config",
        "/xpcs/twotime/config",
        "/entry/sample",
        "/entry/user",
    ]
    with h5py.File(file_path, "r") as hdf_file:
        for group in groups:
            if group in hdf_file:
                data_dict[group] = {}
                recursive_read(hdf_file[group], data_dict[group])
    return data_dict


def get(fname, fields, mode="raw", ret_type="dict", ftype="nexus", optional=()):
    """Retrieve field values from an HDF5 result file.

    Args:
        fname: Path to the HDF5 file.
        fields: List of key names to retrieve.
        mode: ``"raw"`` reads the literal key; ``"alias"`` resolves via the
            key map in ``aps_8idi``.
        ret_type: ``"dict"`` returns a dict keyed by field name; ``"list"``
            returns a flat list of values.
        ftype: Expected file type for the reader backend.
        optional: Subset of *fields* that may be absent from the file; a missing
            one comes back as ``None`` instead of raising.

    Returns:
        Dictionary or list of field values depending on *ret_type*.
    """
    assert mode in ["raw", "alias"], "mode not supported"
    assert ret_type in ["dict", "list"], "ret_type not supported"

    ret: dict[str, Any] = {}
    with h5py.File(fname, "r") as HDF_Result:
        for key in fields:
            path = hdf_key[ftype][key] if mode == "alias" else key
            if path not in HDF_Result:
                if key in optional:
                    logger.debug("optional field not found: %s", path)
                    ret[key] = None
                    continue
                logger.error("path to field not found: %s", path)
                raise ValueError("key not found: %s:%s", key, path)
            else:
                val = HDF_Result.get(path)[()]
            if key in ["saxs_2d"] and val.ndim == 3:  # saxs_2d is in [1xNxM] format
                val = val[0]
            # converts bytes to unicode;
            if type(val) in [np.bytes_, bytes]:
                val = val.decode()
            if isinstance(val, np.ndarray) and val.shape == (1, 1):
                val = val.item()
            ret[key] = val

    if ret_type == "dict":
        return ret
    elif ret_type == "list":
        return [ret[key] for key in fields]


def get_slice(fname: str, field: str, index: Any, mode: str = "alias", ftype: str = "nexus") -> np.ndarray:
    """Read a single slice of a dataset without materializing the whole array.

    Large fields such as the unnormalized ``G2`` cube are hundreds of MB; the
    viewer usually needs one 2D detector frame out of it, so let HDF5 do the
    partial read instead of loading everything and indexing in memory.

    Args:
        fname: Path to the HDF5 file.
        field: Key name, resolved via the key map when *mode* is ``"alias"``.
        index: Anything h5py accepts as an index expression, e.g. ``(3, 0)``.
        mode: ``"raw"`` reads the literal key; ``"alias"`` resolves via ``aps_8idi``.
        ftype: Expected file type for the reader backend.

    Returns:
        The requested slice as a numpy array.

    Raises:
        ValueError: If the field is missing from the file.
    """
    path = hdf_key[ftype][field] if mode == "alias" else field
    with h5py.File(fname, "r") as f:
        if path not in f:
            logger.error("path to field not found: %s", path)
            raise ValueError(f"key not found: {field}:{path}")
        return np.asarray(f[path][index])


def get_shape(fname: str, field: str, mode: str = "alias", ftype: str = "nexus") -> tuple[int, ...] | None:
    """Return the shape of a dataset without reading its contents.

    Args:
        fname: Path to the HDF5 file.
        field: Key name, resolved via the key map when *mode* is ``"alias"``.
        mode: ``"raw"`` reads the literal key; ``"alias"`` resolves via ``aps_8idi``.
        ftype: Expected file type for the reader backend.

    Returns:
        The dataset shape tuple, or ``None`` if the field is absent.
    """
    path = hdf_key[ftype][field] if mode == "alias" else field
    with h5py.File(fname, "r") as f:
        if path not in f:
            return None
        return f[path].shape


def get_analysis_type(fname, ftype="nexus"):
    """Determine the analysis type(s) stored in the file.

    Args:
        fname: Path to the HDF5 file.
        ftype: File type — ``"nexus"`` or ``"aps_8idi"``.

    Returns:
        Tuple containing ``"Twotime"`` or ``"Multitau"``, or both.
    """
    c2_prefix = hdf_key[ftype]["c2_prefix"]
    g2_prefix = hdf_key[ftype]["g2"]
    analysis_type = []
    with h5py.File(fname, "r") as HDF_Result:
        if c2_prefix in HDF_Result:
            analysis_type.append("Twotime")
        if g2_prefix in HDF_Result:
            analysis_type.append("Multitau")

    if len(analysis_type) == 0:
        raise ValueError(f"No analysis type found in {fname}")
    return tuple(analysis_type)


if __name__ == "__main__":
    pass
