from time import sleep
import os
from typing import Mapping
import numpy as np
from Mqtt_manager import Mqtt_Manager
import timeit
import pandas as pd
import pathlib
from SerialPortReader import SerialPortReader

'main data collection file'


class Listener():
    def __init__(self, via_port_reader=True):
        self.data_folder = 'data'
        self.dataset_name = ""
        self.acquisition_number = 1
        self.list_of_features = ["RX_level", "RX_difference", 'F2_std_noise', 'std_noise']
        # self.list_of_features = ["RX_level",
        #                          "RX_difference", "CIR", "F1", "F2", "F3"]
        self.via_port_reader = via_port_reader
        self.allInOne_conn = Mqtt_Manager(
            "192.168.0.119", "allInOne")

        self.data = np.empty(shape=(0, len(self.list_of_features)))
        self.samples = 40

        self.serialPortInitiation = SerialPortReader()

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

    def all_data_collection(self, publish=False):
        if not self.via_port_reader:
            if self.allInOne_conn.processed_data:
                # print(f"accelerom data is {self.accelemeter_conn.processed_data}")
                self.data = np.append(self.data, np.expand_dims(
                    np.array(self.allInOne_conn.processed_data), axis=0), axis=0)
        else:
            pattern = "Data: "
            if self.serialPortInitiation.get_data(pattern=pattern):
                serialPort_data = self.serialPortInitiation.get_data(
                    pattern=pattern)
                self.data = np.append(self.data, np.expand_dims(
                    np.array(serialPort_data), axis=0), axis=0)
                if publish:
                    self.allInOne_conn.publish(
                        'allInOne', f'{serialPort_data}')
                    # pass

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
        if in_raw:
            data_name = f"{self.dataset_name}_{self.acquisition_number}_ss{self.samples}"
        else:
            data_name = f"{self.dataset_name}_{self.acquisition_number}_ss{self.samples/self.acquisition_number}"
        counter = 1
        for root, dirs, files in os.walk(f"{pathlib.Path().absolute()}/data"):
            for f in files:
                # print(f)
                if data_name in f:
                    counter += 1
                    "in raw means saving data with no transformation. Transformation is made based on acquisition column"
                if in_raw:
                    all_in_one_dataframe.to_csv(
                        f"data/{self.dataset_name}_{self.acquisition_number}_ss{self.samples}_{counter}.csv", index=None)
                else:
                    self.dataset_configuration(all_in_one_dataframe, self.list_of_features).to_csv(
                        f"data/{self.dataset_name}_{self.acquisition_number}_ss{self.samples/self.acquisition_number}_{counter}.csv", index=None)
        print("Saved!")


if __name__ == "__main__":
    start = timeit.default_timer()

    test = Listener(via_port_reader=True)
    test.set_dataset_name("NLOS_added_values")
    test.set_acquisition_number(4)
    test.set_sample_size(45000)
    limiter = 0
    while limiter != test.samples:
        # sleep(0.05) #for mqtt??
        test.all_data_collection(publish=True)

        limiter = len(test.data)
        print(f"loading ===>{limiter}/{test.samples}")

    test.saveData(in_raw=True)

    stop = timeit.default_timer()
    print(f"end, time is {(stop - start) / 60:.2f} min")
