import serial
import time

arduino = serial.Serial('/dev/ttyUSB0', 9600)

time.sleep(2)

def send_command(command):

    arduino.write(command.encode())
