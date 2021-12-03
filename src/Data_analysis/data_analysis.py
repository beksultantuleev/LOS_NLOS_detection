import pandas as pd
from scipy.sparse import data
from sklearn.model_selection import train_test_split
from sklearn.feature_selection import RFE
from lightgbm import LGBMClassifier
import shap
import matplotlib.pyplot as plt
import tensorflow as tf
from sklearn.preprocessing import StandardScaler

'data analysis for selecting right variables'

los_data = pd.read_csv('data/LOS_2m_test_4_ss5000_1.csv')
los_data["Class"] = 1

nlos_data = pd.read_csv('data/NLOS_2m_test_4_ss5000_1.csv')
# nlos_data = pd.read_csv('data/NLOS_1m_test_4_ss5000_2.csv')
nlos_data["Class"] = 0
# print(los_data.head())
# print(nlos_data.head())
dataframe = pd.concat([nlos_data, los_data], ignore_index=True)
dataframe = dataframe.drop(["acquisition"], axis=1)

# dataframe.to_csv('full_dataframe_with_rx_difference.csv', index=None)


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
            X, Y, test_size=0.2)


def run_RFE(num_of_feature, classifier):
    print(f"Method is {classifier}")
    rfe = RFE(classifier, num_of_feature)
    rfe = rfe.fit(X, Y)
    # print(rfe.support_)
    # print(rfe.ranking_)
    selected_rfe_features_df = pd.DataFrame(
        {"feature": list(X.columns), "scores": rfe.ranking_})

    "selected features of rfe model"
    order = selected_rfe_features_df.nsmallest(10, "scores")
    print(order)
    best_features_rfe = list(selected_rfe_features_df.nsmallest(
        num_of_feature, "scores")['feature'])
    print(best_features_rfe)

parameters_lgbm = {
        'boosting_type': 'gbdt',
        'num_leaves': 10,
        'max_depth': 2,
        'n_estimators': 50,
        # 'verbose': 1,
        # 'learning_rate': 0.01,
        # 'subsample_for_bin': 200000,
        # 'class_weight':"balanced", #for multiclass
        # 'min_split_gain': 0.5,
        # 'min_child_weight': 10**(-3),
        'n_jobs': -1,
        'feature_fraction': 1,
        'silent': False,
        # 'bagging_freq': 10,
        'is_unbalance': False,
        'metric': 'auc'
    }
lgbm = LGBMClassifier(**parameters_lgbm)
# run_RFE(4, lgbm)


def classification(method):
    # self.method = method
    method.fit(x_train, y_train)
    y_pred_class = method.predict(x_test)
    y_predict = method.predict_proba(x_test)


    "setting shap values"
    explainer = shap.TreeExplainer(method)
    shap_values = explainer.shap_values(x_test)

    "summary plot"
    fig = shap.summary_plot(shap_values[1], x_test, show=True)
    # plt.title(f'{target}, data: {name_of_dataset}')
    # plt.tight_layout()
    # plt.savefig(
    #     f"src_Protection_Project/pictures/shap/summary_plot/{target}_{name_of_dataset}_summary_plot.jpg")
    # plt.close()
    "<<<<<<<<"


# dataframe = dataframe.drop(["CIR", 'FPPL'], axis= 1)
# print(dataframe.loc[dataframe["Class"]==1].corr())

classification(lgbm)
