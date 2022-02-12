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
    def __init__(self, topic, anchor_list=[], room_size=[0, 0, 6, 6], host="localhost"):
        self.room_size = room_size
        self.anchor_list = anchor_list
        self.topic = topic
        self.host = host
        self.mqtt = Mqtt_Manager("localhost", self.topic)
        plt.style.use('fivethirtyeight') #fivethirtyeight ggplot

    def animate(self, i):
        if len(self.mqtt.processed_data) > 0:
            tag = 1
            ax = plt.gca()
            ax.cla()
            plt.title("Real-time map")
            for positions in self.mqtt.processed_data:
                ax.plot(positions[0], positions[1],
                        label='movement', linestyle="--", alpha=0.5)
                ax.plot((positions[0]), (positions[1]), 'o', color='g' if tag ==1 else "r")
                plt.text(positions[0], positions[1], f"filtered {tag}" if tag == 1 else f"original {tag}")
                circle = plt.Circle(
                    (positions[0], positions[1]), 0.5, color='b', fill=False)
                ax.add_patch(circle)
                # print(distances_list)
                tag += 1


            # on y axis (horizontal)
            plt.axhline(self.room_size[0], color="#01BFDA")
            plt.axhline(self.room_size[2], color="#01BFDA")
            # on x axis (vertical)
            plt.axvline(self.room_size[1], color="#01BFDA")
            plt.axvline(self.room_size[3], color="#01BFDA")
            # plt.axhspan(0, 6, alpha=0.2) #does not work with lists
            # plt.axvspan(self.room_size[2], self.room_size[3], alpha=0.2) #does not work with lists
            self.add_anchors(self.anchor_list)

            # plt.grid()
            plt.xlabel("X")
            plt.ylabel("Y")
            # plt.legend(loc='upper left')
            plt.tight_layout()

    def add_anchors(self, anchor_list):
        if any(isinstance(i, list) for i in anchor_list):
            for anchor in anchor_list:
                plt.scatter(anchor[0], anchor[1], color="red", s=150)
                plt.text(anchor[0], anchor[1], anchor[2], color="blue")
        else:
            pass
            # plt.scatter(anchor_list[0], anchor_list[1], color="red", s=150)
            # plt.text(anchor_list[0], anchor_list[1], anchor_list[2], color = "blue")

    def run(self):
        ani = FuncAnimation(plt.gcf(), self.animate, interval=200)
        plt.tight_layout()
        plt.show()


if __name__ == "__main__":

    topic = "positions"
    anchors = [[2, 2, "1 Black"], [0, 0, "2 Red"],
                [5, 0, "3 Blue"]]

    room_size = [-3, 0, 2, 5]  # x1, y1, x2, y2 # positions -  [0, 0, 7, 10], position [0, 0, 4, 4]
    
    test = Plot_manager(topic=topic, room_size=room_size, anchor_list=anchors, host="192.168.0.119") #positions position
    test.run()