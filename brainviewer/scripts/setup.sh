#!/bin/bash

BIN=~/bin/
DOWNLOADS=~/Downloads/

cd ~
if [ ! -d "$BIN" ]; then
    mkdir $BIN
fi

if [ ! -d "$Downloads" ]; then
    mkdir $DOWNLOADS
fi

echo "Installing c3d..."
~/brain_viz/brainviewer/scripts/install_c3d.sh

echo "Installing matlab 2015 runtime..."
~/brain_viz/brainviewer/scripts/install_mcr.sh
