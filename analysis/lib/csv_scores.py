

""" This library contains functions related to manipulating pairwise scores 
based on the structure of the csv UCLA has sent us."""


import os
import numpy as np
import pandas as pd
import collections
import random
import time
import choix
from sklearn.preprocessing import MinMaxScaler
import os
from PIL import Image
from scipy import stats


def MapImagesToIndexes(df):
    """Given a panda data frame of the data, creates a 
    dictonary mapping image names to ints and vice versa """
    image_ids = list(set(df['image1'].tolist() + df['image2'].tolist()))
    int_to_idx = dict(enumerate(image_ids))
    idx_to_int = dict((v, k) for k, v in int_to_idx.items())
    return int_to_idx, idx_to_int

def GenrateChoixData(df, idx_to_int):
    """ make data for choix.opt_pairwise given a dataframe and 
    a dict mapping image names to ints """
    pairs = []
    for row in df.iterrows():
        id1 = idx_to_int[row[1]['image1']]
        id2 = idx_to_int[row[1]['image2']]
        win1 = row[1]['win1']
        win2 = row[1]['win2']
        tie = row[1]['tie']
        for _ in range(win1):
            pairs.append((id1, id2))
            pairs.append((id1, id2))
        for _ in range(win2):
            pairs.append((id2, id1))
            pairs.append((id2, id1))
        for _ in range(tie):
            pairs.append((id1, id2))
            pairs.append((id2, id1))
    return pairs

def GenerateChoixScores(df_in, csvPath = ''):
    """ Given a data frame, it calculates the Choix scores for those pairs and 
    outputs it to a csv file given in the csvPath argument"""
    int_to_idx, idx_to_int = MapImagesToIndexes(df_in)
    n_items = len(idx_to_int)
    pairs = GenrateChoixData(df_in, idx_to_int)
    start_time = time.time()
    params = choix.opt_pairwise(n_items, pairs)
    df = pd.DataFrame(params)
    df['fname'] = [int_to_idx[i] for i in df.index]
    if csvPath != '':
        df.to_csv(csvPath)
    else:
        return df
    print(time.time() - start_time)
    
def ReadScoresFromCsv(csvPath):
    """ reads scores from a csv file """
    df = pd.read_csv(csvPath, index_col=0)
    df.columns = ['violence', 'fname']
    return df

def MinMax(df, column):
    """ Performs a min max operation into a dataframe column specified using a string"""
    df_result = df.copy()
    v = np.matrix(df_result[column])
    scaler = MinMaxScaler()
    df_result[column] = scaler.fit_transform(v.T)
    return df_result

def ClipValues(df, cutpoint): 
    """Given a data frame with a column named violence, clips the values based on a cutpoint """
    df_result = df.copy()
    ix_large = df_result[df_result['violence'] > cutpoint].index
    df_result.loc[ix_large, 'violence'] = cutpoint
    return df_result
