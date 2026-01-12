import cv2
import numpy as np
from collections import Counter

class SceneAnalyzer:
    """
    Analyzes video frames to determine the scene context (ROAD vs PARKING).
    Uses Hough Line Transform to detect structural patterns.
    """
    
    def __init__(self):
        pass

    def detect_scene_type(self, frame_sample):
        """
        Analyzes a single frame (or average of frames) to classify the scene.
        Returns: "ROAD" or "PARKING"
        """
        if frame_sample is None:
            return "ROAD" # Default fallback
            
        # 1. Convert to grayscale and detect edges
        gray = cv2.cvtColor(frame_sample, cv2.cvtColor(cv2.COLOR_BGR2GRAY) if len(frame_sample.shape) == 3 else cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        
        # 2. Detect lines
        # rho=1, theta=np.pi/180, threshold=100, minLineLength=100, maxLineGap=10
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=80, minLineLength=50, maxLineGap=10)
        
        if lines is None:
            return "PARKING" # Less clear structure might imply parking or cluttered scene
            
        # 3. Analyze line angles
        angles = []
        for line in lines:
            x1, y1, x2, y2 = line[0]
            angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))
            angles.append(abs(angle))
            
        # 4. Heuristic Logic
        # Road: Usually has strong diagonal lines (vanishing point) -> Angles around 30-70 degrees
        # Parking: Often horizontal/vertical bay markings -> Angles near 0, 90, 180
        
        road_votes = 0
        parking_votes = 0
        
        for angle in angles:
            # Normalize angle to 0-180
            if angle < 0: angle += 180
            
            # Check for Diagonal (Road-like)
            if 20 < angle < 80 or 100 < angle < 160:
                road_votes += 1
            # Check for Orthogonal (Parking-like)
            elif angle < 15 or angle > 165 or 75 < angle < 105:
                parking_votes += 1
                
        # Calculate ratios
        total = road_votes + parking_votes
        if total == 0: return "PARKING"
        
        road_ratio = road_votes / total
        
        print(f"🔍 Scene Analysis: Road Lines={road_votes}, Parking Lines={parking_votes}, Road Ratio={road_ratio:.2f}")
        
        if road_ratio > 0.4: # If at least 40% of lines are diagonal, it's likely a perspective road view
            return "ROAD"
        else:
            return "PARKING"

    def analyze_video_source(self, video_path, sample_count=5):
        """Read beginning of video to determine type"""
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return "ROAD"
            
        scene_votes = []
        for _ in range(sample_count):
            ret, frame = cap.read()
            if not ret: break
            scene = self.detect_scene_type(frame)
            scene_votes.append(scene)
            
        cap.release()
        
        if not scene_votes: return "ROAD"
        
        # Majority vote
        final_scene = Counter(scene_votes).most_common(1)[0][0]
        return final_scene
