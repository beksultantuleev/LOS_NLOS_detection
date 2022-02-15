from serial import Serial
import json
import numpy as np
# from Mqtt_manager import Mqtt_Manager
from Managers.Mqtt_manager import Mqtt_Manager
import time

class SerialPortReader():
    def __init__(self, baudrate=115200, port='/dev/ttyACM0'):
        self.baudrate = baudrate
        self.port = port
        self.instance = Serial(port=self.port, baudrate=self.baudrate)
        self.data = []

    def get_data(self, pattern):
        raw_data = self.instance.readline().decode('utf')
        if pattern in raw_data:
            self.data = json.loads(raw_data[len(pattern):])
        return self.data
    
    def get_noPattern_data(self):
        raw_data = self.instance.readline().decode('utf')
        print(raw_data)
        # try:
        #     self.data = json.loads(raw_data)
        #     print(self.data)
        # except:
        #     pass
        # # return self.data
        # return self.data

if "__main__" == __name__:
    test = SerialPortReader()

    # mqtt_conn = Mqtt_Manager('192.168.0.119', 'sensor_data')
    data = test.get_noPattern_data()
    while True:
        # time.sleep(0.5)
        
        print(data)
        # mqtt_conn.publish('sensor_data', f"{data}")
            # RX_level = test.get_data("RX_level: ")
            # FP_power = test.get_data('FP_POWER: ')
            # RX_diff = RX_level - FP_power
            # print(RX_diff)
        
