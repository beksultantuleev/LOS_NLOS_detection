from time import time
import numpy as np
import time

class Deque_manager():
    def __init__(self, size):
        self.size = size
        self.data_list = []
        self.std = 0
        self.avg = 0
        self.median = 0
        self.half_array_avrg = 0
    
    def get_data_list(self):
        return self.data_list
    
    def append_data(self, data):
        self.data_list.append(data)
        if len(self.data_list)==self.size+1:
            self.data_list.pop(0)
        self.std = np.std(self.data_list, axis=0)
        self.avg = np.average(self.data_list, axis=0)
        self.median = np.median(self.data_list, axis=0)
        self.half_array_avrg = np.average(self.data_list[int(len(self.data_list)/2):], axis=0)

    def get_std(self):
        return self.std
    
    def get_avrg(self):
        return self.avg
    
    def get_median(self):
        return self.median

    def get_half_array_avrg(self):
        return self.half_array_avrg
    
    def get_last_value(self):
        if len(self.data_list)!=0:
            return self.data_list[-1]

if __name__=="__main__":
    test = Deque_manager(3)
    while True:
        last_pos = np.random.rand(1,3)[0]
        time.sleep(0.5)
        test.append_data(last_pos)
        # print(test.get_data_list())
        print(test.get_median())
    # counter = 0
    # while True:
    #     time.sleep(0.5)
    #     test.append_data(counter)
    #     print(test.get_data_list())
    #     # print(test.get_avrg())
    #     print(test.get_median())
    #     counter+=1

