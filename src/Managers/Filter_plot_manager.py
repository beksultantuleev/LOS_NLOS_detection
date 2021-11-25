from collections import deque
from matplotlib import pyplot as plt

from Mqtt_manager import Mqtt_Manager


class DataPlot:
    def __init__(self, max_entries=50):
        self.axis_x = deque(maxlen=max_entries)
        self.axis_y = deque(maxlen=max_entries)
        self.axis_y2 = deque(maxlen=max_entries)
        self.max_entries = max_entries

        # self.buf1 = deque(maxlen=5)
        # self.buf2 = deque(maxlen=5)

    def add(self, x, data1, data2):
        self.axis_x.append(x)
        self.axis_y.append(data1)
        self.axis_y2.append(data2)


class RealtimePlot:
    def __init__(self, axes):

        self.axes = axes

        self.lineplot, = axes.plot([], [], "r")
        self.lineplot2, = axes.plot([], [], "g")

    def plot(self, dataPlot):
        self.lineplot.set_data(dataPlot.axis_x, dataPlot.axis_y)
        self.lineplot2.set_data(dataPlot.axis_x, dataPlot.axis_y2)

        self.axes.set_xlim(min(dataPlot.axis_x), max(dataPlot.axis_x))
        ymin = min([min(dataPlot.axis_y), min(dataPlot.axis_y2)])-1
        ymax = max([max(dataPlot.axis_y), max(dataPlot.axis_y2)])+1
        self.axes.set_ylim(ymin, ymax)
        self.axes.relim()


if __name__ == "__main__":

    mqtt_conn = Mqtt_Manager('localhost', "Position")  # "Compare"
    fig, axes = plt.subplots()
    plt.title('Plotting Data')
    data = DataPlot(max_entries=50)
    dataPlotting = RealtimePlot(axes)

    count = 0
    while True:

        if mqtt_conn.processed_data:
            original = mqtt_conn.processed_data[0]
            filtered = mqtt_conn.processed_data[1]

            count += 1
            data.add(count, original, filtered)
            dataPlotting.plot(data)
            plt.pause(0.001)
