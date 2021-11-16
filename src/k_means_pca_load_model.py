from matplotlib import scale
import pandas as pd
from sklearn.cluster import KMeans
import numpy as np
from sklearn.decomposition import PCA
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
from collections import Counter
from sklearn.preprocessing import StandardScaler
import joblib
from Mqtt_manager import Mqtt_Manager
import collections

"kmeans + pca"

# data = pd.read_csv('data/raw/data_ss1000000_NLOS_1.txt')
# data = data.drop(["Unnamed: 0", "activity"], axis=1)

# scaler = StandardScaler()
# scaler.fit(data)
# scaled_data = scaler.transform(data)

# pca_model = joblib.load('trained_models/pca.sav')
pca_model = joblib.load('trained_models/pca_by_acquisition_4.sav')
# k_means_model = joblib.load('trained_models/k_means.sav')
k_means_model = joblib.load('trained_models/k_means_by_acquisition_4.sav')

# df = pca_model.transform([data.iloc[4]])
# print(df)
# pred = k_means_model.predict(df)
# print(pred)

data = Mqtt_Manager(
    "localhost", "allInOne")

'for single data'
# while True:
#     if data.processed_data:
#         # print(data.processed_data)
#         df = pca_model.transform([data.processed_data])
#         # print(df)
#         pred = k_means_model.predict(df)
#         print(pred)

'for multiple data'
list_of_features = ["CIR", "FirstPathPL","maxNoise", "RX_level", "FPPL"]

def deque_manager_idea(mqtt_data, size):
    size = size+1
    # for i in range(num_of_deques):
    deque_test = collections.deque([])
    while len(deque_test) < size:
        deque_test.appendleft(mqtt_data)
        if len(deque_test) == size:
            deque_test.pop()
            return np.array(deque_test)

acquisition_number = 4
while True:
    if data.processed_data:
        CIR = deque_manager_idea(data.processed_data[0], acquisition_number)
        FirstPathPL = deque_manager_idea(data.processed_data[1], acquisition_number)
        maxNoise = deque_manager_idea(data.processed_data[2], acquisition_number)
        RX_level = deque_manager_idea(data.processed_data[3], acquisition_number)
        FPPL = deque_manager_idea(data.processed_data[4], acquisition_number)

        new_data = np.concatenate((CIR, FirstPathPL, maxNoise, RX_level, FPPL), axis=0)
        # print(new_data)

        df = pca_model.transform([new_data])
        # print(df)
        pred = k_means_model.predict(df)
        print(pred)
