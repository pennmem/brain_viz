import pytest

from brainviewer.pipeline import *
from cml_pipelines.paths import FilePaths

datafile = functools.partial(resource_filename, 'brainviewer.tests.data')


class TestPipeline:
    @classmethod
    def setup_class(cls):
        cls.paths = FilePaths(datafile("R1291M_1/"), base="",
                              cortex="surf/roi/", image="imaging/autoloc/",
                              tal="tal/", output="blender_scene/")
        cls.subject_id = "R1291M"
        cls.localization = 1

    def test_setup(self):
        setup_status = setup(self.subject_id, self.localization, self.paths)
        assert setup_status is True
        assert os.path.exists(os.path.join(self.paths.cortex, "lh.pial"))
        assert os.path.exists(os.path.join(self.paths.cortex, "rh.pial"))
        assert os.path.exists(os.path.join(self.paths.cortex, "lh.aparc.annot"))
        assert os.path.exists(os.path.join(self.paths.cortex, "rh.aparc.annot"))

    def test_setup_standalone_blender_scene(self):
        setup_standalone_blender_scene(self.paths)

        assert os.path.exists(os.path.join(self.paths.output,
                                           "iEEG_surface.html"))

    @pytest.mark.rhino
    def test_freesurfer_to_wavefront(self):
        returned_paths = freesurfer_to_wavefront(self.paths, True)
        assert os.path.exists(returned_paths.rh_obj)
        assert os.path.exists(returned_paths.lh_obj)

    @pytest.mark.rhino
    def test_avg_hcp_to_subject(self):
        returned_paths = avg_hcp_to_subject(self.subject_id, self.localization,
                                            self.paths, True)
        assert os.path.exists(returned_paths.rh_hcp)
        assert os.path.exists(returned_paths.lh_hcp)

    @classmethod
    def teardown_class(cls):
        """ Cleanup to run when test cases finish """
        if os.path.exists(cls.paths.cortex):
            shutil.rmtree(cls.paths.cortex)

        if os.path.exists(cls.paths.output):
            shutil.rmtree(cls.paths.output)

