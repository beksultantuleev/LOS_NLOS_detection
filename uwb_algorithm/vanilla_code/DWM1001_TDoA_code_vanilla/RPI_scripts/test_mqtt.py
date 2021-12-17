import paho.mqtt.client as mqtt
import json
import random

# read configuration file for the anchor
with open("D:\\UWB\\anch_config.json") as json_file:
    data = json.load(json_file)
    print (data["anchor"])
    id_anch     = data["anchor"]["id"]
    pos         = data["anchor"]["position"]
    num_anchors = data["anchor"]["num-anch"]

topic = "test_localize/anchor_"+str(id_anch)
# topic = "test_localize/dev_01"

mesg = { "dev_id" : 1, "seq" : 0, "tdoa" : 0 }

def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    print(" publish in " + topic)
    for i in range(1,10):
        mesg["seq"] = i
        mesg["tdoa"] = random.random() * 100
        client.publish(topic,  json.dumps(mesg), qos=1)
        print("published " + str(mesg))


client = mqtt.Client()
client.on_connect = on_connect
client.connect("broker.hivemq.com", 1883, 60)
client.loop_forever()
