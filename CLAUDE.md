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
`QT_QPA_PLATFORM=offscreen` to construct real Qt widgets headlessly). `test_pyxpcsviewer.py` is still an
unmodified cookiecutter stub (imports the nonexistent `pyxpcsviewer.pyxpcsviewer`, no real assertions) —
harmless, but don't treat it as a template for new tests.

`test_real_data.py` exercises real XPCS result files through `hdf_reader`/`XpcsFile` (one Multitau-only file,
one Twotime-only file, one with both). Fixtures live in `tests/conftest.py` and resolve paths under
`tests/data/`, which is a symlink to a scratch location (`/scratch/MQICHU/Datasets/xpcs/pyxpcsviewer_test_data`
on the primary dev machine) — the real `.hdf` files are intentionally not tracked in git (`tests/data` is
gitignored). The fixtures `pytest.skip` per-file if the target is missing, so the suite still runs clean
without the data present; only `test_real_data.py`'s cases actually need it.

There is still no CI workflow that runs tests — `.github/workflows/` only has `publish-pypi.yml` (PyPI publish
on tag) and `build-releases.yml` (PyInstaller/AppImage builds on tag). `tox.ini` is likewise stale (references
`py36`/`py37`/`setup.py test`) and is not part of the real dev workflow.

### Regenerating the Qt UI

`src/pyxpcsviewer/gui/view/viewer_ui.py` (~2900 lines) and `src/pyxpcsviewer/gui/view/icons_rc.py` are generated
from `src/pyxpcsviewer/gui/view/view.ui` (Qt Designer) and `gui/view/resources/icons.qrc`. Never hand-edit either
generated file — edit the `.ui`/`.qrc` and regenerate:

```bash
src/pyxpcsviewer/gui/view/convert_ui_to_py.sh
```

## Architecture

The codebase is split into `core/` (pure, GUI-independent logic) and `gui/` (PySide6/pyqtgraph MVC layer that
imports from `core/`); `web/` is an empty placeholder package reserved for a future web frontend.

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
  - **`core/default_setting.py`** holds the default window-size settings dict.
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

### Data format

Result files are HDF5 with a NeXus-derived layout rooted at `/xpcs/...` and `/entry/...`. A file can contain
`Multitau` data (`/xpcs/multitau/...`), `Twotime` data (`/xpcs/twotime/...`), or both — check via
`core.fileIO.hdf_reader.get_analysis_type`. Q-map metadata (masks, beam center, dynamic/static ROI maps) lives
under `/xpcs/qmap/...` and is shared/cached across files via `QMapManager` (keyed by a content hash) since many
result files in one experiment share the same detector geometry.
