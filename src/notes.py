# from keras.models import load_model
from typing import final
from Data_collection import Listener
from time import sleep, time
# from tensorflow import keras
# from keras.models import load_model
import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder

data = pd.read_csv('data/los_nlos_cluster_dataa.txt')

def acquisition_modifier(acquisition_number, length_of_acquisitions):
    if acquisition_number == 1:
        return [1]*length_of_acquisitions
    elif acquisition_number == 0:
        return [0]*length_of_acquisitions
    lis = []
    for i in range(length_of_acquisitions):
        lis.append(i)
    lis = sorted(lis*acquisition_number)[:length_of_acquisitions]
    return lis

data['acquisition'] = acquisition_modifier(4, data.shape[0])
# print(data)

def dataset_configuration(dataset, list_of_independent_vars, acquisition="acquisition"):
    for acq_index in range(1, max(np.unique(dataset[acquisition]))+1):
        temp = dataset[dataset[acquisition] == acq_index]
    dataset['idx'] = dataset.groupby(acquisition).cumcount()

    final_dataframe = dataset.pivot_table(index=acquisition, columns='idx')[
        list_of_independent_vars]
    print(final_dataframe)
    return final_dataframe

list_of_independent_vars=["CIR", "FirstPathPL", "maxNoise", "RX_level", "FPPL"]

# dataset_configuration(data, list_of_independent_vars).to_csv('data/los_nlos_cluster_by_acquisition_4.csv', index= None)

# print(list(data.columns))


