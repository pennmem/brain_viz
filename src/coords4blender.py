import os
import sys
import pandas as pd

sys.path.insert(0, "/home1/zduey/ptsa/")
from ptsa.data.readers import TalReader


TALSTRUCT = "/data10/RAM/subjects/{}/tal/{}_talLocs_database_{}.mat"

def save_coords_for_blender(subject, outdir):
    bipol_reader = TalReader(filename=TALSTRUCT.format(subject, subject, 'bipol'),
                             struct_type = 'bi')
    bipol_structs = bipol_reader.read()

    mono_reader = TalReader(filename=TALSTRUCT.format(subject, subject, 'monopol'),
                            struct_type = 'mono')
    mono_structs = mono_reader.read()

    mono_start_df = get_coords(mono_structs, 'monopolar')
    mono_adj_df = get_coords(mono_structs, 'monopolar', atlas='Dykstra')
    bipo_adj_df = get_coords(bipol_structs, 'bipolar', atlas='Dykstra')

    all_coord_df = pd.concat([mono_start_df, mono_adj_df, bipo_adj_df])
    # Scale coordinates
    for col in ['x', 'y', 'z']:
        all_coord_df[col] = 0.02 * all_coord_df[col]

    all_coord_df.to_csv(outdir + "electrode_coordinates.csv", index=False)

    return


def get_coords(talStruct, elec_type, atlas=None):
    if atlas is None:
        df = pd.DataFrame(columns=['contact_name' , 'contact_type', 'x', 'y', 'z'],
                             data={'contact_name' : talStruct['tagName'],
                                   'contact_type' : talStruct['eType'],
                                   'x' : talStruct['x'],
                                   'y' : talStruct['y'],
                                   'z' : talStruct['z']}
                          )
        df['atlas'] = elec_type + '_orig'
        return df

    df = pd.DataFrame(columns=['contact_name' , 'contact_type', 'x', 'y', 'z'],
                      data={'contact_name' : talStruct['tagName'],
                            'contact_type' : talStruct['eType'],
                            'x' : talStruct['indivSurf']['x_' + atlas],
                            'y' : talStruct['indivSurf']['y_' + atlas],
                            'z' : talStruct['indivSurf']['z_' + atlas]}
                     )
    df['atlas'] = elec_type + '_dykstra'


    return df

