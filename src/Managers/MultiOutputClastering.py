from sklearn.cluster import KMeans
import pandas as pd
import numpy as np

df = pd.read_csv('grand_final_data_50.csv', header=None).values
# print(df.shape[1])

test = np.array([1,0,1,0,1,1])
def index_creator(df):
    ind_x1 = [i for i in range(0, int(df.shape[1]/2))]
    ind_x2 = [i for i in range(int(df.shape[1]/2), df.shape[1])]
    fin = list(zip(ind_x1, ind_x2))
    # return [i for t in fin for i in t]
    return fin


predictions = []
for i in index_creator(df):
    # print(df[:, i])
    'k means'
    kmeans = KMeans(n_clusters=2)
    kmeans.fit(df[:, i])
    label = kmeans.predict(df[:, i])
    predictions.append(label)
# print(np.array(predictions))
print(np.array(predictions).T)
