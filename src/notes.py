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
from scipy.spatial import ConvexHull


# lis = np.array([[10,15,3], [10,14,20], [5,14,21]])
# print(lis)
# print(np.mean(lis, axis=0))
# print(np.median(lis, axis=0))

lis = np.array([10, 10, 10, 10, 10, 100, 10, 3])
# print(lis)
# print(np.mean(lis, axis=0))
# print(np.median(lis, axis=0))
divider = int(len(lis)*0.4)
print(divider)
# print(lis[-divider:])
'old filters'
'still simple filters'
# location = 'data/filtered_vs_original_data/still_comp__anomaly_simple_filter_smpl_anch_sel_300.csv'
# location = 'data/filtered_vs_original_data/still_comp__k_means_simple_filter_smpl_anch_sel_300.csv'
# location = 'data/filtered_vs_original_data/still_comp__gmm_simple_filter_smpl_anch_sel_300.csv'
'moving'
'anomaly det'
# location = 'data/filtered_vs_original_data/move_comp_anomaly_simple_filter_median_smpl_anch_sel_300.csv'
# location = 'data/filtered_vs_original_data/move_comp_anomaly_simple_filter_avrg_smpl_anch_sel_300.csv'
'k means'
# location = 'data/filtered_vs_original_data/move_comp_k_means_simple_filter_median_smpl_anch_sel_300.csv'
# location = 'data/filtered_vs_original_data/move_comp_k_means_simple_filter_avrg_smpl_anch_sel_300.csv'
'gmm'
# location = 'data/filtered_vs_original_data/move_comp_gmm_simple_filter_median_smpl_anch_sel_300.csv'
# location = 'data/filtered_vs_original_data/move_comp_gmm_simple_filter_avrg_smpl_anch_sel_300.csv'

"still std filter"
'anomaly'
# location = 'data/filtered_vs_original_data/still_comp_anomaly_std_fltr_median_smpl_anch_sel_300.csv'
# location = 'data/filtered_vs_original_data/still_comp_anomaly_std_fltr_avrg_smpl_anch_sel_300.csv'
'kmeans'
# location = 'data/filtered_vs_original_data/still_comp_k_means_std_fltr_median_smpl_anch_sel_300.csv'
# location = 'data/filtered_vs_original_data/still_comp_k_means_std_fltr_avrg_smpl_anch_sel_300.csv'
'gmm'
# location = 'data/filtered_vs_original_data/still_comp_gmm_std_fltr_median_smpl_anch_sel_300.csv'
# location = 'data/filtered_vs_original_data/still_comp_gmm_std_fltr_avrg_smpl_anch_sel_300.csv'
'move'
'anomaly'
# location = 'data/filtered_vs_original_data/move_comp_anomaly_std_fltr_median_smpl_anch_sel_300.csv'
# location = 'data/filtered_vs_original_data/move_comp_anomaly_std_fltr_avrg_smpl_anch_sel_300.csv'
'k means'
# location = 'data/filtered_vs_original_data/move_comp_k_means_std_fltr_median_smpl_anch_sel_300.csv'
# location = 'data/filtered_vs_original_data/move_comp_k_means_std_fltr_avrg_smpl_anch_sel_300.csv'
'gmm'
# location = 'data/filtered_vs_original_data/move_comp_gmm_std_fltr_median_smpl_anch_sel_300.csv'
# location = 'data/filtered_vs_original_data/move_comp_gmm_std_fltr_avrg_smpl_anch_sel_300.csv'

"move imp anchor sel, std filt"
'anomaly'
# location = 'data/filtered_vs_original_data/move_comp_anomaly_std_fltr_median_imp_anch_sel_300.csv'
# location = 'data/filtered_vs_original_data/move_comp_anomaly_std_fltr_avrg_imp_anch_sel_300.csv'
'k means'
# location = 'data/filtered_vs_original_data/move_comp_k_means_std_fltr_median_imp_anch_sel_300.csv'
# location = 'data/filtered_vs_original_data/move_comp_k_means_std_fltr_avrg_imp_anch_sel_300.csv'
'gmm'
'bad'
# location = 'data/filtered_vs_original_data/move_comp_gmm_std_fltr_median_imp_anch_sel_300.csv'
# location = 'data/filtered_vs_original_data/move_comp_gmm_std_fltr_avrg_imp_anch_sel_300.csv'
