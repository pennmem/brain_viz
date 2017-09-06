"""
Builds a table containing the previously stimulated contacts
"""

import io
import os
import requests
import pandas as pd


base_query_url = "http://rhino2.psych.upenn.edu:8080/explorer/{}/stream?format=csv&token=CML"

def build_prior_stim_results_table():
    """ Build a table containing the resulst from stimulation experiments """

    # Executes the 'stimulated_contacts' saved query
    stim_site_df = query_to_df(10)

    # Runs the recall table queries for FR, catFR, and PAL. Should be updated to
    # include TH and THR tasks in the future
    recall_table_queries = [11,12,13]
    df = pd.DataFrame()
    for query in recall_table_queries:
        temp_df = query_to_df(query)
        df = df.append(temp_df)

    merged_df = df.merge(stim_site_df, how='left', on=['subject_id', 'experiment', 'session_num'])

    merged_df["open_loop"] = (merged_df["experiment"].str.find('2') != -1)

    # Note: To get per/subject results, comment out this mapping. TODO: Make this easier
    merged_df['experiment'] = merged_df['experiment'].replace('FR2', "FR2/catFR2")
    merged_df['experiment'] = merged_df['experiment'].replace('FR3', "FR3/catFR3")
    merged_df['experiment'] = merged_df['experiment'].replace('FR5', "FR5/catFR5")
    merged_df['experiment'] = merged_df['experiment'].replace('catFR2', "FR2/catFR2")
    merged_df['experiment'] = merged_df['experiment'].replace('catFR3', "FR3/catFR3")
    merged_df['experiment'] = merged_df['experiment'].replace('catFR5', "FR5/catFR5")

    recall_df = (merged_df.groupby(by=['subject_id', 'contact_name', 'stim_list',
                                       'recalled', 'experiment'])
                          .agg({'count_recalled': 'sum',
                                'x': 'first',
                                'y': 'first',
                                'z': 'first',
                                'open_loop': 'first'})
                          .reset_index())

    # We need 6 values to calculate deltarec. There is probably a better way to do
    # this with pivot tables, but for now, I am creating six individual tables and
    # merging them all at the end.
    total_words = (recall_df.groupby(by=["subject_id", "contact_name", "experiment"])
                            .agg({"count_recalled": "sum"})
                            .reset_index()
                            .rename(columns={'count_recalled': 'num_words'}))

    total_recall = (recall_df[recall_df["recalled"] == 1].groupby(["subject_id", "contact_name", "experiment"])
                                                         .agg({"count_recalled": "sum"})
                                                         .reset_index()
                                                         .rename(columns={"count_recalled": "total_recalled"}))

    stim_words = (recall_df[recall_df["stim_list"] == 1].groupby(by=["subject_id", "contact_name", "experiment"])
                                                        .agg({"count_recalled": "sum"})
                                                        .reset_index()
                                                        .rename(columns={"count_recalled": "num_stim_words"}))

    stim_recall = recall_df[(recall_df["stim_list"] == 1) & (recall_df["recalled"] == 1)][["subject_id", "contact_name", "experiment", "count_recalled"]]
    stim_recall = stim_recall.rename(columns={'count_recalled': 'stim_recalled'})

    nonstim_words = (recall_df[recall_df["stim_list"] == 0].groupby(by=["subject_id", "contact_name", "experiment"])
                                                           .agg({"count_recalled": "sum"})
                                                           .reset_index()
                                                           .rename(columns={"count_recalled": "num_nonstim_words"}))

    nostim_recall = recall_df[(recall_df["stim_list"] == 0) & (recall_df["recalled"] == 1)][["subject_id", "contact_name", "experiment","count_recalled"]]
    nostim_recall = nostim_recall.rename(columns={'count_recalled': 'nostim_recalled'})
    nostim_recall.head()

    deltarec_df = recall_df[["subject_id", "experiment", "contact_name", "x", "y", "z"]].drop_duplicates()

    deltarec_df = deltarec_df.merge(total_words, how='left')
    deltarec_df = deltarec_df.merge(stim_words, how='left')
    deltarec_df = deltarec_df.merge(nonstim_words, how='left')
    deltarec_df = deltarec_df.merge(stim_recall, how='left')
    deltarec_df = deltarec_df.merge(nostim_recall, how='left')

    deltarec_df["deltarec"] = (100 *
         (((deltarec_df['stim_recalled'] / deltarec_df['num_stim_words']) -
           (deltarec_df['nostim_recalled'] / deltarec_df['num_nonstim_words'])) /
         ((deltarec_df['stim_recalled'] + deltarec_df['nostim_recalled']) / deltarec_df['num_words'])))


    # Re-order columns to match what Sandy's script is expecting
    deltarec_df["enhancement"] = (deltarec_df["deltarec"] > 0).map({True: "TRUE", False: "FALSE"})
    deltarec_df = deltarec_df[["subject_id", "contact_name", "experiment",
                               "deltarec", "enhancement", "x","y","z"]]
    deltarec_df["contact_name"] = deltarec_df["contact_name"].apply(fix_contact_name)

    return deltarec_df


def query_to_df(query_num):
    """ Request the results of a saved query as a dataframe """

    resp = requests.get(base_query_url.format(str(query_num)))
    data = io.BytesIO(resp.content)
    df = pd.read_csv(data)

    return df

def fix_contact_name(contact_name):
    """ Adds some space around the hypen between monopolar contact names

       Necessary for merging with other datasources that have contact names
       in this format
    """

    tokens = contact_name.split("-")
    fixed_contact_name = tokens[0] + " - " + tokens[1]

    return fixed_contact_name

