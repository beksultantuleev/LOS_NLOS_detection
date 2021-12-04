import numpy as np
from numpy.linalg import multi_dot


class KalmanFilterUWB:
    def __init__(self, q):
        '''"
        Give matrices for an estimator of the form
        _____
        q_pred = A*q + G*[ax, ay, az]  |ax+bu
        p_pred = A*Pup*A.T + GQG.T |c + du
        z = [x,y,z, x1,y1,z1]
        '''
        self.z = []
        self.A = np.eye(np.size(q, 0))
        # for 2 Hz we multiply by 0.5. im trying 0.2
        self.G = np.eye(np.size(q, 0)) * 0.5
        self.H = np.eye(3)
        self.R = np.array(
                [[0.5, 0, 0],
                 [0, 0.5, 0],
                 [0, 0, 0.5]])

        self.Q = np.eye(np.size(q, 0))   # process noise it was * 0.5
        self.q = q

        self.S = []


    def get_state_estimation(self, q, u, z, p_update_old):
        self.q = q
        self.u = np.matrix(u).T  # transpose it
        self.z = np.matrix(z).T

        self.p_update_old = p_update_old

        self.q_prediction = np.dot(self.A, self.q)+np.dot(self.G, self.u)
        self.p_prediction = multi_dot(
            [self.A, self.p_update_old, self.A.T]) + multi_dot([self.G, self.Q, self.G.T])

        self.s_update = np.dot(
            np.dot(self.H, self.p_prediction), self.H.T) + self.R
        # print(f"s_update>>{self.s_update}")
        self.W_gain = multi_dot(
            [self.p_prediction, self.H.T, np.linalg.inv(self.s_update)])

        self.q_update = self.q_prediction + \
            np.dot(self.W_gain,  (self.z - np.dot(self.H, self.q_prediction)))
        # print(f"q_update>>{self.q_update}")
        self.p_update = np.dot(
            (np.eye(3)-np.dot(self.W_gain, self.H)), self.p_prediction)
        # print(f"self.p_update >> \n{self.p_update}")

        self.S = [self.p_update, self.q_update]  # modification part
        return self.S
        # return self.q_update.T.tolist()[0]


if __name__ == "__main__":
    q = np.zeros((3, 1))
    p = np.zeros((3, 3))
    u = [1, 0, 0]  # current speed_x, speed_y, speed_z
    z = [1, 2, 3]
    state = KalmanFilterUWB(q)

    p_update, q_update = state.get_state_estimation(q, u, z, p)
    # # print(f"this is p >>\n{p1}")
    print(f"our UAV is here {q_update.T.tolist()[0]}")
