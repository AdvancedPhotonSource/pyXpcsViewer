# Copyright © UChicago Argonne LLC
# See LICENSE file for details
"""Regression test: changing the target-list selection via the keyboard.

list_view_target used to only call update_plot() on the view's `clicked`
signal, which Qt emits solely for mouse clicks. Arrow-key navigation moves
the current index and updates the selection (in ExtendedSelection mode,
without modifier keys held) without ever emitting `clicked`, so the plot
silently went stale when a user reselected a row with the keyboard.
"""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

pytest.importorskip("PySide6")

from PySide6 import QtCore, QtWidgets

from pyxpcsviewer.gui.model.list_model import ListDataModel


@pytest.fixture
def qapp():
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    yield app


def test_keyboard_reselection_triggers_update_plot(qapp, tmp_path, monkeypatch):
    from pyxpcsviewer.gui.view.xpcs_viewer import XpcsViewer

    window = XpcsViewer(path=str(tmp_path))
    try:
        calls = []
        monkeypatch.setattr(window, "update_plot", lambda: calls.append(1))

        target = ListDataModel(["a.hdf", "b.hdf", "c.hdf"])
        window.update_box(target, mode="target")

        selection_model = window.list_view_target.selectionModel()
        model = window.list_view_target.model()

        selection_model.select(
            model.index(0, 0), QtCore.QItemSelectionModel.ClearAndSelect
        )
        assert len(calls) == 1, "mouse-like selection should trigger update_plot"

        # Arrow-key navigation moves the current index and (without a modifier
        # key) replaces the selection with just that row -- exercise the same
        # selectionModel path a real Down/Up key press would take.
        window.list_view_target.setCurrentIndex(model.index(1, 0))
        assert len(calls) == 2, (
            "keyboard-driven reselection (arrow keys) must also trigger update_plot"
        )
    finally:
        window.close()


def test_rebinding_the_target_list_does_not_duplicate_the_connection(qapp, tmp_path, monkeypatch):
    """update_box() is called on every add_target()/reload with the *same*
    ListDataModel instance, which Qt's setModel() treats as a no-op -- so the
    selectionChanged wiring must attach exactly once, not once per rebind.
    """
    from pyxpcsviewer.gui.view.xpcs_viewer import XpcsViewer

    window = XpcsViewer(path=str(tmp_path))
    try:
        calls = []
        monkeypatch.setattr(window, "update_plot", lambda: calls.append(1))

        target = ListDataModel(["a.hdf", "b.hdf"])
        window.update_box(target, mode="target")
        window.update_box(target, mode="target")  # simulate a second add_target()
        window.update_box(target, mode="target")

        model = window.list_view_target.model()
        window.list_view_target.selectionModel().select(
            model.index(0, 0), QtCore.QItemSelectionModel.ClearAndSelect
        )
        assert len(calls) == 1, "rebinding the same target model must not stack duplicate connections"
    finally:
        window.close()
