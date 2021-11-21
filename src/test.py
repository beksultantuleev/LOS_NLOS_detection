from SerialPortReader import SerialPortReader

serialInit = SerialPortReader()
while True:
    data = serialInit.get_data(pattern="Data: ")
    print(data)