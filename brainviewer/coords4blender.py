import os
import json
import itertools
import pandas as pd

from ptsa.data.readers import TalReader
from typing import Optional
from cmlreaders.path_finder import PathFinder


OBJ_SCALE_FACTOR = 0.02


def save_coords_for_blender(subject_id: str, localization: int, outdir: str,
                            localization_file: Optional[str] = None,
                            rootdir: Optional[str] = "/"):
    """
        Generates a CSV file with metadata about contacts in the subject's
        montage

    Parameters
    ----------
    subject_id: str
        ID of the subject
    localization: int
        Localization number of the subject to use
    outdir: str
        Directory to save the resulting file
    localization_file: str, default None
        Default is to look up the localization file to use, but if specified,
        uses the passed file location
    rootdir: str
        Mount point for RHINO

    Returns
    -------
    saved_results_path: str

    """
    use_matlab = False
    if localization_file is None:
        finder = PathFinder(subject=subject_id, localization=localization,
                            rootdir=rootdir)
        try:
            localization_file = finder.find('localization')
        except FileNotFoundError:
            use_matlab = True

    if use_matlab or not os.path.exists(localization_file):
        # get coordinates from matlab talstruct
        subject_localization = subject_id
        if localization != 0:
            subject_localization = "_".join([subject_id, str(localization)])
        final_df = extract_coordinates_from_talstructs(subject_localization,
                                                       rootdir=rootdir)
    else:
        # get coordinates from the new localization.json file
        final_df = extract_coordinates_from_localization_file(localization_file)

    # Scale coordinates
    for col in ['x', 'y', 'z']:
        final_df[col] = OBJ_SCALE_FACTOR * final_df[col]

    final_df = add_orientation_contact_for_depth_electrodes(final_df)
    final_df = final_df[["contact_name", "contact_type", "x", "y", "z",
                         "atlas", "orient_to"]]
    final_df.to_csv(outdir + "/electrode_coordinates.csv", index=False)

    return os.path.join(outdir, "electrode_coordinates.csv")


def extract_coordinates_from_localization_file(localization_file):
    localization_data = read_json(localization_file)
    localization_df = json_to_dataframe(localization_data)
    localization_df["contact_name"] = localization_df["name"]
    localization_df.loc[localization_df["contact_name"].isnull(),
                        "contact_name"] = (localization_df.loc[localization_df["contact_name"].isnull(),
                                                               "names"].apply(monopolars_to_bipolar))
    localization_df["lead"] = localization_df["contact_name"].apply(lambda x: extract_lead_and_num(x)[0])
    type_map = get_lead_to_type_mapping(localization_data)
    localization_df["contact_type"] = localization_df["lead"].map(type_map)
    localization_df = localization_df[["contact_name", "contact_type",
                                       "coordinate_spaces.fs.corrected",
                                       "coordinate_spaces.fs.raw"]]
    localization_df["x_orig"] = localization_df["coordinate_spaces.fs.raw"].apply(lambda x: x[0])
    localization_df["y_orig"] = localization_df["coordinate_spaces.fs.raw"].apply(lambda x: x[1])
    localization_df["z_orig"] = localization_df["coordinate_spaces.fs.raw"].apply(lambda x: x[2])
    localization_df["x_adj"] = localization_df["coordinate_spaces.fs.corrected"].apply(lambda x: x[0])
    localization_df["y_adj"] = localization_df["coordinate_spaces.fs.corrected"].apply(lambda x: x[1])
    localization_df["z_adj"] = localization_df["coordinate_spaces.fs.corrected"].apply(lambda x: x[2])

    orig_df = localization_df[["contact_name", "contact_type", "x_orig",
                               "y_orig", "z_orig"]]
    orig_df.columns = ["contact_name", "contact_type", "x", "y", "z"]
    orig_df["atlas"] = "orig"

    adj_df = localization_df[["contact_name", "contact_type", "x_adj",
                              "y_adj", "z_adj"]]
    adj_df.columns = ["contact_name", "contact_type", "x", "y", "z"]
    adj_df["atlas"] = "dykstra"

    final_df = pd.concat([orig_df, adj_df])
    final_df["is_monopolar"] = final_df["contact_name"].apply(is_monopolar)
    final_df.loc[final_df["is_monopolar"] == True, "atlas"] = "monopolar_" + final_df.loc[final_df["is_monopolar"] == True, "atlas"]
    final_df.loc[final_df["is_monopolar"] == False, "atlas"] = "bipolar_" + final_df.loc[final_df["is_monopolar"] == False, "atlas"]
    final_df = final_df[final_df["atlas"] != "bipolar_orig"]

    # Add 'o' to original monopolar coordinates
    final_df.loc[final_df["atlas"] == "monopolar_orig",
                 "contact_name"] = "o" + final_df.loc[final_df["atlas"] == "monopolar_orig",
                                                      "contact_name"]

    return final_df


def extract_coordinates_from_talstructs(subject_localization, rootdir="/"):
    talstruct_base_path = os.path.join(rootdir,
                                       "data10/RAM/subjects/{}/tal/{}_talLocs_database_{}.mat")

    # TODO: Use PathFinder once the matlab talstructs are available
    bipol_reader = TalReader(filename=talstruct_base_path.format(subject_localization,
                                                                 subject_localization,
                                                                 'bipol'),
                             struct_type='bi')
    bipol_structs = bipol_reader.read()

    mono_reader = TalReader(filename=talstruct_base_path.format(subject_localization,
                                                                subject_localization,
                                                                'monopol'),
                            struct_type='mono')
    mono_structs = mono_reader.read()

    mono_start_df = get_coords(mono_structs, 'monopolar')
    mono_start_df["contact_name"] = "o" + mono_start_df["contact_name"]

    mono_adj_df = get_coords(mono_structs, 'monopolar', atlas='Dykstra')

    bipo_adj_df = get_coords(bipol_structs, 'bipolar', atlas='Dykstra')

    all_coord_df = pd.concat([mono_start_df, mono_adj_df, bipo_adj_df])

    return all_coord_df


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


def is_monopolar(contact_name):
    """ Utility function to determine if contact is monopolar from the name

    Parameters
    ----------
    contactname: str

    Returns
    -------
    bool

    """
    if contact_name.find("-") == -1:
        return True
    return False


def monopolars_to_bipolar(monopolar_array):
    """ Generated bipolar contact name from array of monopolar names

    Parameters
    ----------
    monopolar_array: array

    Returns
    ------
    str

    """
    return "-".join(monopolar_array)


def extract_lead_and_num(contact_name):
    """ Given a contact name, extract the lead name and contact number

    Parameters
    ----------
    contact_name : str

    Returns
    ------
    (str, int)

    """
    if contact_name.find('-') != -1:
        contact_name = contact_name[0 : contact_name.find('-')]

    # Iterate over name from the end until integer conversion fails
    name_length = len(contact_name)
    found_start = False
    for i in range(1, name_length + 1):
        try:
            int_rep = int(contact_name[name_length - i])
            continue
        except ValueError as e:
            found_start = True
            start_index = name_length - i
        if found_start:
            break
    lead = contact_name[:start_index + 1]
    num = int(contact_name[start_index + 1:])
    return lead, num


def json_to_dataframe(localization_data):
    leads = localization_data["leads"].values()
    flat_contact_data = list(itertools.chain(*[x["contacts"] for x in leads]))
    flat_pairs_data = list(itertools.chain(*[x["pairs"] for x in leads]))
    all_data = []
    all_data.append(pd.io.json.json_normalize(flat_contact_data))
    all_data.append(pd.io.json.json_normalize(flat_pairs_data))
    combined_df = pd.concat(all_data)
    return combined_df


def get_lead_to_type_mapping(localization_data):
    leads = localization_data["leads"].keys()
    types = [localization_data["leads"][lead]["type"] for lead in leads]
    type_map = dict(zip(leads, types))
    return type_map


def guess_localization(subject):
    if subject.find("_") == -1:
        localization = "0"

    else:
        tokens = subject.split("_")
        localization = tokens[-1]

    return localization


def read_json(filepath):
    f = open(filepath, "r")
    json_data = json.load(f)
    f.close()
    return json_data


def add_orientation_contact_for_depth_electrodes(all_coord_df):
    all_coord_df["group"] = all_coord_df["contact_name"].apply(lambda x: extract_lead_and_num(x)[0])
    all_coord_df["num"] = all_coord_df["contact_name"].apply(lambda x: extract_lead_and_num(x)[1])
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
