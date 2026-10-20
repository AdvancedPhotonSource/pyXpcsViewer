# Copyright © UChicago Argonne LLC
# See LICENSE file for details
"""Find XPCS result files in a folder.

GUI-independent: both the Qt file locator and the web workspace list a folder through
:func:`list_result_files`.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

RESULT_EXTENSIONS: tuple[str, ...] = (".hdf", ".h5")
SORT_METHODS: tuple[str, ...] = ("name", "time", "index")


@dataclass(frozen=True)
class ResultFile:
    """One result file of a folder: its name, full path, modification time and size."""

    name: str
    path: str
    mtime: float
    size: int


def list_result_files(
    path: str,
    extensions: tuple[str, ...] = RESULT_EXTENSIONS,
    sort: str = "name",
    reverse: bool = False,
) -> list[ResultFile]:
    """The result files directly under ``path`` (hidden files skipped).

    Args:
        path: Folder to scan.
        extensions: Accepted file name endings, matched case-insensitively.
        sort: ``"name"`` (alphabetical), ``"time"`` (modification time, oldest first) or
            ``"index"`` (the order the file system lists them).
        reverse: Reverse the sorted order.

    Returns:
        The files as :class:`ResultFile` records.

    Raises:
        ValueError: For an unknown ``sort``.
        FileNotFoundError / NotADirectoryError: When ``path`` cannot be scanned.
    """
    if sort not in SORT_METHODS:
        raise ValueError(f"sort must be one of {SORT_METHODS}, not {sort!r}")
    lowered = tuple(ext.lower() for ext in extensions)
    files: list[ResultFile] = []
    with os.scandir(path) as entries:
        for entry in entries:
            if entry.name.startswith(".") or not entry.name.lower().endswith(lowered):
                continue
            try:
                if not entry.is_file():
                    continue
                stat = entry.stat()
            except OSError:
                continue  # vanished between listing and stat
            files.append(ResultFile(entry.name, entry.path, stat.st_mtime, stat.st_size))
    if sort == "name":
        files.sort(key=lambda f: f.name)
    elif sort == "time":
        files.sort(key=lambda f: (f.mtime, f.name))
    if reverse:
        files.reverse()
    return files
