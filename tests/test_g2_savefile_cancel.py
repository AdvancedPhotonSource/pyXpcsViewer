# Copyright © UChicago Argonne LLC
# See LICENSE file for details
"""GUI-level tests for XpcsViewer.savefile_G2_regroup's file-dialog handling.

Cancelling the "Save to File" dialog used to be mapped to ``save_fname=None``,
which ``XpcsFile.save_G2`` interprets as "overwrite the original file in
place" -- so a cancel both clobbered the source HDF5 and still reported
"G2 regrouping saved successfully". Cancel must abort before the kernel is
called: no save, no message box.

As in test_g2_tab_autoload.py, these call the unbound method against a
lightweight fake window rather than constructing a real XpcsViewer.
"""

import os
import types

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

pytest.importorskip("PySide6")

from pyxpcsviewer.gui.view import xpcs_viewer as xv
from pyxpcsviewer.gui.view.xpcs_viewer import XpcsViewer


class _FakePlots:
    def __init__(self):
        self.save_calls = []
        self.save_result = True

    def savefile_G2_regroup(self, **kwargs):
        self.save_calls.append(kwargs)
        return self.save_result


def _window(selected_rows=(0,)):
    win = types.SimpleNamespace()
    win.model = types.SimpleNamespace(target=["a.hdf"])
    win.plots = _FakePlots()
    win.get_selected_rows = lambda: list(selected_rows)
    win._resolve_G2_target_rows = lambda title: XpcsViewer._resolve_G2_target_rows(win, title)
    return win


def _patch_dialogs(monkeypatch, choice):
    monkeypatch.setattr(xv.QtWidgets.QFileDialog, "getSaveFileName", lambda *a, **k: choice)
    boxes = []
    monkeypatch.setattr(xv.QMessageBox, "information", lambda *a: boxes.append(("information", a)))
    monkeypatch.setattr(xv.QMessageBox, "critical", lambda *a: boxes.append(("critical", a)))
    return boxes


def test_savefile_G2_regroup_cancel_aborts_without_saving(monkeypatch):
    """Cancel -> no kernel call at all, no success or failure box."""
    boxes = _patch_dialogs(monkeypatch, ("", "HDF5 (*.hdf)"))
    win = _window()
    XpcsViewer.savefile_G2_regroup(win)
    assert win.plots.save_calls == []
    assert boxes == []


def test_savefile_G2_regroup_chosen_file_saves_and_reports(monkeypatch):
    """A chosen path is forwarded to the kernel and success is reported."""
    boxes = _patch_dialogs(monkeypatch, ("/out/a_regrouped.hdf", "HDF5 (*.hdf)"))
    win = _window()
    XpcsViewer.savefile_G2_regroup(win)
    assert win.plots.save_calls == [{"rows": [0], "save_fname": "/out/a_regrouped.hdf"}]
    assert [kind for kind, _ in boxes] == ["information"]


def test_savefile_G2_regroup_reports_failure(monkeypatch):
    """A kernel failure still surfaces as a critical box."""
    boxes = _patch_dialogs(monkeypatch, ("/out/a_regrouped.hdf", "HDF5 (*.hdf)"))
    win = _window()
    win.plots.save_result = False
    XpcsViewer.savefile_G2_regroup(win)
    assert [kind for kind, _ in boxes] == ["critical"]
