from Mqtt_manager import Mqtt_Manager
import collections
from scipy.ndimage import gaussian_filter
import numpy as np
import time

"ive implemented gaussian filter. try to implement others"
mqtt_conn = Mqtt_Manager('localhost', "Position")


def deque_manager(number, size):
    size = size+1
    deque_ = collections.deque([])
    while len(deque_) < size:
        time.sleep(0.01)
        mqtt_data = mqtt_conn.processed_data[number]
        deque_.appendleft(mqtt_data)
        if len(deque_) == size:
            deque_.pop()
            return np.array(deque_)


while True:
    if mqtt_conn.processed_data:
        lis = deque_manager(0, 50)
        processed = gaussian_filter(lis, 5)
        # print(lis[-1])
        # print(f"{processed[-1]} *")
        mqtt_conn.publish("Compare", f"{[lis[-1], processed[-1]]}")
        # print(f'avrg of original: {np.average(lis)} processed: {np.average(processed)}')
        # time.sleep(0.1)
        # print(mqtt_conn.processed_data)
        # print(lis)

