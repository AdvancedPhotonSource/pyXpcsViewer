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

import warnings

import numpy as np
import pytest

pytest.importorskip("PySide6")

from pyxpcsviewer.gui.control.plot.g2_mod import _setup_subplots, pg_plot, pg_plot_one_g2


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


class _FakePlotAxis(_FakeAxis):
    """Adds the remaining axis methods pg_plot() calls, so pg_plot can run end to end."""

    def __init__(self):
        super().__init__()
        self.plot_calls = []

    def setTitle(self, *args, **kwargs):
        pass

    def setLabel(self, *args, **kwargs):
        pass

    def setRange(self, **kwargs):
        pass

    def setLogMode(self, **kwargs):
        pass

    def addItem(self, *args, **kwargs):
        pass

    def plot(self, *args, **kwargs):
        self.plot_calls.append({"args": args, **kwargs})


class _FakePlotHandler(_FakeHandler):
    def addPlot(self, row, col):
        ax = _FakePlotAxis()
        self.axes.append(ax)
        return ax


class _FakeXpcsFile:
    """Minimal stand-in for XpcsFile, covering only what pg_plot()/get_g2_data() touch."""

    def __init__(self, label, num_qval=2):
        self.atype = ["Multitau"]
        self.label = label
        self.fit_summary = None
        num_tau = 3
        self._tel = np.logspace(-5, 0, num_tau)
        self._g2 = np.ones((num_tau, num_qval))
        self._g2_err = np.full((num_tau, num_qval), 0.01)
        self._q = np.linspace(0.01, 0.02, num_qval)
        self._labels = [f"q={q:.4f}" for q in self._q]

    def get_g2_data(self, qrange=None, trange=None):
        return self._q, self._tel, self._g2, self._g2_err, self._labels


def test_pg_plot_single_layout_does_not_raise_and_uses_qvalue_labels():
    """Regression test: plot_type="single" left `label` unbound in the per-curve
    plot call, raising UnboundLocalError as soon as a user picked the "single"
    G2 layout (one subplot per file, one curve per Q-value).
    """
    hdl = _FakePlotHandler()
    xf_list = [_FakeXpcsFile("fileA"), _FakeXpcsFile("fileB")]

    pg_plot(hdl, xf_list, q_range=None, t_range=None, y_range=None, rows=[], plot_type="single")

    assert len(hdl.axes) == len(xf_list)
    for ax, xf in zip(hdl.axes, xf_list):
        names = [call["name"] for call in ax.plot_calls]
        assert names == xf._labels


def test_pg_plot_one_g2_drops_zero_tau_instead_of_warning():
    """Regression test: some result files' delay_list starts at tau=0 (zero-lag).
    Feeding that straight into np.log10 raised "divide by zero encountered in
    log10" and produced a -inf point instead of just being excluded from the
    log-scale time axis.
    """
    ax = _FakePlotAxis()
    x = np.array([0.0, 1e-5, 1e-4, 1e-3])
    y = np.array([2.0, 1.8, 1.5, 1.1])
    dy = np.array([0.1, 0.1, 0.1, 0.1])

    with warnings.catch_warnings():
        warnings.simplefilter("error", RuntimeWarning)
        pg_plot_one_g2(ax, x, y, dy, color=(0, 0, 0), label="q=0.01", symbol="o")

    plotted_x, plotted_y = ax.plot_calls[0]["args"]
    assert list(plotted_x) == [1e-5, 1e-4, 1e-3]
    assert list(plotted_y) == [1.8, 1.5, 1.1]
