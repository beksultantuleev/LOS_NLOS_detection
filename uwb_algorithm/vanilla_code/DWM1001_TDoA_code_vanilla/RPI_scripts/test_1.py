#%% import and open

import serial
import numpy
import matplotlib.pyplot as plt
from parse import search

# ser = serial.Serial( '/dev/serial0', 115200, timeout=1 ) 


def serial_data_read (idx):
    hser = serial.Serial( '/dev/serial0', 115200, timeout=1 )
    print ("connected to: " + hser.portstr)

    for it in range(0,idx):
        yield hser.readline().decode("utf-8")

    hser.close()
    print ('closed serial port')

#%% collect some data

n_iter = 20 # number of iteration
r = []

for it in range(1,n_iter):
    r.append( search("rx {:d}: id {:d}: rng {:d}", ser.readline().decode("utf-8")) )


print ('close serial')
ser.close()             # close port

#%% plot it

rx = []
ry = []

#TODO cambia con try perchè ogni tanto becca un NONE !!

for line in serial_data_read (10):
    print(line)
    ry.append( search("rng {:d}",line )[0] )
    rx.append( search("rx {:d}",line )[0] )

fig, ax = plt.subplots() 
ax.scatter(rx,ry)
ax.set_title('range data')
ax.set_xlabel('meas #')
ax.set_ylabel('ticks')