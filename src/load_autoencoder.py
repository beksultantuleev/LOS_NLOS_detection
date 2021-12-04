import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import tensorflow as tf
import pandas as pd

from sklearn.metrics import accuracy_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from tensorflow.keras import layers, losses
from tensorflow.keras.datasets import fashion_mnist
from tensorflow.keras.models import Model
from keras.models import load_model
import collections
from Core_functions.hub_of_functions import *


'load regular autoencoder that works like pca'


autoencoder = load_model('trained_models/autoencoder')

# encoder.summary()

data = pd.read_csv('data/los_nlos_cluster_dataa.txt')
x_train = data.drop(['activity'], axis=1)
'reshape data'
x_train = x_train.to_numpy()
x_train = x_train.reshape((x_train.shape[0], x_train.shape[1], 1))
# print(x_train.shape)  # (50000, 5, 1)

encoded_data = autoencoder.encoder(x_train).numpy()
# print(f'shape of encoded is {encoded_data.shape}')
print(encoded_data)
