import luigi
from luigi.contrib.external_program import ExternalProgramTask

# PYTHONPATH='.' luigi --module brain_viz CanStart --local-scheduler --SUBJECT "R1291M_1"

#BASE_PATH = "/home1/zduey/brain_viz/sample_data/{}"

def extract_subject_num(subject):
    """ Convert full subject name to just the number

    Ex: R1291_1 --> 291_1
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
    OUTPUT = luigi.Parameter(default="/reports/r1/subjects/{}/reports/iEEG_surface")

class CanStart(SubjectConfig, luigi.Task):
    """ Checks that the required freesurfer cortical surface files exist for the given SUBJECT """

    def output(self):
        return [luigi.LocalTarget(self.BASE.format(self.SUBJECT) + "/surf/lh.pial"),
                luigi.LocalTarget(self.BASE.format(self.SUBJECT) + "/surf/rh.pial"),
                luigi.LocalTarget(self.BASE.format(self.SUBJECT) + "/label/lh.aparc.annot"),
                luigi.LocalTarget(self.BASE.format(self.SUBJECT) + "/label/rh.aparc.annot")]


class GenBrainVizData(SubjectConfig, ExternalProgramTask):
    """ Creates sub-director for housing output files for the brain visualization """

    def requires(self):
        return CanStart(self.SUBJECT, self.BASE)

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
