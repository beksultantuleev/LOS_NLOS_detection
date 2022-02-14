# from keras.models import load_model
from typing import final
from time import sleep, time
# from tensorflow import keras
# from keras.models import load_model
import pandas as pd
import numpy as np
# from Core_functions.hub_of_functions import deque_manager
from collections import deque
import tensorflow as tf
from keras.models import load_model
from Core_functions.hub_of_functions import value_extractor
import pandas as pd
from scipy.spatial.distance import cdist
from scipy.spatial import ConvexHull


los_data = pd.read_csv('data/NLOS_added_values_4_ss45000_1.csv')
# print(los_data)
los_data['F2_std_noise'] = los_data['std_noise']*10* los_data['F2_std_noise']/1000
print(los_data)
# los_data.to_csv("data/NLOS_added_values_4_ss45000_1.csv", index = False)

