import os
import filecmp
import numpy as np
import shutil
import build_prior_stim_locations as bp

CH2 = "~sudas/DARPA/ch2.nii.gz"
RDIR = "~sudas/bin/localization/template_to_NickOasis"
faffine = RDIR + "/ch22t0GenericAffine.mat"
fwarp = RDIR + "/ch22t1Warp.nii.gz"
finversewarp = RDIR + "/ch22t1InverseWarp.nii.gz"

def setup_directories(subject):
    basedir = "/home1/zduey/brain_viz/test_data/{}/".format(subject)
    workdir= basedir + "prior_stim/"
    baselinedir = basedir + "prior_stim_baseline/"
    tdir = "/home1/zduey/brain_viz/test_data/{}/imaging/autoloc/"
    return basedir, workdir, baselinedir, tdir

def cleanup(subject):
    basedir, workdir, baselinedir, tdir = setup_directories(subject)
    if os.path.exists(workdir):
        shutil.rmtree(workdir)
    return

def test_initialize():
    subject = "R1291M_1"
    cleanup(subject)
    basedir, workdir, baselinedir, tdir = setup_directories(subject)
    bp.initialize(subject, workdir, tdir)
    assert os.path.exists(workdir + subject + "_stimdeltarec_mni.nii.gz")
    assert os.path.exists(workdir + subject + "_stimdeltarec_target_T1.nii.gz")
    assert os.path.exists(workdir + subject + "_stimdeltarec_target_CT.nii.gz")

    return

def test_get_orig_mat():
    subject = "R1291M_1"
    basedir, workdir, baselinedir, tdir = setup_directories(subject)

    Norig_matrix = bp.get_orig_mat(basedir, "vox2ras")
    assert np.shape(Norig_matrix) == (4,4)

    Norig_comparison_matrix = np.loadtxt(baselinedir + "Norig.txt")
    assert np.allclose(Norig_matrix, Norig_comparison_matrix)

    Torig_matrix = bp.get_orig_mat(basedir, "vox2ras-tkr")
    assert np.shape(Torig_matrix) == (4,4)

    return

def test_generate_generic_RAS_file():
    subject = "R1291M_1"
    basedir, workdir, baselinedir, tdir = setup_directories(subject)
    bp.generate_generic_RAS_file(tdir, workdir, subject)

    outfile = subject + '_T01_CT_to_T00_mprageANTs0GenericAffine_RAS_itk.txt'
    assert os.path.exists(workdir + outfile)
    assert filecmp.cmp(workdir + outfile, baselinedir + outfile, shallow=False)

    return

def test_load_mni_coords():
    subject = "R1291M_1"
    basedir, workdir, baselinedir, tdir = setup_directories(subject)
    mni_df = bp.load_mni_coords(subject, tdir)
    assert len(mni_df) > 0
    return

def test_save_mni_coords():
    subject = "R1291M_1"
    stim_subject = "R1001P"
    basedir, workdir, baselinedir, tdir = setup_directories(subject)
    mni_df = bp.load_mni_coords(stim_subject, tdir)
    assert len(mni_df) > 0

    bipolar_contact = "LDA3 - LDA4"
    bp.save_mni_mid_coordinates(workdir, stim_subject, mni_df, bipolar_contact)

    outfile = stim_subject + "_electrode_coordinates_mni_mid.csv"
    assert os.path.exists(workdir + outfile)
    assert filecmp.cmp(workdir + outfile, baselinedir + outfile, shallow=False)

    return

def test_CT_transform():
    subject = "R1291M_1"
    stim_subject = "R1001P"
    basedir, workdir, baselinedir, tdir = setup_directories(subject)
    bp.CT_transform(tdir, workdir, fwarp, faffine, subject, stim_subject)

    outfile = subject + '_from_' + stim_subject + '_electrode_coordinates_mni_mid_tsub_CT.csv'
    assert os.path.exists(workdir + outfile)
    assert filecmp.cmp(workdir + outfile, baselinedir + outfile, shallow=False)

    return

def test_T1_transform():
    subject = "R1291M_1"
    stim_subject = "R1001P"
    basedir, workdir, baselinedir, tdir = setup_directories(subject)
    bp.T1_transform(tdir, workdir, fwarp, faffine, subject, stim_subject)

    outfile = subject + '_from_' + stim_subject +  '_electrode_coordinates_mni_mid_tsub_T1.csv'
    assert os.path.exists(workdir + outfile)
    assert filecmp.cmp(workdir + outfile, baselinedir + outfile, shallow=False)

    return

def test_get_fs_vector():
    subject = "R1291M_1"
    stim_subject = "R1001P"
    basedir, workdir, baselinedir, tdir = setup_directories(subject)

    Norig = bp.get_orig_mat(basedir, "vox2ras")
    Torig = bp.get_orig_mat(basedir, "vox2ras-tkr")

    fs_vector = bp.get_fs_vector(workdir, subject, stim_subject, Norig, Torig)

    assert np.allclose(fs_vector, np.array([-23.982420, 3.400870, -25.032093, 1]), atol=1e-2)

    return

def test_generate_prior_stim_locations():
    return
