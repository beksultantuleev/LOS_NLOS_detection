'not in use'
import numpy as np
import time
import joblib
# amount_of_anchors = 3
# anchors_data = np.array([[0]*amount_of_anchors])
# print(anchors_data)
# st = '''[[4.0000000e+00 6.5549390e+07 1.0000000e+00]
#       [4.0000000e+00 6.5549416e+07 0.0000000e+00]
#       [4.0000000e+00 6.5549288e+07 1.0000000e+00]]'''
st = '[4.0000000e+00 6.5549390e+07 1.0000000e+00]'


print(np.fromstring(st))
# print(65549343+np.random.randint(-10,10))
# anchors = np.array([[4, 116, 65549340, -78.996398, 3.512489],
#                     [4, 116, 65549318, -78.996398, 10.512489],
#                     [4, 116, 65549344, -78.996398, 13.512489]])
# raw_data = anchors[:, -2:]
# pca_model = joblib.load('trained_models/pca.sav')
# k_means_model = joblib.load('trained_models/k_means.sav')

# df = pca_model.transform(raw_data)
# # print(df)
# pred = k_means_model.predict(df)

# # print(pred)
# processed_anchor_data = np.c_[anchors[:,:-2], pred]

# # print(processed_anchor_data)
# print(raw_data.shape)
