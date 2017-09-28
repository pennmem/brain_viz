import os
import json
import sys
import itertools
import pandas as pd
from ptsa.data.readers import TalReader


LOCALIZATION = "/protocols/r1/subjects/{}/localizations/{}/montages/{}/neuroradiology/current_processed/localization.json"


def save_coords_for_blender(subject, outdir, localization_file=None):
    if localization_file is not None:
        LOCALIZATION = localization_file
    localization = guess_localization(subject)
    montage = guess_montage(subject, localization)
    localization_data = read_json(LOCALIZATION.format(subject, localization, montage))
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

    orig_df = localization_df[["contact_name", "contact_type", "x_orig", "y_orig", "z_orig"]]
    orig_df.columns = ["contact_name", "contact_type", "x", "y", "z"]
    orig_df["atlas"] = "orig"

    adj_df = localization_df[["contact_name", "contact_type", "x_adj", "y_adj", "z_adj"]]
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
    # Scaling factor
    for col in ['x', 'y', 'z']:
        final_df[col] = 0.02 * final_df[col]

    final_df = add_orientation_contact_for_depth_electrodes(final_df)
    final_df = final_df[["contact_name", "contact_type", "x", "y", "z", "atlas", "orient_to"]]
    final_df.to_csv(outdir + "/electrode_coordinates.csv", index=False)

    return final_df

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

def guess_montage(subject, localization):
    if subject.find("_") == -1:
        montages = os.listdir("/protocols/r1/subjects/%s/"\
                              "localizations/%s/montages" %
                              (subject, localization))
        montage = montages[0] # just use the first one

    else:
       tokens = subject.split("_")
       montage = tokens[-1]

    return montage


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
