# from keras.models import load_model
from typing import final
from time import sleep, time
# from tensorflow import keras
# from keras.models import load_model
import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder


data = pd.read_csv('full_dataframe_with_rx_difference.csv')

data = data[["RX_level", 'RX_difference']]
# print(data.head())
data.to_csv("data/additional_mix_data.csv", index=None)