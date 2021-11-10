from time import sleep
import os
import signal
from typing import Mapping
import numpy as np
from Mqtt_manager import Mqtt_Manager
import timeit
import pandas as pd
import pathlib

'main data collection file'


class Listener():
    def __init__(self):
        self.data_folder = 'data'
        self.dataset_name = ""
        self.acquisition_number = 1
        self.list_of_features = ["CIR", "FirstPathPL",
                                 "maxNoise", "RX_level", "FPPL"]

        self.allInOne_conn = Mqtt_Manager(
            "localhost", "allInOne")

        self.data = np.empty(shape=(0, 5))
        self.samples = 40

    def set_dataset_name(self, dataset_name):
        self.dataset_name = dataset_name

    def set_acquisition_number(self, acquisition_number):
        self.acquisition_number = acquisition_number

    def acquisition_modifier(self, acquisition_number, length_of_acquisitions):
        if acquisition_number == 1:
            return [1]*length_of_acquisitions
        elif acquisition_number == 0:
            return [0]*length_of_acquisitions
        lis = []
        for i in range(length_of_acquisitions):
            lis.append(i)
        lis = sorted(lis*acquisition_number)[:length_of_acquisitions]
        return lis

    def set_sample_size(self, number):
        self.samples = number

    def all_data_collection(self):
        if self.allInOne_conn.processed_data:
            # print(f"accelerom data is {self.accelemeter_conn.processed_data}")
            self.data = np.append(self.data, np.expand_dims(
                np.array(self.allInOne_conn.processed_data), axis=0), axis=0)

    def dataset_configuration(self, dataset, list_of_independent_vars, acquisition="acquisition"):
        for acq_index in range(1, max(np.unique(dataset[acquisition]))+1):
            temp = dataset[dataset[acquisition] == acq_index]
        dataset['idx'] = dataset.groupby(acquisition).cumcount()

        final_dataframe = dataset.pivot_table(index=acquisition, columns='idx')[
            list_of_independent_vars]
        # print(final_dataframe)
        return final_dataframe

    def saveData(self, in_raw=True):
        all_in_one_dataframe = pd.DataFrame(
            self.data, columns=self.list_of_features)  # 'Distance'

        all_in_one_dataframe.insert(0, 'acquisition', self.acquisition_modifier(
            self.acquisition_number, self.samples))
        data_name = f"{self.dataset_name}_{self.acquisition_number}_ss{self.samples/self.acquisition_number}"
        counter = 1

        for root, dirs, files in os.walk(f"{pathlib.Path().absolute()}/data"):
            for f in files:
                if data_name in f:
                    counter += 1
        if in_raw:
            all_in_one_dataframe.to_csv(
                f"data/{self.dataset_name}_{self.acquisition_number}_ss{self.samples}_{counter}.csv", index=None)
            print("Saved!")
        else:
            self.dataset_configuration(all_in_one_dataframe, self.list_of_features).to_csv(
                f"data/{self.dataset_name}_{self.acquisition_number}_ss{self.samples/self.acquisition_number}_{counter}.csv", index=None)
            print("Saved!")


if __name__ == "__main__":
    start = timeit.default_timer()

    test = Listener()
    test.set_dataset_name("NLOS")
    test.set_acquisition_number(2)
    test.set_sample_size(25000)
    limiter = 0
    while limiter != test.samples:
        sleep(0.01)
        test.all_data_collection()

        limiter = len(test.data)
        print(f"loading ===>{limiter}/{test.samples}")

    test.saveData(in_raw=True)

    stop = timeit.default_timer()
    print(f"end, time is {(stop - start) / 60:.2f} min")
