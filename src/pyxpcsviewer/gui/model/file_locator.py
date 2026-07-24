import datetime
import logging
import os
import time
import traceback

from ...core.fileIO.qmap_utils import QMapManager
from ...core.xpcs_file import XpcsFile as XF
from .listmodel import ListDataModel

logger = logging.getLogger(__name__)


def create_xpcs_dataset(fname, **kwargs):
    """
    create a xpcs_file objects from a given path
    """
    try:
        temp = XF(fname, **kwargs)
    except Exception:
        logger.error("failed to load file: %s", fname)
        logger.error(traceback.format_exc())
        temp = None
    return temp


class FileLocator:
    """Locate XPCS result files, manage source/target lists, and cache loaded
    :class:`~pyxpcsviewer.core.xpcs_file.XpcsFile` objects."""

    def __init__(self, path: str):
        """Initialize with a data directory path.

        Args:
            path: Directory containing ``*_result.hdf`` or ``*_result.h5`` files.
        """
        self.path = path
        self.source = ListDataModel()
        self.source_search = ListDataModel()
        self.target = ListDataModel()
        self.qmap_manager = QMapManager()
        self.cache = {}
        self.timestamp = None

    def set_path(self, path: str) -> None:
        """Update the data directory path.

        Args:
            path: New directory to scan for result files.
        """
        self.path = path

    def clear(self) -> None:
        """Clear the source and source-search lists."""
        self.source.clear()
        self.source_search.clear()

    def get_xf_list(self, rows=None, filter_atype=None, filter_fitted=False):
        """Return cached XpcsFile objects for the requested indices.

        Args:
            rows: List of target indices; ``None`` uses all targets.
            filter_atype: If set, only return files whose analysis type
                contains this string.
            filter_fitted: If ``True``, skip files without a fitting summary.

        Returns:
            List of :class:`~pyxpcsviewer.core.xpcs_file.XpcsFile` objects.
        """
        selected = rows if rows else list(range(len(self.target)))

        ret = []
        for n in selected:
            if n < 0 or n >= len(self.target):
                continue
            # full_fname = os.path.join(self.path, self.target[n])
            full_fname = self.target[n]
            if full_fname not in self.cache:
                xf_obj = create_xpcs_dataset(full_fname, qmap_manager=self.qmap_manager)
                self.cache[full_fname] = xf_obj
            xf_obj = self.cache[full_fname]
            if xf_obj.fit_summary is None and filter_fitted:
                continue
            if filter_atype is None or filter_atype in xf_obj.atype:
                ret.append(xf_obj)
        return ret

    def get_hdf_info(self, fname, filter_str=None):
        """Return the HDF5 structure info for a given file.

        Args:
            fname: Input filename to query.
            filter_str: List of filter strings to narrow the output.

        Returns:
            List of strings describing the HDF5 structure.
        """
        xf_obj = create_xpcs_dataset(os.path.join(self.path, fname), qmap_manager=self.qmap_manager)
        return xf_obj.get_hdf_info(filter_str)

    def add_target(self, alist: list[str], threshold: int = 256, preload: bool = True) -> None:
        """Add a list of filenames to the target model and cache.

        For small batches (≤ *threshold*) each file is loaded into the
        ``XpcsFile`` cache; larger batches are deferred.

        Args:
            alist: List of relative or absolute filenames to add.
            threshold: File count above which preloading is skipped.
            preload: If ``True``, load files into cache for small batches.
        """
        if not alist:
            return
        if preload and len(alist) <= threshold:
            t0 = time.perf_counter()
            for fname in alist:
                full_fname = os.path.join(self.path, fname)
                if full_fname in self.target:
                    continue
                xf_obj = create_xpcs_dataset(full_fname, qmap_manager=self.qmap_manager)
                if xf_obj is not None:
                    self.target.append(full_fname)
                    self.cache[full_fname] = xf_obj

            t1 = time.perf_counter()
            logger.info(f"Load {len(alist)}  files in {t1 - t0:.3f} seconds")
        else:
            logger.info("preload disabled or too many files added")
            full_fname_list = [os.path.join(self.path, fname) for fname in alist]
            self.target.extend(full_fname_list)
        self.timestamp = str(datetime.datetime.now())
        return

    def clear_target(self) -> None:
        """Clear the target list and its file cache."""
        self.target.clear()
        self.cache.clear()

    def remove_target(self, rlist: list[str]) -> None:
        """Remove a list of paths from the target model and cache.

        Args:
            rlist: Paths to remove.
        """
        for x in rlist:
            if x in self.target:
                self.target.remove(x)
            self.cache.pop(x, None)
        if not self.target:
            self.clear_target()
        self.timestamp = str(datetime.datetime.now())

    def reorder_target(self, row: int, direction: str = "up") -> int:
        """Move the target entry at *row* up or down.

        Args:
            row: Zero-based index of the target entry to move.
            direction: Either ``"up"`` or ``"down"``.

        Returns:
            New index on success, or ``-1`` if no move was needed.
        """
        size = len(self.target)
        assert 0 <= row < size, "check row value"
        if (direction == "up" and row == 0) or (direction == "down" and row == size - 1):
            return -1

        item = self.target.pop(row)
        pos = row - 1 if direction == "up" else row + 1
        self.target.insert(pos, item)
        idx = self.target.index(pos)
        self.timestamp = str(datetime.datetime.now())
        return idx

    def search(self, val: str, filter_type: str = "prefix") -> None:
        """Filter the source list by prefix or substring and populate ``source_search``.

        Args:
            val: Search string. Multiple space-separated words require all to match in *substr* mode.
            filter_type: Either ``"prefix"`` or ``"substr"``.
        """
        assert filter_type in [
            "prefix",
            "substr",
        ], "filter_type must be prefix or substr"
        if filter_type == "prefix":
            selected = [x for x in self.source if x.startswith(val)]
        elif filter_type == "substr":
            filter_words = val.split()  # Split search query by whitespace
            selected = [x for x in self.source if all(t in x for t in filter_words)]
        self.source_search.replace(selected)
        return

    def build(
        self,
        path: str | None = None,
        filter_list: tuple[str, ...] = (".hdf", ".h5"),
        sort_method: str = "Filename",
    ) -> bool:
        """Scan a directory for XPCS result files and populate the source model.

        Files are filtered by extension and sorted according to *sort_method*.

        Args:
            path: Directory to scan (also stored as ``self.path``).
            filter_list: Allowed file extensions.
            sort_method: One of ``"Filename"``, ``"Time"``, or ``"Index"``, each
                optionally suffixed with ``"-reverse"``.

        Returns:
            ``True`` on success.
        """
        self.path = path
        flist = [
            entry.name
            for entry in os.scandir(path)
            if entry.is_file() and entry.name.lower().endswith(filter_list) and not entry.name.startswith(".")
        ]
        if sort_method.startswith("Filename"):
            flist.sort()
        elif sort_method.startswith("Time"):
            flist.sort(key=lambda x: os.path.getmtime(os.path.join(path, x)))
        elif sort_method.startswith("Index"):
            pass

        if sort_method.endswith("-reverse"):
            flist.reverse()
        self.source.replace(flist)
        return True


if __name__ == "__main__":
    # test1()
    fl = FileLocator(path="./data/files.txt")
