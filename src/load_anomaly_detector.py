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
from Managers.Mqtt_manager import Mqtt_Manager
import collections
from SerialPortReader import SerialPortReader
import joblib

def value_extractor(pattern, path):
    with open(path) as f:
        lines = f.read().splitlines()
        for i in lines:
            if pattern in i:
                value = float(i[len(pattern):])
                return value

single_data = True
via_mqtt = True

if not via_mqtt:
    serialInitiatort = SerialPortReader()

if single_data:
    autoencoder = load_model('trained_models/anomaly_detection_model')
    path = 'src/Training/logs/anomaly_detection/logs_Single_data_input.txt'
    
    threshold = value_extractor("Threshold:", path)
    min_val =  value_extractor("Min_val:", path)
    max_val = value_extractor("Max_val:", path)

else:
    autoencoder = load_model(
        'trained_models/anomaly_detection_model_acquisition_2')
    path = 'src/Training/logs/anomaly_detection/logs_Multi_data_input.txt'
    
    threshold = value_extractor("Threshold:", path)
    min_val =  value_extractor("Min_val:", path)
    max_val = value_extractor("Max_val:", path)

print(threshold)
def predict(model, data, threshold):
    reconstructions = model(data)
    loss = tf.keras.losses.mae(reconstructions, data)
    return tf.math.less(loss, threshold)



mqtt_conn = Mqtt_Manager(
    "localhost", "allInOne")


'with single data'
if single_data:
    # scaler = joblib.load('trained_models/standard_scaler_anomaly_detection_single_data_input.save')

    while True:

        data_mqtt = np.array(
            mqtt_conn.processed_data)[:] if mqtt_conn.processed_data else np.array([0, 0])

        # scaled_data = scaler.transform([data_mqtt])


        real_data = (np.array(data_mqtt) -
                     min_val) / (max_val - min_val) if len(data_mqtt) > 0 else np.array([0, 0, 0])
        # print(real_data)
        preds = predict(autoencoder, [real_data], threshold)
        print(preds)
        # print(threshold)
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
