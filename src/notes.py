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


lis = np.array([[1,2,3], [4,5,6]])
print(lis)
np.random.shuffle(lis)
print(lis)

