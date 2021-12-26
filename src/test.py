'not in use'
import numpy as np
import time
import joblib
from numpy.core.defchararray import count
from numpy.core.fromnumeric import std
from Managers.Mqtt_manager import Mqtt_Manager
from Core_functions.hub_of_functions import deque_manager

mqtt_ = Mqtt_Manager('192.168.0.119', 'id_toa_los')

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
                print(f'this is t1 ELSE {t[1]}')
            counter+=1
        # print(deque_list)
        # print(std_list)
        print(fixed_ts)
    pass


while True:
    # time.sleep(0.5)
    timestamp_filter()

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
