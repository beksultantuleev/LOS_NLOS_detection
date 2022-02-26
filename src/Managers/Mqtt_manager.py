from os import set_inheritable
from numpy.lib.function_base import bartlett
import paho.mqtt.client as mqttClient
import time
import json
import numpy as np


class Mqtt_Manager:

    Connected = False  # global variable for the state of the connection

    def __init__(self, host, topic=None, port=1883, user=None, passwd=None):
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
        self.test = None
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
        # print(str(message.payload.decode("utf-8")))
        self.test = message.topic

        self.raw_data = message.payload.decode("utf-8")
        self.processed_data = json.loads(self.raw_data)
        # data = message.payload[1:-1].decode("utf-8").split(",")
        # self.processed_data_nested = np.array([[float(data[0])], [float(data[1])], [float(data[2])]])

    def connect(self):
        self.client.connect(self.host, port=self.port)  # connect to broker
        self.client.loop_start()  # start the loop

    def subs(self, topic):
        # local_counter = 0
        # ids = []
        # for topics in args:
        #     ids.append(local_counter)
        #     local_counter += 1
        # self.client.subscribe(list(zip(args, ids)))  # topic
        self.client.subscribe(topic)

    def publish(self, topc, msg):
        # print("published!")
        self.client.publish(topc, msg)


if __name__ == "__main__":
    # import keyboard
    # test = Mqtt_Manager('193.205.194.147', topic="topic", port=10883,
    #                     user='beksultan.tuleev@studenti.unitn.it')
    test = Mqtt_Manager("192.168.0.119", "test_top", 1883)
    count = 0
    try:
        while True:
            while count != 200:
                'data for model testing'
                # test.publish('allInOne', f'[{-79+np.random.random()+np.random.randint(-1,1)}, {5+np.random.randint(-3,15)+np.random.random()}]')
                # test.publish('allInOne', f'[[{-79+np.random.random()+np.random.randint(-1,1)}, {5+np.random.randint(-3,10)+np.random.random()}], [{-79+np.random.random()+np.random.randint(-1,1)}, {5+np.random.randint(-3,10)+np.random.random()}], [{-79+np.random.random()+np.random.randint(-1,1)}, {5+np.random.randint(-3,10)+np.random.random()}]]')
                time.sleep(0.1)
                'raw anchor data'
                num = 29 if count <100 else 31
                test.publish('topic/1', f'1"[4, {count}, {65553000 + np.random.randint(0, 400)}, -78.7,{4+np.random.randint(-3, 3)},{np.random.randint(30, 70)},{5+np.random.randint(-2, 2)},0.75]') #rssi, rx diff, std noise, pmr,snr
                test.publish('topic/2', f'2"[4, {count}, {65554200 + np.random.randint(0, 500)}, -78.7,{4+np.random.randint(-3, 3)},{np.random.randint(30, 70)},{5+np.random.randint(-2, 2)},0.75]') #rssi, rx diff, std noise, pmr,snr
                test.publish('topic/3', f'3"[4, {count}, {65553700 + np.random.randint(0, 200)}, -78.7,{4+np.random.randint(-3, 3)},{np.random.randint(30, 70)},{5+np.random.randint(-2, 2)},0.75]') #rssi, rx diff, s1td noise, pmr,snr
                test.publish('topic/4', f'4"[4, {count}, {65553700 + np.random.randint(0, 200)}, -85.7,{4+np.random.randint(10, 15)},{np.random.randint(20, 30)},{5+np.random.randint(-2, 2)},0.75]') #rssi, rx diff, s1td noise, pmr,snr
                # test.publish('topic/5', f'5"[4, {count}, {65549343+np.random.randint(-100,100)}, -80,11,50,{num},-1.2]') #rssi, rx diff, std noise, pmr,snr
                
                "data for position"
                # test.publish('positions', f'[[{np.random.randint(1,5)}, {np.random.randint(1,5)}, {np.random.randint(1,5)}]]')

                
                count += 1
            count = 0
    except KeyboardInterrupt:
        print("done")
