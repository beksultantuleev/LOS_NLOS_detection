import paho.mqtt.client as mqtt
import re
import numpy as np
import numpy.matlib
import array as arr
import json
import paho.mqtt.client as mqttClient
import time
import collections
# from influxdb import InfluxDBClient
import atexit

Connected = False   #global variable for the state of the connection
DEBUG = False
num_anch = 7
num_tag = 10
buffer_size = 100

slot = np.zeros((num_tag, buffer_size, num_anch), dtype=int)           #creo 100 slot toa

tmp = [] 

DBdata = {}
DBdata['measurement'] = 'TOA_Ranging'
DBdata['tags'] = {}
DBdata['tags'] = {'room' : 'lab', 'anchors' : 0}
DBdata['fields'] = {}
DBdata['tags']['anchors'] = 6
dist = {'A1' : 0, 'A2' : 0, 'A3' : 0, 'A4' : 0, 'A5' : 0, 'A6' : 0}
dict_keys = list(dist.keys())

broker_address= "192.168.0.119"                      #Broker address
port_id = 1883                                     #Broker port
subscriptions_qos  = [("tags/#", 0)]



def on_connect(client, userdata, flags, rc):

  print("Successfully connected to MQTT with result code %s" % str(rc))
  #print("before message_callback_add 1")
  
  client.message_callback_add("tags/#", ToA_callback)
  #print("after message_callback_add")

  (result, _) = client.subscribe(subscriptions_qos)
  
  if (result == mqtt.MQTT_ERR_SUCCESS):
      print("Successfully subscribed to MQTT topics with result code %s" % str(result))



# def db_connect():
#   global clientDB
#   clientDB = InfluxDBClient('localhost', 8086, 'u_uwb', 'de12mO=7C5fTb', 'CAINELLI_TEST1')
#   print("Connected to InfluxDB v" + clientDB.ping())



def on_message(client, userdata, message):
    print("Received: Topic: %s Body: %s", message.topic, message.payload)



# def db_insert(data):
#   #print('inserting ' + data)
#   clientDB.write_points([data])



def ToA_callback(client, userdata, message):

  try:
    
    data = message.payload.split()
  
    if (RepresentsInt(data[2])):
      anch_id = int(data[0])
      tag_id = int(data[1])
      num_msg = int(data[2])
      toa = int(data[3])

      if DEBUG:
        print(str(message.payload.split()))
        print("num_msg: ", num_msg)
        print("anch_id ", anch_id)
        print("tag_id",tag_id)
        print("toa ", toa)

      slot[tag_id, num_msg % 100,anch_id] = toa
      
      for i in range(1,5,1):
        index = np.nonzero(np.all(np.array(slot[i,:,1:7]) != 0, axis=1))[0]
        # print(slot[i,:,1:7])
        # print(np.nonzero(np.all(slot[i,:,1:7] != 0, axis=0))[0])
        
        if index.size > 0:
          slot[i, index, 0] = num_msg
          client.publish('TOA' + str(i) , str(slot[i, index, 1:7]), qos = 0)

          for h in range(1,len(dist),1):
            dist[dict_keys[h-1]] = int(slot[i, index, h])

          DBdata['fields'] = dist
          DBdata['fields']['tagID'] = tag_id

          if DEBUG:
            print('Insert DataBase Data:')
            print(DBdata)
          
          # db_insert(DBdata)
          ts = [DBdata['fields']['A1'], DBdata['fields']['A2'], DBdata['fields']['A3'],
                      DBdata['fields']['A4'], DBdata['fields']['A5'], DBdata['fields']['A6']]
                      
          # Localisation(client,ts,i)
          
          DBdata ['fields'] = {}
          slot[i, index, :] = [0] * (num_anch)
          index = []
          
          # print('Done')
  except:
    raise
# def Localisation(client,data,i):

    M = 6
    c = 299792458

    A_n1 = np.array([[0.00], [7.19], [2.15]])
    A_n2 = np.array([[0.00], [3.62], [3.15]])
    A_n3 = np.array([[0.00], [0.00], [2.15]])
    A_n4 = np.array([[4.79], [1.85], [3.15]])
    A_n5 = np.array([[4.79], [5.45], [2.15]])
    A_n6 = np.array([[3.00], [9.35], [3.15]])
    A_n = np.array([A_n3, A_n1, A_n2, A_n4, A_n5, A_n6])
    n = len(A_n)

    t1 = float(data[0]) * float(15.65e-12)
    t2 = float(data[1]) * float(15.65e-12)
    t3 = float(data[2]) * float(15.65e-12)
    t4 = float(data[3]) * float(15.65e-12)
    t5 = float(data[4]) * float(15.65e-12)
    t6 = float(data[5]) * float(15.65e-12)

    # tolgo dall'inizio ancora riferimento e lascio il valore fuori (tm)
    toa = np.array([[t3, t1, t2, t4, t5, t6]])
    tdoa = toa - toa[0][0]
    tdoa = tdoa[0][1:]
    D = tdoa*c  # D is 5x1


    D = D.reshape(5, 1)
    A_diff_one = np.array((A_n3[0][0]-A_n[1:, 0]), dtype='float')
    A_diff_two = np.array((A_n3[1][0]-A_n[1:, 1]), dtype='float')
    A_diff_three = np.array((A_n3[2][0]-A_n[1:, 2]), dtype='float')

    A = 2 * np.array([A_diff_one, A_diff_two, A_diff_three, D]).T

    b = D**2 + np.linalg.norm(A_n3)**2 - np.sum(A_n[1:, :]**2, 1)
    x_t0 = np.dot(np.linalg.pinv(A), b)  # .reshape(4,1)

    x_t_0 = np.array([x_t0[0][0], x_t0[0][1], x_t0[0][2]])


    # loop
    f = np.zeros((n-1, 1))
    del_f = np.zeros((n-1, 3))
    A_n = A_n.T
    for ii in range(1, n):

        f[ii-1] = np.linalg.norm(x_t_0-A_n[0, :, ii].reshape(3, 1)) - \
        np.linalg.norm(x_t_0-A_n[0, :, 0].reshape(3, 1))

        del_f[ii-1, 0] = np.dot((x_t_0[0]-A_n[0, 0, ii]), np.reciprocal(np.linalg.norm(x_t_0-A_n[0, :, ii].reshape(3, 1)))) - np.dot((x_t_0[0]-A_n[0, 0, 0]), np.reciprocal(np.linalg.norm(x_t_0-A_n[0, :, 0].reshape(3, 1))))
        del_f[ii-1, 1] = np.dot((x_t_0[1]-A_n[0, 1, ii]), np.reciprocal(np.linalg.norm(x_t_0-A_n[0, :, ii].reshape(3, 1)))) - np.dot((x_t_0[1]-A_n[0, 1, 0]), np.reciprocal(np.linalg.norm(x_t_0-A_n[0, :, 0].reshape(3, 1))))
        del_f[ii-1, 2] = np.dot((x_t_0[2]-A_n[0, 2, ii]), np.reciprocal(np.linalg.norm(x_t_0-A_n[0, :, ii].reshape(3, 1)))) - np.dot((x_t_0[2]-A_n[0, 2, 0]), np.reciprocal(np.linalg.norm(x_t_0-A_n[0, :, 0].reshape(3, 1))))
    x_t = np.dot(np.linalg.pinv(del_f), (D-f)) + x_t_0
    # print("position is %s %s %s and tag is %s" % ( x_t[0], x_t[1], x_t[2], i))
    client.publish('Position' + str(i), str(x_t), qos=0)



def RepresentsInt(s):
    try: 
        int(s)
        return True
    except ValueError:
        return False



def main():
    # logger = logging.getLogger('root')
    # logging.basicConfig(format='[%(asctime)s %(levelname)s: %(funcName)20s] %(message)s', level=logging.DEBUG)

    client = mqtt.Client()
    client.max_inflight_messages_set(20000)
    # client.on_log = on_log
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(broker_address, port_id)
    # db_connect()
    client.loop_forever()



if __name__ == '__main__':
    main()
