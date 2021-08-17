from time import sleep
import os
import signal
from typing import Mapping
import numpy as np
# import keyboard
from Mqtt_manager import Mqtt_Manager

import pandas as pd
import pathlib

class Listener():
    def __init__(self):
        self.data_folder = 'data'
        self.activity = ""
        self.act_counter = 1

        self.accelemeter_conn = Mqtt_Manager(
            "localhost", "accelerometer_LSM303AGR")
        self.gyro_conn = Mqtt_Manager("localhost", "gyroscope_LSM6DSL")
        self.magnetometer_conn = Mqtt_Manager(
            "localhost", "magnetometer_LSM303AGR")

        self.acc_data = np.empty(shape=(0, 3))
        self.gyro_data = np.empty(shape=(0, 3))
        self.magnetom_data = np.empty(shape=(0, 3))

        self.samples = 40

    def set_activity(self, activity):
        self.activity = activity
    
    def set_sample_size(self, number):
        self.samples = number

    def accelerom_data_collection(self):
        if self.accelemeter_conn.processed_data:
            # print(f"accelerom data is {self.accelemeter_conn.processed_data}")
            self.acc_data = np.append(self.acc_data, np.expand_dims(
                np.array(self.accelemeter_conn.processed_data), axis=0), axis=0)


    def gyro_data_collection(self):
        if self.gyro_conn.processed_data:
            # print(f"gyro data is {self.accelemeter_conn.processed_data}")
            self.gyro_data = np.append(self.gyro_data, np.expand_dims(
                np.array(self.gyro_conn.processed_data), axis=0), axis=0)
    
    def saveData(self):
        acc_dataframe = pd.DataFrame(self.acc_data, columns=["acc_x","acc_y", "acc_z"])
        gyro_dataframe= pd.DataFrame(self.gyro_data, columns=["gyr_x","gyr_y", "gyr_z"])

        imu_dataframe = pd.concat([acc_dataframe, gyro_dataframe], axis=1)
        imu_dataframe.insert(0, 'activity', self.activity)
        data_name = f"data_ss{self.samples}_{self.activity}"
        counter = 1

        for root, dirs, files in os.walk(f"{pathlib.Path().absolute()}/data/raw"):
            for f in files:
                if data_name in f:
                    counter+=1
        imu_dataframe.to_csv(f"data/raw/data_ss{self.samples}_{self.activity}_{counter}.txt")
        print(f"Saved!\n data/raw/data_ss{self.samples}_{self.activity}_{counter}.txt")
                    
        
        
if __name__ == "__main__":
    test = Listener()
    # accelemeter_conn = Mqtt_Manager(
    #         "localhost", "accelerometer_LSM303AGR")
    # while True:
    #     if accelemeter_conn.processed_data:
    #         sleep(0.3)
    #         print(accelemeter_conn.processed_data)
    test.set_activity("dance")
    test.set_sample_size(10)
    limiter = 0
    while limiter!=test.samples:
        sleep(0.3)
        test.accelerom_data_collection()
        test.gyro_data_collection()
        limiter = len(test.acc_data)
        print(f"loading ===>{limiter}/{test.samples}")
    test.saveData()

