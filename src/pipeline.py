import os
import glob
import shutil
import luigi
import subprocess

from src.rerun import RerunnableTask
from src.mapper import build_prior_stim_location_mapping
from src.deltarec import build_prior_stim_results_table
from src.coords4blender import save_coords_for_blender

# Use for building file locations relative to the project root
PROJECTDIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

class SubjectConfig(luigi.Config):
    """ Genreal Luigi config class for processing single-subject"""
    SUBJECT = luigi.Parameter(default=None)
    SUBJECT_NUM = luigi.Parameter(default=None)
    BASE = luigi.Parameter(default="/data10/eeg/freesurfer/subjects/{}")
    CORTEX = luigi.Parameter(default="/data10/eeg/freesurfer/subjects/{}/surf/roi")
    CONTACT = luigi.Parameter(default="/data10/RAM/subjects/{}/tal/coords")
    TAL = luigi.Parameter(default="/data10/RAM/subjects/{}/tal")
    IMAGE = luigi.Parameter(default="/data10/RAM/subjects/{}/imaging/autoloc/")
    OUTPUT = luigi.Parameter(default="/reports/r1/subjects/{}/reports/iEEG_surface")
    FORCE_RERUN = luigi.Parameter(default=False)


class AllConfig(luigi.Config):
    BASE = luigi.Parameter(default="/data10/eeg/freesurfer/subjects/{}")
    CORTEX = luigi.Parameter(default="/data10/eeg/freesurfer/subjects/{}/surf/roi")
    CONTACT = luigi.Parameter(default="/data10/RAM/subjects/{}/tal/coords")
    TAL = luigi.Parameter(default="/data10/RAM/subjects/{}/tal")
    IMAGE = luigi.Parameter(default="/data10/RAM/subjects/{}/imaging/autoloc/")
    OUTPUT = luigi.Parameter(default="/reports/r1/subjects/{}/reports/iEEG_surface")


class AvgBrainConfig(luigi.Config):
    OUTPUT = luigi.Parameter(default="/reports/r1/subjects/avg/")
    AVG_ROI = luigi.Parameter(default="/data10/eeg/freesurfer/subjects/average/surf/roi/")


class Setup(SubjectConfig, RerunnableTask):
    """
        Checks that the required freesurfer cortical surface and coordinate
        name files exist for the given SUBJECT
    """

    def requires(self):
        return

    def run(self):
        if (os.path.exists(self.CORTEX.format(self.SUBJECT)) == False):
            os.mkdir(self.CORTEX.format(self.SUBJECT))
        shutil.copy(self.BASE.format(self.SUBJECT) + "/surf/lh.pial", self.CORTEX.format(self.SUBJECT))
        shutil.copy(self.BASE.format(self.SUBJECT) + "/surf/rh.pial", self.CORTEX.format(self.SUBJECT))
        shutil.copy(self.BASE.format(self.SUBJECT) + "/label/lh.aparc.annot", self.CORTEX.format(self.SUBJECT))
        shutil.copy(self.BASE.format(self.SUBJECT) + "/label/rh.aparc.annot", self.CORTEX.format(self.SUBJECT))

        return

    # TODO: Add matlab talstruct as explicit dependency. Localization.json for neurorad v2
    def output(self):
        return [luigi.LocalTarget(self.CORTEX.format(self.SUBJECT)),
                luigi.LocalTarget(self.BASE.format(self.SUBJECT) + "/surf/lh.pial"),
                luigi.LocalTarget(self.BASE.format(self.SUBJECT) + "/surf/rh.pial"),
                luigi.LocalTarget(self.BASE.format(self.SUBJECT) + "/label/lh.aparc.annot"),
                luigi.LocalTarget(self.BASE.format(self.SUBJECT) + "/label/rh.aparc.annot"),
                luigi.LocalTarget(self.TAL.format(self.SUBJECT) + "/VOX_coords_mother_dykstra.txt"),
                luigi.LocalTarget(self.TAL.format(self.SUBJECT) + "/VOX_coords_mother_dykstra_bipolar.txt")]


class HCPAtlasMapping(SubjectConfig, RerunnableTask):
    """ Maps the HCP atlas from the fs average brain to the current subject

    This task relies on the mri_surf2surf freesurfer command, which uses the
    FREESURFER_HOME and SUBJECTS_DIR environment variables to search for input
    files and save output. If testing, be sure that these are updated to avoid
    writing to the production file system locations.

    """
    def requires(self):
        return Setup(self.SUBJECT, self.SUBJECT_NUM, self.BASE, self.CORTEX,
                        self.CONTACT, self.TAL, self.IMAGE, self.OUTPUT,
                        self.FORCE_RERUN)


    def run(self):
        subprocess.run("mri_surf2surf " +
                       "--srcsubject fsaverage_temp " +
                       "--sval-annot HCP-MMP1.annot " +
                       "--trgsubject {} ".format(self.SUBJECT) +
                       "--trgsurfval HCP-MMP1.annot " +
                       "--hemi lh",
                       shell=True,
                       check=True)
        subprocess.run("mri_surf2surf " +
                       "--srcsubject fsaverage_temp " +
                       "--sval-annot HCP-MMP1.annot " +
                       "--trgsubject {} ".format(self.SUBJECT) +
                       "--trgsurfval HCP-MMP1.annot " +
                       "--hemi rh",
                       shell=True,
                       check=True)
        shutil.copy(self.BASE.format(self.SUBJECT) + "/label/lh.HCP-MMP1.annot",
                    self.CORTEX.format(self.SUBJECT))
        shutil.copy(self.BASE.format(self.SUBJECT) + "/label/rh.HCP-MMP1.annot",
                    self.CORTEX.format(self.SUBJECT))
        return

    def output(self):
        return [luigi.LocalTarget(self.CORTEX.format(self.SUBJECT) + "/lh.HCP-MMP1.annot"),
                luigi.LocalTarget(self.CORTEX.format(self.SUBJECT) + "/rh.HCP-MMP1.annot")]


class SplitHCPSurface(SubjectConfig, RerunnableTask):
    """ Splits subject's surface into regions based on the HCP atlas """
    def requires(self):
        return [HCPAtlasMapping(self.SUBJECT, self.SUBJECT_NUM, self.BASE, self.CORTEX,
                               self.CONTACT, self.TAL, self.IMAGE, self.OUTPUT,
                               self.FORCE_RERUN),
                FreesurferToWavefront(self.SUBJECT, self.SUBJECT_NUM, self.BASE, self.CORTEX,
                                      self.CONTACT, self.TAL, self.IMAGE, self.OUTPUT,
                                      self.FORCE_RERUN)]


    def run(self):
        os.chdir(self.CORTEX.format(self.SUBJECT))
        subprocess.run(PROJECTDIR + "/bin/annot2dpv lh.HCP-MMP1.annot lh.HCP-MMP1.annot.dpv", shell=True, check=True)
        subprocess.run(PROJECTDIR + "/bin/annot2dpv rh.HCP-MMP1.annot rh.HCP-MMP1.annot.dpv", shell=True, check=True)
        subprocess.run(PROJECTDIR + "/bin/splitsrf lh.pial.srf lh.HCP-MMP1.annot.dpv lh.hcp", shell=True, check=True)
        subprocess.run(PROJECTDIR + "/bin/splitsrf rh.pial.srf rh.HCP-MMP1.annot.dpv rh.hcp", shell=True, check=True)
        os.chdir(PROJECTDIR + "/src/")

        # Convert .srf files to .obj
        hcp_surfaces = glob.glob(self.CORTEX.format(self.SUBJECT) + "/*.hcp.*.srf")
        for surface in hcp_surfaces:
            subprocess.run(PROJECTDIR + "/src/srf2obj " + surface + " > " + surface.replace(".srf", ".obj"),
                           shell=True,
                           check=True)
        return

    def output(self):
        # A couple of hundred objects are produced, so just check for a couple
        return [luigi.LocalTarget(self.CORTEX.format(self.SUBJECT) + "/rh.hcp.0001.obj"),
                luigi.LocalTarget(self.CORTEX.format(self.SUBJECT) + "/lh.hcp.0001.obj")]


class FreesurferToWavefront(SubjectConfig, RerunnableTask):
    """ Converts freesurfer cortical surface binary files to wavefront object files """

    def requires(self):
        return Setup(self.SUBJECT, self.SUBJECT_NUM, self.BASE, self.CORTEX,
                     self.CONTACT, self.TAL, self.IMAGE, self.OUTPUT,
                     self.FORCE_RERUN)

    def run(self):
        subprocess.run("mris_convert " +
                       self.CORTEX.format(self.SUBJECT) + "/lh.pial " +
                       self.CORTEX.format(self.SUBJECT) + "/lh.pial.asc",
                       shell=True,
                       check=True)
        subprocess.run("mris_convert " +
                       self.CORTEX.format(self.SUBJECT) + "/rh.pial " +
                       self.CORTEX.format(self.SUBJECT) + "/rh.pial.asc",
                       shell=True,
                       check=True)
        shutil.move(self.CORTEX.format(self.SUBJECT) + "/lh.pial.asc", self.CORTEX.format(self.SUBJECT) + "/lh.pial.srf")
        shutil.move(self.CORTEX.format(self.SUBJECT) + "/rh.pial.asc", self.CORTEX.format(self.SUBJECT) + "/rh.pial.srf")

        subprocess.run(PROJECTDIR + "/src/srf2obj " +
                       self.CORTEX.format(self.SUBJECT) + "/lh.pial.srf " +
                       "> " +
                       self.CORTEX.format(self.SUBJECT) + "/lh.pial.obj",
                       shell=True,
                       check=True)

        subprocess.run(PROJECTDIR + "/src/srf2obj " +
                        self.CORTEX.format(self.SUBJECT) + "/rh.pial.srf " +
                       "> " +
                       self.CORTEX.format(self.SUBJECT) + "/rh.pial.obj",
                       shell=True,
                       check=True)

        return

    def output(self):
        return [luigi.LocalTarget(self.CORTEX.format(self.SUBJECT) + "/lh.pial.obj"),
                luigi.LocalTarget(self.CORTEX.format(self.SUBJECT) + "/rh.pial.obj")]


class SplitCorticalSurface(SubjectConfig, RerunnableTask):
    """ Splits the left/right hemisphere wavefront objects into independent cortical surfaces """

    def requires(self):
        return FreesurferToWavefront(self.SUBJECT, self.SUBJECT_NUM, self.BASE,
                                     self.CORTEX, self.CONTACT, self.TAL,
                                     self.IMAGE, self.OUTPUT, self.FORCE_RERUN)

    def run(self):
        os.chdir(self.CORTEX.format(self.SUBJECT))
        subprocess.run(PROJECTDIR + "/bin/annot2dpv lh.aparc.annot lh.aparc.annot.dpv", shell=True, check=True)
        subprocess.run(PROJECTDIR + "/bin/annot2dpv rh.aparc.annot rh.aparc.annot.dpv", shell=True, check=True)
        subprocess.run(PROJECTDIR + "/bin/splitsrf lh.pial.srf lh.aparc.annot.dpv lh.pial_roi", shell=True, check=True)
        subprocess.run(PROJECTDIR + "/bin/splitsrf rh.pial.srf rh.aparc.annot.dpv rh.pial_roi", shell=True, check=True)
        os.chdir(PROJECTDIR + "/src/")

        surf_num_dict = {"0001":"Unmeasured.obj",
                         "0002":"BanksSuperiorTemporal.obj",
                         "0003":"CACingulate.obj",
                         "0004":"MiddleFrontalCaudal.obj",
                         "0005":"Cuneus.obj",
                         "0006":"Entorhinal.obj",
                         "0007":"Fusiform.obj",
                         "0008":"InferiorParietal.obj",
                         "0009":"InferiorTemporal.obj",
                         "0010":"Isthmus.obj",
                         "0011":"LateralOccipital.obj",
                         "0012":"OrbitalFrontal.obj",
                         "0013":"Lingual.obj",
                         "0014":"MedialOrbitalFrontal.obj",
                         "0015":"MiddleTemporal.obj",
                         "0016":"Parahippocampal.obj",
                         "0017":"ParacentralLobule.obj",
                         "0018":"InfFrontalParsOpercularis.obj",
                         "0019":"InfFrontalParsOrbitalis.obj",
                         "0020":"InfFrontalParsTriangularis.obj",
                         "0021":"Pericalcarine.obj",
                         "0022":"Post-Central.obj",
                         "0023":"PosteriorCingulate.obj",
                         "0024":"Pre-Central.obj",
                         "0025":"PreCuneus.obj",
                         "0026":"RACingulate.obj",
                         "0027":"MiddleFrontalRostral.obj",
                         "0028":"SuperiorFrontal.obj",
                         "0029":"SuperiorParietal.obj",
                         "0030":"SuperiorTemporal.obj",
                         "0031":"Supra-Marginal.obj",
                         "0032":"FrontalPole.obj",
                         "0033":"TemporalPole.obj",
                         "0034":"TransverseTemporal.obj",
                         "0035":"Insula.obj"}

        for hemisphere in ["lh", "rh"]:
            for surface in surf_num_dict.keys():
                subprocess.run(PROJECTDIR + "/src/srf2obj " +
                               self.CORTEX.format(self.SUBJECT) + "/" + hemisphere + ".pial_roi." + surface + ".srf > " +
                               self.CORTEX.format(self.SUBJECT) + "/" + hemisphere + "." + surf_num_dict[surface],
                               shell=True,
                               check=True)
        return

    def output(self):
        # 70 files are output, but just look for the last .obj file that should have been created
        return [luigi.LocalTarget(self.CORTEX.format(self.SUBJECT) + "/rh.Insula.obj"),
                luigi.LocalTarget(self.CORTEX.format(self.SUBJECT) + "/lh.Insula.obj")]


class GenElectrodeCoordinatesAndNames(SubjectConfig, RerunnableTask):
    """ Creates coordinate files out of MATLAB talstructs """
    def requires(self):
        return SplitCorticalSurface(self.SUBJECT, self.SUBJECT_NUM, self.BASE,
                                    self.CORTEX, self.CONTACT, self.TAL,
                                    self.IMAGE,  self.OUTPUT, self.FORCE_RERUN)

    def run(self):
        save_coords_for_blender(self.SUBJECT, self.CONTACT.format(self.SUBJECT))

    def output(self):
        return [luigi.LocalTarget(self.CONTACT.format(self.SUBJECT) + "/electrode_coordinates.csv")]


class GenMappedPriorStimSites(SubjectConfig, RerunnableTask):
    """" Creates the prior stim locations and results mapped to this subject's specific brain """

    def requires(self):
        """ This only depends on the localization pipeline having been run, so leave it blank for now """
        return

    def run(self):
        build_prior_stim_location_mapping(self.SUBJECT,
                                          self.BASE.format(self.SUBJECT),
                                          self.IMAGE.format(self.SUBJECT))
        return

    def output(self):
        return luigi.LocalTarget(self.BASE.format(self.SUBJECT) + "/prior_stim/" + self.SUBJECT + "_allcords.csv")


class BuildBlenderSite(SubjectConfig, RerunnableTask):
    """ Creates a single directory site for displaying web-based blender scene """
    def requires(self):
        return Setup(self.SUBJECT, self.SUBJECT_NUM,
                     self.BASE, self.CORTEX,
                     self.CONTACT, self.TAL,
                     self.IMAGE, self.OUTPUT,
                     self.FORCE_RERUN)

    def run(self):
        if os.path.exists(self.OUTPUT.format(self.SUBJECT_NUM)) == False:
            shutil.copytree(PROJECTDIR + "/iEEG_surface_template/", self.OUTPUT.format(self.SUBJECT_NUM))
            os.mkdir(self.OUTPUT.format(self.SUBJECT_NUM) + "/axial")
            os.mkdir(self.OUTPUT.format(self.SUBJECT_NUM) + "/coronal")

        shutil.copy(self.TAL.format(self.SUBJECT) + "/VOX_coords_mother_dykstra.txt", self.OUTPUT.format(self.SUBJECT_NUM))
        shutil.copy(self.TAL.format(self.SUBJECT) + "/VOX_coords_mother_dykstra_bipolar.txt", self.OUTPUT.format(self.SUBJECT_NUM))

        return

    def output(self):
        # More files are copied over, so this is a lazy check of output
        return [luigi.LocalTarget(self.OUTPUT.format(self.SUBJECT_NUM) + "/VOX_coords_mother_dykstra.txt")]


class GenBlenderScene(SubjectConfig, RerunnableTask):
    """ Generates the blender scene from wavefront object and coordinate files """

    def requires(self):
        return [BuildBlenderSite(self.SUBJECT, self.SUBJECT_NUM, self.BASE,
                                self.CORTEX, self.CONTACT, self.TAL, self.IMAGE,
                                self.OUTPUT, self.FORCE_RERUN),
                GenElectrodeCoordinatesAndNames(self.SUBJECT, self.SUBJECT_NUM,
                                                self.BASE, self.CORTEX,
                                                self.CONTACT, self.TAL,
                                                self.IMAGE, self.OUTPUT,
                                                self.FORCE_RERUN),
                GenMappedPriorStimSites(self.SUBJECT, self.SUBJECT_NUM,
                                        self.BASE, self.CORTEX, self.CONTACT,
                                        self.TAL, self.IMAGE, self.OUTPUT,
                                        self.FORCE_RERUN),
                SplitHCPSurface(self.SUBJECT, self.SUBJECT_NUM,
                                self.BASE, self.CORTEX, self.CONTACT,
                                self.TAL, self.IMAGE, self.OUTPUT,
                                self.FORCE_RERUN)]

    def run(self):
        subject_stimfile = self.BASE.format(self.SUBJECT) + "/prior_stim/" + self.SUBJECT + "_allcords.csv"
        subprocess.run(["/usr/global/blender-2.78c-linux-glibc219-x86_64/blender",
                        "-b",
                        PROJECTDIR + "/iEEG_surface_template/empty.blend",
                        "-b",
                        "--python",
                        PROJECTDIR + "/src/create_scene.py",
                        "--",
                        self.SUBJECT,
                        self.SUBJECT_NUM,
                        self.CORTEX.format(self.SUBJECT),
                        self.CONTACT.format(self.SUBJECT),
                        self.OUTPUT.format(self.SUBJECT_NUM),
                        subject_stimfile],
                       check=True)
        return

    def output(self):
        return [luigi.LocalTarget(self.OUTPUT.format(self.SUBJECT_NUM) + "/iEEG_surface.blend"),
                luigi.LocalTarget(self.OUTPUT.format(self.SUBJECT_NUM) + "/iEEG_surface.bin"),
                luigi.LocalTarget(self.OUTPUT.format(self.SUBJECT_NUM) + "/iEEG_surface.json")]


class BuildAll(AllConfig, RerunnableTask):
    """ Dummy task that triggers scene building for subjects """
    def requires(self):
        # Create a dictionary mapping subject numbers to subject identifiers
        subject_dirs = glob.glob("/reports/r1/subjects/*/")
        subjects = [path.split('/')[-2] for path in subject_dirs]
        subject_dict = {}
        for subject in subjects:
            match_dirs = glob.glob("/protocols/r1/subjects/R1{}*".format(subject))
            if len(match_dirs) == 1:
                subject_dict[subject] = match_dirs[0].split('/')[-1]

        for subject_num, subject_id in subject_dict.items():
            yield GenBlenderScene(subject_id, subject_num, self.BASE,
                                  self.CORTEX, self.CONTACT, self.TAL,
                                  self.IMAGE, self.OUTPUT, self.FORCE_RERUN)



class CanBuildPriorStimAvgBrain(AvgBrainConfig, luigi.ExternalTask):
    def output(self):
        return luigi.LocalTarget(self.AVG_ROI + "lh.pial.obj")


class BuildPriorStimAvgBrain(AvgBrainConfig, luigi.ExternalTask):
    """ Creates the visualization showing prior stim locations on the average brain """
    def requires(self):
        return CanBuildPriorStimAvgBrain(self.OUTPUT, self.AVG_ROI)

    def run(self):
        shutil.copytree(PROJECTDIR + "/iEEG_avg_surface_template/", self.OUTPUT)
        prior_stim_results_df = build_prior_stim_results_table()
        prior_stim_results_df = prior_stim_results_df[prior_stim_results_df["deltarec"].isnull() == False]
        del prior_stim_results_df["montage_num"] # not needed in this case

        stimfile = self.OUTPUT + "prior_stim_locations.csv"
        prior_stim_results_df.to_csv(stimfile, index=False)

        # run subprocess to generate the blender scene
        subprocess.run(["/usr/global/blender-2.78c-linux-glibc219-x86_64/blender",
                        "-b",
                        PROJECTDIR + "/iEEG_surface_template/empty.blend",
                        "-b",
                        "--python",
                        PROJECTDIR + "/src/create_scene.py",
                        "--",
                        self.AVG_ROI,
                        self.OUTPUT,
                        stimfile],
                       check=True)

        return

    def output(self):
        return luigi.LocalTarget(self.OUTPUT + "iEEG_surface.blend")


