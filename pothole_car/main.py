import cv2
from flask import Flask, Response

from detector import detect_pothole
from navigation import decide_action
from arduino_comm import send_command

app = Flask(__name__)

FRAME_WIDTH = 320
FRAME_HEIGHT = 240

cap = cv2.VideoCapture(0)

def generate_frames():

    while True:

        ret, frame = cap.read()

        if not ret:
            break

        frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))

        # Detect pothole
        detected, x, y = detect_pothole(frame)

        # Navigation decision
        command = decide_action(detected, x, y)

        # Send to Arduino
        send_command(command)

        print("Command:", command)

        # Draw pothole center
        if detected:
            cv2.circle(frame, (x, y), 5, (0, 0, 255), -1)

        # Show command on frame
        cv2.putText(
            frame,
            f"CMD: {command}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2
        )

        # Convert frame to jpg
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
            <img src="/video">
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

    app.run(host='0.0.0.0', port=5000)
