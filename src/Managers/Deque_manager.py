from time import time
import numpy as np
import time

class Deque_manager():
    def __init__(self, size):
        self.size = size
        self.data_list = []
        self.std = 0
        self.avg = 0
    
    def get_data_list(self):
        return self.data_list
    
    def append_data(self, data):
        self.data_list.append(data)
        if len(self.data_list)==self.size+1:
            self.data_list.pop(0)
        self.std = np.std(self.data_list)
        self.avg = np.average(self.data_list)

    def get_std(self):
        return self.std
    
    def get_avrg(self):
        return self.avg

if __name__=="__main__":
    test = Deque_manager(10)
    counter = 0
    while True:
        time.sleep(0.5)
        test.append_data(counter)
        print(test.get_data_list())
        print(test.get_avrg())
        counter+=1

