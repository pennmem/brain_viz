import os
import shutil
import subprocess
import functools
from pkg_resources import resource_filename
from typing import Optional

from cml_pipelines import make_task
from cml_pipelines.paths import FilePaths
from brainviewer.coords4blender import save_coords_for_blender

datafile = functools.partial(resource_filename, 'brainviewer.templates')
bin_files = functools.partial(resource_filename, 'brainviewer.bin')


def generate_data_for_3d_brain_viz(subject_id: str, localization: int,
                                   paths: Optional[FilePaths] = None,
                                   force_rerun: Optional[bool] = False,
                                   blender: Optional[bool] = False):
    """ Generate the underlying data necessary to constract a 3D brain view

    Parameters
    ----------
    subject_id: str
        Subject identifier
    localization: int
        Localization to use for building the brain viewer

    Keyword Arguments
    -----------------
     paths: `cml_pipelines.paths.FilePaths`
        Container for passing around a group of related file paths
    force_rerun: bool, default False
        If true, then forefully re-run all tasks
    blender: bool, default False
        If true, build the Blender-based 3D standalone file

    """
    if paths is None:
        paths = setup_paths(subject_id)

    setup_status = make_task(setup, subject_id, paths, force_rerun=force_rerun)
    electrode_coord_path = save_coords_for_blender(subject_id, localization,
                                                   paths.tal,
                                                   rootdir=paths.root)
    fs_files = freesurfer_to_wavefront(paths, setup_status)
    hcp_files = avg_hcp_to_subject(subject_id, localization, paths,
                                   setup_status)

    if blender:
        # Complete the blender-related tasks
        setup_standalone_blender_scene(paths)
        gen_blender_scene()

    return fs_files.compute()


def setup_paths(subject_id: str, localization: str):
    """
        Helper function to produce a `cml_pipelines.paths.FilePaths` object
        with production paths

    Parameters
    ----------
    subject_id: str
        ID of subject to generate the brain visualization

    localization: str
        Localization number as a string to use. Typically this is 0.

    """
    subject_localization = _combine_subject_localization(subject_id,
                                                         localization)

    # Common paths used throughout the pipeline
    BASE = "/data10/eeg/freesurfer/subjects/{}".format(subject_localization)
    CORTEX = "/data10/eeg/freesurfer/subjects/{}/surf/roi".format(subject_localization)
    CONTACT = "/data10/RAM/subjects/{}/tal/coords".format(subject_localization)
    TAL = "/data10/RAM/subjects/{}/tal".format(subject_localization)
    IMAGE = "/data10/RAM/subjects/{}/imaging/autoloc/".format(subject_localization)
    OUTPUT = "/reports/r1/subjects/{}/reports/iEEG_surface".format(subject_localization)

    RHINO_ROOT = "/"
    paths = FilePaths(RHINO_ROOT, base=BASE, cortex=CORTEX, contact=CONTACT,
                      tal=TAL, image=IMAGE, output=OUTPUT)
    return paths


def setup(subject_id: str, localization: int, paths: FilePaths) -> bool:
    """
        Set up directory structure, move starter files, and check for the
        existence of other files that the full pipeline depends on.
        Short-circuit if any dependencies are unmet

    Parameters
    ----------
    subject_id: str
        ID of subject
    localization: int
        Localization number to use
    paths: `cml_pipelines.paths.FilePaths` container for various file paths

    Returns
    -------
    setup_status: bool
        True if task completed successfully

    """
    if os.path.exists(paths.cortex) is False:
        os.mkdir(paths.cortex)

    subject_localization = _combine_subject_localization(subject_id,
                                                         localization)

    shutil.copy(os.path.join(paths.base, "surf/lh.pial"), paths.cortex)
    shutil.copy(os.path.join(paths.base, "surf/rh.pial"), paths.cortex)
    shutil.copy(os.path.join(paths.base, "label/lh.aparc.annot"), paths.cortex)
    shutil.copy(os.path.join(paths.base, "label/rh.aparc.annot"), paths.cortex)

    # These three files need to exist in order to complete downstream processing
    assert os.path.exists(
        os.path.join(paths.image,
                     "T00/thickness/{}TemplateToSubject0GenericAffine.mat".format(subject_localization)))
    assert os.path.exists(
        os.path.join(paths.image,
                     "T00/thickness/{}TemplateToSubject1Warp.nii.gz".format(subject_localization)))
    assert os.path.exists(
        os.path.join(paths.image,
                     "T01_CT_to_T00_mprageANTs0GenericAffine_RAS.mat"))

    return True


def setup_standalone_blender_scene(paths: FilePaths, force_rerun=False):
    """ Copies the Blender template files to the final destination """
    template_dir = datafile("iEEG_surface_template/")
    if os.path.exists(paths.output):
        if not force_rerun:
            raise RuntimeError("Blender scene already exists. Use force rerun option to overwrite")
        shutil.rmtree(paths.output)

    shutil.copytree(template_dir, paths.output)
    return


def freesurfer_to_wavefront(paths: FilePaths, setup_status: bool) -> FilePaths:
    """ Convert Freesurfer brain piece models to wavefront format """
    subprocess.run("mris_convert " +
                   os.path.join(paths.cortex, "lh.pial ") +
                   os.path.join(paths.cortex, "lh.pial.asc"),
                   shell=True,
                   check=True)
    subprocess.run("mris_convert " +
                   os.path.join(paths.cortex, "rh.pial ") +
                   os.path.join(paths.cortex, "rh.pial.asc"),
                   shell=True,
                   check=True)
    shutil.move(os.path.join(paths.cortex, "lh.pial.asc"),
                os.path.join(paths.cortex, "lh.pial.srf"))
    shutil.move(os.path.join(paths.cortex, "rh.pial.asc"),
                os.path.join(paths.cortex, "rh.pial.srf"))

    subprocess.run(" ".join([bin_files("srf2obj"),
                             os.path.join(paths.cortex, "lh.pial.srf "),
                             ">",
                             os.path.join(paths.cortex, "lh.pial.obj")]),
                   shell=True,
                   check=True)

    subprocess.run(" ".join([bin_files("srf2obj"),
                             os.path.join(paths.cortex, "rh.pial.srf"),
                             ">",
                             os.path.join(paths.cortex, "rh.pial.obj")]),
                   shell=True,
                   check=True)

    exp_files = FilePaths(root="/",
                          rh_obj=os.path.join(paths.cortex, "rh.pial.obj"),
                          lh_obj=os.path.join(paths.cortex, "lh.pial.obj"))

    return exp_files


def avg_hcp_to_subject(subject_id: str, localization: int, paths: FilePaths,
                       setup_status: bool) -> FilePaths:
    """ Convert HCP atlas annotation file into subject-specific space

    Parameters
    ----------
    subject_id: str
        ID of subject
    localization: int
        Localization number to use
    paths: :class:`cml_pipelines.paths.FilePaths` container for various file paths
    setup_status: bool
        True if the setup task completed successfully. The presence of this
        boolean in the function signature is used to notify the pipeline
        framework that this task depends on the result of the setup task

    Returns
    -------
    setup_status: bool
        True if task completed successfully

    """

    subject_localization = _combine_subject_localization(subject_id,
                                                         localization)

    subprocess.run(" ".join(["mri_surf2surf", "--srcsubject fsaverage_temp",
                             "--sval-annot HCP-MMP1.annot",
                             "--trgsubject {}".format(subject_localization),
                             "--trgsurfval HCP-MMP1.annot",
                             "--hemi lh"]),
                   shell=True,
                   check=True)

    subprocess.run(" ".join(["mri_surf2surf",
                             "--srcsubject fsaverage_temp",
                             "--sval-annot HCP-MMP1.annot",
                             "--trgsubject {}".format(subject_localization),
                             "--trgsurfval HCP-MMP1.annot",
                             "--hemi rh"]),
                   shell=True,
                   check=True)

    shutil.copy(os.path.join(paths.base, "label/lh.HCP-MMP1.annot"),
                paths.cortex)
    shutil.copy(os.path.join(paths.base, "label/rh.HCP-MMP1.annot"),
                paths.cortex)

    exp_files = FilePaths(root="/",
                          rh_hcp=os.path.join(paths.cortex, "rh.HCP-MMP1.annot"),
                          lh_hcp=os.path.join(paths.cortex, "lh.HCP-MMP1.annot"))

    return exp_files


def gen_mapped_prior_stim_sites(subject_id, paths, setup_status):
    return


def split_cortical_surface(subject_id: str, paths: FilePaths,
                           fs_to_wav_status: bool):
    return


def split_hcp_surface(subject_id: str, localization: int,  paths: FilePaths,
                      hcp_map_status: bool, fs_to_wav_status: bool):
    """
        Creates individual wavefront object for each region based on the
        Human Connectome Project (HCP) atlas

    Parameters
    ----------
    subject_id: str
        ID of the subject
    localization: int
        Localization number
    paths: :class:`cml_pipelines.paths.FilePaths` container for common paths
    hcp_map_status: bool
        Result of the hcp
    fs_to_wav_status: bool
        Result of the freesurfer to wavefront conversion step

    Returns
    -------

    """
    return True


def gen_blender_scene():
    return


def _combine_subject_localization(subject_id: str, localization: int):
    """ Helper function to combine subject ID and localization number """

    subject_localization = subject_id
    localization = str(localization)
    if localization != '0':
        subject_localization = "_".join([subject_id, localization])

    return subject_localization

