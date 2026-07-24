import os

import h5py


def isNeXusFile(fname: str) -> bool:
    """Check whether *fname* follows the NeXus HDF5 layout.

    Args:
        fname: Path to the HDF5 file.

    Returns:
        True if the NeXus metadata group exists, else False.
    """
    with h5py.File(fname, "r") as f:
        if "/entry/instrument/bluesky/metadata/" in f:
            return True
    return False


def isLegacyFile(fname: str) -> bool:
    """Check whether *fname* follows the legacy APS-8ID-I HDF5 layout.

    Args:
        fname: Path to the HDF5 file.

    Returns:
        True if the ``/xpcs/Version`` dataset exists, else False.
    """
    with h5py.File(fname, "r") as f:
        if "/xpcs/Version" in f:
            return True


def get_ftype(fname: str) -> bool | str:
    """Return the file type of an HDF5 result file.

    Args:
        fname: Path to the HDF5 file.

    Returns:
        ``"nexus"``, ``"legacy"``, or ``False`` if neither format
        matches or the file does not exist.
    """
    if not os.path.isfile(fname):
        return False

    if isLegacyFile(fname):
        return "legacy"
    elif isNeXusFile(fname):
        return "nexus"
    else:
        return False
