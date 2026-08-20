# Copyright © UChicago Argonne LLC
# See LICENSE file for details
"""Offscreen tests for the G2 outlier debug dialog's plot building.

build_debug_plots() is exercised directly with synthetic bundles from
compute_g2_debug_bundle — no real HDF5 file, no worker thread. The
worker/dialog lifecycle and the main-window wiring are tested later in
this file (see test_close_blocked_while_computing / test_debug_button_wired).
"""

import os
import threading
import time
import types
from collections.abc import Callable
from typing import cast

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import numpy as np
import pytest

pytest.importorskip("PySide6")

import pyqtgraph as pg
from PySide6 import QtWidgets

from pyxpcsviewer.core.g2_utils import compute_g2_debug_bundle
from pyxpcsviewer.gui.view.g2_debug_dialog import (
    G2DebugDialog,
    _BadMapPanel,
    _BinSweepPanel,
    _XpcsFileLike,
    build_debug_plots,
)


def make_synthetic():
    """(2 delays, 3 ch, 4x4) G2: dead pixel (0,0); sq 2 rows 2-3 hold
    pixel 15=(3,3) and pixel 8=(2,0) at 10.0 at BOTH delays, and pixel
    13=(3,1) at 10.0 at delay 0 only (a count-1 outlier)."""
    IP = np.ones((2, 4, 4), dtype=np.float32)
    IP[:, 3, 3] = 10.0
    IP[:, 2, 0] = 10.0
    IP[0, 3, 1] = 10.0
    IF = np.ones((2, 4, 4), dtype=np.float32)
    IF[:, 0, 0] = 0.0
    G2 = np.stack([IP, IF, IF], axis=1).astype(np.float32)
    sqmap = np.zeros((4, 4), dtype=np.uint16)
    sqmap[:2, :] = 1
    sqmap[2:, :] = 2
    dqmap = np.ones((4, 4), dtype=np.uint16)
    return G2, sqmap, dqmap


def _zero_bin_bundle():
    """1 delay, (3, 4) image: sq 1 and 3 all ones, sq 2 (middle row) all zero."""
    G2 = np.zeros((1, 3, 3, 4), dtype=np.float32)
    G2[:, 0] = 1.0
    G2[:, 0, 1, :] = 0.0
    G2[:, 1] = 1.0
    G2[:, 2] = 1.0
    sqmap = np.zeros((3, 4), dtype=np.uint16)
    sqmap[0, :] = 1
    sqmap[1, :] = 2
    sqmap[2, :] = 3
    dqmap = np.ones((3, 4), dtype=np.uint16)
    return compute_g2_debug_bundle(sqmap, dqmap, G2)


@pytest.fixture
def qapp():
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    yield app


@pytest.fixture
def bundle():
    G2, sqmap, dqmap = make_synthetic()
    return compute_g2_debug_bundle(sqmap, dqmap, G2, outlier_threshold=3.0, outlier_method="MeanAbsoluteDeviation")


def _host() -> QtWidgets.QWidget:
    host = QtWidgets.QWidget()
    host.setLayout(QtWidgets.QVBoxLayout())
    return host


def test_build_skeleton(qapp, bundle):
    host = _host()
    tabs = build_debug_plots(host, bundle, "fake.hdf", "MeanAbsoluteDeviation", 3.0, False)
    assert tabs.count() == 2
    header = host.findChild(QtWidgets.QLabel, "g2_debug_header")
    assert "threshold=3" in header.text()
    assert "combine=False" in header.text()
    assert "fake.hdf" in header.text()


def test_bin_sweep_renders_all_delays(qapp, bundle):
    host = _host()
    build_debug_plots(host, bundle, "fake.hdf", "MeanAbsoluteDeviation", 3.0, False)
    panel = host.findChild(_BinSweepPanel)
    plots = [it for it in panel.glw.ci.items if isinstance(it, pg.PlotItem)]
    assert len(plots) == 2  # one plot per delay
    spin = host.findChild(QtWidgets.QSpinBox, "g2_debug_sq_spin")
    assert (spin.minimum(), spin.maximum()) == (1, 2)


def _title(panel):
    return next(it for it in panel.glw.ci.items if isinstance(it, pg.PlotItem)).titleLabel.text


def test_bin_sweep_spin_switches_bin_on_editing_finished(qapp, bundle):
    host = _host()
    build_debug_plots(host, bundle, "fake.hdf", "MeanAbsoluteDeviation", 3.0, False)
    panel = host.findChild(_BinSweepPanel)
    spin = host.findChild(QtWidgets.QSpinBox, "g2_debug_sq_spin")
    spin.setValue(2)
    spin.editingFinished.emit()  # Enter / focus-out
    # pixels 15, 8 (both delays) and 13 (delay 0)
    assert "out=3" in _title(panel)
    spin.setValue(1)
    spin.editingFinished.emit()
    assert "out=0" in _title(panel)


def test_bin_sweep_spin_defers_render_until_committed(qapp, bundle):
    """Typing/stepping the spin box must not re-render until the edit is finished."""
    host = _host()
    build_debug_plots(host, bundle, "fake.hdf", "MeanAbsoluteDeviation", 3.0, False)
    panel = host.findChild(_BinSweepPanel)
    spin = host.findChild(QtWidgets.QSpinBox, "g2_debug_sq_spin")
    assert "out=0" in _title(panel)  # bin 1 rendered at construction
    spin.setValue(2)
    assert "out=0" in _title(panel)  # still showing bin 1
    spin.editingFinished.emit()
    assert "out=3" in _title(panel)


def test_bin_sweep_slider_and_spin_are_linked(qapp, bundle):
    host = _host()
    build_debug_plots(host, bundle, "fake.hdf", "MeanAbsoluteDeviation", 3.0, False)
    panel = host.findChild(_BinSweepPanel)
    slider = host.findChild(QtWidgets.QSlider, "g2_debug_sq_slider")
    spin = host.findChild(QtWidgets.QSpinBox, "g2_debug_sq_spin")
    assert (slider.minimum(), slider.maximum()) == (spin.minimum(), spin.maximum())

    spin.setValue(2)
    assert slider.value() == 2  # spin -> slider
    slider.setValue(1)
    assert spin.value() == 1  # slider -> spin
    assert "out=0" in _title(panel)


def test_bin_sweep_slider_renders_on_release_not_during_drag(qapp, bundle):
    host = _host()
    build_debug_plots(host, bundle, "fake.hdf", "MeanAbsoluteDeviation", 3.0, False)
    panel = host.findChild(_BinSweepPanel)
    slider = host.findChild(QtWidgets.QSlider, "g2_debug_sq_slider")
    spin = host.findChild(QtWidgets.QSpinBox, "g2_debug_sq_spin")

    slider.setSliderDown(True)  # handle grabbed
    slider.setValue(2)
    assert spin.value() == 2  # spin tracks the handle live
    assert "out=0" in _title(panel)  # but no re-render mid-drag
    slider.setSliderDown(False)
    slider.sliderReleased.emit()
    assert "out=3" in _title(panel)


def test_bin_sweep_all_zero_bin(qapp):
    host = _host()
    build_debug_plots(host, _zero_bin_bundle(), "fake.hdf", "MeanAbsoluteDeviation", 3.0, False)
    panel = host.findChild(_BinSweepPanel)
    panel.spin.setValue(2)
    panel.spin.editingFinished.emit()
    assert "all zero" in _title(panel)


def test_bad_map_and_mintag_remask(qapp, bundle):
    host = _host()
    build_debug_plots(host, bundle, "fake.hdf", "MeanAbsoluteDeviation", 3.0, False)
    panel = host.findChild(_BadMapPanel)
    assert panel is not None
    view = host.findChild(pg.ImageView, "g2_debug_map_view")
    spin = host.findChild(QtWidgets.QSpinBox, "g2_debug_mintag_spin")
    summary = host.findChild(QtWidgets.QLabel, "g2_debug_map_summary")

    img = view.getProcessedImage()
    assert img.shape == (4, 4)
    # pixels 15=(3,3) and 8=(2,0) are flagged at both delays -> count 2;
    # pixel 13=(3,1) only at delay 0 -> count 1
    assert img[3, 3] == 2 and img[2, 0] == 2
    assert img[3, 1] == 1
    assert int(img.max()) == 2
    assert "tagged ≥1: 3" in summary.text()
    assert "dead pixels = 1" in summary.text()

    spin.setValue(2)
    img2 = view.getProcessedImage()
    assert img2[3, 1] == 0  # the count-1 pixel is masked by the min-tag filter
    assert int((img2 == 2).sum()) == 2  # only the two count==2 pixels remain
    assert "tagged ≥2: 2" in summary.text()
    # min_tag == max count must not collapse levels to (c, c) — that would
    # render the remaining pixels in the colormap's low color
    lo, hi = view.ui.histogram.region.getRegion()
    assert hi > lo


def _pump(qapp: QtWidgets.QApplication, predicate: Callable[[], bool], timeout: float = 10.0) -> bool:
    """Pump events until predicate() is true or timeout."""
    deadline = time.time() + timeout
    while not predicate() and time.time() < deadline:
        qapp.processEvents()
        time.sleep(0.01)
    return predicate()


def test_dialog_computes_and_populates(qapp):
    G2, sqmap, dqmap = make_synthetic()
    # cast: SimpleNamespace has no declared members, so mypy cannot check it
    # against the _XpcsFileLike protocol structurally
    fake = cast("_XpcsFileLike", types.SimpleNamespace(fname="fake.hdf", G2=G2, sqmap=sqmap, dqmap=dqmap))
    dlg = G2DebugDialog(fake, "MeanAbsoluteDeviation", 3.0, False)
    dlg.show()
    assert _pump(qapp, lambda: not dlg._worker_running)
    tab = dlg.findChild(QtWidgets.QTabWidget)
    assert tab is not None
    assert tab.count() == 2
    assert dlg.findChild(QtWidgets.QLabel, "g2_debug_header") is not None
    dlg.close()
    assert not dlg.isVisible()


def test_close_blocked_while_computing(qapp):
    gate = threading.Event()
    G2, sqmap, dqmap = make_synthetic()

    class SlowXfile:
        fname = "fake.hdf"
        sqmap: np.ndarray
        dqmap: np.ndarray

        @property
        def G2(self):
            gate.wait(timeout=10)
            return G2

    # class bodies don't see the test's locals, so set these from outside
    SlowXfile.sqmap = sqmap
    SlowXfile.dqmap = dqmap
    dlg = G2DebugDialog(SlowXfile(), "MeanAbsoluteDeviation", 3.0, False)
    dlg.show()
    assert _pump(qapp, lambda: dlg._worker.isRunning(), timeout=5.0)
    dlg.close()
    assert dlg.isVisible()  # close ignored while computing
    gate.set()
    assert _pump(qapp, lambda: not dlg._worker_running)
    assert dlg.findChild(QtWidgets.QTabWidget) is not None
    dlg.close()
    assert not dlg.isVisible()


def test_dialog_failed_path(qapp):
    shown = []
    _, sqmap, dqmap = make_synthetic()

    class BrokenXfile:
        fname = "fake.hdf"
        sqmap: np.ndarray
        dqmap: np.ndarray

        @property
        def G2(self):
            raise OSError("disk error")

    # class bodies don't see the test's locals, so set these from outside
    BrokenXfile.sqmap = sqmap
    BrokenXfile.dqmap = dqmap
    dlg = G2DebugDialog(BrokenXfile(), "MeanAbsoluteDeviation", 3.0, False)
    dlg._show_failure = lambda msg: shown.append(msg)  # type: ignore[method-assign]
    dlg.show()
    assert _pump(qapp, lambda: not dlg.isVisible(), timeout=10.0)
    assert len(shown) == 1
    assert "disk error" in shown[0]


def test_debug_button_wired(qapp, tmp_path):
    from pyxpcsviewer.gui.view.xpcs_viewer import XpcsViewer

    window = XpcsViewer(path=str(tmp_path))
    assert window.pushButton_G2_debug is not None
    assert window._g2_debug_dialog is None
    window.debug_G2_regroup()  # no selection: silent no-op, no dialog
    assert window._g2_debug_dialog is None


def test_bin_sweep_slider_fills_the_row(qapp, bundle):
    """The slider takes all horizontal space left over -- no trailing spacer."""
    host = _host()
    build_debug_plots(host, bundle, "fake.hdf", "MeanAbsoluteDeviation", 3.0, False)
    panel = host.findChild(_BinSweepPanel)
    top = panel.layout().itemAt(0).layout()
    items = [top.itemAt(i) for i in range(top.count())]
    assert all(it.spacerItem() is None for it in items)
    assert items[-1].widget() is panel.slider
    assert panel.slider.sizePolicy().horizontalPolicy() == QtWidgets.QSizePolicy.Policy.Expanding


def test_bin_sweep_plots_are_light_themed(qapp, bundle):
    """White canvas with black axes/labels, despite pyqtgraph's dark global config."""
    host = _host()
    build_debug_plots(host, bundle, "fake.hdf", "MeanAbsoluteDeviation", 3.0, False)
    panel = host.findChild(_BinSweepPanel)
    assert panel.glw.backgroundBrush().color().name() == "#ffffff"
    for item in (it for it in panel.glw.ci.items if isinstance(it, pg.PlotItem)):
        for name in ("left", "bottom"):
            axis = item.getAxis(name)
            assert axis.pen().color().name() == "#000000"
            assert axis.textPen().color().name() == "#000000"
        assert item.titleLabel.opts["color"] == "#000000"


def test_header_reports_the_outlier_target(qapp):
    """The header names the target the bundle was actually built with, so it
    cannot drift from what the panels plot."""
    G2, sqmap, dqmap = make_synthetic()
    host = _host()
    b = compute_g2_debug_bundle(sqmap, dqmap, G2, outlier_threshold=3.0, target="G20")
    build_debug_plots(host, b, "fake.hdf", "MeanAbsoluteDeviation", 3.0, False)
    header = host.findChild(QtWidgets.QLabel, "g2_debug_header")
    assert "target=G20" in header.text()
    assert "min_tag=1" in header.text()


def test_bin_sweep_labels_the_plotted_quantity(qapp):
    """The histograms are of `target`, not always g2 -- say so on the axis."""
    G2, sqmap, dqmap = make_synthetic()
    host = _host()
    b = compute_g2_debug_bundle(sqmap, dqmap, G2, outlier_threshold=3.0, target="G20")
    build_debug_plots(host, b, "fake.hdf", "MeanAbsoluteDeviation", 3.0, False)
    panel = host.findChild(_BinSweepPanel)
    item = next(it for it in panel.glw.ci.items if isinstance(it, pg.PlotItem))
    assert "G20" in item.getAxis("bottom").labelString()


def test_bad_map_slider_presets_to_the_configured_min_tag(qapp, bundle):
    """This panel is how you pick Min Tag, so it opens on the current value."""
    host = _host()
    build_debug_plots(host, bundle, "fake.hdf", "MeanAbsoluteDeviation", 3.0, False, 2)
    spin = host.findChild(QtWidgets.QSpinBox, "g2_debug_mintag_spin")
    assert spin.value() == 2


def test_dialog_forwards_target_to_the_bundle(qapp):
    """The dialog must compute on the target it was opened with, or it
    visualizes something other than what ReGroup will do."""
    G2, sqmap, dqmap = make_synthetic()
    fake = cast("_XpcsFileLike", types.SimpleNamespace(fname="fake.hdf", G2=G2, sqmap=sqmap, dqmap=dqmap))
    dlg = G2DebugDialog(fake, "MeanAbsoluteDeviation", 3.0, False, "g2-per-pixel")
    assert _pump(qapp, lambda: not dlg._worker_running)
    header = dlg.findChild(QtWidgets.QLabel, "g2_debug_header")
    assert "target=g2-per-pixel" in header.text()
    dlg.close()
