import random
from itertools import count
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from mpl_toolkits import mplot3d
import numpy as np
from scipy.spatial import distance
from Mqtt_manager import Mqtt_Manager
from scipy.spatial.distance import cdist
import time

"this is final version 3.0, works with MQTT direct data access"


class Plot_manager:
    def __init__(self, topic, host="localhost"):
        self.topic = topic
        self.host = host
        self.mqtt = Mqtt_Manager("localhost", self.topic)
        plt.style.use('ggplot')  # fivethirtyeight ggplot

    def animate(self, i):
        if len(self.mqtt.processed_data) > 0:
            ax = plt.gca()
            ax.cla()
            plt.title("Real-time map")

            # print(self.mqtt.processed_data[0])

            if self.mqtt.processed_data[0]>0:
                plt.text(0.5, 0.5, "LOS", size=50,
                        ha="center", va="center",
                        bbox=dict(boxstyle="round",
                                ec=(0, 1, 0),
                                fc=(0, 1, 0)
                                )
                        )
            else:
                plt.text(0.5, 0.5, "NLOS", size=50,
                     ha="center", va="center",
                     bbox=dict(boxstyle="round",
                               ec=(1., 0, 0),
                               fc=(1., 0, 0)
                               )
                     )


            # plt.grid()
            # plt.xlabel("X")
            # plt.ylabel("Y")
            # plt.legend(loc='upper left')
            plt.tight_layout()

    # def add_anchors(self, anchor_list):
    #     if any(isinstance(i, list) for i in anchor_list):
    #         for anchor in anchor_list:
    #             plt.scatter(anchor[0], anchor[1], color="red", s=150)
    #             plt.text(anchor[0], anchor[1], anchor[2], color="blue")
    #     else:
    #         pass
            # plt.scatter(anchor_list[0], anchor_list[1], color="red", s=150)
            # plt.text(anchor_list[0], anchor_list[1], anchor_list[2], color = "blue")

    def run(self):
        ani = FuncAnimation(plt.gcf(), self.animate, interval=200)
        plt.tight_layout()
        plt.show()


if __name__ == "__main__":


    topic = "LOS"



    test = Plot_manager(topic=topic, host="localhost")  # positions position
    test.run()
