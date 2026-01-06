import cv2
import numpy as np
import os
import json

# ==================== CONFIGURATION ====================
SOURCE_VIDEO_PATH = "33035-395456492_medium.mp4" # Change this to your target video
# =======================================================

class ZoneDefiner:
    def __init__(self, video_path):
        self.video_path = video_path
        self.zones = []
        self.current_points = []
        self.window_name = "Define Zones - Click to add points, Press 'Enter' to finish zone, 'S' to save, 'Q' to quit"
        
    def mouse_callback(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            self.current_points.append([x, y])
            print(f"📍 Point added: ({x}, {y})")

    def run(self):
        cap = cv2.VideoCapture(self.video_path)
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            print("❌ Error: Could not read video.")
            return

        h, w = frame.shape[:2]
        cv2.namedWindow(self.window_name)
        cv2.setMouseCallback(self.window_name, self.mouse_callback)

        while True:
            display_frame = frame.copy()
            
            # Draw existing zones
            for zone in self.zones:
                pts = np.array(zone['points'], np.int32)
                cv2.polylines(display_frame, [pts], True, (0, 255, 0), 2)
                cv2.putText(display_frame, f"{zone['name']} ({zone['category']})", 
                            (pts[0][0], pts[0][1]-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

            # Draw current points
            for pt in self.current_points:
                cv2.circle(display_frame, tuple(pt), 4, (0, 0, 255), -1)
            if len(self.current_points) > 1:
                cv2.polylines(display_frame, [np.array(self.current_points)], False, (0, 0, 255), 1)

            cv2.imshow(self.window_name, display_frame)
            key = cv2.waitKey(1) & 0xFF
            
            if key == 13: # Enter key
                if len(self.current_points) >= 3:
                    name = input("Enter Zone Name (e.g., VIP Spot): ")
                    print("Categories: 1: PARKING_SPOT, 2: NO_PARKING, 3: ROAD_LANE")
                    cat_idx = input("Enter Category Number: ")
                    categories = {"1": "PARKING_SPOT", "2": "NO_PARKING", "3": "ROAD_LANE"}
                    category = categories.get(cat_idx, "ROAD_LANE")
                    
                    # Convert to relative coordinates
                    rel_points = [[p[0]/w, p[1]/h] for p in self.current_points]
                    
                    self.zones.append({
                        "name": name,
                        "category": category,
                        "points": self.current_points.copy(),
                        "rel_points": rel_points
                    })
                    self.current_points = []
                    print(f"✅ Zone '{name}' added!")
                else:
                    print("⚠️ Need at least 3 points for a zone.")
            
            elif key == ord('s'):
                self.save_zones()
                break
                
            elif key == ord('q'):
                break

        cv2.destroyAllWindows()

    def save_zones(self):
        print("\n🚀 Copy the following ZONES list into your config.py:\n")
        print("ZONES = [")
        for zone in self.zones:
            pts_str = ", ".join([f"[{p[0]:.3f}, {p[1]:.3f}]" for p in zone['rel_points']])
            print("    {")
            print(f"        'name': '{zone['name']}',")
            print(f"        'category': '{zone['category']}',")
            print(f"        'polygon': np.array([{pts_str}])")
            print("    },")
        print("]")

if __name__ == "__main__":
    definer = ZoneDefiner(SOURCE_VIDEO_PATH)
    definer.run()