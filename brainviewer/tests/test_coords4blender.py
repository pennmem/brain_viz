import os
import pytest
import functools

from pkg_resources import resource_filename
from brainviewer.coords4blender import (
    save_coords_for_blender, extract_lead_and_num
)

datafile = functools.partial(resource_filename, "brainviewer.tests.data")


def test_extract_lead_and_num():
    assert extract_lead_and_num("LAD1") == ("LAD", 1)
    assert extract_lead_and_num("LAD41") == ("LAD", 41)
    assert extract_lead_and_num("RHLD1-RHLD2") == ("RHLD", 1)
    assert extract_lead_and_num("HTYX28-HTYX28") == ("HTYX", 28)
    assert extract_lead_and_num("1TAL2") == ("1TAL", 2)
    assert extract_lead_and_num("23TAL9") == ("23TAL", 9)
    assert extract_lead_and_num("11ABC8-11ABC9") == ("11ABC", 8)
    return


def test_localization_extraction():
    basedir = datafile("R1338T/")
    output_file = datafile("R1338T/electrode_coordinates.csv")
    input_loc_file = datafile("R1338T/localization.json")
    save_coords_for_blender("R1338T",
                            0,
                            basedir,
                            localization_file=input_loc_file)
    assert os.path.exists(output_file)
    os.remove(output_file)


@pytest.mark.rhino
def test_talstruct_extraction(rhino_root):
    basedir = datafile("output/")
    output_file = datafile("output/electrode_coordinates.csv")
    save_coords_for_blender("R1001P",
                            0,
                            basedir,
                            rootdir=rhino_root)
    assert os.path.exists(output_file)
    os.remove(output_file)
