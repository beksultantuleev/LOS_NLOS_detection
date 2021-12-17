# RPI python scripts

This is just for testing the functionalities.

Tested on RPi with the following images:
- custom RTLS image from Decawave, need to disable something before...
- Raspbian buster 

con raspi-config va disabilitata la seriale di debug, e abilitato il controllo hw della seriale.
cosi la `serial0` è utilizzabile.
da installare librerie come rpi.gpio, mqtt paho, ecc