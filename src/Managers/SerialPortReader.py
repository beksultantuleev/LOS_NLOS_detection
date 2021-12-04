from serial import Serial
import json
import numpy as np
from Managers.Mqtt_manager import Mqtt_Manager

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

if "__main__" == __name__:
    test = SerialPortReader()

    mqtt_conn = Mqtt_Manager('localhost', 'allInOne')
    while True:
        # print(test.get_data("Data: "))
        # print(test.get_data("Distance: "))
        mqtt_conn.publish('allInOne', f"{test.get_data('Data:new ')}")
            # RX_level = test.get_data("RX_level: ")
            # FP_power = test.get_data('FP_POWER: ')
            # RX_diff = RX_level - FP_power
            # print(RX_diff)
        
