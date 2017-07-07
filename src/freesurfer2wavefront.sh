#!/bin/bash

echo $1
echo $2

BASEDIR=$1
CORTEXDIR=$2

mkdir $CORTEXDIR

cp $BASEDIR/surf/lh.pial $CORTEXDIR/
cp $BASEDIR/surf/rh.pial $CORTEXDIR/
cp $BASEDIR/label/lh.aparc.annot $CORTEXDIR/
cp $BASEDIR/label/rh.aparc.annot $CORTEXDIR/

mris_convert $CORTEXDIR/lh.pial $CORTEXDIR/lh.pial.asc
mris_convert $CORTEXDIR/rh.pial $CORTEXDIR/rh.pial.asc

# This is just renaming. Can we just do this in the step above?
mv $CORTEXDIR/lh.pial.asc $CORTEXDIR/lh.pial.srf
mv $CORTEXDIR/rh.pial.asc $CORTEXDIR/rh.pial.srf

srf2obj $CORTEXDIR/lh.pial.srf > $CORTEXDIR/lh.pial.obj
srf2obj $CORTEXDIR/rh.pial.srf > $CORTEXDIR/rh.pial.obj
