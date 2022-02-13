from matplotlib import scale
import pandas as pd
from sklearn.cluster import KMeans
import numpy as np
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
from collections import Counter
from sklearn.preprocessing import StandardScaler
import joblib
import sklearn.metrics as metrics
from sklearn.mixture import GaussianMixture

'PCA with k means / gmm'

num_of_classes = 2
save_models = True
use_scaler = True
single_data = True
num_of_acquisition = 4
random_state = None
"kmeans + pca train models"

data_los = pd.read_csv('data/LOS_added_values_complete.csv')
data_nlos = pd.read_csv('data/NLOS_added_values_4_ss45000_1.csv')
# data_nlos2 = pd.read_csv('data/NLOS_data_water_2_ss95000_1.csv')
# data_mix = pd.read_csv('data/additional_mix_data.csv')
# data = pd.concat([data_los, data_nlos, data_nlos2, data_mix], ignore_index=True)
data = pd.concat([data_los, data_nlos], ignore_index=True)


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


if single_data:
    data = data.drop(["acquisition", ], axis=1)  # ''F2_std_noise''
else:
    data['acquisition'] = acquisition_modifier(num_of_acquisition, len(data))
    data = multiInputConfiguration(data, list_of_independent_vars=[
                                   'RX_level', 'RX_difference'])

# print(f"data is here! {data}")
if use_scaler:
    scaler = StandardScaler()
    scaler.fit(data)
    scaled_data = scaler.transform(data)
pca = PCA(n_components=2)
# print(f'scaled data is here! {scaled_data}')
# Transform the data
if use_scaler:
    df = pca.fit_transform(scaled_data)
else:
    df = pca.fit_transform(data)
# print(df)


'k means'
kmeans = KMeans(n_clusters=num_of_classes,
                random_state=random_state)  # , random_state=42
kmeans.fit(df)
label = kmeans.predict(df)
'gmm was removed cuz its hard to control output'
# gm = GaussianMixture(n_components=2,
#                      covariance_type='tied', verbose=1, init_params='kmeans', random_state=random_state).fit(df) #random_state=42,
# label_proba = gm.predict_proba(df)
# label_gmm = gm.predict(df)
"test silhouette score"
# labels = kmeans.labels_
# print(f"silhouette score is {metrics.silhouette_score(df, labels, metric='euclidean')}")

"save model"
if save_models:
    if single_data:
        if use_scaler:
            joblib.dump(
                scaler, 'trained_models/standard_scaler_pca_kmeans.save')
        joblib.dump(pca, 'trained_models/pca.sav')
        joblib.dump(kmeans, 'trained_models/k_means.sav')
        # joblib.dump(gm, 'trained_models/gmm.sav')

    else:
        if use_scaler:
            joblib.dump(
                scaler, f'trained_models/standard_scaler_pca_kmeans_by_acquisition_{num_of_acquisition}.save')
        joblib.dump(
            pca, f'trained_models/pca_by_acquisition_{num_of_acquisition}.sav')
        joblib.dump(
            kmeans, f'trained_models/k_means_by_acquisition_{num_of_acquisition}.sav')


"plotting"
# filter rows of original data
for i in range(num_of_classes):
    filtered_label = df[label == i]
    # Plotting the results
    plt.scatter(filtered_label[:, 0], filtered_label[:, 1])

# plt.scatter(df[:, 0], df[:, 1])

# import plotly.express as px
# fig = px.scatter(df, x=0, y=1)
# fig.show()
plt.xlabel("Principal Component 1")
plt.ylabel("Principal Component 2")
plt.title("PCA with k-means")
plt.tight_layout()
plt.savefig(
    f"src/Data_analysis/plot_data/pca_kmeans.png")
plt.close()
# plt.show()
