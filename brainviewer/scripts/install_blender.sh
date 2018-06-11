#!/bin/bash
wget http://mirror.cs.umn.edu/blender.org/release/Blender2.78/blender-2.78c-linux-glibc219-x86_64.tar.bz2 -P ~/Downloads

wget https://www.blend4web.com/pub/blend4web_ce_17_06.zip -P ~/Downloads

tar -xzf ~/Downloads/blender-2.78c-linux-glibc219-x86_64.tar.bz2 --directory ~/bin/blender/

mkdir ~/bin/blend4web/
unzip ~/Downloads/blend4web_ce_17_06.zip -d ~/bin/blend4web/

# Run setup_scripts.py with blender to initialize scripts directory within blender
~/blender/blender -b --python setup_scripts.py
