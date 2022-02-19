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
        self.fraction_array_avrg = 0
        self.fraction_array_median = 0
    
    def get_data_list(self):
        return self.data_list
    
    def append_data(self, data, divider_percentage = 0.25):
        self.data_list.append(data)
        if len(self.data_list)==self.size+1:
            self.data_list.pop(0)
        self.divider = int(len(self.data_list)*divider_percentage)
        self.std = np.std(self.data_list, axis=0)
        self.avg = np.average(self.data_list, axis=0)
        self.median = np.median(self.data_list, axis=0)
        self.fraction_array_avrg = np.average(self.data_list[-self.divider:], axis=0)
        self.fraction_array_median = np.median(self.data_list[-self.divider:], axis=0)

    def get_std(self):
        return self.std
    
    def get_avrg(self):
        return self.avg
    
    def get_median(self):
        return self.median

    def get_fraction_array_avrg(self):
        return self.fraction_array_avrg
    
    def get_fraction_array_median(self):
        return self.fraction_array_median
    
    def get_last_value(self):
        if len(self.data_list)!=0:
            return self.data_list[-1]

if __name__=="__main__":
    test = Deque_manager(16)
    # while True:
    #     last_pos = np.random.rand(1,3)[0]
    #     time.sleep(0.5)
    #     test.append_data(last_pos)
    #     # print(test.get_data_list())
    #     print(test.get_median())
    counter = 0
    while True:
        time.sleep(0.5)
        test.append_data(counter+ np.random.randint(-10, 10), divider_percentage=0.25)
        print(test.get_data_list())
        # print(test.get_avrg())
        print(f'full avrg>> {test.get_avrg()}')
        print(f'full median>> {test.get_median()}')
        print(f'frac avrg>> {test.get_fraction_array_avrg()}')
        print(f'frac median>> {test.get_fraction_array_median()}')
        counter+=1

