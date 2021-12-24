import paho.mqtt.client as mqtt
import numpy as np
from Managers.Mqtt_manager import Mqtt_Manager
import json
import re
import collections
import time
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
        self.ts = [0]*self.amount_of_anchors
        self.anchors_data = [0]*self.amount_of_anchors

    def deque_manager(self, size, data):
        'updated deque manager, new values at the end of deque'
        size = size+1
        deque_test = collections.deque([])
        while len(deque_test) < size:
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
                    self.anchors_data[counter] = res
                counter += 1

    def msg_splitter(self, anchor_data):
        tag_id = anchor_data[0]
        msg_num = anchor_data[1]
        toa = anchor_data[2]
        rssi = anchor_data[3]
        rx_diff = anchor_data[4]
        return tag_id, msg_num, toa, rssi, rx_diff

    def get_position(self):
        counter = 0
        for i in self.anchors_data:
            tag_id, msg_num, toa, rssi, rx_diff = self.msg_splitter(
                anchor_data=i)
            self.ts[counter] = toa
            counter += 1

        return self.Localisation(self.ts, tag_id)

    def Localisation(self, ts, i):
        M = 3
        c = 299792458

        A_n = self.anchor_postion_list
        n = len(A_n)

        toa = [0]* len(self.ts)
        counter = 0
        for time_stamp in self.ts:
            t = np.float32(time_stamp) * np.float32(15.65e-12)
            toa[counter] = t
            counter+=1

        toa = np.array([toa])
        tdoa = toa - toa[0][0]
        tdoa = tdoa[0][1:]
        D = tdoa*c  # D is 2x1
        # print(self.ts)

        D = D.reshape(len(self.ts)-1, 1)
        A_diff_one = np.array((A_n[-1][0][0]-A_n[1:, 0]), dtype='float32')
        A_diff_two = np.array((A_n[-1][1][0]-A_n[1:, 1]), dtype='float32')
        A_diff_three = np.array((A_n[-1][2][0]-A_n[1:, 2]), dtype='float32')

        A = 2 * np.array([A_diff_one, A_diff_two, A_diff_three, D]).T

        b = D**2 + np.linalg.norm(A_n[-1])**2 - np.sum(A_n[1:, :]**2, 1)
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
        # print(f"position is {x_t[0]}, {x_t[1]}, {x_t[2]} and tag is {i}")
        self.position = [x_t[0][0], x_t[1][0], x_t[2][0]]
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
        time.sleep(0.5)
        # print(test.get_position())
        print(test.anchors_data)
