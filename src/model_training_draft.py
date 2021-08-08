from numpy.core.fromnumeric import shape

import pandas as pd
import numpy as np
import random

# from keras.models import Sequential
from keras.layers import Dense
# from keras import optimizers
# from keras.utils import to_categorical
# from tensorflow.keras.utils import to_categorical
from tensorflow import keras
from keras.models import Sequential
from sklearn.preprocessing import LabelEncoder
# data_split_tuner_value = 10  # 13 for succ #total 50
epoch_number = 50
batch_number = 8
validation_ratio = 0.2


''' Main Code '''

# Now use panda to handle the dataset
# columnNames = ['acquisition','activity','acc_x','acc_y','acc_z','gyr_x','gyr_y','gyr_z'] # add activity instead letter ,'temperature'
# dataset = pd.read_csv(dataset_path,header = None, names=columnNames,na_values=',')
dataset = pd.read_csv("data/motion_recognition.csv")
dataset = dataset.drop(['Unnamed: 0'], axis=1)

lbl_encode = LabelEncoder()
value_codes = [i for i in enumerate(np.sort(dataset['activity'].unique()))]
print(value_codes)
for col in dataset:
    if dataset[col].dtype.name == "object":
        try:
            dataset[col] = lbl_encode.fit_transform(
                dataset[col])
        except:
            pass

# # find the number
last_index = max(np.unique(dataset.acquisition))

second_axis = []
for acq_index in range(1, last_index+1):  # it was with 1
    second_axis.append(dataset[dataset.acquisition == acq_index].shape[0])

# print(f"second axis is {second_axis}")
# print(min(second_axis))

dtensor = np.empty((0, 6*min(second_axis)))  # change shape of dtensor
labels = np.empty((0))


for acq_index in range(1, last_index+1):  # it was from 2

    temp = dataset[dataset.acquisition == acq_index]

    acc_x = temp.acc_x
    acc_y = temp.acc_y
    acc_z = temp.acc_z

    gyr_x = temp.gyr_x
    gyr_y = temp.gyr_y
    gyr_z = temp.gyr_z

    dtensor = np.vstack([dtensor, np.concatenate(
        (acc_x, acc_y, acc_z, gyr_x, gyr_y, gyr_z))])
    labels = np.append(labels, np.unique(temp.activity))

print(labels)
labels = np.asarray(pd.get_dummies(labels), dtype=np.int8)

print(labels)
# print(labels.shape)

sample_index = np.arange(0,dtensor.shape[0])
# print(sample_index)

shuffled_indexes = random.sample(list(sample_index), len(list(sample_index)))
# print(shuffled_indexes)

data_split_tuner_value = int(len(sample_index)*validation_ratio)
# print(data_split_tuner_value)

train_data = dtensor[shuffled_indexes[data_split_tuner_value:],:] #it was 20 i made it 6 put shuffle??
test_data = dtensor[shuffled_indexes[:data_split_tuner_value],:]
train_labels = labels[shuffled_indexes[data_split_tuner_value:],:]
test_labels = labels[shuffled_indexes[:data_split_tuner_value],:]

# print(train_data)
# print(f"train {dtensor[sample_index[1:],:]}")
# print(list(dtensor[7]))
# print(labels)
# print(f"test {sample_index[1:]}")
# print(list(test_data[0]))

train_shape = train_data.shape[1]
# print(train_shape)
# print(train_data.shape)
# print(test_data.shape)
# #print(test_data.dtype)
# # print(train_labels.shape)
# #print(test_labels.dtype)

model = Sequential()
model.add(Dense(240,input_shape =(train_shape,),name='input_layer'))
model.add(Dense(64, activation = 'relu', name='hidden1'))

model.add(Dense(2, activation='softmax' , name = 'output_layer')) #softmax #dont forget to put output number
model.compile(optimizer= 'rmsprop', loss='categorical_crossentropy', metrics=['accuracy']) #use sparse is each letter is an integer (es a->1 b->2 c->3 ..) #it was rmsprop now adam
model.summary()

model.fit(train_data,train_labels,epochs=epoch_number, batch_size=batch_number, validation_split=validation_ratio , verbose=1)
results = model.evaluate(test_data, test_labels, verbose=1)

results_names = model.metrics_names
result = "\nThe %s value is: %f \nThe %s value is: %f \n" %(results_names[0] ,results[0],results_names[1] ,results[1])
print(result)
print(f"""Ratio trainded data  {len(train_data)/len(sample_index)}
          Ratio tested data {len(test_data)/ len(sample_index)}""")


# model.save('trained_models/still_wave.h5')
# f = open("trained_models/still_wave.txt", "w")
# f.write(result)
# f.close()
# np.save('trained_models/still_wave_validation.npy', test_data)
# np.save('trained_models/still_wave_label_val.npy', test_labels)
