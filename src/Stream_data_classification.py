from keras.models import load_model
from Data_collection import Listener
from time import sleep
from Mqtt_manager import Mqtt_Manager
import collections
import numpy as np


class Stream_data_classification():
    def __init__(self, model_location):
        self.model = load_model(model_location)
        # self.accelemeter_conn = Mqtt_Manager(
        #     "localhost", "accelerometer_LSM303AGR")
        # self.gyro_conn = Mqtt_Manager("localhost", "gyroscope_LSM6DSL")

    def deque_manager(self, mqtt_conn, size):
        size = size+1
        # for i in range(num_of_deques):
        deque_x = collections.deque([])
        deque_y = collections.deque([])
        deque_z = collections.deque([])
        if mqtt_conn.processed_data:
            while len(deque_x) < size:
                deque_x.appendleft(mqtt_conn.processed_data[0])
                deque_y.appendleft(mqtt_conn.processed_data[1])
                deque_z.appendleft(mqtt_conn.processed_data[2])
                if len(deque_x) == size:
                    deque_x.pop()
                    deque_y.pop()
                    deque_z.pop()
                    return np.concatenate((np.array(deque_x), np.array(deque_y), np.array(deque_z)), axis=0)


if __name__ == "__main__":

    test = Stream_data_classification(
        model_location="trained_models/binary_nn.h5")  # still_wave#binary_nn
    accelemeter_conn = Mqtt_Manager(
        "localhost", "accelerometer_LSM303AGR")
    gyro_conn = Mqtt_Manager("localhost", "gyroscope_LSM6DSL")

    sample_size = 10
    window_counter = 0
    while True:
        sleep(0.3)
        accelerometer = test.deque_manager(accelemeter_conn, sample_size)
        gyroscope = test.deque_manager(gyro_conn, sample_size)

        if accelerometer is not None and gyroscope is not None:

            new_data = np.array([np.concatenate(
                (accelerometer, gyroscope), axis=0)])
            # print(new_data)
            window_counter+=1
            if window_counter == sample_size:
                predicted_classes = test.model.predict_classes(new_data)
                print(f"predicted classes {predicted_classes} ")
                window_counter = 0

            # print(window_counter)
            # model.summary()
            # predicted_classes = test.model.predict_classes(new_data)
            # print(f"predicted classes {predicted_classes} ")

            # predicted_prob = test.model.predict_proba(new_data)
            # print(f"predict probs {predicted_prob}")
            # if y_new[0]==0:
            #     print("move")
            # else:
            #     print("still")
