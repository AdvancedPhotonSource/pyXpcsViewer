# Copyright © UChicago Argonne LLC
# See LICENSE file for details
"""Switching to a longer two-time file must auto-range to the whole C2 map.

plot_twotime used to call ``setImage(autoRange=True)`` before refreshing the
zoom-out floor from apply_zoom_limit. ViewBox ``maxXRange``/``maxYRange``
also cap what an auto-range may produce, so the floor left behind by a short
acquisition (say 10 s) clipped the auto-range of a following 100 s file to the
old extent -- only the lower-left corner showed until the user hit "View All".
Drives the real plot_twotime with a duck-typed XpcsFile and real pyqtgraph
widgets so the ViewBox clamping is exercised for real.
"""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import numpy as np
import pytest

pytest.importorskip("PySide6")


@pytest.fixture
def qapp():
    from PySide6 import QtWidgets

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    yield app


class _FakeTwotimeFile:
    """Minimal stand-in for XpcsFile with Twotime data of ``n_frames`` x ``dt`` seconds."""

    atype = ("Twotime",)

    def __init__(self, n_frames, dt):
        self.n_frames, self.dt = n_frames, dt

    def get_twotime_maps(self, scale, auto_crop, highlight_xy, selection):
        return np.zeros((8, 8), dtype=np.int32), np.ones((8, 8), dtype=np.float32), None

    def get_twotime_c2(self, selection, correct_diag):
        n = self.n_frames
        return {
            "c2_mat": np.ones((n, n), dtype=np.float32),
            "delta_t": self.dt,
            "acquire_period": self.dt,
            "g2_full": np.ones(n, dtype=np.float32),
            "g2_partial": np.ones((2, n), dtype=np.float32),
        }


@pytest.fixture
def twotime_hdl(qapp):
    import pyqtgraph as pg

    from pyxpcsviewer.gui.view.plothandler import ImageViewPlotItem

    layout = pg.GraphicsLayoutWidget()
    tt = ImageViewPlotItem()
    tt.resize(400, 400)
    hdl = {
        "saxs": pg.ImageItem(),
        "dqmap": pg.ImageItem(),
        "tt": tt,
        "c2g2": layout.addPlot(),
    }
    tt.show()
    qapp.processEvents()
    try:
        yield hdl
    finally:
        tt.close()
        layout.close()


def _visible_span(hdl):
    (x0, x1), (y0, y1) = hdl["tt"].getView().vb.viewRange()
    return x1 - x0, y1 - y0


def test_longer_acquisition_auto_ranges_to_full_extent(qapp, twotime_hdl):
    from pyxpcsviewer.gui.control.plot.twotime import plot_twotime

    plot_twotime(_FakeTwotimeFile(n_frames=100, dt=0.1), twotime_hdl)  # 10 s
    qapp.processEvents()
    plot_twotime(_FakeTwotimeFile(n_frames=1000, dt=0.1), twotime_hdl)  # 100 s
    qapp.processEvents()

    span_x, span_y = _visible_span(twotime_hdl)
    assert span_x >= 100.0 and span_y >= 100.0, (
        f"view shows only {span_x:.1f} s x {span_y:.1f} s of the 100 s C2 map; "
        "the previous file's zoom limit clipped the auto-range"
    )


def test_shorter_acquisition_still_fills_the_view(qapp, twotime_hdl):
    from pyxpcsviewer.gui.control.plot.twotime import plot_twotime

    plot_twotime(_FakeTwotimeFile(n_frames=1000, dt=0.1), twotime_hdl)  # 100 s
    qapp.processEvents()
    plot_twotime(_FakeTwotimeFile(n_frames=100, dt=0.1), twotime_hdl)  # 10 s
    qapp.processEvents()

    span_x, span_y = _visible_span(twotime_hdl)
    # The whole 10 s map must be visible, and the view must have zoomed in to
    # fit it rather than staying at the 100 s extent. The aspect ratio is
    # locked and the plot area is not square, so only the tighter axis is
    # compared against the padded 10 s extent.
    assert span_x >= 10.0 and span_y >= 10.0, f"map not fully visible: {span_x:.1f} x {span_y:.1f}"
    assert min(span_x, span_y) <= 15.0, f"view did not zoom in to the 10 s map: {span_x:.1f} x {span_y:.1f}"
