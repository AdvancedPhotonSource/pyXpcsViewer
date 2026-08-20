# Copyright © UChicago Argonne LLC
# See LICENSE file for details
"""Tests for JobManager.submit_g2_regroup bookkeeping.

Exercises WorkerSlot + G2RegroupWorker together through a real QThreadPool
(catching the classic PySide6 "worker garbage-collected before the background
thread runs it" pitfall that a fully-synchronous unit test would miss), while
calling submit_g2_regroup as an unbound method against a minimal stand-in
object instead of a real JobManager. Constructing a real JobManager starts
an unrelated fit-pool warm-up (a ProcessPoolExecutor forked on a background
QThreadPool thread) that deadlocks under this sandbox's fork() restrictions
when combined with this file's event-loop polling.
"""

import os
import time
from collections.abc import Callable

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

pytest.importorskip("PySide6")

from PySide6 import QtCore, QtWidgets

from pyxpcsviewer.gui.control.background_job import WorkerSlot
from pyxpcsviewer.gui.control.job_manager import JobManager


@pytest.fixture
def qapp():
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    yield app


def _pump(qapp: QtWidgets.QApplication, predicate: Callable[[], bool], timeout: float = 5.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        qapp.processEvents()
        if predicate():
            return True
        time.sleep(0.01)
    return predicate()


class _FakePlots:
    def __init__(self, exc=None):
        self.calls = []
        self._exc = exc

    def process_G2_regroup(self, **kwargs):
        self.calls.append(kwargs)
        if self._exc is not None:
            raise self._exc


class _JobsStandIn:
    """Just the attributes JobManager.submit_g2_regroup touches -- avoids
    JobManager.__init__'s fit-pool warm-up (see module docstring)."""

    def __init__(self):
        self.thread_pool = QtCore.QThreadPool()
        self._g2_regroup = WorkerSlot()


def test_submit_g2_regroup_runs_worker_and_reports_success(qapp):
    jobs = _JobsStandIn()
    plots = _FakePlots()
    results = []

    worker = JobManager.submit_g2_regroup(jobs, plots, {"rows": [0]}, on_finished=results.append)

    assert worker is not None
    assert jobs._g2_regroup.busy  # occupied immediately, before the thread runs
    assert _pump(qapp, lambda: not jobs._g2_regroup.busy)

    assert plots.calls == [{"rows": [0]}]
    assert results == [None]


def test_submit_g2_regroup_reports_error_and_frees_slot(qapp):
    jobs = _JobsStandIn()
    plots = _FakePlots(exc=ValueError("no qmap"))
    results = []

    JobManager.submit_g2_regroup(jobs, plots, {"rows": [0]}, on_finished=results.append)

    assert _pump(qapp, lambda: not jobs._g2_regroup.busy)

    assert len(results) == 1
    assert "no qmap" in results[0]


def test_submit_g2_regroup_refuses_when_already_busy(qapp):
    jobs = _JobsStandIn()
    jobs._g2_regroup._worker = "sentinel-occupying-the-slot"  # simulate a job already in flight
    plots = _FakePlots()

    worker = JobManager.submit_g2_regroup(jobs, plots, {}, on_finished=lambda *_: None)

    assert worker is None
    assert plots.calls == []
