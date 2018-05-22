import os
import filecmp
import numpy as np
import shutil

import brainviewer.mapper as mapper


def setup_directories(subject):
    basedir = os.path.dirname(os.path.dirname(os.path.realpath(__file__))) + "/test_data/{}/".format(subject)
    workdir= basedir + "prior_stim/"
    baselinedir = basedir + "prior_stim_baseline/"
    imagedir = basedir + "imaging/autoloc/"
    return basedir, workdir, baselinedir, imagedir

def cleanup(subject):
    basedir, workdir, baselinedir, imagedir = setup_directories(subject)
    if os.path.exists(workdir):
        shutil.rmtree(workdir)
    return

def test_initialize():
    subject = "R1291M_1"
    cleanup(subject)
    basedir, workdir, baselinedir, imagedir = setup_directories(subject)
    mapper.initialize(subject, workdir, imagedir)
    assert os.path.exists(workdir + subject + "_stimdeltarec_mni.nii.gz")
    assert os.path.exists(workdir + subject + "_stimdeltarec_target_T1.nii.gz")
    assert os.path.exists(workdir + subject + "_stimdeltarec_target_CT.nii.gz")

    return

def test_get_orig_mat():
    subject = "R1291M_1"
    basedir, workdir, baselinedir, imagedir = setup_directories(subject)

    Norig_matrix = mapper.get_orig_mat(basedir, "vox2ras")
    assert np.shape(Norig_matrix) == (4,4)

    Norig_comparison_matrix = np.loadtxt(baselinedir + "Norig.txt")
    assert np.allclose(Norig_matrix, Norig_comparison_matrix)

    Torig_matrix = mapper.get_orig_mat(basedir, "vox2ras-tkr")
    assert np.shape(Torig_matrix) == (4,4)

    return

def test_generate_generic_RAS_file():
    subject = "R1291M_1"
    basedir, workdir, baselinedir, imagedir = setup_directories(subject)
    mapper.generate_generic_RAS_file(imagedir, workdir, subject)

    outfile = subject + '_T01_CT_to_T00_mprageANTs0GenericAffine_RAS_itk.txt'
    assert os.path.exists(workdir + outfile)
    assert filecmp.cmp(workdir + outfile, baselinedir + outfile, shallow=False)

    return

def test_load_orig_mni_coords():
    subject = "R1291M_1"
    basedir, workdir, baselinedir, imagedir = setup_directories(subject)
    mni_df = mapper.load_orig_mni_coords(subject)
    assert len(mni_df) > 0
    return

def test_load_adj_mni_coords():
    subject = "R1216E"
    basedir, workdir, baselinedir, imagedir = setup_directories(subject)
    mni_df = mapper.load_adj_mni_coords(subject)
    assert len(mni_df) > 0

    subject = "R1027J"
    basedir, workdir, baselinedir, imagedir = setup_directories(subject)
    mni_df = mapper.load_adj_mni_coords(subject)
    assert (mni_df is None) # no adjusted coordinates (depths only)

    return

def test_get_mni_coords():
    # R1291M_1 does not have the correct updated mni file, so use a subject
    # who does have one
    subject = "R1216E"
    basedir, workdir, baselinedir, imagedir = setup_directories(subject)
    mni_df = mapper.get_mni_coords(subject)
    assert len(mni_df) > 0

    # Unajusted coordinates only. Should still return data
    subject = "R1027J"
    basedir, workdir, baselinedir, imagedir = setup_directories(subject)
    mni_df = mapper.get_mni_coords(subject)
    assert len(mni_df) > 0

    return

def test_save_mni_coords():
    subject = "R1291M_1"
    stim_subject = "R1001P"
    basedir, workdir, baselinedir, imagedir = setup_directories(subject)
    mni_df = mapper.get_mni_coords(stim_subject)
    assert len(mni_df) > 0

    bipolar_contact = "LDA3-LDA4"
    mapper.save_mni_mid_coordinates(workdir, stim_subject, mni_df, bipolar_contact)

    outfile = stim_subject + "_electrode_coordinates_mni_mid.csv"
    assert os.path.exists(workdir + outfile)
    return

def test_save_mni_coords_custom_bipolar():
    subject = "R1291M_1"
    stim_subject = "R1042M"
    basedir, workdir, baselinedir, imagedir = setup_directories(subject)
    mni_df = mapper.get_mni_coords(stim_subject)
    assert len(mni_df) > 0

    bipolar_contact = "RTG55-RTG63"
    mapper.save_mni_mid_coordinates(workdir, stim_subject, mni_df, bipolar_contact)

    outfile = stim_subject + "_electrode_coordinates_mni_mid.csv"
    assert os.path.exists(workdir + outfile)

    return


def test_CT_transform():
    subject = "R1291M_1"
    stim_subject = "R1001P"
    basedir, workdir, baselinedir, imagedir = setup_directories(subject)
    mapper.CT_transform(imagedir, workdir, mapper.WARP_FILE, mapper.GENERIC_AFFINE_TRANSFORM_FILE, subject, stim_subject)

    outfile = subject + '_from_' + stim_subject + '_electrode_coordinates_mni_mid_tsub_CT.csv'
    assert os.path.exists(workdir + outfile)

    return

def test_T1_transform():
    subject = "R1291M_1"
    stim_subject = "R1001P"
    basedir, workdir, baselinedir, imagedir = setup_directories(subject)
    mapper.T1_transform(imagedir, workdir, mapper.WARP_FILE, mapper.GENERIC_AFFINE_TRANSFORM_FILE, subject, stim_subject)

    outfile = subject + '_from_' + stim_subject +  '_electrode_coordinates_mni_mid_tsub_T1.csv'
    assert os.path.exists(workdir + outfile)

    return

def test_get_fs_vector():
    subject = "R1291M_1"
    stim_subject = "R1001P"
    basedir, workdir, baselinedir, imagedir = setup_directories(subject)

    Norig = mapper.get_orig_mat(basedir, "vox2ras")
    Torig = mapper.get_orig_mat(basedir, "vox2ras-tkr")

    fs_vector = mapper.get_fs_vector(workdir, subject, stim_subject, Norig, Torig)

    # Had to be adjusted now that we are using dysktra adjusted mni coordinates
    assert np.allclose(fs_vector, np.array([-24.277, 3.4594, -24.514, 1]), atol=1e-2)

    return

def test_build_prior_stim_location_mapping():
    """ Long-running test. Do not run every time. """
    subject = "R1291M_1"
    basedir, workdir, baselinedir, imagedir = setup_directories(subject)
    mapper.build_prior_stim_location_mapping(subject,
                                             basedir,
                                             "/data10/RAM/subjects/{}/imaging/autoloc/".format(subject))
    return
