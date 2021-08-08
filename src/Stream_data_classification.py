from keras.models import load_model
from Data_collection import Listener
from time import sleep
from Mqtt_manager import Mqtt_Manager
import collections

class Stream_data_classification():
    def __init__(self, model_location):
        self.model = load_model(model_location)
        # self.accelemeter_conn = Mqtt_Manager(
        #     "localhost", "accelerometer_LSM303AGR")
        # self.gyro_conn = Mqtt_Manager("localhost", "gyroscope_LSM6DSL")

    def deque_manager(self, mqtt_conn, size):
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
                    return list(deque_x) + list(deque_y) + list(deque_z)

if __name__ == "__main__":
    test = Stream_data_classification(model_location="trained_models/new_data_motion.h5")
    accelemeter_conn = Mqtt_Manager(
        "localhost", "accelerometer_LSM303AGR")
    gyro_conn = Mqtt_Manager("localhost", "gyroscope_LSM6DSL")
    while True: 
        sleep(0.2)
        if test.deque_manager(accelemeter_conn, 2):
            new_data = [test.deque_manager(gyro_conn, 41) + test.deque_manager(accelemeter_conn, 41)]
            # model.summary()
            predicted_classes = test.model.predict_classes(new_data)
            print(f"predicted classes {predicted_classes}")
            predicted_prob = test.model.predict_proba(new_data)
            print(f"predict probs {predicted_prob}")
            # if y_new[0]==0:
            #     print("move")
            # else:
            #     print("still")

# model = load_model("trained_models/new_data_motion.h5")
# accelemeter_conn = Mqtt_Manager(
#     "localhost", "accelerometer_LSM303AGR")
# gyro_conn = Mqtt_Manager("localhost", "gyroscope_LSM6DSL")


# def deque_manager(accelemeter_conn, size):
#     deque_x = collections.deque([])
#     deque_y = collections.deque([])
#     deque_z = collections.deque([])
#     if accelemeter_conn.processed_data:
#         while len(deque_x) < size:
#             deque_x.appendleft(accelemeter_conn.processed_data[0])
#             deque_y.appendleft(accelemeter_conn.processed_data[1])
#             deque_z.appendleft(accelemeter_conn.processed_data[2])
#             if len(deque_x) == size:
#                 deque_x.pop()
#                 deque_y.pop()
#                 deque_z.pop()
#                 return list(deque_x) + list(deque_y) + list(deque_z)



