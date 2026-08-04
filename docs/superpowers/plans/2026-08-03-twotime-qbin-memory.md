# Twotime qbin selection memory Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** When a new dataset is selected in the twotime tab, keep the previously used q-bin index position instead of always resetting to index 0.

**Architecture:** `PlotController.plot_twotime` clamps the caller-supplied `selection` index to the newly-selected file's q-bin count and returns `(new_qbin_labels_or_None, selection_used)` instead of just labels. `XpcsViewer.plot_twotime` uses that returned index (with widget signals blocked during combobox repopulation) to keep the combobox/slider showing the correct position instead of resetting to 0 via a redundant cascade render.

**Tech Stack:** Python, PySide6 (Qt widgets, not touched at the widget-definition level), pytest.

## Global Constraints

- Match by index position, not by q-bin label/value (explicit design decision — see spec).
- Out-of-range remembered index clamps to the last valid index for the new file (does not fall back to 0).
- Session-only in-memory state — no persistence to disk.
- No new instance attributes for "remembered" state — reuse the combobox's own pre-switch `currentIndex()`.
- Full design spec: `docs/superpowers/specs/2026-08-03-twotime-qbin-memory-design.md`.

---

### Task 1: Clamp and return the rendered selection from `PlotController.plot_twotime`

**Files:**
- Modify: `src/pyxpcsviewer/gui/control/plot_controller.py:361-381`
- Test: `tests/test_twotime_selection.py` (new file)

**Interfaces:**
- Consumes: `XpcsFile.get_twotime_qbin_labels() -> list[str]` (existing, unchanged, `src/pyxpcsviewer/core/xpcs_file.py:571`); `twotime.plot_twotime(xfile, hdl, selection=..., **kwargs) -> None` (existing, unchanged, `src/pyxpcsviewer/gui/control/plot/twotime.py:10`).
- Produces: `PlotController.plot_twotime(self, hdl, rows=None, selection=0, **kwargs) -> tuple[list[str] | None, int]`. The first tuple element is the new q-bin labels if the active file changed this call, else `None`. The second element is the q-bin index that was actually rendered (equal to the `selection` argument unless it had to be clamped down for a smaller new file). Task 2 consumes this exact return shape.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_twotime_selection.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_twotime_selection.py -v`
Expected: FAIL (or ERROR) — current `plot_twotime` returns a bare `list | None`, so unpacking `labels, selection = controller.plot_twotime(...)` raises `TypeError: cannot unpack non-iterable NoneType object` (or a similar unpacking error) on every test.

- [ ] **Step 3: Implement the clamp-and-return logic**

Replace `src/pyxpcsviewer/gui/control/plot_controller.py:361-381` (the current `plot_twotime` method body) with:

```python
    def plot_twotime(self, hdl, rows=None, selection=0, **kwargs):
        """Display two-time correlation (C2) map alongside SAXS-2D background and G2 traces.

        Args:
            hdl: Dict-like handle mapping names to ``ImageView`` / ``PlotWidget`` widgets.
            rows: List of target indices; uses twotime targets.
            selection: Q-bin index requested by the caller (e.g. the twotime
                combobox's current index before repopulation). Clamped to
                the new file's q-bin count when the active file changes.
            **kwargs: Passed to :func:`.plot.twotime.plot_twotime`.

        Returns:
            Tuple of ``(new_qbin_labels, selection_used)``. The first
            element is a new ``qbin_labels`` list if the active file
            changed, else ``None``. The second element is the q-bin index
            that was actually rendered (equal to *selection* unless it had
            to be clamped down for the new file).
        """
        xf_list = self.model.get_xf_list(rows, filter_atype="Twotime")
        if len(xf_list) == 0:
            return None, selection
        xfile = xf_list[0]
        new_qbin_labels = None
        if self.current_dset is None or self.current_dset.fname != xfile.fname:
            self.current_dset = xfile
            new_qbin_labels = xfile.get_twotime_qbin_labels()
            selection = max(0, min(selection, len(new_qbin_labels) - 1))
        twotime.plot_twotime(xfile, hdl, selection=selection, **kwargs)
        return new_qbin_labels, selection
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_twotime_selection.py -v`
Expected: PASS (5 passed)

- [ ] **Step 5: Commit**

```bash
git add src/pyxpcsviewer/gui/control/plot_controller.py tests/test_twotime_selection.py
git commit -m "Preserve twotime qbin selection index across dataset switches"
```

---

### Task 2: Sync the twotime combobox/slider without resetting the index

**Files:**
- Modify: `src/pyxpcsviewer/gui/view/xpcs_viewer.py:593-618`

**Interfaces:**
- Consumes: `PlotController.plot_twotime(...) -> tuple[list[str] | None, int]` from Task 1.
- Produces: No new public interface — this is the terminal consumer for this feature.

- [ ] **Step 1: Update `plot_twotime` in `xpcs_viewer.py`**

Replace `src/pyxpcsviewer/gui/view/xpcs_viewer.py:593-618` (the current `plot_twotime` method) with:

```python
    def plot_twotime(self, dryrun: bool = False, highlight_xy=None):
        """Display two-time correlation (C2) maps alongside SAXS-2D background.

        Returns keyword arguments in dry-run mode; otherwise renders the twotime view.
        """
        kwargs = {
            "rows": self.get_selected_rows(),
            "auto_crop": self.twotime_autocrop.isChecked(),
            "highlight_xy": highlight_xy,
            "cmap": self.cb_twotime_cmap.currentText(),
            "vmin": self.c2_min.value(),
            "vmax": self.c2_max.value(),
            "correct_diag": self.twotime_correct_diag.isChecked(),
            "autolevel": self.checkBox_twotime_autolevel.isChecked(),
            "selection": max(0, self.comboBox_twotime_selection.currentIndex()),
        }
        if dryrun:
            return kwargs

        if self.mp_2t_hdls is None:
            self.init_twotime_plot_handler()
        new_labels, selection = self.plots.plot_twotime(self.mp_2t_hdls, **kwargs)
        if new_labels is not None:
            self.comboBox_twotime_selection.blockSignals(True)
            self.horizontalSlider_twotime_selection.blockSignals(True)
            self.comboBox_twotime_selection.clear()
            self.comboBox_twotime_selection.addItems(new_labels)
            self.comboBox_twotime_selection.setCurrentIndex(selection)
            self.horizontalSlider_twotime_selection.setMaximum(len(new_labels) - 1)
            self.horizontalSlider_twotime_selection.setValue(selection)
            self.comboBox_twotime_selection.blockSignals(False)
            self.horizontalSlider_twotime_selection.blockSignals(False)
```

This is the only call site of `self.plots.plot_twotime` in the view layer (confirmed via `grep -n "plots.plot_twotime" src/pyxpcsviewer/gui/view/xpcs_viewer.py`), so no other code needs updating for the new tuple return shape.

- [ ] **Step 2: Verify no other callers of `PlotController.plot_twotime` exist**

Run: `grep -rn "\.plot_twotime(" src/pyxpcsviewer/`
Expected: three matches:
- `gui/control/plot_controller.py:380` — `twotime.plot_twotime(xfile, hdl, **kwargs)`, a call to the unrelated module-level renderer in `plot/twotime.py`, unaffected by this change.
- `gui/view/xpcs_viewer.py:579` — `self.plot_twotime(highlight_xy=(x, y))`, the Q-map click handler calling the *view's own* `plot_twotime` method (the one just edited); it already goes through the updated code path with no separate change needed.
- `gui/view/xpcs_viewer.py:614` — `self.plots.plot_twotime(self.mp_2t_hdls, **kwargs)`, the single direct call into `PlotController.plot_twotime`, already updated in Step 1.

- [ ] **Step 3: Run the full test suite**

Run: `pytest`
Expected: All tests pass (or skip, for the real-data tests that require `tests/data/` fixtures per `CLAUDE.md`) — no regressions from this change. `tests/test_twotime_selection.py` from Task 1 continues to pass.

- [ ] **Step 4: Manually verify in the running GUI**

Run: `pyxpcsviewer <path_to_hdf_directory>` (a directory containing at least two Twotime-capable `.hdf` result files — see `CLAUDE.md`'s "Conda environment for testing" note for the environment to use).

In the twotime tab:
1. Select a file, change the q-bin combobox to a non-zero index (e.g. index 2).
2. Select a different target file in the list.
3. Confirm the combobox now shows the same index position (2) rather than resetting to index 0, and the C2/G2 plots reflect that q-bin of the new file.
4. If available, select a file with fewer q-bins than the current selection and confirm the combobox clamps to its last valid index instead of erroring.

- [ ] **Step 5: Commit**

```bash
git add src/pyxpcsviewer/gui/view/xpcs_viewer.py
git commit -m "Keep twotime combobox/slider in sync with preserved qbin index"
```
