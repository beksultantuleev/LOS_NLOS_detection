'not in use'
import numpy as np
import time
import joblib
from numpy.core.defchararray import count
from numpy.core.fromnumeric import std
from Managers.Mqtt_manager import Mqtt_Manager
from Core_functions.hub_of_functions import deque_manager

mqtt_ = Mqtt_Manager('192.168.0.119', 'id_toa_los')


A_n1 = np.array([[0], [1], [1.8]])
A_n2 = np.array([[6], [0], [2]])
A_n3 = np.array([[3], [3.5], [1]])  # master
# A_n4 = np.array([[3], [5], [1]])  # master
anchor_postion_list = np.array([A_n1, A_n2, A_n3])

# std_list = [0]*3
std_list = [[0, 0], [0,0], [0, 0]]
fixed_ts = [0]*3

def timestamp_filter():
    if mqtt_.processed_data:
        # std_list = [0]*len(mqtt_.processed_data)
        deque_list = [0]*len(mqtt_.processed_data)
        # print(mqtt_.processed_data)
        counter = 0
        for t in mqtt_.processed_data:
            if t[-1] == 0:
                deque_man_list = deque_manager(1, 10, mqtt_, counter)
                deque_list[counter] = deque_man_list
                std_list[counter] = [np.std(deque_man_list), np.average(deque_man_list)]
            
            if t[1]>std_list[counter][1]-std_list[counter][0] and t[1]<std_list[counter][1]+std_list[counter][0]:
                # print(f'this is t1 IF {t[1]}, ')
                fixed_ts[counter] = [t[0], t[1], t[2]]
            else:
                # print(f'this is t1 ELSE {t[1]}, and avrg is {std_list[counter][1]}')
                fixed_ts[counter] = [t[0], std_list[counter][1], t[2]] #put avrg timestamp
            counter+=1
        # print(deque_list)
        # print(std_list)
        return fixed_ts


def get_position(ts_with_los_prediction):
    c = 299792458

    A_n = anchor_postion_list
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

    position = [[x_t[0][0], x_t[1][0], x_t[2][0]], tag_id]
    return position



while True:
    # time.sleep(0.5)
    ts_with_los_pred = timestamp_filter()
    if ts_with_los_pred != None:
        print(get_position(ts_with_los_pred))

# print(65549343+np.random.randint(-10,10))
# anchors = np.array([[4, 116, 65549340, -78.996398, 3.512489],
#                     [4, 116, 65549318, -78.996398, 10.512489],
#                     [4, 116, 65549344, -78.996398, 13.512489]])
# raw_data = anchors[:, -2:]
# pca_model = joblib.load('trained_models/pca.sav')
# k_means_model = joblib.load('trained_models/k_means.sav')

# df = pca_model.transform(raw_data)
# # print(df)
# pred = k_means_model.predict(df)

# # print(pred)
# processed_anchor_data = np.c_[anchors[:,:-2], pred]

# # print(processed_anchor_data)
# print(raw_data.shape)
