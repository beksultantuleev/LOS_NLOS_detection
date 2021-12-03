# from keras.models import load_model
from typing import final
from time import sleep, time
# from tensorflow import keras
# from keras.models import load_model
import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder


def dataset_configuration(dataset, list_of_independent_vars, acquisition="acquisition"):
    for acq_index in range(1, max(np.unique(dataset[acquisition]))+1):
        temp = dataset[dataset[acquisition] == acq_index]
    dataset['idx'] = dataset.groupby(acquisition).cumcount()

    final_dataframe = dataset.pivot_table(index=acquisition, columns='idx')[
        list_of_independent_vars]
    # print(final_dataframe)
    return final_dataframe

data = pd.read_csv('data/transmission_test_4_ss4000_2.csv')
list_of_features = ["transmission", "RX_level", "RX_difference","CIR","F1","F2","F3"]
new_data = dataset_configuration(data, list_of_independent_vars=list_of_features)
new_data.to_csv("after_transformation.csv", index=None)