from anytree import Node, RenderTree
from anytree.exporter import DotExporter
import matplotlib.pyplot as plt
from sklearn import tree


Mqtt_broker = Node("MQTT\nbroker") #root
raspberry_pi = Node("Raspberry\nPi", Mqtt_broker)
capable_pc = Node("Personal \ncomputer", Mqtt_broker)

dwm1000_dev_board = Node("DWM1001\n Anchor", raspberry_pi)
nlos_detection_mitigation = Node("NLOS \ndetection &\nmitigation \nalgorithm", capable_pc)
tag = Node("DWM1001\nTag", dwm1000_dev_board)
position_estimation = Node("Position \nestimation", nlos_detection_mitigation)


# for pre, fill, node in RenderTree(Mqtt_broker):
#     print("%s%s" % (pre, node.name))
# DotExporter(Mqtt_broker).to_picture("src/Data_analysis/plot_data/infrastructure_tree_vanilla.png")


DotExporter(Mqtt_broker, edgeattrfunc = lambda node, child: "dir=both").to_picture('src/Data_analysis/plot_data/infrastructure_tree_both.png')
for line in DotExporter(Mqtt_broker, edgeattrfunc = lambda node, child: "dir=both"):
    print(line)