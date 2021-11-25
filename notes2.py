import numpy as np
from numpy.core.numeric import outer
from scipy.spatial import distance
import math
import pandas as pd
from src.Mqtt_manager import Mqtt_Manager
import os
import pathlib

dataframe = pd.DataFrame()
path = f"{pathlib.Path().absolute()}/data/good_nlos_data/"
for root, dirs, files in os.walk(path):
    for i in files:

        # print(i)
        data = pd.read_csv(f'data/good_nlos_data/{i}')
        dataframe = pd.concat([dataframe, data], ignore_index=True)

# print(dataframe)

# new_data = pd.concat([new_los, new_los_upclose], ignore_index=True)
# print(new_data)

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

dataframe['acquisition'] = acquisition_modifier(2, len(dataframe))

print(dataframe)
# dataframe.to_csv("data/NLOS_good_data_complete.csv", index=None)