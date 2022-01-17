from Managers.SerialPortReader import SerialPortReader
from Managers.Mqtt_manager import Mqtt_Manager

test = SerialPortReader()

mqtt_conn = Mqtt_Manager('192.168.0.119', 'allInOne')
pattern = 'Data: '
while True:
    # print(test.get_data("Data: "))
    # print(test.get_data("Distance: "))
    mqtt_conn.publish('allInOne', f"{test.get_data(pattern=pattern)}")
        # RX_level = test.get_data("RX_level: ")
        # FP_power = test.get_data('FP_POWER: ')
        # RX_diff = RX_level - FP_power
        # print(RX_diff)