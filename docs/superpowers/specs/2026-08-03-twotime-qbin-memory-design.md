# Twotime tab: remember qbin selection across dataset switches

## Problem

In the twotime tab, `comboBox_twotime_selection` lets the user pick which
processed q-bin's C2 map/G2 traces to display. When the user selects a
different dataset (target file) in the list, the combobox is repopulated
from that file's own q-bin labels (`XpcsFile.get_twotime_qbin_labels()`,
different files can have different q-bin sets/counts) and the selection
always resets to index 0, discarding whatever q-bin the user was looking at.

## Root cause

`PlotController.plot_twotime` (`gui/control/plot_controller.py:361-381`) is
called with `selection` computed from the *pre-switch* combobox index
(`gui/view/xpcs_viewer.py:607`). When the active file changes, it renders
once using that stale index against the *new* file's data (no bounds
check — `XpcsFile.get_twotime_c2` asserts
`selection < len(c2_processed_bins)`, so a new file with fewer q-bins than
the old selection would crash). The view then calls
`comboBox_twotime_selection.clear()` + `addItems(new_labels)`
(`gui/view/xpcs_viewer.py:615-618`), which resets `currentIndex()` to 0 and
fires `currentIndexChanged` (connected to `update_plot`,
`gui/view/xpcs_viewer.py:184`), triggering a second, corrective render at
index 0. The net observable behavior is: selection always ends up at 0,
with a wasted intermediate render (and a crash risk) along the way.

## Goal

When a new dataset is selected in the twotime tab, keep the previously
used q-bin **index position** (not by matching q-bin label/value) instead
of resetting to 0. This is session-only, in-memory state — no persistence
to disk, resets naturally on app restart.

## Design

### 1. `gui/control/plot_controller.py::PlotController.plot_twotime`

Change return value from `new_qbin_labels | None` to
`(new_qbin_labels | None, selection: int)`.

When the active file changes (`self.current_dset is None or
self.current_dset.fname != xfile.fname`):
- Fetch `new_qbin_labels = xfile.get_twotime_qbin_labels()` (unchanged).
- Clamp the incoming `selection` kwarg to
  `[0, len(new_qbin_labels) - 1]` **before** calling
  `twotime.plot_twotime(xfile, hdl, selection=selection, **kwargs)`, so the
  actual render always uses a valid, position-preserved index for the new
  file.
- Return `(new_qbin_labels, selection)` with the (possibly clamped) value
  that was actually rendered.

When the file has not changed, return `(None, selection)` unchanged
(selection passes through as given, matching current behavior of not
touching the combobox).

### 2. `gui/view/xpcs_viewer.py::XpcsViewer.plot_twotime`

The `kwargs["selection"]` computed via
`max(0, self.comboBox_twotime_selection.currentIndex())` already *is* the
"remembered" pre-switch position — no new state variable needed.

After the render call:

```python
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

Blocking signals on both widgets during repopulation is required: without
it, `clear()`/`addItems()` fire `currentIndexChanged` (wired to
`update_plot`), causing the redundant double-render that is the root cause
of today's "always resets to 0" behavior. With this change, exactly one
render happens per file switch, at the correct clamped index, and the
combobox/slider end up visually in sync with what was actually rendered.

## Edge cases

- **First-ever twotime render** (`current_dset is None`): pre-switch
  combobox index is `-1` → `max(0, -1)` = 0 → clamped to `[0, N-1]` → 0.
  Same as today.
- **New file has fewer q-bins than the remembered index**: clamp to the
  last valid index (`len(new_qbin_labels) - 1`), instead of the current
  assertion-crash risk.
- **New file has ≥ as many q-bins**: remembered index carries over exactly.
- **Switching between already-visited files** (`current_dset.fname`
  unchanged): combobox is not touched at all — unchanged from today.
- **Persistence**: session-only. No disk/QSettings persistence; state is
  just live widget state.

## Out of scope

- Matching the remembered selection by q-bin label/value across files with
  differing q-bin sets (explicitly rejected in favor of position-based
  matching).
- Persisting the selection across app restarts.
- Any other tab's combobox/selection state.

## Testing

No existing test exercises the twotime tab's widget interactions
(`tests/test_xpcs_viewer_smoke.py` is GUI-smoke-level only). Add a focused
test that calls `PlotController.plot_twotime` directly against two
minimal stub objects standing in for `XpcsFile` (differing
`c2_processed_bins` lengths, via `model.get_xf_list` returning the stub),
verifying:
- Index is preserved across a file switch when the new file has enough
  q-bins.
- Index is clamped to the last valid one when the new file has fewer
  q-bins.
- The returned tuple shape `(labels_or_None, selection)` is correct in
  both the file-changed and file-unchanged cases.

This avoids needing a real Qt event loop for the core clamping logic.
