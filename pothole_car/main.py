import cv2
from flask import Flask, Response
from picamera2 import Picamera2

from detector import detect_pothole
from navigation import decide_action
from arduino_comm import send_command

app = Flask(__name__)

FRAME_WIDTH = 320
FRAME_HEIGHT = 240

# Picamera2 setup
picam2 = Picamera2()

config = picam2.create_preview_configuration(
    main={"size": (FRAME_WIDTH, FRAME_HEIGHT)}
)

picam2.configure(config)

picam2.start()

print("Camera started")


def generate_frames():

    while True:

        # Capture frame
        frame = picam2.capture_array()

        # Convert RGB to BGR
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

        # Detect pothole
        detected, x, y = detect_pothole(frame)

        # Navigation logic
        command = decide_action(detected, x, y)

        # Send to Arduino
        send_command(command)

        print("Command:", command)

        # Draw pothole center
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

        # Convert to jpg
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
