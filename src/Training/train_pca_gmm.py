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

'PCA with GMM'

num_of_classes = 2
save_models = True
# use_scaler = True
# single_data = True
# num_of_acquisition = 4

"kmeans + pca train models"

data_los = pd.read_csv('data/LOS_good_data_complete.csv')
data_nlos = pd.read_csv('data/NLOS_good_data_complete.csv')
data_nlos2 = pd.read_csv('data/NLOS_data_water_2_ss95000_1.csv')
data_mix = pd.read_csv('data/additional_mix_data.csv')
data = pd.concat([data_los, data_nlos, data_nlos2,
                 data_mix], ignore_index=True)


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


data = data.drop(["acquisition", ], axis=1)  # 'maxNoise'
# print(data)

# print(f"data is here! {data}")

scaler = StandardScaler()
scaler.fit(data)
scaled_data = scaler.transform(data)
pca = PCA(n_components=2)
# print(f'scaled data is here! {scaled_data}')
# Transform the data

df = pca.fit_transform(scaled_data)

# print(df)

'k means'
# kmeans = KMeans(n_clusters=num_of_classes, random_state=42)
# kmeans.fit(df)
# label = kmeans.predict(df)

'gmm'
gm = GaussianMixture(n_components=2, random_state=42,
                     covariance_type='tied', verbose=1, init_params='kmeans').fit(df)
label_proba = gm.predict_proba(df)
label = gm.predict(df)
# print(np.min(label))
# print(label)


"save model"
if save_models:
    'pca and scaler is the same as for kmeans'
    # joblib.dump(scaler, 'trained_models/standard_scaler_pca_gmm.save')
    # joblib.dump(pca, 'trained_models/pca_for_gmm.sav')
    joblib.dump(gm, 'trained_models/gmm.sav')

"plotting"
# filter rows of original data
for i in range(num_of_classes):
    filtered_label = df[label == i]
    # Plotting the results
    plt.scatter(filtered_label[:, 0], filtered_label[:, 1])

plt.xlabel("Principal Component 1")
plt.ylabel("Principal Component 2")
plt.title("PCA with gmm")
plt.tight_layout()
plt.show()
