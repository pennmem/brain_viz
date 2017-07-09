#!/bin/bash

CODEDIR=$(pwd)
CONTACTDIR=$1
TALDIR=$2
OUTDIR=$3

mkdir $OUTDIR
mkdir $OUTDIR/axial
mkdir $OUTDIR/coronal

cp  $CODEDIR/../iEEG_surface_template/* $OUTDIR/
cp $CONTACTDIR/monopolar_names.txt $OUTDIR/
cp $CONTACTDIR/bipolar_names.txt $OUTDIR/
cp $CONTACTDIR/monopolar_start_names.txt $OUTDIR/
cp $TALDIR/VOX_coords_mother_dykstra.txt $OUTDIR/
cp $TALDIR/VOX_coords_mother_dykstra_bipolar.txt $OUTDIR/

