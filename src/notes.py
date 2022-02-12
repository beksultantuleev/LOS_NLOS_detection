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


'not in use'
nlos = [4,5]
anchors = np.array([[1.00000000e+00, 4.00000000e+00, 6.55493648e+07, 1.00000000e+00],
           [2.00000000e+00, 4.00000000e+00, 6.55493308e+07, 1.00000000e+00],
           [3.00000000e+00, 4.00000000e+00, 6.55493175e+07, 1.00000000e+00],
           [4.00000000e+00, 4.00000000e+00, 6.55492778e+07, 0.00000000e+00],
           [5.00000000e+00, 4.00000000e+00, 6.55493372e+07, 0.00000000e+00]])
print(anchors)
for i in nlos:
    anchors = anchors[anchors[:, 0] != i]
print("\n new")
print(anchors)
