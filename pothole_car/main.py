import cv2
from flask import Flask, Response

from detector import detect_pothole
from navigation import decide_action
from arduino_comm import send_command

app = Flask(__name__)

FRAME_WIDTH = 320
FRAME_HEIGHT = 240

# Camera setup
cap = cv2.VideoCapture(0, cv2.CAP_V4L2)

cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

if not cap.isOpened():

    print("Camera failed to open")

else:

    print("Camera started")


def generate_frames():

    while True:

        ret, frame = cap.read()

        if not ret:

            print("Failed to read frame")
            continue

        frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))

        # Detect pothole
        detected, x, y = detect_pothole(frame)

        # Navigation decision
        command = decide_action(detected, x, y)

        # Send command to Arduino
        send_command(command)

        print("Command:", command)

        # Draw pothole point
        if detected:

            cv2.circle(
                frame,
                (x, y),
                5,
                (0, 0, 255),
                -1
            )

        # Display command
        cv2.putText(
            frame,
            f"CMD: {command}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2
        )

        # Encode frame
        _, buffer = cv2.imencode('.jpg', frame)

        frame_bytes = buffer.tobytes()

        yield (
            b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n' +
            frame_bytes +
            b'\r\n'
        )


@app.route('/')

def index():

    return """
    <html>

        <head>
            <title>Pothole Detection Car</title>
        </head>

        <body>

            <h1>Pothole Detection Stream</h1>

            <img src="/video" width="640">

        </body>

    </html>
    """


@app.route('/video')

def video():

    return Response(
        generate_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )


if __name__ == "__main__":

    app.run(
        host='0.0.0.0',
        port=5000,
        threaded=True,
        debug=False,
        use_reloader=False
    )
