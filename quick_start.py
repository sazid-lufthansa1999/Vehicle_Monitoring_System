"""
Quick Start Example for Vehicle Tracking System
This script helps you get started quickly with a sample configuration
"""

import cv2
import numpy as np
from config import *

def create_sample_config():
    """
    Creates a sample configuration based on common video resolutions
    """
    print("🎬 Quick Start Configuration Helper")
    print("=" * 50)
    
    # Check if video exists
    import os
    if not os.path.exists(SOURCE_VIDEO_PATH):
        print(f"\n⚠️  Video not found: {SOURCE_VIDEO_PATH}")
        print("\nPlease update SOURCE_VIDEO_PATH in config.py")
        print("Example: SOURCE_VIDEO_PATH = 'path/to/your/video.mp4'")
        return
    
    # Get video info
    cap = cv2.VideoCapture(SOURCE_VIDEO_PATH)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()
    
    print(f"\n📹 Video Information:")
    print(f"   Resolution: {width}x{height}")
    print(f"   FPS: {fps}")
    print(f"   Total Frames: {total_frames}")
    print(f"   Duration: {total_frames/fps:.2f} seconds")
    
    # Suggest line position
    print(f"\n📏 Suggested Line Counter Position:")
    print(f"   Horizontal line (middle): Point({width//10}, {height//2}) -> Point({width*9//10}, {height//2})")
    print(f"   Vertical line (middle): Point({width//2}, {height//10}) -> Point({width//2}, {height*9//10})")
    
    # Suggest perspective points
    print(f"\n🎯 Suggested Perspective Points (for speed estimation):")
    print(f"   Top-left: [{width//4}, {height//3}]")
    print(f"   Top-right: [{width*3//4}, {height//3}]")
    print(f"   Bottom-left: [{width//6}, {height*5//6}]")
    print(f"   Bottom-right: [{width*5//6}, {height*5//6}]")
    
    print(f"\n💡 Tips:")
    print(f"   1. Update config.py with these values")
    print(f"   2. Adjust LINE_START and LINE_END based on where you want to count")
    print(f"   3. For speed estimation, choose 4 points on the road forming a rectangle")
    print(f"   4. Measure real-world dimensions for accurate speed")
    
    print(f"\n✅ Ready to run: python vehicle_tracker.py")


def visualize_line_position():
    """
    Shows the first frame with the counting line drawn
    Helps you verify line position before processing
    """
    import os
    if not os.path.exists(SOURCE_VIDEO_PATH):
        print(f"❌ Video not found: {SOURCE_VIDEO_PATH}")
        return
    
    cap = cv2.VideoCapture(SOURCE_VIDEO_PATH)
    ret, frame = cap.read()
    cap.release()
    
    if not ret:
        print("❌ Could not read video frame")
        return
    
    # Draw the counting line
    cv2.line(
        frame,
        (int(LINE_START.x), int(LINE_START.y)),
        (int(LINE_END.x), int(LINE_END.y)),
        LINE_COLOR,
        LINE_THICKNESS
    )
    
    # Add text
    cv2.putText(
        frame,
        "COUNTING LINE",
        (int(LINE_START.x), int(LINE_START.y) - 10),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        LINE_COLOR,
        2
    )
    
    # Draw perspective points if enabled
    if ENABLE_SPEED_ESTIMATION:
        for i, point in enumerate(SOURCE_POINTS):
            cv2.circle(frame, tuple(point.astype(int)), 10, (0, 0, 255), -1)
            cv2.putText(
                frame,
                f"P{i+1}",
                tuple(point.astype(int) + np.array([15, 0])),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 0, 255),
                2
            )
    
    # Save preview
    preview_path = "line_position_preview.jpg"
    cv2.imwrite(preview_path, frame)
    print(f"✅ Preview saved to: {preview_path}")
    print(f"   Check if the line position is correct!")
    
    # Try to display
    try:
        cv2.imshow("Line Position Preview (Press any key to close)", frame)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    except:
        print("   (Could not display window, but image is saved)")


if __name__ == "__main__":
    print("\n" + "="*50)
    print("  Vehicle Tracking System - Quick Start")
    print("="*50 + "\n")
    
    print("Choose an option:")
    print("1. Show video info and suggestions")
    print("2. Visualize line position")
    print("3. Both")
    
    choice = input("\nEnter choice (1/2/3): ").strip()
    
    if choice in ['1', '3']:
        create_sample_config()
    
    if choice in ['2', '3']:
        print("\n")
        visualize_line_position()
