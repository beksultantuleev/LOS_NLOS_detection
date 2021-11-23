from keras.layers import serialization
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.sparse import data
import tensorflow as tf
import pandas as pd
import time
from sklearn.metrics import accuracy_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from tensorflow.keras import layers, losses
from tensorflow.keras.datasets import fashion_mnist
from tensorflow.keras.models import Model
from keras.models import load_model
from Mqtt_manager import Mqtt_Manager
import collections
from SerialPortReader import SerialPortReader

single_data = True
via_mqtt = True

if not via_mqtt:
    serialInitiatort = SerialPortReader()

if single_data:
    autoencoder = load_model('trained_models/anomaly_detection_model')
    threshold = 0.020093761  # 0.016315665  # 0.007123868
else:
    autoencoder = load_model(
        'trained_models/anomaly_detection_model_acquisition_2')
    threshold = 0.015414234  # 0.032122597

min_val = -97.257522
max_val = 18.941238  # 3165.0


def predict(model, data, threshold):
    reconstructions = model(data)
    loss = tf.keras.losses.mae(reconstructions, data)
    return tf.math.less(loss, threshold)


if via_mqtt:
    mqtt_conn = Mqtt_Manager(
        "localhost", "allInOne")

# print(autoencoder.summary())

'with single data'
time.sleep(3)
if single_data:
    while True:
        if via_mqtt:
            data_mqtt = np.array(
                mqtt_conn.processed_data)[:-1] if mqtt_conn.processed_data else np.array([0, 0])
        else:
            data_mqtt = np.array(
                serialInitiatort.get_data(pattern="Data: ")[:-1])
        # print(data_mqtt)
        real_data = (np.array(data_mqtt) -
                     min_val) / (max_val - min_val) if len(data_mqtt)>0 else np.array([0,0])
        # print(real_data)                     
        preds = predict(autoencoder, [real_data], threshold)
        print(preds)
        msg = [1] if np.array(preds)[0] else [0]
        mqtt_conn.publish("LOS", f'{msg}')


'with multiple data'


def deque_manager_idea(number, size):
    size = size+1
    deque_test = collections.deque([])
    while len(deque_test) < size:
        mqtt_data = mqtt_conn.processed_data[number] if mqtt_conn.processed_data else 0
        deque_test.appendleft(mqtt_data)
        if len(deque_test) == size:
            deque_test.pop()
            return np.array(deque_test)


acquisition_number = 2
window_counter = 0
if not single_data:
    while True:
        'change data.processed data to data = mqtt_conn.processed_data if blah blah else [0,0,0]'
        # if data.processed_data:
        data = np.array(
            mqtt_conn.processed_data) if mqtt_conn.processed_data else np.array([0, 0])
        window_counter += 1
        RX_level = deque_manager_idea(
            0, acquisition_number)
        RX_difference = deque_manager_idea(
            1, acquisition_number)
        real_data = ((np.concatenate((RX_level, RX_difference),
                     axis=0)) - min_val) / (max_val - min_val)
        # print(real_data)
        'put here a window counter'
        if window_counter == acquisition_number:
            preds = predict(autoencoder, [real_data], threshold)
            print(preds)
            # print(real_data)
            msg = [1] if np.array(preds)[0] else [0]
            mqtt_conn.publish("LOS", f'{msg}')
            window_counter = 0
