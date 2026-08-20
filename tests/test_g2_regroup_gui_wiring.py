# Copyright © UChicago Argonne LLC
# See LICENSE file for details
"""GUI-level wiring tests for XpcsViewer.process_G2_regroup.

process_G2_regroup used to call PlotController.process_G2_regroup directly
on the Qt main thread, which froze the window for the duration of a regroup
(worst case ~75-80s with outlier rejection enabled, before g2_utils's
find_g2_pixel_outliers was vectorized). It now submits the job through
JobManager.submit_g2_regroup (a G2RegroupWorker on a QThreadPool) and
disables the regroup/save buttons meanwhile.

These tests call XpcsViewer.process_G2_regroup as an unbound method against
a lightweight fake window (same fake-widget style as test_g2_mod.py), not a
real XpcsViewer instance: constructing a real XpcsViewer starts JobManager's
fit-pool warm-up (a ProcessPoolExecutor forked on a background QThreadPool
thread), which is unrelated to this feature and, combined with this file's
tight event-loop polling, deadlocks under this sandbox's fork() restrictions
-- a pre-existing hazard orthogonal to what's under test here. window.jobs is
therefore a minimal stand-in binding the real JobManager.submit_g2_regroup
(see test_g2_regroup_job_manager.py for the same pattern applied directly).
"""

import os
import time
import types
from collections.abc import Callable

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

pytest.importorskip("PySide6")

from PySide6 import QtCore, QtWidgets

from pyxpcsviewer.gui.control.background_job import WorkerSlot
from pyxpcsviewer.gui.control.job_manager import JobManager
from pyxpcsviewer.gui.view.xpcs_viewer import XpcsViewer


@pytest.fixture
def qapp():
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    yield app


def _pump(qapp: QtWidgets.QApplication, predicate: Callable[[], bool], timeout: float = 5.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        qapp.processEvents()
        if predicate():
            return True
        time.sleep(0.01)
    return predicate()


class _FakeButton:
    def __init__(self):
        self._enabled = True

    def isEnabled(self):
        return self._enabled

    def setEnabled(self, value):
        self._enabled = value


class _FakeCheckbox:
    def __init__(self, checked=False):
        self._checked = checked

    def isChecked(self):
        return self._checked


class _FakeCombo:
    def __init__(self, text="MeanAbsoluteDeviation"):
        self._text = text

    def currentText(self):
        return self._text


class _FakeSpin:
    def value(self):
        return 3.0


class _FakeTabWidget:
    def currentIndex(self):
        return 0  # "internal" qmap method


class _FakePlots:
    def __init__(self, exc=None):
        self.calls = []
        self.plot_g2_calls = []
        self._exc = exc

    def process_G2_regroup(self, **kwargs):
        self.calls.append(kwargs)
        if self._exc is not None:
            raise self._exc

    def plot_g2(self, hdl, **kwargs):
        self.plot_g2_calls.append((hdl, kwargs))


class _JobsStandIn:
    """Real JobManager.submit_g2_regroup bound to a minimal stand-in -- avoids
    JobManager.__init__'s unrelated fit-pool warm-up (see module docstring)."""

    def __init__(self, thread_pool):
        self.thread_pool = thread_pool
        self._g2_regroup = WorkerSlot()

    submit_g2_regroup = JobManager.submit_g2_regroup


class _FakeWindow:
    """Duck-typed stand-in for XpcsViewer exposing only what process_G2_regroup touches."""

    def __init__(self, selected_rows=(0,), regroup_exc=None):
        self.thread_pool = QtCore.QThreadPool()
        self.jobs = _JobsStandIn(self.thread_pool)
        self.plots = _FakePlots(exc=regroup_exc)
        self.pushButton_G2_regroup = _FakeButton()
        self.pushButton_G2_savefile = _FakeButton()
        self.tabWidget_G2_regroup = _FakeTabWidget()
        self.checkBox_G2_removeoutlier = _FakeCheckbox(False)
        self.comboBox_G2_outliermethod = _FakeCombo()
        self.doubleSpinBox_G2_threshold = _FakeSpin()
        self.checkBox_G2_combineoutlier = _FakeCheckbox(False)
        self.comboBox_G2_errormodel = _FakeCombo("per-pixel")
        self.comboBox_G2_outliertarget = _FakeCombo("G20")
        self.pg_regroup_g2 = object()
        self._selected_rows = list(selected_rows)
        # process_G2_regroup passes this as the on_finished callback; bind the
        # real XpcsViewer implementation since it only touches attributes this
        # fake already provides (buttons, plots, plot_g2, pg_regroup_g2).
        self._on_G2_regroup_finished = types.MethodType(XpcsViewer._on_G2_regroup_finished, self)

    def get_selected_rows(self):
        return self._selected_rows

    def plot_g2(self, dryrun=False):
        return {"dryrun": True} if dryrun else None


def test_process_G2_regroup_disables_buttons_then_reenables_and_replots(qapp):
    window = _FakeWindow()

    XpcsViewer.process_G2_regroup(window)

    # Disabled synchronously, before the worker thread has had a chance to run.
    assert not window.pushButton_G2_regroup.isEnabled()
    assert not window.pushButton_G2_savefile.isEnabled()

    assert _pump(qapp, lambda: window.pushButton_G2_regroup.isEnabled())

    assert window.plots.calls and window.plots.calls[0]["rows"] == [0]
    assert window.plots.calls[0]["error_model"] == "per-pixel"
    assert window.pushButton_G2_savefile.isEnabled()
    assert window.plots.plot_g2_calls and window.plots.plot_g2_calls[0][1] == {"dryrun": True}


def test_process_G2_regroup_failure_reenables_buttons_and_reports_error(qapp, monkeypatch):
    window = _FakeWindow(regroup_exc=ValueError("no qmap found"))
    shown = []
    monkeypatch.setattr(
        "pyxpcsviewer.gui.view.xpcs_viewer.QMessageBox.critical",
        lambda *args, **kwargs: shown.append(args),
    )

    XpcsViewer.process_G2_regroup(window)
    assert not window.pushButton_G2_regroup.isEnabled()

    assert _pump(qapp, lambda: window.pushButton_G2_regroup.isEnabled())

    assert window.pushButton_G2_savefile.isEnabled()
    assert len(shown) == 1
    assert "no qmap found" in shown[0][2]
    assert not window.plots.plot_g2_calls  # no replot on failure


def test_process_G2_regroup_noop_without_selection(qapp):
    window = _FakeWindow(selected_rows=())

    XpcsViewer.process_G2_regroup(window)

    assert window.plots.calls == []
    assert window.pushButton_G2_regroup.isEnabled()


def test_process_G2_regroup_forwards_the_outlier_target(qapp):
    """The target picked in the UI must reach compute_g2, not silently default."""
    window = _FakeWindow()
    window.checkBox_G2_removeoutlier = _FakeCheckbox(True)  # the fake has no setChecked()
    window.comboBox_G2_outliertarget = _FakeCombo("g2-per-pixel")

    XpcsViewer.process_G2_regroup(window)

    assert _pump(qapp, lambda: len(window.plots.calls) == 1)
    assert window.plots.calls[0]["target"] == "g2-per-pixel"


def test_process_G2_regroup_sends_target_even_with_rejection_off(qapp):
    """outlier_threshold=-1 makes target moot, but the kwargs shape stays stable."""
    window = _FakeWindow()  # checkBox_G2_removeoutlier defaults to False

    XpcsViewer.process_G2_regroup(window)

    assert _pump(qapp, lambda: len(window.plots.calls) == 1)
    assert window.plots.calls[0]["outlier_threshold"] == -1.0
    assert window.plots.calls[0]["target"] == "G20"


def test_outlier_target_combo_exists_with_both_targets(qapp, tmp_path):
    """The generated UI exposes the combo, with item text matching OUTLIER_TARGETS."""
    from pyxpcsviewer.core.g2_utils import OUTLIER_TARGETS

    window = XpcsViewer(path=str(tmp_path))
    combo = window.comboBox_G2_outliertarget
    items = [combo.itemText(i) for i in range(combo.count())]
    assert items == list(OUTLIER_TARGETS)
    assert combo.currentText() == "G20"
