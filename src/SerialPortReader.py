from posix import ST_RDONLY
from serial import Serial
import json
import numpy as np

import serial


# serianInstanace = Serial('/dev/ttyACM0', baudrate=115200)


# while True:
#     data = serianInstanace.readline().decode('utf')
#     if "Data: " in data:
#         processed_data = json.loads(data[6:])
#         print(processed_data)

class SerialPortReader():
    def __init__(self, baudrate=115200, port='/dev/ttyACM0'):
        self.baudrate = baudrate
        self.port = port
        self.instance = Serial(port=self.port, baudrate=self.baudrate)
        self.data = []

    def get_data(self, pattern):
        raw_data = self.instance.readline().decode('utf')
        final_data = None
        if pattern in raw_data:
            self.data = json.loads(raw_data[len(pattern):])
        return self.data

if "__main__" == __name__:
    test = SerialPortReader()
    while True:
        print(test.get_data("Data: "))
        # print(test.get_data("Distance: "))

            # RX_level = test.get_data("RX_level: ")
            # FP_power = test.get_data('FP_POWER: ')
            # RX_diff = RX_level - FP_power
            # print(RX_diff)
        
