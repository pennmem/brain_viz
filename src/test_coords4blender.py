import os
import numpy as np
import pandas as pd
import subprocess
from coords4blender import save_coords_for_blender, extract_lead_and_num

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
    save_coords_for_blender("R1338T",
                            "/home1/zduey/brain_viz/test_data/R1338T/",
                            localization_file="/home1/zduey/brain_viz/test_data/R1338T/localization.json")
    assert os.path.exists("/home1/zduey/brain_viz/test_data/R1338T/electrode_coordinates.csv")
    return
