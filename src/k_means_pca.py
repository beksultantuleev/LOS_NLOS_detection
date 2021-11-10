from matplotlib import scale
import pandas as pd
from sklearn.cluster import KMeans
import numpy as np
from sklearn.decomposition import PCA
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
from collections import Counter
from sklearn.preprocessing import StandardScaler
import joblib

"kmeans + pca"

data = pd.read_csv('data/los_nlos_cluster_dataa.txt')
# data = pd.read_csv('data/los_nlos_cluster_by_acquisition_4.csv')
data = data.drop(["activity"], axis=1)

scaler = StandardScaler()
scaler.fit(data)
scaled_data = scaler.transform(data)

pca = PCA(n_components=2)

#Transform the data
df = pca.fit_transform(scaled_data)
# df = pca.fit_transform(data)
# print(df)
# joblib.dump(pca, 'trained_models/pca_by_acquisition_4.sav')

'k means'
kmeans = KMeans(n_clusters= 2)
kmeans.fit(df)
label = kmeans.predict(df)

"save model"
# joblib.dump(kmeans, 'trained_models/k_means_by_acquisition_4.sav')

"custom data testing"
# label = kmeans.predict([df[0]]) #df[:1,:]
# print(label)
# print(df[:1,:])
print(f"df is here {df}")

# print(label[:20])
"plotting"
# filter rows of original data
filtered_label0 = df[label == 0]
filtered_label1 = df[label == 1]
 
#Plotting the results
plt.scatter(filtered_label0[:,0] , filtered_label0[:,1] , color = 'red')
plt.scatter(filtered_label1[:,0] , filtered_label1[:,1] , color = 'black')
plt.show()


