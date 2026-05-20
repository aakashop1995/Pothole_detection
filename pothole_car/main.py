from flask import Flask, Response
import cv2
import time
import threading

from detector import detect_pothole
from navigation import decide_action
from arduino_comm import send_command

app = Flask(__name__)

# --------------------------------
# Camera setup
# --------------------------------
cap = cv2.VideoCapture(0, cv2.CAP_V4L2)

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

FRAME_WIDTH = 320
FRAME_HEIGHT = 240

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

        ret, frame = cap.read()

        if not ret or frame is None:

            print("Failed to read frame")
            continue

        frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))

        # -----------------------------
        # Pothole Detection
        # -----------------------------
        detected, x, y = detect_pothole(frame)

        # -----------------------------
        # Navigation Logic
        # -----------------------------
        command = decide_action(detected, x, y)

        # -----------------------------
        # Send command to Arduino
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

        # -----------------------------
        # Show command text
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

# Start capture thread
threading.Thread(
    target=capture_loop,
    daemon=True
).start()

# --------------------------------
# MJPEG stream generator
# --------------------------------
def generate():

    global latest_frame

    while True:

        with lock:

            frame = None if latest_frame is None else latest_frame.copy()

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
# Flask routes
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
