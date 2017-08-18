import os
import numpy as np
import pandas as pd
import subprocess
from coords4blender import save_coords_for_blender, extract_group_num


def test_matlab_python_match():
    subject = "R1291M_1"
    output = "/home1/zduey/brain_viz/test_data/{}/coords_baseline/".format(subject)

    command = 'matlab -r "coords4blender(\'' + subject + '\',\'' + output + '\'); exit;"'
    subprocess.run(command, shell=True)
    save_coords_for_blender(subject, output)

    assert os.path.exists(output + "electrode_coordinates.csv")

    matlab_mono_df = pd.read_table(output + "monopolar_blender.txt", sep="\t", header=None)
    matlab_mono_coords = matlab_mono_df[[1,2,3]].values

    matlab_bipol_df = pd.read_table(output + "bipolar_blender.txt", sep="\t", header=None)
    matlab_bipol_coords = matlab_bipol_df[[1,2,3]].values

    python_coord_df = pd.read_csv(output + "electrode_coordinates.csv")
    python_mono_coords = python_coord_df[python_coord_df["atlas"] == "monopolar_dykstra"][["x", "y","z"]].values
    python_bipol_coords = python_coord_df[python_coord_df["atlas"] == "bipolar_dykstra"][["x", "y", "z"]].values

    assert np.allclose(python_mono_coords, matlab_mono_coords, atol=1e-1)
    assert np.allclose(python_bipol_coords, matlab_bipol_coords, atol=1e-1)

    return

def test_extract_group_num():
    assert extract_group_num("LAD1") == ("LAD", 1)
    assert extract_group_num("LAD41") == ("LAD", 41)
    assert extract_group_num("RHLD1-RHLD2") == ("RHLD", 1)
    assert extract_group_num("HTYX28-HTYX28") == ("HTYX", 28)
    assert extract_group_num("1TAL2") == ("1TAL", 2)
    assert extract_group_num("23TAL9") == ("23TAL", 9)
    assert extract_group_num("11ABC8-11ABC9") == ("11ABC", 8)
    return
