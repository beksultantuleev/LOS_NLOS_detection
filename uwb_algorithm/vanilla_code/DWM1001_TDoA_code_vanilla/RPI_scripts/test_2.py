import serial
import RPi.GPIO as GPIO
import json
import paho.mqtt.client as mqtt
from time import sleep

GPIO.setmode(GPIO.BOARD)
GPIO.setup(18, GPIO.OUT) #check the pin here !



mesg = { "dev_id" : 1, "seq" : 0, "tdoa" : 0 }

hser = serial.Serial( '/dev/serial0', 115200, timeout=1 )

def reset_dwm():
    GPIO.output(18, GPIO.LOW)
    sleep(1)
    GPIO.output(18, GPIO.HIGH)

with open("D:\\UWB\\anch_config.json") as json_file:
    data = json.load(json_file)
    print (data["anchor"])
    id_anch     = data["anchor"]["id"]
    pos         = data["anchor"]["position"]
    num_anchors = data["anchor"]["num-anch"]

topic = "test_localize/anchor_"+str(id_anch)
# topic = "test_localize/dev_01"

def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

    for it in range(0,idx):
        mesg["tdoa"] = hser.readline().decode("utf-8")
        mesg["seq"] = it
        client.publish(topic,  json.dumps(mesg), qos=1)
        print("published " + str(mesg))

    hser.close()
    print ('closed serial port')



hser.write(str(id_anch)+"\n")
print hser.readline().decode("utf-8")

hser.write("1010\n")
print hser.readline().decode("utf-8")


client = mqtt.Client()
client.on_connect = on_connect
client.connect("192.168.1.18", 1883, 60)
client.loop_forever()


