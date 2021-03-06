#!/bin/bash
wget http://mirror.cs.umn.edu/blender.org/release/Blender2.78/blender-2.78c-linux-glibc219-x86_64.tar.bz2 -P ~/Downloads
wget https://www.blend4web.com/pub/blend4web_ce_17_06.zip -P ~/Downloads

tar -xjf ~/Downloads/blender-2.78c-linux-glibc219-x86_64.tar.bz2 --directory ~/bin/
mv ~/bin/blender-2.78c-linux-glibc219-x86_64 ~/bin/blender/
unzip ~/Downloads/blend4web_ce_17_06.zip -d ~/bin/
mv ~/bin/blend4web_ce_17_06/ ~/bin/blend4web

# Run setup_blender.py with the python runtime that is bundled with blender 
# to initialize scripts directory within blender
~/bin/blender/blender -b --python setup_blender.py
