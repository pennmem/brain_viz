#!/bin/bash

CODEDIR=$(pwd) # current/code directory
CORTEXDIR=$1

cd $CORTEXDIR/
matlab -r "annot2dpv lh.aparc.annot lh.aparc.annot.dpv;annot2dpv rh.aparc.annot rh.aparc.annot.dpv;splitsrf lh.pial.srf lh.aparc.annot.dpv lh.pial_roi;splitsrf rh.pial.srf rh.aparc.annot.dpv rh.pial_roi;exit;"
cd $CODEDIR

srf2obj $CORTEXDIR/lh.pial_roi.0001.srf > $CORTEXDIR/lh.Unmeasured.obj
srf2obj $CORTEXDIR/lh.pial_roi.0002.srf > $CORTEXDIR/lh.BanksSuperiorTemporal.obj
srf2obj $CORTEXDIR/lh.pial_roi.0003.srf > $CORTEXDIR/lh.CACingulate.obj
srf2obj $CORTEXDIR/lh.pial_roi.0004.srf > $CORTEXDIR/lh.MiddleFrontalCaudal.obj
srf2obj $CORTEXDIR/lh.pial_roi.0005.srf > $CORTEXDIR/lh.Cuneus.obj
srf2obj $CORTEXDIR/lh.pial_roi.0006.srf > $CORTEXDIR/lh.Entorhinal.obj
srf2obj $CORTEXDIR/lh.pial_roi.0007.srf > $CORTEXDIR/lh.Fusiform.obj
srf2obj $CORTEXDIR/lh.pial_roi.0008.srf > $CORTEXDIR/lh.InferiorParietal.obj
srf2obj $CORTEXDIR/lh.pial_roi.0009.srf > $CORTEXDIR/lh.InferiorTemporal.obj
srf2obj $CORTEXDIR/lh.pial_roi.0010.srf > $CORTEXDIR/lh.Isthmus.obj
srf2obj $CORTEXDIR/lh.pial_roi.0011.srf > $CORTEXDIR/lh.LateralOccipital.obj
srf2obj $CORTEXDIR/lh.pial_roi.0012.srf > $CORTEXDIR/lh.OrbitalFrontal.obj
srf2obj $CORTEXDIR/lh.pial_roi.0013.srf > $CORTEXDIR/lh.Lingual.obj
srf2obj $CORTEXDIR/lh.pial_roi.0014.srf > $CORTEXDIR/lh.MedialOrbitalFrontal.obj
srf2obj $CORTEXDIR/lh.pial_roi.0015.srf > $CORTEXDIR/lh.MiddleTemporal.obj
srf2obj $CORTEXDIR/lh.pial_roi.0016.srf > $CORTEXDIR/lh.Parahippocampal.obj
srf2obj $CORTEXDIR/lh.pial_roi.0017.srf > $CORTEXDIR/lh.ParacentralLobule.obj
srf2obj $CORTEXDIR/lh.pial_roi.0018.srf > $CORTEXDIR/lh.InfFrontalParsOpercularis.obj
srf2obj $CORTEXDIR/lh.pial_roi.0019.srf > $CORTEXDIR/lh.InfFrontalParsOrbitalis.obj
srf2obj $CORTEXDIR/lh.pial_roi.0020.srf > $CORTEXDIR/lh.InfFrontalParsTriangularis.obj
srf2obj $CORTEXDIR/lh.pial_roi.0021.srf > $CORTEXDIR/lh.Pericalcarine.obj
srf2obj $CORTEXDIR/lh.pial_roi.0022.srf > $CORTEXDIR/lh.Post-Central.obj
srf2obj $CORTEXDIR/lh.pial_roi.0023.srf > $CORTEXDIR/lh.PosteriorCingulate.obj
srf2obj $CORTEXDIR/lh.pial_roi.0024.srf > $CORTEXDIR/lh.Pre-Central.obj
srf2obj $CORTEXDIR/lh.pial_roi.0025.srf > $CORTEXDIR/lh.PreCuneus.obj
srf2obj $CORTEXDIR/lh.pial_roi.0026.srf > $CORTEXDIR/lh.RACingulate.obj
srf2obj $CORTEXDIR/lh.pial_roi.0027.srf > $CORTEXDIR/lh.MiddleFrontalRostral.obj
srf2obj $CORTEXDIR/lh.pial_roi.0028.srf > $CORTEXDIR/lh.SuperiorFrontal.obj
srf2obj $CORTEXDIR/lh.pial_roi.0029.srf > $CORTEXDIR/lh.SuperiorParietal.obj
srf2obj $CORTEXDIR/lh.pial_roi.0030.srf > $CORTEXDIR/lh.SuperiorTemporal.obj
srf2obj $CORTEXDIR/lh.pial_roi.0031.srf > $CORTEXDIR/lh.Supra-Marginal.obj
srf2obj $CORTEXDIR/lh.pial_roi.0032.srf > $CORTEXDIR/lh.FrontalPole.obj
srf2obj $CORTEXDIR/lh.pial_roi.0033.srf > $CORTEXDIR/lh.TemporalPole.obj
srf2obj $CORTEXDIR/lh.pial_roi.0034.srf > $CORTEXDIR/lh.TransverseTemporal.obj
srf2obj $CORTEXDIR/lh.pial_roi.0035.srf > $CORTEXDIR/lh.Insula.obj
srf2obj $CORTEXDIR/rh.pial_roi.0001.srf > $CORTEXDIR/rh.Unmeasured.obj
srf2obj $CORTEXDIR/rh.pial_roi.0002.srf > $CORTEXDIR/rh.BanksSuperiorTemporal.obj
srf2obj $CORTEXDIR/rh.pial_roi.0003.srf > $CORTEXDIR/rh.CACingulate.obj
srf2obj $CORTEXDIR/rh.pial_roi.0004.srf > $CORTEXDIR/rh.MiddleFrontalCaudal.obj
srf2obj $CORTEXDIR/rh.pial_roi.0005.srf > $CORTEXDIR/rh.Cuneus.obj
srf2obj $CORTEXDIR/rh.pial_roi.0006.srf > $CORTEXDIR/rh.Entorhinal.obj
srf2obj $CORTEXDIR/rh.pial_roi.0007.srf > $CORTEXDIR/rh.Fusiform.obj
srf2obj $CORTEXDIR/rh.pial_roi.0008.srf > $CORTEXDIR/rh.InferiorParietal.obj
srf2obj $CORTEXDIR/rh.pial_roi.0009.srf > $CORTEXDIR/rh.InferiorTemporal.obj
srf2obj $CORTEXDIR/rh.pial_roi.0010.srf > $CORTEXDIR/rh.Isthmus.obj
srf2obj $CORTEXDIR/rh.pial_roi.0011.srf > $CORTEXDIR/rh.LateralOccipital.obj
srf2obj $CORTEXDIR/rh.pial_roi.0012.srf > $CORTEXDIR/rh.OrbitalFrontal.obj
srf2obj $CORTEXDIR/rh.pial_roi.0013.srf > $CORTEXDIR/rh.Lingual.obj
srf2obj $CORTEXDIR/rh.pial_roi.0014.srf > $CORTEXDIR/rh.MedialOrbitalFrontal.obj
srf2obj $CORTEXDIR/rh.pial_roi.0015.srf > $CORTEXDIR/rh.MiddleTemporal.obj
srf2obj $CORTEXDIR/rh.pial_roi.0016.srf > $CORTEXDIR/rh.Parahippocampal.obj
srf2obj $CORTEXDIR/rh.pial_roi.0017.srf > $CORTEXDIR/rh.ParacentralLobule.obj
srf2obj $CORTEXDIR/rh.pial_roi.0018.srf > $CORTEXDIR/rh.InfFrontalParsOpercularis.obj
srf2obj $CORTEXDIR/rh.pial_roi.0019.srf > $CORTEXDIR/rh.InfFrontalParsOrbitalis.obj
srf2obj $CORTEXDIR/rh.pial_roi.0020.srf > $CORTEXDIR/rh.InfFrontalParsTriangularis.obj
srf2obj $CORTEXDIR/rh.pial_roi.0021.srf > $CORTEXDIR/rh.Pericalcarine.obj
srf2obj $CORTEXDIR/rh.pial_roi.0022.srf > $CORTEXDIR/rh.Post-Central.obj
srf2obj $CORTEXDIR/rh.pial_roi.0023.srf > $CORTEXDIR/rh.PosteriorCingulate.obj
srf2obj $CORTEXDIR/rh.pial_roi.0024.srf > $CORTEXDIR/rh.Pre-Central.obj
srf2obj $CORTEXDIR/rh.pial_roi.0025.srf > $CORTEXDIR/rh.PreCuneus.obj
srf2obj $CORTEXDIR/rh.pial_roi.0026.srf > $CORTEXDIR/rh.RACingulate.obj
srf2obj $CORTEXDIR/rh.pial_roi.0027.srf > $CORTEXDIR/rh.MiddleFrontalRostral.obj
srf2obj $CORTEXDIR/rh.pial_roi.0028.srf > $CORTEXDIR/rh.SuperiorFrontal.obj
srf2obj $CORTEXDIR/rh.pial_roi.0029.srf > $CORTEXDIR/rh.SuperiorParietal.obj
srf2obj $CORTEXDIR/rh.pial_roi.0030.srf > $CORTEXDIR/rh.SuperiorTemporal.obj
srf2obj $CORTEXDIR/rh.pial_roi.0031.srf > $CORTEXDIR/rh.Supra-Marginal.obj
srf2obj $CORTEXDIR/rh.pial_roi.0032.srf > $CORTEXDIR/rh.FrontalPole.obj
srf2obj $CORTEXDIR/rh.pial_roi.0033.srf > $CORTEXDIR/rh.TemporalPole.obj
srf2obj $CORTEXDIR/rh.pial_roi.0034.srf > $CORTEXDIR/rh.TransverseTemporal.obj
srf2obj $CORTEXDIR/rh.pial_roi.0035.srf > $CORTEXDIR/rh.Insula.obj
