# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

pyXPCSViewer (package `xpcs-viewer`, importable as `pyxpcsviewer`) is a PySide6/pyqtgraph desktop GUI for
visualizing and analyzing X-ray Photon Correlation Spectroscopy (XPCS) datasets produced at APS beamline 8-ID-I.
It reads a custom NeXus-based HDF5 format containing multi-tau (g2) and two-time correlation results, SAXS
1D/2D scattering, intensity-vs-time, and Q-map metadata.

## Commands

Conda environment for testing the installation and running the commands below: `/local/MQICHU/envs/l2604_xpcs`.

Install in editable mode with dev extras (the package is not installed by default in this checkout):

```bash
pip install -e ".[dev]"
```

Run the GUI:

```bash
pyxpcsviewer path_to_hdf_directory   # or: pyxpcsviewer   (uses cwd)
```

Run the web viewer (needs the `web` extras: `pip install -e ".[web,dev]"` — fastapi, uvicorn, plotly, httpx):

```bash
pyxpcsviewer-web path_to_hdf_directory            # serves http://127.0.0.1:8070/
pyxpcsviewer-web path --port 8070 --open          # --open starts a browser; --host 0.0.0.0 opens it to the network
```

Lint (no ruff config in the repo, so ruff runs with its default rule set):

```bash
ruff check .
ruff format .
```

Type check (`[tool.mypy]` in pyproject.toml runs in `strict` mode over the whole repo):

```bash
mypy .
```

Tests:

```bash
pytest
```

There is a real test suite under `tests/`: `test_fitting.py`, `test_g2_bounds_init.py`, `test_g2_mod.py`,
`test_view_utils.py`, and `test_xpcs_viewer_smoke.py` (the latter two `pytest.importorskip("PySide6")` and set
`QT_QPA_PLATFORM=offscreen` to construct real Qt widgets headlessly). The web viewer has `test_web_workspace.py`
(the service on the real files), `test_web_api.py` (the routes through FastAPI's `TestClient`; skipped without
fastapi/httpx) and `test_web_encoding.py`; the GUI-independent helpers have `test_discover.py`, `test_image_utils.py`
and `test_intt_utils.py`. `test_pyxpcsviewer.py` is still an
unmodified cookiecutter stub (imports the nonexistent `pyxpcsviewer.pyxpcsviewer`, no real assertions) —
harmless, but don't treat it as a template for new tests.

`test_real_data.py` exercises real XPCS result files through `hdf_reader`/`XpcsFile` (one Multitau-only file,
one Twotime-only file, one with both). Fixtures live in `tests/conftest.py` and resolve paths under
`tests/data/`, which is a symlink to a scratch location (`/scratch/MQICHU/Datasets/xpcs/pyxpcsviewer_test_data`
on the primary dev machine) — the real `.hdf` files are intentionally not tracked in git (`tests/data` is
gitignored). The fixtures `pytest.skip` per-file if the target is missing, so the suite still runs clean
without the data present; only `test_real_data.py`'s cases actually need it.

There is still no CI workflow that runs tests — `.github/workflows/` only has `publish-pypi.yml`, which builds
the sdist/wheel and publishes to PyPI on tag push. There is no PyInstaller/AppImage build workflow in the repo.

### Regenerating the Qt UI

`src/pyxpcsviewer/gui/view/viewer_ui.py` (~2900 lines) and `src/pyxpcsviewer/gui/view/icons_rc.py` are generated
from `src/pyxpcsviewer/gui/view/view.ui` (Qt Designer) and `gui/view/resources/icons.qrc`. Never hand-edit either
generated file — edit the `.ui`/`.qrc` and regenerate:

```bash
src/pyxpcsviewer/gui/view/convert_ui_to_py.sh
```

## Architecture

The codebase is split into `core/` (pure, GUI-independent logic), `gui/` (PySide6/pyqtgraph MVC layer that
imports from `core/`) and `web/` (a FastAPI service over `core/` plus a browser front end, see below).

### Layering

```
cli.py -> gui/view/xpcs_viewer.py (XpcsViewer QMainWindow, generated Ui_mainWindow)
              -> gui/control/viewer_kernel.py (ViewerKernel, extends FileLocator)
                    -> gui/model/file_locator.py (FileLocator: source/target file lists, XpcsFile cache)
                    -> gui/control/plot/*.py (stateless plotting/analysis functions)
                    -> core/xpcs_file.py (XpcsFile: one HDF5 result file)
                          -> core/fileIO/hdf_reader.py, core/fileIO/qmap_utils.py, core/fileIO/aps_8idi.py
```

- **`cli.py`** parses args and calls `gui.view.xpcs_viewer.main_gui(path, label_style)`.
- **`core/`** contains all GUI-independent logic — importable and usable without Qt ever being invoked:
  - **`core/xpcs_file.py`** (`XpcsFile`) wraps a single HDF5 result file, lazily exposing g2/g2_err, saxs_1d/2d,
    two-time, and Q-map data as attributes/properties, plus fitting via `core/fitting.py`
    (curve fits are cached on disk with `joblib.Memory` under `~/.pyxpcsviewer/joblib/`).
  - **`core/fileIO/aps_8idi.py`** is the single source of truth mapping semantic field names (e.g. `"g2"`,
    `"saxs_2d"`, `"dqmap"`) to literal HDF5 paths in the NeXus layout (e.g. `/xpcs/multitau/normalized_g2`).
    `core/fileIO/hdf_reader.py` (`get`/`put`/`get_analysis_type`) and `core/fileIO/qmap_utils.py`
    (`QMap`/`QMapManager`) read through this key map rather than hardcoding paths — when adding a new field,
    add it here first.
  - **`core/g2_utils.py`**, **`core/twotime_utils.py`**, **`core/fast_g2_averaging.py`** hold pure g2/two-time
    regrouping and multiprocessing-based fast-averaging logic (the last has an argparse CLI entry point).
  - **`core/file_io/discover.py`** (`list_result_files`) lists a folder's result files for both front ends;
    **`core/image_utils.py`** (block-mean downsampling, log scaling, percentile tables) and **`core/intt_utils.py`**
    (moving average, spectrum) are pure helpers the web viewer draws on.
- **`gui/`** is organized as MVC and imports from `core/` for all business logic:
  - **`gui/model/file_locator.py`** (`FileLocator`, parent of `ViewerKernel`) manages the "source" (files found
    in the working directory) and "target" (user-selected files) `ListDataModel`s, an `XpcsFile` object cache
    keyed by full path, and a shared `QMapManager`.
  - **`gui/model/listmodel.py`** provides `ListDataModel`/`TableDataModel`, thin `QAbstractListModel`/
    `QAbstractTableModel` wrappers used for the source/target file lists and the averaging job table.
  - **`gui/control/viewer_kernel.py`** (`ViewerKernel`) is the controller: it owns the `AverageToolbox` worker,
    fitting/plot orchestration, and delegates actual plotting to `gui/control/plot/` functions, passing them
    pyqtgraph/matplotlib widget handles plus a list of `XpcsFile` objects.
  - **`gui/control/plot/`** holds one file per analysis/plot domain (`g2mod`, `saxs1d`, `saxs2d`, `stability`,
    `intt`, `tauq`, `twotime`). These are plain functions taking a list of `XpcsFile` plus a plot handler, not
    classes — follow this pattern for new plot types rather than adding methods to `ViewerKernel` directly.
  - **`gui/control/average_toolbox.py`** (`AverageToolbox`) runs as a `QRunnable` submitted to
    `XpcsViewer.thread_pool`, using `multiprocessing.shared_memory` (via `core/fast_g2_averaging.py`) for fast
    G2 averaging across a `ProcessPoolExecutor`.
  - **`gui/view/xpcs_viewer.py`** defines `XpcsViewer`, which mixes the generated `Ui_mainWindow` (from
    `gui/view/viewer_ui.py`) with hand-written slots. Each GUI tab has a `plot_<tab>(self, dryrun=False, ...)`
    method that both builds a kwargs dict from widget state and (when `dryrun=False`) forwards it to the
    matching `ViewerKernel` method. `update_plot()` calls the current tab's `plot_*` in dryrun mode first and
    diffs kwargs against `self.plot_kwargs_record` to avoid redundant re-plots when nothing changed.
    `tab_mapping` in this file is the source of truth for tab index -> name -> `plot_<name>` method resolution.
  - **`gui/view/plothandler/`** wraps pyqtgraph (`pyqtgraph_handler.py`) and matplotlib (`matplot_qt.py`)
    widgets used as the custom widget classes referenced by `viewer_ui.py`.
  - **`gui/view/view.ui`**, **`gui/view/resources/icons.qrc`** are the Qt Designer sources for the generated
    `viewer_ui.py`/`icons_rc.py`.

### Web viewer (`web/`)

`pyxpcsviewer-web` (`web/cli.py`) serves one result folder in the browser with the three-column layout of gixsu's
web app (files and the metadata of the file shown | the detector image | one tab per analysis, result above
controls, gutters draggable). Nothing in `web/` imports Qt.

- **`web/workspace.py`** (`Workspace`) is the service: the folder's files (analysis types cached by name/mtime),
  an LRU of open `XpcsFile` objects, and one method per thing the page shows — `image` (downsampled detector maps
  with a 201-point percentile table for the contrast slider), `pixel`, `g2`/`fit_g2`/`tauq`, `saxs1d`,
  `stability`/`g2_stability`, `intt`, `twotime_bins`/`twotime_c2`/`twotime_bin_at`, `summary`, `hdf_info`. Every
  method returns a JSON-ready dict; large arrays are packed by **`web/encoding.py`** as base64 typed arrays
  (`{"dtype": "f4", "bdata": ..., "shape": [...]}`), decoded by `static/js/api.js`. `WorkspaceError` is a 4xx.
  Fits are run through `XpcsFile.fit_g2`/`fit_tauq`, so the τ(q) tab reads the g2 tab's fit from the same object.
- **`web/app.py`** (`build_app(root, label_style=, cache_size=, host=)`) wraps it as `/api/...` routes (OpenAPI
  at `/api/docs`), serves `static/` and `plotly.min.js` from the installed `plotly` package (`/vendor/`), and
  accepts only loopback Host headers (plus the bound address) unless bound to 0.0.0.0 (`trusted_hosts`).
- **`web/static/`** is the page, plain ES modules with no build step: `index.html` holds every panel's controls
  (named inputs read by `widgets.readForm`, persisted in localStorage); `style.css` carries the design tokens
  (gixsu's, so the tools look like one family) and bundles Inter as `fonts/inter-xpcs.woff2` (OFL, see the
  license file there); `js/state.js` is the store (files, the file shown, the files checked, the tab, the
  two-time bin); `js/files.js` and `js/image.js` are the left and center columns; `js/charts.js` is the Plotly
  theme and the panel grid; `js/g2figure.js` builds g2 grids for the g2 and stability tabs; `js/tabs/*.js` is one
  module per tab built with `tabs/base.js`'s `makeTab` (stale when its dependencies change, refreshed when
  shown). The URL carries the file shown, the files checked and the tab (`?file=&check=&tab=`), so a view can be
  shared. Analyses of several files use the checked files, else the file shown; single-file tabs (stability,
  two-time, metadata) use the file shown. A click on a q-bin of the image picks the two-time block.
- Not in the web viewer (Qt only): the averaging toolbox, G2 regrouping and its debug dialog, the g2 map.

### Data format

Result files are HDF5 with a NeXus-derived layout rooted at `/xpcs/...` and `/entry/...`. A file can contain
`Multitau` data (`/xpcs/multitau/...`), `Twotime` data (`/xpcs/twotime/...`), or both — check via
`core.fileIO.hdf_reader.get_analysis_type`. Q-map metadata (masks, beam center, dynamic/static ROI maps) lives
under `/xpcs/qmap/...` and is shared/cached across files via `QMapManager` (keyed by a content hash) since many
result files in one experiment share the same detector geometry.
