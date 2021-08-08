from numpy.core.fromnumeric import shape

import pandas as pd
import numpy as np
import random
from sklearn.preprocessing import LabelEncoder
from keras.layers import Dense

from tensorflow import keras
from keras.models import Sequential


class Model_manager():
    def __init__(self, validation_ratio = 0.2, epoch_number = 50, batch_number = 8):
        self.lbl_encode = LabelEncoder()
        self.epoch_number = epoch_number
        self.batch_number = batch_number
        self.validation_ratio = validation_ratio
        self.model = Sequential()
        self.train_data = None
        self.test_data = None
        self.train_labels = None
        self.test_labels = None
        self.result = None

    def dataset_configuration(self, location):
        dataset = pd.read_csv(location)
        dataset = dataset.drop(['Unnamed: 0'], axis=1)
        
        self.value_codes = [i for i in enumerate(np.sort(dataset['activity'].unique()))]
        
        for col in dataset:
            if dataset[col].dtype.name == "object":
                try:
                    dataset[col] = self.lbl_encode.fit_transform(
                        dataset[col])
                except:
                    pass

        last_index = max(np.unique(dataset.acquisition))

        second_axis = []
        for acq_index in range(1, last_index+1):  # from 1 to whatever
            second_axis.append(
                dataset[dataset.acquisition == acq_index].shape[0])

        dtensor = np.empty((0, 6*min(second_axis)))  # change shape of dtensor
        labels = np.empty((0))

        for acq_index in range(1, last_index+1):  # it was from 2
            temp = dataset[dataset.acquisition == acq_index]
            acc_x = temp.acc_x
            acc_y = temp.acc_y
            acc_z = temp.acc_z

            gyr_x = temp.gyr_x
            gyr_y = temp.gyr_y
            gyr_z = temp.gyr_z

            dtensor = np.vstack([dtensor, np.concatenate(
                (acc_x, acc_y, acc_z, gyr_x, gyr_y, gyr_z))])
            labels = np.append(labels, np.unique(temp.activity))

        labels = np.asarray(pd.get_dummies(labels), dtype=np.int8)

        # print(labels.shape)

        sample_index = np.arange(0, dtensor.shape[0])
        # print(sample_index)

        self.shuffled_indexes = random.sample(
            list(sample_index), len(list(sample_index)))
        # print(shuffled_indexes)

        data_split_tuner_value = int(len(sample_index)*self.validation_ratio)

        self.train_data = dtensor[self.shuffled_indexes[data_split_tuner_value:], :]
        self.test_data = dtensor[self.shuffled_indexes[:data_split_tuner_value], :]
        self.train_labels = labels[self.shuffled_indexes[data_split_tuner_value:], :]
        self.test_labels = labels[self.shuffled_indexes[:data_split_tuner_value], :]

        self.train_shape = self.train_data.shape[1]

    def start_training(self, input_nodes, output_nodes):
        self.model.add(Dense(input_nodes, input_shape=(
            self.train_shape,), name='input_layer'))
        self.model.add(Dense(64, activation='relu', name='hidden1'))
        self.model.add(Dense(32, activation='relu', name='hidden2'))

        self.model.add(
            Dense(output_nodes, activation='softmax', name='output_layer'))

        self.model.compile(
            optimizer='rmsprop', loss='categorical_crossentropy', metrics=['accuracy'])
        self.model.summary()

        self.model.fit(self.train_data, self.train_labels, epochs=self.epoch_number,
                       batch_size=self.batch_number, validation_split=self.validation_ratio, verbose=1)
        results = self.model.evaluate(
            self.test_data, self.test_labels, verbose=1)

        results_names = self.model.metrics_names
        self.result = "\nThe %s value is: %f \nThe %s value is: %f \n" % (
            results_names[0], results[0], results_names[1], results[1])
        print(self.result)
        print(f"""Ratio trainded data  {len(self.train_data)/len(self.shuffled_indexes)}
                Ratio tested data {len(self.test_data)/ len(self.shuffled_indexes)}""")
        print(f"value encoder {self.value_codes}")

    def save_model(self, name):
        self.model.save(f'trained_models/{name}.h5')
        f = open(f"trained_models/{name}.txt", "w")
        f.write(self.result)
        f.close()
        np.save(f'trained_models/{name}_validation.npy', self.test_data)
        np.save(f'trained_models/{name}_label_val.npy', self.test_labels)


if __name__ == "__main__":
    test = Model_manager(validation_ratio = 0.3, epoch_number = 30, batch_number = 8)
    test.dataset_configuration(location="data/new_data_motion_test.csv")
    test.start_training(240, 2)
    test.save_model("new_data_motion")
