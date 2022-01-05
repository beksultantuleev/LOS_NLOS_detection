'not in use'
import numpy as np
import time
import joblib
from numpy.core.defchararray import count
from numpy.core.fromnumeric import std
from tensorflow.python.ops.gen_math_ops import truncate_div_eager_fallback
from Managers.Mqtt_manager import Mqtt_Manager
from Core_functions.hub_of_functions import deque_manager
from Managers.Deque_manager import Deque_manager
'after making deque manager i dont need this anymore. everything in position calculation file'

mqtt_ = Mqtt_Manager('192.168.0.119', 'id_toa_los')


A_n1 = np.array([[0], [1], [1.8]])
A_n2 = np.array([[6], [0], [2]])
A_n3 = np.array([[3], [3.5], [1]])  # master
A_n4 = np.array([[3], [5], [1]])  # master
anchor_postion_list = np.array([A_n1, A_n2, A_n3, A_n4])


def get_position(ts_with_los_prediction, exclude_nlos=False):
    los = 1
    los_anchors = []
    nlos_anchors = []
    A_n = anchor_postion_list
    # print(np.array(ts_with_los_prediction))
    'add logic of excluding bad anchors here'
    if exclude_nlos:
        number_of_anchors_for_pos_estimation = 3
        for counter, value in enumerate(ts_with_los_prediction):
            anchors_with_counter = np.append(value, np.array([counter]), axis=0)
            if value[-1] == los:
                los_anchors.append(anchors_with_counter)
            else:
                nlos_anchors.append(anchors_with_counter)
        los_anchors = np.array(los_anchors)
        nlos_anchors = np.array(nlos_anchors)
        # print(los_anchors)
        # print(nlos_anchors)
        if len(los_anchors) >= number_of_anchors_for_pos_estimation:
            los_anchor_indices = los_anchors[:, -1].astype(int)
            A_n = A_n[los_anchor_indices, :, :]
            ts_with_los_prediction = los_anchors[:, :-1]
        else:
            if len(los_anchors) != 0:
                count = 0
                while len(los_anchors) != number_of_anchors_for_pos_estimation:
                    los_anchors = np.append(los_anchors, np.expand_dims(
                        nlos_anchors[count], axis=0), axis=0)
                    count += 1
                los_anchor_indices = los_anchors[:, -1].astype(int)
                # print(los_anchor_indices)
                A_n = A_n[los_anchor_indices, :, :]
                print(A_n)
                ts_with_los_prediction = los_anchors[:, :-1]
            else:
                # num_of
                nlos_anchor_indices = nlos_anchors[:, -1].astype(int)[:number_of_anchors_for_pos_estimation]
                A_n = A_n[nlos_anchor_indices, :, :]
                # print(A_n)
                ts_with_los_prediction = nlos_anchors[:number_of_anchors_for_pos_estimation, :-1]
                # print(ts_with_los_prediction)

    n = len(A_n)
    c = 299792458

    toa = [0] * len(ts_with_los_prediction)
    counter = 0
    for time_stamp_with_los in ts_with_los_prediction:
        t = np.float32(time_stamp_with_los[1]) * np.float32(15.65e-12)
        toa[counter] = t
        counter += 1

    toa = np.array([toa])
    # print(toa)
    tdoa = toa - toa[0][0]  # changed here
    # print(tdoa)
    tdoa = tdoa[0][1:]
    # print(tdoa)
    D = tdoa*c  # D is 2x1
    # print(D)

    D = D.reshape(len(ts_with_los_prediction)-1, 1)
    # print(D)
    A_diff_one = np.array((A_n[0][0][0]-A_n[1:, 0]), dtype='float32')
    # print(A_diff_one)
    A_diff_two = np.array((A_n[0][1][0]-A_n[1:, 1]), dtype='float32')
    # print(A_diff_two)
    A_diff_three = np.array((A_n[0][2][0]-A_n[1:, 2]), dtype='float32')
    # print(A_diff_three)

    A = 2 * np.array([A_diff_one, A_diff_two, A_diff_three, D]).T
    # print(A)

    b = D**2 + np.linalg.norm(A_n[0])**2 - np.sum(A_n[1:, :]**2, 1)
    x_t0 = np.dot(np.linalg.pinv(A), b)
    # print(x_t0)

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

    position = [[x_t[0][0], x_t[1][0], x_t[2][0]], tag_id]
    return position


# while True:
    # time.sleep(0.5)
ts_with_pred = [[4.0, 65549325.0, 1.0],
                [4.0, 65549353.6, 1.0],
                [4.0, 65549427.5, 1.0],
                [4.0, 65549361.75, 0.0]]
print(get_position(ts_with_pred, exclude_nlos=True))
