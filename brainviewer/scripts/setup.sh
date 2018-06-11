#!/bin/bash

BIN=~/bin/
DOWNLOADS=~/Downloads/

cd ~
if [ ! -d "$BIN" ]; then
    mkdir ~/bin/bin
fi

if [ ! -d "$Downloads" ]; then
    mkdir ~/bin/bin
fi

echo "Installing c3d..."
./install_c3d.sh

echo "Installing matlab 2015 runtime..."
./install_mcr.sh