from anytree import Node, RenderTree
from anytree.exporter import DotExporter
import matplotlib.pyplot as plt
from sklearn import tree

IPS = Node("IPS") #root
optical_systems = Node("Optical systems", parent=IPS)
RF = Node("Radio frequency", parent=IPS)
IR = Node("Infrared", parent=IPS)
Ultrasound = Node("Ultrasound", parent=IPS)
Optical = Node("Optical", parent=IPS)
UWB = Node("UWB", parent=RF)
FM = Node("FM", parent=RF)
Hybrid = Node("Hybrid", parent=RF)
wlan = Node("WLAN", parent=RF)
RFID = Node("RFID", parent=RF)
Bluetooth = Node("Bluetooth", parent=RF)

# m_1 = Node("M_1", parent=gm_2)

for pre, fill, node in RenderTree(IPS):
    print("%s%s" % (pre, node.name))

DotExporter(IPS).to_picture("src/Data_analysis/plot_data/IPS.png")

Positioning = Node("Positioning") #root
self_pos = Node("Self Positioning", parent=Positioning)
aid_pos = Node("Aided Positioning", parent=Positioning)
outdoor_pos = Node("Outdoor Positioning", parent=aid_pos)
outdoor_pos = Node("Indoor Positioning", parent=aid_pos)
DotExporter(Positioning).to_picture("src/Data_analysis/plot_data/Positioning.png")
