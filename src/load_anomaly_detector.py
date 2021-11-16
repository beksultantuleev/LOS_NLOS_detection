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

single_data = True

if single_data:
    autoencoder = load_model('trained_models/anomaly_detection_model')
    threshold = 0.016315665#0.007123868
else:
    autoencoder = load_model('trained_models/anomaly_detection_model_acquisition_2')
    threshold = 0.015414234#0.032122597

min_val = -96.890289
max_val = 18.303719#3165.0

def predict(model, data, threshold):
    reconstructions = model(data)
    loss = tf.keras.losses.mae(reconstructions, data)
    return tf.math.less(loss, threshold)


data = Mqtt_Manager(
    "localhost", "allInOne")

# print(autoencoder.summary())

'with single data'
if single_data:
    while True:
        if data.processed_data:
            real_data = (np.array(data.processed_data) -
                        min_val) / (max_val - min_val)
            preds = predict(autoencoder, [real_data], threshold)
            print(preds)
            msg = [1] if np.array(preds)[0] else [0]
            data.publish("LOS", f'{msg}')


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
if not single_data:
    while True:
        if data.processed_data:
            window_counter+=1
            # maxNoise = deque_manager_idea(data.processed_data[0], acquisition_number)
            RX_level = deque_manager_idea(data.processed_data[0], acquisition_number)
            RX_difference = deque_manager_idea(data.processed_data[1], acquisition_number)
            real_data = ((np.concatenate((RX_level, RX_difference), axis=0)) - min_val) / (max_val - min_val)
            # print(real_data)
            'put here a window counter'
            if window_counter == acquisition_number:
                preds = predict(autoencoder, [real_data], threshold)
                print(preds)
                # print(real_data)
                msg = [1] if np.array(preds)[0] else [0]
                data.publish("LOS", f'{msg}')
                window_counter = 0
                

