import numpy as np
import time
from collections import defaultdict, deque
import cv2
import os
import config

class BehaviorEngine:
    """Analyzes vehicle behavior (trajectory, parking, violations)"""
    
    def __init__(self, fps, width, height):
        self.fps = fps
        self.width = width
        self.height = height
        
        # tracker_id -> deque of (center_x, center_y, timestamp, speed)
        self.path_history = defaultdict(lambda: deque(maxlen=int(fps * 10))) # 10 seconds history
        
        # tracker_id -> timestamp when first seen stationary
        self.stationary_start = {}
        
        # List of detected violations to be recorded
        # Each entry: {tracker_id, type, start_time, frame_index}
        self.active_violations = []
        
        # Cooldown to avoid multiple alerts for same vehicle/violation type
        self.violation_cooldown = defaultdict(float) # (tracker_id, type) -> timestamp

    def is_inside_polygon(self, point, polygon):
        """Check if a point is inside a polygon ROI"""
        # Polygon is scaled relative [0,1], convert to pixel coordinates
        pixel_polygon = polygon * np.array([self.width, self.height])
        return cv2.pointPolygonTest(pixel_polygon.astype(np.float32), (float(point[0]), float(point[1])), False) >= 0

    def analyze(self, detections, current_frame_index, speeds):
        """Main analysis loop for behavior detection"""
        current_time = current_frame_index / self.fps
        violations_triggered = []
        
        # Cleanup expired active violations (show for 3 seconds on UI)
        self.active_violations = [v for v in self.active_violations if current_time - v.get('v_time', 0) < 3.0]

        if detections.tracker_id is None:
            return violations_triggered

        for i, (xyxy, tracker_id) in enumerate(zip(detections.xyxy, detections.tracker_id)):
            center_x = (xyxy[0] + xyxy[2]) / 2
            center_y = (xyxy[1] + xyxy[3]) / 2
            center = (center_x, center_y)
            speed = speeds.get(tracker_id, 0)
            
            # 1. Update Path History
            self.path_history[tracker_id].append((center_x, center_y, current_time, speed))

            # Find which zone the vehicle is in
            current_zone = None
            for zone_cfg in config.ZONES:
                if self.is_inside_polygon(center, zone_cfg["polygon"]):
                    current_zone = zone_cfg
                    break

            # 2. Speeding Detection (Always active if speed is high)
            if speed > config.SPEED_LIMIT_KMH:
                if current_zone and current_zone["category"] == "ROAD_LANE":
                    self._trigger_violation(tracker_id, "SPEEDING", current_frame_index, violations_triggered)

            # 3. Movement Status
            is_stationary = speed < config.STATIONARY_SPEED_THRESHOLD
            
            if is_stationary:
                if tracker_id not in self.stationary_start:
                    self.stationary_start[tracker_id] = current_time
                
                stationary_duration = current_time - self.stationary_start[tracker_id]
                
                # Check Zone-based violations
                if current_zone:
                    if current_zone["category"] == "NO_PARKING":
                        if stationary_duration > config.ILLEGAL_PARKING_THRESHOLD:
                            self._trigger_violation(tracker_id, "ILLEGAL_PARKING", current_frame_index, violations_triggered)
                    
                    elif current_zone["category"] == "PARKING_SPOT":
                        # Check Crooked Parking (simplified: check if center is too close to ROI boundary)
                        if self._is_crooked(center, current_zone["polygon"]):
                            if stationary_duration > config.STATIONARY_TIME_THRESHOLD:
                                self._trigger_violation(tracker_id, "CROOKED_PARKING", current_frame_index, violations_triggered)
                
                # Sudden Stop on Road
                elif config.MONITORING_MODE != "PARKING" and stationary_duration > config.STATIONARY_TIME_THRESHOLD:
                    # If not in a designated parking spot but stopped on screen
                    self._trigger_violation(tracker_id, "SUDDEN_STOP", current_frame_index, violations_triggered)
            else:
                self.stationary_start.pop(tracker_id, None)

            # 4. Loitering Detection (Moving slowly for too long)
            if config.STATIONARY_SPEED_THRESHOLD < speed < 10.0:
                loitering_duration = self._get_loitering_duration(tracker_id)
                if loitering_duration > config.LOITERING_TIME_THRESHOLD:
                    self._trigger_violation(tracker_id, "LOITERING", current_frame_index, violations_triggered)

            # 5. Wrong Way Detection (Only in ROAD_LANE)
            if current_zone and current_zone["category"] == "ROAD_LANE":
                if len(self.path_history[tracker_id]) > self.fps:
                    if self._check_wrong_way(tracker_id):
                        self._trigger_violation(tracker_id, "WRONG_WAY", current_frame_index, violations_triggered)

        return violations_triggered

    def _is_crooked(self, center, polygon):
        """Estimate if vehicle is crooked (not centered in spot)"""
        # Calculate polygon center
        poly_center = np.mean(polygon, axis=0)
        
        # Calculate distance from vehicle center to polygon center
        # Relative units (0 to 1)
        dist = np.sqrt((center[0]/self.width - poly_center[0])**2 + (center[1]/self.height - poly_center[1])**2)
        
        # If the vehicle center is too far from the spot center, it's poorly parked
        return dist > config.CROOKED_PARKING_THRESHOLD

    def _get_loitering_duration(self, tracker_id):
        history = self.path_history[tracker_id]
        if not history: return 0
        
        # Check consecutive points with slow speed
        loitering_start_time = history[-1][2]
        for i in range(len(history)-1, -1, -1):
            if config.STATIONARY_SPEED_THRESHOLD < history[i][3] < 10.0:
                loitering_start_time = history[i][2]
            else:
                break
        return history[-1][2] - loitering_start_time

    def _check_if_stationary(self, tracker_id):
        history = self.path_history[tracker_id]
        if len(history) < self.fps: return False
        
        # Compare current pos with pos 1 second ago
        old_pos = history[0] # oldest in window
        new_pos = history[-1]
        
        dist = np.sqrt((new_pos[0]-old_pos[0])**2 + (new_pos[1]-old_pos[1])**2)
        # Movement threshold (e.g., less than 5 pixels in 1 second)
        return dist < (self.width * 0.005)

    def _check_wrong_way(self, tracker_id):
        # Simplistic: Check if Y movement is negative while road expects positive (or vice versa)
        # In a real system, this depends on the specific road orientation
        history = self.path_history[tracker_id]
        start_y = history[0][1]
        end_y = history[-1][1]
        
        # Dummy road logic: assuming vehicles should go DOWN (Y increases)
        # If moving UP significantly, it's wrong way
        if (start_y - end_y) > (self.height * 0.1): # Moved up 10% of screen
            return True
        return False

    def _trigger_violation(self, tracker_id, v_type, frame_index, violations_triggered):
        # Cooldown check (default 10 seconds for same vehicle/type)
        if time.time() - self.violation_cooldown[(tracker_id, v_type)] < 10:
            return
            
        self.violation_cooldown[(tracker_id, v_type)] = time.time()
        
        violation = {
            "tracker_id": tracker_id,
            "type": v_type,
            "frame_index": frame_index,
            "timestamp": time.strftime("%Y%m%d_%H%M%S"),
            "v_time": frame_index / self.fps # Store for persistence check
        }
        violations_triggered.append(violation)
        # Update/Add to active violations for UI
        existing = [v for v in self.active_violations if v['tracker_id'] == tracker_id and v['type'] == v_type]
        if not existing:
            self.active_violations.append(violation)
        else:
            existing[0]['v_time'] = violation['v_time']
            
        print(f"⚠️ VIOLATION DETECTED: {v_type} (ID: {tracker_id}) at frame {frame_index}")
