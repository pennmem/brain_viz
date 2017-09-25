import os
import sys
import pandas as pd
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
    mono_start_df["contact_name"] = "o" + mono_start_df["contact_name"]

    mono_adj_df = get_coords(mono_structs, 'monopolar', atlas='Dykstra')

    bipo_adj_df = get_coords(bipol_structs, 'bipolar', atlas='Dykstra')

    all_coord_df = pd.concat([mono_start_df, mono_adj_df, bipo_adj_df])
    # Scale coordinates
    for col in ['x', 'y', 'z']:
        all_coord_df[col] = 0.02 * all_coord_df[col]

    all_coord_df = add_orientation_contact_for_depth_electrodes(all_coord_df)
    all_coord_df = all_coord_df[["contact_name", "contact_type", "x", "y", "z", "atlas", "orient_to"]]
    all_coord_df.to_csv(outdir + "/electrode_coordinates.csv", index=False)

    return


def get_coords(talStruct, elec_type, atlas=None):
    if atlas is None:
        df = pd.DataFrame(columns=['contact_name' , 'contact_type', 'x', 'y', 'z'],
                             data={'contact_name' : talStruct['tagName'],
                                   'contact_type' : talStruct['eType'],
                                   'x' : talStruct['indivSurf']['x'],
                                   'y' : talStruct['indivSurf']['y'],
                                   'z' : talStruct['indivSurf']['z']}
                          )
        df['atlas'] = elec_type + '_orig'
        return df

    # Dykstra coordinates will be empty for subjects with only depths. Use
    # tal coordinates instead in these cases
    if (set(talStruct["eType"]) == {"D"}):
        df = pd.DataFrame(columns=['contact_name' , 'contact_type', 'x', 'y', 'z'],
                             data={'contact_name' : talStruct['tagName'],
                                   'contact_type' : talStruct['eType'],
                                   'x' : talStruct['indivSurf']['x'],
                                   'y' : talStruct['indivSurf']['y'],
                                   'z' : talStruct['indivSurf']['z']}
                          )
        df['atlas'] = elec_type + '_dykstra'
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

def extract_group_num(contact_name):
    found_start = False
    if contact_name.find('-') != -1:
        contact_name = contact_name[0 : contact_name.find('-')]

    # Iterate over name from the end until integer conversion fails
    name_length = len(contact_name)
    found_start = False
    for i in range(1 , name_length + 1):
        try:
            int_rep = int(contact_name[name_length - i])
            continue
        except ValueError as e:
            found_start = True
            start_index = name_length - i
        if found_start:
            break
    group = contact_name[:start_index + 1]
    num = int(contact_name[start_index + 1:])
    return group, num

def add_orientation_contact_for_depth_electrodes(all_coord_df):
    all_coord_df["group"] = all_coord_df["contact_name"].apply(lambda x: extract_group_num(x)[0])
    all_coord_df["num"] = all_coord_df["contact_name"].apply(lambda x: extract_group_num(x)[1])
    max_num_df = (all_coord_df.groupby(by=["group"])
                              .agg({"num":max})
                              .reset_index()
                              .rename(columns={"num":"max_num"})
                 )
    all_coord_df = all_coord_df.merge(max_num_df)
    all_coord_df["depth"] = (all_coord_df["contact_type"].str.find("D") != -1)
    all_coord_df["bipolar"] = (all_coord_df["contact_name"].str.find('-') != -1)
    all_coord_df["num_str"] = all_coord_df["num"].astype(str)
    all_coord_df["num_plus_one"] = all_coord_df["num"].apply(lambda x: str(x + 1))
    all_coord_df["num_plus_two"] = all_coord_df["num"].apply(lambda x: str(x + 2))

    all_coord_df["bipolar_orient_to"] = (all_coord_df["group"] +
                                         all_coord_df["num_plus_one"] +
                                         "-" +
                                         all_coord_df["group"] +
                                         all_coord_df["num_plus_two"])
    all_coord_df["monopolar_orient_to"] = (all_coord_df["group"] +
                                           all_coord_df["num_plus_one"])

    all_coord_df['orient_to'] = None
    all_coord_df.loc[(all_coord_df["bipolar"] == True) &
                     (all_coord_df["depth"] == True) &
                     (all_coord_df["num"] < all_coord_df["max_num"] - 1),
                     "orient_to"] = all_coord_df.loc[(all_coord_df["bipolar"] == True) &
                                                     (all_coord_df["depth"] == True) &
                                                     (all_coord_df["num"] < all_coord_df["max_num"] - 1),
                                                     "bipolar_orient_to"]
    all_coord_df.loc[(all_coord_df["bipolar"] == False) &
                     (all_coord_df["depth"] == True) &
                     (all_coord_df["num"] < all_coord_df["max_num"]),
                     "orient_to"] = all_coord_df.loc[(all_coord_df["bipolar"] == False) &
                                                     (all_coord_df["depth"] == True) &
                                                     (all_coord_df["num"] < all_coord_df["max_num"]),"monopolar_orient_to"]


    return all_coord_df
