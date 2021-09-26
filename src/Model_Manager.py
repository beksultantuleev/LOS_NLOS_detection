from typing import final
from numpy.core.fromnumeric import shape

import pandas as pd
import numpy as np
import random
from sklearn.preprocessing import LabelEncoder
from keras.layers import Dense, Dropout

from tensorflow import keras
from keras.models import Sequential
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
import sklearn.metrics as metrics
from sklearn.svm import SVC
import joblib


class Model_manager():
    def __init__(self, validation_ratio=0.2, epoch_number=50, batch_number=8):
        self.lbl_encode = LabelEncoder()
        self.epoch_number = epoch_number
        self.batch_number = batch_number
        self.validation_ratio = validation_ratio
        self.model = Sequential()

    def dataset_configuration(self, datapath, list_of_independent_vars, target, acquisition="acquisition"):
        dataset = pd.read_csv(datapath)  # add  function
        Y_list_labels = []
        # it was from 2
        for acq_index in range(1, max(np.unique(dataset[acquisition]))+1):
            temp = dataset[dataset[acquisition] == acq_index]
            Y_list_labels = np.append(Y_list_labels, np.unique(temp[target]))
        # dataset = dataset.drop(
        #     [target, 'Unnamed: 0'], axis=1) #if no inder after merge
        dataset['idx'] = dataset.groupby(acquisition).cumcount()

        final_dataframe = dataset.pivot_table(index=acquisition, columns='idx')[
            list_of_independent_vars]
        final_dataframe[target] = Y_list_labels

        # get enumerator codes
        self.value_codes = [i for i in enumerate(
            np.sort(final_dataframe[target].unique()))]

        # encoding
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
        # print(self.X)
        

    def logistic_reg(self, set_name = "logistic_reg_default"):

        logistic_classifier = LogisticRegression(solver='liblinear')
        logistic_classifier.fit(self.x_train, self.y_train.values.ravel())
        y_pred_logistic = logistic_classifier.predict(self.x_test)
        cm = metrics.confusion_matrix(self.y_test, y_pred_logistic)
        print(cm)
        # print(self.value_codes)
        filename = f'trained_models/{set_name}.sav'
        joblib.dump(logistic_classifier, filename)

    def SVM(self):

        self.x_train, self.x_test, self.y_train, self.y_test = train_test_split(
            self.X, self.Y, test_size=0.2)
        svm_classifier = SVC(kernel='linear')
        svm_classifier.fit(self.x_train, self.y_train)
        y_pred_svm = svm_classifier.predict(self.x_test)
        cm = metrics.confusion_matrix(self.y_test, y_pred_svm)
        print(cm)
    
    
    def binary_nn(self, name='binary_nn', epoch=5, batch=64):

        self.model.add(Dense(len(self.X.columns), input_dim=len(
            self.X.columns), activation='relu'))
        self.model.add(Dropout(0.5))
        self.model.add(Dense(64, activation='relu'))
        self.model.add(Dropout(0.5))
        self.model.add(Dense(32, activation='relu'))
        self.model.add(Dropout(0.5))
        self.model.add(Dense(1, activation='sigmoid'))

        self.model.summary()
        self.model.compile(
            optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])

        history = self.model.fit(self.x_train, self.y_train, epochs=epoch, validation_data=(
            self.x_test, self.y_test), batch_size=batch)
        y_pred_custom_binary_nn = np.argmax(self.model.predict(self.x_test), axis=-1)
        # self.model.save(f'trained_models/{name}.h5')
        # print(f'SAVED to trained_models/{name}.h5')
        # print(y_pred_custom_binary_nn)
        cm = metrics.confusion_matrix(
            self.y_test, y_pred_custom_binary_nn)
        print(cm)
        self.model.save(f'trained_models/{name}.h5')
        print(f'SAVED to trained_models/{name}.h5')
    
    
    # def custom_binary_nn(self):
    #     self.model.add(Dense(len(self.X.columns), input_dim=len(
    #         self.X.columns), activation='relu'))
    #     self.model.add(Dense(64, activation='relu'))
    #     self.model.add(Dense(32, activation='relu'))
    #     self.model.add(Dense(8, activation='relu'))
    #     self.model.add(Dense(1, activation='sigmoid'))
    #     self.model.compile(loss='binary_crossentropy',
    #                        optimizer='adam', metrics=['accuracy'])
    #     self.model.fit(self.x_train, self.y_train, batch_size=self.batch_number,
    #                    epochs=self.epoch_number, verbose=1, validation_data=self.x_test)
    #     y_pred_custom_binary_nn = self.model.predict_classes(self.x_test)
    #     # print(y_pred_custom_binary_nn)
    #     cm_custom_binary_nn = metrics.confusion_matrix(
    #         self.y_test, y_pred_custom_binary_nn)
    #     print(cm_custom_binary_nn)
    #     print(self.value_codes)

    def save_custom_binary_nn(self, name):
        self.model.save(f'trained_models/{name}.h5')
        print(f'SAVED to trained_models/{name}.h5')


if __name__ == "__main__":
    test = Model_manager(validation_ratio=0.3,
                         epoch_number=200, batch_number=16)

    # test.dataset_configuration(datapath="data/short_data_motion_test.csv", list_of_independent_vars=['acc_x', 'acc_y', 'acc_z', 'gyr_x', 'gyr_y', 'gyr_z'], target='activity')
    test.dataset_configuration(datapath="data/firstLosNlos.csv", list_of_independent_vars=["CIR", "FirstPathPL", "maxNoise", "RX_level", "FPPL"], target='activity')
    print(test.value_codes)
    # test.custom_binary_nn()
    # test.binary_nn(epoch=10)

    # test.save_custom_binary_nn("binary_nn")

    # test.logistic_reg(set_name='logistic_regression')
    # test.SVM()
