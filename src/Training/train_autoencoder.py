import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import tensorflow as tf
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import accuracy_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from tensorflow.keras import layers, losses
from tensorflow.keras.datasets import fashion_mnist
from tensorflow.keras.models import Model
from tensorflow.python.keras.engine.sequential import Sequential
import joblib

'first autoencoder works like pca, not in use'

data = pd.read_csv('data/los_nlos_cluster_dataa.txt')
x_train = data.drop(['activity'], axis=1)
'reshape data'
x_train = x_train.to_numpy()
x_train = x_train.reshape((x_train.shape[0], x_train.shape[1], 1))
print(x_train.shape)  # (50000, 5, 1)

# (x_train, _), (x_test, _) = fashion_mnist.load_data()

# x_train = x_train.astype('float32') / 255.
# x_test = x_test.astype('float32') / 255.


latent_dim = 2


class Autoencoder(Model):
    def __init__(self, latent_dim):
        super(Autoencoder, self).__init__()
        self.latent_dim = latent_dim
        self.encoder = tf.keras.Sequential([
            layers.Flatten(),
            layers.Dense(latent_dim, activation='relu'),
        ])
        self.decoder = tf.keras.Sequential([
            layers.Dense(5, activation='sigmoid'),
            layers.Reshape((5, 1))
        ])

    def call(self, x):
        encoded = self.encoder(x)
        decoded = self.decoder(encoded)
        return decoded


autoencoder = Autoencoder(latent_dim)

autoencoder.compile(optimizer='adam', loss=losses.MeanSquaredError())

autoencoder.fit(x_train, x_train,
                epochs=2,
                shuffle=True)

pred = autoencoder.predict(x_train)
# print(f"shape of pred is {pred.shape}")
encoded_data = autoencoder.encoder(x_train).numpy()
decoded_data = autoencoder.decoder(encoded_data).numpy()

# print(f"shape of original is {x_train.shape}")
print(f'shape of encoded is {encoded_data.shape}')
print(encoded_data)
# print(f'shape of decoded is {decoded_data.shape}')
'save autoencoder model'
# autoencoder.save('trained_models/autoencoder')

'k means'
kmeans = KMeans(n_clusters= 2)
kmeans.fit(encoded_data)
label = kmeans.predict(encoded_data)
# print(f'len of label {len(label)} \nUnique vals {np.unique(label)} \nlabel itself \n{label}')


"save model"
# joblib.dump(kmeans, 'trained_models/k_means_for_autoencoder.sav')

"custom data testing"
# label = kmeans.predict([df[0]]) #df[:1,:]
# print(label)
# print(df[:1,:])


# print(label[:20])
"plotting"
# filter rows of original data
filtered_label0 = encoded_data[label == 0]
filtered_label1 = encoded_data[label == 1]
 
#Plotting the results
plt.scatter(filtered_label0[:,0] , filtered_label0[:,1] , color = 'red')
plt.scatter(filtered_label1[:,0] , filtered_label1[:,1] , color = 'black')
plt.show()


'illustration>'
# n = 10
# plt.figure(figsize=(20, 4))
# for i in range(n):
#   # display original
#   ax = plt.subplot(2, n, i + 1)
#   plt.imshow(x_train[i])
#   plt.title("original")
#   plt.gray()
#   ax.get_xaxis().set_visible(False)
#   ax.get_yaxis().set_visible(False)

#   # display reconstruction
#   ax = plt.subplot(2, n, i + 1 + n)
#   plt.imshow(decoded_data[i])
#   plt.title("reconstructed")
#   plt.gray()
#   ax.get_xaxis().set_visible(False)
#   ax.get_yaxis().set_visible(False)
# plt.show()
'illustration<'
