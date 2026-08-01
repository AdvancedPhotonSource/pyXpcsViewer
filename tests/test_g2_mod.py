# Copyright © UChicago Argonne LLC
# See LICENSE file for details
"""Tests for pyxpcsviewer.gui.control.plot.g2_mod._setup_subplots.

Focus: show_label must actually gate whether a legend is added, not just
which legend *style* is used. Before the fix, pg_plot's call site
(_setup_subplots(hdl, num_figs, num_col, y_auto, show_label)) positionally
bound show_label to the stability_legend parameter -- so unchecking the g2
tab's "show label" checkbox only swapped legend styles instead of removing
the legend. pg_plot_stability's call site additionally passed
stability_legend=True as a keyword on top of that same positional slot,
which raised "got multiple values for argument 'stability_legend'" any time
the g2_stability tab tried to plot.
"""

from pyxpcsviewer.gui.control.plot.g2_mod import _setup_subplots


class _FakeLegend:
    def anchor(self, **kwargs):
        pass


class _FakeAxis:
    def __init__(self):
        self.legend_calls = []

    def addLegend(self, **kwargs):
        self.legend_calls.append(kwargs)
        return _FakeLegend()

    def setMouseEnabled(self, **kwargs):
        pass


class _FakeHandler:
    def __init__(self):
        self.axes = []

    def addPlot(self, row, col):
        ax = _FakeAxis()
        self.axes.append(ax)
        return ax

    def adjust_canvas_size(self, **kwargs):
        pass

    def clear(self):
        pass


def test_show_label_false_skips_legend_g2_tab_call_pattern():
    hdl = _FakeHandler()
    axes = _setup_subplots(hdl, 1, 4, False, False)
    assert axes[0].legend_calls == []


def test_show_label_true_adds_legend_g2_tab_call_pattern():
    hdl = _FakeHandler()
    axes = _setup_subplots(hdl, 1, 4, False, True)
    assert len(axes[0].legend_calls) == 1


def test_stability_call_pattern_does_not_raise_and_respects_show_label():
    hdl = _FakeHandler()
    axes = _setup_subplots(hdl, 1, 4, False, True, stability_legend=True)
    assert len(axes[0].legend_calls) == 1

    hdl = _FakeHandler()
    axes = _setup_subplots(hdl, 1, 4, False, False, stability_legend=True)
    assert axes[0].legend_calls == []
