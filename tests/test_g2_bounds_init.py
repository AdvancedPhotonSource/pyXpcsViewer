# Copyright © UChicago Argonne LLC
# See LICENSE file for details
"""Tests for the g2 tau-bound (g2_bmin/g2_bmax) one-shot auto-population.

Focus: XpcsViewer.init_g2() used to overwrite g2_bmin/g2_bmax unconditionally
on every g2 replot, silently clobbering a manually-tightened fit bound each
time a different file was selected. It should now only auto-populate once
per target list -- the first g2 plot after the target list goes from empty
to non-empty -- and leave it alone afterward, until the list empties out and
gets a new target added.
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


@pytest.fixture
def window(qapp, tmp_path):
    from pyxpcsviewer.gui.view.xpcs_viewer import XpcsViewer

    win = XpcsViewer(path=str(tmp_path))
    yield win
    win.close()


def test_first_init_g2_populates_bounds(window):
    assert window._g2_bounds_initialized is False

    qd = np.array([0.01, 0.02, 0.03])
    tel = [np.array([1e-3, 1.0])]
    window.init_g2(qd, tel)

    assert window._g2_bounds_initialized is True
    assert window.g2_bmin.value() == pytest.approx(1e-3 / 20)
    assert window.g2_bmax.value() == pytest.approx(1.0 * 10)


def test_second_init_g2_does_not_clobber_manual_bound(window):
    window.init_g2(np.array([0.01]), [np.array([1e-3, 1.0])])

    # user manually tightens the bound after the first auto-populate
    window.g2_bmin.setValue(0.05)
    window.g2_bmax.setValue(5.0)

    # a different file is now selected -- a very different tau range
    window.init_g2(np.array([0.02]), [np.array([1e-2, 100.0])])

    assert window.g2_bmin.value() == pytest.approx(0.05)
    assert window.g2_bmax.value() == pytest.approx(5.0)


def test_add_target_unlocks_bounds_when_list_was_empty(window):
    from PySide6.QtCore import QItemSelectionModel

    window.init_g2(np.array([0.01]), [np.array([1e-3, 1.0])])
    window.g2_bmin.setValue(0.05)
    window.g2_bmax.setValue(5.0)
    assert window._g2_bounds_initialized is True
    assert len(window.model.target) == 0

    # Drive the real add_target() through a selected source-list entry
    # (rather than re-implementing its guard), so this exercises the actual
    # code path. The fake filename fails to load into an XpcsFile -- that's
    # fine, the unlock only needs the target list to have been empty *before*
    # the add attempt, which add_target() checks up front.
    window.model.source.append("fake.hdf")
    window.update_box(window.model.source, mode="source")
    sel_model = window.list_view_source.selectionModel()
    idx = window.list_view_source.model().index(0, 0)
    sel_model.select(idx, QItemSelectionModel.SelectionFlag.Select)

    window.add_target()

    assert window._g2_bounds_initialized is False

    window.init_g2(np.array([0.02]), [np.array([1e-2, 100.0])])
    assert window.g2_bmin.value() == pytest.approx(1e-2 / 20)
    assert window.g2_bmax.value() == pytest.approx(100.0 * 10)
