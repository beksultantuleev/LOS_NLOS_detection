from os import set_inheritable
from numpy.lib.function_base import bartlett
import paho.mqtt.client as mqttClient
import time
import json
import numpy as np

class Mqtt_Manager:
    
    Connected = False  # global variable for the state of the connection

    def __init__(self, host, topic, port=1883, user=None, passwd=None):
        self.host = host
        self.port = port
        self.user = user
        self.passwd = passwd
        self.topic = topic
        self.client = mqttClient.Client() 
        self.client.on_connect = self.on_connect  # attach function to callback
        self.client.on_message = self.on_message 
        self.raw_data = []
        self.processed_data = []
        self.processed_data_nested = []
        self.connect()
        self.subs(self.topic)
        # self.multiple_data = []

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("Connected to broker")
            global Connected  # Use global variable
            Connected = True  # Signal connection
        else:
            print("Connection failed")

    def on_message(self, client, userdata, message):
        'change here if want different data structure'
        self.raw_data = message.payload.decode("utf-8")
        self.processed_data = json.loads(self.raw_data)
        # data = message.payload[1:-1].decode("utf-8").split(",")
        # self.processed_data_nested = np.array([[float(data[0])], [float(data[1])], [float(data[2])]])


    def connect(self):
        self.client.connect(self.host, port=self.port)  # connect to broker
        self.client.loop_start()  # start the loop

    def subs(self, *args):
        local_counter = 0
        ids = []
        for topics in args:
            ids.append(local_counter)   
            local_counter+=1
        self.client.subscribe(list(zip(args, ids)))  # topic
    
    def publish(self, topc, msg):
        # print("published!")
        self.client.publish(topc, msg)

# try:
#     while True:
#         time.sleep(2)
#         # value = "from subs"
#         # client.publish("my_publish_test", value)

# except KeyboardInterrupt:
#     print("exiting")
#     client.disconnect()
#     client.loop_stop()
if __name__=="__main__":
    import keyboard
    test = Mqtt_Manager("localhost", "accelerometer_LSM303AGR") #accelerometer_LSM303AGR
    
    try:
        while True:
            time.sleep(0.1)
            if test.processed_data:
                print(test.processed_data)
    except KeyboardInterrupt:
        print("done")

        
