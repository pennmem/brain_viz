import os
import glob
import shutil
import subprocess
import functools
from pkg_resources import resource_filename
from typing import Optional

from cml_pipelines import make_task
from cml_pipelines.paths import FilePaths
from brainviewer.coords4blender import save_coords_for_blender
from brainviewer.mapper import build_prior_stim_location_mapping
from brainviewer.deltarec import build_prior_stim_results_table

datafile = functools.partial(resource_filename, 'brainviewer.templates')
bin_files = functools.partial(resource_filename, 'brainviewer.bin')
code_files = functools.partial(resource_filename, 'brainviewer')


__all__ = ["setup_subject_directory", "setup_paths",
           "setup_standalone_blender_scene", "freesurfer_to_wavefront",
           "avg_hcp_to_subject", "gen_mapped_prior_stim_sites",
           "split_hcp_surface", "split_dk_surface", "gen_blender_scene",
           "save_coords_for_blender", "generate_subject_brain",
           "generate_average_brain"]


def generate_average_brain(paths: Optional[FilePaths] = None,
                           blender: Optional[bool] = False,
                           force_rerun: Optional[bool] = False):
    """
        Generate the underlying data necessary to create a 3D view for an
        average brain

    Parameters
    ----------
    paths: :class:`cml_pipelines.paths.FilePaths`
        File path container for paths needed by the pipeline
    blender: bool
        If True, generates standalone Blender files for the average brain
    force_rerun: bool
        If True, overwrites existing visualization if one exists
    """
    if paths is None:
        paths = setup_avg_paths()

    prior_stim_results_df = make_task(build_prior_stim_results_table).compute()
    prior_stim_results_df = prior_stim_results_df[
        prior_stim_results_df["deltarec"].isnull() == False]
    del prior_stim_results_df["montage_num"]  # not needed in this case

    stimfile = "".join([paths.output, "/", "prior_stim_locations.csv"])
    prior_stim_results_df.to_csv(stimfile, index=False)

    if blender:
        blender_setup_status = make_task(setup_standalone_blender_scene,
                                         paths,
                                         avg=True,
                                         force_rerun=force_rerun).compute()

        # run subprocess to generate the blender scene for average brain
        subprocess.run(["/usr/global/blender-2.78c-linux-glibc219-x86_64/blender",
                        "-b",
                        datafile("iEEG_surface_template/empty.blend"),
                        "-b",
                        "--python",
                        code_files("create_scene.py"),
                        "--",
                        paths.avg_roi,
                        paths.output,
                        stimfile],
                       check=True)


def generate_subject_brain(subject_id: str, localization: str,
                           paths: Optional[FilePaths] = None,
                           force_rerun: Optional[bool] = False,
                           blender: Optional[bool] = False):
    """ Generate the underlying data necessary to construct a 3D brain view
        specific to a particular subject

    Parameters
    ----------
    subject_id: str
        Subject identifier
    localization: str
        Localization to use for building the brain viewer
    paths: `cml_pipelines.paths.FilePaths`
        Container for various file paths
    force_rerun: bool
        If True, cached results and previously-generated files are ignored so
        that the brain visualization can be rebuilt
    blender: bool
        If True, the blender version of the 3D brain visualization is built

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
        paths = setup_paths(subject_id, localization)

    setup_status = make_task(setup_subject_directory, subject_id, localization,
                             paths)
    electrode_coord_path = make_task(save_coords_for_blender, subject_id,
                                     localization, paths.tal,
                                     rootdir=paths.root)
    fs_files = make_task(freesurfer_to_wavefront, paths, setup_status)
    hcp_subj_files = make_task(avg_hcp_to_subject, subject_id, localization,
                               paths, setup_status)
    hcp_files = make_task(split_hcp_surface, paths, hcp_subj_files, fs_files)
    dk_files = make_task(split_dk_surface, paths, fs_files)
    prior_stim = make_task(gen_mapped_prior_stim_sites, subject_id,
                           localization, paths, setup_status)
    if blender:
        # Complete the blender-related tasks
        blender_setup_status = make_task(setup_standalone_blender_scene, paths)
        output = make_task(gen_blender_scene, subject_id, localization, paths,
                           blender_setup_status, prior_stim, hcp_files,
                           dk_files, electrode_coord_path)
        return output.compute()

    # If not producing the blender scene, simply create the underlying data
    electrode_coord_path.compute()
    hcp_files.compute()
    dk_files.compute()
    prior_stim.compute()
    return


def setup_avg_paths() -> FilePaths:
    """ Create default paths for building average brain visualization

    Returns
    -------
    paths: :class:`cml_pipelines.paths.FilePaths`
        File path container
    """
    paths = FilePaths("/", output="reports/r1/subjects/avg/",
                      avg_roi="data10/eeg/freesurfer/subjects/average/surf/roi/")
    return paths


def setup_paths(subject_id: str, localization: str,
                rhino_root: Optional[str] ="/"):
    """
        Helper function to produce a `cml_pipelines.paths.FilePaths` object
        with production paths for building a subject-specific 3D brain
        visualization

    Parameters
    ----------
    subject_id: str
        ID of subject to generate the brain visualization
    localization: str
        Localization number as a string to use. Typically this is 0.
    rhino_root: str, default: "/"
        Mount point for RHINO
    """
    subject_localization = _combine_subject_localization(subject_id,
                                                         localization)
    subject_num = _extract_subject_num(subject_id)

    # Common paths used throughout the pipeline
    BASE = "/data10/eeg/freesurfer/subjects/{}".format(subject_localization)
    CORTEX = "/data10/eeg/freesurfer/subjects/{}/surf/roi".format(subject_localization)
    CONTACT = "/data10/RAM/subjects/{}/tal/coords".format(subject_localization)
    TAL = "/data10/RAM/subjects/{}/tal".format(subject_localization)
    IMAGE = "/data10/RAM/subjects/{}/imaging/autoloc/".format(subject_localization)
    OUTPUT = "/reports/r1/subjects/{}/reports/iEEG_surface".format(subject_num)

    paths = FilePaths(rhino_root, base=BASE, cortex=CORTEX, contact=CONTACT,
                      tal=TAL, image=IMAGE, output=OUTPUT)
    return paths


def setup_subject_directory(subject_id: str, localization: int,
                            paths: FilePaths) -> bool:
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


def setup_standalone_blender_scene(paths: FilePaths, avg=False,
                                   force_rerun=False) -> bool:
    """ Copies Blender template files to the final output location

    Parameters
    ----------
    paths: `cml_pipelines.paths.FilePaths`
        Container for file paths
    avg: bool
        If True, use the template for the average brain
    force_rerun: bool
        If true, overwrites existing files

    Returns
    -------
    bool: True if copy was successful, False on failure

    """
    if avg:
        template_dir = datafile("iEEG_avg_surface_template/")
    else:
        template_dir = datafile("iEEG_surface_template/")

    if os.path.exists(paths.output):
        if not force_rerun:
            raise RuntimeError("Blender scene already exists. Use force rerun "
                               "option to overwrite")
        shutil.rmtree(paths.output)

    shutil.copytree(template_dir, paths.output)
    return True


def freesurfer_to_wavefront(paths: FilePaths, setup_status: bool) -> FilePaths:
    """ Convert Freesurfer brain piece models to wavefront format

    Parameters
    ----------
    paths: :class:`cml_pipelines.paths.FilePaths
        File path container
    setup_status: bool
        If true, setup step was succesful. Indicates that this task is
        dependent on the setup completing successfully

    Returns
    -------
    exp_files: :class:`cml_pipelines.paths.FilePaths`
        File path container with files produced by the task

    """
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
    localization: str
        Localization number to use
    paths: :class:`cml_pipelines.paths.FilePaths`
        Container for various file paths produced by the task
    setup_status: bool
        True if the setup task completed successfully. The presence of this
        boolean in the function signature is used to notify the pipeline
        framework that this task depends on the result of the setup task

    Returns
    -------
    exp_files: :class:`cml_pipelines.paths.FilePaths`
        File path container object containing files produced by this task

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
                          rh_hcp=os.path.join(paths.cortex,
                                              "rh.HCP-MMP1.annot"),
                          lh_hcp=os.path.join(paths.cortex,
                                              "lh.HCP-MMP1.annot"))

    return exp_files


def gen_mapped_prior_stim_sites(subject_id, localization, paths,
                                setup_status) -> FilePaths:
    """ Map prior stim site locations into this subject's coordinate space

    Parameters
    ----------
    subject_id: str
        Subject ID
    localization: str
        Localization number to use
    paths: :class:`cml_pipelines.paths.FilePaths`
        Container for various file paths needed by the task
    setup_status: bool
        Status of the setup task. Indicates that this task is dependent on
        setup completing successfully

    Returns
    -------
    exp_paths: :class:`cml_pipelines.paths.FilePaths`
        File path container for files produced by this task

    """
    subject_localization = _combine_subject_localization(subject_id,
                                                         localization)
    output_file = build_prior_stim_location_mapping(subject_localization,
                                                    paths.base,
                                                    paths.image)

    exp_paths = FilePaths(root="/", prior_stim=output_file)

    return exp_paths


def split_dk_surface(paths: FilePaths, fs_to_wav_files: FilePaths) -> FilePaths:
    """ Creates individual brain objects based on Desikan-Killiany atlas

    Parameters
    ----------
    paths: :class:`cml_pipelines.paths.FilePaths`
        File path container for files needed by this task
    fs_to_wav_files: :class:`cml_pipelines.paths.FilePaths`
        File path container for files produced by the freesurfer_to_wavefront,
        which also indicates a dependency on this task

    Returns
    -------
    exp_files: :class:`cml_pipelines.paths.FilePaths`
        File path container for files produced by this task

    """
    subprocess.run(" ".join([bin_files("annot2dpv"),
                             os.path.join(paths.cortex, "rh.aparc.annot"),
                             os.path.join(paths.cortex, "rh.aparc.annot.dpv")]),
                   shell=True,
                   check=True)
    subprocess.run(" ".join([bin_files("annot2dpv"),
                             os.path.join(paths.cortex, "lh.aparc.annot"),
                             os.path.join(paths.cortex, "lh.aparc.annot.dpv")]),
                   shell=True,
                   check=True)

    subprocess.run(" ".join([bin_files("splitsrf"),
                             os.path.join(paths.cortex, "rh.pial.srf"),
                             os.path.join(paths.cortex, "rh.aparc.annot.dpv"),
                             os.path.join(paths.cortex, "rh.pial_roi")]),
                   shell=True,
                   check=True)

    subprocess.run(" ".join([bin_files("splitsrf"),
                             os.path.join(paths.cortex, "lh.pial.srf"),
                             os.path.join(paths.cortex, "lh.aparc.annot.dpv"),
                             os.path.join(paths.cortex, "lh.pial_roi")]),
                   shell=True,
                   check=True)

    # Mapping between the default numeric number and the name of the brain
    # region
    surf_num_dict = {"0001": "Unmeasured.obj",
                     "0002": "BanksSuperiorTemporal.obj",
                     "0003": "CACingulate.obj",
                     "0004": "MiddleFrontalCaudal.obj",
                     "0005": "Cuneus.obj",
                     "0006": "Entorhinal.obj",
                     "0007": "Fusiform.obj",
                     "0008": "InferiorParietal.obj",
                     "0009": "InferiorTemporal.obj",
                     "0010": "Isthmus.obj",
                     "0011": "LateralOccipital.obj",
                     "0012": "OrbitalFrontal.obj",
                     "0013": "Lingual.obj",
                     "0014": "MedialOrbitalFrontal.obj",
                     "0015": "MiddleTemporal.obj",
                     "0016": "Parahippocampal.obj",
                     "0017": "ParacentralLobule.obj",
                     "0018": "InfFrontalParsOpercularis.obj",
                     "0019": "InfFrontalParsOrbitalis.obj",
                     "0020": "InfFrontalParsTriangularis.obj",
                     "0021": "Pericalcarine.obj",
                     "0022": "Post-Central.obj",
                     "0023": "PosteriorCingulate.obj",
                     "0024": "Pre-Central.obj",
                     "0025": "PreCuneus.obj",
                     "0026": "RACingulate.obj",
                     "0027": "MiddleFrontalRostral.obj",
                     "0028": "SuperiorFrontal.obj",
                     "0029": "SuperiorParietal.obj",
                     "0030": "SuperiorTemporal.obj",
                     "0031": "Supra-Marginal.obj",
                     "0032": "FrontalPole.obj",
                     "0033": "TemporalPole.obj",
                     "0034": "TransverseTemporal.obj",
                     "0035": "Insula.obj"}

    base_input_file = paths.cortex + "/{hemisphere}.pial_roi.{surface_num}.srf"
    base_output_file = paths.cortex + "/{hemisphere}.{surface_name}"
    exp_files = FilePaths(root="/")
    for hemisphere in ["lh", "rh"]:
        for surface in surf_num_dict.keys():
            subprocess.run(" ".join([bin_files("srf2obj"),
                                     base_input_file.format(
                                         hemisphere=hemisphere,
                                         surface_num=surface),
                                     ">",
                                     base_output_file.format(
                                         hemisphere=hemisphere,
                                         surface_name=surf_num_dict[surface])]),
                           shell=True,
                           check=True)
            # Adding the output file to the set of paths
            setattr(exp_files, "".join([hemisphere, surface]),
                    base_output_file.format(hemisphere=hemisphere,
                                            surface_name=surf_num_dict[surface])
                    )

    return exp_files


def split_hcp_surface(paths: FilePaths, hcp_subj_files: FilePaths,
                      fs_to_wav_files: FilePaths) -> FilePaths:
    """ Creates individual brain objects based on the HCP atlas

    Parameters
    ----------
    paths: :class:`cml_pipelines.paths.FilePaths`
        File path container for files needed by this task
    hcp_subj_files: :class:`cml_pipelines.paths.FilePaths`
        File path container for files produced by the avg_hcp_to_subject task,
        indicating a dependency on this task
    fs_to_wav_files: :class:`cml_pipelines.paths.FilePaths`
        File path container for files produced by the freesurfer_to_wavefront
        task, indicating a dependency on this task

    Returns
    -------
    exp_files: :class:`cml_pipelines.paths.FilePaths`
        File path container for files produced by this task

    """
    subprocess.run(" ".join([bin_files("annot2dpv"),
                             os.path.join(paths.cortex, "lh.HCP-MMP1.annot"),
                             os.path.join(paths.cortex, "lh.HCP-MMP1.annot.dpv")]),
                   shell=True,
                   check=True)
    subprocess.run(" ".join([bin_files("annot2dpv"),
                             os.path.join(paths.cortex, "rh.HCP-MMP1.annot"),
                             os.path.join(paths.cortex, "rh.HCP-MMP1.annot.dpv")]),
                   shell=True,
                   check=True)
    subprocess.run(" ".join([bin_files("splitsrf"),
                             os.path.join(paths.cortex, "lh.pial.srf"),
                             os.path.join(paths.cortex, "lh.HCP-MMP1.annot.dpv"),
                             os.path.join(paths.cortex, "lh.hcp")]),
                   shell=True,
                   check=True)
    subprocess.run(" ".join([bin_files("splitsrf"),
                             os.path.join(paths.cortex, "rh.pial.srf"),
                             os.path.join(paths.cortex, "rh.HCP-MMP1.annot.dpv"),
                             os.path.join(paths.cortex, "rh.hcp")]),
                   shell=True,
                   check=True)

    hcp_surfaces = glob.glob(os.path.join(paths.cortex, "*.hcp.*.srf"))
    for surface in hcp_surfaces:
        subprocess.run(" ".join([bin_files("srf2obj"),
                                 surface,
                                 ">",
                                 surface.replace(".srf", ".obj")]),
                       shell=True,
                       check=True)

    exp_files = FilePaths(root="/", lh_hcp=os.path.join(paths.cortex,
                                                        "lh.hcp.0001.obj"),
                          rh_hcp=os.path.join(paths.cortex,
                                              "rh.hcp.0001.obj"))

    return exp_files


def gen_blender_scene(subject_id: str, localization: int, paths: FilePaths,
                      build_site_status, prior_stim_paths: FilePaths,
                      split_hcp_files: FilePaths, split_dk_files: FilePaths,
                      electrode_coord_files: FilePaths) -> FilePaths:
    """ Creates the Blender-based 3D brain standalone brain visualization

    Parameters
    ----------
    subject_id: str
        Subject ID
    localization: str
        Localization number to use
    paths: :class:`cml_pipelines.paths.FilePaths`
        File path container for files needed by this task
    build_site_status: bool
        Status of the setup_standalone_blender_scene task, indicating a
        dependency on this task
    prior_stim_paths: :class:`cml_pipelines.paths.FilePaths`
        File path container for files produced by the
        gen_mapped_prior_stim_sites task, indicating a dependency on this task
    split_hcp_files: :class:`cml_pipelines.paths.FilePaths`
        File path container for files produced by the split_hcp_surface task,
        indicating a dependency on this task
    split_dk_files: :class:`cml_pipelines.paths.FilePaths`
        File path container for files produced by the split_dk_surface,
        indicating a dependency on this task
    electrode_coord_files: :class:`cml_pipelines.paths.FilePaths`
        File path container for files produced by the save_coords_for_blender
        task, indicating a dependency on this task

    Returns
    -------
    exp_output: :class:`cml_pipelines.paths.FilePaths`
        File path container for files produced by this task

    """
    prior_stim_sites = prior_stim_paths.prior_stim
    subject_localiztion = _combine_subject_localization(subject_id,
                                                        localization)
    subprocess.run(["/usr/global/blender-2.78c-linux-glibc219-x86_64/blender",
                    "-b",
                    datafile("iEEG_surface_template/empty.blend"),
                    "-b",
                    "--python",
                    code_files("create_scene.py"),
                    "--",
                    subject_localiztion,
                    paths.cortex,
                    paths.tal,
                    paths.output,
                    prior_stim_sites],
                   check=True)
    exp_output = FilePaths(root="/",
                           blender_file=os.path.join(paths.output,
                                                     'iEEG_surface.json'))

    return exp_output


def _combine_subject_localization(subject_id: str, localization: int):
    """ Helper function to combine subject ID and localization number """

    subject_localization = subject_id
    localization = str(localization)
    if localization != '0':
        subject_localization = "_".join([subject_id, localization])

    return subject_localization


def _extract_subject_num(subject):
    """ Helper function to extract subject number from ID """
    if subject.find("R1") == -1:
        raise RuntimeError("Only R1 protocol subjects supported")

    subject_num = subject.replace("R1", "")
    if subject.find("_") == -1:
        subject_num = subject_num[:-1]
        return subject_num

    underscore_idx = subject_num.find("_")
    subject_num = subject_num[:underscore_idx - 1] + subject_num[underscore_idx:]
    return subject_num


# For quicker ad-hoc testing
if __name__ == "__main__":
    generate_subject_brain("R1387E", 0, blender=True, force_rerun=True)

