import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import tensorflow as tf
import datetime
from sklearn.metrics import accuracy_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from tensorflow.keras import layers  # , losses
from tensorflow.keras.models import Model
from sklearn.preprocessing import StandardScaler
from AnomalyDetector import AnomalyDetector
import joblib


class Train_anomaly_detection_model():
    def __init__(self):
        self.list_of_features = ["RX_level", 'RX_difference']
        self.single_data_input = True
        self.save_model = False
        self.turn_on_all_plots = True
        self.number_of_features = len(self.list_of_features)

    def set_configuration(self, single_data_input=True, save_model=False, turn_on_all_plots=True, list_of_features=["RX_level", 'RX_difference'], acquisition_number = 2):
        self.single_data_input = single_data_input
        self.save_model = save_model
        self.turn_on_all_plots = turn_on_all_plots
        self.list_of_features = list_of_features
        self.acquisition_number = acquisition_number
        if not self.single_data_input:
            self.number_of_features = len(self.list_of_features)*self.acquisition_number
        else:
            self.number_of_features = len(self.list_of_features)

    def multiInputConfiguration(self, dataset, list_of_independent_vars, acquisition="acquisition", set_num_of_acquisition = 2):
        dataset[acquisition] = self.acquisition_modifier(acquisition_number=set_num_of_acquisition, length_of_acquisitions=len(dataset))
        for acq_index in range(1, max(np.unique(dataset[acquisition]))+1):
            temp = dataset[dataset[acquisition] == acq_index]
        dataset['idx'] = dataset.groupby(acquisition).cumcount()

        final_dataframe = dataset.pivot_table(index=acquisition, columns='idx')[
            list_of_independent_vars]
        # print(final_dataframe)
        return final_dataframe

    def acquisition_modifier(self, acquisition_number, length_of_acquisitions):
        if acquisition_number == 1:
            return [1]*length_of_acquisitions
        elif acquisition_number == 0:
            return [0]*length_of_acquisitions
        lis = []
        for i in range(length_of_acquisitions):
            lis.append(i)
        lis = sorted(lis*acquisition_number)[:length_of_acquisitions]
        return lis

    def select_dataset(self, los_data, nlos_data, sklearn_scale=False):
        los_data = pd.read_csv(los_data)
        nlos_data = pd.read_csv(nlos_data)
        if not self.single_data_input:
            los_data = self.multiInputConfiguration(
                los_data, self.list_of_features, set_num_of_acquisition=self.acquisition_number)
            nlos_data = self.multiInputConfiguration(
                nlos_data, self.list_of_features, set_num_of_acquisition=self.acquisition_number)

        los_data['Class'] = 1
        nlos_data['Class'] = 0
        dataframe = pd.concat([nlos_data, los_data], ignore_index=True)
        if self.single_data_input:
            dataframe = dataframe[self.list_of_features + ["Class"]]
            # print(dataframe)
        # print(dataframe)
        # print(dataframe.shape)
        raw_data = dataframe.values

        # The last element contains the labels
        labels = raw_data[:, -1]

        # The other data points are the electrocadriogram data
        data = raw_data[:, 0:-1]
        x_train, x_test, y_train, y_test = train_test_split(
            data, labels, test_size=0.2)
        if sklearn_scale:
            'note! use scaling for training set only to avoid data leakage'
            scaler = StandardScaler()
            scaler.fit(x_train)
            x_train = scaler.transform(x_train)
            x_test = scaler.transform(x_test)
            scaler_name = 'single_data_input' if self.single_data_input else "multiple_data_input"
            joblib.dump(
                scaler, f'trained_models/standard_scaler_anomaly_detection_{scaler_name}.save')
            "<<<<"
        "scaling here by tensorflow"
        # min_val = tf.reduce_min(x_train)
        # max_val = tf.reduce_max(x_train)

        min_val = tf.reduce_min(
            dataframe.loc[dataframe["Class"] == 1][self.list_of_features])
        max_val = tf.reduce_max(
            dataframe.loc[dataframe["Class"] == 1][self.list_of_features])

        x_train = (x_train - min_val) / (max_val - min_val)
        x_test = (x_test - min_val) / (max_val - min_val)

        self.min_val = min_val
        self.max_val = max_val

        x_train = tf.cast(x_train, tf.float32)
        x_test = tf.cast(x_test, tf.float32)

        y_train = y_train.astype(bool)
        y_test = y_test.astype(bool)

        self.x_test = x_test
        self.x_train = x_train
        self.y_test = y_test
        self.y_train = y_train

        self.normal_train_data = x_train[y_train]
        self.normal_test_data = x_test[y_test]

        self.anomalous_train_data = x_train[~y_train]
        self.anomalous_test_data = x_test[~y_test]
        if self.turn_on_all_plots:
            plt.grid()
            plt.plot(np.arange(self.number_of_features),
                     self.normal_train_data[0])
            plt.title("A Normal LOS")
            plt.show()
            # print(len(normal_train_data[0]))

            plt.grid()
            plt.plot(np.arange(self.number_of_features),
                     self.anomalous_train_data[0])
            plt.title("An Anomalous or NLOS")
            plt.show()

    def start_training(self, epochs=50, batch_size=1024):
        autoencoder = AnomalyDetector(num_of_features=self.number_of_features)
        autoencoder.compile(optimizer='adam', loss='mae')

        history = autoencoder.fit(self.normal_train_data, self.normal_train_data,
                                  epochs=epochs,
                                  batch_size=batch_size,
                                  validation_data=(self.x_test, self.x_test),
                                  shuffle=True)

        'save the model'
        if self.save_model:
            if self.single_data_input:
                autoencoder.save('trained_models/anomaly_detection_model')
            else:
                autoencoder.save(
                    'trained_models/anomaly_detection_model_acquisition_2')
            print('Model is saved!')
        if self.turn_on_all_plots:
            plt.plot(history.history["loss"], label="Training Loss")
            plt.plot(history.history["val_loss"], label="Validation Loss")
            plt.legend()
            # plt.show()
            plt.close()

        encoded_data = autoencoder.encoder(self.normal_test_data).numpy()
        decoded_data = autoencoder.decoder(encoded_data).numpy()
        if self.turn_on_all_plots:
            plt.plot(self.normal_test_data[0], 'b')
            plt.plot(decoded_data[0], 'r')
            plt.fill_between(
                np.arange(self.number_of_features), decoded_data[0], self.normal_test_data[0], color='lightcoral')
            plt.legend(labels=["Input", "Reconstruction", "Error"])
            plt.show()
        # plt.close()

        encoded_data = autoencoder.encoder(self.anomalous_test_data).numpy()
        decoded_data = autoencoder.decoder(encoded_data).numpy()
        if self.turn_on_all_plots:
            plt.plot(self.anomalous_test_data[0], 'b')
            plt.plot(decoded_data[0], 'r')
            plt.fill_between(
                np.arange(self.number_of_features), decoded_data[0], self.anomalous_test_data[0], color='lightcoral')
            plt.legend(labels=["Input", "Reconstruction", "Error"])
            plt.show()
            # plt.close()

        reconstructions = autoencoder.predict(self.normal_train_data)
        train_loss = tf.keras.losses.mae(
            reconstructions, self.normal_train_data)
        if self.turn_on_all_plots:
            plt.hist(train_loss[None, :], bins=50)
            plt.xlabel("Train loss")
            plt.ylabel("No of examples")
            # plt.show()
            plt.close()

        threshold = np.mean(train_loss) + np.std(train_loss)
        # print("Threshold: ", threshold)

        reconstructions = autoencoder.predict(self.anomalous_test_data)
        test_loss = tf.keras.losses.mae(
            reconstructions, self.anomalous_test_data)

        if self.turn_on_all_plots:
            plt.hist(test_loss[None, :], bins=50)
            plt.xlabel("Test loss")
            plt.ylabel("No of examples")
            plt.show()
            # plt.close()

        def predict(model, data, threshold):
            reconstructions = model(data)
            loss = tf.keras.losses.mae(reconstructions, data)
            return tf.math.less(loss, threshold)

        def log_stats(predictions, labels):
            log = f'''
Time: {datetime.datetime.now()}
Threshold: {threshold}
Min_val: {self.min_val}
Max_val: {self.max_val}
Accuracy: {accuracy_score(labels, predictions)}
Precision: {precision_score(labels, predictions)}
Recall: {recall_score(labels, predictions)}
            
            '''
            if self.single_data_input:
                log_name = "Single_data_input"
            else:
                log_name = 'Multi_data_input'
            file = open(
                f"src/Training/logs/anomaly_detection/logs_{log_name}.txt", "w")
            file.write(log)
            file.close()
            print(log)

        preds = predict(autoencoder, self.x_test, threshold)
        log_stats(preds, self.y_test)



if "__main__" == __name__:
    test = Train_anomaly_detection_model()
    list_of_features = ["RX_level", 'RX_difference']
    test.set_configuration(single_data_input=False, save_model=True,
                           turn_on_all_plots=True, list_of_features=list_of_features, 
                           acquisition_number=4)
    test.select_dataset('data/LOS_good_data_complete.csv',
                        'data/NLOS_data_water_2_ss95000_1.csv', sklearn_scale=False)
    test.start_training(epochs=50)
