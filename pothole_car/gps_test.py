import serial
import time

PORT = "/dev/ttyS0"   # CHANGE THIS if needed

try:
    gps = serial.Serial(PORT, baudrate=9600, timeout=1)
    time.sleep(2)
    print("GPS connected on", PORT)

except Exception as e:
    gps = None
    print("GPS not connected:", e)


def get_gps_location():

    if gps is None:
        return None, None

    while True:

        try:
            line = gps.readline().decode('utf-8', errors='ignore')

            if line.startswith("$GPGGA"):

                parts = line.split(",")

                if parts[2] and parts[4]:

                    lat = float(parts[2][:2]) + float(parts[2][2:]) / 60
                    lon = float(parts[4][:2]) + float(parts[4][2:]) / 60

                    if parts[3] == "S":
                        lat = -lat
                    if parts[5] == "W":
                        lon = -lon

                    return lat, lon

        except:
            continue
