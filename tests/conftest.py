# Copyright © UChicago Argonne LLC
# See LICENSE file for details
"""Shared fixtures for the real XPCS result files under tests/data/.

The three files cover the three shapes a result file can take: Multitau-only,
Twotime-only, and both -- see core.file_io.hdf_reader.get_analysis_type.
"""

from pathlib import Path

import pytest

DATA_DIR = Path(__file__).parent / "data"

_REAL_FILES = {
    "multitau": DATA_DIR / "D0131_multitau.hdf",
    "twotime": DATA_DIR / "Ac0023_LiC18TFSI_180C_1p0mm_a2160_f002000_r00001_twotime.hdf",
    "both": DATA_DIR / "Cb0023_SPM-GDMA-Na-06x_a2666_f001000_r00001_both.hdf",
}


def _require(path: Path) -> str:
    if not path.exists():
        pytest.skip(f"real test fixture not available: {path}")
    return str(path)


@pytest.fixture(scope="session")
def multitau_path():
    """Path to a real Multitau-only result file."""
    return _require(_REAL_FILES["multitau"])


@pytest.fixture(scope="session")
def twotime_path():
    """Path to a real Twotime-only result file."""
    return _require(_REAL_FILES["twotime"])


@pytest.fixture(scope="session")
def both_path():
    """Path to a real result file with both Multitau and Twotime analyses."""
    return _require(_REAL_FILES["both"])


@pytest.fixture
def multitau_xf(multitau_path):
    """A freshly loaded XpcsFile for the Multitau-only fixture."""
    from pyxpcsviewer.core.xpcs_file import XpcsFile

    return XpcsFile(multitau_path)


@pytest.fixture
def twotime_xf(twotime_path):
    """A freshly loaded XpcsFile for the Twotime-only fixture."""
    from pyxpcsviewer.core.xpcs_file import XpcsFile

    return XpcsFile(twotime_path)


@pytest.fixture
def both_xf(both_path):
    """A freshly loaded XpcsFile for the combined Multitau+Twotime fixture."""
    from pyxpcsviewer.core.xpcs_file import XpcsFile

    return XpcsFile(both_path)
