# Copyright © UChicago Argonne LLC
# See LICENSE file for details
"""Reading the result files.

Importing this package registers the extra HDF5 compression filters (Zstandard, Bitshuffle, LZ4 ...)
when ``hdf5plugin`` is installed: result files written at the beamline use them, and h5py cannot
read such a dataset until the plugin is loaded.
"""

import contextlib

with contextlib.suppress(ImportError):  # the plain-HDF5 fallback: only uncompressed files open
    import hdf5plugin
