# Copyright © UChicago Argonne LLC
# See LICENSE file for details
import os

from PySide6 import QtCore


class ListDataModel(QtCore.QAbstractListModel):
    """Thin ``QAbstractListModel`` wrapping a plain Python list.

    Displays the basename of each full-path entry in the Qt model view.
    """

    def __init__(self, input_list: list | None = None) -> None:
        """Initialize with an optional initial list.

        Args:
            input_list: Initial items to populate the model.
        """
        super().__init__()
        if input_list is None:
            self.input_list = []
        else:
            self.input_list = input_list

    # overwrite parent method
    def data(self, index, role):
        """Return the basename of the full path stored at *index*."""
        if role == QtCore.Qt.DisplayRole:
            content = self.input_list[index.row()]
            basename = os.path.basename(content)
            return basename

    # overwrite parent method
    def rowCount(self, index):
        """Return the number of items in the underlying list."""
        return len(self.input_list)

    def extend(self, new_input_list: list) -> None:
        """Append multiple items and emit ``layoutChanged``."""
        self.input_list.extend(new_input_list)
        self.layoutChanged.emit()

    def append(self, new_item) -> None:
        """Append a single item and emit ``layoutChanged``."""
        self.input_list.append(new_item)
        self.layoutChanged.emit()

    def replace(self, new_input_list: list) -> None:
        """Clear the model and populate it with *new_input_list*."""
        self.input_list.clear()
        self.extend(new_input_list)

    def __len__(self) -> int:
        """Return the number of items in the underlying list."""
        return len(self.input_list)

    def __getitem__(self, i):
        """Return the item at index *i*."""
        return self.input_list[i]

    def pop(self, i: int = -1):
        """Remove and return the item at index *i*.

        Args:
            i: Index to remove (default last item).
        """
        return self.input_list.pop(i)

    def insert(self, i: int, item) -> None:
        """Insert *item* at position *i* and emit ``layoutChanged``."""
        self.input_list.insert(i, item)
        self.layoutChanged.emit()

    def copy(self) -> list:
        """Return a shallow copy of the underlying list."""
        return self.input_list.copy()
        self.layoutChanged.emit()

    def remove(self, x) -> None:
        """Remove the first occurrence of *x* and emit ``layoutChanged``."""
        self.input_list.remove(x)
        self.layoutChanged.emit()

    def clear(self) -> None:
        """Clear all items and emit ``layoutChanged``."""
        self.input_list.clear()
        self.layoutChanged.emit()


class TableDataModel(QtCore.QAbstractTableModel):
    """Table variant of ``ListDataModel`` with fixed column headers for job entries."""

    def __init__(self, input_list: list | None = None) -> None:
        """Initialize with an optional initial list.

        Args:
            input_list: Initial items (expected to be job-like objects with
                attributes ``jid``, ``size``, ``_progress``, ``stime``, ``eta``,
                ``etime``, ``short_name``).
        """
        super().__init__()
        if input_list is None:
            self.input_list = []
        else:
            self.input_list = input_list
        self.xlabels = ["id", "size", "progress", "start", "ETA (s)", "finish", "fname"]

    # overwrite parent method
    def data(self, index, role):
        """Return formatted job data for display at *index*."""
        if role == QtCore.Qt.DisplayRole:
            x = self.input_list[index.row()]
            ret = [x.jid, x.size, x._progress, x.stime, x.eta, x.etime, x.short_name]
            return ret[index.column()]

    # overwrite parent method
    def rowCount(self, index):
        """Return the number of job entries in the table."""
        return len(self.input_list)

    # overwrite parent method
    def columnCount(self, index):
        """Return the fixed number of columns (7)."""
        return len(self.xlabels)

    def headerData(self, section, orientation, role):
        """Return section headers for the job table."""
        if role == QtCore.Qt.DisplayRole and orientation == QtCore.Qt.Horizontal:
            return self.xlabels[section]

    def extend(self, new_input_list):
        """Append multiple job entries and emit ``layoutChanged``."""
        self.input_list.extend(new_input_list)
        self.layoutChanged.emit()

    def append(self, new_item):
        """Append a single job entry and emit ``layoutChanged``."""
        self.input_list.append(new_item)
        self.layoutChanged.emit()

    def replace(self, new_input_list):
        """Clear the table and populate it with *new_input_list*."""
        self.input_list.clear()
        self.extend(new_input_list)

    def pop(self, index):
        """Remove the job entry at *index* if valid."""
        if 0 <= index < self.__len__():
            self.input_list.pop(index)
            self.layoutChanged.emit()

    def __len__(self):
        """Return the number of job entries."""
        return len(self.input_list)

    def __getitem__(self, i):
        """Return the entry at index *i*."""
        return self.input_list[i]

    def copy(self):
        """Return a shallow copy of the underlying list."""
        return self.input_list.copy()

    def remove(self, x):
        """Remove the first occurrence of *x* from the table."""
        self.input_list.remove(x)

    def clear(self):
        """Clear all entries from the table (no ``layoutChanged``)."""
        self.input_list.clear()


def test():
    """Smoke-test: create a ``ListDataModel`` and print its items."""
    a = ["a", "b", "c"]
    model = ListDataModel(a)
    for n in range(len(model)):
        print(model[n])


if __name__ == "__main__":
    test()
