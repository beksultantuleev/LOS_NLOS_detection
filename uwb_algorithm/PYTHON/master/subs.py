import paho.mqtt.client as mqtt
import re
import paho.mqtt.client as mqttClient
import time


def on_connect(client, userdata, flags, rc):
 
    if rc == 0:
        print("Connected to broker")
 
        global Connected       #Use global variable
        Connected = True       #Signal connection 
 
    else:
        print("Connection failed")
 
 
def on_message(client, userdata, message):

    # characters = [chr(ascii) for ascii in message.payload] # Convert ASCII to char
    # chars_joined = ''.join(characters) # Join chars to a string
    # received_message = chars_joined.split(",")     # Split string by comma
    # print(received_message)
    received_message = message.payload.decode("utf-8")
    # print(received_message[0])
    client.publish("tags/" + received_message[2], str(received_message[0] + " " + received_message[2] +  received_message[3:]), qos=0)
    print(received_message)
    

Connected = False   #global variable for the state of the connection

 
broker_address= "192.168.0.119"                      	#Broker address
port_id = 1883                                     	#Broker port
 
client = mqtt.Client()                             	#create new instance
client.on_connect = on_connect                     	#attach function to callback
client.on_message = on_message                     	#attach function to callback
 
client.connect(broker_address, port = port_id)     	#connect to broker


#start the loop
client.loop_start()       
      
 
while Connected != True:         
    time.sleep(0.1)
    
 
anch_m = client.subscribe("topic/master")
anch_1 = client.subscribe("topic/1")
anch_2 = client.subscribe("topic/2")
# anch_3 = client.subscribe("topic/3")
# anch_4 = client.subscribe("topic/4")
# anch_5 = client.subscribe("topic/5")


try:
    while True:
        time.sleep(1)
 
except KeyboardInterrupt:
    print ("exiting")
    client.disconnect()
    client.loop_stop()
