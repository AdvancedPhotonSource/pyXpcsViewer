# Copyright © UChicago Argonne LLC
# See LICENSE file for details
"""GUI-level tests for XpcsViewer.plot_G2_regroup's auto-load behaviour.

The G2 tab used to render nothing until a file was clicked in the target list
(it bailed out on an empty selection, unlike the other tabs, whose
get_xf_list(rows=[]) falls back to all targets), and it wrapped the plot call
in a modal QProgressDialog because the whole G2 cube was read for every
refresh. Now it defaults to the first target and reads a single frame.

As in test_g2_regroup_gui_wiring.py, these call the unbound method against a
lightweight fake window rather than constructing a real XpcsViewer.
"""

import os
import types

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

pytest.importorskip("PySide6")

from pyxpcsviewer.gui.view import xpcs_viewer as xv
from pyxpcsviewer.gui.view.xpcs_viewer import XpcsViewer


class _Combo:
    def __init__(self, text):
        self._text = text

    def currentText(self):
        return self._text


class _Value:
    def __init__(self, value):
        self._value = value

    def value(self):
        return self._value


class _StatusBar:
    def __init__(self):
        self.messages = []

    def showMessage(self, text, timeout=0):
        self.messages.append(text)


class _FakePlots:
    def __init__(self):
        self.calls = []

    def plot_G2_regroup(self, hdl, **kwargs):
        self.calls.append(kwargs)


def _window(targets=("a.hdf", "b.hdf"), selected_rows=()):
    win = types.SimpleNamespace()
    win.model = types.SimpleNamespace(target=list(targets))
    win.plots = _FakePlots()
    win.statusbar = _StatusBar()
    win.comboBox_G2_target = _Combo("G2")
    win.cb_saxs2D_cmap = _Combo("jet")
    win.horizontalSlider_G2_delay = _Value(0)
    win.doubleSpinBox_G2_vmin = _Value(0.0)
    win.doubleSpinBox_G2_vmax = _Value(1.0)
    win.pg_regroup_G2 = object()
    win.get_selected_rows = lambda: list(selected_rows)
    return win


def test_plot_G2_regroup_autoloads_first_target(monkeypatch):
    """No selection -> the first target renders instead of nothing."""
    monkeypatch.setattr(xv, "has_G2_field", lambda fname: True)
    win = _window()
    XpcsViewer.plot_G2_regroup(win)
    assert win.plots.calls and win.plots.calls[0]["rows"] == [0]


def test_plot_G2_regroup_keeps_an_explicit_selection(monkeypatch):
    monkeypatch.setattr(xv, "has_G2_field", lambda fname: True)
    win = _window(selected_rows=(1,))
    XpcsViewer.plot_G2_regroup(win)
    assert win.plots.calls[0]["rows"] == [1]


def test_plot_G2_regroup_dryrun_reports_the_autoloaded_row(monkeypatch):
    """The dry-run kwargs must carry the resolved row so update_plot's diff works."""
    monkeypatch.setattr(xv, "has_G2_field", lambda fname: True)
    win = _window()
    kwargs = XpcsViewer.plot_G2_regroup(win, dryrun=True)
    assert kwargs["rows"] == [0]
    assert win.plots.calls == []


def test_plot_G2_regroup_without_targets_does_nothing(monkeypatch):
    monkeypatch.setattr(xv, "has_G2_field", lambda fname: True)
    win = _window(targets=())
    assert XpcsViewer.plot_G2_regroup(win) is None
    assert win.plots.calls == []


def test_plot_G2_regroup_reports_missing_G2_without_a_modal_box(monkeypatch):
    """A file without G2 gets a status-bar note, not a dialog blocking the tab."""
    monkeypatch.setattr(xv, "has_G2_field", lambda fname: False)

    def _fail(*args, **kwargs):
        raise AssertionError("plot_G2_regroup must not open a modal message box")

    monkeypatch.setattr(xv.QMessageBox, "critical", _fail)
    win = _window()
    XpcsViewer.plot_G2_regroup(win)
    assert win.plots.calls == []
    assert win.statusbar.messages and "No G2 data" in win.statusbar.messages[0]
