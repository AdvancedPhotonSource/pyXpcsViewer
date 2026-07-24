# Step 2 Plan: Convert GUI into MVC structure

Target layout (final state of `src/pyxpcsviewer/`):

```
src/pyxpcsviewer/
├── __init__.py
├── cli.py
├── core/                     # done in step 1
│   ├── __init__.py
│   ├── default_setting.py
│   ├── fast_g2_averaging.py
│   ├── fitting.py
│   ├── g2_utils.py
│   ├── twotime_utils.py
│   ├── xpcs_file.py
│   └── fileIO/
│       ├── __init__.py
│       ├── aps_8idi.py
│       ├── ftype_utils.py
│       ├── hdf_reader.py
│       └── qmap_utils.py
├── gui/
│   ├── __init__.py
│   ├── model/
│   │   ├── __init__.py
│   │   ├── listmodel.py          # from helper/listmodel.py
│   │   └── file_locator.py       # from file_locator.py
│   ├── control/
│   │   ├── __init__.py
│   │   ├── viewer_kernel.py      # from viewer_kernel.py
│   │   ├── average_toolbox.py    # from module/average_toolbox.py (whole file, per your decision)
│   │   └── plot/
│   │       ├── __init__.py       # from module/__init__.py
│   │       ├── g2mod.py
│   │       ├── intt.py
│   │       ├── saxs1d.py
│   │       ├── saxs2d.py
│   │       ├── stability.py
│   │       ├── tauq.py
│   │       └── twotime.py
│   └── view/
│       ├── __init__.py
│       ├── xpcs_viewer.py        # from xpcs_viewer.py
│       ├── viewer_ui.py          # generated, from viewer_ui.py
│       ├── icons_rc.py           # generated, from icons_rc.py
│       ├── convert_ui_to_py.sh   # from scripts/update_ui.sh, paths updated
│       ├── view.ui               # from ui/xpcs.ui
│       ├── plothandler/
│       │   ├── __init__.py
│       │   ├── matplot_qt.py
│       │   └── pyqtgraph_handler.py
│       └── resources/
│           ├── icons.qrc         # from ui/resources/icons.qrc
│           └── icons8-giraffe-full-body-100.png
└── web/
    └── __init__.py               # empty package, left blank per your instructions
```

`configure/aps_8idi.json` and `module_web/`, `web_gui.py` are dead/unreferenced (confirmed via grep — nothing imports `configure`, and `web_gui.py`/`module_web` already documented in CLAUDE.md as an unfinished, non-wired prototype). Plan: delete `configure/` (genuinely orphaned, not even loaded), and delete `web_gui.py` + `module_web/` since `web/` is being deliberately left blank per your instructions and these aren't wired to anything anyway. I will confirm this with you before deleting (see "Confirm before delete" below) rather than doing it silently.

## File-by-file actions

### gui/model/
- `git mv helper/listmodel.py gui/model/listmodel.py`. No internal changes needed (only imports `PySide6.QtCore`, `os`).
- `git mv file_locator.py gui/model/file_locator.py`. Edit imports:
  - `from .fileIO.qmap_utils import QMapManager` → `from ..core.fileIO.qmap_utils import QMapManager`
  - `from .helper.listmodel import ListDataModel` → `from .listmodel import ListDataModel`
  - `from .xpcs_file import XpcsFile as XF` → `from ..core.xpcs_file import XpcsFile as XF`
- Remove now-empty `helper/` directory once `listmodel.py` and its `__init__.py` are moved. Remove now-empty `fileIO/` directory (already emptied in step 1, only has `__init__.py` left) — delete it.
- New `gui/model/__init__.py` (empty).

### gui/control/
- `git mv viewer_kernel.py gui/control/viewer_kernel.py`. Edit imports:
  - `from .file_locator import FileLocator` → `from ..model.file_locator import FileLocator`
  - `from .helper.listmodel import TableDataModel` → `from ..model.listmodel import TableDataModel`
  - `from .module import g2mod, intt, saxs1d, saxs2d, stability, tauq, twotime` → `from .plot import g2mod, intt, saxs1d, saxs2d, stability, tauq, twotime`
  - `from .module.average_toolbox import AverageToolbox` → `from .average_toolbox import AverageToolbox`
  - `from .xpcs_file import XpcsFile` → `from ..core.xpcs_file import XpcsFile`
  - Fix `get_pg_tree(self, rows)`: replace the body's `xf_list[0].get_pg_tree()` call with a local implementation (was removed from `XpcsFile` in step 1 because it's GUI code). Add a module-level helper `_build_pg_tree(xf)` in `viewer_kernel.py` that reconstructs the old logic using `xf.load_data()` + `pg.DataTreeWidget` (this is legitimate here since `viewer_kernel.py` now lives in `gui/control/` and already imports `pyqtgraph as pg`):
    ```python
    def _build_pg_tree(xf):
        data = xf.load_data()
        for key, val in data.items():
            if isinstance(val, np.ndarray):
                if val.size > 4096:
                    data[key] = "data size is too large"
                if val.size == 1:
                    data[key] = float(val)
        data["analysis_type"] = xf.atype
        data["label"] = xf.label
        tree = pg.DataTreeWidget(data=data)
        tree.setWindowTitle(xf.fname)
        tree.resize(600, 800)
        return tree
    ```
    and change `get_pg_tree(self, rows)` to `return _build_pg_tree(xf_list[0])`.
- `git mv module/average_toolbox.py gui/control/average_toolbox.py`. Edit imports:
  - `from ..fileIO.hdf_reader import put, get` → `from ..core.fileIO.hdf_reader import put, get`
  - `from ..xpcs_file import XpcsFile as XF` → `from ..core.xpcs_file import XpcsFile as XF`
  - `from ..helper.listmodel import ListDataModel` → `from ..model.listmodel import ListDataModel`
  - `from .fast_G2_averaging import fast_average_shared_memory` → `from ..core.fast_g2_averaging import fast_average_shared_memory`
- `git mv module gui/control/plot` (moves the whole directory in one step: `g2mod.py`, `intt.py`, `saxs1d.py`, `saxs2d.py`, `stability.py`, `tauq.py`, `twotime.py`, `__init__.py`; `average_toolbox.py` already moved out above).
  - Edit `gui/control/plot/__init__.py`: no path changes needed (relative imports `from . import g2mod` etc. still resolve); add `tauq` and `twotime` to match what `viewer_kernel.py` actually imports (currently `__init__.py`'s `__all__`/imports only lists 5 of 7 — leave as-is unless you want it fixed; not in scope for step 2, flagging only).
  - Edit `gui/control/plot/saxs1d.py`: `from ..plothandler.matplot_qt import get_color_marker` → `from ...view.plothandler.matplot_qt import get_color_marker`
  - `stability.py`'s `from .saxs1d import ...` needs no change (still same-directory).
- New `gui/control/__init__.py` (empty).

### gui/view/
- `git mv xpcs_viewer.py gui/view/xpcs_viewer.py`. Edit imports:
  - `from .module.apply_qmap import has_G2_field` → `from ..core.g2_utils import has_G2_field`
  - `from .viewer_kernel import ViewerKernel` → `from ..control.viewer_kernel import ViewerKernel`
  - `from .viewer_ui import Ui_mainWindow as Ui` → `from .viewer_ui import Ui_mainWindow as Ui` (unchanged, still same directory)
  - Inside `load_default_setting()`: `from .default_setting import setting` → `from ..core.default_setting import setting`
- `git mv viewer_ui.py gui/view/viewer_ui.py`. Edit generated import: `from .plothandler import (...)` → `from .plothandler import (...)` (unchanged — plothandler moves alongside it into `gui/view/plothandler/`). `from . import icons_rc` stays unchanged (same directory).
- `git mv icons_rc.py gui/view/icons_rc.py`. No changes (no internal relative imports).
- `git mv plothandler gui/view/plothandler`. No internal import changes needed (`matplot_qt.py`/`pyqtgraph_handler.py` only import external libs).
- `git mv ui/xpcs.ui gui/view/view.ui`.
- `git mv ui/resources gui/view/resources` (carries `icons.qrc` and the png).
- Remove now-empty `ui/` directory.
- `git mv scripts/update_ui.sh gui/view/convert_ui_to_py.sh`. Update paths inside (it currently does `cd`-relative `../src/pyxpcsviewer` and outputs to that dir); rewrite to reflect new locations:
  ```bash
  WD="$(cd "$(dirname "$0")" && pwd)"
  pyside6-uic "$WD/view.ui" -o viewer_ui.py
  pyside6-rcc "$WD/resources/icons.qrc" -o "$WD/icons_rc.py"
  sed 's/import icons_rc.*/from . import icons_rc/' viewer_ui.py > "$WD/viewer_ui.py"
  rm viewer_ui.py
  ```
- New `gui/view/__init__.py` (empty).

### gui/ top level
- New `gui/__init__.py` (empty).

### web/
- New `web/__init__.py` (empty package, per your instruction to leave it blank).

### cli.py
- No move (stays at `src/pyxpcsviewer/cli.py`, it's the top-level entry point, not GUI/core-specific).
- Edit: `from pyxpcsviewer.xpcs_viewer import main_gui` → `from pyxpcsviewer.gui.view.xpcs_viewer import main_gui`

### CLAUDE.md
- Update the "Layering" section and file paths to reflect the new `core/` + `gui/{model,control,view}` structure once step 2 lands (separate small edit after implementation, not part of the moves themselves).

## Confirm before delete
Two things look orphaned; I'll delete them as part of step 2 unless you say otherwise:
- `src/pyxpcsviewer/configure/aps_8idi.json` — nothing in the codebase references `configure` or this json file (grepped, zero hits); looks like a leftover duplicate of `core/fileIO/aps_8idi.py`'s `key` dict.
- `src/pyxpcsviewer/web_gui.py` and `src/pyxpcsviewer/module_web/` — already documented in CLAUDE.md as dead/experimental, unwired Dash prototype. Since `web/` is being created empty per your instruction, these don't move there; they'd just be deleted as dead code, or left in place untouched if you'd rather not touch them in this pass.

## Verification
After all moves/edits, run the same style of smoke test as step 1: import `pyxpcsviewer.cli`, `pyxpcsviewer.gui.view.xpcs_viewer`, `pyxpcsviewer.gui.control.viewer_kernel`, `pyxpcsviewer.gui.model.file_locator` and confirm no `ModuleNotFoundError`/`ImportError` (Qt app won't actually launch headlessly, but imports resolving cleanly proves the reorganization is wired correctly). Then run `git status --short` to confirm only expected renames/edits appear.
