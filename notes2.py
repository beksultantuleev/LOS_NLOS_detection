import numpy as np

lis = np.array([4,1])
# print(lis)
# print(np.diff(lis, axis=0))
# print(lis[1:] - lis[:-1])
def diff(lis):
    return lis[:-1]-lis[1:]

print(diff(lis))