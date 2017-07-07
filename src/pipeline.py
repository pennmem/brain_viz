import os
import luigi
from luigi.contrib.external_program import ExternalProgramTask


def extract_subject_num(subject):
    """ Convert full subject name to just the number

        Ex: R1291_1 -> 291_1
    """
    if len(subject) > 7:
        subject_num = subject[2:5] + subject[6:]
    else:
        subject_num = subject[2:5]
    return subject_num


class SubjectConfig(luigi.Config):
    """ Genreal Luigi config class for processing single-subject"""
    SUBJECT = luigi.Parameter()
    BASE = luigi.Parameter(default="/data10/eeg/freesurfer/subjects/{}")
    CORTEX = luigi.Parameter(default="/data10/eeg/freesurfer/subjects/{}/surf/roi")
    CONTACT = luigi.Parameter(default="/data10/RAM/subjects/{}/tal/coords")
    TAL = luigi.Parameter(default="/data10/RAM/subjects/{}/tal")
    OUTPUT = luigi.Parameter(default="/reports/r1/subjects/{}/reports/iEEG_surface_new")


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
                luigi.LocalTarget(self.CONTACT.format(self.SUBJECT) + "/monopolar_names.txt"),
                luigi.LocalTarget(self.CONTACT.format(self.SUBJECT) + "/bipolar_names.txt"),
                luigi.LocalTarget(self.CONTACT.format(self.SUBJECT) + "/monopolar_start_names.txt"),
                luigi.LocalTarget(self.TAL.format(self.SUBJECT) + "/VOX_coords_mother_dykstra.txt"),
                luigi.LocalTarget(self.TAL.format(self.SUBJECT) + "/VOX_coords_mother_dykstra_bipolar.txt")]


class FreesurferToWavefront(SubjectConfig, ExternalProgramTask):
    """ Converts freesurfer cortical surface binary files to wavefront object files """

    def requires(self):
        return CanStart(self.SUBJECT, self.BASE, self.CORTEX, self.CONTACT, self.TAL, self.OUTPUT)

    def program_args(self):
        return [os.path.dirname(os.path.abspath('__file__')) + "/freesurfer2wavefront.sh",
                self.BASE.format(self.SUBJECT),
                self.CORTEX.format(self.SUBJECT)]

    def output(self):
        return [luigi.LocalTarget(self.CORTEX.format(self.SUBJECT) + "/lh.pial.obj"),
                luigi.LocalTarget(self.CORTEX.format(self.SUBJECT) + "/rh.pial.obj")]


class SplitCorticalSurface(SubjectConfig, ExternalProgramTask):
    """ Splits the left/right hemisphere wavefront objects into independent cortical surfaces """

    def requires(self):
        return FreesurferToWavefront(self.SUBJECT, self.BASE, self.CORTEX, self.CONTACT, self.OUTPUT)

    def program_args(self):
        # Need to change directory into cortexdir
        matlab_command = "annot2dpv lh.aparc.annot lh.aparc.annot.dpv;\
                          annot2dpv rh.aparc.annot rh.aparc.annot.dpv;\
                          splitsrf lh.pial.srf lh.aparc.annot.dpv lh.pial_roi;\
                          splitsrf rh.pial.srf rh.aparc.annot.dpv rh.pial_roi;\
                          exit;"
        return ["maltab", "-r", matlab_command]

    def output(self):
        # 70 files are output, but just look for the last .obj file that should have been created
        return [luigi.LocalTarget(self.CORTEX.format(self.SUBJECT) + "/lh.pial_roi_0035.srf"),
                luigi.LocalTarget(self.CORTEX.format(self.SUBJECT) + "/rh.pial_roi_0035.srf")]


class GenElectrodeCordinatesAndNames(SubjectConfig, ExternalProgramTask):
    """ Creates coordinate files and electrode names for blender """
    pass

class GenBlenderScene(SubjectConfig, ExternalProgramTask):
    """ Generates the blender scene from wavefront object and coordinate files """
    pass

class BuildBlenderSite(SubjectConfig, ExternalProgramTask):
    """ Creates a single directory site for displaying web-based blender scene """
    pass

class GenBrainVizData(SubjectConfig, ExternalProgramTask):
    """ Creates sub-director for housing output files for the brain visualization """

    def requires(self):
        return CanStart(self.SUBJECT, self.BASE, self.CORTEX, self.CONTACT, self.OUTPUT)

    def program_args(self):
        subject_num = extract_subject_num(self.SUBJECT)
        return ["./convert.sh",
                self.SUBJECT,
                subject_num,
                self.BASE.format(self.SUBJECT),
                self.CORTEX.format(self.SUBJECT),
                self.CONTACT.format(self.SUBJECT),
                self.OUTPUT.format(subject_num)]

    def output(self):
        subject_num = extract_subject_num(self.SUBJECT)
        return [luigi.LocalTarget(self.OUTPUT.format(subject_num) + "/iEEG_surface.blend")]

class BrainVizPipeline(SubjectConfig, luigi.WrapperTask):
    " Luigi wrapper task for running a single-SUBJECT brain viz pipeline """

    def requires(self):
        yield GenBrainVizData(self.SUBJECT, self.BASE, self.CORTEX, self.CONTACT, self.OUTPUT)
