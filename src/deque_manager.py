from keras.models import load_model
from Data_collection import Listener
from time import sleep
from Mqtt_manager import Mqtt_Manager
import collections


model = load_model("trained_models/still_wave.h5")
accelemeter_conn = Mqtt_Manager(
    "localhost", "accelerometer_LSM303AGR")
gyro_conn = Mqtt_Manager("localhost", "gyroscope_LSM6DSL")


def deque_manager(accelemeter_conn, size):
    deque_x = collections.deque([])
    deque_y = collections.deque([])
    deque_z = collections.deque([])
    if accelemeter_conn.processed_data:
        while len(deque_x) < size:
            deque_x.appendleft(accelemeter_conn.processed_data[0])
            deque_y.appendleft(accelemeter_conn.processed_data[1])
            deque_z.appendleft(accelemeter_conn.processed_data[2])
            if len(deque_x) == size:
                deque_x.pop()
                deque_y.pop()
                deque_z.pop()
                return list(deque_x) + list(deque_y) + list(deque_z)


while True:
    sleep(0.2)
    if deque_manager(accelemeter_conn, 2):
        new_data = [deque_manager(gyro_conn, 41) + deque_manager(accelemeter_conn, 41)]
        model.summary()
        y_new = model.predict_classes(new_data)
        print(y_new)
        # if y_new[0]==0:
        #     print("wave")
        # else:
        #     print("still")
