# from keras.models import load_model
from Data_collection import Listener
from time import sleep, time
# from tensorflow import keras
# from keras.models import load_model
import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder

data = pd.read_csv('data/los_nlos_cluster_dataa.txt')


def activity_modifier(number_of_activity, length_of_activity):
    if number_of_activity == 1:
        return [1]*length_of_activity
    lis = []
    for i in range(length_of_activity):
        lis.append(i)
    lis = sorted(lis*number_of_activity)[:length_of_activity]
    return lis

number_of_activity = 2
length_of_activity = data.shape[0]
actv = activity_modifier(number_of_activity, length_of_activity)
data["activity"] = actv
print(data)


