import pandas as pd
from scipy.sparse import data
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.feature_selection import RFE
from lightgbm import LGBMClassifier
import shap
import matplotlib.pyplot as plt
import tensorflow as tf
from sklearn.preprocessing import StandardScaler

'data analysis for selecting right variables'

los_data = pd.read_csv('data/LOS_added_values_complete.csv')
# los_data = los_data[los_data['RX_difference'] >0]

los_data["Class"] = 1

# print(los_data[los_data['RX_difference'] <0])


nlos_data = pd.read_csv('data/NLOS_added_values_4_ss45000_1.csv')

# print(nlos_data[nlos_data['RX_difference'] <0])
# to_drop_index = nlos_data[(nlos_data['RX_difference'] <10) & (nlos_data['RX_level'] >-85)].index
# nlos_data.drop(to_drop_index, inplace = True)

nlos_data["Class"] = 0

dataframe = pd.concat([nlos_data, los_data], ignore_index=True)
dataframe = dataframe.drop(["acquisition"], axis=1)#, "F2_std_noise"
print(f">>>>>>>>>>>>>>>>>>>>>>\nRX_level max value is {dataframe['RX_level'].max()} and min is {dataframe['RX_level'].min()}")
print(f">>>>>>>>>>>>>>>>>>>>>>\nRX_difference max value is {dataframe['RX_difference'].max()} and min is {dataframe['RX_difference'].min()}")

# print(dataframe[dataframe['RX_difference'] <0])

Y = dataframe.iloc[:, -1]
X = dataframe.iloc[:, :-1]



x_train, x_test, y_train, y_test = train_test_split(
            X, Y, test_size=0.3)


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
        'max_depth': 4,
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
rf = RandomForestClassifier()

def classification(method):
    method.fit(x_train, y_train)
    "setting shap values"
    explainer = shap.TreeExplainer(method)
    shap_values = explainer.shap_values(x_test)
    "summary plot"
    fig = shap.summary_plot(shap_values[1], x_test, show=False)
    plt.title(f'Features')
    plt.tight_layout()
    # plt.show()
    plt.savefig(
        f"src/Data_analysis/plot_data/summary_plot.jpg")
    plt.close()
    'Dependence plot'
    _selected_features = [i for i in x_test]
    for i in range(len(_selected_features)):
        # shap_values[0]>>to [1]
        shap.dependence_plot(i, shap_values[1], x_test, show=False)
        # plt.title(f"dependences")
        plt.tight_layout()
        plt.savefig(
        f"src/Data_analysis/plot_data/Dep_plot_{i}.jpg")
    plt.close()
    "<<<<<<<<"

# print(dataframe.loc[dataframe["Class"]==1].corr())
classification(lgbm)
