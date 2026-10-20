# Copyright © UChicago Argonne LLC
# See LICENSE file for details
"""core.file_io.discover: listing the result files of a folder."""

import os
import time

import pytest

from pyxpcsviewer.core.file_io.discover import list_result_files


def _touch(path, mtime=None):
    with open(path, "wb") as f:
        f.write(b"x")
    if mtime is not None:
        os.utime(path, (mtime, mtime))


def test_lists_result_files_only(tmp_path):
    _touch(tmp_path / "b_results.hdf")
    _touch(tmp_path / "a_results.H5")
    _touch(tmp_path / ".hidden.hdf")
    _touch(tmp_path / "notes.txt")
    (tmp_path / "sub.hdf").mkdir()
    files = list_result_files(str(tmp_path))
    assert [f.name for f in files] == ["a_results.H5", "b_results.hdf"]
    assert all(f.path == str(tmp_path / f.name) and f.size == 1 for f in files)


def test_sorts_by_time_and_reverses(tmp_path):
    now = time.time()
    _touch(tmp_path / "old.hdf", now - 100)
    _touch(tmp_path / "new.hdf", now)
    assert [f.name for f in list_result_files(str(tmp_path), sort="time")] == ["old.hdf", "new.hdf"]
    assert [f.name for f in list_result_files(str(tmp_path), sort="time", reverse=True)] == ["new.hdf", "old.hdf"]
    assert [f.name for f in list_result_files(str(tmp_path), sort="name", reverse=True)] == ["old.hdf", "new.hdf"]


def test_unknown_sort_rejected(tmp_path):
    with pytest.raises(ValueError):
        list_result_files(str(tmp_path), sort="size")
