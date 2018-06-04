import os
import pytest
import shutil
import functools
from pkg_resources import resource_filename

from brainviewer.pipeline import *
from cml_pipelines.paths import FilePaths

datafile = functools.partial(resource_filename, 'brainviewer.tests.data')


class TestPipelineTasks:
    """ Functional tests for individual pipeline tasks """
    @classmethod
    def setup_class(cls):
        cls.paths = FilePaths(datafile("R1291M_1/"), base="",
                              cortex="surf/roi/", image="imaging/autoloc/",
                              tal="tal/", output="blender_scene/")
        cls.subject_id = "R1291M"
        cls.localization = 1

    @pytest.mark.rhino
    def test_save_coords_for_blender(self):
        returned_path = save_coords_for_blender(self.subject_id,
                                                self.localization,
                                                self.paths.tal,
                                                rootdir="/")
        assert os.path.exists(returned_path)

    def test_setup(self):
        setup_status = setup(self.subject_id, self.localization, self.paths)
        assert setup_status is True
        assert os.path.exists(os.path.join(self.paths.cortex, "lh.pial"))
        assert os.path.exists(os.path.join(self.paths.cortex, "rh.pial"))
        assert os.path.exists(os.path.join(self.paths.cortex, "lh.aparc.annot"))
        assert os.path.exists(os.path.join(self.paths.cortex, "rh.aparc.annot"))

    def test_setup_standalone_blender_scene(self):
        setup_standalone_blender_scene(self.paths, force_rerun=True)

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

    @pytest.mark.rhino
    def test_split_dk_surface(self):
        returned_paths = split_dk_surface(self.paths, self.paths)
        assert os.path.exists(returned_paths.lh0001)

    @pytest.mark.rhino
    def test_split_hcp_surface(self):
        returned_paths = split_hcp_surface(self.paths, self.paths, self.paths)
        assert os.path.exists(returned_paths.lh_hcp)
        assert os.path.exists(returned_paths.rh_hcp)

    @pytest.mark.rhino
    def test_gen_mapped_prior_stim_sites(self):
        returned_paths = gen_mapped_prior_stim_sites(self.subject_id,
                                                     self.localization,
                                                     self.paths,
                                                     True)
        assert os.path.exists(returned_paths.prior_stim)

    @pytest.mark.rhino
    def test_gen_blender_scene(self):
        prior_stim_output = FilePaths(
            root="/",
            prior_stim=os.path.join(self.paths.base,
                                    "prior_stim/R1291M_1_allcords.csv"))
        # Most of the FilePaths objects that are passed are only used to
        # denote dependencies and are not actually used, which is why
        returned_paths = gen_blender_scene(self.subject_id, self.localization,
                                           self.paths, True, prior_stim_output,
                                           self.paths, self.paths, self.paths)
        assert os.path.exists(returned_paths.blender_file)

    @classmethod
    def teardown_class(cls):
        """ Cleanup to run when test cases finish """
        if os.path.exists(cls.paths.cortex):
            shutil.rmtree(cls.paths.cortex)

        if os.path.exists(cls.paths.output):
            shutil.rmtree(cls.paths.output)


def test_full_pipeline():
    """ Black-box test for the full 3D pipeline """
    paths = FilePaths(datafile("R1291M_1/"), base="",
                      cortex="surf/roi/", image="imaging/autoloc/",
                      tal="tal/", output="blender_scene/")
    subject_id = "R1291M"
    localization = 1
    output_file = generate_3d_brain_viz(subject_id, localization, paths=paths,
                                        force_rerun=True, blender=True)

    assert os.path.exists(output_file.blender_file)

    if os.path.exists(paths.cortex):
        shutil.rmtree(paths.cortex)

    if os.path.exists(paths.output):
        shutil.rmtree(paths.output)

