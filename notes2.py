import numpy as np
from numpy.core.numeric import outer
from scipy.spatial import distance
import math
import pandas as pd


new_los = pd.read_csv("data/new_LOS_2_ss50000_1.csv")
new_los_upclose = pd.read_csv('data/LOS_mqtt_upclose_2_ss5000_1.csv')

new_data = pd.concat([new_los, new_los_upclose], ignore_index=True)
# print(new_data)

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
new_data['acquisition'] = acquisition_modifier(2, len(new_data))
print(new_data)
new_data.to_csv("data/LOS_serial_port_complete.csv", index=None)