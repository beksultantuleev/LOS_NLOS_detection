from anytree import Node, RenderTree
from anytree.exporter import DotExporter
import matplotlib.pyplot as plt
from sklearn import tree

# Position_est_alg = Node("Postion estimating\n algorithms") #root
# range_based = Node("Range-based\n algorithms", Position_est_alg) #root
# range_free = Node("Range-free\n algorithms", Position_est_alg) #root
# proximity_based = Node("Proximity-based\n algorithms", range_free) #root
# toa_ = Node("ToA", range_based)
# tdoa_ = Node("TDoA", range_based)
# aoa_ = Node("AoA", range_based)
# rssi = Node("RSSI", range_based)

# DotExporter(Position_est_alg).to_picture("src/Data_analysis/plot_data/Position_est_alg.png")


Indoor_Positioning = Node("Indoor Positioning\n algorithms") #root
fingerprinting = Node("Fingerprinting", Indoor_Positioning)
proximity = Node("Proximity", Indoor_Positioning)
trilat = Node("Trilateration", Indoor_Positioning)
triang = Node("Triangulation", Indoor_Positioning)
toa = Node("ToA", trilat)
tdoa = Node("TDoA", trilat)
aoa = Node("AoA", triang)
rss = Node("RSSI", fingerprinting)
rss = Node("RSSI", proximity)
rss = Node("RSSI", trilat)

for pre, fill, node in RenderTree(Indoor_Positioning):
    print("%s%s" % (pre, node.name))
DotExporter(Indoor_Positioning).to_picture("src/Data_analysis/plot_data/Indoor_Positioning.png")


# IPS = Node("Indoor Positioning\nSystems") #root
# optical_systems = Node("Optical\nsystems", parent=IPS)
# RF = Node("Radio\nfrequency", parent=IPS)
# IR = Node("Infrared", parent=IPS)
# Ultrasound = Node("Ultrasound", parent=IPS)
# UWB = Node("UWB", parent=RF)
# FM = Node("FM", parent=RF)
# Hybrid = Node("Hybrid", parent=RF)
# wlan = Node("WLAN", parent=RF)
# RFID = Node("RFID", parent=RF)
# Bluetooth = Node("Bluetooth", parent=RF)

# # m_1 = Node("M_1", parent=gm_2)

# for pre, fill, node in RenderTree(IPS):
#     print("%s%s" % (pre, node.name))

# DotExporter(IPS).to_picture("src/Data_analysis/plot_data/IPS.png")

# Positioning = Node("Positioning") #root
# self_pos = Node("Self Positioning", parent=Positioning)
# aid_pos = Node("Aided Positioning", parent=Positioning)
# outdoor_pos = Node("Outdoor Positioning", parent=aid_pos)
# outdoor_pos = Node("Indoor Positioning", parent=aid_pos)
# DotExporter(Positioning).to_picture("src/Data_analysis/plot_data/Positioning.png")
