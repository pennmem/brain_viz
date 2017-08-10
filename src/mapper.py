import io
import os
import sys
import shutil
import logging
import datetime
import constants
import subprocess
import numpy as np
import pandas as pd

from deltarec import build_prior_stim_results_table


now = datetime.datetime.now()
now = now.strftime("%Y_%m_%d_%H_%M_%S")
logging.basicConfig(filename='../logs/contact_mapper_%s.log' % now,
                    format='[%(levelname)s]: %(asctime)s -- %(message)s',
                    level=logging.INFO,
                    datefmt='%m/%d/%Y %I:%M:%S %p')


def build_prior_stim_location_mapping(subject, basedir, imagedir):
    if os.path.exists(imagedir) == False:
        msg = "autloc folder for {} does not exist".format(subject)
        logging.error(msg)
        raise FileNotFoundError(msg)

    logging.info("Initializing prior stim location folder")
    workdir = basedir + "/prior_stim/"
    initialize(subject, workdir, imagedir)

    logging.info("Building subject-specific files")
    Norig = get_orig_mat(basedir, "vox2ras")
    Torig = get_orig_mat(basedir, "vox2ras-tkr")
    generate_generic_RAS_file(imagedir, workdir, subject)

    logging.info("Getting prior stim results")
    prior_stim_df = build_prior_stim_results_table()
    prior_stim_df["fs_x"] = np.nan
    prior_stim_df["fs_y"] = np.nan
    prior_stim_df["fs_z"] = np.nan

    subjects = prior_stim_df["subject_id"].unique()
    for stim_subject in subjects:
        logging.info("Converting coordinates from stim subject {} to subject {}".format(stim_subject, subject))
        mni_df = load_mni_coords(stim_subject)
        if mni_df is None:
            continue # error handled in function

        stimulated_bipolars = prior_stim_df[prior_stim_df["subject_id"] == stim_subject]["contact_name"].unique()
        for bipolar_contact in stimulated_bipolars:
            ret_code = save_mni_mid_coordinates(workdir, stim_subject,
                                                mni_df, bipolar_contact)
            if ret_code == -1:
                continue
            T1_transform(imagedir, workdir, constants.WARP_FILE,
                         constants.GENERIC_AFFINE_TRANSFORM_FILE, subject,
                         stim_subject)
            fs_coords = get_fs_vector(workdir, subject, stim_subject, Norig, Torig)

            prior_stim_df.loc[((prior_stim_df["subject_id"] == stim_subject) &
                               (prior_stim_df["contact_name"] == bipolar_contact)),
                              "fs_x"] = fs_coords[0]

            prior_stim_df.loc[((prior_stim_df["subject_id"] == stim_subject) &
                               (prior_stim_df["contact_name"] == bipolar_contact)),
                              "fs_y"] = fs_coords[1]

            prior_stim_df.loc[((prior_stim_df["subject_id"] == stim_subject) &
                               (prior_stim_df["contact_name"] == bipolar_contact)),
                              "fs_z"] = fs_coords[2]

    # Final cleanup of the file
    prior_stim_df = prior_stim_df.dropna(axis=0, how='any')
    del prior_stim_df['x']
    del prior_stim_df['y']
    del prior_stim_df['z']
    prior_stim_df.to_csv(workdir + subject + "_allcords.csv", index=False)
    return


def initialize(subject, workdir, imagedir):
    if os.path.exists(workdir) == False:
        os.mkdir(workdir)

    subprocess.run("c3d " + constants.CH2 + " -scale 0 -o " + workdir + subject +\
                   "_stimdeltarec_mni.nii.gz",
                   shell=True)

    subprocess.run("c3d " + imagedir + "T00_" + subject +\
                   "_mprage.nii.gz -scale 0 -o " + workdir + subject +\
                   "_stimdeltarec_target_T1.nii.gz",
                   shell=True)

    subprocess.run("c3d " + imagedir + "T01_" + subject +\
                   "_CT.nii.gz  -scale 0 -o " + workdir + subject +\
                   "_stimdeltarec_target_CT.nii.gz",
                   shell=True)
    return


def get_orig_mat(basedir, mri_info_command):
    result = subprocess.run('mri_info --' + mri_info_command + ' ' +\
                            basedir + "/mri/orig.mgz",
                            stdout=subprocess.PIPE,
                            shell=True)
    output = io.BytesIO(result.stdout)
    matrix = np.loadtxt(output)
    return matrix


def generate_generic_RAS_file(imagedir, workdir, subject):
    imagedir = imagedir
    subprocess.run('c3d_affine_tool ' + imagedir +\
                   '/T01_CT_to_T00_mprageANTs0GenericAffine_RAS.mat -oitk ' +\
                   workdir + subject +\
                   '_T01_CT_to_T00_mprageANTs0GenericAffine_RAS_itk.txt',
                   shell=True)
    return

def load_mni_coords(subject):
    mni_file = "/data10/RAM/subjects/{}/imaging/autoloc/electrodelabels_and_coordinates_mni_mid.csv".format(subject)
    # Some subjects do not have this file built. Gracefully skip them for now
    if os.path.exists(mni_file) == False:
      logging.error("No mni coordinate file for subject {}".format(subject))
      return

    try:
        mni_df = pd.read_csv(mni_file, header=None)
    except Exception as e:
        logging.exception("Error loading mni coordinate file for subject {}".format(subject), exc_info=e)
        return

    mni_df["subject_id"] = subject

    if len(mni_df.columns) != 11:
        logging.error("Invalid mni coordinate file for subject: {}".format(subject))
        return

    mni_df = mni_df.rename(columns={0:'contact_name',
                                    1:'?',
                                    2:'x',
                                    3:'y',
                                    4:'z',
                                    5:'t',
                                    6:'label',
                                    7:'mass',
                                    8:'volume',
                                    9:'count'})
    del mni_df["?"]
    mni_df = mni_df[["subject_id", "contact_name", "x", "y", "z", "t",
                     "label", "mass", "volume", "count"]]

    return mni_df

def save_mni_mid_coordinates(workdir, subject, mni_df, bipolar_contact):
    single_contact_df = mni_df[mni_df["contact_name"] == bipolar_contact]
    if len(single_contact_df) == 0:
        logging.error("Contact {} not found for subject {}".format(bipolar_contact, subject))
        return -1
    single_contact_df["x"] *= -1
    single_contact_df["y"] *= -1

    output_df = single_contact_df[["x","y","z","t","label","mass","volume","count"]]
    output_df.to_csv(workdir + subject + "_electrode_coordinates_mni_mid.csv", index=False)

    return


def CT_transform(imagedir, workdir, warp_file, affine_transform_file, subject, stim_subject):
    subprocess.run('~sudas/bin/ants/antsApplyTransformsToPoints -d 3 -i ' + \
                   workdir + stim_subject + '_electrode_coordinates_mni_mid.csv -o ' + \
                   workdir + subject + '_from_' + stim_subject +\
                   '_electrode_coordinates_mni_mid_tsub_CT.csv -t ' + warp_file +\
                   ' -t ' + affine_transform_file + ' -t ' + imagedir +\
                   '/T00/thickness/' + subject + 'TemplateToSubject1Warp.nii.gz -t ' +\
                   imagedir + '/T00/thickness/' + subject + 'TemplateToSubject0GenericAffine.mat -t ' + \
                   workdir + subject + '_T01_CT_to_T00_mprageANTs0GenericAffine_RAS_itk.txt',
                   shell=True)
    return

def T1_transform(imagedir, workdir, warp_file, affine_transform_file, subject, stim_subject):
    subprocess.run('~sudas/bin/ants/antsApplyTransformsToPoints -d 3 -i ' + \
                   workdir + stim_subject + '_electrode_coordinates_mni_mid.csv -o ' + \
                   workdir + subject + '_from_' + stim_subject +\
                   '_electrode_coordinates_mni_mid_tsub_T1.csv -t ' + warp_file +\
                   ' -t ' + affine_transform_file + ' -t ' + imagedir +\
                   '/T00/thickness/' + subject + 'TemplateToSubject1Warp.nii.gz -t ' +\
                   imagedir + '/T00/thickness/' + subject + 'TemplateToSubject0GenericAffine.mat',
                   shell=True)

    return

def get_fs_vector(workdir, subject, stim_subject, Norig, Torig):
    coords = np.loadtxt(workdir + subject + "_from_" + stim_subject +\
                        "_electrode_coordinates_mni_mid_tsub_T1.csv",
                        skiprows=1,
                        delimiter=',')
    coords = coords[:3]
    nifti_to_itk = np.array([-1,-1,1])
    coords = coords * nifti_to_itk
    coords = np.append(coords, [1])
    fscoords = np.dot(np.dot(Torig, np.linalg.inv(Norig)), coords)
    return fscoords
