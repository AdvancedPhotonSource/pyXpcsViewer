# G2 Outlier Debug Dialog Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a "Debug" button to the G2_regroup tab's Group Setting box that opens a pyqtgraph dialog visualizing what the configured outlier settings do to the first selected Multitau file (per-sq-bin g2_pixel histograms + bad-pixel detector map).

**Architecture:** A pure `compute_g2_debug_bundle()` in `core/g2_utils.py` mirrors `compute_g2`'s preprocessing (dead-pixel mask → `normalize_g2` → `find_g2_pixel_outliers`) and returns arrays. A new self-contained module `gui/view/g2_debug_dialog.py` holds a `G2DebugWorker(QThread)` (HDF5 load + compute off the main thread) and `G2DebugDialog(QDialog)` whose plot building lives in a plain `build_debug_plots()` function so offscreen tests can exercise it with synthetic bundles. Spec: `docs/superpowers/specs/2026-08-19-g2-debug-dialog-design.md`.

**Tech Stack:** Python 3.10+, PySide6, pyqtgraph 0.14.0, numpy, h5py, pytest.

## Global Constraints

- Test/lint/type-check env: `/local/MQICHU/envs/l2604_xpcs` (has `python`, `mypy`, `ruff`, `pyside6-uic`, `pyside6-rcc`). Run from repo root `/home/beams4/MQICHU/Tools_cloud/xpcs_toolchains/pyXpcsViewer`.
- Test command pattern: `/local/MQICHU/envs/l2604_xpcs/bin/python -m pytest tests/<file> -v`
- Lint: `ruff check <files>` and `ruff format <files>` (ruff at `~/.local/bin/ruff`).
- Type check: `/local/MQICHU/envs/l2604_xpcs/bin/mypy <files>` — **strict mode over the whole repo** (`pyproject.toml [tool.mypy] files="." strict=true`; `tests.*` gets `allow_untyped_defs=true`). New code must be fully annotated and mypy-clean. **`src/pyxpcsviewer/core/g2_utils.py` currently has 19 pre-existing mypy errors** — do not fix them, but verify your additions don't increase the count (run mypy on the file before/after; count must stay 19).
- **Never hand-edit** `src/pyxpcsviewer/gui/view/viewer_ui.py` or `icons_rc.py` — regenerate via `src/pyxpcsviewer/gui/view/convert_ui_to_py.sh` (needs `pyside6-uic`/`pyside6-rcc` on PATH, i.e. `PATH=/local/MQICHU/envs/l2604_xpcs/bin:$PATH`).
- pyqtgraph only in the dialog — no matplotlib.
- Working branch: `mc_dev`. Commit after each task with message ending `Co-Authored-By: Claude <noreply@anthropic.com>`.
- pyqtgraph API notes (0.14.0): histograms are drawn with `pg.BarGraphItem`; `PlotItem.addLine(x=..., pen=...)` draws vertical lines; `PlotItem.getTitle()` returns a `TextItem` (has `.toPlainText()`); `GraphicsLayoutWidget.clear()` + `addPlot(row=, col=)`; `GraphicsLayoutWidget.ci.items` is the list of added items; `ImageView.getImage()` returns the array last passed to `setImage`.

---

### Task 1: Core `compute_g2_debug_bundle`

**Files:**
- Modify: `src/pyxpcsviewer/core/g2_utils.py` (append new function at end of file)
- Test: `tests/test_g2_utils.py` (new)

**Interfaces:**
- Consumes: existing `normalize_g2(G2_3ch)` (line 33 of g2_utils.py) and `find_g2_pixel_outliers(sqmap_1d, g2_pixel, threshold, method, combine_outlier)` (line 77) — both in `core/g2_utils.py`.
- Produces: `compute_g2_debug_bundle(sqmap: np.ndarray, dqmap: np.ndarray, G2: np.ndarray, outlier_method: str = "MeanAbsoluteDeviation", outlier_threshold: float = 3.0, combine_outlier: bool = False) -> dict` returning keys: `g2_pixel` (ndarray float, `(n_delays, n_pixels)`), `bad` (ndarray bool, same shape), `sqmap_1d` / `dqmap_1d` (ndarray int, dead pixels set to 0), `img_shape` (`tuple[int, int]`), `n_delays` / `n_sq` / `n_dq` / `n_dead` (int). Task 2+ consume this dict shape.

- [x] **Step 1: Write the failing test**

Create `tests/test_g2_utils.py`:

```python
# Copyright © UChicago Argonne LLC
# See LICENSE file for details
"""Tests for pyxpcsviewer.core.g2_utils.compute_g2_debug_bundle.

The bundle is what the G2 outlier debug dialog plots. It must mirror
compute_g2's preprocessing (dead-pixel masking, normalize_g2) and its
outlier pass (find_g2_pixel_outliers) exactly, so the dialog shows what
ReGroup actually sees.
"""

import numpy as np

from pyxpcsviewer.core.g2_utils import compute_g2_debug_bundle, find_g2_pixel_outliers, normalize_g2


def make_data():
    """(2 delays, 3 ch, 4x4) synthetic G2 with known outliers.

    Flat pixel index = row*4+col:
      0  = (0,0): IF1=IF2=0 at every delay -> dead
      15 = (3,3): g2_pixel=10 at delay 0 only (sq 2)
      8  = (2,0): g2_pixel=10 at delay 1 only (sq 2)
    sq 1 = rows 0-1 (pixels 0-7), sq 2 = rows 2-3 (pixels 8-15); single dq bin.
    """
    IP = np.ones((2, 4, 4), dtype=np.float32)
    IP[0, 3, 3] = 10.0
    IP[1, 2, 0] = 10.0
    IF = np.ones((2, 4, 4), dtype=np.float32)
    IF[:, 0, 0] = 0.0
    G2 = np.stack([IP, IF, IF], axis=1).astype(np.float32)  # (2, 3, 4, 4)
    sqmap = np.zeros((4, 4), dtype=np.uint16)
    sqmap[:2, :] = 1
    sqmap[2:, :] = 2
    dqmap = np.ones((4, 4), dtype=np.uint16)
    return G2, sqmap, dqmap


def test_bundle_shapes():
    G2, sqmap, dqmap = make_data()
    b = compute_g2_debug_bundle(sqmap, dqmap, G2)
    assert b["g2_pixel"].shape == (2, 16)
    assert b["g2_pixel"].dtype == np.float32
    assert b["bad"].shape == (2, 16)
    assert b["bad"].dtype == bool
    assert b["img_shape"] == (4, 4)
    assert b["n_delays"] == 2
    assert b["n_sq"] == 2
    assert b["n_dq"] == 1
    assert b["n_dead"] == 1


def test_bundle_dead_pixel_masked():
    G2, sqmap, dqmap = make_data()
    b = compute_g2_debug_bundle(sqmap, dqmap, G2)
    assert b["sqmap_1d"][0] == 0  # dead pixel removed from its sq bin
    assert b["dqmap_1d"][0] == 0
    assert (b["sqmap_1d"][1:] != 0).all()
    assert sqmap[0, 0] == 1  # input not mutated


def test_bundle_g2_pixel_matches_normalize_g2():
    G2, sqmap, dqmap = make_data()
    b = compute_g2_debug_bundle(sqmap, dqmap, G2)
    n_delays, n_channels, img_v, img_h = G2.shape
    expected = normalize_g2(G2.reshape(n_delays, n_channels, -1))
    np.testing.assert_allclose(b["g2_pixel"], expected)


def test_bundle_bad_matches_outlier_pass():
    G2, sqmap, dqmap = make_data()
    b = compute_g2_debug_bundle(sqmap, dqmap, G2, outlier_threshold=3.0, method="MeanAbsoluteDeviation")
    expected = find_g2_pixel_outliers(b["sqmap_1d"], b["g2_pixel"], threshold=3.0, method="MeanAbsoluteDeviation")
    np.testing.assert_array_equal(b["bad"], expected)
    assert b["bad"].sum() == 2
    assert b["bad"][0, 15]
    assert b["bad"][1, 8]


def test_bundle_known_outliers():
    G2, sqmap, dqmap = make_data()
    b = compute_g2_debug_bundle(sqmap, dqmap, G2, outlier_threshold=3.0)
    # bin of seven 1s + one 10: median 1, MAD 0 -> clamped to 1, hi = 1+3 = 4
    assert b["bad"][0, 15]
    assert b["bad"][1, 8]
    assert not b["bad"][0, 0]  # dead pixels are out of all sq bins
    b100 = compute_g2_debug_bundle(sqmap, dqmap, G2, outlier_threshold=100.0)
    assert b100["bad"].sum() == 0


def test_bundle_combine_outlier_union():
    G2, sqmap, dqmap = make_data()
    b = compute_g2_debug_bundle(sqmap, dqmap, G2, outlier_threshold=3.0, combine_outlier=True)
    # sq 2 union = {8, 15} -> both flagged at every delay; sq 1 unaffected
    assert b["bad"][0, 8] and b["bad"][0, 15]
    assert b["bad"][1, 8] and b["bad"][1, 15]
    assert b["bad"].sum() == 4
```

- [x] **Step 2: Run test to verify it fails**

Run: `/local/MQICHU/envs/l2604_xpcs/bin/python -m pytest tests/test_g2_utils.py -v`
Expected: FAIL — `ImportError: cannot import name 'compute_g2_debug_bundle'`

- [x] **Step 3: Write the implementation**

Append to `src/pyxpcsviewer/core/g2_utils.py`:

```python
def compute_g2_debug_bundle(
    sqmap: np.ndarray,
    dqmap: np.ndarray,
    G2: np.ndarray,
    outlier_method: str = "MeanAbsoluteDeviation",
    outlier_threshold: float = 3.0,
    combine_outlier: bool = False,
) -> dict:
    """Compute the per-pixel data the G2 outlier debug dialog plots.

    Mirrors :func:`compute_g2` preprocessing exactly (dead-pixel masking,
    normalize) and runs the same outlier pass, so the dialog visualizes what
    ReGroup actually sees. Pure numpy, no file IO.

    Args:
        sqmap: Static ROI map, shape ``(img_v, img_h)``.
        dqmap: Dynamic ROI map, shape ``(img_v, img_h)``.
        G2: Unnormalized G2, shape ``(n_delays, 3, img_v, img_h)``.
        outlier_method: ``"MeanAbsoluteDeviation"`` or ``"StandardDeviation"``.
        outlier_threshold: Upper-bound rejection threshold (MADs / std devs).
        combine_outlier: If ``True``, union outlier masks across all delays
            per sq bin (same semantics as :func:`find_g2_pixel_outliers`).

    Returns:
        Dict with ``g2_pixel`` (n_delays, n_pixels), ``bad`` (bool, same shape),
        ``sqmap_1d`` / ``dqmap_1d`` (dead pixels set to 0), ``img_shape``
        ``(img_v, img_h)``, ``n_delays``, ``n_sq``, ``n_dq``, ``n_dead``.
    """
    n_delays, n_channels, img_v, img_h = G2.shape
    G2 = G2.reshape(n_delays, n_channels, -1)
    sqmap_1d = sqmap.ravel().copy()
    dqmap_1d = dqmap.ravel().copy()

    dead = np.all((G2[:, 1] == 0) & (G2[:, 2] == 0), axis=0)
    n_dead = int(np.sum(dead))
    sqmap_1d[dead] = 0
    dqmap_1d[dead] = 0

    g2_pixel = normalize_g2(G2)
    bad = find_g2_pixel_outliers(
        sqmap_1d, g2_pixel, threshold=outlier_threshold, method=outlier_method, combine_outlier=combine_outlier
    )

    return {
        "g2_pixel": g2_pixel,
        "bad": bad,
        "sqmap_1d": sqmap_1d,
        "dqmap_1d": dqmap_1d,
        "img_shape": (img_v, img_h),
        "n_delays": n_delays,
        "n_sq": int(np.max(sqmap_1d)),
        "n_dq": int(np.max(dqmap_1d)),
        "n_dead": n_dead,
    }
```

- [x] **Step 4: Run test to verify it passes**

Run: `/local/MQICHU/envs/l2604_xpcs/bin/python -m pytest tests/test_g2_utils.py -v`
Expected: all 6 tests PASS

- [x] **Step 5: Lint + type check**

Run:
```bash
ruff format tests/test_g2_utils.py src/pyxpcsviewer/core/g2_utils.py
ruff check tests/test_g2_utils.py src/pyxpcsviewer/core/g2_utils.py
/local/MQICHU/envs/l2604_xpcs/bin/mypy src/pyxpcsviewer/core/g2_utils.py
```
Expected: ruff clean; mypy reports exactly 19 errors (the pre-existing ones — none on the new function's lines).

- [x] **Step 6: Commit**

```bash
git add src/pyxpcsviewer/core/g2_utils.py tests/test_g2_utils.py
git commit -m "Add compute_g2_debug_bundle to core.g2_utils for the G2 debug dialog

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 2: `g2_debug_dialog.py` — helpers, bin-sweep panel, `build_debug_plots` skeleton

**Files:**
- Create: `src/pyxpcsviewer/gui/view/g2_debug_dialog.py`
- Test: `tests/test_g2_debug_dialog.py` (new)

**Interfaces:**
- Consumes: bundle dict from Task 1 (`compute_g2_debug_bundle` return shape); pyqtgraph 0.14.0, PySide6.
- Produces:
  - `build_debug_plots(widget: QtWidgets.QWidget, bundle: dict, fname: str, method: str, threshold: float, combine_outlier: bool) -> QtWidgets.QTabWidget` — appends a header QLabel (objectName `g2_debug_header`) and the QTabWidget to `widget`'s existing layout; returns the tab widget. Tab 0 "sq-bin histograms" holds the bin-sweep panel; tab 1 "Bad-pixel map" is an empty placeholder until Task 4.
  - `_BinSweepPanel(QtWidgets.QWidget)` with `.spin` (QSpinBox, objectName `g2_debug_sq_spin`, range 1..n_sq) and `.glw` (pg.GraphicsLayoutWidget, one PlotItem per delay, grid columns = `ceil(sqrt(n_delays))`).
  - `_add_hist(item, values, n_outlier, title_prefix, method, threshold)` and `_center_and_hi(values, method, threshold) -> tuple[float, float]` module helpers (reused by Task 3).

- [x] **Step 1: Write the failing tests**

Create `tests/test_g2_debug_dialog.py`:

```python
# Copyright © UChicago Argonne LLC
# See LICENSE file for details
"""Offscreen tests for the G2 outlier debug dialog's plot building.

build_debug_plots() is exercised directly with synthetic bundles from
compute_g2_debug_bundle — no real HDF5 file, no worker thread. The
worker/dialog lifecycle and the main-window wiring are tested later in
this file (see test_close_blocked_while_computing / test_debug_button_wired).
"""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import numpy as np
import pytest

pytest.importorskip("PySide6")

from PySide6 import QtWidgets

import pyqtgraph as pg

from pyxpcsviewer.core.g2_utils import compute_g2_debug_bundle
from pyxpcsviewer.gui.view.g2_debug_dialog import _BinSweepPanel, build_debug_plots


def make_synthetic():
    """(2 delays, 3 ch, 4x4) G2: dead pixel (0,0); sq 2 rows 2-3 hold two
    outliers — pixel 15=(3,3) and pixel 8=(2,0) at 10.0 at BOTH delays."""
    IP = np.ones((2, 4, 4), dtype=np.float32)
    IP[:, 3, 3] = 10.0
    IP[:, 2, 0] = 10.0
    IF = np.ones((2, 4, 4), dtype=np.float32)
    IF[:, 0, 0] = 0.0
    G2 = np.stack([IP, IF, IF], axis=1).astype(np.float32)
    sqmap = np.zeros((4, 4), dtype=np.uint16)
    sqmap[:2, :] = 1
    sqmap[2:, :] = 2
    dqmap = np.ones((4, 4), dtype=np.uint16)
    return G2, sqmap, dqmap


def _zero_bin_bundle():
    """1 delay, (3, 4) image: sq 1 and 3 all ones, sq 2 (middle row) all zero."""
    G2 = np.zeros((1, 3, 3, 4), dtype=np.float32)
    G2[:, 0] = 1.0
    G2[:, 0, 1, :] = 0.0
    G2[:, 1] = 1.0
    G2[:, 2] = 1.0
    sqmap = np.zeros((3, 4), dtype=np.uint16)
    sqmap[0, :] = 1
    sqmap[1, :] = 2
    sqmap[2, :] = 3
    dqmap = np.ones((3, 4), dtype=np.uint16)
    return compute_g2_debug_bundle(sqmap, dqmap, G2)


@pytest.fixture
def qapp():
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    yield app


@pytest.fixture
def bundle():
    G2, sqmap, dqmap = make_synthetic()
    return compute_g2_debug_bundle(sqmap, dqmap, G2, outlier_threshold=3.0, method="MeanAbsoluteDeviation")


def _host() -> QtWidgets.QWidget:
    host = QtWidgets.QWidget()
    host.setLayout(QtWidgets.QVBoxLayout())
    return host


def test_build_skeleton(qapp, bundle):
    host = _host()
    tabs = build_debug_plots(host, bundle, "fake.hdf", "MeanAbsoluteDeviation", 3.0, False)
    assert tabs.count() == 2
    header = host.findChild(QtWidgets.QLabel, "g2_debug_header")
    assert "threshold=3" in header.text()
    assert "combine=False" in header.text()
    assert "fake.hdf" in header.text()


def test_bin_sweep_renders_all_delays(qapp, bundle):
    host = _host()
    build_debug_plots(host, bundle, "fake.hdf", "MeanAbsoluteDeviation", 3.0, False)
    panel = host.findChild(_BinSweepPanel)
    plots = [it for it in panel.glw.ci.items if isinstance(it, pg.PlotItem)]
    assert len(plots) == 2  # one plot per delay
    spin = host.findChild(QtWidgets.QSpinBox, "g2_debug_sq_spin")
    assert spin.range() == (1, 2)


def test_bin_sweep_spin_switches_bin(qapp, bundle):
    host = _host()
    build_debug_plots(host, bundle, "fake.hdf", "MeanAbsoluteDeviation", 3.0, False)
    panel = host.findChild(_BinSweepPanel)
    spin = host.findChild(QtWidgets.QSpinBox, "g2_debug_sq_spin")
    spin.setValue(2)
    plot0 = [it for it in panel.glw.ci.items if isinstance(it, pg.PlotItem)][0]
    assert "out=2" in plot0.getTitle().toPlainText()  # pixels 15 and 8 flagged
    spin.setValue(1)
    assert "out=0" in plot0.getTitle().toPlainText()


def test_bin_sweep_all_zero_bin(qapp):
    host = _host()
    build_debug_plots(host, _zero_bin_bundle(), "fake.hdf", "MeanAbsoluteDeviation", 3.0, False)
    panel = host.findChild(_BinSweepPanel)
    panel.spin.setValue(2)
    plot0 = [it for it in panel.glw.ci.items if isinstance(it, pg.PlotItem)][0]
    assert "all zero" in plot0.getTitle().toPlainText()
```

- [x] **Step 2: Run tests to verify they fail**

Run: `/local/MQICHU/envs/l2604_xpcs/bin/python -m pytest tests/test_g2_debug_dialog.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'pyxpcsviewer.gui.view.g2_debug_dialog'`

- [x] **Step 3: Write the implementation**

Create `src/pyxpcsviewer/gui/view/g2_debug_dialog.py`:

```python
# Copyright © UChicago Argonne LLC
# See LICENSE file for details
"""G2 outlier-rejection debug dialog (G2_regroup tab).

The "Debug" button in the Group Setting box opens this dialog for the first
selected Multitau file. It visualizes what the configured outlier settings
(method / threshold / combine) do to the per-pixel g2:

* "sq-bin histograms" tab: per-sq-bin histograms of g2_pixel with the
  center + threshold*spread bounds used by find_g2_pixel_outliers — either
  all delays for one bin (bin sweep) or all bins for one delay (delay sweep,
  paged).
* "Bad-pixel map" tab: detector image of how many delays each pixel was
  flagged as an outlier, with a minimum-tag filter.

The heavy HDF5 load + outlier pass runs on G2DebugWorker (QThread); plot
building is synchronous and lives in build_debug_plots() so offscreen tests
can exercise it directly with a synthetic bundle (the dict returned by
core.g2_utils.compute_g2_debug_bundle).
"""

from __future__ import annotations

import math
import os

import numpy as np
import pyqtgraph as pg
from PySide6 import QtWidgets
from PySide6.QtCore import Qt
from typing import Protocol


class _XpcsFileLike(Protocol):
    """Structural subset of core.xpcs_file.XpcsFile the dialog needs."""

    fname: str
    sqmap: np.ndarray
    dqmap: np.ndarray

    @property
    def G2(self) -> np.ndarray | None: ...


def _center_and_hi(values: np.ndarray, method: str, threshold: float) -> tuple[float, float]:
    """Center and upper bound exactly as find_g2_pixel_outliers computes them.

    ``values`` must already be the non-zero (alive) g2_pixel values for one
    (sq bin, delay) pair.
    """
    if method == "StandardDeviation":
        center = float(np.mean(values))
        spread = float(np.std(values))
    else:  # MeanAbsoluteDeviation (default)
        center = float(np.median(values))
        spread = float(np.median(np.abs(values - center)))
    if spread == 0:
        spread = 1.0
    return center, center + threshold * spread


def _add_hist(
    item: pg.PlotItem,
    values: np.ndarray,
    n_outlier: int,
    title_prefix: str,
    method: str,
    threshold: float,
) -> None:
    """Draw one histogram subplot with center / hi-bound lines and a title.

    Zero (photon-starved) values must already be removed from ``values``;
    an empty array renders a labeled empty axis.
    """
    if values.size == 0:
        item.setTitle(f"{title_prefix}  (all zero)")
        return
    center, hi = _center_and_hi(values, method, threshold)
    counts, edges = np.histogram(values, bins=40)
    item.addItem(
        pg.BarGraphItem(
            x=0.5 * (edges[1:] + edges[:-1]),
            height=counts,
            width=float(edges[1] - edges[0]),
            brush=pg.mkBrush("steelblue"),
        )
    )
    item.addLine(x=center, pen=pg.mkPen("g", width=1))
    item.addLine(x=hi, pen=pg.mkPen("r", style=Qt.DashLine, width=1))
    item.setTitle(f"{title_prefix}  n={values.size}  out={n_outlier}")


class _BinSweepPanel(QtWidgets.QWidget):
    """All-delay histogram grid for one selectable sq bin."""

    def __init__(
        self,
        bundle: dict,
        method: str,
        threshold: float,
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._bundle = bundle
        self._method = method
        self._threshold = threshold

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        top = QtWidgets.QHBoxLayout()
        top.addWidget(QtWidgets.QLabel("sq bin:"))
        self.spin = QtWidgets.QSpinBox()
        self.spin.setObjectName("g2_debug_sq_spin")
        self.spin.setRange(1, bundle["n_sq"])
        self.spin.valueChanged.connect(self._render)
        top.addWidget(self.spin)
        top.addStretch(1)
        layout.addLayout(top)

        n_delays = bundle["n_delays"]
        self._cols = math.ceil(math.sqrt(n_delays))
        self.glw = pg.GraphicsLayoutWidget()
        layout.addWidget(self.glw)
        self._render()

    def _render(self) -> None:
        self.glw.clear()
        d = self.spin.value()
        roi = self._bundle["sqmap_1d"] == d
        if int(roi.sum()) == 0:
            item = self.glw.addPlot(row=0, col=0)
            item.setTitle(f"sq={d}  (empty)")
            return
        for delay in range(self._bundle["n_delays"]):
            row, col = divmod(delay, self._cols)
            item = self.glw.addPlot(row=row, col=col)
            values = self._bundle["g2_pixel"][delay][roi]
            values = values[values != 0]
            n_outlier = int(self._bundle["bad"][delay][roi].sum())
            _add_hist(item, values, n_outlier, f"delay={delay}", self._method, self._threshold)


def build_debug_plots(
    widget: QtWidgets.QWidget,
    bundle: dict,
    fname: str,
    method: str,
    threshold: float,
    combine_outlier: bool,
) -> QtWidgets.QTabWidget:
    """Populate *widget* with the debug header and the two tabs.

    Appends to *widget*'s existing layout and returns the QTabWidget.
    Tab 1 (bad-pixel map) is filled in by a later task.
    """
    layout = widget.layout()
    header = QtWidgets.QLabel(
        f"{os.path.basename(fname)} | delays={bundle['n_delays']}  sq={bundle['n_sq']}  "
        f"dq={bundle['n_dq']}  dead={bundle['n_dead']} | "
        f"method={method}, threshold={threshold:g}, combine={combine_outlier}"
    )
    header.setObjectName("g2_debug_header")
    header.setWordWrap(True)
    layout.addWidget(header)

    tabs = QtWidgets.QTabWidget()
    tabs.addTab(_BinSweepPanel(bundle, method, threshold), "sq-bin histograms")
    tabs.addTab(QtWidgets.QWidget(), "Bad-pixel map")
    layout.addWidget(tabs)
    return tabs
```

- [x] **Step 4: Run tests to verify they pass**

Run: `/local/MQICHU/envs/l2604_xpcs/bin/python -m pytest tests/test_g2_debug_dialog.py -v`
Expected: all 4 tests PASS

- [x] **Step 5: Lint + type check**

Run:
```bash
ruff format src/pyxpcsviewer/gui/view/g2_debug_dialog.py tests/test_g2_debug_dialog.py
ruff check src/pyxpcsviewer/gui/view/g2_debug_dialog.py tests/test_g2_debug_dialog.py
/local/MQICHU/envs/l2604_xpcs/bin/mypy src/pyxpcsviewer/gui/view/g2_debug_dialog.py
```
Expected: clean (0 mypy errors on the new file).

- [x] **Step 6: Commit**

```bash
git add src/pyxpcsviewer/gui/view/g2_debug_dialog.py tests/test_g2_debug_dialog.py
git commit -m "Add G2 debug dialog plot builder with bin-sweep histogram panel

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 3: Delay-sweep panel (all sq bins for one delay, paged)

**Files:**
- Modify: `src/pyxpcsviewer/gui/view/g2_debug_dialog.py` (add `_DelaySweepPanel`, rewire tab 0 to a QSplitter)
- Test: `tests/test_g2_debug_dialog.py` (append)

**Interfaces:**
- Consumes: `_add_hist()` and the bundle dict from Task 2.
- Produces: `_DelaySweepPanel(QtWidgets.QWidget)` with `.spin` (objectName `g2_debug_delay_spin`, range 0..n_delays−1), `.glw`, `.prev_btn` (objectName `g2_debug_prev_btn`), `.next_btn` (objectName `g2_debug_next_btn`), `.page_label` (objectName `g2_debug_page_label`, text `page k/N`), 60 bins per page in a 12-column grid. `build_debug_plots` tab 0 becomes a vertical `QSplitter` with the bin-sweep panel on top and the delay-sweep panel below.

- [x] **Step 1: Write the failing tests**

Append to `tests/test_g2_debug_dialog.py` (extend the `from pyxpcsviewer.gui.view.g2_debug_dialog import ...` line to also import `_DelaySweepPanel`):

```python
def _paged_bundle():
    """1 delay, (8, 16) image, 128 sq bins (one per pixel) -> 3 pages of 60."""
    G2 = np.zeros((1, 3, 8, 16), dtype=np.float32)
    G2[:, 0] = 1.0
    G2[:, 1] = 1.0
    G2[:, 2] = 1.0
    sqmap = np.arange(1, 129, dtype=np.uint16).reshape(8, 16)
    dqmap = np.ones((8, 16), dtype=np.uint16)
    return compute_g2_debug_bundle(sqmap, dqmap, G2)


def test_delay_sweep_paging(qapp):
    host = _host()
    build_debug_plots(host, _paged_bundle(), "fake.hdf", "MeanAbsoluteDeviation", 3.0, False)
    label = host.findChild(QtWidgets.QLabel, "g2_debug_page_label")
    prev = host.findChild(QtWidgets.QToolButton, "g2_debug_prev_btn")
    next_ = host.findChild(QtWidgets.QToolButton, "g2_debug_next_btn")
    assert label.text() == "page 1/3"
    assert not prev.isEnabled()
    assert next_.isEnabled()
    next_.click()
    assert label.text() == "page 2/3"
    next_.click()
    assert label.text() == "page 3/3"
    assert not next_.isEnabled()
    prev.click()
    assert label.text() == "page 2/3"


def test_delay_sweep_plot_counts(qapp):
    host = _host()
    build_debug_plots(host, _paged_bundle(), "fake.hdf", "MeanAbsoluteDeviation", 3.0, False)
    panel = host.findChild(_DelaySweepPanel)
    plots = [it for it in panel.glw.ci.items if isinstance(it, pg.PlotItem)]
    assert len(plots) == 60  # first page: bins 1-60
    panel._goto_page(2)
    plots = [it for it in panel.glw.ci.items if isinstance(it, pg.PlotItem)]
    assert len(plots) == 8  # last page: bins 121-128
```

- [x] **Step 2: Run tests to verify they fail**

Run: `/local/MQICHU/envs/l2604_xpcs/bin/python -m pytest tests/test_g2_debug_dialog.py -v`
Expected: the 2 new tests FAIL with `AttributeError: _DelaySweepPanel` (import error) — existing 4 still pass.

- [x] **Step 3: Write the implementation**

In `src/pyxpcsviewer/gui/view/g2_debug_dialog.py`, add after the `_BinSweepPanel` class:

```python
class _DelaySweepPanel(QtWidgets.QWidget):
    """All-sq-bin histogram grid for one selectable delay, paged 60 per page."""

    PER_PAGE = 60
    COLS = 12

    def __init__(
        self,
        bundle: dict,
        method: str,
        threshold: float,
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._bundle = bundle
        self._method = method
        self._threshold = threshold
        self._page = 0

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        top = QtWidgets.QHBoxLayout()
        top.addWidget(QtWidgets.QLabel("delay:"))
        self.spin = QtWidgets.QSpinBox()
        self.spin.setObjectName("g2_debug_delay_spin")
        self.spin.setRange(0, bundle["n_delays"] - 1)
        self.spin.valueChanged.connect(self._render)
        top.addWidget(self.spin)
        self.prev_btn = QtWidgets.QToolButton()
        self.prev_btn.setObjectName("g2_debug_prev_btn")
        self.prev_btn.setText("◀")
        self.prev_btn.clicked.connect(lambda: self._goto_page(self._page - 1))
        top.addWidget(self.prev_btn)
        self.page_label = QtWidgets.QLabel("")
        self.page_label.setObjectName("g2_debug_page_label")
        top.addWidget(self.page_label)
        self.next_btn = QtWidgets.QToolButton()
        self.next_btn.setObjectName("g2_debug_next_btn")
        self.next_btn.setText("▶")
        self.next_btn.clicked.connect(lambda: self._goto_page(self._page + 1))
        top.addWidget(self.next_btn)
        top.addStretch(1)
        layout.addLayout(top)

        self.glw = pg.GraphicsLayoutWidget()
        layout.addWidget(self.glw)
        self._render()

    def _n_pages(self) -> int:
        return math.ceil(self._bundle["n_sq"] / self.PER_PAGE)

    def _goto_page(self, page: int) -> None:
        self._page = max(0, min(page, self._n_pages() - 1))
        self._render()

    def _render(self) -> None:
        self.glw.clear()
        delay = self.spin.value()
        first = self._page * self.PER_PAGE + 1
        last = min(first + self.PER_PAGE - 1, self._bundle["n_sq"])
        for i, d in enumerate(range(first, last + 1)):
            row, col = divmod(i, self.COLS)
            item = self.glw.addPlot(row=row, col=col)
            roi = self._bundle["sqmap_1d"] == d
            if int(roi.sum()) == 0:
                item.setTitle(f"sq={d}  (empty)")
                continue
            values = self._bundle["g2_pixel"][delay][roi]
            values = values[values != 0]
            n_outlier = int(self._bundle["bad"][delay][roi].sum())
            _add_hist(item, values, n_outlier, f"sq={d}", self._method, self._threshold)
        self.page_label.setText(f"page {self._page + 1}/{self._n_pages()}")
        self.prev_btn.setEnabled(self._page > 0)
        self.next_btn.setEnabled(self._page < self._n_pages() - 1)
```

Then in `build_debug_plots`, replace the tab-0 line:

```python
    tabs.addTab(_BinSweepPanel(bundle, method, threshold), "sq-bin histograms")
```

with:

```python
    splitter = QtWidgets.QSplitter(Qt.Vertical)
    splitter.addWidget(_BinSweepPanel(bundle, method, threshold))
    splitter.addWidget(_DelaySweepPanel(bundle, method, threshold))
    tabs.addTab(splitter, "sq-bin histograms")
```

- [x] **Step 4: Run tests to verify they pass**

Run: `/local/MQICHU/envs/l2604_xpcs/bin/python -m pytest tests/test_g2_debug_dialog.py -v`
Expected: all 6 tests PASS

- [x] **Step 5: Lint + type check**

Run:
```bash
ruff format src/pyxpcsviewer/gui/view/g2_debug_dialog.py tests/test_g2_debug_dialog.py
ruff check src/pyxpcsviewer/gui/view/g2_debug_dialog.py tests/test_g2_debug_dialog.py
/local/MQICHU/envs/l2604_xpcs/bin/mypy src/pyxpcsviewer/gui/view/g2_debug_dialog.py
```
Expected: clean.

- [x] **Step 6: Commit**

```bash
git add src/pyxpcsviewer/gui/view/g2_debug_dialog.py tests/test_g2_debug_dialog.py
git commit -m "Add delay-sweep histogram panel (paged) to G2 debug dialog

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 4: Bad-pixel map panel

**Files:**
- Modify: `src/pyxpcsviewer/gui/view/g2_debug_dialog.py` (add `_BadMapPanel`, wire as tab 1)
- Test: `tests/test_g2_debug_dialog.py` (append)

**Interfaces:**
- Consumes: bundle dict (`bad`, `img_shape`, `n_dead`).
- Produces: `_BadMapPanel(QtWidgets.QWidget)` with constructor `(bundle: dict, parent: QtWidgets.QWidget | None = None)` and `.spin` (objectName `g2_debug_mintag_spin`, range 1..max tag count, default 1), `.view` (pg.ImageView, objectName `g2_debug_map_view`, "hot" colormap, colorbar), `.summary` (QLabel, objectName `g2_debug_map_summary`). `build_debug_plots` tab 1 becomes this panel.

- [x] **Step 1: Write the failing test**

Append to `tests/test_g2_debug_dialog.py` (extend the module import line to also import `_BadMapPanel`):

```python
def test_bad_map_and_mintag_remask(qapp, bundle):
    host = _host()
    build_debug_plots(host, bundle, "fake.hdf", "MeanAbsoluteDeviation", 3.0, False)
    view = host.findChild(pg.ImageView, "g2_debug_map_view")
    spin = host.findChild(QtWidgets.QSpinBox, "g2_debug_mintag_spin")
    summary = host.findChild(QtWidgets.QLabel, "g2_debug_map_summary")

    img = view.getImage()
    assert img.shape == (4, 4)
    # pixels 15=(3,3) and 8=(2,0) are flagged at both delays -> count 2
    assert img[3, 3] == 2 and img[2, 0] == 2
    assert int(img.max()) == 2
    assert "tagged ≥1: 2" in summary.text()
    assert "dead pixels = 1" in summary.text()

    spin.setValue(2)
    img2 = view.getImage()
    assert int((img2 == 2).sum()) == 2  # only the two count==2 pixels remain
    assert "tagged ≥2: 2" in summary.text()
```

- [x] **Step 2: Run test to verify it fails**

Run: `/local/MQICHU/envs/l2604_xpcs/bin/python -m pytest tests/test_g2_debug_dialog.py::test_bad_map_and_mintag_remask -v`
Expected: FAIL — tab 1 is still the empty placeholder, `findChild(pg.ImageView, "g2_debug_map_view")` returns None.

- [x] **Step 3: Write the implementation**

In `src/pyxpcsviewer/gui/view/g2_debug_dialog.py`, add after `_DelaySweepPanel`:

```python
class _BadMapPanel(QtWidgets.QWidget):
    """Detector image of outlier tag counts with a minimum-tag filter."""

    def __init__(self, bundle: dict, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self._counts = bundle["bad"].sum(axis=0).reshape(bundle["img_shape"])
        self._n_dead = bundle["n_dead"]

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        top = QtWidgets.QHBoxLayout()
        top.addWidget(QtWidgets.QLabel("min tag count:"))
        self.spin = QtWidgets.QSpinBox()
        self.spin.setObjectName("g2_debug_mintag_spin")
        self.spin.setRange(1, max(1, int(self._counts.max())))
        self.spin.valueChanged.connect(self._render)
        top.addWidget(self.spin)
        self.summary = QtWidgets.QLabel("")
        self.summary.setObjectName("g2_debug_map_summary")
        top.addWidget(self.summary)
        top.addStretch(1)
        layout.addLayout(top)

        self.view = pg.ImageView()
        self.view.setObjectName("g2_debug_map_view")
        self.view.ui.roi.setVisible(False)
        self.view.setColorMap(pg.colormap.get("hot"))
        layout.addWidget(self.view)
        self._render()

    def _render(self) -> None:
        min_tag = self.spin.value()
        img = self._counts.astype(float)
        img[self._counts < min_tag] = 0.0
        vmax = max(1, int(self._counts.max()))
        self.view.setImage(img)
        self.view.setLevels((min_tag, vmax))
        n = int(np.sum(self._counts >= min_tag))
        total = int(self._counts.size)
        self.summary.setText(
            f"tagged ≥{min_tag}: {n} ({100.0 * n / total:.3f}%), "
            f"max count = {int(self._counts.max())}, dead pixels = {self._n_dead}"
        )
```

In `build_debug_plots`, replace:

```python
    tabs.addTab(QtWidgets.QWidget(), "Bad-pixel map")
```

with:

```python
    tabs.addTab(_BadMapPanel(bundle), "Bad-pixel map")
```

Note: `setLevels((min_tag, vmax))` clips sub-threshold pixels (set to 0) to the colormap's low color — black in "hot" — which is the "masked" look.

- [x] **Step 4: Run tests to verify they pass**

Run: `/local/MQICHU/envs/l2604_xpcs/bin/python -m pytest tests/test_g2_debug_dialog.py -v`
Expected: all 7 tests PASS

- [x] **Step 5: Lint + type check**

Run:
```bash
ruff format src/pyxpcsviewer/gui/view/g2_debug_dialog.py tests/test_g2_debug_dialog.py
ruff check src/pyxpcsviewer/gui/view/g2_debug_dialog.py tests/test_g2_debug_dialog.py
/local/MQICHU/envs/l2604_xpcs/bin/mypy src/pyxpcsviewer/gui/view/g2_debug_dialog.py
```
Expected: clean.

- [x] **Step 6: Commit**

```bash
git add src/pyxpcsviewer/gui/view/g2_debug_dialog.py tests/test_g2_debug_dialog.py
git commit -m "Add bad-pixel map panel (min-tag filter) to G2 debug dialog

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 5: `G2DebugWorker` + `G2DebugDialog`

**Files:**
- Modify: `src/pyxpcsviewer/gui/view/g2_debug_dialog.py` (append worker + dialog classes)
- Test: `tests/test_g2_debug_dialog.py` (append)

**Interfaces:**
- Consumes: `compute_g2_debug_bundle` (Task 1), `build_debug_plots` (Tasks 2–4), `_XpcsFileLike` Protocol (Task 2).
- Produces:
  - `G2DebugWorker(QtCore.QThread)` with constructor `(xfile: _XpcsFileLike, method: str, threshold: float, combine_outlier: bool, parent: QtCore.QObject | None = None)` and signals `progress_stage = QtCore.Signal(str)`, `finished_bundle = QtCore.Signal(object)`, `failed = QtCore.Signal(str)`.
  - `G2DebugDialog(QtWidgets.QDialog)` with constructor `(xfile: _XpcsFileLike, method: str, threshold: float, combine_outlier: bool, parent: QtWidgets.QWidget | None = None)`; instance attrs `_worker_running: bool`, `_worker: G2DebugWorker`; instance method `_show_failure(msg: str)` (the QMessageBox.critical call — instance-level so tests can override it). Task 6's slot constructs this.

- [x] **Step 1: Write the failing tests**

Append to `tests/test_g2_debug_dialog.py` (add `import threading`, `import time`, and `from typing import cast` at the top; extend the `g2_debug_dialog` import line to also import `G2DebugDialog` and `_XpcsFileLike`):

```python
def _pump(qapp, predicate, timeout=10.0):
    """Pump events until predicate() is true or timeout."""
    deadline = time.time() + timeout
    while not predicate() and time.time() < deadline:
        qapp.processEvents()
        time.sleep(0.01)
    return predicate()


def test_dialog_computes_and_populates(qapp):
    G2, sqmap, dqmap = make_synthetic()
    # cast: SimpleNamespace has no declared members, so mypy cannot check it
    # against the _XpcsFileLike protocol structurally
    fake = cast("_XpcsFileLike", types.SimpleNamespace(fname="fake.hdf", G2=G2, sqmap=sqmap, dqmap=dqmap))
    dlg = G2DebugDialog(fake, "MeanAbsoluteDeviation", 3.0, False)
    dlg.show()
    assert _pump(qapp, lambda: not dlg._worker_running)
    tab = dlg.findChild(QtWidgets.QTabWidget)
    assert tab is not None
    assert tab.count() == 2
    assert dlg.findChild(QtWidgets.QLabel, "g2_debug_header") is not None
    dlg.close()
    assert not dlg.isVisible()


def test_close_blocked_while_computing(qapp):
    gate = threading.Event()
    G2, sqmap, dqmap = make_synthetic()

    class SlowXfile:
        fname = "fake.hdf"
        sqmap = sqmap
        dqmap = dqmap

        @property
        def G2(self):
            gate.wait(timeout=10)
            return G2

    dlg = G2DebugDialog(SlowXfile(), "MeanAbsoluteDeviation", 3.0, False)
    dlg.show()
    assert _pump(qapp, lambda: dlg._worker.isRunning(), timeout=5.0)
    dlg.close()
    assert dlg.isVisible()  # close ignored while computing
    gate.set()
    assert _pump(qapp, lambda: not dlg._worker_running)
    assert dlg.findChild(QtWidgets.QTabWidget) is not None
    dlg.close()
    assert not dlg.isVisible()


def test_dialog_failed_path(qapp):
    shown = []
    G2, sqmap, dqmap = make_synthetic()

    class BrokenXfile:
        fname = "fake.hdf"
        sqmap = sqmap
        dqmap = dqmap

        @property
        def G2(self):
            raise OSError("disk error")

    dlg = G2DebugDialog(BrokenXfile(), "MeanAbsoluteDeviation", 3.0, False)
    dlg._show_failure = lambda msg: shown.append(msg)  # noqa: method-member-amend
    dlg.show()
    assert _pump(qapp, lambda: not dlg.isVisible(), timeout=10.0)
    assert len(shown) == 1
    assert "disk error" in shown[0]
```

Note: `import types` is also needed at the top of the test file.

- [x] **Step 2: Run tests to verify they fail**

Run: `/local/MQICHU/envs/l2604_xpcs/bin/python -m pytest tests/test_g2_debug_dialog.py -v`
Expected: the 3 new tests FAIL — `ImportError: cannot import name 'G2DebugDialog'`; the 7 existing pass.

- [x] **Step 3: Write the implementation**

Append to `src/pyxpcsviewer/gui/view/g2_debug_dialog.py` (add `from PySide6 import QtCore`, `from PySide6.QtWidgets import QMessageBox`, and `from pyxpcsviewer.core.g2_utils import compute_g2_debug_bundle` to the import block):

```python
class G2DebugWorker(QtCore.QThread):
    """Load the unnormalized G2 (fresh h5py handle per read — thread-safe)
    and run the outlier pass off the main thread."""

    progress_stage = QtCore.Signal(str)
    finished_bundle = QtCore.Signal(object)
    failed = QtCore.Signal(str)

    def __init__(
        self,
        xfile: _XpcsFileLike,
        method: str,
        threshold: float,
        combine_outlier: bool,
        parent: QtCore.QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._xfile = xfile
        self._method = method
        self._threshold = threshold
        self._combine = combine_outlier

    def run(self) -> None:
        try:
            self.progress_stage.emit("Loading G2…")
            G2 = self._xfile.G2
            if G2 is None:
                raise ValueError("file has no unnormalized G2 (/xpcs/multitau/unnormalized_G2)")
            sqmap = self._xfile.sqmap
            dqmap = self._xfile.dqmap
            self.progress_stage.emit("Detecting outliers…")
            bundle = compute_g2_debug_bundle(
                sqmap,
                dqmap,
                G2,
                outlier_method=self._method,
                outlier_threshold=self._threshold,
                combine_outlier=self._combine,
            )
        except Exception as exc:  # report any failure to the UI
            self.failed.emit(f"{type(exc).__name__}: {exc}")
            return
        self.finished_bundle.emit(bundle)


class G2DebugDialog(QtWidgets.QDialog):
    """Modeless debug dialog: placeholder while the worker runs, then the
    plot tabs. Close is ignored while the worker is running (the HDF5 read
    cannot be interrupted mid-read)."""

    def __init__(
        self,
        xfile: _XpcsFileLike,
        method: str,
        threshold: float,
        combine_outlier: bool,
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._fname = xfile.fname
        self._method = method
        self._threshold = threshold
        self._combine = combine_outlier
        self._worker_running = True
        self.setWindowTitle(f"G2 outlier debug — {os.path.basename(self._fname)}")
        self.setMinimumSize(900, 700)

        layout = QtWidgets.QVBoxLayout(self)
        self._placeholder = QtWidgets.QLabel("Computing G2 debug data…\n(close is disabled until this finishes)")
        self._placeholder.setAlignment(Qt.AlignCenter)
        self._stage = QtWidgets.QLabel("…")
        self._progress = QtWidgets.QProgressBar()
        self._progress.setRange(0, 0)  # indeterminate
        layout.addWidget(self._placeholder)
        layout.addWidget(self._stage)
        layout.addWidget(self._progress)

        self._worker = G2DebugWorker(xfile, method, threshold, combine_outlier, self)
        self._worker.progress_stage.connect(self._on_stage)
        self._worker.finished_bundle.connect(self._on_bundle)
        self._worker.failed.connect(self._on_failed)
        self._worker.start()

    def _on_stage(self, text: str) -> None:
        self._stage.setText(text)

    def _on_bundle(self, bundle: dict) -> None:
        self._worker_running = False
        layout = self.layout()
        for w in (self._placeholder, self._stage, self._progress):
            layout.removeWidget(w)
            w.deleteLater()
        build_debug_plots(self, bundle, self._fname, self._method, self._threshold, self._combine)

    def _on_failed(self, msg: str) -> None:
        self._worker_running = False
        self._show_failure(msg)
        self.close()

    def _show_failure(self, msg: str) -> None:
        QMessageBox.critical(self, "G2 debug failed", msg)

    def closeEvent(self, event: QtWidgets.QCloseEvent) -> None:
        if self._worker_running:
            event.ignore()
            return
        event.accept()
```

- [x] **Step 4: Run tests to verify they pass**

Run: `/local/MQICHU/envs/l2604_xpcs/bin/python -m pytest tests/test_g2_debug_dialog.py -v`
Expected: all 10 tests PASS

- [x] **Step 5: Lint + type check**

Run:
```bash
ruff format src/pyxpcsviewer/gui/view/g2_debug_dialog.py tests/test_g2_debug_dialog.py
ruff check src/pyxpcsviewer/gui/view/g2_debug_dialog.py tests/test_g2_debug_dialog.py
/local/MQICHU/envs/l2604_xpcs/bin/mypy src/pyxpcsviewer/gui/view/g2_debug_dialog.py
```
Expected: clean.

- [x] **Step 6: Commit**

```bash
git add src/pyxpcsviewer/gui/view/g2_debug_dialog.py tests/test_g2_debug_dialog.py
git commit -m "Add G2DebugWorker and G2DebugDialog lifecycle

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 6: UI button, regenerated UI, main-window wiring

**Files:**
- Modify: `src/pyxpcsviewer/gui/view/view.ui` (one new QPushButton)
- Regenerate: `src/pyxpcsviewer/gui/view/viewer_ui.py` (via script — never hand-edit)
- Modify: `src/pyxpcsviewer/gui/view/xpcs_viewer.py` (import, state attr, connection, slot)
- Test: `tests/test_g2_debug_dialog.py` (append smoke test)

**Interfaces:**
- Consumes: `G2DebugDialog` (Task 5); existing `XpcsViewer.get_selected_rows()`, `self.model.get_xf_list(rows, filter_atype="Multitau")` (gui/model/file_locator.py:65), `has_G2_field` (already imported in xpcs_viewer.py line 20), widgets `comboBox_G2_outliermethod` / `doubleSpinBox_G2_threshold` / `checkBox_G2_combineoutlier` / `checkBox_G2_removeoutlier` (checkbox read but only for future-proofing — settings are always applied per the spec decision).
- Produces: `XpcsViewer.pushButton_G2_debug`, `XpcsViewer._g2_debug_dialog: G2DebugDialog | None`, `XpcsViewer.debug_G2_regroup() -> None`.

- [x] **Step 1: Write the failing smoke test**

Append to `tests/test_g2_debug_dialog.py`:

```python
def test_debug_button_wired(qapp, tmp_path):
    from pyxpcsviewer.gui.view.xpcs_viewer import XpcsViewer

    window = XpcsViewer(path=str(tmp_path))
    assert window.pushButton_G2_debug is not None
    assert window._g2_debug_dialog is None
    window.debug_G2_regroup()  # no selection: silent no-op, no dialog
    assert window._g2_debug_dialog is None
```

- [x] **Step 2: Run test to verify it fails**

Run: `/local/MQICHU/envs/l2604_xpcs/bin/python -m pytest tests/test_g2_debug_dialog.py::test_debug_button_wired -v`
Expected: FAIL — `AttributeError: 'XpcsViewer' object has no attribute 'pushButton_G2_debug'`

- [x] **Step 3: Add the button to `view.ui`**

In `src/pyxpcsviewer/gui/view/view.ui`, inside `gridLayout_50` (the "Group Setting" `groupBox_23` layout), after the `checkBox_G2_combineoutlier` item and before the layout's closing tag, insert:

```xml
                <item row="1" column="6">
                 <widget class="QPushButton" name="pushButton_G2_debug">
                  <property name="text">
                   <string>Debug</string>
                  </property>
                 </widget>
                </item>
```

Precise anchor — replace:

```xml
                 <widget class="QCheckBox" name="checkBox_G2_combineoutlier">
                  <property name="text">
                   <string>Combine Outlier</string>
                  </property>
                  <property name="checkable">
                   <bool>true</bool>
                  </property>
                  <property name="checked">
                   <bool>false</bool>
                  </property>
                 </widget>
                </item>
               </layout>
```

with the same block plus the new `<item row="1" column="6">` inserted between `</item>` and `</layout>` (i.e. the new item is the last item of `gridLayout_50`, landing directly under the ReGroup button at row 0 column 6).

- [x] **Step 4: Regenerate the UI python**

Run:
```bash
PATH=/local/MQICHU/envs/l2604_xpcs/bin:$PATH bash src/pyxpcsviewer/gui/view/convert_ui_to_py.sh
git diff --stat src/pyxpcsviewer/gui/view/viewer_ui.py
```
Expected: a small diff — a `self.pushButton_G2_debug = QtWidgets.QPushButton(...)` block, its grid geometry, and text "Debug". If the diff is unexpectedly huge (uic version churn beyond the new button), inspect it before proceeding; the generated file must differ only by the new button.

- [x] **Step 5: Wire `xpcs_viewer.py`**

Four edits in `src/pyxpcsviewer/gui/view/xpcs_viewer.py`:

1. Imports — after `from .viewer_ui import Ui_mainWindow as Ui` (line ~26) add:
```python
from .g2_debug_dialog import G2DebugDialog
```

2. State — after `self._g2_bounds_initialized = False` (line ~143) add:
```python
        # G2 outlier debug dialog (lazy: None until the first Debug click)
        self._g2_debug_dialog: G2DebugDialog | None = None
```

3. Connection — after `self.pushButton_G2_loadQMap.clicked.connect(self.load_external_qmap_for_G2_regroup)` (line ~196) add:
```python
        self.pushButton_G2_debug.clicked.connect(self.debug_G2_regroup)
```

4. Slot — insert after the `savefile_G2_regroup` method (which ends at line ~375, before `def process_G2_regroup`):
```python
    def debug_G2_regroup(self) -> None:
        """Open the G2 outlier debug dialog for the first selected Multitau file.

        The configured threshold/method are always applied (the "Remove
        Outlier" checkbox is deliberately ignored — the dialog shows what
        the settings would do). The heavy load/compute runs on a QThread
        inside the dialog.
        """
        rows = self.get_selected_rows()
        if len(rows) == 0:
            return
        xf_list = self.model.get_xf_list(rows, filter_atype="Multitau")
        if len(xf_list) == 0:
            return
        xfile = xf_list[0]
        if not has_G2_field(xfile.fname):
            QMessageBox.critical(self, "No G2 data found", "No G2 data found in the selected dataset.")
            return
        if self._g2_debug_dialog is not None and self._g2_debug_dialog.isVisible():
            self._g2_debug_dialog.raise_()
            self._g2_debug_dialog.activateWindow()
            return
        self._g2_debug_dialog = G2DebugDialog(
            xfile,
            self.comboBox_G2_outliermethod.currentText(),
            self.doubleSpinBox_G2_threshold.value(),
            self.checkBox_G2_combineoutlier.isChecked(),
            parent=self,
        )
        self._g2_debug_dialog.show()
```

- [x] **Step 6: Run the new test to verify it passes**

Run: `/local/MQICHU/envs/l2604_xpcs/bin/python -m pytest tests/test_g2_debug_dialog.py::test_debug_button_wired -v`
Expected: PASS

- [x] **Step 7: Full verification**

Run:
```bash
/local/MQICHU/envs/l2604_xpcs/bin/python -m pytest tests/ -v
ruff format src/pyxpcsviewer/gui/view/xpcs_viewer.py tests/test_g2_debug_dialog.py
ruff check src/pyxpcsviewer/gui/view/xpcs_viewer.py tests/test_g2_debug_dialog.py
/local/MQICHU/envs/l2604_xpcs/bin/mypy src/pyxpcsviewer/gui/view/xpcs_viewer.py src/pyxpcsviewer/gui/view/g2_debug_dialog.py
```
Expected: whole suite passes (note `test_real_data.py` cases auto-skip without the scratch data — that is normal); ruff clean; no NEW mypy errors in `xpcs_viewer.py` (if the file had pre-existing errors, the count must be unchanged — check `git stash && mypy ... && git stash pop` if in doubt).

- [x] **Step 8: Commit**

```bash
git add src/pyxpcsviewer/gui/view/view.ui src/pyxpcsviewer/gui/view/viewer_ui.py src/pyxpcsviewer/gui/view/xpcs_viewer.py tests/test_g2_debug_dialog.py
git commit -m "Add Debug button to G2 group settings opening the outlier debug dialog

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Final manual verification (after Task 6, on the dev machine)

Run the viewer on real data:

```bash
PYTHONDONTWRITEBYTECODE=1 /local/MQICHU/envs/l2604_xpcs/bin/python -m pyxpcsviewer /home/beams/MQICHU/Datasets/xpcs/2026_0817_G2
```

1. Select `A0096_GlassyCarbon_a0002_f001000_r00001_results.hdf` in the target list, open the **G2_regroup** tab.
2. Group Setting: Remove Outlier checked, threshold 3.0, MeanAbsoluteDeviation, Combine unchecked → click **Debug**.
3. Dialog: header shows file + settings; bin sweep on sq bins 100/200/300 (known-bad in the A0096 dataset) shows red-dash upper bounds with non-zero `out=` counts; delay sweep pages 1/6 (360 bins); bad-pixel map shows scattered flagged pixels; min tag count 2 hides one-off flags.
4. Check the checkbox **Combine Outlier**, click Debug again → the old dialog is brought to front (no new one); close it, click Debug → fresh dialog with a denser map (union across delays).
5. Uncheck **Remove Outlier** and click Debug → dialog still applies threshold 3.0 (by design) and the header shows it.
6. Compare bin-sweep outlier counts against the prints of `sweep_sq_all_delays_exclude_zeros.py` (threshold 4.0 there — expect fewer outliers there, same flagged pixels where values exceed both bounds).
