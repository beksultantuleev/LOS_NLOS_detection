import serial
#import RPi.GPIO as GPIO
import json
import paho.mqtt.client as mqtt
import time
from time import sleep
import math
import os


# GPIO.setmode(GPIO.BCM)
# GPIO.setup(18, GPIO.OUT) #check the pin here !

# SET OUTPUT MESSAGE
mesg = {}


class ReadLine:
    def __init__(self, s):
        self.buf = bytearray()
        self.s = s

    def readline(self):
        i = self.buf.find(b"\n")
        if i >= 0:
            r = self.buf[:i+1]
            self.buf = self.buf[i+1:]
            return r
        while True:
            i = max(1, min(2048, self.s.in_waiting))
            data = self.s.read(i)
            i = data.find(b"\n")
            if i >= 0:
                r = self.buf + data[:i+1]
                self.buf[0:] = data[i+1:]
                return r
            else:
                self.buf.extend(data)

hser = serial.Serial('/dev/ttyACM0', 115200, timeout=None)  # '/dev/ttyACM0'
rl = ReadLine(hser)

# apre file e ricavo i dati e li printo
# with open("D:\\UWB\\anch_config.json") as json_file:
with open("uwb_algorithm/PYTHON/anch_config.json") as json_file:  # "uwb_algorithm/PYTHON/anch_config.json"
    data = json.load(json_file)
    print(data)
    id_anch = data["id"]
    pos = data["position"]
    num_anchors = data["num_anch"]
    broker_addr = data["broker"]
    Anch_M = data["Anch_M"]

# VAriable DEF:
# Anch_M = [2.93, 11.05, 6.68]
tof = int(math.sqrt((pos[0] - Anch_M[0]) ** 2 + (pos[1] - Anch_M[1])
          ** 2 + (pos[2] - Anch_M[2]) ** 2) / 299702547 / 15.65e-12)
#it = 0
print(f'tof is {tof}')
#topic = "test_localize/anchor_"+str(id_anch)
topic = "topic/"+str(id_anch)
# topic = "test_localize/dev_01"


def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

    # read DW_INIT ok
    init = hser.readline().decode("utf")

    client.publish(topic, str("anch ") + str(id_anch) +
                   str(": ") + init, qos=0)
    print("published " + str(init))

    # read TWR_corr
    corr = hser.readline().decode("utf")
    client.publish(topic, str("anch ") + str(id_anch) +
                   str(": ") + corr, qos=0)
    print("twr_corr " + str(corr))

    # read SYNC
    sync = hser.readline().decode("utf")
    client.publish(topic, str("anch ") + str(id_anch) +
                   str(": ") + sync, qos=0)
    print("sync factor " + str(sync))

    global Connected  # Use global variable
    Connected = True


print(f"id of anchor is {id_anch}")
# hser.write(str(id_anch)+"\n")
hser.write(str.encode(f"{id_anch}\n"))
print(hser.readline().decode("utf"))

# hser.write(str(tof)+"\n")
hser.write(str.encode(f"{tof}\n"))
print(hser.readline().decode("utf"))

Connected = False
client = mqtt.Client()
client.on_connect = on_connect
client.connect(broker_addr, 1883, 60)
client.loop_start()
while Connected != True:  # Wait for connection
    time.sleep(0.1)

try:
    while True:
        mesg = rl.readline().decode("utf")
        # print(mesg)
        try:
            processed_msg = f"{id_anch}{json.dumps(mesg)[:-5]}"
            # print(processed_msg)
            #if len(mesg.split()) < 7:
            client.publish(topic, processed_msg, qos=0)
            #     client.publish(topic, str(id_anch) + json.dumps(mesg)[:-5], qos=0)

                # print("published " + str("anch ") +
                #         str(id_anch) + str(": ") + str(mesg))
            print(f"published {id_anch} {mesg}")
        except:
            print(f"corrupted msg")

except KeyboardInterrupt:
    hser.close()
    print('closed serial port')
    client.disconnect()
    client.loop_stop()
