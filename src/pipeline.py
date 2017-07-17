import os
import glob
import luigi
from luigi.contrib.external_program import ExternalProgramTask



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


class FreesurferToWavefront(SubjectConfig, ExternalProgramTask):
    """ Converts freesurfer cortical surface binary files to wavefront object files """

    def requires(self):
        return CanStart(self.SUBJECT, self.SUBJECT_NUM, self.BASE, self.CORTEX, self.CONTACT, self.TAL, self.OUTPUT)

    def program_args(self):
        return ["./freesurfer2wavefront.sh",
                self.BASE.format(self.SUBJECT),
                self.CORTEX.format(self.SUBJECT)]

    def output(self):
        return [luigi.LocalTarget(self.CORTEX.format(self.SUBJECT) + "/lh.pial.obj"),
                luigi.LocalTarget(self.CORTEX.format(self.SUBJECT) + "/rh.pial.obj")]


class SplitCorticalSurface(SubjectConfig, ExternalProgramTask):
    """ Splits the left/right hemisphere wavefront objects into independent cortical surfaces """

    def requires(self):
        return FreesurferToWavefront(self.SUBJECT, self.SUBJECT_NUM, self.BASE, self.CORTEX, self.CONTACT, self.TAL, self.OUTPUT)

    def program_args(self):
        return ["./split_cortical.sh",
                self.CORTEX.format(self.SUBJECT)]

    def output(self):
        # 70 files are output, but just look for the last .obj file that should have been created
        return [luigi.LocalTarget(self.CORTEX.format(self.SUBJECT) + "/rh.Insula.obj"),
                luigi.LocalTarget(self.CORTEX.format(self.SUBJECT) + "/lh.Insula.obj")]


class GenElectrodeCoordinatesAndNames(SubjectConfig, ExternalProgramTask):
    """ Creates coordinate files and electrode names for blender """
    def requires(self):
        return SplitCorticalSurface(self.SUBJECT, self.SUBJECET_NUM, self.BASE, self.CORTEX, self.CONTACT, self.TAL, self.OUTPUT)

    def program_args(self):
        return ["./create_coordinates.sh",
                self.SUBJECT,
                self.CONTACT.format(self.SUBJECT)]

    def output(self):
        return [luigi.LocalTarget(self.CONTACT.format(self.SUBJECT) + "/monopolar_start_blender.txt"),
                luigi.LocalTarget(self.CONTACT.format(self.SUBJECT) + "/monopolar_blender.txt"),
                luigi.LocalTarget(self.CONTACT.format(self.SUBJECT) + "/bipolar_blender.txt"),
                luigi.LocalTarget(self.CONTACT.format(self.SUBJECT) + "/monopolar_start_names.txt"),
                luigi.LocalTarget(self.CONTACT.format(self.SUBJECT) + "/monopolar_names.txt"),
                luigi.LocalTarget(self.CONTACT.format(self.SUBJECT) + "/bipolar_names.txt")]


class BuildBlenderSite(SubjectConfig, ExternalProgramTask):
    """ Creates a single directory site for displaying web-based blender scene """
    def requires(self):
        return GenElectrodeCoordinatesAndNames(self.SUBJECT, self.SUBJECT_NUM, self.BASE, self.CORTEX, self.CONTACT, self.TAL, self.OUTPUT)

    def program_args(self):
        return ["./build_template_site.sh",
                self.CONTACT.format(self.SUBJECT),
                self.TAL.format(self.SUBJECT),
                self.OUTPUT.format(self.SUBJECT_NUM)]

    def output(self):
        # More files are copied over, so this is a lazy check of output
        return [luigi.LocalTarget(self.OUTPUT.format(self.SUBJECT_NUM) + "/monopolar_names.txt")]


class GenBlenderScene(SubjectConfig, ExternalProgramTask):
    """ Generates the blender scene from wavefront object and coordinate files """
    def requires(self):
        return BuildBlenderSite(self.SUBJECT, self.SUBJECT_NUM, self.BASE, self.CORTEX, self.CONTACT, self.TAL, self.OUTPUT)

    def program_args(self):
        return ["/home1/zduey/blender/blender",
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
                self.OUTPUT.format(self.SUBJECT_NUM)]

    def output(self):
        return [luigi.LocalTarget(self.OUTPUT.format(self.SUBJECT_NUM) + "/iEEG_surface.blend"),
                luigi.LocalTarget(self.OUTPUT.format(self.SUBJECT_NUM) + "/iEEG_surface.bin"),
                luigi.LocalTarget(self.OUTPUT.format(self.SUBJECT_NUM) + "/iEEG_surface.json")]

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
