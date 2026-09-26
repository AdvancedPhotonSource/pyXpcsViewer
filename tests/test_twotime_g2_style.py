# Copyright © UChicago Argonne LLC
# See LICENSE file for details
"""Tests for the Two-time tab's g2 style (semilogx/linear) x-axis toggle.

plot_twotime_g2 draws g2_full/g2_partial inside mp_2t_map's "c2g2" plot and
used to hardcode setLogMode(x=True, ...). comboBox_g2_style lets the user
pick "semilogx" (default, matching the old hardcoded behavior) or "linear".
"""

import numpy as np

from pyxpcsviewer.gui.control.plot.twotime import plot_twotime_g2


class _FakePlotWidget:
    def __init__(self):
        self.log_mode = None
        self.cleared = False
        self.auto_ranged = False

    def clear(self):
        self.cleared = True

    def setLabel(self, *args, **kwargs):
        pass

    def plot(self, *args, **kwargs):
        pass

    def setLogMode(self, x=False, y=False):
        self.log_mode = (x, y)

    def autoRange(self):
        self.auto_ranged = True


def _c2_result():
    return {
        "g2_full": np.linspace(1.0, 1.5, 10),
        "g2_partial": np.linspace(1.0, 1.5, 30).reshape(3, 10),
        "acquire_period": 0.001,
    }


def test_default_style_is_semilogx():
    hdl = {"c2g2": _FakePlotWidget()}
    plot_twotime_g2(hdl, _c2_result())
    assert hdl["c2g2"].log_mode == (True, False)


def test_explicit_semilogx_style():
    hdl = {"c2g2": _FakePlotWidget()}
    plot_twotime_g2(hdl, _c2_result(), g2_style="semilogx")
    assert hdl["c2g2"].log_mode == (True, False)


def test_linear_style_uses_linear_x():
    hdl = {"c2g2": _FakePlotWidget()}
    plot_twotime_g2(hdl, _c2_result(), g2_style="linear")
    assert hdl["c2g2"].log_mode == (False, False)
