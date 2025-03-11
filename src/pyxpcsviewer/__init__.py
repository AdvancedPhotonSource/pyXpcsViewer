from importlib.metadata import version, PackageNotFoundError
from pyxpcsviewer.xpcs_file import XpcsFile

# Version handling
try:
    __version__ = version("pyxpcsviewer")
except PackageNotFoundError:
    __version__ = "0.1.0"  # Fallback if package is not installed

__author__ = 'Miaoqi Chu'
__credits__ = 'Argonne National Laboratory'