import os
import numpy as np
import pandas as pd
import subprocess

from src.coords4blender import save_coords_for_blender, extract_lead_and_num


def test_extract_lead_and_num():
    assert extract_lead_and_num("LAD1") == ("LAD", 1)
    assert extract_lead_and_num("LAD41") == ("LAD", 41)
    assert extract_lead_and_num("RHLD1-RHLD2") == ("RHLD", 1)
    assert extract_lead_and_num("HTYX28-HTYX28") == ("HTYX", 28)
    assert extract_lead_and_num("1TAL2") == ("1TAL", 2)
    assert extract_lead_and_num("23TAL9") == ("23TAL", 9)
    assert extract_lead_and_num("11ABC8-11ABC9") == ("11ABC", 8)
    return

def test_output_produced():
    subject = "R1338T"
    basedir = os.path.dirname(os.path.dirname(os.path.realpath(__file__))) + "/test_data/{}/".format(subject)
    save_coords_for_blender("R1338T",
                            basedir,
                            localization_file=basedir + "/localization.json")
    assert os.path.exists(basedir + "electrode_coordinates.csv")
    return
