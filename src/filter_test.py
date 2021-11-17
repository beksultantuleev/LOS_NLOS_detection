from Mqtt_manager import Mqtt_Manager
import collections
from scipy.ndimage import gaussian_filter
import numpy as np
import time

'im trying to implement filters ive already done in previous project this is test file'

mqtt_conn = Mqtt_Manager('localhost', "Position")


def deque_manager(number, size):
    'problem in here. we need to refresh mqtt_data,its putting fixed value every time'
    size = size+1
    deque_test = collections.deque([])
    while len(deque_test) < size:
        time.sleep(0.01)
        mqtt_data = mqtt_conn.processed_data[number]
        deque_test.appendleft(mqtt_data)
        if len(deque_test) == size:
            deque_test.pop()
            return np.array(deque_test)


while True:
    if mqtt_conn.processed_data:

        # print(raw_pos)
        # print(mqtt_conn.processed_data)
        # time.sleep(0.5)
        lis = deque_manager(2, 20)
        processed = gaussian_filter(lis, 15)
        # print(lis[-1])
        print(f"{processed[-1]} *")
        # time.sleep(0.1)
        # print(mqtt_conn.processed_data)
        # print(lis)

