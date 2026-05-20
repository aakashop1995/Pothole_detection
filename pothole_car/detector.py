import cv2
import numpy as np
import onnxruntime as ort

FRAME_WIDTH = 320
FRAME_HEIGHT = 240

MODEL_SIZE = 320

# --------------------------------
# Load ONNX model
# --------------------------------
session = ort.InferenceSession(
    "/home/jayesh/Pothole_detection/model/best.onnx"
)

input_name = session.get_inputs()[0].name

# --------------------------------
# Detect pothole
# --------------------------------
def detect_pothole(frame):

    # Resize frame for model
    img = cv2.resize(
        frame,
        (MODEL_SIZE, MODEL_SIZE)
    )

    # Convert BGR -> RGB
    img = cv2.cvtColor(
        img,
        cv2.COLOR_BGR2RGB
    )

    # Normalize
    img = img.astype(np.float32) / 255.0

    # HWC -> CHW
    img = np.transpose(img, (2, 0, 1))

    # Add batch dimension
    img = np.expand_dims(img, axis=0)

    # Run ONNX inference
    outputs = session.run(
        None,
        {input_name: img}
    )

    predictions = outputs[0][0]

    # Loop detections
    for detection in predictions:

        confidence = detection[4]

        # Confidence threshold
        if confidence > 0.5:

            x_center = detection[0]
            y_center = detection[1]
            width = detection[2]
            height = detection[3]

            # Convert coordinates
            x1 = int(
                (x_center - width / 2)
                * FRAME_WIDTH
                / MODEL_SIZE
            )

            y1 = int(
                (y_center - height / 2)
                * FRAME_HEIGHT
                / MODEL_SIZE
            )

            x2 = int(
                (x_center + width / 2)
                * FRAME_WIDTH
                / MODEL_SIZE
            )

            y2 = int(
                (y_center + height / 2)
                * FRAME_HEIGHT
                / MODEL_SIZE
            )

            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2

            # Only near potholes
            if center_y > FRAME_HEIGHT // 2:

                return True, center_x, center_y

    return False, 0, 0
