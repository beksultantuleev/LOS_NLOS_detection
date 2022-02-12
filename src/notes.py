# from keras.models import load_model
from typing import final
from time import sleep, time
# from tensorflow import keras
# from keras.models import load_model
import pandas as pd
import numpy as np
# from Core_functions.hub_of_functions import deque_manager
from collections import deque
import tensorflow as tf
from keras.models import load_model
from Core_functions.hub_of_functions import value_extractor
import pandas as pd
from scipy.spatial.distance import cdist
from scipy.spatial import ConvexHull
# points = np.random.rand(30, 2)   # 30 random points in 2-D
# hull = ConvexHull(points)
# # print(hull.simplices)
# import matplotlib.pyplot as plt
# plt.plot(points[:,0], points[:,1], 'o')
# for simplex in hull.simplices:
#     plt.plot(points[simplex,0], points[simplex,1], 'k-')

# plt.plot(points[hull.vertices,0], points[hull.vertices,1], 'r--', lw=2)
# plt.plot(points[hull.vertices[0],0], points[hull.vertices[0],1], 'ro')
# plt.show()

A_n1 = np.array([[2], [2], [0.9]])
A_n2 = np.array([[0], [0], [0.5]])
A_n3 = np.array([[5], [0], [1.8]])  # master
A_n4 = np.array([[3], [5], [1]])  # master
A_n5 = np.array([[2], [5], [4]]) 
anchors_pos = np.array([A_n1, A_n2, A_n3, A_n4, A_n5])

anchors_pos = anchors_pos.reshape(5,3)[:, :-1]
# print(anchors_pos)
points = anchors_pos  
set_points = []
hull = ConvexHull(points)
import matplotlib.pyplot as plt
plt.plot(points[:,0], points[:,1], 'o')
for simplex in hull.simplices:
    print(f'zero >>{points[simplex,0]}, one >> {points[simplex,1]}')
    plt.plot(points[simplex,0], points[simplex,1], 'k-')
print(f'original points >>\n {points}')


# plt.plot(points[hull.vertices,0], points[hull.vertices,1], 'r--', lw=2)
# plt.plot(points[hull.vertices[0],0], points[hull.vertices[0],1], 'ro')
plt.show()
# print(points[simplex,1])