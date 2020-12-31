WD=xpcs_viewer
# ui file
pyuic5 $WD/ui/xpcs.ui -o viewer_ui.py
# resource file goes to the current level
pyrcc5 $WD/ui/resources/icons.qrc -o $WD/icons_rc.py
sed 's/import icons_rc.*/from . import icons_rc/' viewer_ui.py > $WD/viewer_ui.py
rm viewer_ui.py 

