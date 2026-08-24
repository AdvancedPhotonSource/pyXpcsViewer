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


class _FakeIntSpin:
    def __init__(self, value=1):
        self._value = value

    def value(self):
        return self._value


class _FakeStatusBar:
    def __init__(self):
        self.messages = []

    def showMessage(self, text, timeout=0):
        self.messages.append(text)


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

    def __init__(self, selected_rows=(0,), regroup_exc=None, n_targets=1):
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
        self.comboBox_G2_outliertarget = _FakeCombo("g2-per-pixel")
        self.spinBox_G2_mintagcount = _FakeIntSpin(1)
        self.pg_regroup_g2 = object()
        self.statusbar = _FakeStatusBar()
        self.model = types.SimpleNamespace(target=[f"f{i}.hdf" for i in range(n_targets)])
        self._selected_rows = list(selected_rows)
        # process_G2_regroup passes this as the on_finished callback; bind the
        # real XpcsViewer implementation since it only touches attributes this
        # fake already provides (buttons, plots, plot_g2, pg_regroup_g2).
        self._on_G2_regroup_finished = types.MethodType(XpcsViewer._on_G2_regroup_finished, self)
        self._resolve_G2_target_rows = types.MethodType(XpcsViewer._resolve_G2_target_rows, self)

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


def test_process_G2_regroup_uses_the_only_file_when_nothing_is_selected(qapp):
    """One file in the list is an unambiguous choice, so don't make the user
    click it -- a dead ReGroup button reads as broken."""
    window = _FakeWindow(selected_rows=(), n_targets=1)

    XpcsViewer.process_G2_regroup(window)

    assert _pump(qapp, lambda: len(window.plots.calls) == 1)
    assert window.plots.calls[0]["rows"] == [0]
    assert any("only file" in m for m in window.statusbar.messages)


def test_process_G2_regroup_warns_when_the_choice_is_ambiguous(qapp, monkeypatch):
    window = _FakeWindow(selected_rows=(), n_targets=3)
    warned = []
    monkeypatch.setattr(
        "pyxpcsviewer.gui.view.xpcs_viewer.QMessageBox.warning",
        lambda *args, **kwargs: warned.append(args),
    )

    XpcsViewer.process_G2_regroup(window)

    assert window.plots.calls == []
    assert window.pushButton_G2_regroup.isEnabled()  # not left disabled on the abort
    assert len(warned) == 1
    assert "3 files" in warned[0][2]


def test_process_G2_regroup_warns_when_no_files_are_loaded(qapp, monkeypatch):
    window = _FakeWindow(selected_rows=(), n_targets=0)
    warned = []
    monkeypatch.setattr(
        "pyxpcsviewer.gui.view.xpcs_viewer.QMessageBox.warning",
        lambda *args, **kwargs: warned.append(args),
    )

    XpcsViewer.process_G2_regroup(window)

    assert window.plots.calls == []
    assert "No files in the target list" in warned[0][2]


def test_explicit_selection_wins_over_the_fallback(qapp):
    """A selection is never second-guessed, even with other files present."""
    window = _FakeWindow(selected_rows=(2,), n_targets=5)

    XpcsViewer.process_G2_regroup(window)

    assert _pump(qapp, lambda: len(window.plots.calls) == 1)
    assert window.plots.calls[0]["rows"] == [2]
    assert window.statusbar.messages == []


def test_process_G2_regroup_forwards_the_outlier_target(qapp):
    """The target picked in the UI must reach compute_g2, not silently default."""
    window = _FakeWindow()
    window.checkBox_G2_removeoutlier = _FakeCheckbox(True)  # the fake has no setChecked()
    window.comboBox_G2_outliertarget = _FakeCombo("G2")

    XpcsViewer.process_G2_regroup(window)

    assert _pump(qapp, lambda: len(window.plots.calls) == 1)
    assert window.plots.calls[0]["target"] == "G2"


def test_process_G2_regroup_sends_target_even_with_rejection_off(qapp):
    """outlier_threshold=-1 makes target moot, but the kwargs shape stays stable."""
    window = _FakeWindow()  # checkBox_G2_removeoutlier defaults to False

    XpcsViewer.process_G2_regroup(window)

    assert _pump(qapp, lambda: len(window.plots.calls) == 1)
    assert window.plots.calls[0]["outlier_threshold"] == -1.0
    assert window.plots.calls[0]["target"] == "g2-per-pixel"
    assert window.plots.calls[0]["min_tag_count"] == 0


def test_outlier_target_combo_exists_with_both_targets(qapp, tmp_path):
    """The generated UI exposes the combo, with item text matching OUTLIER_TARGETS."""
    from pyxpcsviewer.core.g2_utils import OUTLIER_TARGETS

    window = XpcsViewer(path=str(tmp_path))
    combo = window.comboBox_G2_outliertarget
    items = [combo.itemText(i) for i in range(combo.count())]
    assert items == list(OUTLIER_TARGETS)
    assert combo.currentText() == "g2-per-pixel"


def test_min_tag_count_sent_only_when_combine_outlier_is_on(qapp):
    """The Combine Outlier checkbox gates the persistence filter; the spin box
    supplies its count. Unchecked must send 0, not the spin's value."""
    window = _FakeWindow()
    window.checkBox_G2_removeoutlier = _FakeCheckbox(True)
    window.checkBox_G2_combineoutlier = _FakeCheckbox(False)
    window.spinBox_G2_mintagcount = _FakeIntSpin(30)

    XpcsViewer.process_G2_regroup(window)
    assert _pump(qapp, lambda: len(window.plots.calls) == 1)
    assert window.plots.calls[0]["min_tag_count"] == 0

    window.plots.calls.clear()
    window.checkBox_G2_combineoutlier = _FakeCheckbox(True)
    XpcsViewer.process_G2_regroup(window)
    assert _pump(qapp, lambda: len(window.plots.calls) == 1)
    assert window.plots.calls[0]["min_tag_count"] == 30


def test_min_tag_spin_defaults_to_one(qapp, tmp_path):
    """1 reproduces the historical union, so the default must not change behaviour."""
    window = XpcsViewer(path=str(tmp_path))
    assert window.spinBox_G2_mintagcount.value() == 1


@pytest.mark.parametrize(
    ("remove", "combine", "expected"),
    [(True, True, True), (True, False, False), (False, True, False), (False, False, False)],
)
def test_min_tag_enabled_only_when_both_switches_are_on(qapp, tmp_path, remove, combine, expected):
    """Min Tag is the count for Combine Outlier, which does nothing while Remove
    Outlier is off -- so it must follow both, not just the one next to it.
    Designer connections cannot express an AND, hence the hand-written slot."""
    window = XpcsViewer(path=str(tmp_path))
    window.checkBox_G2_removeoutlier.setChecked(remove)
    window.checkBox_G2_combineoutlier.setChecked(combine)
    assert window.spinBox_G2_mintagcount.isEnabled() is expected
    assert window.label_G2_mintagcount.isEnabled() is expected


def test_min_tag_starts_disabled(qapp, tmp_path):
    """Combine Outlier is unchecked by default, and Qt only fires toggled() on a
    change, so the initial state has to be set explicitly at construction."""
    window = XpcsViewer(path=str(tmp_path))
    assert not window.checkBox_G2_combineoutlier.isChecked()
    assert not window.spinBox_G2_mintagcount.isEnabled()


def test_min_tag_sits_next_to_the_checkbox_that_gates_it(qapp, tmp_path):
    """It used to sit in the opposite corner of the box from Combine Outlier,
    which made it read as permanently greyed out."""
    window = XpcsViewer(path=str(tmp_path))
    grid = window.gridLayout_50
    combine_row, combine_col, _, combine_span = grid.getItemPosition(grid.indexOf(window.checkBox_G2_combineoutlier))
    label_row, label_col, _, _ = grid.getItemPosition(grid.indexOf(window.label_G2_mintagcount))
    assert label_row == combine_row
    assert label_col == combine_col + combine_span  # immediately to its right


def test_g2_regroup_tab_controls_have_tooltips(qapp, tmp_path):
    """Every control on the G2 regroup tab is annotated. The outlier settings
    interact in non-obvious ways (target vs. threshold vs. persistence), so an
    unlabelled control here is a real usability hole."""
    window = XpcsViewer(path=str(tmp_path))
    page = window.tabWidget.widget(12)
    assert window.tabWidget.tabText(12) == "G2"
    # pyqtgraph's ImageView contributes its own controls; not ours to annotate
    pg_owned = {
        "roiBtn",
        "menuBtn",
        "normGroup",
        "normSubtractRadio",
        "normDivideRadio",
        "normOffRadio",
        "normROICheck",
        "normTimeRangeCheck",
        "normFrameCheck",
        "normXBlurSpin",
        "normYBlurSpin",
        "normTBlurSpin",
        "label_3",
        "label_4",
        "label_5",
        "label_8",
        "label_9",
        "label_10",
    }
    # these three labels are already full explanatory sentences in the UI
    self_documenting = {"label_74", "label_75", "label_78"}
    kinds = (
        QtWidgets.QComboBox,
        QtWidgets.QSpinBox,
        QtWidgets.QDoubleSpinBox,
        QtWidgets.QCheckBox,
        QtWidgets.QPushButton,
        QtWidgets.QSlider,
        QtWidgets.QGroupBox,
        QtWidgets.QLabel,
        QtWidgets.QTabWidget,
    )
    missing = [
        child.objectName()
        for child in page.findChildren(QtWidgets.QWidget)
        if isinstance(child, kinds)
        and child.objectName()
        and child.objectName() != "qt_spinbox_lineedit"
        and child.objectName() not in pg_owned
        and child.objectName() not in self_documenting
        and not child.toolTip()
    ]
    assert missing == []


def test_paired_label_and_control_share_a_tooltip(qapp, tmp_path):
    """Users hover the label as often as the widget, so the two must agree."""
    window = XpcsViewer(path=str(tmp_path))
    for label, control in (
        ("label_G2_outliertarget", "comboBox_G2_outliertarget"),
        ("label_G2_mintagcount", "spinBox_G2_mintagcount"),
        ("label_G2_errormodel", "comboBox_G2_errormodel"),
        ("label_76", "doubleSpinBox_G2_threshold"),
        ("label_72", "comboBox_G2_target"),
    ):
        assert getattr(window, label).toolTip() == getattr(window, control).toolTip(), label
