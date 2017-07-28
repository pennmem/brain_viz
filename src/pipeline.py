import os
import glob
import shutil
import luigi
import subprocess


class SubjectConfig(luigi.Config):
    """ Genreal Luigi config class for processing single-subject"""
    SUBJECT = luigi.Parameter(default=None)
    SUBJECT_NUM = luigi.Parameter(default=None)
    BASE = luigi.Parameter(default="/data10/eeg/freesurfer/subjects/{}")
    CORTEX = luigi.Parameter(default="/data10/eeg/freesurfer/subjects/{}/surf/roi")
    CONTACT = luigi.Parameter(default="/data10/RAM/subjects/{}/tal/coords")
    TAL = luigi.Parameter(default="/data10/RAM/subjects/{}/tal")
    OUTPUT = luigi.Parameter(default="/reports/r1/subjects/{}/reports/iEEG_surface")


class AllConfig(luigi.Config):
    BASE = luigi.Parameter(default="/data10/eeg/freesurfer/subjects/{}")
    CORTEX = luigi.Parameter(default="/data10/eeg/freesurfer/subjects/{}/surf/roi")
    CONTACT = luigi.Parameter(default="/data10/RAM/subjects/{}/tal/coords")
    TAL = luigi.Parameter(default="/data10/RAM/subjects/{}/tal")
    OUTPUT = luigi.Parameter(default="/reports/r1/subjects/{}/reports/iEEG_surface")


class CanStart(SubjectConfig, luigi.Task):
    """
        Checks that the required freesurfer cortical surface and coordinate
        name files exist for the given SUBJECT
    """

    def output(self):
        return [luigi.LocalTarget(self.BASE.format(self.SUBJECT) + "/surf/lh.pial"),
                luigi.LocalTarget(self.BASE.format(self.SUBJECT) + "/surf/rh.pial"),
                luigi.LocalTarget(self.BASE.format(self.SUBJECT) + "/label/lh.aparc.annot"),
                luigi.LocalTarget(self.BASE.format(self.SUBJECT) + "/label/rh.aparc.annot"),
                luigi.LocalTarget(self.TAL.format(self.SUBJECT) + "/VOX_coords_mother_dykstra.txt"),
                luigi.LocalTarget(self.TAL.format(self.SUBJECT) + "/VOX_coords_mother_dykstra_bipolar.txt")]


class FreesurferToWavefront(SubjectConfig, luigi.Task):
    """ Converts freesurfer cortical surface binary files to wavefront object files """

    def requires(self):
        return CanStart(self.SUBJECT, self.SUBJECT_NUM, self.BASE, self.CORTEX, self.CONTACT, self.TAL, self.OUTPUT)

    def run(self):
        os.mkdir(self.CORTEX.format(self.SUBJECT))
        shutil.copy(self.BASE.format(self.SUBJECT) + "/surf/lh.pial", self.CORTEX.format(self.SUBJECT))
        shutil.copy(self.BASE.format(self.SUBJECT) + "/surf/rh.pial", self.CORTEX.format(self.SUBJECT))
        shutil.copy(self.BASE.format(self.SUBJECT) + "/label/lh.aparc.annot", self.CORTEX.format(self.SUBJECT))
        shutil.copy(self.BASE.format(self.SUBJECT) + "/label/rh.aparc.annot", self.CORTEX.format(self.SUBJECT))

        subprocess.run("mris_convert " +
                        self.CORTEX.format(self.SUBJECT) + "/lh.pial " +
                        self.CORTEX.format(self.SUBJECT) + "/lh.pial.asc",
                       shell=True)
        subprocess.run("mris_convert " +
                       self.CORTEX.format(self.SUBJECT) + "/rh.pial " +
                       self.CORTEX.format(self.SUBJECT) + "/rh.pial.asc",
                       shell=True)
        shutil.move(self.CORTEX.format(self.SUBJECT) + "/lh.pial.asc", self.CORTEX.format(self.SUBJECT) + "/lh.pial.srf")
        shutil.move(self.CORTEX.format(self.SUBJECT) + "/rh.pial.asc", self.CORTEX.format(self.SUBJECT) + "/rh.pial.srf")

        subprocess.run("srf2obj " +
                       self.CORTEX.format(self.SUBJECT) + "/lh.pial.srf " +
                       "> " +
                       self.CORTEX.format(self.SUBJECT) + "/lh.pial.obj",
                       shell=True)

        subprocess.run("srf2obj " +
                        self.CORTEX.format(self.SUBJECT) + "/rh.pial.srf " +
                       "> " +
                       self.CORTEX.format(self.SUBJECT) + "/rh.pial.obj",
                       shell=True)

        return

    def output(self):
        return [luigi.LocalTarget(self.CORTEX.format(self.SUBJECT) + "/lh.pial.obj"),
                luigi.LocalTarget(self.CORTEX.format(self.SUBJECT) + "/rh.pial.obj")]


class SplitCorticalSurface(SubjectConfig, luigi.Task):
    """ Splits the left/right hemisphere wavefront objects into independent cortical surfaces """

    def requires(self):
        return FreesurferToWavefront(self.SUBJECT, self.SUBJECT_NUM, self.BASE, self.CORTEX, self.CONTACT, self.TAL, self.OUTPUT)

    def run(self):
        codedir = os.getcwd() # code directory
        os.chdir(self.CORTEX.format(self.SUBJECT))
        subprocess.run("matlab -r 'annot2dpv lh.aparc.annot lh.aparc.annot.dpv;"\
                       "annot2dpv rh.aparc.annot rh.aparc.annot.dpv;"\
                       "splitsrf lh.pial.srf lh.aparc.annot.dpv lh.pial_roi;"\
                       "splitsrf rh.pial.srf rh.aparc.annot.dpv rh.pial_roi;"\
                       "exit;'",
                       shell=True)
        os.chdir(codedir)

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
                subprocess.run("srf2obj " +
                               self.CORTEX.format(self.SUBJECT) + "/" + hemisphere + ".pial_roi." + surface + ".srf > " +
                               self.CORTEX.format(self.SUBJECT) + "/" + hemisphere + "." + surf_num_dict[surface],
                               shell=True)
        return

    def output(self):
        # 70 files are output, but just look for the last .obj file that should have been created
        return [luigi.LocalTarget(self.CORTEX.format(self.SUBJECT) + "/rh.Insula.obj"),
                luigi.LocalTarget(self.CORTEX.format(self.SUBJECT) + "/lh.Insula.obj")]


class GenElectrodeCoordinatesAndNames(SubjectConfig, luigi.Task):
    """ Creates coordinate files and electrode names for blender

        Note: This task is no longer necessary since the names of the electrodes
        can be retrieved from the talstruct (contacts.json and pairs.json), which
        is also captured in the database
    """
    def requires(self):
        return SplitCorticalSurface(self.SUBJECT, self.SUBJECT_NUM, self.BASE, self.CORTEX, self.CONTACT, self.TAL, self.OUTPUT)

    def run(self):
        codedir = os.getcwd()
        os.chdir(self.CONTACT.format(self.SUBJECT))
        command = 'matlab -r "coords4blender(\'' + self.SUBJECT + '\',\'' + self.CONTACT.format(self.SUBJECT) + '\'); exit;"'
        subprocess.run(command, shell=True)
        os.chdir(codedir)

    def output(self):
        return [luigi.LocalTarget(self.CONTACT.format(self.SUBJECT) + "/monopolar_start_blender.txt"),
                luigi.LocalTarget(self.CONTACT.format(self.SUBJECT) + "/monopolar_blender.txt"),
                luigi.LocalTarget(self.CONTACT.format(self.SUBJECT) + "/bipolar_blender.txt"),
                luigi.LocalTarget(self.CONTACT.format(self.SUBJECT) + "/monopolar_start_names.txt"),
                luigi.LocalTarget(self.CONTACT.format(self.SUBJECT) + "/monopolar_names.txt"),
                luigi.LocalTarget(self.CONTACT.format(self.SUBJECT) + "/bipolar_names.txt")]


class BuildBlenderSite(SubjectConfig, luigi.Task):
    """ Creates a single directory site for displaying web-based blender scene """
    def requires(self):
        return GenElectrodeCoordinatesAndNames(self.SUBJECT, self.SUBJECT_NUM, self.BASE, self.CORTEX, self.CONTACT, self.TAL, self.OUTPUT)

    def run(self):
        shutil.copytree(os.getcwd() + "/../iEEG_surface_template/", self.OUTPUT.format(self.SUBJECT_NUM))
        os.mkdir(self.OUTPUT.format(self.SUBJECT_NUM) + "/axial")
        os.mkdir(self.OUTPUT.format(self.SUBJECT_NUM) + "/coronal")

        shutil.copy(self.CONTACT.format(self.SUBJECT) + "/monopolar_names.txt", self.OUTPUT.format(self.SUBJECT_NUM))
        shutil.copy(self.CONTACT.format(self.SUBJECT) + "/bipolar_names.txt", self.OUTPUT.format(self.SUBJECT_NUM))
        shutil.copy(self.CONTACT.format(self.SUBJECT) + "/monopolar_start_names.txt", self.OUTPUT.format(self.SUBJECT_NUM))
        shutil.copy(self.TAL.format(self.SUBJECT) + "/VOX_coords_mother_dykstra.txt", self.OUTPUT.format(self.SUBJECT_NUM))
        shutil.copy(self.TAL.format(self.SUBJECT) + "/VOX_coords_mother_dykstra_bipolar.txt", self.OUTPUT.format(self.SUBJECT_NUM))

        return

    def output(self):
        # More files are copied over, so this is a lazy check of output
        return [luigi.LocalTarget(self.OUTPUT.format(self.SUBJECT_NUM) + "/monopolar_names.txt")]


class GenBlenderScene(SubjectConfig, luigi.Task):
    """ Generates the blender scene from wavefront object and coordinate files """

    def requires(self):
        return BuildBlenderSite(self.SUBJECT, self.SUBJECT_NUM, self.BASE, self.CORTEX, self.CONTACT, self.TAL, self.OUTPUT)

    def run(self):
        subprocess.run(["/home1/zduey/blender/blender",
                        "-b",
                        "/home1/zduey/brain_viz/iEEG_surface_template/empty.blend",
                        "-b",
                        "--python",
                        "create_scene.py",
                        "--",
                        self.SUBJECT,
                        self.SUBJECT_NUM,
                        self.CORTEX.format(self.SUBJECT),
                        self.CONTACT.format(self.SUBJECT),
                        self.OUTPUT.format(self.SUBJECT_NUM)])
        return

    def output(self):
        return [luigi.LocalTarget(self.OUTPUT.format(self.SUBJECT_NUM) + "/iEEG_surface.blend"),
                luigi.LocalTarget(self.OUTPUT.format(self.SUBJECT_NUM) + "/iEEG_surface.bin"),
                luigi.LocalTarget(self.OUTPUT.format(self.SUBJECT_NUM) + "/iEEG_surface.json")]

class RebuildBlenderScene(SubjectConfig, luigi.Task):
    """ Remove the old blender scene and regenereate it. Used for when the underlying
        visualization data (.bin, .blend, .json) or the scene creation script has
        changed
    """

    def requires(self):
        if os.path.exists(self.OUTPUT.format(self.SUBJECT_NUM)):
            shutil.rmtree(self.OUTPUT.format(self.SUBJECT_NUM))
            yield GenBlenderScene(self.SUBJECT, self.SUBJECT_NUM, self.BASE, self.CORTEX, self.CONTACT, self.TAL, self.OUTPUT)



class BuildAll(AllConfig, luigi.Task):
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
            yield GenBlenderScene(subject_id, subject_num, self.BASE, self.CORTEX, self.CONTACT, self.TAL, self.OUTPUT)
