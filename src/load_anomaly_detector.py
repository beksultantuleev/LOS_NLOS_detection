import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.sparse import data
import tensorflow as tf
import pandas as pd

from sklearn.metrics import accuracy_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from tensorflow.keras import layers, losses
from tensorflow.keras.datasets import fashion_mnist
from tensorflow.keras.models import Model
from keras.models import load_model
from Mqtt_manager import Mqtt_Manager
import collections


# autoencoder = load_model('trained_models/anomaly_detection_model')
autoencoder = load_model('trained_models/anomaly_detection_model_acquisition_2')


def predict(model, data, threshold):
    reconstructions = model(data)
    loss = tf.keras.losses.mae(reconstructions, data)
    return tf.math.less(loss, threshold)


# threshold = 0.023342917
threshold = 0.037871532 #acquisition 2
min_val = -110.053703
max_val = 3165.0

# raw_data = (raw_data - min_val) / (max_val - min_val) #scaling formula


data = Mqtt_Manager(
    "localhost", "allInOne")

# print(autoencoder.summary())

'with single data'
# while True:
#     if data.processed_data:
#         real_data = (np.array(data.processed_data) -
#                      min_val) / (max_val - min_val)
#         preds = predict(autoencoder, [real_data], threshold)
#         print(preds)
#         msg = [1] if np.array(preds)[0] else [0]
#         data.publish("LOS", f'{msg}')


'with multiple data'

def deque_manager_idea(mqtt_data, size):
    size = size+1
    # for i in range(num_of_deques):
    deque_test = collections.deque([])
    while len(deque_test) < size:
        deque_test.appendleft(mqtt_data)
        if len(deque_test) == size:
            deque_test.pop()
            return np.array(deque_test)

acquisition_number = 2
window_counter = 0
while True:
    if data.processed_data:
        window_counter+=1
        CIR = deque_manager_idea(data.processed_data[0], acquisition_number)
        maxNoise = deque_manager_idea(data.processed_data[1], acquisition_number)
        RX_level = deque_manager_idea(data.processed_data[2], acquisition_number)
        FPPL = deque_manager_idea(data.processed_data[3], acquisition_number)
        real_data = ((np.concatenate((CIR, maxNoise, RX_level, FPPL), axis=0)) - min_val) / (max_val - min_val)
        # print(real_data)
        'put here a window counter'
        if window_counter == acquisition_number:
            preds = predict(autoencoder, [real_data], threshold)
            print(preds)
            # print(real_data)
            msg = [1] if np.array(preds)[0] else [0]
            data.publish("LOS", f'{msg}')
            window_counter = 0

