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


'not in use'


def predict(model, data, threshold):
    reconstructions = model(data)
    loss = tf.keras.losses.mae(reconstructions, data)
    result = np.array(tf.math.less(loss, threshold))
    return result.astype(int)
    # return tf.math.less(loss, threshold)



autoencoder = load_model('trained_models/anomaly_detection_model')
path = 'src/Training/logs/anomaly_detection/logs_Single_data_input.txt'

threshold = value_extractor("Threshold:", path)
min_val = value_extractor("Min_val:", path)
max_val = value_extractor("Max_val:", path)

raw_data = [[-78.996398,   1.512489],
            [-78.996398,   3.512489],
            [-80.996398, 15.512489]]
# raw_data = [-79.996398,   8.512489]
real_data = (np.array(raw_data) -
                        min_val) / (max_val - min_val)

# print(f'threshold is {threshold}') 0.010434809140861034 #0.03 good threshold
# print(real_data)
print(predict(autoencoder, real_data, 0.03))
