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

los_data = pd.read_csv('data/LOS_2_ss25000_1.csv')
los_data = los_data.drop(["acquisition", 'FirstPathPL'], axis=1)
# los_data["Class"] = 1

nlos_data = pd.read_csv('data/NLOS_2_ss25000_1.csv')
nlos_data = nlos_data.drop(
    ["acquisition", 'FirstPathPL'], axis=1)  # , 'FirstPathPL'
# nlos_data["Class"] = 0
dataframe = pd.concat([nlos_data, los_data], ignore_index=True)
raw_data = dataframe.values
autoencoder = load_model('trained_models/anomaly_detection_model')


def predict(model, data, threshold):
    reconstructions = model(data)
    loss = tf.keras.losses.mae(reconstructions, data)
    return tf.math.less(loss, threshold)


def print_stats(predictions, labels):
    print("Accuracy = {}".format(accuracy_score(labels, predictions)))
    print("Precision = {}".format(precision_score(labels, predictions)))
    print("Recall = {}".format(recall_score(labels, predictions)))


threshold = 0.023342917
min_val = -110.053703
max_val = 3165.0

raw_data = (raw_data - min_val) / (max_val - min_val)
# print(raw_data)

data = Mqtt_Manager(
    "localhost", "allInOne")

preds = predict(autoencoder, raw_data, threshold)
# print_stats(preds, y_test)
print(preds)
# print(autoencoder.summary())
while True:
    if data.processed_data:
        real_data = (np.array(data.processed_data) - min_val) / (max_val - min_val)
        preds = predict(autoencoder, [real_data], threshold)
        print(preds)
