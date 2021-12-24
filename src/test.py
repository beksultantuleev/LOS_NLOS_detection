'not in use'
import numpy as np
import time
import joblib

# print(65549343+np.random.randint(-10,10))
anchors = np.array([[4, 116, 65549340, -78.996398, 3.512489],
                    [4, 116, 65549318, -78.996398, 10.512489],
                    [4, 116, 65549344, -78.996398, 13.512489]])
raw_data = anchors[:, -2:]
pca_model = joblib.load('trained_models/pca.sav')
k_means_model = joblib.load('trained_models/k_means.sav')

df = pca_model.transform(raw_data)
# print(df)
pred = k_means_model.predict(df)

# print(pred)
processed_anchor_data = np.c_[anchors[:,:-2], pred]

print(processed_anchor_data)
