"""
Configuration file for Vehicle Tracking and Line Counting System
Customize these parameters according to your video and requirements
"""

import numpy as np
from supervision.geometry.core import Point

# ==================== SYSTEM MODE ====================
# Options: "ROAD", "PARKING", "BOTH"
MONITORING_MODE = "BOTH"

# ==================== MODEL CONFIGURATION ====================
MODEL_PATH = "yolov8n.pt"
CONFIDENCE_THRESHOLD = 0.15
IOU_THRESHOLD = 0.45
VEHICLE_CLASSES = [2, 3, 5, 7]  # car, motorcycle, bus, truck

# ==================== VIDEO CONFIGURATION ====================
SOURCE_VIDEO_PATH = "2103099-uhd_3840_2160_30fps.mp4"  # Path to your input video
TARGET_VIDEO_PATH = "output_video.mp4"  # Path to save output video

# ==================== LINE COUNTER CONFIGURATION ====================
# Set to "AUTO" to automatically scale based on video resolution
# Or use Point(x, y) for custom position
LINE_START = "AUTO"  
LINE_END = "AUTO"   

# ==================== SPEED ESTIMATION CONFIGURATION ====================
# Enable/disable speed estimation
ENABLE_SPEED_ESTIMATION = True

# Source points - 4 points in the video frame forming a quadrilateral
# Set to "AUTO" to use relative road section based on resolution
SOURCE_POINTS = "AUTO"

# Target points - corresponding real-world dimensions in meters
# This defines the actual size of the area in the real world
# Example: 20 meters wide, 30 meters long
TARGET_WIDTH = 20   # meters
TARGET_HEIGHT = 30  # meters

TARGET_POINTS = np.array([
    [0, 0],
    [TARGET_WIDTH, 0],
    [0, TARGET_HEIGHT],
    [TARGET_WIDTH, TARGET_HEIGHT]
])

# Frame rate of the video (used for speed calculation)
VIDEO_FPS = "AUTO"  # Set to "AUTO" to detect from video file

# ==================== BEHAVIOR MONITORING CONFIGURATION ====================
ENABLE_BEHAVIOR_ANALYSIS = True

# Speed rules
SPEED_LIMIT_KMH = 60.0  # Threshold for speeding alert

# Parking/Stopped rules
STATIONARY_TIME_THRESHOLD = 5.0  # Seconds before considering a vehicle "stopped"
ILLEGAL_PARKING_THRESHOLD = 15.0  # Seconds before an alert is triggered in No-Park zone

# Direction rules
WRONG_WAY_SENSITIVITY = 0.8  # 0 to 1, how strict the direction check is

# ==================== ZONE CONFIGURATION ====================
# Regions are defined as polygons (scaled 0.0 to 1.0) with a category
# Categories: "PARKING_SPOT", "NO_PARKING", "ROAD_LANE"
ZONES = [
    {
        "name": "Emergency Exit",
        "category": "NO_PARKING",
        "polygon": np.array([[0.1, 0.1], [0.3, 0.1], [0.3, 0.45], [0.1, 0.45]])
    },
    {
        "name": "VIP Spot",
        "category": "PARKING_SPOT",
        "polygon": np.array([[0.7, 0.3], [0.95, 0.3], [0.95, 0.9], [0.7, 0.9]])
    },
    {
        "name": "Driveway",
        "category": "ROAD_LANE",
        "polygon": np.array([[0.35, 0.3], [0.65, 0.3], [0.65, 0.9], [0.35, 0.9]])
    }
]

# Behavior specific thresholds
CROOKED_PARKING_THRESHOLD = 0.2 # Max distance from ROI center 
LOITERING_TIME_THRESHOLD = 15.0  # Seconds of slow movement before alert
STATIONARY_SPEED_THRESHOLD = 2.0 # km/h considered as stopped

# ==================== VIOLATION RECORDING CONFIGURATION ====================
ENABLE_VIOLATION_RECORDING = True
VIOLATION_OUTPUT_DIR = "violations"
PRE_VIOLATION_SECONDS = 5
POST_VIOLATION_SECONDS = 5

# ==================== BYTETRACK CONFIGURATION ====================
TRACK_THRESH = 0.1
TRACK_BUFFER = 60
MATCH_THRESH = 0.8
FRAME_RATE = 30

# ==================== VISUALIZATION CONFIGURATION ====================
# Colors (BGR format for OpenCV)
LINE_COLOR = (0, 255, 255)      # Yellow for counting line
BOX_COLOR = (0, 255, 0)         # Green for bounding boxes
TEXT_COLOR = (255, 255, 255)    # White for text
IN_COUNT_COLOR = (0, 255, 0)    # Green for IN count
OUT_COUNT_COLOR = (0, 0, 255)   # Red for OUT count

# Line and text settings
# Set to "AUTO" to scale based on resolution
LINE_THICKNESS = "AUTO"
BOX_THICKNESS = "AUTO"
TEXT_THICKNESS = "AUTO"
TEXT_SCALE = "AUTO"

# Display settings
SHOW_CONFIDENCE = True
SHOW_SPEED = False
SHOW_TRACKER_ID = True
