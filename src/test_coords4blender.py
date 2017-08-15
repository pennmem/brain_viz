import os
import numpy as np
import pandas as pd
import subprocess
from coords4blender import save_coords_for_blender

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
