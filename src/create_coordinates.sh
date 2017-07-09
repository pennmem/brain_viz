#!/bin/bash

CODEDIR=$(pwd)
SUBJECT=$1
CONTACTDIR=$2

cd $CONTACTDIR/
matlab -r "coords4blender('$SUBJECT', '$CONTACTDIR'); exit;"
cd $CODEDIR


