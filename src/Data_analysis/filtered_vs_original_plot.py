from turtle import color
import matplotlib.pyplot as plt
import pandas as pd
import re

dict_of_locations = {
    # 'still simple filters'
    # 'anomaly'
    'location1': 'data/filtered_vs_original_data/still_comp_anomaly_simple_filter_median_smpl_anch_sel_200.csv',
    'location2': 'data/filtered_vs_original_data/still_comp_anomaly_simple_filter_avrg_smpl_anch_sel_200.csv',
    # 'k means   :,
    'location3': 'data/filtered_vs_original_data/still_comp_k_means_simple_filter_median_smpl_anch_sel_200.csv',
    'location4': 'data/filtered_vs_original_data/still_comp_k_means_simple_filter_avrg_smpl_anch_sel_200.csv',
    # 'gmm'   ,
    'location5': 'data/filtered_vs_original_data/still_comp_gmm_simple_filter_median_smpl_anch_sel_200.csv',
    'location6': 'data/filtered_vs_original_data/still_comp_gmm_simple_filter_avrg_smpl_anch_sel_200.csv',
    # 'move'  :,
    # 'anomaly   :,
    'location7': 'data/filtered_vs_original_data/move_comp_anomaly_simple_filter_median_smpl_anch_sel_200.csv',
    'location8': 'data/filtered_vs_original_data/move_comp_anomaly_simple_filter_avrg_smpl_anch_sel_200.csv',
    # 'k means   :,
    'location9': 'data/filtered_vs_original_data/move_comp_k_means_simple_filter_median_smpl_anch_sel_200.csv',
    'location10': 'data/filtered_vs_original_data/move_comp_k_means_simple_filter_avrg_smpl_anch_sel_200.csv',
    # 'gmm',
    'location11': 'data/filtered_vs_original_data/move_comp_gmm_simple_filter_median_smpl_anch_sel_200.csv',
    'location12': 'data/filtered_vs_original_data/move_comp_gmm_simple_filter_avrg_smpl_anch_sel_200.csv',
    # "std filter",
    # 'anomaly',
    'location13': 'data/filtered_vs_original_data/move_comp_anomaly_std_fltr_avrg_smpl_anch_sel_200.csv',
    'location14': 'data/filtered_vs_original_data/move_comp_anomaly_std_fltr_median_smpl_anch_sel_200.csv',
    # 'k means:
    'location15': 'data/filtered_vs_original_data/move_comp_k_means_std_fltr_avrg_smpl_anch_sel_200.csv',
    'location16': 'data/filtered_vs_original_data/move_comp_k_means_std_fltr_median_smpl_anch_sel_200.csv',
    # 'gmm:
    'location17': 'data/filtered_vs_original_data/move_comp_gmm_std_fltr_median_smpl_anch_sel_200.csv',
    'location18': 'data/filtered_vs_original_data/move_comp_gmm_std_fltr_avrg_smpl_anch_sel_200.csv',
    # 'move std, imp anch selection',
    # 'anomaly',
    'location19': 'data/filtered_vs_original_data/move_comp_anomaly_std_fltr_avrg_imp_anch_sel_200.csv',
    'location20': 'data/filtered_vs_original_data/move_comp_anomaly_std_fltr_median_imp_anch_sel_200.csv',
    # 'k means :
    'location21': 'data/filtered_vs_original_data/move_comp_k_means_std_fltr_avrg_imp_anch_sel_200.csv',
    'location22': 'data/filtered_vs_original_data/move_comp_k_means_std_fltr_median_imp_anch_sel_200.csv',
    # 'gmm :
    'location23': 'data/filtered_vs_original_data/move_comp_gmm_std_fltr_median_imp_anch_sel_200.csv',
    'location24': 'data/filtered_vs_original_data/move_comp_gmm_std_fltr_avrg_imp_anch_sel_200.csv',
    # "moving tag",
    # 'anomaly',
    'location25': 'data/filtered_vs_original_data/moving_tag_still_comp_anomaly_std_fltr_median_smpl_anch_sel_200.csv',
    'location26': 'data/filtered_vs_original_data/moving_tag_still_comp_anomaly_std_fltr_avrg_smpl_anch_sel_200.csv',
    # 'problem in imp anch sel filter'# location = 'data/filtered_vs_original_data/moving_tag_still_comp_anomaly_std_fltr_avrg_imp_anch_sel_200.csv',
    # "problem"# location = 'data/filtered_vs_original_data/moving_tag_still_comp_anomaly_std_fltr_median_imp_anch_sel_200.csv',
    # 'kmeans',
    'location27': 'data/filtered_vs_original_data/moving_tag_still_comp_k_means_std_fltr_median_smpl_anch_sel_200.csv',
    'location28': 'data/filtered_vs_original_data/moving_tag_still_comp_k_means_std_fltr_avrg_smpl_anch_sel_200.csv',
    # 'gmm :
    'location29': 'data/filtered_vs_original_data/moving_tag_still_comp_gmm_std_fltr_avrg_smpl_anch_sel_200.csv',
    'location30': 'data/filtered_vs_original_data/moving_tag_still_comp_gmm_std_fltr_median_smpl_anch_sel_200.csv'
}
for k, location in dict_of_locations.items():
    if k == 'location30':

        patterns = location.split('comp_')
        title_ = patterns[-1][:-4]

        data = pd.read_csv(location, names=['x1', 'y1', 'x2', 'y2'])

        # plt.style.use('fivethirtyeight')
        plt.style.use('bmh')
        plt.plot(data['x2'], data['y2'], color='red',
                label='original', linestyle=":", alpha=1)
        plt.plot(data['x1'], data['y1'], color='g',
                label='filtered', linestyle="-", alpha=0.7)
        plt.axis('scaled')
        plt.title(title_)
        plt.xlabel("X (scale in meters)")
        plt.ylabel("Y (scale in meters)")
        plt.legend()
        plt.tight_layout()
        # plt.savefig(
        #     f"src/Data_analysis/plot_data/position_plot_fitered_original/{k}.png")
        # plt.close()
        plt.show()
