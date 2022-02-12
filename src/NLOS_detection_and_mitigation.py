import paho.mqtt.client as mqtt
import numpy as np
import json
import re
import time
import joblib
# from Managers.Mqtt_manager import Mqtt_Manager
from Managers.Anchor_manager import Anchor_manager
from Managers.Deque_manager import Deque_manager
from Core_functions.hub_of_functions import *
import tensorflow as tf
from keras.models import load_model
from Managers.MultiOutputClastering import MultiOutputClustering
from sklearn.ensemble import RandomForestClassifier
from sklearn.multioutput import MultiOutputClassifier
from scipy.spatial.distance import cdist

"main class with models and mitigation filters"


class NLOS_detection_and_Mitigation:
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
            self.deque_list[i] = Deque_manager(15)

        'anchor filter'
        self.last_know_position = None

        "pca k means"
        self.pca_wait_flag = True
        self.vanilla_ts = None
        self.pca_model = joblib.load('trained_models/pca.sav')
        self.k_means_model = joblib.load('trained_models/k_means.sav')

        "autoencoder"
        self.autoencoder = load_model('trained_models/anomaly_detection_model')
        self.path = 'src/Training/logs/anomaly_detection/logs_Single_data_input.txt'
        self.threshold = 0.03  # value_extractor("Threshold:", path)
        self.min_val = value_extractor("Min_val:", self.path)
        self.max_val = value_extractor("Max_val:", self.path)

        "grand model"
        self.grand_model = None
        self.data_mitigation = np.empty(shape=(0, self.amount_of_anchors))
        self.data_detection = np.empty(shape=(0, self.amount_of_anchors))
        self.pred_from_mitigation = [0]*self.amount_of_anchors
        self.pred_from_grand_model = None
        self.pred_from_detection = None
        self.data_size = 100
        self.final_data = None
        self.data_collection_complete = False

    def on_message(self, client, userdata, message):
        msg = f'{message.payload.decode("utf")}'
        pattern = re.compile(r'\[.+')
        matches = pattern.finditer(msg)
        actv_anch = []
        for match in matches:
            res = json.loads(match.group(0))
            for i in range(1, self.amount_of_anchors+1):
                top_name = f'topic/{i}'
                if message.topic == top_name:
                    'you can put "i" in "res" to have anchor identification'
                    self.raw_anchors_data[i-1] = [i] + res  # [i]+

        # 'below is check to remove 0 from raw anchor data'
        # if self.data_collection_complete:
        #     for d in self.raw_anchors_data:
        #         if type(d)!= list:
        #             self.raw_anchors_data.remove(d)
        # print(f'this is raw anch data \n{self.raw_anchors_data}')

    def pca_k_means_model(self):
        if self.pca_wait_flag:
            time.sleep(0.9)
            self.pca_wait_flag = False
        raw_anchors_data = np.delete(np.array(self.raw_anchors_data), 2, 1)
        self.vanilla_ts = raw_anchors_data[:, :-2]
        input_data = np.array(raw_anchors_data)[:, -2:]
        df = self.pca_model.transform(input_data)
        self.pred_from_detection = self.k_means_model.predict(df)
        self.processed_anchors_data = np.c_[
            raw_anchors_data[:, :-2], self.pred_from_detection]
        if not self.data_collection_complete:
            self.data_detection = np.append(self.data_detection, np.expand_dims(
                self.pred_from_detection, axis=0), axis=0)

        # print(f'1 from detection {pred}')

    def anomaly_detection(self):
        "true or 1 is LOS"
        raw_anchors_data = np.delete(np.array(self.raw_anchors_data), 2, 1)

        self.vanilla_ts = raw_anchors_data[:, :-2]
        raw_data = np.array(raw_anchors_data)[:, -2:]
        input_data = (np.array(raw_data) -
                      self.min_val) / (self.max_val - self.min_val)
        self.pred_from_detection = predict_anomaly_detection(
            self.autoencoder, input_data, self.threshold)
        self.processed_anchors_data = np.c_[
            raw_anchors_data[:, :-2], self.pred_from_detection]

        if not self.data_collection_complete:
            self.data_detection = np.append(self.data_detection, np.expand_dims(
                self.pred_from_detection, axis=0), axis=0)
        # print(f'1 from detection {pred}')

    def simple_timestamp_filter(self, los=1):
        'update done'
        counter = 0
        # print(self.processed_anchors_data)
        for t in self.processed_anchors_data:
            if t[-1] == los:  # LOS
                self.deque_list[counter].append_data(t[2])
                # self.modified_ts[counter] = [t[0], t[1], t[2]]
                'try to put average'
                self.modified_ts[counter] = [
                    t[0], t[1], self.deque_list[counter].get_half_array_avrg(), t[3]]  # put half array arvg
            else:
                # self.modified_ts[counter] = [t[0], self.deque_list[counter].get_last_value(), t[2]]
                self.modified_ts[counter] = [
                    t[0], t[1], self.deque_list[counter].get_avrg(), t[3]]
            counter += 1
        return np.array(self.modified_ts)

    def smart_timestamp_filter(self, los=1):
        counter = 0
        for t in self.processed_anchors_data:
            'get right std and avrgs'
            if t[-1] == los:  # LOS
                self.deque_list[counter].append_data(t[1])
            'apply those stds and avrgs'
            if t[1] > self.deque_list[counter].get_avrg()-self.deque_list[counter].get_std() and t[1] < self.deque_list[counter].get_avrg()+self.deque_list[counter].get_std():
                'prediction of mitigation'
                self.pred_from_mitigation[counter] = 1
                if t[-1] == los:
                    # self.modified_ts[counter] = [t[0], t[1], t[2]]
                    self.modified_ts[counter] = [
                        t[0], self.deque_list[counter].get_half_array_avrg(), t[2]]  # put half array avrg
                # else:
                #     self.modified_ts[counter] = [t[0], self.deque_list[counter].get_last_value(), t[2]]
            else:
                self.pred_from_mitigation[counter] = 0

                self.modified_ts[counter] = [
                    t[0], self.deque_list[counter].get_avrg(), t[2]]  # put avrg timestamp
                # self.modified_ts[counter] = [
                #     t[0], self.deque_list[counter].get_last_value(), t[2]] #put last los value
            # print(f"std>> {self.deque_list[counter].get_std()}")
            counter += 1

        if not self.data_collection_complete:
            self.data_mitigation = np.append(self.data_mitigation, np.expand_dims(
                self.pred_from_mitigation, axis=0), axis=0)
            if len(self.data_mitigation) == self.data_size:
                self.data_collection_complete = True
                'save data '
                self.final_data = np.append(
                    self.data_detection, self.data_mitigation, axis=1)
                'further saving data'
                filename = f"grand_final_data_{self.data_size}.csv"
                np.savetxt(filename, self.final_data, delimiter=",")

                'Grand model training process'
                print("Model training process is started")
                rf = RandomForestClassifier(max_depth=2)
                Multi_output_clustering = MultiOutputClustering(
                    data_for_training=self.final_data)
                Multi_output_clustering.label_creation()
                model_location = 'trained_models/multioutput_model.sav'
                Multi_output_clustering.multiOutputClassifier(
                    rf, filename=model_location)
                self.grand_model = joblib.load(model_location)
        else:
            self.launch_grand_model()

        return self.modified_ts

    def launch_grand_model(self):
        input_data = np.concatenate(
            [self.pred_from_detection, self.pred_from_mitigation], axis=0)
        # print(f'this is input data')
        self.pred_from_grand_model = self.grand_model.predict([input_data])
        # print(f'grand model {self.pred_from_grand_model} input_data {input_data}')

    def get_position(self, ts_with_A_n, in_2d=False):
        'make this as only position estimation logic'
        "that takes [tagid, ts, lospred] values only"

        ts_with_los_prediction, A_n = ts_with_A_n

        n = len(A_n)
        c = 299792458

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

        self.position = [[x_t[0][0], x_t[1][0], x_t[2][0]], tag_id] if not in_2d else [
            [x_t[0][0], x_t[1][0]], tag_id]
        return self.position

    def simple_anchor_selection_filter(self, ts_with_los_prediction, los=1, in_2d=False):
        'this anchor id logic is embedded'
        los_anchors = np.empty(shape=(0, 4))

        nlos_anchors = np.empty(shape=(0, 4))
        A_n = self.anchor_postion_list

        'logic of excluding bad anchors here'

        number_of_anchors_for_pos_estimation = 3
        for value in ts_with_los_prediction:

            if value[-1] == los:
                # print(value)
                los_anchors = np.append(los_anchors, np.expand_dims(
                    value, axis=0), axis=0)
            else:
                nlos_anchors = np.append(nlos_anchors, np.expand_dims(
                    value, axis=0), axis=0)

        # print(f'los {los_anchors}')
        # print(f'nlos {nlos_anchors}')

        if len(los_anchors) >= number_of_anchors_for_pos_estimation:
            los_anchor_indices = los_anchors[:, 0].astype(
                int) - 1  # subsract 1 cuz A_n starts with 0
            # print(los_anchor_indices)
            A_n = A_n[los_anchor_indices, :, :]
            # print(A_n)
            ts_with_los_prediction = los_anchors[:, 1:]
            # print(ts_with_los_prediction)
        else:
            if len(los_anchors) != 0:
                count = 0
                while len(los_anchors) != number_of_anchors_for_pos_estimation:
                    los_anchors = np.append(los_anchors, np.expand_dims(
                        nlos_anchors[count], axis=0), axis=0)
                    count += 1
                los_anchor_indices = los_anchors[:, 0].astype(int) - 1
    #             # print(los_anchor_indices)
                A_n = A_n[los_anchor_indices, :, :]
                ts_with_los_prediction = los_anchors[:, 1:]
            else:
                # num_of
                nlos_anchor_indices = nlos_anchors[:, 0].astype(
                    int)[:number_of_anchors_for_pos_estimation] - 1
                A_n = A_n[nlos_anchor_indices, :, :]
                # print(A_n)
                ts_with_los_prediction = nlos_anchors[:
                                                      number_of_anchors_for_pos_estimation, 1:]

        ts_with_A_n = ts_with_los_prediction, A_n
        # print(ts_with_A_n)
        # return ts_with_A_n
        return self.get_position(ts_with_A_n, in_2d)

    def publish(self):
        'first is filtered and second is original'
        # ts_with_pred = self.smart_timestamp_filter()
        ts_with_pred = self.simple_timestamp_filter()
        filtered = self.simple_anchor_selection_filter(ts_with_pred)[0]
        original = self.simple_anchor_selection_filter(self.vanilla_ts)[0]
        payload_ = f'[{filtered}, {original}]'
        self.client.publish('positions', payload_)
        # print(
        #     f'1 filtered {filtered} \t {np.concatenate([self.pred_from_detection, self.pred_from_mitigation], axis=0)} {self.pred_from_grand_model}')
        print(
            f'1 filtered {np.array(self.raw_anchors_data)} \t  {self.pred_from_detection}')
        print(f'2 original {original}')

    def project_athena(self, ts_with_los_prediction, los=1):
        'in development'
        'it will become smart anchor selection filter'
        'embedd convex hull logic as well'
        # print(ts_with_los_prediction)
        A_n = self.anchor_postion_list

        los_anchors = np.empty(shape=(0, 4))
        nlos_anchors = np.empty(shape=(0, 4))

        # print(ts_with_los_prediction)
        for value in ts_with_los_prediction:
            if value[-1] == los:
                # print(value)
                los_anchors = np.append(los_anchors, np.expand_dims(
                    value, axis=0), axis=0)
            else:
                nlos_anchors = np.append(nlos_anchors, np.expand_dims(
                    value, axis=0), axis=0)
        # print(f'los {los_anchors}')
        # print(f'nlos {nlos_anchors}')

        coordinates = [0]
        nlos_id = []
        if len(los_anchors) >= 3:
            ts_with_An_los = get_ts_with_An(los_anchors, A_n)
            coordinates[0] = self.get_position(ts_with_An_los, in_2d=True)[0]
            if len(nlos_anchors) != 0:
                for nlos_anch in nlos_anchors:
                    nlos_id.append(nlos_anch[0])
                    los_anchors = np.append(los_anchors, np.expand_dims(
                        nlos_anch, axis=0), axis=0)
                    ts_with_An_los = get_ts_with_An(los_anchors, A_n)

                    coordinates.append(self.get_position(
                        ts_with_An_los, in_2d=True)[0])

            euclid_dist_between_points = cdist(
                coordinates, coordinates, "euclidean")[0, :]
            # print(euclid_dist_between_points)
            # print(nlos_id)
            distance_deviation_and_anchor = list(
                zip(np.delete(euclid_dist_between_points, 0), nlos_id))
            # print(distance_deviation_and_anchor)
            for value in distance_deviation_and_anchor:
                if value[0] > 1.5:  # threshold
                    "delete  bad anchors"
                    los_anchors = los_anchors[los_anchors[:, 0] != value[1]]
            # print(los_anchors)
            ts_with_An_los = get_ts_with_An(los_anchors, A_n)
            estimated_position = self.get_position(ts_with_An_los)
            self.last_know_position = estimated_position[0]
            # print(f'in if: >{len(coordinates)}')

            return estimated_position
        else:
            coordinates[0] = self.last_know_position[:-1]
            # print(coordinates)
            for nlos_anch in nlos_anchors:
                nlos_id.append(nlos_anch[0])
                los_anchors = np.append(los_anchors, np.expand_dims(
                    nlos_anch, axis=0), axis=0)
                ts_with_An_los = get_ts_with_An(los_anchors, A_n)

                coordinates.append(self.get_position(
                    ts_with_An_los, in_2d=True)[0])
            # print(f'in else: >{nlos_id}')
            euclid_dist_between_points = cdist(
                coordinates, coordinates, "euclidean")[0, :]
            print(euclid_dist_between_points)


if __name__ == "__main__":

    A_n1 = np.array([[2], [2], [0.9]])
    A_n2 = np.array([[0], [0], [0.5]])
    A_n3 = np.array([[5], [0], [1.8]])  # master
    A_n4 = np.array([[3], [5], [1]])  # master
    A_n5 = np.array([[2], [5], [4]])  # master
    anchors_pos = np.array([A_n1, A_n2, A_n3, A_n4, A_n5])
    # anchors_pos = np.array([A_n1, A_n2, A_n3])
    # print(A_n1.shape)
    test = NLOS_detection_and_Mitigation(anchor_postion_list=anchors_pos)
    while True:
        'adding anchor number from start'
        time.sleep(0.4)
        test.anomaly_detection()
        ts_with_pred = test.simple_timestamp_filter()
        # pos = test.get_position(
        #     (ts_with_pred[:, 1:], anchors_pos), in_2d=True)
        pos = test.project_athena(
            ts_with_pred)

        print(pos)

        'with grand model'
        # time.sleep(0.1)
        # # test.anomaly_detection()
        # test.pca_k_means_model()
        # test.publish()

        "anomaly detection"
        # time.sleep(0.2)
        # test.anomaly_detection()
        # ts_with_pred = test.timestamp_filter()
        # print(f"1 filtered> {test.get_position(ts_with_pred)} \t{[ts_with_pred[0][-1], ts_with_pred[1][-1], ts_with_pred[2][-1]]}")
        # print(f"2 original> {test.get_position(test.vanilla_ts)} ")

        # "working test, pca kmeans"
        # test.pca_k_means_model()
        # # print(test.timestamp_filter())
        # ts_with_pred = test.timestamp_filter()
        # # print(ts_with_pred)
        # if ts_with_pred != None:
        #     print(f"1 filtered> {test.get_position(ts_with_pred)} \t{[ts_with_pred[0][-1], ts_with_pred[1][-1], ts_with_pred[2][-1]]}")
        #     print(f"2 original> {test.get_position(test.vanilla_ts)} ")
