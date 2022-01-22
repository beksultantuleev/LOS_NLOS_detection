import pandas as pd
from scipy.sparse import data
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt
import tensorflow as tf
from sklearn.preprocessing import StandardScaler
import joblib
import sklearn.metrics as metrics
from keras.models import load_model
from hub_of_functions import value_extractor, predict_anomaly_detection
import numpy as np
import seaborn as sns

'''note! validation works fine for 1 m data, for longer range i need to sample new data
roc curve has elbows because i cant get predict_proba in unsupervised ML. Conf mat works well.
probably i need to sample data for 2,3,4 etc meters and merge em together (i have data for LOS).
'''

# los_data = pd.read_csv('data/LOS_1m_test_4_ss5000_1.csv')
los_data = pd.read_csv('data/LOS_good_data_complete.csv')
los_data["Class"] = 1

nlos_data = pd.read_csv('data/NLOS_2m_generated_4_ss95000_1.csv')
# nlos_data = pd.read_csv('data/NLOS_data_water_2_ss95000_1.csv')
# nlos_data = pd.read_csv('data/NLOS_1m_test_4_ss5000_1.csv')
nlos_data["Class"] = 0
# print(los_data.head())
# print(nlos_data.head())
dataframe = pd.concat([nlos_data, los_data], ignore_index=True)
# dataframe = dataframe.drop(["acquisition", 'F1', 'F2', 'F3', 'CIR'], axis=1)
dataframe = dataframe.drop(["acquisition"], axis=1)
# dataframe['RX_level'] = dataframe['RX_level'] * (-1)
# print(f">>>>>>>>>>>>>>>>>>>>>>\nmax value is {dataframe['RX_level'].max()} and min is {dataframe['RX_level'].min()}")


'scaler'
# class_ = dataframe["Class"]
# scaler = StandardScaler()
# scaler.fit(dataframe.iloc[:, :-1])
# dataframe = pd.DataFrame(scaler.transform(dataframe.iloc[:, :-1]), columns=list(dataframe.iloc[:, :-1].columns))
# print(dataframe.shape)

# print(dataframe)
Y = dataframe.iloc[:, -1]
X = dataframe.iloc[:, :-1]
# Y = class_
# X = dataframe

x_train, x_test, y_train, y_test = train_test_split(
    X, Y, test_size=0.1)

pca = False

'anomaly detection'
autoencoder = load_model('trained_models/anomaly_detection_model')
path = 'src/Training/logs/anomaly_detection/logs_Single_data_input.txt'

threshold = 0.03  # value_extractor("Threshold:", path)
min_val = value_extractor("Min_val:", path)
max_val = value_extractor("Max_val:", path)
df_anomaly = (x_train.values -
              min_val) / (max_val - min_val)

'to check'
# df_anomaly = (np.array([-84, 10]) -
#               min_val) / (max_val - min_val)
# pred = predict_anomaly_detection(autoencoder, [df_anomaly], threshold)
'kmeans pca'
pca_model = joblib.load('trained_models/pca.sav')
k_means_model = joblib.load('trained_models/k_means.sav')
scaler = joblib.load('trained_models/standard_scaler_pca_kmeans.save')

# df = pca_model.transform(x_train)
"pca use scaler! its better"
# df = pca_model.transform([[-79, 8]])
# scaled_data = scaler.transform([[-85, 7]])
scaled_data = scaler.transform(x_train)
df = pca_model.transform(scaled_data)
pred = [0]*2

pred[0] = k_means_model.predict(df)
pred[1] = predict_anomaly_detection(autoencoder, df_anomaly, threshold)

for i in range(len(pred)):
    print(f"{'pca with k-means' if i == 0 else 'Anomaly Detection'}")
    accuracy = metrics.accuracy_score(
        y_train, pred[i])
    cm = metrics.confusion_matrix(
        y_train, pred[i])
    print(cm)
    print(accuracy)

# # plt.style.use('default')
# # sns.heatmap(cm, annot=True, fmt='', cmap='Blues')
# # plt.title(f"{'PCA with K-means' if pca else 'Anomaly Detection'}")
# # # plt.savefig(
# # #     f"src_Protection_Project/pictures/confusion_matrix/binary/cm_{i[1]}_{name_of_dataset}.jpg")
# # plt.show()

for i in range(len(pred)):
    plt.style.use('fivethirtyeight')
    fpr, tpr, thresh = metrics.roc_curve(y_train, pred[i])
    auc = metrics.roc_auc_score(y_train, pred[i])
    precision, recall, thresholds = metrics.precision_recall_curve(
        y_train, pred[i])

    plt.plot(
        fpr, tpr, label=f"{'PCA with k-means' if i == 0 else 'Anomaly Detection'}, auc= {auc:.4f}")
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.title(f"ROC graph")
    plt.plot([0, 1], [0, 1], linestyle="--",
             c="black", linewidth=2)


# plot_name = "PRC"
# AP = metrics.average_precision_score(
#     y_train, pred)
# plt.plot(recall, precision, linestyle="-",
#          label=f"pca (AP = {AP:.4f})")
# plt.xlabel("Recall")
# plt.ylabel("Precision")
# plt.title(f"Precision-Recall graph")

plt.legend(loc="best")
plt.tight_layout()
plt.show()
