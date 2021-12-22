import paho.mqtt.client as mqtt
import numpy as np
from Managers.Mqtt_manager import Mqtt_Manager
import json
import re
import collections
import time
# mqtt_inst = Mqtt_Manager("192.168.0.119", topic=[("topic/#", 0)])

# while True:
#     print(mqtt_inst.test)

def deque_manager(size, data):
    'updated deque manager, new values at the end of deque'
    size = size+1
    deque_test = collections.deque([])
    while len(deque_test) < size:
        deque_test.append(data)
        if len(deque_test) == size:
            # deque_test.pop()
            deque_test.popleft()
            return np.array(deque_test)


broker_address="192.168.0.119" 
#broker_address="iot.eclipse.org"
print("creating new instance")
client = mqtt.Client('P1') #create new instance
print("connecting to broker")
client.connect(broker_address) #connect to broker



# client.subscribe([("topic/1", 0), ("topic/2", 0)])
client.subscribe([("topic/#", 0)])


def on_message(client, userdata, message): 
    msg = f'{message.payload.decode("utf")}'
    pattern = re.compile(r'\[.+')
    matches = pattern.finditer(msg) 
    for match in matches:
        res = json.loads(match.group(0))
        if message.topic == "topic/1":
            anch1 = res
        if message.topic == "topic/2":
            anch2 = res


  
    

client.on_message=on_message        #attach function to callback

# client.loop_forever()
while True:
    client.loop_start()    #start the loop
