# Copyright © UChicago Argonne LLC
# See LICENSE file for details

WD="$(cd "$(dirname "$0")" && pwd)"
HEADER='# Copyright © UChicago Argonne LLC
# See LICENSE file for details'
TMP="$(mktemp -d)"
# ui file
pyside6-uic "$WD/view.ui" -o "$TMP/viewer_ui.py"
# resource file goes to the current level, with the license header prepended
pyside6-rcc "$WD/resources/icons.qrc" -o "$TMP/icons_rc.py"
{ printf '%s\n\n' "$HEADER"; cat "$TMP/icons_rc.py"; } > "$WD/icons_rc.py"
# fix the resource import and insert the license header after the encoding line
{ head -n 1 "$TMP/viewer_ui.py"; printf '%s\n' "$HEADER"; tail -n +2 "$TMP/viewer_ui.py"; } \
    | sed 's/import icons_rc.*/from . import icons_rc/' > "$WD/viewer_ui.py"
rm -r "$TMP"
