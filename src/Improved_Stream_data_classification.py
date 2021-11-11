from keras.models import load_model
from Data_collection import Listener
from time import sleep
from Mqtt_manager import Mqtt_Manager
import collections
import numpy as np
import joblib

'dont need it at the moment'
class Stream_data_classification():
    def __init__(self):

        self.allInOne = Mqtt_Manager(
            "localhost", "allInOne")
        # self.gyro_conn = Mqtt_Manager("localhost", "gyroscope_LSM6DSL")

    def load_model(self, model_location, is_sklearn=True):
        if is_sklearn:
            self.model = joblib.load(model_location)
        else:
            self.model = load_model(model_location)

    def deque_manager(self, mqtt_conn, size):
        size = size+1
        # for i in range(num_of_deques):
        deque_cir = collections.deque([])
        deque_firstpathpl = collections.deque([])
        deque_maxnoise = collections.deque([])
        deque_rxlevel = collections.deque([])
        deque_fppl = collections.deque([])

        if mqtt_conn.processed_data:
            while len(deque_cir) < size:
                deque_cir.appendleft(mqtt_conn.processed_data[0])
                deque_firstpathpl.appendleft(mqtt_conn.processed_data[1])
                deque_maxnoise.appendleft(mqtt_conn.processed_data[2])

                deque_rxlevel.appendleft(mqtt_conn.processed_data[3])
                deque_fppl.appendleft(mqtt_conn.processed_data[4])
                if len(deque_cir) == size:
                    deque_cir.pop()
                    deque_firstpathpl.pop()
                    deque_maxnoise.pop()
                    deque_rxlevel.pop()
                    deque_fppl.pop()
                    return np.concatenate((np.array(deque_cir), np.array(deque_firstpathpl), np.array(deque_maxnoise), np.array(deque_rxlevel), np.array(deque_fppl)), axis=0)

    def run_classification(self, sample_size, use_window_classification, sleep_time):
        window_counter = 0
        while True:
            sleep(sleep_time)
            all_data = self.deque_manager(self.allInOne, sample_size)
            # gyroscope = self.deque_manager(self.gyro_conn, sample_size)

            if all_data is not None:
                "cant pass new data to predict classes"
                # new_data = np.array([np.concatenate(
                #     (all_data, gyroscope), axis=0)])
                new_data = np.array([all_data])
                # print(new_data)
                
                window_counter += 1
                if use_window_classification:
                    if window_counter == sample_size:
                        predicted_classes = np.argmax(test.model.predict(new_data), axis=-1)

                        print(f"predicted classes window {predicted_classes} ")
                        window_counter = 0
                else:
                    predicted_classes = np.argmax(test.model.predict(new_data), axis=-1)
                    print(f"predicted classes no window {predicted_classes} ")


if __name__ == "__main__":

    test = Stream_data_classification()  # still_wave#binary_nn
    # test.load_model(model_location="trained_models/logistic_regression.sav", is_sklearn=True)
    test.load_model(
        model_location="trained_models/binary_nn.h5", is_sklearn=False)
    test.run_classification(50, False, 0.1)
