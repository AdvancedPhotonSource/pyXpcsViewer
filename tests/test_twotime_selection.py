# Copyright © UChicago Argonne LLC
# See LICENSE file for details
"""Tests for PlotController.plot_twotime's q-bin selection memory.

Focus: when the active twotime file changes, the caller-supplied selection
index should be preserved by position and clamped to the new file's q-bin
count, not silently reset to 0 -- see
docs/superpowers/specs/2026-08-03-twotime-qbin-memory-design.md.
"""

import pytest

from pyxpcsviewer.gui.control.plot_controller import PlotController


class _FakeXpcsFile:
    def __init__(self, fname, num_qbins):
        self.fname = fname
        self._labels = [f"q-bin {i}" for i in range(num_qbins)]

    def get_twotime_qbin_labels(self):
        return list(self._labels)


class _FakeModel:
    def __init__(self, xf_list):
        self._xf_list = xf_list

    def get_xf_list(self, rows=None, filter_atype=None, filter_fitted=False):
        return self._xf_list


@pytest.fixture(autouse=True)
def _stub_render(monkeypatch):
    """Replace the real pyqtgraph-driven renderer with a no-op.

    plot_twotime's job under test is index bookkeeping, not rendering; the
    real twotime.plot_twotime needs live XpcsFile data and pyqtgraph
    widgets neither of which this test constructs.
    """
    monkeypatch.setattr(
        "pyxpcsviewer.gui.control.plot_controller.twotime.plot_twotime",
        lambda *args, **kwargs: None,
    )


def test_first_render_uses_given_selection_and_returns_labels():
    xf = _FakeXpcsFile("a.hdf", num_qbins=5)
    controller = PlotController(_FakeModel([xf]))

    labels, selection = controller.plot_twotime(hdl={}, selection=2)

    assert labels == ["q-bin 0", "q-bin 1", "q-bin 2", "q-bin 3", "q-bin 4"]
    assert selection == 2


def test_selection_preserved_across_file_switch_with_enough_qbins():
    xf_a = _FakeXpcsFile("a.hdf", num_qbins=5)
    xf_b = _FakeXpcsFile("b.hdf", num_qbins=5)
    controller = PlotController(_FakeModel([xf_a]))
    controller.plot_twotime(hdl={}, selection=3)

    controller.model = _FakeModel([xf_b])
    labels, selection = controller.plot_twotime(hdl={}, selection=3)

    assert labels == ["q-bin 0", "q-bin 1", "q-bin 2", "q-bin 3", "q-bin 4"]
    assert selection == 3


def test_selection_clamped_when_new_file_has_fewer_qbins():
    xf_a = _FakeXpcsFile("a.hdf", num_qbins=5)
    xf_b = _FakeXpcsFile("b.hdf", num_qbins=2)
    controller = PlotController(_FakeModel([xf_a]))
    controller.plot_twotime(hdl={}, selection=4)

    controller.model = _FakeModel([xf_b])
    labels, selection = controller.plot_twotime(hdl={}, selection=4)

    assert labels == ["q-bin 0", "q-bin 1"]
    assert selection == 1


def test_same_file_reselected_returns_none_labels_and_given_selection():
    xf = _FakeXpcsFile("a.hdf", num_qbins=5)
    controller = PlotController(_FakeModel([xf]))
    controller.plot_twotime(hdl={}, selection=1)

    labels, selection = controller.plot_twotime(hdl={}, selection=1)

    assert labels is None
    assert selection == 1


def test_no_matching_twotime_file_returns_none_and_given_selection():
    controller = PlotController(_FakeModel([]))

    labels, selection = controller.plot_twotime(hdl={}, selection=3)

    assert labels is None
    assert selection == 3
