from matplotlib import scale
import pandas as pd
from sklearn.cluster import KMeans
import numpy as np
from sklearn.decomposition import PCA
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
from collections import Counter

data = pd.read_csv('data/raw/data_ss1000000_NLOS_1.txt')


data = data.drop(["Unnamed: 0", "activity"], axis=1)

"k means "
# kmeans = KMeans(n_clusters=2, random_state=0).fit(data)
# print(np.array(data.iloc[0]))
# for i in range(10000):
#     print(i)
#     pred = kmeans.predict([np.array(data.iloc[i])])
#     print(pred)

# pred = kmeans.predict([np.array(data.iloc[7000])])
# print(pred)
# labels = kmeans.predict(data)
# print(Counter(labels).values())
# for i in labels:
#     print(i)

# print(np.array(data.iloc[7000]))
# print(np.array(data.iloc[0]))
# print(np.array(data.iloc[1000]))

"pca"

from sklearn.preprocessing import StandardScaler
scaler = StandardScaler()
scaler.fit(data)
scaled_data = scaler.transform(data)

# # print(scaled_data)

# pca = PCA(n_components=2)
# pca.fit(scaled_data)

# x_pca = pca.transform(scaled_data)

# print(x_pca)
# plt.figure(figsize=(8,6))
# plt.scatter(x_pca[:,0],x_pca[:,1])
# plt.xlabel('First principal component')
# plt.ylabel('Second Principal Component')
# plt.show()


"kmeans + pca"

pca = PCA(2)
 
#Transform the data
df = pca.fit_transform(scaled_data)
 
# print(df.shape)
 
#Initialize the class object
kmeans = KMeans(n_clusters= 2)
kmeans.fit(df)
#predict the labels of clusters.
label = kmeans.predict(df)
# label = kmeans.predict([df[0]]) #df[:1,:]
# print(label)
# print(df[:1,:])


# print(label[:20])

#filter rows of original data
filtered_label0 = df[label == 0]
 
#plotting the results
# plt.scatter(filtered_label0[:,0] , filtered_label0[:,1])
# plt.show()

#filter rows of original data
filtered_label0 = df[label == 0]
 
filtered_label1 = df[label == 1]
 
#Plotting the results
plt.scatter(filtered_label0[:,0] , filtered_label0[:,1] , color = 'red')
plt.scatter(filtered_label1[:,0] , filtered_label1[:,1] , color = 'black')
plt.show()


