from turtle import color
import matplotlib.pyplot as plt
import pandas as pd
import re
from matplotlib.pyplot import figure
import numpy as np

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
    # if k == 'location10':

    patterns = location.split('comp_')
    title_ = patterns[-1][:-4]

    data = pd.read_csv(location, names=['x1', 'y1', 'x2', 'y2'])
    figure(dpi=150)
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
    plt.savefig(
        f"src/Data_analysis/plot_data/position_plot_fitered_original/{k}.png")
    plt.close()
    # plt.show()

    ###########
    'table plotting'

    ground_x = data['x2'].median()
    ground_y = data['y2'].median()
    data['error_original'] = ((data['x2'] - ground_x) **
                            2 + (data['y2'] - ground_y)**2)**(1/2)
    data['error_filtered'] = ((data['x1'] - ground_x) **
                            2 + (data['y1'] - ground_y)**2)**(1/2)
    figure(dpi=150)
    plt.plot(data['error_original'], color='red', linestyle=":",
            alpha=1, label=f"Original. Average: {data['error_original'].mean():.3f}")
    plt.plot(data['error_filtered'], color='g', linestyle="-",
            alpha=0.7, label=f"Filtered. Average: {data['error_filtered'].mean():.3f}")
    plt.ylabel("Error (m)")
    plt.xlabel(f'Samples\n{title_}')
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
                        #   colWidths=[0.5] * 2,
                        )

    plt.subplots_adjust(left=0.2, bottom=-0.32)
    plt.tight_layout()
    # plt.xticks([])
    plt.legend()
    the_table.scale(1, 3.3)
    plt.savefig(
        f"src/Data_analysis/plot_data/position_plot_fitered_original/error_stat_{k}.png")
    plt.close()
    # plt.show()
