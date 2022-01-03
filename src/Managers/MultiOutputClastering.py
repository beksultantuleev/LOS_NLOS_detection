from sklearn.ensemble import RandomForestClassifier
from sklearn.cluster import KMeans
import pandas as pd
import numpy as np
from sklearn.multioutput import MultiOutputClassifier
from sklearn.model_selection import train_test_split
from sklearn import metrics
from sklearn.metrics import multilabel_confusion_matrix
import datetime
from lightgbm import LGBMClassifier
import joblib




class MultiOutputClustering():
    def __init__(self, data_for_training):
        self.data_for_training = data_for_training
        self.Y = None

    def index_creator(self, np_array, return_index=False):
        ind_x1 = [i for i in range(0, int(np_array.shape[1]/2))]
        ind_x2 = [i for i in range(
            int(np_array.shape[1]/2), np_array.shape[1])]
        fin = list(zip(ind_x1, ind_x2))
        if return_index:
            return [i for t in fin for i in t]
        else:
            return fin

    def label_creation(self):
        predictions = []
        detection_mitigation_pair = self.index_creator(self.data_for_training)
        'k means'
        kmeans = KMeans(n_clusters=2, random_state=14)
        kmeans.fit(self.data_for_training[:, detection_mitigation_pair[0]])
        for i in detection_mitigation_pair:
            label = kmeans.predict(self.data_for_training[:, i])
            predictions.append(label)
        # print(np.array(predictions))
        self.Y = np.array(predictions).T

        self.x_train, self.x_test, self.y_train, self.y_test = train_test_split(
            self.data_for_training, self.Y, test_size=0.2)#[:, self.index_creator(self.data_for_training, return_index=True)]
    
    
    def multiOutputClassifier(self, classifier, filename = 'multioutput_model.sav'):
        "works well"
        clf = MultiOutputClassifier(classifier).fit(
            self.x_train, self.y_train)

        # y_pred = np.transpose([y_pred[:, 1]
        #                     for y_pred in clf.predict_proba(x_test)])
        # score = roc_auc_score(self.y_test, y_score, average=None)

        y_pred_classif = clf.predict(self.x_test)
        hamming_loss = metrics.hamming_loss(self.y_test, y_pred_classif)
        jaccard_score = metrics.jaccard_score(
            self.y_test, y_pred_classif, average='weighted')
        accuracy = metrics.accuracy_score(self.y_test, y_pred_classif)

        "save model"
        # filename = f'multioutput_model.sav'
        joblib.dump(clf, filename)

        cm = multilabel_confusion_matrix(self.y_test, y_pred_classif)
        results = f'the classifier is {clf}, targets are {None}. Time is {datetime.datetime.now()} \n hamming loss is {hamming_loss}, jaccard score is {jaccard_score} \n accuracy is {accuracy} \nconf matrix is \n{cm}'
        print(results)

        # self.plot_roc_curve(self.y_test, y_pred,
        #                     name_of_dataset=name_of_dataset)
        # self.plot_pr_curve(self.y_test, y_pred,
        #                    name_of_dataset=name_of_dataset)
        print('end')

if __name__ == "__main__":

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
        'silent': True,
        # 'bagging_freq': 10,
        'is_unbalance': True,
        'metric': 'auc'
    }
    lgbm = LGBMClassifier(**parameters_lgbm)

    rf = RandomForestClassifier(max_depth=2)
    X = pd.read_csv('grand_final_data_100.csv', header=None).values

    test = MultiOutputClustering(data_for_training=X)
    test.label_creation()
    test.multiOutputClassifier(rf)


    # model_ = joblib.load('multioutput_model.sav')
    # new_data = [0,0,0,0,0,0]
    # pred = model_.predict([new_data])
    # print(pred)
