# Step 1 plan: extract `core/`

Goal: create `src/pyxpcsviewer/core/` containing every function/class that has
no GUI (PySide6/pyqtgraph/matplotlib) dependency, so it can eventually be used
headlessly and imported cleanly by the future `gui/` package. This step does
**not** need to keep the app runnable — GUI files are left as-is (still
importing old locations) and will be rewired in step 2.

## New layout

```
src/pyxpcsviewer/core/
├── __init__.py
├── fileIO/
│   ├── __init__.py
│   ├── aps_8idi.py         <- moved verbatim from fileIO/aps_8idi.py
│   ├── ftype_utils.py      <- moved verbatim from fileIO/ftype_utils.py
│   ├── hdf_reader.py       <- moved verbatim from fileIO/hdf_reader.py
│   └── qmap_utils.py       <- moved verbatim from fileIO/qmap_utils.py
├── fitting.py              <- moved verbatim from helper/fitting.py
├── twotime_utils.py        <- moved verbatim from module/twotime_utils.py
├── g2_utils.py             <- moved from module/apply_qmap.py (see below)
├── fast_g2_averaging.py    <- moved from module/fast_G2_averaging.py, minus
│                              the `main()`/argparse CLI block (see below)
└── xpcs_file.py            <- moved from xpcs_file.py, with the one GUI
                               method (get_pg_tree) removed
```

No file in `core/` will import anything from `PySide6`, `pyqtgraph`, or
`matplotlib`. `core/` will not import anything from the future `gui/`
package — dependencies only flow core → nothing, gui → core.

## File-by-file actions

1. **`fileIO/aps_8idi.py`, `fileIO/ftype_utils.py`, `fileIO/hdf_reader.py`, `fileIO/qmap_utils.py`**
   → move as-is into `core/fileIO/`. No GUI imports found in any of them.
   Internal relative imports (`.aps_8idi`) keep working unchanged since the
   package structure is preserved 1:1.

2. **`helper/fitting.py`** → move to `core/fitting.py`. Pure numpy/scipy/
   sklearn/joblib, no GUI coupling. (`helper/listmodel.py` stays behind —
   it subclasses `QAbstractListModel`/`QAbstractTableModel` and is GUI-only;
   it will move into `gui/model/` in step 2.)

3. **`module/twotime_utils.py`** → move to `core/twotime_utils.py`. Pure
   h5py/numpy, no GUI coupling. Update its internal import
   `from ..fileIO.aps_8idi import key` → `from .fileIO.aps_8idi import key`.

4. **`module/apply_qmap.py`** → move to `core/g2_utils.py` (renamed: the
   file is about G2→g2 regrouping math and HDF I/O, not "applying a qmap").
   Drop the `test(fname)` function at the bottom, which does
   `import matplotlib.pyplot as plt` and is dead/debug-only code (not called
   anywhere in the codebase) — confirmed via grep. Keep `keymap`,
   `has_G2_field`, `average_by_qindex`, `compute_g2`, `save_G2_to_file`,
   `regroup_G2_with_qmap_array`, `regroup_G2`.

5. **`module/fast_G2_averaging.py`** → move to `core/fast_g2_averaging.py`.
   This file has no GUI imports, but has a `main()` + `argparse` +
   `if __name__ == "__main__"` CLI block (lines ~474-602) for standalone
   command-line use. Keep it — it's a legitimate non-GUI entry point, not
   dead code, and doesn't conflict with "core has no GUI deps." Update its
   internal import `from .apply_qmap import ...` → `from .g2_utils import ...`.

6. **`module/average_toolbox.py`** — **stays put** (not moved to core). It
   subclasses `QtCore.QRunnable`/`QObject` and emits Qt signals; it is a
   GUI-triggered background worker, not core logic. It will move to
   `gui/control/` (or similar) in step 2. Its helper function
   `_process_single_file` and `validate_g2_baseline` are pure and *could*
   be extracted, but per your instructions core extraction should preserve
   working units rather than surgically split a single small file — leaving
   the whole module for step 2 is simpler and lower risk. (Flag this as a
   judgment call — I can split it now instead if you'd rather.)

7. **`xpcs_file.py`** → move to `core/xpcs_file.py`. This file has exactly
   one GUI touchpoint: `get_pg_tree()` (uses `pg.DataTreeWidget`). That
   method will be deleted from `core/xpcs_file.py`'s `XpcsFile` class and
   re-implemented as a free function in `gui/` (step 2) that takes an
   `XpcsFile` instance and builds the widget — since `XpcsFile.load_data()`
   is public, this is a direct lift-and-shift for step 2. The `import
   pyqtgraph as pg` line is removed accordingly. Internal imports update:
   - `from .fileIO.hdf_reader import ...` → `from .fileIO.hdf_reader import ...` (unchanged path since fileIO moves with it, still `core/fileIO/`)
   - `from .fileIO.qmap_utils import get_qmap` → unchanged path
   - `from .helper.fitting import fit_with_fixed` → `from .fitting import fit_with_fixed`
   - `from .module.twotime_utils import ...` → `from .twotime_utils import ...`
   - the two lazy imports of `from .module.apply_qmap import ...` inside
     `regroup_G2`/`save_G2` methods → `from .g2_utils import ...`

8. **`default_setting.py`** → move to `core/default_setting.py` (trivial
   dict, no dependencies, purely data used by the GUI's settings loader).

## What stays outside `core/` (for step 2 to handle)

- `helper/listmodel.py` — Qt model classes.
- `file_locator.py` — imports `helper/listmodel.ListDataModel` (Qt), so it's
  GUI-adjacent even though it has no widget code; leave for step 2 to decide
  whether it becomes a controller or gets its Qt dependency swapped out.
- `viewer_kernel.py`, `xpcs_viewer.py`, `viewer_ui.py`, `icons_rc.py`,
  `cli.py` — GUI entry points/controllers.
- `module/g2mod.py`, `module/saxs1d.py`, `module/saxs2d.py`,
  `module/stability.py`, `module/intt.py`, `module/twotime.py`,
  `module/tauq.py`, `module/average_toolbox.py` — all plotting functions
  (pyqtgraph/matplotlib draw calls) or Qt workers; these are exactly the
  "module" layer the CLAUDE.md describes as plot/analysis glue and belong
  in `gui/` in step 2.
- `plothandler/` — pyqtgraph/matplotlib widget wrappers, GUI-only.
- `web_gui.py`, `module_web/` — dead prototype code; left in place
  untouched (not part of either core or gui/web scaffolding — you said
  leave `web/` blank for now, so I won't migrate this dead code into it).

## Mechanical steps

1. `git mv` each file/directory listed above into its new `core/...` location.
2. Fix intra-core relative imports (listed per-file above).
3. Add `core/__init__.py` (empty, or re-export `XpcsFile` similar to the
   current top-level `__init__.py`'s `from pyxpcsviewer.xpcs_file import
   XpcsFile` — will ask whether you want that re-export or a bare empty file).
4. Do **not** touch any file outside `core/` in this step — old files keep
   their old imports (`from .fileIO...`, `from .helper.fitting...`, etc.)
   even though those paths will now be broken. This is the accepted
   "temporarily broken" tradeoff you chose. `viewer_kernel.py`,
   `xpcs_viewer.py`, `file_locator.py`, `module/average_toolbox.py`,
   `module/fast_G2_averaging.py`'s old copy, etc. will not import
   successfully until step 2 rewires them — expected and fine.
5. Sanity-check `core/` is self-contained and GUI-free:
   `grep -rE "PySide6|pyqtgraph|matplotlib" src/pyxpcsviewer/core/` → must
   return nothing.
6. Smoke-test core in isolation with a throwaway script (not committed)
   that does `python -c "from pyxpcsviewer.core.xpcs_file import XpcsFile"`
   from a clean environment/venv where PySide6/pyqtgraph aren't even needed
   for this import chain, confirming zero GUI coupling.

## Open judgment call to confirm

`module/average_toolbox.py`: leave entirely for step 2 (option A, as
planned above), or split now — extract `_process_single_file` and
`validate_g2_baseline` (pure, no Qt) into `core/average_utils.py` and leave
the `AverageToolbox(QRunnable)` class behind? Defaulting to option A
(leave it all for step 2) unless you tell me otherwise.
