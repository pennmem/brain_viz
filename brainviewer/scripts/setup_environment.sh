#!/bin/bash

# Constants needed by matlab and the matlab runtime to run the brainviewer pipeline
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:"~/bin/mcr/v85/runtime/glnxa64:~/bin/mcr/v85/bin/glnxa64:~/bin/mcr/v85/sys/os/glnxa64"
export MCR_CACHE_ROOT="~/"

# Add bin folder and c3d to path
PATH=$PATH:~/bin:~/c3d/bin/:/usr/global/freesurfer/bin:/usr/global/freesurfer/mni/bin:/home2/iped/dcmtk-3.6.0-linux-i686-static/bin:

# Freesurfer setup
export FREESURFER_HOME="/usr/global/freesurfer"
export SUBJECTS_DIR="/data10/eeg/freesurfer/subjects/"
source $FREESURFER_HOME/SetUpFreeSurfer.sh

export PATH

# Make an alias for blender
export BLENDER_HOME=/usr/global/blender-2.78c-linux-glibc219-x86_64/
alias blender=$BLENDER_HOME/blender



