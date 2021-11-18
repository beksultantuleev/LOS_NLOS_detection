import numpy as np
from numpy.core.numeric import outer
from scipy.spatial import distance
import math
from src.LQR_controller import LQRcontroller


lqr = LQRcontroller()
lis = np.array([4, 1, 3])
# print(lis)
# print(np.diff(lis, axis=0))
# print(lis[1:] - lis[:-1])


def diff(lis):
    return lis[0]-lis[-1]

def modified_euclidean_d(finish, start):
    output = []
    for i in range(len(finish)):
        result = math.sqrt((finish[i]-start[i])**2)
        output.append(result)
    return output

# print(diff(lis))
finish = [-4,4,4]
start = [1,2,1]

print(f"modified dist {modified_euclidean_d(finish, start)}")
dst = distance.euclidean(start, finish)
print(f"euclidean dist  {dst}")

lqr.set_current_state(start)
lqr.set_desired_state(finish)
print(f"lqr is {lqr.calculate_cmd_input()}")