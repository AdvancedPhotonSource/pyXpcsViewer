# Copyright © UChicago Argonne LLC
# See LICENSE file for details
"""Smoke tests for pyxpcsviewer.gui.view.xpcs_viewer.XpcsViewer construction.

Focus: XpcsViewer.__init__ must not raise on a plain, data-free startup, and
_set_plot_backgrounds() must actually paint every ImageView white -- not just
avoid raising. This is the seam that caught two pyqtgraph 0.14.0 regressions:

1. ImageView.getView() returns a ViewBox for plain ImageView, but a PlotItem
   for ImageViewPlotItem (the two-time tab), and PlotItem has no
   setBackgroundColor of its own -- an AttributeError on startup.
2. ImageView.ui.histogram is a HistogramLUTWidget (a GraphicsView with its own
   scene/background), not just a HistogramLUTItem -- setting only the nested
   HistogramLUTItem.vb left the surrounding widget area black, since a
   ViewBox's background is independent of its enclosing GraphicsView's scene
   background. This second bug produced no exception, so it required
   asserting on the actual rendered background color, not just "didn't crash".
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


def test_xpcs_viewer_constructs_without_data(qapp, tmp_path):
    from pyxpcsviewer.gui.view.xpcs_viewer import XpcsViewer

    window = XpcsViewer(path=str(tmp_path))
    try:
        window._set_plot_backgrounds()

        for iv in (
            window.pg_saxs,
            window.pg_qmap,
            window.widget_g2map_qmap,
            window.pg_regroup_G2,
            window.mp_2t,
        ):
            assert iv.ui.histogram.backgroundBrush().color().name() == "#ffffff", (
                f"{iv} histogram widget background was not painted white"
            )
    finally:
        window.close()
