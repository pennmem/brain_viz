import os
import filecmp
import pytest
import numpy as np
import shutil
import functools

from pkg_resources import resource_filename

import brainviewer.mapper as mapper
from cml_pipelines.paths import FilePaths

datafile = functools.partial(resource_filename, 'brainviewer.tests.data')


class TestMapper:
    @classmethod
    def setup_class(cls):
        cls.paths = FilePaths(datafile("R1291M_1/"), base="",
                              workdir="prior_stim/",
                              baselinedir="prior_stim_baseline/",
                              imagedir="imaging/autoloc/")
        cls.subject_id = "R1291M_1"

    # @classmethod
    # def teardown_class(cls):
    #     if os.path.exists(cls.paths.workdir):
    #         shutil.rmtree(cls.paths.workdir, ignore_errors=True)
    #     return

    def test_initialize(self):
        mapper.initialize(self.subject_id, self.paths.workdir + "/",
                          self.paths.imagedir + "/")
        assert os.path.exists("".join([self.paths.workdir + "/",
                                       self.subject_id,
                                       "_stimdeltarec_mni.nii.gz"]))
        assert os.path.exists("".join([self.paths.workdir + "/",
                                       self.subject_id,
                                       "_stimdeltarec_target_T1.nii.gz"]))
        assert os.path.exists("".join([self.paths.workdir + "/",
                                       self.subject_id,
                                       "_stimdeltarec_target_CT.nii.gz"]))

    def test_get_orig_mat(self):
        norig_matrix = mapper.get_orig_mat(self.paths.base, "/vox2ras")
        assert np.shape(norig_matrix) == (4, 4)

        norig_comparison_matrix = np.loadtxt(self.paths.baselinedir + "/Norig.txt")
        assert np.allclose(norig_matrix, norig_comparison_matrix)

        torig_matrix = mapper.get_orig_mat(self.paths.base, "/vox2ras-tkr")
        assert np.shape(torig_matrix) == (4, 4)

    def test_generate_generic_ras_file(self):
        mapper.generate_generic_RAS_file(self.paths.imagedir + "/",
                                         self.paths.workdir + "/",
                                         self.subject_id)

        outfile = (self.subject_id +
                   '_T01_CT_to_T00_mprageANTs0GenericAffine_RAS_itk.txt')
        assert os.path.exists(self.paths.workdir + "/" + outfile)
        assert filecmp.cmp(self.paths.workdir + "/" + outfile,
                           self.paths.baselinedir + "/" + outfile,
                           shallow=False)

    @pytest.mark.rhino
    def test_load_orig_mni_coords(self):
        mni_df = mapper.load_orig_mni_coords(self.subject_id)
        assert len(mni_df) > 0

    # def test_load_adj_mni_coords(self):
    #     subject = "R1216E"
    #     basedir, workdir, baselinedir, imagedir = setup_directories(subject)
    #     mni_df = mapper.load_adj_mni_coords(subject)
    #     assert len(mni_df) > 0
    #
    #     subject = "R1027J"
    #     basedir, workdir, baselinedir, imagedir = setup_directories(subject)
    #     mni_df = mapper.load_adj_mni_coords(subject)
    #     assert (mni_df is None) # no adjusted coordinates (depths only)

    # def test_get_mni_coords(self):
    #     # R1291M_1 does not have the correct updated mni file, so use a subject
    #     # who does have one
    #     subject = "R1216E"
    #     basedir, workdir, baselinedir, imagedir = setup_directories(subject)
    #     mni_df = mapper.get_mni_coords(subject)
    #     assert len(mni_df) > 0
    #
    #     # Unajusted coordinates only. Should still return data
    #     subject = "R1027J"
    #     basedir, workdir, baselinedir, imagedir = setup_directories(subject)
    #     mni_df = mapper.get_mni_coords(subject)
    #     assert len(mni_df) > 0

    @pytest.mark.rhino
    @pytest.mark.parametrize("stim_subject,bipolar_contact", [
        ('R1001P', 'LDA3-LDA4'),
        ('R1042M', 'RTG55-RTG63'), # requires building custom bipolar coords
    ])
    def test_save_mni_coords(self, stim_subject, bipolar_contact):
        stim_subject = "R1001P"
        mni_df = mapper.get_mni_coords(stim_subject)
        assert len(mni_df) > 0

        bipolar_contact = "LDA3-LDA4"
        mapper.save_mni_mid_coordinates(self.paths.workdir + "/",
                                        stim_subject, mni_df, bipolar_contact)

        outfile = stim_subject + "_electrode_coordinates_mni_mid.csv"
        assert os.path.exists(self.paths.workdir + "/" + outfile)

    def test_ct_transform(self):
        subject = "R1291M_1"
        stim_subject = "R1001P"
        mapper.CT_transform(self.paths.imagedir + "/",
                            self.paths.workdir + "/",
                            mapper.WARP_FILE,
                            mapper.GENERIC_AFFINE_TRANSFORM_FILE, subject,
                            stim_subject)

        outfile = "".join([subject, '_from_', stim_subject,
                           '_electrode_coordinates_mni_mid_tsub_CT.csv'])
        assert os.path.exists(self.paths.workdir + "/" + outfile)

    def test_t1_transform(self):
        stim_subject = "R1001P"
        mapper.T1_transform(self.paths.imagedir + "/",
                            self.paths.workdir + "/",
                            mapper.WARP_FILE,
                            mapper.GENERIC_AFFINE_TRANSFORM_FILE,
                            self.subject_id, stim_subject)

        outfile = "".join([self.subject_id, '_from_', stim_subject,
                           '_electrode_coordinates_mni_mid_tsub_T1.csv'])
        assert os.path.exists(self.paths.workdir + "/" + outfile)

    def test_get_fs_vector(self):
        stim_subject = "R1001P"
        norig = mapper.get_orig_mat(self.paths.basedir, "/vox2ras")
        torig = mapper.get_orig_mat(self.paths.basedir, "/vox2ras-tkr")

        fs_vector = mapper.get_fs_vector(self.paths.workdir + "/",
                                         self.subject_id,
                                         stim_subject, norig, torig)

        # Had to be adjusted now that we are using dysktra adjusted mni
        # coordinates
        assert np.allclose(fs_vector,
                           np.array([-24.277, 3.4594, -24.514, 1]), atol=1e-2)

    @pytest.mark.rhino
    def test_build_prior_stim_location_mapping(self):
        """ Long-running test. Do not run every time. """
        subject = "R1291M_1"
        mapper.build_prior_stim_location_mapping(self.subject_id,
                                                 self.paths.basedir,
                                                 "/data10/RAM/subjects/{}/imaging/autoloc/".format(subject))
