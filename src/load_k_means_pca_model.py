from matplotlib import scale
import pandas as pd
from sklearn.cluster import KMeans
import numpy as np
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
from collections import Counter
from sklearn.preprocessing import StandardScaler
import joblib
from Managers.Mqtt_manager import Mqtt_Manager
import collections
import time



"kmeans + pca"
use_scaler = False
single_data = False
acquisition_number = 4
"acquisition 4 and multiple data works good"

if single_data:
    pca_model = joblib.load('trained_models/pca.sav')
    k_means_model = joblib.load('trained_models/k_means.sav')
    if use_scaler:
        scaler = joblib.load('trained_models/standard_scaler_pca_kmeans.save')
else:
    pca_model = joblib.load(f'trained_models/pca_by_acquisition_{acquisition_number}.sav')
    k_means_model = joblib.load(f'trained_models/k_means_by_acquisition_{acquisition_number}.sav')
    if use_scaler:
        scaler = joblib.load(f'trained_models/standard_scaler_pca_kmeans_by_acquisition_{acquisition_number}.save')

mqtt_conn = Mqtt_Manager(
    "localhost", "allInOne")

def deque_manager(number, size):
    'updated deque manager, new values at the end of deque'
    size = size+1
    deque_test = collections.deque([])
    while len(deque_test) < size:
        time.sleep(0.01) #to see updates in deques
        mqtt_data = mqtt_conn.processed_data[number] if mqtt_conn.processed_data else 0
        # deque_test.appendleft(mqtt_data)
        deque_test.append(mqtt_data)
        if len(deque_test) == size:
            # deque_test.pop()
            deque_test.popleft()
            return np.array(deque_test)

'for single data'
if single_data:
    while True:
        raw_data = mqtt_conn.processed_data[:] if mqtt_conn.processed_data else [0, 0]
        if use_scaler:
            scaled_data = scaler.transform([raw_data])
            df = pca_model.transform(scaled_data)
            # print(scaled_data)
        else:
            df = pca_model.transform([raw_data])

        # print(df)
        pred = k_means_model.predict(df)
        mqtt_conn.publish("LOS", f'{pred}')
        print(pred)
else:
    'for multiple data'
    window_counter = 0
    list_of_features = ["RX_level", "RX_difference"]
    while True:
        transmission = deque_manager(0, acquisition_number)
        RX_level = deque_manager(1, acquisition_number)
        RX_difference = deque_manager(2, acquisition_number)
        raw_data = np.concatenate((transmission, RX_level), axis=0)
        print(raw_data)


        # RX_level = deque_manager(0, acquisition_number)
        # RX_difference = deque_manager(1, acquisition_number)
        # raw_data = np.concatenate((RX_level, RX_difference), axis=0)
        # # print(new_data)
        # if use_scaler:
        #     scaled_data = scaler.transform([raw_data])
        #     df = pca_model.transform(scaled_data)
        #     # print(scaled_data)
        #     # print(df)
        # else:
        #     df = pca_model.transform([raw_data])
        # # print(df)
        # window_counter += 1
        # if window_counter == acquisition_number:
        #     # print(new_data)
        #     pred = k_means_model.predict(df)
        #     mqtt_conn.publish("LOS", f'{pred}')
        #     print(pred)
        #     window_counter = 0

