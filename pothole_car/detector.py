from ultralytics import YOLO

model = YOLO("model/best.pt")

FRAME_HEIGHT = 240

def detect_pothole(frame):

    results = model(frame)

    for result in results:

        boxes = result.boxes

        for box in boxes:

            x1, y1, x2, y2 = box.xyxy[0]

            x1 = int(x1)
            y1 = int(y1)
            x2 = int(x2)
            y2 = int(y2)

            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2

            # Only near potholes
            if center_y > FRAME_HEIGHT // 2:

                return True, center_x, center_y

    return False, 0, 0
