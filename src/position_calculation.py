import paho.mqtt.client as mqtt
import numpy as np
import json
import re
import collections
import time
import joblib
from Managers.Mqtt_manager import Mqtt_Manager

# mqtt_inst = Mqtt_Manager("192.168.0.119", topic=[("topic/#", 0)])

# while True:
#     print(mqtt_inst.test)


class Position_finder:
    def __init__(self, anchor_postion_list=[]):
        broker_address = "192.168.0.119"
        print("creating new instance")
        self.client = mqtt.Client('P1')  # create new instance
        self.client.connect(broker_address)  # connect to broker
        self.client.subscribe([("topic/#", 0)])
        self.client.on_message = self.on_message
        self.client.loop_start()
        self.position = []
        self.anchor_postion_list = anchor_postion_list
        self.amount_of_anchors = len(self.anchor_postion_list)
        self.ts_with_los_prediction = [0]*self.amount_of_anchors
        self.raw_anchors_data = [0]*self.amount_of_anchors
        self.processed_anchors_data = None
        self.pca_wait_flag = True
        self.mqtt_ = Mqtt_Manager('192.168.0.119', 'id_toa_los')

    def deque_manager_(self, size, data):
        'updated deque manager, new values at the end of deque'
        size = size+1
        deque_test = collections.deque([])
        while len(deque_test) < size:
            # time.sleep(0.5)
            deque_test.append(data)
            if len(deque_test) == size:
                # deque_test.pop()
                deque_test.popleft()
                return np.array(deque_test)

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

    def msg_splitter(self, anchor_data):
        tag_id = anchor_data[0]
        msg_num = anchor_data[1]
        toa = anchor_data[2]
        los = anchor_data[3]
        # rssi = anchor_data[3]
        # rx_diff = anchor_data[4]
        # return tag_id, msg_num, toa, rssi, rx_diff
        return tag_id, msg_num, toa, los

    def pca_k_means_model(self):
        if self.pca_wait_flag:
            time.sleep(0.9)
            self.pca_wait_flag = False
        raw_anchors_data = np.array(self.raw_anchors_data)

        raw_data = np.array(raw_anchors_data)[:, -2:]
        pca_model = joblib.load('trained_models/pca.sav')
        k_means_model = joblib.load('trained_models/k_means.sav')
        df = pca_model.transform(raw_data)
        pred = k_means_model.predict(df)
        self.processed_anchors_data = np.c_[raw_anchors_data[:, :-2], pred]
        # print(self.processed_anchor_data)

        counter = 0
        for i in self.processed_anchors_data:
            tag_id, msg_num, toa, los = self.msg_splitter(
                anchor_data=i)
            self.ts_with_los_prediction[counter] = [tag_id, toa, los]
            counter += 1
        self.ts_with_los_prediction = np.array(self.ts_with_los_prediction)
        self.client.publish('id_toa_los', f"{self.ts_with_los_prediction}")
        # print(self.ts_with_los_prediction)

    def timestamp_filter(self):
        'i guess it needs to get data from mqtt'
        'now i need to convert numpy array string to array'
        print(f'this is >> {self.mqtt_.processed_data}')
        # deque_list = [0]*len(self.ts_with_los_prediction)
        # # print(self.ts_with_los_prediction)

        # counter = 0
        # for t in self.ts_with_los_prediction:
        #     if t[-1] == 1:
        #         print(self.deque_manager_(4, t[1]))
        #     counter+=1
        pass

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
        test.pca_k_means_model()
        test.timestamp_filter()

        # print(test.get_position(test.ts_with_los_prediction))
        # print(test.ts_with_los_prediction)
        # print(test.raw_anchors_data)
        # print(test.processed_anchor_data)
