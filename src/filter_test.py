from Mqtt_manager import Mqtt_Manager
import collections
from scipy.ndimage import gaussian_filter
import numpy as np
import time

'im trying to implement filters ive already done in previous project this is test file'

mqtt_conn = Mqtt_Manager('localhost', "Position")

def deque_manager_idea(mqtt_data, size):
    size = size+1
    deque_test = collections.deque([])
    while len(deque_test) < size:
        deque_test.appendleft(mqtt_data)
        time.sleep(0.1)
        if len(deque_test) == size:
            deque_test.pop()
            return np.array(deque_test)


while True:
    if mqtt_conn.processed_data:
        lis = deque_manager_idea(mqtt_conn.processed_data[0], 50)
        processed = gaussian_filter(lis, 10)
        print(lis)
        print(f"{processed} *")
        # time.sleep(0.1)
        # print(mqtt_conn.processed_data)
        # print(lis)
        
