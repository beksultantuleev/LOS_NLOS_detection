# from keras.models import load_model
from typing import final
from time import sleep, time
# from tensorflow import keras
# from keras.models import load_model
import pandas as pd
import numpy as np
# from Core_functions.hub_of_functions import deque_manager
from collections import deque
import tensorflow as tf
from keras.models import load_model
from Core_functions.hub_of_functions import value_extractor
import pandas as pd
from scipy.spatial.distance import cdist
from matplotlib import pyplot as plt
from matplotlib.pyplot import figure

data = pd.read_csv(
    'data/filtered_vs_original_data/still_comp_anomaly_simple_filter_median_smpl_anch_sel_200.csv', names=['x1', 'y1', 'x2', 'y2'])
plt.style.use('bmh')
ground_x = data['x2'].median()
ground_y = data['y2'].median()
data['error_original'] = ((data['x2'] - ground_x) **
                          2 + (data['y2'] - ground_y)**2)**(1/2)
data['error_filtered'] = ((data['x1'] - ground_x) **
                          2 + (data['y1'] - ground_y)**2)**(1/2)
figure(dpi=150)
plt.plot(data['error_original'], color='red', linestyle=":",
         alpha=1, label=f"Original {data['error_original'].mean():.3f}")
plt.plot(data['error_filtered'], color='g', linestyle="-",
         alpha=0.7, label=f"Filtered {data['error_filtered'].mean():.3f}")
plt.ylabel("Error (m)")
title = 'this is title'
plt.xlabel(f'Samples\n{title}')
#table data
filtered_error = list(data['error_filtered'].describe().values)
original_error = list(data['error_original'].describe().values)
'rounding'
filtered_error = np.around(filtered_error, 3)[1:]
original_error = np.around(original_error, 3)[1:]

cell_text = np.array([filtered_error, original_error]).T
rows = list(data['error_original'].describe().keys())[1:]
columns = ['Filtered', 'Original']

the_table = plt.table(cellText=cell_text,
                      rowLabels=rows,
                      colLabels=columns,
                      loc='top',
                      cellLoc='center',
                    #   colWidths=[0.1] * 3,
                      )

plt.subplots_adjust(left=0.2, bottom=-0.32)
plt.tight_layout()
# plt.xticks([])
plt.legend()
the_table.scale(1, 3.3)
# plt.show()
# plt.savefig('test.png')

