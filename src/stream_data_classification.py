from keras.models import load_model
from Data_collection import Listener
from time import sleep


model = load_model("trained_models/still_wave.h5")

listener = Listener()
listener = Listener()
listener.set_activity("deleteme")
listener.set_sample_size(40)
limiter = 0
while True:
    sleep(0.1)
    listener.accelerom_data_collection()
    listener.gyro_data_collection()


print("hello")