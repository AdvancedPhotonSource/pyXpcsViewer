# Copyright © UChicago Argonne LLC
# See LICENSE file for details
"""Tests for G2RegroupWorker, which moves PlotController.process_G2_regroup
off the Qt GUI thread so a slow regroup (especially with outlier rejection
enabled) does not freeze the main window.
"""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

pytest.importorskip("PySide6")

from PySide6 import QtWidgets

from pyxpcsviewer.gui.control.g2_regroup_worker import G2RegroupWorker


@pytest.fixture
def qapp():
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    yield app


class _FakePlots:
    def __init__(self, exc=None):
        self.calls = []
        self._exc = exc

    def process_G2_regroup(self, **kwargs):
        self.calls.append(kwargs)
        if self._exc is not None:
            raise self._exc


def test_worker_calls_process_G2_regroup_and_emits_finished_with_none(qapp):
    plots = _FakePlots()
    worker = G2RegroupWorker(plots, {"rows": [0], "outlier_threshold": 3.0})
    results = []
    worker.signals.finished.connect(results.append)

    worker.run()

    assert plots.calls == [{"rows": [0], "outlier_threshold": 3.0}]
    assert results == [None]


def test_worker_emits_finished_with_error_message_on_exception(qapp):
    plots = _FakePlots(exc=ValueError("no qmap"))
    worker = G2RegroupWorker(plots, {"rows": [0]})
    results = []
    worker.signals.finished.connect(results.append)

    worker.run()

    assert len(results) == 1
    assert "ValueError" in results[0]
    assert "no qmap" in results[0]
