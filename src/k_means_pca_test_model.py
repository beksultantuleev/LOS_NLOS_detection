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

"kmeans + pca"

# data = pd.read_csv('data/raw/data_ss1000000_NLOS_1.txt')
# data = data.drop(["Unnamed: 0", "activity"], axis=1)

# scaler = StandardScaler()
# scaler.fit(data)
# scaled_data = scaler.transform(data)

pca_model = joblib.load('trained_models/pca.sav')
k_means_model = joblib.load('trained_models/k_means.sav')

# df = pca_model.transform([data.iloc[4]])
# print(df)
# pred = k_means_model.predict(df)
# print(pred)

data = Mqtt_Manager(
    "localhost", "allInOne")

while True:
    if data.processed_data:
        # print(data.processed_data)
        df = pca_model.transform([data.processed_data])
        # print(df)
        pred = k_means_model.predict(df)
        print(pred)
