import tensorflow as tf
from sklearn.metrics import accuracy_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from tensorflow.keras import layers#, losses
# from tensorflow.keras.datasets import fashion_mnist
from tensorflow.keras.models import Model

class AnomalyDetector(Model):
    def __init__(self, num_of_features):
        super(AnomalyDetector, self).__init__()
        self.num_of_features = num_of_features
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
