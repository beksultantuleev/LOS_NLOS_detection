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

'''
to validate data and plot confusion matrix, ROC and PRC
'''
"control here"
plot_cm = False
plot_roc_prc = False


'select data'
# los_data = pd.read_csv('data/LOS_1m_test_4_ss5000_1.csv')
los_data = pd.read_csv('data/LOS_added_values_complete.csv')
los_data["Class"] = 1

nlos_data = pd.read_csv('data/NLOS_added_values_2_ss29988_1.csv')
# nlos_data = pd.read_csv('data/NLOS_data_water_2_ss95000_1.csv')
# nlos_data = pd.read_csv('data/NLOS_1m_test_4_ss5000_1.csv')
nlos_data["Class"] = 0
dataframe = pd.concat([nlos_data, los_data], ignore_index=True)
dataframe = dataframe.drop(["acquisition", ], axis=1) #'F2_std_noise'


Y = dataframe.iloc[:, -1]
X = dataframe.iloc[:, :-1]


x_train, x_test, y_train, y_test = train_test_split(
    X, Y, test_size=0.01)

'anomaly detection'
autoencoder = load_model('trained_models/anomaly_detection_model')
path = 'src/Training/logs/anomaly_detection/logs_Single_data_input.txt'

threshold = value_extractor("Threshold:", path)
min_val = value_extractor("Min_val:", path)
max_val = value_extractor("Max_val:", path)
df_anomaly = (x_train.values -
              min_val) / (max_val - min_val)

'to check anomaly'
# df_anomaly = (np.array([-79, 3, 12, 60]) -
#               min_val) / (max_val - min_val)
# pred = predict_anomaly_detection(autoencoder, [df_anomaly], threshold)
# print(pred)
'kmeans pca and gmm'
pca_model = joblib.load('trained_models/pca.sav')
scaler = joblib.load('trained_models/standard_scaler_pca_kmeans.save')
scaler_gmm = joblib.load('trained_models/standard_scaler_gmm.save')
k_means_model = joblib.load('trained_models/k_means.sav')
gmm_model = joblib.load('trained_models/gmm.sav')

'to test pca and kmeans or gmm'
# scaled_data = scaler.transform([[-79, 3, 7, 24]])
# df = pca_model.transform(scaled_data)
# pred = gmm_model.predict(df)
# pred = k_means_model.predict(df)
# pred_proba = gmm_model.predict_proba(df)
# print(pred)
# print(pred_proba)
'end testing'
scaled_data = scaler.transform(x_train)
scaled_data_for_gmm = scaler_gmm.transform(x_train)
df = pca_model.transform(scaled_data)


pred = [0]*3
pred[0] = k_means_model.predict(df)
pred[1] = gmm_model.predict(scaled_data_for_gmm)
pred[2] = predict_anomaly_detection(autoencoder, df_anomaly, threshold)


model_name = {0: 'pca with k-means', 1: 'pca with gmm', 2: 'Anomaly Detection'}
for i in range(len(pred)):
    print(f'>>>>{model_name[i]}<<<')

    accuracy = metrics.accuracy_score(
        y_train, pred[i])
    cm = metrics.confusion_matrix(
        y_train, pred[i])
    precision = metrics.precision_score(y_train, pred[i])
    recall_score = metrics.recall_score(y_train, pred[i])
    print(cm)
    print(f'accuracy {accuracy} \nprecision {precision} \nrecall {recall_score}')
    if plot_cm:

        plt.style.use('default')
        sns.heatmap(cm, annot=True, fmt='', cmap='Blues')
        plt.title(f"{model_name[i]}")
        # plt.title(f"{'PCA with GMM'}")
        plt.show()

if plot_roc_prc:
    pred[2] = gmm_model.predict_proba(scaled_data_for_gmm)[:, 1]
    'roc'
    for i in range(len(pred)):
        plt.style.use('fivethirtyeight')
        fpr, tpr, thresh = metrics.roc_curve(y_train, pred[2])
        auc = metrics.roc_auc_score(y_train, pred[2])
        precision, recall, thresholds = metrics.precision_recall_curve(
            y_train, pred[2])

    'prc'
    AP = metrics.average_precision_score(
        y_train, pred[2])
    plt.plot(recall, precision, linestyle="-",
             label=f"PCA with GMM (Avrg Precision = {AP:.4f})")
    plt.xlabel("Recall")
    plt.ylabel("Precision")
    plt.title(f"Precision-Recall graph")
    plt.legend(loc="best")
    plt.tight_layout()
    plt.show()
    'roc'
    plt.plot(
        fpr, tpr, label=f"PCA with GMM, auc= {auc:.4f}")
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.title(f"ROC graph")
    plt.plot([0, 1], [0, 1], linestyle="--",
                c="black", linewidth=2)

    plt.legend(loc="best")
    plt.tight_layout()
    plt.show()
