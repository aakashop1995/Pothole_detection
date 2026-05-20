from gps import get_gps_location
import time

print("Starting GPS test... (wait for fix)")

while True:

    lat, lon = get_gps_location()

    if lat is not None and lon is not None:
        print(f"GPS FIX → Lat: {lat}, Lon: {lon}")
    else:
        print("No GPS fix yet...")

    time.sleep(1)
