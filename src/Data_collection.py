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
        self.number_of_activities = 1

        self.allInOne_conn = Mqtt_Manager(
            "localhost", "allInOne")

        self.data = np.empty(shape=(0, 5))
        self.samples = 40

    def set_number_of_activities(self, number_of_activities):
        self.number_of_activities = number_of_activities

    def activity_modifier(self, number_of_activities, length_of_activity):
        if number_of_activities == 1:
            return [1]*length_of_activity
        lis = []
        for i in range(length_of_activity):
            lis.append(i)
        lis = sorted(lis*number_of_activities)[:length_of_activity]
        return lis

    def set_sample_size(self, number):
        self.samples = number

    def all_data_collection(self):
        if self.allInOne_conn.processed_data:
            # print(f"accelerom data is {self.accelemeter_conn.processed_data}")
            self.data = np.append(self.data, np.expand_dims(
                np.array(self.allInOne_conn.processed_data), axis=0), axis=0)


    def saveData(self):
        all_in_one_dataframe = pd.DataFrame(self.data, columns=[
                                            "CIR", "FirstPathPL", "maxNoise", "RX_level", "FPPL"]) #'Distance'
        # gyro_dataframe= pd.DataFrame(self.gyro_data, columns=["gyr_x","gyr_y", "gyr_z"])

        # imu_dataframe = pd.concat([all_in_one_dataframe, gyro_dataframe], axis=1)
        all_in_one_dataframe.insert(0, 'activity', self.activity_modifier(self.number_of_activities, self.samples))
        data_name = f"data_ss{self.samples}_{self.activity}"
        counter = 1

        for root, dirs, files in os.walk(f"{pathlib.Path().absolute()}/data/raw"):
            for f in files:
                if data_name in f:
                    counter += 1
        all_in_one_dataframe.to_csv(
            f"data/raw/data_ss{self.samples}_{self.activity}_{counter}.txt", index=None)
        print(
            f"Saved!\n data/raw/data_ss{self.samples}_{self.activity}_{counter}.txt")


if __name__ == "__main__":
    test = Listener()

    test.set_number_of_activities(1)
    test.set_sample_size(500)
    limiter = 0
    while limiter != test.samples:
        sleep(0.01)
        test.all_data_collection()

        limiter = len(test.data)
        print(f"loading ===>{limiter}/{test.samples}")

    test.saveData()
