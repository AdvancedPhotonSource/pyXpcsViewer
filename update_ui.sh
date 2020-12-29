WD=xpcs_viewer
# ui file
pyuic5 $WD/ui/xpcs.ui -o $WD/viewer_ui.py
# resource file goes to the current level
pyrcc5 $WD/ui/resources/icons.qrc -o icons_rc.py
