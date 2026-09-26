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


def test_bin_sweep_wrapped_in_scroll_area(qapp, bundle):
    host = _host()
    build_debug_plots(host, bundle, "fake.hdf", "MeanAbsoluteDeviation", 3.0, False)
    panel = host.findChild(_BinSweepPanel)
    scroll = host.findChild(QtWidgets.QScrollArea, "g2_debug_hist_scroll")
    assert scroll is not None
    assert scroll.widget() is panel.glw


def test_bin_sweep_zero_checkbox_default_unchecked(qapp, bundle):
    host = _host()
    build_debug_plots(host, bundle, "fake.hdf", "MeanAbsoluteDeviation", 3.0, False)
    checkbox = host.findChild(QtWidgets.QCheckBox, "g2_debug_include_zero_checkbox")
    assert checkbox is not None
    assert checkbox.isChecked() is False


def test_bin_sweep_include_zero_checkbox_shows_zero_values(qapp):
    host = _host()
    build_debug_plots(host, _zero_bin_bundle(), "fake.hdf", "MeanAbsoluteDeviation", 3.0, False)
    panel = host.findChild(_BinSweepPanel)
    checkbox = host.findChild(QtWidgets.QCheckBox, "g2_debug_include_zero_checkbox")
    panel.spin.setValue(2)
    panel.spin.editingFinished.emit()
    assert "all zero" in _title(panel)  # unchanged default behavior

    checkbox.setChecked(True)
    assert "all zero" not in _title(panel)
    assert "n=4" in _title(panel)  # the 4 zero pixels in that row are now shown


def test_bin_sweep_smooth_bkg_nan_excluded_even_with_zero_checkbox(qapp):
    """NaN (no valid smooth-bkg reference) must stay excluded regardless of
    the include-zero-values checkbox -- it isn't a real value, unlike a
    photon-starved zero."""
    G2, sqmap, dqmap, scattering_1d = make_smooth_bkg_synthetic(scale=5.0)
    scattering_1d = scattering_1d.copy()
    scattering_1d[1] = np.nan  # sq bin 2 has no valid reference
    b = compute_g2_debug_bundle(
        sqmap, dqmap, G2, outlier_method="G2-smooth-bkg", outlier_threshold=3.0, scattering_1d=scattering_1d
    )
    host = _host()
    build_debug_plots(host, b, "fake.hdf", "G2-smooth-bkg", 3.0, False)
    panel = host.findChild(_BinSweepPanel)
    checkbox = host.findChild(QtWidgets.QCheckBox, "g2_debug_include_zero_checkbox")
    panel.spin.setValue(2)
    panel.spin.editingFinished.emit()
    assert "all zero" in _title(panel)
    checkbox.setChecked(True)
    assert "all zero" in _title(panel)  # still excluded -- NaN, not zero


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


def test_debug_button_wired(qapp, tmp_path, monkeypatch):
    from pyxpcsviewer.gui.view.xpcs_viewer import XpcsViewer

    warned = []
    monkeypatch.setattr(
        "pyxpcsviewer.gui.view.xpcs_viewer.QMessageBox.warning",
        lambda *args, **kwargs: warned.append(args),
    )
    window = XpcsViewer(path=str(tmp_path))
    assert window.pushButton_G2_debug is not None
    assert window._g2_debug_dialog is None
    window.debug_G2_regroup()  # empty target list: warn, no dialog
    assert window._g2_debug_dialog is None
    assert len(warned) == 1
    assert "No files in the target list" in warned[0][2]


def test_bin_sweep_slider_fills_the_row(qapp, bundle):
    """The slider takes all horizontal space the other controls leave over --
    no trailing spacer (the zero-values checkbox trails it as a real widget)."""
    host = _host()
    build_debug_plots(host, bundle, "fake.hdf", "MeanAbsoluteDeviation", 3.0, False)
    panel = host.findChild(_BinSweepPanel)
    top = panel.layout().itemAt(0).layout()
    items = [top.itemAt(i) for i in range(top.count())]
    assert all(it.spacerItem() is None for it in items)
    assert items[-1].widget() is panel.zero_checkbox
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
    b = compute_g2_debug_bundle(sqmap, dqmap, G2, outlier_threshold=3.0, target="G2")
    build_debug_plots(host, b, "fake.hdf", "MeanAbsoluteDeviation", 3.0, False)
    header = host.findChild(QtWidgets.QLabel, "g2_debug_header")
    assert "target=G2" in header.text()
    assert "min_tag=1" in header.text()


def test_bin_sweep_labels_the_plotted_quantity(qapp):
    """The histograms are of `target`, not always g2 -- say so on the axis."""
    G2, sqmap, dqmap = make_synthetic()
    host = _host()
    b = compute_g2_debug_bundle(sqmap, dqmap, G2, outlier_threshold=3.0, target="G2")
    build_debug_plots(host, b, "fake.hdf", "MeanAbsoluteDeviation", 3.0, False)
    panel = host.findChild(_BinSweepPanel)
    item = next(it for it in panel.glw.ci.items if isinstance(it, pg.PlotItem))
    assert "G2" in item.getAxis("bottom").labelString()


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


def make_smooth_bkg_synthetic(scale=5.0):
    """(2 delays, 3 ch, 4x4) G2 tracking scale*scattering_1d per sq bin, with
    a smooth-bkg outlier at pixel (0,0) delay 0 (g2=100 there, 1.0 elsewhere)."""
    n_delays = 2
    sqmap = np.zeros((4, 4), dtype=np.uint16)
    sqmap[:2, :] = 1
    sqmap[2:, :] = 2
    scattering_1d = np.array([10.0, 20.0])
    IP = np.zeros((n_delays, 4, 4))
    IF = np.zeros((n_delays, 4, 4))
    for idx, sq_val in enumerate(scattering_1d, start=1):
        mask = sqmap == idx
        IP[:, mask] = scale * sq_val
        IF[:, mask] = scale * sq_val
    g2 = np.ones((n_delays, 4, 4))
    g2[0, 0, 0] = 100.0
    G2 = np.stack([g2 * IP * IF, IP, IF], axis=1)
    dqmap = np.ones((4, 4), dtype=np.uint16)
    return G2, sqmap, dqmap, scattering_1d


def test_bundle_smooth_bkg_flags_the_bright_pixel_and_reports_scale():
    G2, sqmap, dqmap, scattering_1d = make_smooth_bkg_synthetic(scale=5.0)
    b = compute_g2_debug_bundle(
        sqmap, dqmap, G2, outlier_method="G2-smooth-bkg", outlier_threshold=3.0, scattering_1d=scattering_1d
    )
    assert b["target"] == "G2-smooth-bkg"
    assert b["scale"] == pytest.approx(5.0)
    assert b["bad"][0, 0]
    assert not b["bad"][1, 0]


def test_header_reports_the_smooth_bkg_scale():
    """The scale factor is central to what G2-smooth-bkg does; the header must
    show it, unlike the other two methods where there's no such factor."""
    G2, sqmap, dqmap, scattering_1d = make_smooth_bkg_synthetic(scale=5.0)
    host = _host()
    b = compute_g2_debug_bundle(
        sqmap, dqmap, G2, outlier_method="G2-smooth-bkg", outlier_threshold=3.0, scattering_1d=scattering_1d
    )
    build_debug_plots(host, b, "fake.hdf", "G2-smooth-bkg", 3.0, False)
    header = host.findChild(QtWidgets.QLabel, "g2_debug_header")
    assert "target=G2-smooth-bkg" in header.text()
    assert "scale=5" in header.text()


def test_header_omits_scale_for_non_smooth_bkg_methods():
    G2, sqmap, dqmap = make_synthetic()
    host = _host()
    b = compute_g2_debug_bundle(sqmap, dqmap, G2, outlier_threshold=3.0)
    build_debug_plots(host, b, "fake.hdf", "MeanAbsoluteDeviation", 3.0, False)
    header = host.findChild(QtWidgets.QLabel, "g2_debug_header")
    assert "scale=" not in header.text()


def test_bin_sweep_smooth_bkg_has_no_center_line():
    """G2-smooth-bkg is a flat threshold cut -- no per-bin center to draw."""
    G2, sqmap, dqmap, scattering_1d = make_smooth_bkg_synthetic(scale=5.0)
    host = _host()
    b = compute_g2_debug_bundle(
        sqmap, dqmap, G2, outlier_method="G2-smooth-bkg", outlier_threshold=3.0, scattering_1d=scattering_1d
    )
    build_debug_plots(host, b, "fake.hdf", "G2-smooth-bkg", 3.0, False)
    panel = host.findChild(_BinSweepPanel)
    item = next(it for it in panel.glw.ci.items if isinstance(it, pg.PlotItem))
    # exactly one InfiniteLine (the red hi/threshold bound); a center line
    # would be a second one
    lines = [ln for ln in item.items if isinstance(ln, pg.InfiniteLine)]
    assert len(lines) == 1


def test_dialog_forwards_saxs_1d_for_smooth_bkg_method(qapp):
    """The worker must pull scattering_1d from the file when the method needs
    it, or the smooth-bkg fit has nothing to fit against."""
    G2, sqmap, dqmap, scattering_1d = make_smooth_bkg_synthetic(scale=5.0)
    fake = cast(
        "_XpcsFileLike",
        types.SimpleNamespace(
            fname="fake.hdf", G2=G2, sqmap=sqmap, dqmap=dqmap, saxs_1d={"Iq": scattering_1d[None, :]}
        ),
    )
    dlg = G2DebugDialog(fake, "G2-smooth-bkg", 3.0, False)
    assert _pump(qapp, lambda: not dlg._worker_running)
    header = dlg.findChild(QtWidgets.QLabel, "g2_debug_header")
    assert "target=G2-smooth-bkg" in header.text()
    assert "scale=5" in header.text()
    dlg.close()
