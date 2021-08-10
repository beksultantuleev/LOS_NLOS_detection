from typing import final
from numpy.core.fromnumeric import shape

import pandas as pd
import numpy as np
import random
from sklearn.preprocessing import LabelEncoder
from keras.layers import Dense

from tensorflow import keras
from keras.models import Sequential
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
import sklearn.metrics as metrics
from sklearn.svm import SVC


class Model_manager():
    def __init__(self, validation_ratio=0.2, epoch_number=50, batch_number=8):
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
        self.X = None

    def old_dataset_configuration(self, location):
        dataset = pd.read_csv(location)
        dataset = dataset.drop(['Unnamed: 0'], axis=1)

        self.value_codes = [i for i in enumerate(
            np.sort(dataset['activity'].unique()))]

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

        # change shape of dtensor
        self.dtensor = np.empty((0, 6*min(second_axis)))
        self.labels = np.empty((0))

        for acq_index in range(1, last_index+1):  # it was from 2
            temp = dataset[dataset.acquisition == acq_index]
            acc_x = temp.acc_x
            acc_y = temp.acc_y
            acc_z = temp.acc_z

            gyr_x = temp.gyr_x
            gyr_y = temp.gyr_y
            gyr_z = temp.gyr_z

            self.dtensor = np.vstack([self.dtensor, np.concatenate(
                (acc_x, acc_y, acc_z, gyr_x, gyr_y, gyr_z))])
            self.labels = np.append(self.labels, np.unique(temp.activity))

        self.Y = pd.DataFrame(self.labels)
        self.labels = np.asarray(pd.get_dummies(self.labels), dtype=np.int8)

        self.X = pd.DataFrame(self.dtensor)

    def dataset_configuration(self, list_of_independent_vars, target):
        dataset = pd.read_csv("data/new_data_motion_test.csv")
        Y_list_labels = []
        for acq_index in range(1, max(np.unique(dataset.acquisition))+1):  # it was from 2
            temp = dataset[dataset.acquisition == acq_index]
            Y_list_labels = np.append(Y_list_labels, np.unique(temp[target]))
        dataset = dataset.drop(
            [target, 'Unnamed: 0'], axis=1)
        dataset['idx'] = dataset.groupby('acquisition').cumcount()

        final_dataframe = dataset.pivot_table(index='acquisition', columns='idx')[
            list_of_independent_vars]
        final_dataframe[target] = Y_list_labels

        #get enumerator codes
        self.value_codes = [i for i in enumerate(
            np.sort(final_dataframe[target].unique()))]
        
        #encoding
        for col in final_dataframe:
            if final_dataframe[col].dtype.name == "object":
                try:
                    final_dataframe[col] = self.lbl_encode.fit_transform(
                        final_dataframe[col])
                except:
                    pass
        self.Y = final_dataframe[target]
        self.X = final_dataframe.drop([target], axis=1)
        self.x_train, self.x_test, self.y_train, self.y_test = train_test_split(
            self.X, self.Y, test_size=0.2)
        # print(len(self.X.columns))

    def logistic_reg(self):

        logistic_classifier = LogisticRegression(solver='liblinear')
        logistic_classifier.fit(self.x_train, self.y_train.values.ravel())
        y_pred_logistic = logistic_classifier.predict(self.x_test)
        cm = metrics.confusion_matrix(self.y_test, y_pred_logistic)
        print(cm)
        # print(self.value_codes)

    def SVM(self):
        
        self.x_train, self.x_test, self.y_train, self.y_test = train_test_split(
            self.X, self.Y, test_size=0.2)
        svm_classifier = SVC(kernel='linear')
        svm_classifier.fit(self.x_train, self.y_train)
        y_pred_svm = svm_classifier.predict(self.x_test)
        cm = metrics.confusion_matrix(self.y_test, y_pred_svm)
        print(cm)
    
    def custom_nn(self, input_nodes, output_nodes):
        sample_index = np.arange(0, self.dtensor.shape[0])
        # print(sample_index)
        self.shuffled_indexes = random.sample(
            list(sample_index), len(list(sample_index)))
        # print(shuffled_indexes)

        data_split_tuner_value = int(len(sample_index)*self.validation_ratio)

        self.train_data = self.dtensor[self.shuffled_indexes[data_split_tuner_value:], :]
        self.test_data = self.dtensor[self.shuffled_indexes[:data_split_tuner_value], :]
        self.train_labels = self.labels[self.shuffled_indexes[data_split_tuner_value:], :]
        self.test_labels = self.labels[self.shuffled_indexes[:data_split_tuner_value], :]

        self.train_shape = self.train_data.shape[1]

        self.model.add(Dense(input_nodes, input_shape=(
            self.train_shape,), name='input_layer'))
        self.model.add(Dense(64, activation='relu', name='hidden1'))
        self.model.add(Dense(32, activation='relu', name='hidden2'))
        self.model.add(
            Dense(output_nodes, activation='softmax', name='output_layer'))

        self.model.compile(
            optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])  # "binary_crossentropy" categorical_crossentropy
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

    def save_custom_nn_model(self, name):
        self.model.save(f'trained_models/{name}.h5')
        f = open(f"trained_models/{name}.txt", "w")
        f.write(self.result)
        f.close()
        np.save(f'trained_models/{name}_validation.npy', self.test_data)
        np.save(f'trained_models/{name}_label_val.npy', self.test_labels)

    def custom_binary_nn(self):
        self.model.add(Dense(len(self.X.columns), input_dim=len(self.X.columns), activation='relu'))
        self.model.add(Dense(3, activation='relu'))
        self.model.add(Dense(1, activation='sigmoid'))
        self.model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])
        self.model.fit(self.x_train, self.y_train, batch_size=8, epochs=50, verbose=1, validation_data=self.test_data)
        results = self.model.evaluate(
            self.x_test, self.y_test, verbose=1)

        results_names = self.model.metrics_names
        self.result = "\nThe %s value is: %f \nThe %s value is: %f \n" % (
            results_names[0], results[0], results_names[1], results[1])
        print(self.result)
if __name__ == "__main__":
    test = Model_manager(validation_ratio=0.3,
                         epoch_number=200, batch_number=16)
    # test.old_dataset_configuration(location="data/new_data_motion_test.csv")
    test.dataset_configuration(
        ['acc_x', 'acc_y', 'acc_z', 'gyr_x', 'gyr_y', 'gyr_z'], 'activity')
    test.custom_binary_nn()
    # test.custom_nn(120, 2)
    # test.save_model("new_data_motion")
    # test.get_reshaped_df()
    # test.logistic_reg()
    # test.SVM()
