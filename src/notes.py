# from keras.models import load_model
from Data_collection import Listener
from time import sleep
# from tensorflow import keras
from keras.models import load_model
import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder

dataset = pd.read_csv("data/motion_recognition.csv")

dataset = dataset.drop(["Unnamed: 0"], axis=1)

lbl_encode = LabelEncoder()

for col in dataset:
    if dataset[col].dtype.name == "object":
        try:
            dataset[col] = lbl_encode.fit_transform(
                dataset[col])
        except:
            pass

print(dataset)


