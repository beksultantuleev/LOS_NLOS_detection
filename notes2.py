import tensorflow as tf
import pandas as pd

dataframe = pd.read_csv('full_dataframe_with_rx_difference.csv')

min_val = tf.reduce_min(dataframe.loc[dataframe["Class"]==1][['RX_level', 'RX_difference']])
max_val = tf.reduce_max(dataframe.loc[dataframe["Class"]==1][['RX_level', 'RX_difference']])

print(min_val)
print(max_val)
print(dataframe.loc[dataframe["Class"]==1][['RX_level', 'RX_difference']])