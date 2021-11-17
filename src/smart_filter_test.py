from Mqtt_manager import Mqtt_Manager
import time
import numpy as np
import collections
from scipy.spatial import distance
mqtt_conn = Mqtt_Manager('localhost', "Position")


def deque_manager_with_ts(size):
    size = size+1
    deque_ = collections.deque([])
    while len(deque_) < size:
        # time.sleep(0.5)
        time.sleep(1) #will indicate certain distance per second
        mqtt_data = np.array(mqtt_conn.processed_data) if mqtt_conn.processed_data else np.array([0,0,0])
        deque_.appendleft((mqtt_data, time.time()))
        if len(deque_) == size:
            deque_.pop()
            return np.array(deque_)

def diff(lis):
    return (lis[:-1]-lis[1:])[0]



while True:
    velocity = None
    los = True
    data = np.array(mqtt_conn.processed_data) if mqtt_conn.processed_data else np.array([0,0,0])
    if los:
        data_deque_with_ts = deque_manager_with_ts(2)
        # print(data_deque_with_ts.shape)
        position_data = data_deque_with_ts[:,0]
        time_data = data_deque_with_ts[:,1]

        dst = distance.euclidean(position_data[0], position_data[-1])
        # print(dst)
        velocity = dst/diff(time_data)
        print(velocity)
        



# ts = time.time()
# st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
# print(st)
# print(ts)
