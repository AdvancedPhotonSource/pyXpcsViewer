# Copyright © UChicago Argonne LLC
# See LICENSE file for details
"""Offscreen tests for the G2 outlier debug dialog's plot building.

build_debug_plots() is exercised directly with synthetic bundles from
compute_g2_debug_bundle — no real HDF5 file, no worker thread. The
worker/dialog lifecycle and the main-window wiring are tested later in
this file (see test_close_blocked_while_computing / test_debug_button_wired).
"""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import numpy as np
import pytest

pytest.importorskip("PySide6")

import pyqtgraph as pg
from PySide6 import QtWidgets

from pyxpcsviewer.core.g2_utils import compute_g2_debug_bundle
from pyxpcsviewer.gui.view.g2_debug_dialog import _BadMapPanel, _BinSweepPanel, _DelaySweepPanel, build_debug_plots


def make_synthetic():
    """(2 delays, 3 ch, 4x4) G2: dead pixel (0,0); sq 2 rows 2-3 hold two
    outliers — pixel 15=(3,3) and pixel 8=(2,0) at 10.0 at BOTH delays."""
    IP = np.ones((2, 4, 4), dtype=np.float32)
    IP[:, 3, 3] = 10.0
    IP[:, 2, 0] = 10.0
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


def _paged_bundle():
    """1 delay, (8, 16) image, 128 sq bins (one per pixel) -> 3 pages of 60."""
    G2 = np.zeros((1, 3, 8, 16), dtype=np.float32)
    G2[:, 0] = 1.0
    G2[:, 1] = 1.0
    G2[:, 2] = 1.0
    sqmap = np.arange(1, 129, dtype=np.uint16).reshape(8, 16)
    dqmap = np.ones((8, 16), dtype=np.uint16)
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


def test_bin_sweep_spin_switches_bin(qapp, bundle):
    host = _host()
    build_debug_plots(host, bundle, "fake.hdf", "MeanAbsoluteDeviation", 3.0, False)
    panel = host.findChild(_BinSweepPanel)
    spin = host.findChild(QtWidgets.QSpinBox, "g2_debug_sq_spin")
    spin.setValue(2)
    plot0 = next(it for it in panel.glw.ci.items if isinstance(it, pg.PlotItem))
    assert "out=2" in plot0.titleLabel.text  # pixels 15 and 8 flagged
    spin.setValue(1)
    plot0 = next(it for it in panel.glw.ci.items if isinstance(it, pg.PlotItem))
    assert "out=0" in plot0.titleLabel.text


def test_bin_sweep_all_zero_bin(qapp):
    host = _host()
    build_debug_plots(host, _zero_bin_bundle(), "fake.hdf", "MeanAbsoluteDeviation", 3.0, False)
    panel = host.findChild(_BinSweepPanel)
    panel.spin.setValue(2)
    plot0 = next(it for it in panel.glw.ci.items if isinstance(it, pg.PlotItem))
    assert "all zero" in plot0.titleLabel.text


def test_delay_sweep_paging(qapp):
    host = _host()
    build_debug_plots(host, _paged_bundle(), "fake.hdf", "MeanAbsoluteDeviation", 3.0, False)
    label = host.findChild(QtWidgets.QLabel, "g2_debug_page_label")
    prev = host.findChild(QtWidgets.QToolButton, "g2_debug_prev_btn")
    next_ = host.findChild(QtWidgets.QToolButton, "g2_debug_next_btn")
    assert label.text() == "page 1/3"
    assert not prev.isEnabled()
    assert next_.isEnabled()
    next_.click()
    assert label.text() == "page 2/3"
    next_.click()
    assert label.text() == "page 3/3"
    assert not next_.isEnabled()
    prev.click()
    assert label.text() == "page 2/3"


def test_delay_sweep_plot_counts(qapp):
    host = _host()
    build_debug_plots(host, _paged_bundle(), "fake.hdf", "MeanAbsoluteDeviation", 3.0, False)
    panel = host.findChild(_DelaySweepPanel)
    plots = [it for it in panel.glw.ci.items if isinstance(it, pg.PlotItem)]
    assert len(plots) == 60  # first page: bins 1-60
    panel._goto_page(2)
    plots = [it for it in panel.glw.ci.items if isinstance(it, pg.PlotItem)]
    assert len(plots) == 8  # last page: bins 121-128


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
    # pixels 15=(3,3) and 8=(2,0) are flagged at both delays -> count 2
    assert img[3, 3] == 2 and img[2, 0] == 2
    assert int(img.max()) == 2
    assert "tagged ≥1: 2" in summary.text()
    assert "dead pixels = 1" in summary.text()

    spin.setValue(2)
    img2 = view.getProcessedImage()
    assert int((img2 == 2).sum()) == 2  # only the two count==2 pixels remain
    assert "tagged ≥2: 2" in summary.text()
