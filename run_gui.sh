#!/bin/bash
LOG_FILE=.log

date >> $LOG_FILE
echo "start new gui instance" >> $LOG_FILE
echo "arguments: " "$@" >> $LOG_FILE

if [ "$1" != "" ]; then
    if [ "$1" == "--update" ]; then
        echo "update xpcs_gui"
        git pull
        exit
    fi
    target_folder=$(realpath $1)
else
    target_folder=$(pwd)
fi

echo "target folder $target_folder" >> $LOG_FILE

if [ -d $target_folder ]; then
    WD=/home/beams/8IDIUSER/Documents/Miaoqi/xpcs_gui
    cd $WD
    /APSshare/anaconda3/x86_64/bin/python gui.py $target_folder &
else
    echo "no such directory: " $1 or $target_folder
fi

echo "      " >> $LOG_FILE

