import pytest

from brainviewer.pipeline import *
from cml_pipelines.paths import FilePaths

datafile = functools.partial(resource_filename, 'brainviewer.tests.data')


class TestPipeline:
    @classmethod
    def setup_class(cls):
        cls.paths = FilePaths(datafile(""), base="", cortex="surf/roi/",
                              image="", tal="", output="output/blender_scene/")
        cls.subject_id = "R1405E"
        cls.localization = 0

    def test_setup(self):
        setup_status = setup(self.subject_id, self.paths)
        assert setup_status == True
        assert os.path.exists(os.path.join(self.paths.cortex, "lh.pial"))
        assert os.path.exists(os.path.join(self.paths.cortex, "rh.pial"))
        assert os.path.exists(os.path.join(self.paths.cortex, "lh.aparc.annot"))
        assert os.path.exists(os.path.join(self.paths.cortex, "rh.aparc.annot"))

    def test_setup_standalone_blender_scene(self):
        setup_standalone_blender_scene(self.paths)

        assert os.path.exists(datafile("output/blender_scene/iEEG_surface.html"))
        shutil.rmtree(datafile("output/blender_scene/"), ignore_errors=True)

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

