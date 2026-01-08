"""
Vehicle Tracking and Line Counting System
Uses YOLOv8 for detection, Supervision ByteTrack for tracking, and LineCounter for counting
"""

import cv2
import numpy as np
from ultralytics import YOLO
from tqdm import tqdm
import supervision as sv

import config
import time


from collections import defaultdict, deque

class SpeedEstimator:
    """Estimates speed of tracked objects using perspective transformation and sliding window smoothing"""
    
    def __init__(self, source_points, target_points, fps):
        """
        Initialize speed estimator
        
        Args:
            source_points: 4 points in image coordinates
            target_points: 4 corresponding points in real-world coordinates (meters)
            fps: Video frame rate
        """
        self.fps = fps
        self.transformation_matrix = cv2.getPerspectiveTransform(
            source_points.astype(np.float32),
            target_points.astype(np.float32)
        )
        # Store position history: tracker_id -> deque of (transformed_y, frame_number)
        # We use a window of size equal to FPS (1 second of history)
        self.position_history = defaultdict(lambda: deque(maxlen=int(fps)))
        
    def transform_point(self, point):
        """Transform image point to real-world coordinates"""
        point_homogeneous = np.array([[[point[0], point[1]]]], dtype=np.float32)
        transformed = cv2.perspectiveTransform(point_homogeneous, self.transformation_matrix)
        return transformed[0][0]
    
    def calculate_speed(self, tracker_id, center_point, frame_number):
        """
        Calculate smoothed speed in km/h
        
        Args:
            tracker_id: Unique tracker ID
            center_point: (x, y) center of bounding box
            frame_number: Current frame number
            
        Returns:
            Speed in km/h or None if not enough data
        """
        # Transform current position to real-world coordinates
        current_real_pos = self.transform_point(center_point)
        
        # We focus on the Y coordinate (distance along the road/perspective)
        # but could use full 2D distance if needed. The blog post suggests using Y displacement.
        self.position_history[tracker_id].append((current_real_pos, frame_number))
        
        # Need at least half a second of data for a stable reading
        if len(self.position_history[tracker_id]) < self.fps / 2:
            return None
        
        # Get oldest and newest data points in the window
        (start_pos, start_frame) = self.position_history[tracker_id][0]
        (end_pos, end_frame) = self.position_history[tracker_id][-1]
        
        # Calculate distance in meters using the full 2D position
        distance = np.sqrt(
            (end_pos[0] - start_pos[0])**2 + 
            (end_pos[1] - start_pos[1])**2
        )
        
        # Calculate time elapsed in seconds
        frames_elapsed = end_frame - start_frame
        time_elapsed = frames_elapsed / self.fps
        
        if time_elapsed > 0:
            # Speed in m/s
            speed_ms = distance / time_elapsed
            # Convert to km/h
            speed_kmh = speed_ms * 3.6
            return speed_kmh
        
        return None


from behavior_engine import BehaviorEngine
from recorder import ViolationRecorder
import threading

class VehicleMonitoringSystem:
    def __init__(self):
        self.lock = threading.Lock()
        self.latest_processed_frame = None
        print(f"🎥 Loading video: {config.SOURCE_VIDEO_PATH}")
        self.video_info = sv.VideoInfo.from_video_path(config.SOURCE_VIDEO_PATH)
        self.width, self.height = self.video_info.width, self.video_info.height
        self.fps = self.video_info.fps if config.VIDEO_FPS == "AUTO" else config.VIDEO_FPS
        
        # Stats
        self.in_count = 0
        self.out_count = 0
        self.total_violations = 0
        self.recent_violations = deque(maxlen=10)
        
        self.on_violation_callback = None # Set by external app
        
        self.running = False
        self.worker_thread = None
        self.processed_frame_buffer = None
        
        # Initialization
        # Load models
        print(f"📡 Loading Base Model: {config.MODEL_PATH}")
        self.model = YOLO(config.MODEL_PATH)
        
        self.violation_model = None
        if hasattr(config, 'VIOLATION_MODEL_PATH') and config.VIOLATION_MODEL_PATH:
            print(f"🛰️ Loading Violation Model: {config.VIOLATION_MODEL_PATH}")
            self.violation_model = YOLO(config.VIOLATION_MODEL_PATH)
            
        self.byte_tracker = sv.ByteTrack()
        
        line_start = sv.Point(0, self.height * 0.7) if config.LINE_START == "AUTO" else config.LINE_START
        line_end = sv.Point(self.width, self.height * 0.7) if config.LINE_END == "AUTO" else config.LINE_END
        self.line_counter = sv.LineZone(start=line_end, end=line_start)
        
        self.line_thickness = max(2, int(self.width * 0.003)) if config.LINE_THICKNESS == "AUTO" else config.LINE_THICKNESS
        self.text_thickness = max(1, int(self.width * 0.002)) if config.TEXT_THICKNESS == "AUTO" else config.TEXT_THICKNESS
        self.text_scale = (self.width * 0.0006) if config.TEXT_SCALE == "AUTO" else config.TEXT_SCALE
        
        if config.SOURCE_POINTS == "AUTO":
            self.source_points = np.array([
                [self.width * 0.25, self.height * 0.33],
                [self.width * 0.75, self.height * 0.33],
                [self.width * 0.15, self.height * 0.85],
                [self.width * 0.85, self.height * 0.85]
            ])
        else:
            self.source_points = config.SOURCE_POINTS

        self.speed_estimator = None
        if config.ENABLE_SPEED_ESTIMATION:
            self.speed_estimator = SpeedEstimator(source_points=self.source_points, target_points=config.TARGET_POINTS, fps=self.fps)
        
        self.behavior_engine = None
        if config.ENABLE_BEHAVIOR_ANALYSIS:
            self.behavior_engine = BehaviorEngine(fps=self.fps, width=self.width, height=self.height)
        
        self.recorder = None
        if config.ENABLE_VIOLATION_RECORDING:
            self.recorder = ViolationRecorder(fps=self.fps, width=self.width, height=self.height)

        self.box_annotator = sv.BoxAnnotator(thickness=int(self.width * 0.002))
        self.label_annotator = sv.LabelAnnotator(text_thickness=self.text_thickness, text_scale=self.text_scale)
        self.line_annotator = sv.LineZoneAnnotator(thickness=self.line_thickness, text_thickness=self.text_thickness, text_scale=self.text_scale)
        
        # Store points for reset
        self.p_start, self.p_end = line_start, line_end

    def generate_frames(self):
        frame_generator = sv.get_video_frames_generator(config.SOURCE_VIDEO_PATH)
        for frame_number, frame in enumerate(frame_generator):
            # 1. Base Detection (for counting/tracking)
            base_results = self.model(frame, verbose=False, conf=config.CONFIDENCE_THRESHOLD, iou=config.IOU_THRESHOLD, classes=config.VEHICLE_CLASSES, imgsz=960)[0]
            detections = sv.Detections.from_ultralytics(base_results)
            detections = self.byte_tracker.update_with_detections(detections)
            self.line_counter.trigger(detections)

            # 2. Violation Detection (from specialist model)
            v_detections = None
            if self.violation_model:
                v_results = self.violation_model(frame, verbose=False, conf=config.CONFIDENCE_THRESHOLD, iou=config.IOU_THRESHOLD, classes=config.VIOLATION_CLASSES, imgsz=960)[0]
                v_detections = sv.Detections.from_ultralytics(v_results)
                
                # Check for direct AI violations
                for i, class_id in enumerate(v_detections.class_id):
                    v_type_map = {0: "TURNING", 1: "U_TURN", 2: "WRONG_WAY"}
                    v_type = v_type_map.get(class_id)
                    if v_type:
                        violation = {
                            "tracker_id": -1,
                            "type": v_type,
                            "frame_index": frame_number,
                            "timestamp": time.strftime("%Y%m%d_%H%M%S"),
                            "v_time": frame_number / self.fps
                        }
                        self._handle_ai_violation(violation)
            
            self.in_count = self.line_counter.in_count
            self.out_count = self.line_counter.out_count

            current_speeds = {}
            if self.speed_estimator and detections.tracker_id is not None:
                for i, tracker_id in enumerate(detections.tracker_id):
                    xyxy = detections.xyxy[i]
                    center = ((xyxy[0]+xyxy[2])/2, (xyxy[1]+xyxy[3])/2)
                    speed = self.speed_estimator.calculate_speed(tracker_id, center, frame_number)
                    if speed is not None: current_speeds[tracker_id] = speed

            violations = []
            if self.behavior_engine:
                violations = self.behavior_engine.analyze(detections, frame_number, current_speeds)
                
            if config.ENABLE_VIOLATION_RECORDING and self.recorder:
                with self.lock:
                    for v in violations:
                        self.recorder.start_recording(v)
                        self.total_violations += 1
                        self.recent_violations.append(v)
                        if self.on_violation_callback:
                            self.on_violation_callback(v)
                self.recorder.add_frame(frame)

            self.latest_processed_frame = frame

            labels = []
            for i in range(len(detections)):
                tid = detections.tracker_id[i] if detections.tracker_id is not None else None
                parts = []
                if tid is not None: parts.append(f"ID:{tid}")
                if config.SHOW_SPEED and tid in current_speeds: parts.append(f"{current_speeds[tid]:.0f}km/h")
                if self.behavior_engine:
                    v_types = set([v["type"] for v in self.behavior_engine.active_violations if v["tracker_id"] == tid])
                    for v_type in v_types: parts.append(f"⚠️{v_type}")
                labels.append(" | ".join(parts))

            annotated_frame = frame.copy()
            zone_colors = {"PARKING_SPOT": (0, 255, 0), "NO_PARKING": (0, 0, 255), "ROAD_LANE": (255, 0, 0)}
            for zone_cfg in config.ZONES:
                if zone_cfg['name'] in ["VIP Spot", "Driveway", "Emergency Exit"]:
                    continue
                color = zone_colors.get(zone_cfg["category"], (255, 255, 255))
                abs_zone = (zone_cfg["polygon"] * np.array([self.width, self.height])).astype(np.int32)
                cv2.polylines(annotated_frame, [abs_zone], True, color, self.line_thickness)
                cv2.putText(annotated_frame, zone_cfg['name'], (abs_zone[0][0], abs_zone[0][1]-10), 
                            cv2.FONT_HERSHEY_SIMPLEX, self.text_scale, color, self.text_thickness)

            # Annotate Base Detections
            annotated_frame = self.box_annotator.annotate(scene=annotated_frame, detections=detections)
            annotated_frame = self.label_annotator.annotate(scene=annotated_frame, detections=detections, labels=labels)
            
            # Annotate Violation Detections (Warning style)
            if v_detections and len(v_detections) > 0:
                v_labels = [f"⚠️ {self.violation_model.model.names[cid]}" for cid in v_detections.class_id]
                annotated_frame = self.box_annotator.annotate(scene=annotated_frame, detections=v_detections)
                annotated_frame = self.label_annotator.annotate(scene=annotated_frame, detections=v_detections, labels=v_labels)
                
            self.line_annotator.annotate(frame=annotated_frame, line_counter=self.line_counter)
            
            yield annotated_frame

    def reset_processing_state(self):
        """Resets counters and trackers when a video loops or restarts"""
        with self.lock:
            self.in_count = 0
            self.out_count = 0
            self.total_violations = 0
            self.recent_violations.clear()
            self.byte_tracker = sv.ByteTrack()
            # Re-init line counter (using the swapped points user requested)
            self.line_counter = sv.LineZone(start=self.p_end, end=self.p_start)
            if self.behavior_engine:
                self.behavior_engine.active_violations.clear()
            print("🔄 Processing state reset for next loop cycle")

    def _worker_loop(self):
        """Background loop to process frames continuously"""
        while self.running:
            try:
                # Reset before each loop if it's not the first time or if it's a file
                self.reset_processing_state()
                
                processed_count = 0
                for frame in self.generate_frames():
                    processed_count += 1
                    if not self.running:
                        break
                    with self.lock:
                        self.processed_frame_buffer = frame
                
                # If it was just an image (1 frame), sleep longer to avoid high-frequency restart
                if self.video_info.total_frames == 1 or processed_count == 1:
                    import time
                    while self.running:
                        time.sleep(1)
                
                if not self.running:
                    break
            except Exception as e:
                print(f"❌ Worker error: {e}")
                import time
                time.sleep(1)

    def start(self):
        """Start the background processing thread"""
        if not self.running:
            self.running = True
            self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
            self.worker_thread.start()
            print("🚀 Background AI Processor Started")

    def stop(self):
        """Stop the background processing thread"""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=2)
            print("🛑 Background AI Processor Stopped")

    def _handle_ai_violation(self, violation):
        """Handle violations detected directly by the behavior model"""
        # Add to recent for polling
        with self.lock:
            # Check for duplicates within short time for same spot/type (simplified cooldown)
            recent_types = [rv['type'] for rv in self.recent_violations][-5:]
            if violation['type'] not in recent_types:
                self.recent_violations.append(violation)
                self.total_violations += 1
                if self.on_violation_callback:
                    self.on_violation_callback(violation)

    def get_latest_frame(self):
        """Thread-safe access to the latest processed frame"""
        with self.lock:
            return self.processed_frame_buffer

def process_video():
    monitoring_system = VehicleMonitoringSystem()
    video_info = monitoring_system.video_info
    
    with sv.VideoSink(config.TARGET_VIDEO_PATH, video_info) as sink:
        pbar = tqdm(total=video_info.total_frames)
        for frame in monitoring_system.generate_frames():
            sink.write_frame(frame)
            pbar.update(1)
        pbar.close()
    
    print("\n✅ Processing complete!")
    print(f"💾 Results saved to: {config.TARGET_VIDEO_PATH}")

if __name__ == "__main__":
    try:
        process_video()
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

