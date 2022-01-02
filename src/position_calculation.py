import paho.mqtt.client as mqtt
import numpy as np
import json
import re
import time
import joblib
from Managers.Mqtt_manager import Mqtt_Manager
from Managers.Deque_manager import Deque_manager
from Core_functions.hub_of_functions import *
import tensorflow as tf
from keras.models import load_model


class Position_finder:
    def __init__(self, anchor_postion_list=[]):
        broker_address = "192.168.0.119"
        self.client = mqtt.Client('P1')  # create new instance
        self.client.connect(broker_address)  # connect to broker
        self.client.subscribe([("topic/#", 0)])
        self.client.on_message = self.on_message
        self.client.loop_start()
        self.position = []
        self.anchor_postion_list = anchor_postion_list
        self.amount_of_anchors = len(self.anchor_postion_list)
        self.raw_anchors_data = [0]*self.amount_of_anchors
        self.processed_anchors_data = None

        self.modified_ts = [0]*len(self.anchor_postion_list)
        self.deque_list = [0]*len(self.anchor_postion_list)
        for i in range(len(self.anchor_postion_list)):
            self.deque_list[i] = Deque_manager(10)
        
        "pca k means"
        self.pca_wait_flag = True
        self.vanilla_ts = None
        self.pca_model = joblib.load('trained_models/pca.sav')
        self.k_means_model = joblib.load('trained_models/k_means.sav')

        "autoencoder"
        self.autoencoder = load_model('trained_models/anomaly_detection_model')
        self.path = 'src/Training/logs/anomaly_detection/logs_Single_data_input.txt'
        self.threshold = 0.03#value_extractor("Threshold:", path)
        self.min_val = value_extractor("Min_val:", self.path)
        self.max_val = value_extractor("Max_val:", self.path)
        "grand model"
        self.data_mitigation = np.empty(shape=(0, self.amount_of_anchors))
        self.data_detection = np.empty(shape=(0, self.amount_of_anchors))
        
        self.pred_from_mitigation = [np.nan]*self.amount_of_anchors

    def on_message(self, client, userdata, message):
        msg = f'{message.payload.decode("utf")}'
        pattern = re.compile(r'\[.+')
        matches = pattern.finditer(msg)
        for match in matches:
            res = json.loads(match.group(0))
            topics = []
            for i in range(1, self.amount_of_anchors+1):
                top_name = f'topic/{i}'
                topics.append(top_name)
            counter = 0
            for topic in topics:
                if message.topic == topic:
                    self.raw_anchors_data[counter] = res
                counter += 1


    def pca_k_means_model(self):
        if self.pca_wait_flag:
            time.sleep(0.9)
            self.pca_wait_flag = False
        raw_anchors_data = np.delete(np.array(self.raw_anchors_data), 1, 1)
        self.vanilla_ts = raw_anchors_data[:, :-2]
        input_data = np.array(raw_anchors_data)[:, -2:]
        df = self.pca_model.transform(input_data)
        pred = self.k_means_model.predict(df)
        self.processed_anchors_data = np.c_[raw_anchors_data[:, :-2], pred]
        
      

    def anomaly_detection(self): 
        "true or 1 is LOS"
        raw_anchors_data = np.delete(np.array(self.raw_anchors_data), 1, 1)
        self.vanilla_ts = raw_anchors_data[:, :-2]
        raw_data = np.array(raw_anchors_data)[:, -2:]
        input_data = (np.array(raw_data) -
                        self.min_val) / (self.max_val - self.min_val)
        pred = predict_anomaly_detection(self.autoencoder, input_data, self.threshold)
        self.processed_anchors_data = np.c_[raw_anchors_data[:, :-2], pred]
        self.data_detection = np.append(self.data_detection, np.expand_dims(
                    pred, axis=0), axis=0)
        # print(f'1 from detection {pred}')


    def timestamp_filter(self, los = 1):
        # if self.mqtt_.processed_data:
        # print(self.deque_list[0].get_std_avrg())
        # print(self.deque_list[0].get_data_list())
        counter = 0
        for t in self.processed_anchors_data:
            if t[-1] == los:  # LOS
                self.deque_list[counter].append_data(t[1])
                

            if t[1] > self.deque_list[counter].get_avrg()-self.deque_list[counter].get_std() and t[1] < self.deque_list[counter].get_avrg()+self.deque_list[counter].get_std():
                self.modified_ts[counter] = [t[0], t[1], t[2]]
                
                "add logic of global function"
                self.pred_from_mitigation[counter] = 1
            else:
                self.modified_ts[counter] = [t[0], self.deque_list[counter].get_avrg(), t[2]]  # put avrg timestamp
                self.pred_from_mitigation[counter] = 0
            counter += 1
        # print(f"2 from mitigation {self.pred_from_mitigation}")
        self.data_mitigation = np.append(self.data_mitigation, np.expand_dims(self.pred_from_mitigation, axis=0), axis=0)
        
        return self.modified_ts

    def get_position(self, ts_with_los_prediction):
        c = 299792458

        A_n = self.anchor_postion_list
        n = len(A_n)

        toa = [0] * len(ts_with_los_prediction)
        counter = 0
        for time_stamp_with_los in ts_with_los_prediction:
            t = np.float32(time_stamp_with_los[1]) * np.float32(15.65e-12)
            toa[counter] = t
            counter += 1

        toa = np.array([toa])
        tdoa = toa - toa[0][0]  # changed here
        # print(tdoa)
        tdoa = tdoa[0][1:]
        # print(tdoa)
        D = tdoa*c  # D is 2x1
        # print(D)

        D = D.reshape(len(ts_with_los_prediction)-1, 1)
        A_diff_one = np.array((A_n[0][0][0]-A_n[1:, 0]), dtype='float32')
        A_diff_two = np.array((A_n[0][1][0]-A_n[1:, 1]), dtype='float32')
        A_diff_three = np.array((A_n[0][2][0]-A_n[1:, 2]), dtype='float32')

        A = 2 * np.array([A_diff_one, A_diff_two, A_diff_three, D]).T

        b = D**2 + np.linalg.norm(A_n[0])**2 - np.sum(A_n[1:, :]**2, 1)
        x_t0 = np.dot(np.linalg.pinv(A), b)

        x_t_0 = np.array([x_t0[0][0], x_t0[0][1], x_t0[0][2]])

        # loop
        f = np.zeros((n-1, 1))
        del_f = np.zeros((n-1, 3))
        A_n = A_n.T
        for ii in range(1, n):

            f[ii-1] = np.linalg.norm(x_t_0-A_n[0, :, ii].reshape(3, 1)) - \
                np.linalg.norm(x_t_0-A_n[0, :, 0].reshape(3, 1))

            del_f[ii-1, 0] = np.dot((x_t_0[0]-A_n[0, 0, ii]), np.reciprocal(np.linalg.norm(x_t_0-A_n[0, :, ii].reshape(
                3, 1)))) - np.dot((x_t_0[0]-A_n[0, 0, 0]), np.reciprocal(np.linalg.norm(x_t_0-A_n[0, :, 0].reshape(3, 1))))
            del_f[ii-1, 1] = np.dot((x_t_0[1]-A_n[0, 1, ii]), np.reciprocal(np.linalg.norm(x_t_0-A_n[0, :, ii].reshape(
                3, 1)))) - np.dot((x_t_0[1]-A_n[0, 1, 0]), np.reciprocal(np.linalg.norm(x_t_0-A_n[0, :, 0].reshape(3, 1))))
            del_f[ii-1, 2] = np.dot((x_t_0[2]-A_n[0, 2, ii]), np.reciprocal(np.linalg.norm(x_t_0-A_n[0, :, ii].reshape(
                3, 1)))) - np.dot((x_t_0[2]-A_n[0, 2, 0]), np.reciprocal(np.linalg.norm(x_t_0-A_n[0, :, 0].reshape(3, 1))))
        x_t = np.dot(np.linalg.pinv(del_f), (D-f)) + x_t_0
        tag_id = ts_with_los_prediction[0][0]

        self.position = [[x_t[0][0], x_t[1][0], x_t[2][0]], tag_id]
        return self.position


if __name__ == "__main__":

    A_n1 = np.array([[0], [1], [1.8]])
    A_n2 = np.array([[6], [0], [2]])
    A_n3 = np.array([[3], [3.5], [1]])  # master
    # A_n4 = np.array([[3], [5], [1]])  # master
    anchors_pos = np.array([A_n1, A_n2, A_n3])
    # print(A_n1.shape)
    test = Position_finder(anchor_postion_list=anchors_pos)
    while True:
        time.sleep(0.2)
        test.anomaly_detection()
        ts_with_pred = test.timestamp_filter()
        # print(test.get_position(ts_with_pred))
        test.get_position(ts_with_pred)
        # print(test.test_)
        # print(test.data_mitigation)
        print(f'mitigation {test.data_mitigation.shape}')
        print(f'detection {test.data_detection.shape}')


    #     "anomaly detection"
    #     # time.sleep(0.2)
    #     test.anomaly_detection()
    #     ts_with_pred = test.timestamp_filter()
    #     print(f"1 filtered> {test.get_position(ts_with_pred)} \t{[ts_with_pred[0][-1], ts_with_pred[1][-1], ts_with_pred[2][-1]]}")
    #     print(f"2 original> {test.get_position(test.vanilla_ts)} ")

        # "working test, pca kmeans"
        # test.pca_k_means_model()
        # # print(test.timestamp_filter())
        # ts_with_pred = test.timestamp_filter()
        # # print(ts_with_pred)
        # if ts_with_pred != None:
        #     print(f"1 filtered> {test.get_position(ts_with_pred)} \t{[ts_with_pred[0][-1], ts_with_pred[1][-1], ts_with_pred[2][-1]]}")
        #     print(f"2 original> {test.get_position(test.vanilla_ts)} ")

