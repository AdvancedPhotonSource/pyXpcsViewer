# Copyright © UChicago Argonne LLC
# See LICENSE file for details
"""File dialogs must open in the folder currently being browsed, not the start-up one.

XpcsViewer used to seed its "Open directory" dialog with ``start_wd`` (fixed at
construction) and the other dialogs with no directory at all, so after browsing
to a new folder every later dialog jumped back to where the viewer was started.
Cancelling the browse dialog even reloaded the start-up folder. These tests pin
the fixed behaviour by stubbing the static QFileDialog entry points.
"""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

pytest.importorskip("PySide6")


@pytest.fixture
def qapp():
    from PySide6 import QtWidgets

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    yield app


@pytest.fixture
def viewer(qapp, tmp_path):
    from pyxpcsviewer.gui.view.xpcs_viewer import XpcsViewer

    start = tmp_path / "start"
    start.mkdir()
    window = XpcsViewer(path=str(start))
    try:
        yield window
    finally:
        window.close()


def _dir_arg(args, kwargs):
    """Return the ``dir`` argument of a stubbed static QFileDialog call."""
    if "dir" in kwargs:
        return kwargs["dir"]
    return args[2] if len(args) > 2 else None


@pytest.fixture
def dialog_spy(monkeypatch):
    """Stub the three static QFileDialog getters to record their start dir and cancel."""
    from PySide6 import QtWidgets

    seen = {}

    def existing_directory(*args, **kwargs):
        seen["existing_directory"] = _dir_arg(args, kwargs)
        return ""

    def open_file_name(*args, **kwargs):
        seen["open_file_name"] = _dir_arg(args, kwargs)
        return "", ""

    def save_file_name(*args, **kwargs):
        seen["save_file_name"] = _dir_arg(args, kwargs)
        return "", ""

    monkeypatch.setattr(QtWidgets.QFileDialog, "getExistingDirectory", existing_directory)
    monkeypatch.setattr(QtWidgets.QFileDialog, "getOpenFileName", open_file_name)
    monkeypatch.setattr(QtWidgets.QFileDialog, "getSaveFileName", save_file_name)
    return seen


def test_browse_dialog_opens_in_current_folder_and_cancel_keeps_it(viewer, tmp_path, dialog_spy):
    window = viewer
    other = tmp_path / "other"
    other.mkdir()

    window.load_path(str(other))
    assert window.work_dir.text() == str(other)
    assert window.model.path == str(other)
    assert window._current_dir() == str(other)

    # The "Load" button passes clicked(bool) -> path=False, which opens the dialog.
    window.load_path(False)
    assert dialog_spy["existing_directory"] == str(other), "browse dialog did not start in the current folder"
    # Cancelling must not snap back to the start-up directory.
    assert window.work_dir.text() == str(other)
    assert window.model.path == str(other)


def test_other_dialogs_follow_current_folder(viewer, tmp_path, dialog_spy):
    window = viewer
    other = tmp_path / "other"
    other.mkdir()
    window.load_path(str(other))

    window.load_external_qmap_for_G2_regroup()
    assert dialog_spy["open_file_name"] == str(other)

    window.select_bkgfile()
    assert dialog_spy["open_file_name"] == str(other)

    window.saxs1d_export()
    assert dialog_spy["existing_directory"] == str(other)

    window.avg_save_path.setText("")
    window.set_average_save_name()
    assert dialog_spy["save_file_name"] == str(other)


def test_average_dialogs_prefer_chosen_save_path_and_survive_cancel(viewer, tmp_path, dialog_spy):
    window = viewer
    save_dir = tmp_path / "save_here"
    save_dir.mkdir()
    window.avg_save_path.setText(str(save_dir))
    window.avg_save_name.setText("Average_keep.hdf")

    window.set_average_save_path()
    assert dialog_spy["existing_directory"] == str(save_dir)
    assert window.avg_save_path.text() == str(save_dir), "cancel wiped the save path"

    window.set_average_save_name()
    assert dialog_spy["save_file_name"] == str(save_dir)
    assert window.avg_save_name.text() == "Average_keep.hdf", "cancel wiped the save name"
