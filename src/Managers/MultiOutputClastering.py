from sklearn.ensemble import RandomForestClassifier
from sklearn.cluster import KMeans
import pandas as pd
import numpy as np
from sklearn.multioutput import MultiOutputClassifier, MultiOutputRegressor
from sklearn.model_selection import train_test_split
from sklearn import metrics
from sklearn.metrics import multilabel_confusion_matrix
import datetime
from lightgbm import LGBMClassifier
import joblib
from sklearn.linear_model import LogisticRegression


class MultiOutputClustering():
    def __init__(self, data_for_training, detection_weight=0.6):
        self.data_for_training = data_for_training
        self.detection_weight = detection_weight
        self.Y = None

    def label_creation(self):
        num_of_columns = self.data_for_training.shape[1]
        detection = self.data_for_training[:, :-int(num_of_columns/2)] * self.detection_weight
        mitigation = self.data_for_training[:,
                                            int(num_of_columns/2):] * (1 - self.detection_weight)
        self.Y = detection+mitigation

        self.Y[self.Y >= 0.5] = 1
        self.Y[self.Y < 0.5] = 0
        self.x_train, self.x_test, self.y_train, self.y_test = train_test_split(
            self.data_for_training, self.Y, test_size=0.2)
        # print(self.Y)

    def multiOutputClassifier(self, classifier, filename='trained_models/multioutput_model.sav'):
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

    rf = RandomForestClassifier(max_depth=4, class_weight='balanced')
    lr = LogisticRegression(class_weight='balanced')
    X = pd.read_csv('data/grand_mode_data/grand_final_data_100.csv', header=None).values
    # print(X)
    test = MultiOutputClustering(data_for_training=X)
    test.label_creation()
    test.multiOutputClassifier(lr)

    # model_ = joblib.load('multioutput_model.sav')
    # new_data = [0, 0, 0, 0, 0, 0]
    # pred = model_.predict([new_data])
    # print(pred)
