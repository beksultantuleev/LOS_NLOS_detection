import numpy as np
import scipy.linalg
import time
from numpy.linalg import multi_dot


class LQRcontroller:
    def __init__(self):

        self.dt = 0.5  # make lower to have higher data refresh rate
        self.A = np.array(
            [[1.0, 0.0, 0.0],
             [0.0, 1.0, 0.0],
                [0.0, 0.0, 1.0]])
        self.B = np.array(
            [[self.dt, 0.0, 0.0],
             [0.0, self.dt, 0.0],
                [0.0, 0.0, self.dt]])
        self.Q = np.array(  # Q controls state accuracy
            [[1, 0.0, 0.0],
             [0.0, 1, 0.0],
                [0.0, 0.0, 1]])  # 0.7 is good for kalman 0.3
        self.R = np.array(
            [[0.5, 0.0, 0.0],
             [0.0, 0.5, 0.0],
                [0.0, 0.0, 0.5]])  # R controls inpu5t accuracy
        self.desired_state = []
        self.current_state = []
        self.cmd_input = []
        self.max_input_power = np.ones((1, 3))[0] * 10
        self.max_velocity = 1

    def dlqr(self):
        '''Solve the discrete time lqr controller
        x[k+1] = A x[k] + B u[k]
        cost = sum x[k].T*Q*x[k] + u[k].T*R*u[k]'''

        # first, solve the ricatti equation
        self.P = np.matrix(scipy.linalg.solve_discrete_are(
            self.A, self.B, self.Q, self.R))
        # compute the LQR gain
        self.K = np.matrix(scipy.linalg.inv(
            self.B.T*self.P*self.B+self.R)*multi_dot([self.B.T, self.P, self.A]))
        # print(f"optimal K is {self.K}")
        return -self.K  # #The feedback gain is a matrix K

    def get_current_input(self):
        return self.cmd_input

    def set_current_state(self, current_state):
        self.current_state = current_state

    def set_desired_state(self, desired_state):
        self.desired_state = desired_state

    def calculate_cmd_input(self):
        #u = -K_lqr * (current_state - desired_state) + u_d
        # u_d is required input to maintain desired state
        distance = np.subtract(self.current_state, self.desired_state)

        # velocities needed to get to desited state
        u = np.dot(self.dlqr(), distance).tolist()[0]
        # print(f"distance {u}")

        self.cmd_input = np.array([u[0], u[1],u[2]])
        return self.get_current_input()


if __name__ == "__main__":

    mambo = LQRcontroller()
    # ====================
    mambo.set_current_state([0,0,0])
    mambo.set_desired_state([5,-1, -1])
    u = mambo.calculate_cmd_input()
    print(u)
    # ===================
    # destX = 1
    # num = 0
    # mambo.set_desired_state([destX, 0, 0])
    # while num < destX:

    #     mambo.set_current_state([num, 0, 0])
    #     u = mambo.calculate_cmd_input()
    #     num += 0.1
    #     time.sleep(0.2)
    #     print(f"{u} at position>> {num}")
# ========================================
    # destY = 2
    # num = 0
    # mambo.set_desired_state([0, destY, 0])
    # while num <destY:

    #     mambo.set_current_state([0,num,0])
    #     u = mambo.calculate_cmd_input()
    #     num +=0.5
    #     time.sleep(0.1)
    #     print(f"{u} at position>> {num}")
# ========================================
    # destZ = 3
    # num = 0
    # mambo.set_desired_state([0, 0, destZ])
    # while num <destZ:

    #     mambo.set_current_state([0,0,num])
    #     u = mambo.calculate_cmd_input()
    #     num +=0.5
    #     time.sleep(0.1)
    #     print(f"{u} at position>> {num}")