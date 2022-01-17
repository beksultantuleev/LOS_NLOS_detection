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


'not in use'
arr = np.array([[1,2,3,4], [5,6,7,8], [9,10,11,12]])
print(arr)
print("and")
arr = np.delete(arr, 0, 1)
print(arr)
# A_n1 = np.array([[0], [1], [1.8]])
# A_n2 = np.array([[6], [0], [2]])
# A_n3 = np.array([[3], [3.5], [1]])  # master
# A_n4 = np.array([[3], [5], [1]])  # master
# A_n = np.array([A_n1, A_n2, A_n3, A_n4])

# nlos = np.array([[4.00000000e+00, 6.55494275e+07, 1.00000000e+00, 1.00000000e+00],
#                  [4.00000000e+00, 6.55493618e+07, 1.00000000e+00, 4.00000000e+00]])
# los = np.array([[4.00000000e+00, 6.55494275e+07, 1.00000000e+00, 2.00000000e+00],
#                 [4.00000000e+00, 6.55493618e+07, 1.00000000e+00, 3.00000000e+00]])

# t = np.float32(65549343) * np.float32(15.65e-12)
# c = 299792458

# print(t*c)
