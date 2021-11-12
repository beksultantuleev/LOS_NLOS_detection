import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import tensorflow as tf

from sklearn.metrics import accuracy_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from tensorflow.keras import layers, losses
from tensorflow.keras.datasets import fashion_mnist
from tensorflow.keras.models import Model
from sklearn.preprocessing import StandardScaler

def dataset_configuration(dataset, list_of_independent_vars, acquisition="acquisition"):
    for acq_index in range(1, max(np.unique(dataset[acquisition]))+1):
        temp = dataset[dataset[acquisition] == acq_index]
    dataset['idx'] = dataset.groupby(acquisition).cumcount()

    final_dataframe = dataset.pivot_table(index=acquisition, columns='idx')[
        list_of_independent_vars]
    # print(final_dataframe)
    return final_dataframe

list_of_independent_vars=["CIR", "maxNoise", "RX_level", "FPPL"]



los_data = pd.read_csv('data/LOS_2_ss25000_1.csv')
los_data = dataset_configuration(los_data, list_of_independent_vars)
# los_data = los_data.drop(["acquisition", 'FirstPathPL'], axis=1)
los_data["Class"] = 1

nlos_data = pd.read_csv('data/NLOS_2_ss25000_1.csv')
nlos_data = dataset_configuration(nlos_data, list_of_independent_vars)

# nlos_data = nlos_data.drop(["acquisition", 'FirstPathPL'], axis=1) #, 'FirstPathPL'
nlos_data["Class"] = 0
# print(los_data.head())
# print(nlos_data.head())
dataframe = pd.concat([nlos_data, los_data], ignore_index=True)
num_of_features = 8

print(dataframe)
"scaling data"
'note! use scaling for training set only to avoid data leakage'
# class_ = dataframe['Class']
# scaler = StandardScaler()
# scaler.fit(dataframe.iloc[:, :-1])
# dataframe = pd.DataFrame(scaler.transform(dataframe.iloc[:, :-1]), columns=list(dataframe.iloc[:, :-1].columns))
# dataframe['Class'] = class_
"<<<<"
# print(df)
# dataframe = pd.read_csv('data/ecg.csv', header=None)
raw_data = dataframe.values
# print(dataframe.head())
# print(raw_data)
print(dataframe)

# The last element contains the labels
labels = raw_data[:, -1]
# print(raw_data.shape)
# The other data points are the electrocadriogram data
data = raw_data[:, 0:-1]

x_train, x_test, y_train, y_test = train_test_split(
    data, labels, test_size=0.2)



"scaling here by tensorflow"
min_val = tf.reduce_min(x_train)
max_val = tf.reduce_max(x_train)

x_train = (x_train - min_val) / (max_val - min_val)
x_test = (x_test - min_val) / (max_val - min_val)


x_train = tf.cast(x_train, tf.float32)
x_test = tf.cast(x_test, tf.float32)

y_train = y_train.astype(bool)
y_test = y_test.astype(bool)


normal_train_data = x_train[y_train]
normal_test_data = x_test[y_test]

anomalous_train_data = x_train[~y_train]
anomalous_test_data = x_test[~y_test]

# print(
#     f'normal data - {normal_train_data.shape}, anomaly {anomalous_train_data.shape}, entire ds {x_train.shape}')

plt.grid()
plt.plot(np.arange(num_of_features), normal_train_data[0])
plt.title("A Normal LOS")
plt.show()
# print(len(normal_train_data[0]))

plt.grid()
plt.plot(np.arange(num_of_features), anomalous_train_data[0])
plt.title("An Anomalous or NLOS")
plt.show()


class AnomalyDetector(Model):
    def __init__(self):
        super(AnomalyDetector, self).__init__()
        self.encoder = tf.keras.Sequential([
            layers.Dense(32, activation="relu"),
            layers.Dense(16, activation="relu"),
            layers.Dense(8, activation="relu")])

        self.decoder = tf.keras.Sequential([
            # layers.Dense(8, activation="relu"),
            layers.Dense(16, activation="relu"),
            layers.Dense(32, activation="relu"),
            layers.Dense(num_of_features, activation="sigmoid")])

    def call(self, x):
        encoded = self.encoder(x)
        decoded = self.decoder(encoded)
        return decoded


autoencoder = AnomalyDetector()

autoencoder.compile(optimizer='adam', loss='mae')

history = autoencoder.fit(normal_train_data, normal_train_data,
                          epochs=30,
                          batch_size=1024,
                          validation_data=(x_test, x_test),
                          shuffle=True)

'save the model'
autoencoder.save('trained_models/anomaly_detection_model_acquisition_2')

plt.plot(history.history["loss"], label="Training Loss")
plt.plot(history.history["val_loss"], label="Validation Loss")
plt.legend()
# plt.show()
plt.close()

encoded_data = autoencoder.encoder(normal_test_data).numpy()
decoded_data = autoencoder.decoder(encoded_data).numpy()

plt.plot(normal_test_data[0], 'b')
plt.plot(decoded_data[0], 'r')
plt.fill_between(
    np.arange(num_of_features), decoded_data[0], normal_test_data[0], color='lightcoral')
plt.legend(labels=["Input", "Reconstruction", "Error"])
plt.show()
# plt.close()


encoded_data = autoencoder.encoder(anomalous_test_data).numpy()
decoded_data = autoencoder.decoder(encoded_data).numpy()

plt.plot(anomalous_test_data[0], 'b')
plt.plot(decoded_data[0], 'r')
plt.fill_between(
    np.arange(num_of_features), decoded_data[0], anomalous_test_data[0], color='lightcoral')
plt.legend(labels=["Input", "Reconstruction", "Error"])
plt.show()
# plt.close()


reconstructions = autoencoder.predict(normal_train_data)
train_loss = tf.keras.losses.mae(reconstructions, normal_train_data)

plt.hist(train_loss[None, :], bins=50)
plt.xlabel("Train loss")
plt.ylabel("No of examples")
# plt.show()
plt.close()

threshold = np.mean(train_loss) + np.std(train_loss)
print("Threshold: ", threshold)


reconstructions = autoencoder.predict(anomalous_test_data)
test_loss = tf.keras.losses.mae(reconstructions, anomalous_test_data)

plt.hist(test_loss[None, :], bins=50)
plt.xlabel("Test loss")
plt.ylabel("No of examples")
# plt.show()
plt.close()


def predict(model, data, threshold):
    reconstructions = model(data)
    loss = tf.keras.losses.mae(reconstructions, data)
    return tf.math.less(loss, threshold)


def print_stats(predictions, labels):
    print("Accuracy = {}".format(accuracy_score(labels, predictions)))
    print("Precision = {}".format(precision_score(labels, predictions)))
    print("Recall = {}".format(recall_score(labels, predictions)))


preds = predict(autoencoder, x_test, threshold)
print_stats(preds, y_test)

# print(x_test)
print(f'Min val is {min_val} \nMax val is {max_val}')