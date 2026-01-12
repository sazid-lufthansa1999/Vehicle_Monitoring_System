import cv2
import numpy as np
from collections import Counter
from ultralytics import YOLO

class SceneAnalyzer:
    """
    Enhanced scene analyzer using multi-factor analysis:
    1. Line pattern detection (perspective vs grid)
    2. Vehicle movement patterns (flow vs stationary)
    3. Camera angle detection (street-level vs overhead)
    """
    
    def __init__(self):
        # Load a lightweight YOLO model for vehicle detection during analysis
        self.detector = YOLO("yolo11n.pt")

    def analyze_line_patterns(self, frame):
        """Analyze structural lines in the frame"""
        if len(frame.shape) == 3:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            gray = frame
            
        # Adaptive edge detection for varying lighting
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        
        # Detect lines
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=60, minLineLength=40, maxLineGap=15)
        
        if lines is None or len(lines) < 5:
            return 0.0  # Neutral score
            
        # Analyze line angles
        diagonal_count = 0
        orthogonal_count = 0
        
        for line in lines:
            x1, y1, x2, y2 = line[0]
            angle = abs(np.degrees(np.arctan2(y2 - y1, x2 - x1)))
            
            # Normalize to 0-180
            if angle < 0: angle += 180
            
            # Diagonal lines (perspective/vanishing point) = ROAD
            if 25 < angle < 75 or 105 < angle < 155:
                diagonal_count += 1
            # Orthogonal lines (grid/bays) = PARKING
            elif angle < 20 or angle > 160 or 80 < angle < 100:
                orthogonal_count += 1
        
        total = diagonal_count + orthogonal_count
        if total == 0: return 0.0
        
        # Return road confidence (-1 to 1, positive = ROAD)
        return (diagonal_count - orthogonal_count) / total

    def analyze_vehicle_movement(self, frames):
        """Analyze vehicle movement patterns across multiple frames"""
        if len(frames) < 3:
            return 0.0
            
        movement_vectors = []
        
        for i in range(len(frames) - 1):
            # Detect vehicles in consecutive frames
            results1 = self.detector(frames[i], verbose=False, conf=0.3, classes=[2, 3, 5, 7])
            results2 = self.detector(frames[i+1], verbose=False, conf=0.3, classes=[2, 3, 5, 7])
            
            if len(results1[0].boxes) == 0 or len(results2[0].boxes) == 0:
                continue
                
            # Calculate average movement
            boxes1 = results1[0].boxes.xyxy.cpu().numpy()
            boxes2 = results2[0].boxes.xyxy.cpu().numpy()
            
            # Simple centroid tracking
            for b1 in boxes1[:5]:  # Limit to first 5 vehicles
                cx1, cy1 = (b1[0] + b1[2]) / 2, (b1[1] + b1[3]) / 2
                
                # Find closest match in next frame
                min_dist = float('inf')
                best_match = None
                for b2 in boxes2:
                    cx2, cy2 = (b2[0] + b2[2]) / 2, (b2[1] + b2[3]) / 2
                    dist = np.sqrt((cx2 - cx1)**2 + (cy2 - cy1)**2)
                    if dist < min_dist and dist < 100:  # Max 100px movement
                        min_dist = dist
                        best_match = (cx2 - cx1, cy2 - cy1)
                
                if best_match:
                    movement_vectors.append(best_match)
        
        if not movement_vectors:
            return 0.0
            
        # Analyze movement consistency
        vectors = np.array(movement_vectors)
        avg_movement = np.mean(np.abs(vectors), axis=0)
        
        # ROAD: Consistent directional flow (high Y movement)
        # PARKING: Random/minimal movement
        flow_score = avg_movement[1] / (avg_movement[0] + 1)  # Y/X ratio
        
        # Normalize to -1 to 1 (positive = ROAD)
        return np.tanh(flow_score - 0.5)

    def analyze_camera_perspective(self, frame):
        """Detect camera angle (street-level vs overhead)"""
        h, w = frame.shape[:2]
        
        # Detect horizon line or vanishing point
        if len(frame.shape) == 3:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            gray = frame
            
        # Check for perspective distortion in top vs bottom
        top_half = gray[:h//2, :]
        bottom_half = gray[h//2:, :]
        
        # Street-level: More detail in bottom (closer objects)
        # Overhead: Uniform distribution
        top_edges = cv2.Canny(top_half, 50, 150).sum()
        bottom_edges = cv2.Canny(bottom_half, 50, 150).sum()
        
        ratio = bottom_edges / (top_edges + 1)
        
        # Street-level (ROAD) typically has ratio > 1.2
        # Overhead (PARKING) has ratio closer to 1.0
        if ratio > 1.3:
            return 1.0  # Strong ROAD indicator
        elif ratio < 0.9:
            return -0.5  # Slight PARKING indicator
        else:
            return 0.0  # Neutral

    def detect_scene_type(self, frames):
        """
        Multi-factor scene classification
        frames: list of frames (or single frame)
        """
        if not isinstance(frames, list):
            frames = [frames]
            
        if not frames or frames[0] is None:
            return "ROAD"
        
        # Factor 1: Line Pattern Analysis
        line_score = self.analyze_line_patterns(frames[0])
        
        # Factor 2: Vehicle Movement (if multiple frames)
        movement_score = 0.0
        if len(frames) >= 3:
            movement_score = self.analyze_vehicle_movement(frames)
        
        # Factor 3: Camera Perspective
        perspective_score = self.analyze_camera_perspective(frames[0])
        
        # Weighted combination
        final_score = (
            line_score * 0.4 +
            movement_score * 0.4 +
            perspective_score * 0.2
        )
        
        print(f"🔍 Scene Analysis:")
        print(f"   Line Pattern: {line_score:.2f} | Movement: {movement_score:.2f} | Perspective: {perspective_score:.2f}")
        print(f"   Final Score: {final_score:.2f} ({'ROAD' if final_score > 0 else 'PARKING'})")
        
        return "ROAD" if final_score > 0 else "PARKING"

    def analyze_video_source(self, video_path, sample_count=10):
        """Analyze video with enhanced multi-frame analysis"""
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return "ROAD"
        
        # Collect frames for analysis
        frames = []
        frame_skip = 5  # Analyze every 5th frame
        
        for i in range(sample_count * frame_skip):
            ret, frame = cap.read()
            if not ret: break
            
            if i % frame_skip == 0:
                frames.append(frame)
        
        cap.release()
        
        if not frames:
            return "ROAD"
        
        # Perform multi-frame analysis
        scene_type = self.detect_scene_type(frames)
        
        return scene_type
