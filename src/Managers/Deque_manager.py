from Mqtt_manager import Mqtt_Manager
import collections
import numpy as np

'deque idea, was implemented in instances itself so at the moment not in use'

cir_conn = Mqtt_Manager('localhost', 'CIR')
fppl_conn = Mqtt_Manager('localhost', 'FPPL')
# while True:
#     if mqtt_data.processed_data:
#         print(mqtt_data.processed_data)

def deque_manager_idea(mqtt_conn, size):
    size = size+1
    # for i in range(num_of_deques):
    deque_test = collections.deque([])
    if mqtt_conn.processed_data:
        while len(deque_test) < size:
            deque_test.appendleft(mqtt_conn.processed_data[0])
            if len(deque_test) == size:
                deque_test.pop()
                return np.array(deque_test)
while True:
    print(deque_manager_idea(cir_conn, 2))
    print(deque_manager_idea(fppl_conn, 3))
