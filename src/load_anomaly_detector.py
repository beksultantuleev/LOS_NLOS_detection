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
from Core_functions.hub_of_functions import *
import joblib
from Managers.Deque_manager import Deque_manager

single_data = True
use_scaler = False
acquisition_number = 4

mqtt_conn = Mqtt_Manager(
    "192.168.0.119", "allInOne")



if single_data:
    if use_scaler:
        scaler = joblib.load(
            'trained_models/standard_scaler_anomaly_detection_single_data_input.save')
    autoencoder = load_model('trained_models/anomaly_detection_model')
    path = 'src/Training/logs/anomaly_detection/logs_Single_data_input.txt'

    threshold = 0.01#value_extractor("Threshold:", path) 0.008/ 0.01
    min_val = value_extractor("Min_val:", path)
    max_val = value_extractor("Max_val:", path)
else:
    if use_scaler:
        scaler = joblib.load(
            'trained_models/standard_scaler_anomaly_detection_single_data_input.save')
    autoencoder = load_model(
        'trained_models/anomaly_detection_model_acquisition_2')
    path = 'src/Training/logs/anomaly_detection/logs_Multi_data_input.txt'

    threshold = value_extractor("Threshold:", path)
    min_val = value_extractor("Min_val:", path)
    max_val = value_extractor("Max_val:", path)



def predict(model, data, threshold):
    reconstructions = model(data)
    loss = tf.keras.losses.mae(reconstructions, data)
    return tf.math.less(loss, threshold)

'with single data'
if single_data:
    while True:
        raw_data = np.array(
            mqtt_conn.processed_data)[:] if mqtt_conn.processed_data else np.array([0, 0])
        if use_scaler:
            "not finished yet"
            scaled_data = scaler.transform([raw_data])
            real_data = (np.array(raw_data) -
                        min_val) / (max_val - min_val) if len(raw_data) > 0 else np.array([0, 0])
        else:
            real_data = (np.array(raw_data) -
                        min_val) / (max_val - min_val) if len(raw_data) > 0 else np.array([0, 0])
        # print(real_data)
        preds = predict(autoencoder, [real_data], threshold)
        print(preds)
        # print(threshold)
        msg = [1] if np.array(preds)[0] else [0]
        mqtt_conn.publish("LOS", f'{msg}')
else:
    'with multiple data'
    window_counter = 0
    list_of_features = ["RX_level", "RX_difference"]
    deque_list = [0]*len(list_of_features)
    for i in range(len(list_of_features)):
        deque_list[i] = Deque_manager(acquisition_number)
    while True:
        # RX_level = deque_manager(
        #     0, acquisition_number, mqtt_conn)
        # RX_difference = deque_manager(
        #     1, acquisition_number, mqtt_conn)
        raw_data = mqtt_conn.processed_data[:] if mqtt_conn.processed_data else [0, 0]

        time.sleep(0.1)
        deque_list[0].append_data(raw_data[0])
        deque_list[1].append_data(raw_data[1])
        RX_level = deque_list[0].get_data_list()
        RX_difference = deque_list[1].get_data_list() 


        raw_data = ((np.concatenate((RX_level, RX_difference),
                    axis=0)) - min_val) / (max_val - min_val)
        if len(raw_data) == acquisition_number*len(list_of_features):
            window_counter += 1
            if window_counter == acquisition_number:
                preds = predict(autoencoder, [raw_data], threshold)
                print(preds)
                msg = [1] if np.array(preds)[0] else [0]
                mqtt_conn.publish("LOS", f'{msg}')
                window_counter = 0
