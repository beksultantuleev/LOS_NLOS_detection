from collections import deque, defaultdict

import matplotlib.animation as animation
from matplotlib import pyplot as plt

import threading

from random import randint

# from statistics import *
from Mqtt_manager import Mqtt_Manager

class DataPlot:
    def __init__(self, max_entries=300):
        self.axis_x = deque(maxlen=max_entries)
        self.axis_y = deque(maxlen=max_entries)
        self.axis_y2 = deque(maxlen=max_entries)

        self.max_entries = max_entries

        self.buf1 = deque(maxlen=5)
        self.buf2 = deque(maxlen=5)

    def add(self, x, data1, data2):

        self.axis_x.append(x)
        self.axis_y.append(data1)
        self.axis_y2.append(data2)


class RealtimePlot:
    def __init__(self, axes):

        self.axes = axes

        self.lineplot, = axes.plot([], [], "g")
        self.lineplot2, = axes.plot([], [], "r")

    def plot(self, dataPlot):
        self.lineplot.set_data(dataPlot.axis_x, dataPlot.axis_y)
        self.lineplot2.set_data(dataPlot.axis_x, dataPlot.axis_y2)

        self.axes.set_xlim(min(dataPlot.axis_x), max(dataPlot.axis_x))
        ymin = min([min(dataPlot.axis_y), min(dataPlot.axis_y2)])-1
        ymax = max([max(dataPlot.axis_y), max(dataPlot.axis_y2)])+1
        self.axes.set_ylim(ymin, ymax)
        self.axes.relim()





if __name__ == "__main__":

    mqtt_conn = Mqtt_Manager('localhost', "Position")
    fig, axes = plt.subplots()
    plt.title('Plotting Data')
    data = DataPlot()
    dataPlotting = RealtimePlot(axes)

    count = 0
    while True:
        if mqtt_conn.processed_data:
            data1 = mqtt_conn.processed_data[0]
            data2 = mqtt_conn.processed_data[2]

            
            count += 1
            data.add(count, data1, data2)
            dataPlotting.plot(data)

            plt.pause(0.001)
