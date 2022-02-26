import numpy as np
import pandas as pd


data = pd.read_csv('grand_model_test_data_all_anchors.csv')
# anch1_nlos = data[data['det1']==0]

for i in range(1,4):
    print(f'anch{i}')
    percentage = data[f'grand{i}'].value_counts()[0]/data[f'det{i}'].value_counts()[0]
    total_nlos = data[f'det{i}'].value_counts()[0]
    nlos_found_by_grand = data[f'grand{i}'].value_counts()[0]

    percentage_los = data[f'det{i}'].value_counts()[1]/data[f'grand{i}'].value_counts()[1]
    total_los = data[f'det{i}'].value_counts()[1]
    los_found_by_grand = data[f'grand{i}'].value_counts()[1]

    # print(f'total Nlos {total_nlos}, nlos grand m {nlos_found_by_grand} total Los {total_los}, los grand m {los_found_by_grand}')
    print(f'nlos grand m/ total Nlos {1-nlos_found_by_grand/total_nlos:.2f} los grand m/ total los {los_found_by_grand/total_los -1:.2f}')
