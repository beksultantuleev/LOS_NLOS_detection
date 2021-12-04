import numpy as np
import pandas as pd
import collections
import time
from Managers.Mqtt_manager import Mqtt_Manager

'data transformation'
def multiInputConfiguration(dataset, list_of_independent_vars, acquisition="acquisition"):
    for acq_index in range(1, max(np.unique(dataset[acquisition]))+1):
        temp = dataset[dataset[acquisition] == acq_index]
    dataset['idx'] = dataset.groupby(acquisition).cumcount()

    final_dataframe = dataset.pivot_table(index=acquisition, columns='idx')[
        list_of_independent_vars]
    # print(final_dataframe)
    return final_dataframe

def acquisition_modifier(acquisition_number, length_of_acquisitions):
    if acquisition_number == 1:
        return [1]*length_of_acquisitions
    elif acquisition_number == 0:
        return [0]*length_of_acquisitions
    lis = []
    for i in range(length_of_acquisitions):
        lis.append(i)
    lis = sorted(lis*acquisition_number)[:length_of_acquisitions]
    return lis

def value_extractor(pattern, path):
    with open(path) as f:
        lines = f.read().splitlines()
        for i in lines:
            if pattern in i:
                value = float(i[len(pattern):])
                return value
'deque managers'
def deque_manager(number, size, mqtt_conn):
    'updated deque manager, new values at the end of deque'
    size = size+1
    deque_test = collections.deque([])
    while len(deque_test) < size:
        time.sleep(0.01) #to see updates in deques
        mqtt_data = mqtt_conn.processed_data[number] if mqtt_conn.processed_data else 0
        # deque_test.appendleft(mqtt_data)
        deque_test.append(mqtt_data)
        if len(deque_test) == size:
            # deque_test.pop()
            deque_test.popleft()
            return np.array(deque_test)