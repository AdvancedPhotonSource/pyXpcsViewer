#!/bin/bash

if [ "$1" != "" ]; then
    if [ "$1" == "--update" ]; then
        echo "update xpcs_gui"
        git pull
        exit
    fi
    target_folder=$(realpath $1)
else
    target_folder=`pwd`
fi

WD=/home/beams/8IDIUSER/Documents/Miaoqi/xpcs_gui
cd $WD
/APSshare/anaconda3/x86_64/bin/python gui.py $target_folder &

