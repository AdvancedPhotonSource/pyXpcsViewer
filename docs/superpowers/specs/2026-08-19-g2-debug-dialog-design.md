# G2 Outlier Debug Dialog — Design

Date: 2026-08-19
Status: approved in brainstorming, pending spec review

## Problem

Debugging the G2 outlier-rejection logic (`compute_g2` / `find_g2_pixel_outliers` in
`core/g2_utils.py`) currently requires standalone matplotlib scripts run outside the
viewer (e.g. `sweep_sq_all_delays_exclude_zeros.py`, `plot_bad_pixel_map.py` in a dataset
directory). The goal is a **Debug button in the G2_regroup tab's "Group Setting" box** that
opens a pyqtgraph dialog visualizing exactly what the configured outlier settings do to the
currently selected file.

## Scope (approved)

- Plot group **A**: per-sq-bin g2_pixel histograms, both presentations:
  - *Bin sweep*: pick one sq bin → grid of histograms across all delays
  - *Delay sweep*: pick one delay → grid of histograms across all sq bins (paged)
- Plot group **B**: bad-pixel detector map — which pixels were flagged, colored by how many
  delays they were flagged
- Excluded (YAGNI): per-pixel tag-count histogram, per-sq outlier-fraction curve,
  ROI-structure/zero-pixel analysis, per-dq-bin histograms
- **Always** compute the outlier mask with the configured threshold + method, regardless of
  the "Remove Outlier" checkbox; the settings used are displayed in the dialog header
- pyqtgraph only (no matplotlib in the dialog)

## Architecture

Option chosen: **self-contained dialog module + pure core compute bundle**. The heavy
computation lives in `core/` (testable without Qt); the dialog is one new module under
`gui/view/`; the main window only gets a button and a short slot. The alternative
(controller-mediated) approach was rejected: the flow is asynchronous (background load), so
threading a ~600 MB bundle through `PlotController` adds indirection without benefit.

### Files

| File | Change |
|------|--------|
| `src/pyxpcsviewer/core/g2_utils.py` | + `compute_g2_debug_bundle()` |
| `src/pyxpcsviewer/gui/view/g2_debug_dialog.py` | **new** — worker + dialog + `build_debug_plots()` |
| `src/pyxpcsviewer/gui/view/view.ui` | + `pushButton_G2_debug` in `groupBox_23` |
| `src/pyxpcsviewer/gui/view/viewer_ui.py` | **regenerated** via `convert_ui_to_py.sh` (never hand-edited) |
| `src/pyxpcsviewer/gui/view/xpcs_viewer.py` | + connection + `debug_G2_regroup()` slot |
| `tests/test_g2_utils.py` | **new** — core bundle tests |
| `tests/test_g2_debug_dialog.py` | **new** — offscreen dialog-plot tests |

## Core: `compute_g2_debug_bundle`

```python
def compute_g2_debug_bundle(
    sqmap, dqmap, G2,
    outlier_method="MeanAbsoluteDeviation",
    outlier_threshold=3.0,
    combine_outlier=False,
) -> dict:
```

Mirrors `compute_g2`'s preprocessing exactly, so the dialog shows what ReGroup actually
sees:

1. Reshape `G2` from `(n_delays, 3, img_v, img_h)` to `(n_delays, 3, n_pixels)`
2. Dead-pixel mask: pixels with `IF1 == 0 & IF2 == 0` at **all** delays are set to 0 in
   working copies of `sqmap_1d`/`dqmap_1d` (same as `compute_g2`)
3. `g2_pixel = normalize_g2(G2)` → `(n_delays, n_pixels)`
4. `bad = find_g2_pixel_outliers(sqmap_1d, g2_pixel, threshold=outlier_threshold,
   method=outlier_method, combine_outlier=combine_outlier)` → bool `(n_delays, n_pixels)`

Returns a dict: `g2_pixel`, `bad`, `sqmap_1d`, `dqmap_1d` (dead-masked), `img_shape`,
`n_delays`, `n_sq`, `n_dq`, `n_dead`.

Pure numpy; no file IO. For A0096-sized data: 1.4 GB G2 load (done by the caller) + ~0.6 GB
of transient arrays (g2_pixel float32 ≈ 480 MB, bad bool ≈ 120 MB).

## Data flow

```
[Debug button]
  → xpcs_viewer.py::debug_G2_regroup()
      1. rows = get_selected_rows(); empty → return (silent)
      2. xf_list = model.get_xf_list(rows, filter_atype="Multitau"); empty → return
      3. xfile = xf_list[0]; not has_G2_field(xfile.fname) → QMessageBox.critical
      4. settings: method (comboBox_G2_outliermethod), threshold (doubleSpinBox_G2_threshold),
         combine (checkBox_G2_combineoutlier) — always applied
      5. if self._g2_debug_dialog is not None and self._g2_debug_dialog.isVisible()
         → raise_()/activateWindow(), return
      6. self._g2_debug_dialog = G2DebugDialog(xfile, method, threshold, combine, self)
         self._g2_debug_dialog.show()
```

### Threading (background worker — approved over main-thread blocking)

`G2DebugWorker(QThread)` in `g2_debug_dialog.py`:

- `run()`: ① `xfile.G2` (cached_property → fresh `h5py.File` per call, thread-safe),
  `xfile.sqmap`, `xfile.dqmap` (cached arrays); ② `compute_g2_debug_bundle(...)`
- Signals: `progress_stage(str)` ("Loading G2…", "Detecting outliers…"),
  `finished(object)` (bundle dict), `failed(str)` (exception text)
- Thread-safety rationale: `core/file_io/hdf_reader.get()` opens and closes its own
  `h5py.File` handle per call; `sqmap`/`dqmap` are read-only cached numpy arrays

### Dialog lifecycle

- `G2DebugDialog(xfile, method, threshold, combine_outlier, parent=None)` — modeless,
  single instance per main window (guarded in the slot)
- On open: placeholder page with centered "computing…" label + stage text + indeterminate
  `QProgressBar`; worker started
- `finished` → populate tabs via `build_debug_plots()` (synchronous, fast: only numpy
  slices + pyqtgraph items)
- `failed` → `QMessageBox.critical` with the error text, then close
- `closeEvent`: while the worker is running, `event.ignore()` (the 1.4 GB h5py read cannot
  be interrupted mid-read); after completion, close normally and the bundle is released
- Closing the dialog frees the bundle; `xfile.G2` stays in the XpcsFile cache (existing
  behavior — ReGroup pays the same cache cost)

## Dialog layout

**Header** (QLabel above a QTabWidget): file name, `n_delays` / `n_sq` / `n_dq` /
`n_dead`, and the settings used, e.g.
`method=MeanAbsoluteDeviation, threshold=3.0, combine=False`.

**Tab 1 — "sq-bin histograms"** (QSplitter, two panels):

- *Bin sweep*: `QSpinBox` (sq, 1..n_sq) → grid of all delays for that bin
  (columns = `ceil(sqrt(n_delays))`). Each subplot: histogram of **nonzero**
  `g2_pixel[d, roi]` (zero = photon-starved, excluded from the histogram), green center
  line, red dashed upper bound `center + threshold·spread`, title
  `delay=d  n=<nonzero count>  out=<flagged count>`. Bins with no pixels → "(empty)" title;
  all-zero delay → "(all zero)" title.
- *Delay sweep*: `QSpinBox` (delay, 0..n_delays−1) → grid of all sq bins, **60 per page**
  (12×5) with ◀ / ▶ buttons and a `page k/N` label (mirrors the paging in
  `debug_g2_outlier_hist_sq.py`). Same center/bound lines, title
  `sq=idx  n=<nonzero count>  out=<flagged count>`.

Histogram bounds shown are recomputed from the displayed (nonzero) values with the same
center/spread rule as `find_g2_pixel_outliers` (median / MAD-median or mean / std per the
selected method; `spread == 0` → 1.0) so the lines match the mask exactly.

**Tab 2 — "Bad-pixel map"**:

- pyqtgraph `ImageView` of `bad.sum(axis=0).reshape(img_shape)`, "hot" colormap + colorbar
  labeled "# delays this pixel was flagged as an outlier"
- `QSpinBox` **min tag count** (default 1): pixels with count below the minimum are masked
  (black). Covers both the ≥1 and ≥2 variants of the standalone scripts.
- Summary QLabel: `tagged ≥<min>: N (pct%), max count = M, dead pixels = n_dead`

## Error handling

- No rows selected / no Multitau file → slot returns silently (matches `process_G2_regroup`)
- No `unnormalized_G2` field → `QMessageBox.critical`, no dialog
- Worker exception (HDF5 read error, OOM, …) → `failed` → `QMessageBox.critical` + close
- Empty/all-zero sq bins → labeled empty axes, no crash
- `spread == 0` → clamped to 1.0 (existing behavior in `find_g2_pixel_outliers`)

## Testing

- `tests/test_g2_utils.py` (new; pure core, no Qt): `compute_g2_debug_bundle` on small
  synthetic arrays —
  - bundle shapes/dtypes (`g2_pixel` (n_delays, n_pixels), `bad` bool same shape)
  - dead-pixel masking (IF1=IF2=0 at all delays → zeroed in returned maps, `n_dead` count)
  - `bad` equals `find_g2_pixel_outliers(masked_sqmap, g2_pixel, ...)`
  - `combine_outlier=True` → union across delays per sq bin
  - known small case with a hand-computed outlier count
- `tests/test_g2_debug_dialog.py` (new; `QT_QPA_PLATFORM=offscreen`,
  `pytest.importorskip("PySide6")`, qapp fixture — same pattern as
  `test_xpcs_viewer_smoke.py`): call `build_debug_plots()` directly with a hand-made
  synthetic bundle (2 delays × 8 sq bins × 16 px) on a bare widget —
  - both tabs exist; header shows settings
  - changing the sq spinbox / delay spinbox re-renders without exception
  - min-tag spinbox re-masks the bad-pixel image
  - all-zero bin renders a labeled empty axis
- No GUI test touches a real HDF5 file or starts the worker thread (the worker is only
  exercised end-to-end manually).

## Manual verification

Run the viewer on `/home/beams/MQICHU/Datasets/xpcs/2026_0817_G2`, select the A0096 results
file in the target list, open the G2_regroup tab, set threshold 3.0 / MAD / no combine,
click Debug:

1. Bin sweep on a bin known to have outliers matches the values printed by
   `sweep_sq_all_delays_exclude_zeros.py` for that bin
2. Bad-pixel map matches `bad_pixel_map.png` (≥1) / `bad_pixel_map_exclude_one_tag.png` (≥2)
   from the standalone run (threshold 4.0 there → compare shape/locations, not exact counts)
3. Raising the threshold visibly shrinks flagged counts; Combine Outlier makes the map
   denser (union across delays)

## Out of scope / future

- Background-worker progress finer than 2 stages (h5py read is a single blocking call)
- Cancellation of an in-flight compute
- Multiple files / averaged-G2 debugging (ReGroup itself only uses the first selected file)
- Per-dq-bin histograms, tag-count histogram, per-sq outlier-fraction curve (groups C/D)
