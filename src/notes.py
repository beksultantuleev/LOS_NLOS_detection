# from keras.models import load_model
from Data_collection import Listener
from time import sleep, time
# from tensorflow import keras
# from keras.models import load_model
import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder

li = np.array([1,2,3])
li2 = np.array([4,5,6])
li_concat = np.concatenate((li, li2), axis=0)
print(li_concat)
if li_concat.size!=0:
    print("yes")

