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
./install_c3d.sh

echo "Installing matlab 2015 runtime..."
./install_mcr.sh