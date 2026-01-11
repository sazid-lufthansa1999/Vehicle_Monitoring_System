from ultralytics import YOLO
import cv2
import numpy as np
from collections import defaultdict

# Load your custom YOLOv8 model (using yolov8n for general vehicle detection)
model = YOLO("yolov8n.pt")

# Tracker history: tracker_id -> [last_positions]
track_history = defaultdict(lambda: [])

# Violation states: tracker_id -> type
active_violations = {}

# ------------------------------
# Helper: Check Wrong Way (Lane Aware)
# ------------------------------
def is_wrong_way(tracker_id, x, y, frame_w, frame_h):
    history = track_history[tracker_id]
    if len(history) < 10: return False
    
    start_y = history[0][1]
    curr_y = y
    divider = frame_w / 2
    min_move = frame_h * 0.05
    
    # Left Lane: Should go DOWN (Y increases)
    if x < divider:
        if (start_y - curr_y) > min_move: return True # Moving UP
    # Right Lane: Should go UP (Y decreases)
    else:
        if (curr_y - start_y) > min_move: return True # Moving DOWN
        
    return False

# ------------------------------
# Function: Main Detection Loop
# ------------------------------
def run_detection(source, is_live=False):
    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        print(f"❌ Cannot open source: {source}")
        return

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(cap.get(cv2.CAP_PROP_FPS)) or 30

    # Define a dummy Parking Zone for testing Crooked Parking (Center Square)
    parking_zone = np.array([[width*0.7, height*0.3], [width*0.9, height*0.3], 
                             [width*0.9, height*0.8], [width*0.7, height*0.8]], np.int32)

    while True:
        ret, frame = cap.read()
        if not ret: break

        # Use YOLOv8 tracking (ByteTrack)
        results = model.track(frame, persist=True, verbose=False, classes=[2, 3, 5, 7])[0]
        
        if results.boxes.id is not None:
            boxes = results.boxes.xywh.cpu().numpy()
            track_ids = results.boxes.id.int().cpu().numpy()
            
            for box, track_id in zip(boxes, track_ids):
                x, y, w, h = box
                track_history[track_id].append((x, y))
                if len(track_history[track_id]) > 30: track_history[track_id].pop(0)

                # 1. Check Wrong Way
                if is_wrong_way(track_id, x, y, width, height):
                    active_violations[track_id] = "WRONG WAY"

                # 2. Check Crooked Parking (If in Zone and 'stationary' - simple check)
                is_in_zone = cv2.pointPolygonTest(parking_zone, (float(x), float(y)), False) >= 0
                if is_in_zone and w > h: # Simple heuristic: if car horizontal in vertical spot
                    active_violations[track_id] = "CROOKED PARKING"

        # Visualization
        annotated_frame = results.plot()
        
        # Draw Parking Zone
        cv2.polylines(annotated_frame, [parking_zone], True, (0, 255, 0), 2)
        cv2.putText(annotated_frame, "PARKING ZONE", (int(width*0.7), int(height*0.28)), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        # Overlay Violations
        for tid, v_type in list(active_violations.items()):
            # Find current box for this ID to draw near it
            if results.boxes.id is not None and tid in results.boxes.id:
                idx = (results.boxes.id == tid).nonzero()[0][0]
                bx = results.boxes.xyxy[idx].cpu().numpy()
                cv2.putText(annotated_frame, f"⚠️ VIOLATION: {v_type}", (int(bx[0]), int(bx[1])-30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        cv2.imshow("Smart Detection - app2.py", annotated_frame)
        if cv2.waitKey(1) & 0xFF == ord('q'): break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    print("--- Traffic Violation Detector (Standalone) ---")
    print("Logic: Lane-Aware Wrong Way & Dynamic Parking Check")
    choice = input("1=Video File, 2=Webcam: ")
    if choice == "1":
        path = input("Video Path: ")
        run_detection(path)
    else:
        run_detection(0, is_live=True)
