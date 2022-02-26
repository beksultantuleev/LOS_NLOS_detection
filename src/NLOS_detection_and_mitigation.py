from logging import exception
import paho.mqtt.client as mqtt
import numpy as np
import json
import re
import time
import joblib
from sklearn.cluster import k_means
# from Managers.Mqtt_manager import Mqtt_Manager
# from Managers.Anchor_manager import Anchor_manager
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
        self.number_of_features = 5
        self.vanilla_ts = None

        self.modified_ts = [0]*len(self.anchor_postion_list)
        self.deque_list = [0]*len(self.anchor_postion_list)
        for i in range(len(self.anchor_postion_list)):
            self.deque_list[i] = Deque_manager(
                8, divider_percentage=0.5)

        'anchor filter'
        self.last_know_position = []
        self.last_know_pos_object = Deque_manager(3)
        self.set_threshold = 0.3

        "pca k means"
        self.wait_flag = True
        self.pca_model = joblib.load('trained_models/pca.sav')
        self.k_means_model = joblib.load('trained_models/k_means.sav')
        self.scaler_pca = joblib.load(
            'trained_models/standard_scaler_pca_kmeans.save')

        "pca gmm"
        self.gmm_model = joblib.load('trained_models/gmm.sav')

        "autoencoder"
        self.autoencoder = load_model('trained_models/anomaly_detection_model')
        self.path = 'src/Training/logs/anomaly_detection/logs_Single_data_input.txt'
        # value_extractor("Threshold:", self.path) #0.004575138445943594
        self.threshold = 0.01
        self.min_val = value_extractor("Min_val:", self.path)
        self.max_val = value_extractor("Max_val:", self.path)

        "grand model"
        self.grand_model = None
        self.data_mitigation = np.empty(shape=(0, self.amount_of_anchors))
        self.data_detection = np.empty(shape=(0, self.amount_of_anchors))
        self.pred_from_mitigation = [1]*self.amount_of_anchors
        self.pred_from_grand_model = []
        self.pred_from_detection = None
        self.data_size = 100
        self.final_data = None
        self.data_collection_complete = False
        self.grand_model_data = np.empty(shape=(0, 9))

        "filtered vs original data"
        self.filtered_data = np.empty(shape=(0, 2))
        self.original_data = np.empty(shape=(0, 2))
        self.detection_name = ''
        self.filter_name = ''
        self.anchor_selection_name = ''

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
                    self.raw_anchors_data[i-1] = [i] + res

    def set_data_size(self, size):
        self.data_size = size

    def pca_k_means_model_or_gmm(self, k_means=True):
        if self.wait_flag:
            time.sleep(0.9)
            self.wait_flag = False
        raw_anchors_data = np.delete(np.array(self.raw_anchors_data), 2, 1)
        self.vanilla_ts = raw_anchors_data[:, :-(self.number_of_features)]
        input_data = np.array(raw_anchors_data)[:, -(self.number_of_features):]
        scaled_data = self.scaler_pca.transform(input_data)
        df = self.pca_model.transform(scaled_data)
        if k_means:
            self.pred_from_detection = self.k_means_model.predict(df)
            self.detection_name = '_k_means'
        else:
            self.pred_from_detection = self.gmm_model.predict(df)
            self.detection_name = '_gmm'

        self.processed_anchors_data = np.c_[
            raw_anchors_data[:, :-(self.number_of_features)], self.pred_from_detection]
        if not self.data_collection_complete:
            self.data_detection = np.append(self.data_detection, np.expand_dims(
                self.pred_from_detection, axis=0), axis=0)

    def anomaly_detection(self):
        if self.wait_flag:
            time.sleep(0.9)
            self.wait_flag = False
        self.detection_name = '_anomaly'
        raw_anchors_data = np.delete(np.array(self.raw_anchors_data), 2, 1)
        self.vanilla_ts = raw_anchors_data[:, :-(self.number_of_features)]
        raw_data = np.array(raw_anchors_data)[:, -(self.number_of_features):]
        input_data = (np.array(raw_data) -
                      self.min_val) / (self.max_val - self.min_val)
        self.pred_from_detection = predict_anomaly_detection(
            self.autoencoder, input_data, self.threshold)
        self.processed_anchors_data = np.c_[
            raw_anchors_data[:, :-(self.number_of_features)], self.pred_from_detection]
        if not self.data_collection_complete:
            self.data_detection = np.append(self.data_detection, np.expand_dims(
                self.pred_from_detection, axis=0), axis=0)

    def simple_timestamp_filter(self, los=1, median=True):
        self.filter_name = '_simple_filter_avrg'
        if median:
            self.filter_name = '_simple_filter_median'
        counter = 0
        for t in self.processed_anchors_data:
            if t[-1] == los:  # LOS
                self.deque_list[counter].append_data(t[2])
                if median:
                    self.modified_ts[counter] = [
                        t[0], t[1], self.deque_list[counter].get_fraction_array_median(), t[3]]
                else:
                    self.modified_ts[counter] = [
                        t[0], t[1], self.deque_list[counter].get_fraction_array_avrg(), t[3]]
            else:
                'try to test with median value instead of mean'
                if median:
                    self.modified_ts[counter] = [
                        t[0], t[1], self.deque_list[counter].get_median(), t[3]]  # get_fraction_array_median()
                else:
                    self.modified_ts[counter] = [
                        t[0], t[1], self.deque_list[counter].get_avrg(), t[3]]  # get_fraction_array_avrg()
            counter += 1
        return np.array(self.modified_ts)

    def std_ts_filter(self, los=1, median=True):
        'test this logic'
        self.filter_name = '_std_fltr_avrg'
        if median:
            self.filter_name = '_std_fltr_median'

        counter = 0
        for t in self.processed_anchors_data:
            'get right std and avrgs'
            if t[-1] == los:  # LOS
                self.deque_list[counter].append_data(t[2])
            'apply those stds and avrgs'
            minimum_value = self.deque_list[counter].get_avrg(
            )-self.deque_list[counter].get_std()
            maximum_value = self.deque_list[counter].get_avrg(
            )+self.deque_list[counter].get_std()
            # print(
            #     f'Anch>{counter}, TS> {t[2]}, min> {minimum_value:.2f}, max> {maximum_value:.2f}  std > {self.deque_list[counter].get_std():.2f} \t {self.pred_from_mitigation}')

            if t[2] > minimum_value and t[2] < maximum_value:
                'prediction of mitigation'
                self.pred_from_mitigation[counter] = 1
                if median:
                    self.modified_ts[counter] = [
                        t[0], t[1], self.deque_list[counter].get_fraction_array_median(), t[3]]
                else:
                    self.modified_ts[counter] = [
                        t[0], t[1], self.deque_list[counter].get_fraction_array_avrg(), t[3]]
            else:
                self.pred_from_mitigation[counter] = 0

                if median:
                    self.modified_ts[counter] = [
                        t[0], t[1], self.deque_list[counter].get_median(), t[3]]
                else:
                    self.modified_ts[counter] = [
                        t[0], t[1], self.deque_list[counter].get_avrg(), t[3]]  # put avrg timestamp
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
                filename = f"data/grand_mode_data/grand_final_data_{self.data_size}.csv"
                np.savetxt(filename, self.final_data, delimiter=",")

                'Grand model training process'
                print("Model training process is started")
                rf = RandomForestClassifier(
                    max_depth=3, class_weight="balanced")
                Multi_output_clustering = MultiOutputClustering(
                    data_for_training=self.final_data, detection_weight=0.5)  # under question
                Multi_output_clustering.label_creation()
                model_location = 'trained_models/multioutput_model.sav'
                Multi_output_clustering.multiOutputClassifier(
                    rf, filename=model_location)
                self.grand_model = joblib.load(model_location)
        else:
            self.launch_grand_model()

        return np.array(self.modified_ts)

    def launch_grand_model(self):
        input_data = np.concatenate(
            [self.pred_from_detection, self.pred_from_mitigation], axis=0)
        # print(f'this is input data {input_data}')
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

    def los_nlos_divider(self, ts_with_los_prediction, los=1):
        los_anchors = np.empty(shape=(0, 4))
        nlos_anchors = np.empty(shape=(0, 4))

        for value in ts_with_los_prediction:
            if value[-1] == los:
                los_anchors = np.append(los_anchors, np.expand_dims(
                    value, axis=0), axis=0)
            else:
                nlos_anchors = np.append(nlos_anchors, np.expand_dims(
                    value, axis=0), axis=0)
        return los_anchors, nlos_anchors

    def simple_anchor_selection_filter(self, ts_with_los_prediction, los=1, in_2d=False):
        self.anchor_selection_name = '_smpl_anch_sel'
        number_of_anchors_for_pos_estimation = 3
        A_n = self.anchor_postion_list
        los_anchors, nlos_anchors = self.los_nlos_divider(
            ts_with_los_prediction)
        # print(f'los {los_anchors}')
        # print(f'nlos {nlos_anchors}')
        if len(los_anchors) >= number_of_anchors_for_pos_estimation:
            ts_with_A_n = get_ts_with_An(los_anchors, A_n)
        else:
            np.random.shuffle(nlos_anchors)
            los_anchors = np.concatenate(
                [los_anchors, nlos_anchors], axis=0)[:3, :]
            ts_with_A_n = get_ts_with_An(los_anchors, A_n)

        return self.get_position(ts_with_A_n, in_2d)

    def get_selected_anchors(self, los_anchors, nlos_anchors, A_n, coordinates, nlos_id, set_threshold=0.5):
        if len(nlos_anchors) != 0:
            if len(los_anchors) < 2:
                nlos_anchors = np.concatenate(
                    [los_anchors, nlos_anchors], axis=0)
                los_anchors = nlos_anchors[:2, :]
                for nlos_anch in nlos_anchors[2:, :]:
                    nlos_id.append(nlos_anch[0])
                    los_anchors = np.append(los_anchors, np.expand_dims(
                        nlos_anch, axis=0), axis=0)
                    ts_with_An_los = get_ts_with_An(los_anchors, A_n)
                    coordinates.append(self.get_position(
                        ts_with_An_los, in_2d=True)[0])
            else:
                for nlos_anch in nlos_anchors:
                    nlos_id.append(nlos_anch[0])
                    los_anchors = np.append(los_anchors, np.expand_dims(
                        nlos_anch, axis=0), axis=0)
                    ts_with_An_los = get_ts_with_An(los_anchors, A_n)
                    coordinates.append(self.get_position(
                        ts_with_An_los, in_2d=True)[0])

        euclid_dist_between_points = cdist(
            coordinates, coordinates, "euclidean")[0, :]
        distance_deviation_and_anchor = list(
            zip(np.delete(euclid_dist_between_points, 0), nlos_id))
        for value in distance_deviation_and_anchor:
            if value[0] > set_threshold:  # threshold
                "delete  bad anchors"
                los_anchors = los_anchors[los_anchors[:, 0] != value[1]]
        # print(f'test nlos anch {nlos_id}')
        return los_anchors

    def improved_anchor_selection_filter(self, ts_with_los_prediction, los=1, in_2d=False):
        self.anchor_selection_name = '_imp_anch_sel'
        A_n = self.anchor_postion_list
        los_anchors, nlos_anchors = self.los_nlos_divider(
            ts_with_los_prediction)
        coordinates = [0]
        nlos_id = []
        if len(los_anchors) >= 3:
            ts_with_An_los = get_ts_with_An(los_anchors, A_n)
            'calculate first true position'
            coordinates[0] = self.get_position(ts_with_An_los, in_2d=True)[0]
            los_anchors = self.get_selected_anchors(
                los_anchors, nlos_anchors, A_n, coordinates, nlos_id, set_threshold=self.set_threshold)

            ts_with_An_los = get_ts_with_An(los_anchors, A_n)
            estimated_position = self.get_position(ts_with_An_los, in_2d=in_2d)
            'last know pos update'
            # self.last_know_position = estimated_position[0][:-1] if not in_2d else estimated_position[0]

            last_pos_data = estimated_position[0][:-
                                                  1] if not in_2d else estimated_position[0]
            self.last_know_pos_object.append_data(last_pos_data)
            self.last_know_position = self.last_know_pos_object.get_median()
            return estimated_position
        else:
            # print(self.last_know_position)
            if len(self.last_know_position) != 0:
                coordinates[0] = self.last_know_position
            else:
                coordinates[0] = self.get_position(
                    (ts_with_los_prediction[:, 1:], A_n), in_2d=True)[0]

            los_anchors = self.get_selected_anchors(
                los_anchors, nlos_anchors, A_n, coordinates, nlos_id, set_threshold=0.5)
            ts_with_An_los = get_ts_with_An(los_anchors, A_n)
            estimated_position = self.get_position(ts_with_An_los, in_2d=in_2d)
            'update last known pos data'
            # self.last_know_position = estimated_position[0][:-1] if not in_2d else estimated_position[0]

            last_pos_data = estimated_position[0][:-
                                                  1] if not in_2d else estimated_position[0]
            self.last_know_pos_object.append_data(last_pos_data)
            self.last_know_position = self.last_know_pos_object.get_median()

            return estimated_position

    def anchor_selection_with_grand_model(self, ts_with_los_prediction, los=1, in_2d=False):
        '''try smth like if GM not ready, use simple anchor sel.
        as soon it is ready, use this filter'''
        if len(self.pred_from_grand_model) == 0:
            return self.simple_anchor_selection_filter(
                ts_with_los_prediction, in_2d=in_2d)
        else:
            self.anchor_selection_name = '_grand_model_anch_sel'
            number_of_anchors_for_pos_estimation = 3
            A_n = self.anchor_postion_list
            # self.processed_anchors_data = np.c_[
            #     raw_anchors_data[:, :-(self.number_of_features)], self.pred_from_detection]
            'change ml predictions to grand model predictions'
            ts_with_los_prediction = np.c_[
                ts_with_los_prediction[:, :-1], self.pred_from_grand_model[0]]#
            los_anchors, nlos_anchors = self.los_nlos_divider(
                ts_with_los_prediction)
            if len(los_anchors) >= number_of_anchors_for_pos_estimation:
                ts_with_A_n = get_ts_with_An(los_anchors, A_n)
            else:
                np.random.shuffle(nlos_anchors)
                los_anchors = np.concatenate(
                    [los_anchors, nlos_anchors], axis=0)[:3, :]
                ts_with_A_n = get_ts_with_An(los_anchors, A_n)
            return self.get_position(ts_with_A_n, in_2d)

    def publish(self, save_data=False, still=True, median=True, moving_tag=True):
        'first is filtered and second is original'
        # ts_with_pred = test.simple_timestamp_filter(median=median)
        ts_with_pred = self.std_ts_filter(median=median)
        # filtered = test.get_position(
        #     (ts_with_pred[:, 1:], self.anchor_postion_list), in_2d=True)
        # filtered = test.improved_anchor_selection_filter(
        #     ts_with_pred, in_2d=True)
        filtered = self.simple_anchor_selection_filter(
            ts_with_pred, in_2d=True)
        original = self.get_position(
            (self.vanilla_ts[:, 1:], self.anchor_postion_list), in_2d=True)
        # print(filtered)
        # print(original)
        payload_ = f'[{filtered[0]}, {original[0]}]'
        'save data '
        if save_data:

            self.filtered_data = np.append(self.filtered_data, np.expand_dims(
                filtered[0], axis=0), axis=0)
            self.original_data = np.append(self.original_data, np.expand_dims(
                original[0], axis=0), axis=0)
            if len(self.original_data) == self.data_size:
                comparison_data = np.append(
                    self.filtered_data, self.original_data, axis=1)
                still_name = 'still'
                if not still:
                    still_name = 'move'
                if moving_tag:
                    moving_name = 'moving_tag_'
                filename = f"data/filtered_vs_original_data/{moving_name}{still_name}_comp{self.detection_name+self.filter_name+self.anchor_selection_name}_{self.data_size}.csv"
                np.savetxt(filename, comparison_data, delimiter=",")
                print(
                    f'data saved! shape is>>>>>>>>>>>> {comparison_data.shape}')
                raise exception('done')

        self.client.publish('positions', payload_)
        # if len(self.pred_from_grand_model) != 0:
        #     det_mitig_data_grand_model = np.concatenate(
        #         [self.pred_from_detection, self.pred_from_mitigation, self.pred_from_grand_model[0]], axis=0)

        #     self.grand_model_data = np.append(self.grand_model_data, np.expand_dims(
        #         det_mitig_data_grand_model, axis=0), axis=0)
        #     print(
        #         f'filt {filtered[0]} shape is {self.grand_model_data.shape} \t\t {det_mitig_data_grand_model}')  # {self.pred_from_grand_model}
        #     if len(self.grand_model_data) == self.data_size:
        #         columns_ = ['det1', 'det2', 'det3', 'mit1',
        #                     'mit2', 'mit3', 'grand1', 'grand2', 'grand3']

        #         grand_model_test = pd.DataFrame(
        #             self.grand_model_data, columns=columns_)
        #         grand_model_test.to_csv(
        #             'grand_model_test_data_all_anchors.csv', index=False)
        #         print(
        #             f'data saved! shape is>>>>>>>>>>>> {self.grand_model_data.shape}')
        #         raise exception('done')

        # else:
        #     print(
        #         f'grand model is training! {np.concatenate([self.pred_from_detection, self.pred_from_mitigation], axis=0)}')


if __name__ == "__main__":

    A_n1 = np.array([[2], [0], [1]])
    A_n2 = np.array([[5], [2.3], [1]])
    A_n3 = np.array([[0], [3], [1]])  # master
    A_n4 = np.array([[3], [5], [1]])
    # A_n5 = np.array([[2], [5], [4]])
    anchors_pos = np.array([A_n1, A_n2, A_n3, A_n4])
    # anchors_pos = np.array([A_n1, A_n2, A_n3])
    # print(A_n1.shape)
    test = NLOS_detection_and_Mitigation(anchor_postion_list=anchors_pos)
    test.set_data_size(200)  # 200
    while True:
        'testing'
        time.sleep(0.1)
        test.anomaly_detection()
        # test.pca_k_means_model_or_gmm(k_means=False)
        # test.publish(save_data=False, still=True,
        #              median=True, moving_tag=False)
        ts_with_pred = test.std_ts_filter()
        pos = test.anchor_selection_with_grand_model(ts_with_pred, in_2d=True)

        # print(test.threshold)
        # print(test.vanilla_ts)
        # ts_with_pred = test.simple_timestamp_filter()
        # pos = test.get_position(
        #     (test.vanilla_ts[:, 1:], anchors_pos), in_2d=True)
        # pos = test.smart_anchor_selection_filter(
        #     ts_with_pred, in_2d=True)

        print(pos)

        'with grand model'
        # time.sleep(0.1)
        # test.anomaly_detection()
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
