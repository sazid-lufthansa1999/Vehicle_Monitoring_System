from ultralytics import YOLO
import cv2
import numpy as np
from collections import defaultdict

# Load your custom YOLOv8 model (using yolov8n for general vehicle detection)
model = YOLO("best.pt")

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
    min_move = frame_h * 0.02
    
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

                # 1. Custom Wrong Way Logic (Vector analysis - backup)
                if is_wrong_way(track_id, x, y, width, height):
                    active_violations[track_id] = "VIOLENCE"
                
                # 2. Model-based Violation Detection (Lane Change, Turning, U-Turn, Wrong Way)
                # best.pt has: {0: 'Lane Change', 1: 'Turning', 2: 'U Turn', 3: 'Wrong Way'}
                if results.boxes.id is not None:
                    # Find indices for this track_id
                    match_idx = (results.boxes.id == track_id).nonzero()
                    if len(match_idx) > 0:
                        idx = match_idx[0][0]
                        cls_id = int(results.boxes.cls[idx])
                        class_name = model.names[cls_id]
                        
                        # All violations from model = VIOLENCE
                        if cls_id in [0, 1, 2, 3]:  # Lane Change, Turning, U Turn, Wrong Way
                            active_violations[track_id] = "VIOLENCE"

        # Visualization
        annotated_frame = results.plot()
        
        # Overlay Violations
        if results.boxes.id is not None:
            for tid, v_type in list(active_violations.items()):
                # Find current box for this ID
                ids_list = results.boxes.id.int().cpu().numpy().tolist()
                if tid in ids_list:
                    idx = ids_list.index(tid)
                    bx = results.boxes.xyxy[idx].cpu().numpy()
                    # Drawing without emoji to avoid OpenCV rendering issues
                    color = (0, 0, 255) if v_type == "VIOLENCE" else (0, 255, 255)
                    cv2.putText(annotated_frame, f"ALERT: {v_type}", (int(bx[0]), int(bx[1])-15),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 3)

        cv2.imshow("Smart Detection - app2.py", annotated_frame)
        if cv2.waitKey(1) & 0xFF == ord('q'): break

    cap.release()
    cv2.destroyAllWindows()

import tkinter as tk
from tkinter import filedialog, messagebox

# ------------------------------
# GUI and Main Logic
# ------------------------------
class DetectionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Traffic Monitor - Standalone v2")
        self.root.geometry("400x250")
        self.root.configure(bg="#1a1a1a")

        # UI Styling
        title_font = ("Arial", 14, "bold")
        btn_font = ("Arial", 10, "bold")

        tk.Label(root, text="Traffic Violation Detector", font=title_font, fg="white", bg="#1a1a1a").pack(pady=20)
        
        # Mode Selection Buttons
        tk.Button(root, text="📁 SELECT VIDEO FILE", font=btn_font, bg="#2563eb", fg="white", 
                  width=25, height=2, command=self.select_video).pack(pady=10)
        
        tk.Button(root, text="📷 START WEBCAM", font=btn_font, bg="#16a34a", fg="white", 
                  width=25, height=2, command=self.start_webcam).pack(pady=10)

        tk.Label(root, text="Press 'Q' on the video window to quit", fg="#9ca3af", bg="#1a1a1a", font=("Arial", 8)).pack(side="bottom", pady=10)

    def select_video(self):
        file_path = filedialog.askopenfilename(filetypes=[("Video files", "*.mp4 *.avi *.mov *.mkv *.webm")])
        if file_path:
            self.root.withdraw() # Hide UI while processing
            try:
                run_detection(file_path)
            except Exception as e:
                messagebox.showerror("Error", str(e))
            self.root.deiconify() # Bring back UI

    def start_webcam(self):
        self.root.withdraw()
        try:
            run_detection(0, is_live=True)
        except Exception as e:
            messagebox.showerror("Error", str(e))
        self.root.deiconify()

if __name__ == "__main__":
    root = tk.Tk()
    app = DetectionApp(root)
    root.mainloop()
