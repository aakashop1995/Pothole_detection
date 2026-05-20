import serial
import time

arduino = None

try:

    arduino = serial.Serial('/dev/ttyACM0', 9600)

    time.sleep(2)

    print("Arduino connected")

except:

    print("Arduino not connected")


def send_command(command):

    if arduino:

        arduino.write(command.encode())
