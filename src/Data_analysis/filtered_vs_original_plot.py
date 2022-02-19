from turtle import color
import matplotlib.pyplot as plt
import pandas as pd

'still simple filters'
# location = 'data/filtered_vs_original_data/still_comp__anomaly_simple_filter_smpl_anch_sel_300.csv'
# location = 'still_data/filtered_vs_original_data/comp__k_means_simple_filter_smpl_anch_sel_300.csv'
# location = 'still_data/filtered_vs_original_data/comp__gmm_simple_filter_smpl_anch_sel_300.csv'
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


data = pd.read_csv(location, names=['x1', 'y1', 'x2', 'y2'])


plt.plot(data['x2'], data['y2'], color='r',
         label='original', linestyle="--", alpha=0.5)
plt.plot(data['x1'], data['y1'], color='g',
         label='filtered', linestyle="-", alpha=0.5)
plt.axis('scaled')
plt.xlabel("X")
plt.ylabel("Y")
plt.legend()
plt.tight_layout()
plt.show()
