import numpy as np


A_n1 = np.array([[0], [1], [1.8]])
A_n2 = np.array([[6], [0], [2]])
A_n3 = np.array([[3], [3.5], [1]])  # master
# A_n4 = np.array([[3], [5], [1]])  # master
anchor_postion_list = np.array([A_n1, A_n2, A_n3])


def get_position(ts_with_los_prediction):
    c = 299792458

    A_n = anchor_postion_list
    n = len(A_n)

    toa = [0] * len(ts_with_los_prediction)
    counter = 0
    for time_stamp_with_los in ts_with_los_prediction:
        t = np.float32(time_stamp_with_los[1]) * np.float32(15.65e-12)
        toa[counter] = t
        counter += 1

    toa = np.array([toa])
    tdoa = toa - toa[0][0]  # changed here
    # print(tdoa)
    tdoa = tdoa[0][1:]
    # print(tdoa)
    D = tdoa*c  # D is 2x1
    print(ts_with_los_prediction)
    # print(D)

    D = D.reshape(len(ts_with_los_prediction)-1, 1)
    A_diff_one = np.array((A_n[0][0][0]-A_n[1:, 0]), dtype='float32')
    A_diff_two = np.array((A_n[0][1][0]-A_n[1:, 1]), dtype='float32')
    A_diff_three = np.array((A_n[0][2][0]-A_n[1:, 2]), dtype='float32')

    A = 2 * np.array([A_diff_one, A_diff_two, A_diff_three, D]).T

    b = D**2 + np.linalg.norm(A_n[0])**2 - np.sum(A_n[1:, :]**2, 1)
    x_t0 = np.dot(np.linalg.pinv(A), b)

    x_t_0 = np.array([x_t0[0][0], x_t0[0][1], x_t0[0][2]])

    # loop
    f = np.zeros((n-1, 1))
    del_f = np.zeros((n-1, 3))
    A_n = A_n.T
    for ii in range(1, n):

        f[ii-1] = np.linalg.norm(x_t_0-A_n[0, :, ii].reshape(3, 1)) - \
            np.linalg.norm(x_t_0-A_n[0, :, 0].reshape(3, 1))

        del_f[ii-1, 0] = np.dot((x_t_0[0]-A_n[0, 0, ii]), np.reciprocal(np.linalg.norm(x_t_0-A_n[0, :, ii].reshape(
            3, 1)))) - np.dot((x_t_0[0]-A_n[0, 0, 0]), np.reciprocal(np.linalg.norm(x_t_0-A_n[0, :, 0].reshape(3, 1))))
        del_f[ii-1, 1] = np.dot((x_t_0[1]-A_n[0, 1, ii]), np.reciprocal(np.linalg.norm(x_t_0-A_n[0, :, ii].reshape(
            3, 1)))) - np.dot((x_t_0[1]-A_n[0, 1, 0]), np.reciprocal(np.linalg.norm(x_t_0-A_n[0, :, 0].reshape(3, 1))))
        del_f[ii-1, 2] = np.dot((x_t_0[2]-A_n[0, 2, ii]), np.reciprocal(np.linalg.norm(x_t_0-A_n[0, :, ii].reshape(
            3, 1)))) - np.dot((x_t_0[2]-A_n[0, 2, 0]), np.reciprocal(np.linalg.norm(x_t_0-A_n[0, :, 0].reshape(3, 1))))
    x_t = np.dot(np.linalg.pinv(del_f), (D-f)) + x_t_0
    tag_id = ts_with_los_prediction[0][0]

    position = [[x_t[0][0], x_t[1][0], x_t[2][0]], tag_id]
    return position


ts = [[4.0, 65549328.5, 1.0], [4.0, 65549274.7, 0.0], [4.0, 65549361.6, 0.0]]
print(get_position(ts))
