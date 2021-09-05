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
        # self.list_of_topics = None
        self.list_of_connections = []
        self.list_of_data = []

        


        self.samples = 40

    def set_activity(self, activity):
        self.activity = activity

    def set_sample_size(self, number):
        self.samples = number

    def accelerom_data_collection(self):
        if self.accelemeter_conn.processed_data:
            # print(f"accelerom data is {self.accelemeter_conn.processed_data}")
            self.data = np.append(self.data, np.expand_dims(
                np.array(self.accelemeter_conn.processed_data), axis=0), axis=0)

    def get_connections(self, list_of_topics):
        self.data = np.empty(shape=(0, 1))
        for topics in list_of_topics:
            self.connection = Mqtt_Manager('localhost', topics)
            self.list_of_connections.append(self.connection)
        # return self.list_of_connections

    def data_collection(self):
        for connection in self.list_of_connections:
            if connection.processed_data:
                self.data = np.append(self.data, np.expand_dims(
                    np.array(connection.processed_data), axis=0), axis=0)
                self.list_of_data.append(self.data)
        

    def saveData(self):
        # dataframe = pd.DataFrame(self.data, columns=["acc_x","acc_y", "acc_z"])
        # gyro_dataframe= pd.DataFrame(self.gyro_data, columns=["gyr_x","gyr_y", "gyr_z"])
        for dataframe in self.list_of_data:
            

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

    test.set_activity("dance")
    test.set_sample_size(10)
    limiter = 0
    test.get_connections(["CIR", "FPPL"])
    while limiter != test.samples:
        sleep(0.3)
        test.data_collection()

        limiter = len(test.data)
        print(f"loading ===>{limiter}/{test.samples}")
    test.saveData()
