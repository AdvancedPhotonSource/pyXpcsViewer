# Copyright © UChicago Argonne LLC
# See LICENSE file for details
"""Tests for pyxpcsviewer.gui.control.plot.view_utils.apply_zoom_limit.

Focus: the computed maxXRange/maxYRange passed to ViewBox.setLimits, since
that's the actual mechanism that keeps users from scrolling an image down to
an invisible speck. Uses a bare duck-typed fake instead of a real pyqtgraph
ViewBox so the test doesn't need a QApplication.
"""

from pyxpcsviewer.gui.control.plot.view_utils import apply_zoom_limit


class _FakeViewBox:
    def __init__(self):
        self.limits = None

    def setLimits(self, **kwargs):
        self.limits = kwargs


class _FakeViewWithVb:
    """Stand-in for a pyqtgraph PlotItem, which exposes its ViewBox via .vb."""

    def __init__(self):
        self.vb = _FakeViewBox()


class _FakeImageView:
    def __init__(self, view):
        self._view = view

    def getView(self):
        return self._view


def test_plain_viewbox_gets_limits_from_image_shape():
    vb = _FakeViewBox()
    apply_zoom_limit(_FakeImageView(vb), (100, 200), min_zoom=0.25)
    assert vb.limits == {"maxXRange": 800.0, "maxYRange": 400.0}


def test_plotitem_style_view_uses_wrapped_vb():
    view = _FakeViewWithVb()
    apply_zoom_limit(_FakeImageView(view), (100, 200), min_zoom=0.25)
    assert view.vb.limits == {"maxXRange": 800.0, "maxYRange": 400.0}


def test_scale_factor_is_applied_before_dividing_by_min_zoom():
    vb = _FakeViewBox()
    # e.g. the twotime C2 image, scaled by delta_t via ImageItem.setScale()
    apply_zoom_limit(_FakeImageView(vb), (100, 200), min_zoom=0.25, scale=0.5)
    assert vb.limits == {"maxXRange": 400.0, "maxYRange": 200.0}


def test_none_or_too_short_shape_is_a_no_op():
    vb = _FakeViewBox()
    apply_zoom_limit(_FakeImageView(vb), None)
    apply_zoom_limit(_FakeImageView(vb), (5,))
    assert vb.limits is None
