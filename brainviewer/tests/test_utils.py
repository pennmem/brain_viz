import os
import functools
from pkg_resources import resource_filename

from brainviewer.utils import *
from cml_pipelines.paths import FilePaths

datafile = functools.partial(resource_filename, 'brainviewer.tests.data')


class TestUtils:
    @classmethod
    def setup_class(cls):
        cls.paths = FilePaths(datafile(""), base="", cortex="surf/roi/",
                              image="", tal="")
        cls.subject_id = "R1405E"
        cls.localization = "0"

    def test_setup(self):
        setup_status = setup(self.subject_id, self.paths)
        assert setup_status == True
        assert os.path.exists(os.path.join(self.paths.cortex, "lh.pial"))
        assert os.path.exists(os.path.join(self.paths.cortex, "rh.pial"))
        assert os.path.exists(os.path.join(self.paths.cortex, "lh.aparc.annot"))
        assert os.path.exists(os.path.join(self.paths.cortex, "rh.aparc.annot"))

    def test_avg_hcp_to_subject(self):
        # os.environ["FREESURFER_HOME"] = ""
        # os.environ["SUBJECTS_DIR"] = datafile("")
        # hcp_status = avg_hcp_to_subject(self.subject_id, self.paths, True)
        pass

    def test_gen_electrode_coordinates_and_names(self):
        output_path = gen_electrode_coordinates_and_names(self.subject_id,
                                                          self.localization,
                                                          self.paths)
        assert os.path.exists(output_path)
