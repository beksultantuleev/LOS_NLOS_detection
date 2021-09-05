from keras.models import load_model
from Data_collection import Listener
from time import sleep
from Mqtt_manager import Mqtt_Manager
import collections
import numpy as np


class Stream_data_classification():
    def __init__(self, model_location):
        self.model = load_model(model_location)
        self.accelemeter_conn = Mqtt_Manager(
            "localhost", "accelerometer_LSM303AGR")
        self.gyro_conn = Mqtt_Manager("localhost", "gyroscope_LSM6DSL")

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

    def run_classification(self, sample_size, use_window_classification, sleep_time):
        window_counter = 0
        while True:
            sleep(sleep_time)
            accelerometer = self.deque_manager(self.accelemeter_conn, sample_size)
            gyroscope = self.deque_manager(self.gyro_conn, sample_size)

            if accelerometer is not None and gyroscope is not None:

                new_data = np.array([np.concatenate(
                    (accelerometer, gyroscope), axis=0)])

                window_counter+=1
                if use_window_classification:
                    if window_counter == sample_size:
                        predicted_classes = test.model.predict_classes(new_data)
                        print(f"predicted classes window {predicted_classes} ")
                        window_counter = 0
                else:
                    predicted_classes = test.model.predict_classes(new_data)
                    print(f"predicted classes no window {predicted_classes} ")
                    

if __name__ == "__main__":

    test = Stream_data_classification(
        model_location="trained_models/binary_nn.h5")  # still_wave#binary_nn

    test.run_classification(10, True, 0.3)

