import io
import os
import sys
import shutil
import logging
import datetime
import subprocess
import numpy as np
import pandas as pd

from src.deltarec import build_prior_stim_results_table


# Module level globals. 
CH2 = "~sudas/DARPA/ch2.nii.gz"
RDIR = "~sudas/bin/localization/template_to_NickOasis"
GENERIC_AFFINE_TRANSFORM_FILE = RDIR + "/ch22t0GenericAffine.mat"
WARP_FILE = RDIR + "/ch22t1Warp.nii.gz"

# List of subjects to ignore for prior stim locations
SUBJECT_BLACKLIST = ["R1027J"]


def build_prior_stim_location_mapping(subject, basedir, imagedir):
    """ Converts prior stim locations into a given subject's space

    This function is the entrypoint to the script and calls the helper
    functions defined in this module.

    Parameters
    ----------
    subject: str
        Subject identifyer indicating the target subject for the mapping

    basedir: str
        Filepath of where the

    imagedir: str
        Filepath where data based on MRI/CT imaging can be found

    """

    start_logging()
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
        if stim_subject in SUBJECT_BLACKLIST:
            logging.info("Skipping {} because they are blacklisted. Updated constants if this is undesired.".format(subject))
            continue

        logging.info("Converting coordinates from stim subject {} to subject {}".format(stim_subject, subject))
        stimulated_bipolars = prior_stim_df[prior_stim_df["subject_id"] == stim_subject]["contact_name"].unique()
        for bipolar_contact in stimulated_bipolars:
            montage_num = prior_stim_df[(prior_stim_df["subject_id"] == stim_subject) &
                                        (prior_stim_df["contact_name"] == bipolar_contact)]["montage_num"].values[0]

            # Be sure to load the correct file depending on the montage used
            updated_subject = stim_subject
            if montage_num != 0:
                updated_subject = "_".join([stim_subject, str(int(montage_num))])
            mni_df = load_mni_coords(updated_subject)
            if mni_df is None:
                continue # error handled in function

            ret_code = save_mni_mid_coordinates(workdir, stim_subject,
                                                mni_df, bipolar_contact)
            if ret_code == -1:
                continue # skip if issues were encountered
            T1_transform(imagedir, workdir, WARP_FILE,
                         GENERIC_AFFINE_TRANSFORM_FILE, subject,
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
    del prior_stim_df['montage_num']
    prior_stim_df.to_csv(workdir + subject + "_allcords.csv", index=False)
    return


def start_logging():
    """ Create a log file for debugging purposes """
    now = datetime.datetime.now()
    now = now.strftime("%Y_%m_%d_%H_%M_%S")
    basedir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    logging.basicConfig(filename=(basedir + "/logs/contact_mapper_%s.log" % now),
                        format='[%(levelname)s]: %(asctime)s -- %(message)s',
                        level=logging.INFO,
                        datefmt='%m/%d/%Y %I:%M:%S %p')
    return

def initialize(subject, workdir, imagedir):
    if os.path.exists(workdir) == False:
        os.mkdir(workdir)

    subprocess.run("c3d " + CH2 + " -scale 0 -o " + workdir + subject +\
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
    """ Load mni coordinates for bipolar pairs

    If a file cannot be found for the given subject and the subjecet has
    multiple montages, a previous montage will be loaded. For example, if
    the file does not exist for R1291M_1, then the file for R1291M will be
    loaded. If an error is encountered while attempting to load the file,
    an error will be logged. If the file is improperly formatted, an error
    will also be logged.

    """
    mni_loc = "/data10/RAM/subjects/{}/imaging/autoloc/electrodelabels_and_coordinates_mni_mid.csv"
    mni_file = mni_loc.format(subject)
    # Some subjects do not have this file built. Gracefully skip them for now
    if os.path.exists(mni_file) == False:
        logging.error("No mni coordinate file for subject {}".format(subject))

      # Try loading original file if a different montage is being used
        original_subject = get_original_subject(subject)
        if ((original_subject == subject) or
            (os.path.exists(mni_loc.format(original_subject)) == False)):
            return
        else:
            mni_file = mni_loc.format(original_subject)
            logging.info("Reverting to original montage mni file for subject %s" % original_subject)
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

    # Convert contact names to uppercase for consistency
    mni_df["contact_name"] = mni_df["contact_name"].apply(lambda x: x.upper())

    mni_df = mni_df[["subject_id", "contact_name", "x", "y", "z", "t",
                     "label", "mass", "volume", "count"]]

    return mni_df

def get_original_subject(subject):
    orig_subject = subject
    if subject.find("_") != -1:
        orig_subject = subject[:subject.find("_")]
    return orig_subject


def load_monopolar_mni_coords(subject):
    mni_file = "/data10/RAM/subjects/{}/imaging/autoloc/electrodenames_coordinates_mni.csv".format(subject)
    # Some subjects do not have this file built. Gracefully skip them for now
    if os.path.exists(mni_file) == False:
      logging.error("No monopolar mni coordinate file for subject {}".format(subject))
      return

    try:
        mni_df = pd.read_csv(mni_file, header=None)
    except Exception as e:
        logging.exception("Error loading monopolar mni coordinate file for subject {}".format(subject), exc_info=e)
        return

    mni_df["subject_id"] = subject

    if len(mni_df.columns) != 10:
        logging.error("Invalid number of columns for monopolar mni coordinate file for subject: {}".format(subject))
        return

    mni_df = mni_df.rename(columns={0:'contact_name',
                                    1:'x',
                                    2:'y',
                                    3:'z',
                                    4:'t',
                                    5:'label',
                                    6:'mass',
                                    7:'volume',
                                    8:'count'})

    # Convert contact names to uppercase for consistency
    mni_df["contact_name"] = mni_df["contact_name"].apply(lambda x: x.upper())

    mni_df = mni_df[["subject_id", "contact_name", "x", "y", "z", "t",
                     "label", "mass", "volume", "count"]]

    return mni_df


def save_mni_mid_coordinates(workdir, subject, mni_df, bipolar_contact):
    single_contact_df = mni_df[mni_df["contact_name"] == bipolar_contact]
    if len(single_contact_df) == 0:
        single_contact_df = build_custom_bipolar(subject, mni_df, bipolar_contact)
        # Break here if unable to track down the contact
        if single_contact_df is None:
            return -1

    single_contact_df["x"] *= -1
    single_contact_df["y"] *= -1

    output_df = single_contact_df[["x","y","z","t","label","mass","volume","count"]]
    output_df.to_csv(workdir + subject + "_electrode_coordinates_mni_mid.csv", index=False)

    return


def build_custom_bipolar(subject, mni_df, bipolar_contact):
    """ For non-consecutive contacts, create the mni_mid coordinates manually """
    monopolar_mni_df = load_monopolar_mni_coords(subject)
    contact_tokens = bipolar_contact.split('-')
    contact1 = contact_tokens[0].strip()
    contact2 = contact_tokens[1].strip()

    subset_df = monopolar_mni_df[monopolar_mni_df["contact_name"].isin([contact1, contact2])]
    if len(subset_df) != 2:
        logging.error("Unable to find monopolars for subject %s, contact %s" % (subject, bipolar_contact))
        return None

    x_coord = subset_df["x"].sum() / 2.0
    y_coord = subset_df["y"].sum() / 2.0
    z_coord = subset_df["z"].sum() / 2.0
    volume = subset_df["volume"].values[0]

    # Build single-row dataframe
    single_contact_df = pd.DataFrame(data={
        "x": [x_coord],
        "y": [y_coord],
        "z": [z_coord],
        "t": [0],
        "label": [0],
        "mass": [0],
        "volume": [volume],
        "count": [1]
    }, columns=["x","y", "z", "t", "label", "mass", "volume", "count"])

    return single_contact_df

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
