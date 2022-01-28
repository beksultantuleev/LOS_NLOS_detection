from Managers.Mqtt_manager import Mqtt_Manager
import time
import numpy as np
import collections
from scipy.spatial import distance
import math
from Controllers_and_KF.LQR_controller import LQRcontroller
from Controllers_and_KF.KalmanFilter import KalmanFilterUWB

'dead reckoning, in beta mode'

mqtt_conn = Mqtt_Manager('localhost', "Position")
mqtt_los = Mqtt_Manager('localhost', "LOS")
lqr = LQRcontroller()
q = np.ones((3, 1))
p = np.zeros((3, 3))
state = KalmanFilterUWB(q)


def deque_manager_with_ts(size):
    size = size+1
    deque_ = collections.deque([])
    while len(deque_) < size:
        'time sleep will indicate certain distance per second'
        time.sleep(0.1)
        mqtt_data = np.array(
            mqtt_conn.processed_data) if mqtt_conn.processed_data else np.array([0, 0, 0])
        deque_.appendleft((mqtt_data, time.time()))
        if len(deque_) == size:
            deque_.pop()
            return np.array(deque_)


def diff(lis):
    return lis[0]-lis[-1]


N_found = False
n = 2
axis_velocity = None
current_kalman_position = None

while True:
    
    los = mqtt_los.processed_data[0] if mqtt_los.processed_data else 1
    data = np.array(
        mqtt_conn.processed_data) if mqtt_conn.processed_data else np.array([0, 0, 0])
    if los ==1:
        data_deque_with_ts = deque_manager_with_ts(n)
        # print(data_deque_with_ts.shape)
        position_data = data_deque_with_ts[:, 0]
        time_data = data_deque_with_ts[:, 1]
        time_difference = diff(time_data)

        'expand deque to contain 1 second data'
        if not N_found:
            while time_difference < 1:
                data_deque_with_ts = deque_manager_with_ts(n)
                time_data = data_deque_with_ts[:, 1]
                time_difference = diff(time_data)
                print(f"collecting time samples {time_difference:.1}/1")
                n += 1
        N_found = True

        'distance calc'
        current_real_position = position_data[0]
        last_real_position = position_data[-1]
        linear_distance = distance.euclidean(
            current_real_position, last_real_position)
        lqr.set_current_state(last_real_position)
        lqr.set_desired_state(current_real_position)
        axis_distance = lqr.calculate_cmd_input()

        axis_velocity = axis_distance/time_difference  # last velocity
        linear_velocity = linear_distance/time_difference

        "kalman filter part"
        p_update, q_update = state.get_state_estimation(
            q, axis_velocity, current_real_position, p)
        current_kalman_position = np.array(q_update.T.tolist()[0])

        print(f"<<KALMAN POS of LOS>> {current_kalman_position}")
        print(f"real position {current_real_position}")
        print(f"axis velocity {axis_velocity}")
        print(f"linear velocity {linear_velocity}")
        print(f'time diff {time_difference}')
    else:
        # print(f"axis vel {axis_velocity}")
        # print(f"kalman pos {current_kalman_position}")
        "kalman filter part"
        p_update, q_update = state.get_state_estimation(
            q, axis_velocity, current_kalman_position, p)
        current_kalman_position = np.array(q_update.T.tolist()[0])
        print(f"<<KALMAN POS of NLOS>> {current_kalman_position}")
        print(f"velocity of NLOS {axis_velocity}")
        time.sleep(1)
