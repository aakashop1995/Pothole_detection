from flask import Flask, Response
import cv2
import time
import threading
from gps import get_gps_location
from picamera2 import Picamera2

from detector import detect_pothole
from navigation import decide_action
from arduino_comm import send_command

app = Flask(__name__)

FRAME_WIDTH = 320
FRAME_HEIGHT = 240

# --------------------------------
# Picamera2 setup
# --------------------------------
picam2 = Picamera2()

config = picam2.create_preview_configuration(
    main={"size": (FRAME_WIDTH, FRAME_HEIGHT)}
)

picam2.configure(config)

picam2.start()

print("Camera started")

# --------------------------------
# Shared frame
# --------------------------------
latest_frame = None

lock = threading.Lock()

# --------------------------------
# Camera capture thread
# --------------------------------
def capture_loop():

    global latest_frame

    while True:

        try:

            # Capture frame
            frame = picam2.capture_array()

            # Convert RGB -> BGR
            frame = cv2.cvtColor(
                frame,
                cv2.COLOR_RGB2BGR
            )

            # Resize
            frame = cv2.resize(
                frame,
                (FRAME_WIDTH, FRAME_HEIGHT)
            )

            # -----------------------------
            # Pothole Detection
            # -----------------------------
            detected, x, y = detect_pothole(frame)

            # -----------------------------
            # Navigation Logic
            # -----------------------------
            command = decide_action(
                detected,
                x,
                y
            )

            # -----------------------------
            # Send to Arduino
            # -----------------------------
            send_command(command)

            print("Command:", command)

            # -----------------------------
            # Draw pothole center
            # -----------------------------
            if detected:

                cv2.circle(
                    frame,
                    (x, y),
                    5,
                    (0, 0, 255),
                    -1
                )
                print("Pothole detected")

                # get GPS only when needed
                lat, lon = get_gps_location()

                print("GPS:", lat, lon)

            # -----------------------------
            # Display command
            # -----------------------------
            cv2.putText(
                frame,
                f"CMD: {command}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 0),
                2
            )

            with lock:

                latest_frame = frame

            time.sleep(0.01)

        except Exception as e:

            print("Camera Error:", e)

# Start capture thread
threading.Thread(
    target=capture_loop,
    daemon=True
).start()

# --------------------------------
# MJPEG Stream Generator
# --------------------------------
def generate():

    global latest_frame

    while True:

        with lock:

            frame = (
                None
                if latest_frame is None
                else latest_frame.copy()
            )

        if frame is None:

            continue

        success, buffer = cv2.imencode(
            '.jpg',
            frame,
            [int(cv2.IMWRITE_JPEG_QUALITY), 80]
        )

        if not success:

            continue

        yield (
            b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n' +
            buffer.tobytes() +
            b'\r\n'
        )

        time.sleep(0.03)

# --------------------------------
# Flask Routes
# --------------------------------
@app.route('/')

def home():

    return """
    <html>

        <body>

            <h2>Pothole Detection Car</h2>

            <img src="/video" width="640"/>

        </body>

    </html>
    """

@app.route('/video')

def video():

    return Response(
        generate(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

# --------------------------------
# Run Flask
# --------------------------------
if __name__ == '__main__':

    app.run(
        host='0.0.0.0',
        port=5000,
        threaded=True,
        debug=False,
        use_reloader=False
    )
