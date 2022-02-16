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


# lis = np.array([[10,15,3], [10,14,20], [5,14,21]])
# print(lis)
# print(np.mean(lis, axis=0))
# print(np.median(lis, axis=0))

lis = np.array([10, 10, 10, 4, 10, 100, 10, 3])
print(lis)
print(np.mean(lis, axis=0))
print(np.median(lis, axis=0))
